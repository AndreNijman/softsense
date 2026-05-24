"""Fin Ray finger design-iteration harness.

For one parameter set (FR_* overrides on gripper.py):
  1. regenerate the finger cross-section (build123d) and mesh it (gmsh),
  2. extrude to linear tets and run the high-quality 3D corotational contact FEA
     -- CLAMPED AT THE TWO PIN BORES (C, D), like the real coupler-mounted finger,
  3. press the rigid amphora-neck cylinder into the contact face (FROZEN scenario),
  4. compute load-distribution metrics (does the WHOLE finger engage / does the top
     wrap?), save the solution, a wrap-stages PNG, a force-vs-y PNG, metrics.json.

FROZEN scenario (identical every iteration for fair comparison):
  R_neck=22 mm, neck centre y=80 mm, press 10 mm over 24 steps, kpen=2000,
  3 z-layers, gmsh size 0.5-1.3 mm, TPU E=40 MPa nu=0.42.

Usage:  python iter_harness.py <iter_name> '<params_json>'
        params_json = {"FR_WALL": 2.0, ...}  (FR_* overrides; {} = baseline)
"""
import os, sys, json, time, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
import gmsh
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

REPO = "/home/andre/gripper-cad"
ITERDIR = os.path.join(REPO, "fea", "iterations")

# ---- FROZEN FEA scenario ----
R_NECK = 22.0
YC = 80.0
PRESS_MAX = 10.0
NSTEPS = 24
KPEN = 2000.0
NLAYERS = 3
Z0, Z1 = 13.0, 23.0
MESH_MIN, MESH_MAX = 0.5, 1.3
E_TPU, NU = 40.0, 0.42
TPU_STRENGTH = 25.0   # MPa (conservative low end) for margin
GAP = 0.5

# FR_* parameters the harness is allowed to vary (captured from gripper at import).
FR_KEYS = ["FR_BLADE_LEN", "FR_BASE_WIDTH", "FR_TIP_WIDTH", "FR_WALL",
           "FR_N_RIBS", "FR_RIB_SLANT_DEG", "FR_INSET_BASE", "FR_INSET_TIP",
           "FR_CONTACT_OFFSET", "FR_BASE_DROP",
           "FR_CONTACT_WALL", "FR_CONTACT_WALL_TIP", "FR_SPINE_WALL",
           "FR_SPINE_WALL_TIP", "FR_RIB_WALL", "FR_RIB_WALL_TIP"]
PRESS_AT_REPORT = 8.0   # mm -- report metrics at this CLOSURE (the user's grasp
                        # scenario). Closure is the actuator input -> fair across
                        # variants; grip force is a reported result, not controlled.
                        # (Grip-controlled reporting washed out: at low grip the
                        # finger has barely closed and nothing can wrap yet.)

os.environ["GRIPPER_OPEN"] = "0"; os.environ["GRIPPER_FINGER_SCALE"] = "1.0"
import gripper
from build123d import Axis, export_step
_BASE_FR = {k: getattr(gripper, k) for k in FR_KEYS}


# ----------------------------------------------------------------- geometry
def regen_section(params, workdir):
    """Apply FR_* overrides, build the finger, section the top face, gmsh-mesh it.
    Returns p(N,2), tris(M,3 0-based), and landmarks (C,D,r_bore,base_y,tip_y)."""
    params = dict(params)
    gen = params.pop("_gen", None)
    refR = gripper.solve_side_right(0.0)
    C, D = refR["C"], refR["D"]
    if gen == "finray2":               # topology-R&D generator
        import finray2
        solid, lm_g = finray2.build(C, D, gripper.Z_FINGER0, gripper.T_FINGER, params)
        top = solid.faces().filter_by(Axis.Z).sort_by(Axis.Z)[-1]
    else:                              # production finger with FR_* overrides
        for k, v in _BASE_FR.items():  # reset to baseline first (clean state)
            setattr(gripper, k, v)
        for k, v in params.items():
            setattr(gripper, k, v)
        fng = gripper.finray_finger_closed(C, D, -1, gripper.Z_FINGER0, gripper.T_FINGER)
        top = fng.faces().filter_by(Axis.Z).sort_by(Axis.Z)[-1]
        lm_g = None
    step = os.path.join(workdir, "section.step")
    export_step(top, step)

    gmsh.initialize(); gmsh.option.setNumber("General.Terminal", 0)
    gmsh.open(step); gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax", MESH_MAX)
    gmsh.option.setNumber("Mesh.MeshSizeMin", MESH_MIN)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.model.mesh.generate(2); gmsh.model.mesh.optimize("Netgen")
    ntags, ncoords, _ = gmsh.model.mesh.getNodes()
    coords = ncoords.reshape(-1, 3)[:, :2]
    tag2i = {int(t): i for i, t in enumerate(ntags)}
    etypes, _, enodes = gmsh.model.mesh.getElements(dim=2)
    tris = None
    for et, en in zip(etypes, enodes):
        if et == 2:
            tris = np.array([[tag2i[int(n)] for n in tri]
                             for tri in en.reshape(-1, 3)], dtype=np.int64)
    gmsh.finalize()
    if lm_g is not None:
        lm = lm_g
    else:
        base_y = max(C[1], D[1]) - gripper.FR_BASE_DROP
        tip_y = base_y + gripper.FR_BLADE_LEN * gripper.FINGER_SCALE
        lm = dict(C=list(C), D=list(D), r_bore=gripper.MOUNT_HOLE_R,
                  base_y=base_y, tip_y=tip_y)
    return coords, tris, lm


# ----------------------------------------------------------------- FEA core
def Dmat(nu):
    lam = E_TPU * nu / ((1 + nu) * (1 - 2 * nu)); mu = E_TPU / (2 * (1 + nu))
    D = np.zeros((6, 6)); D[:3, :3] = lam
    D[0, 0] = D[1, 1] = D[2, 2] = lam + 2 * mu
    D[3, 3] = D[4, 4] = D[5, 5] = mu
    return D
D6 = Dmat(NU)


def build_tets(p2d, tris):
    N2 = p2d.shape[0]
    zs = np.linspace(Z0, Z1, NLAYERS + 1)
    nodes = np.zeros((N2 * (NLAYERS + 1), 3))
    for k, zc in enumerate(zs):
        nodes[k * N2:(k + 1) * N2, :2] = p2d
        nodes[k * N2:(k + 1) * N2, 2] = zc
    tets = []
    for k in range(NLAYERS):
        b, t = k * N2, (k + 1) * N2
        for (a, bb, c) in tris:
            a0, b0, c0 = b + a, b + bb, b + c
            a1, b1, c1 = t + a, t + bb, t + c
            tets += [(a0, b0, c0, a1), (b0, c0, a1, b1), (c0, a1, b1, c1)]
    tets = np.array(tets, np.int64)
    Jm = np.stack([nodes[tets][:, 1] - nodes[tets][:, 0],
                   nodes[tets][:, 2] - nodes[tets][:, 0],
                   nodes[tets][:, 3] - nodes[tets][:, 0]], axis=2)
    neg = np.linalg.det(Jm) < 0
    tets[neg] = tets[neg][:, [0, 2, 1, 3]]
    return nodes, tets, N2


def precompute(nodes, tets):
    X = nodes[tets]
    Jm = np.stack([X[:, 1] - X[:, 0], X[:, 2] - X[:, 0], X[:, 3] - X[:, 0]], axis=2)
    invJm = np.linalg.inv(Jm); V = np.abs(np.linalg.det(Jm)) / 6.0
    dNref = np.array([[-1, -1, -1], [1, 0, 0], [0, 1, 0], [0, 0, 1]], float)
    dNdx = np.einsum('ij,njk->nik', dNref, invJm)
    Ntet = tets.shape[0]; B = np.zeros((Ntet, 6, 12))
    for i in range(4):
        gx, gy, gz = dNdx[:, i, 0], dNdx[:, i, 1], dNdx[:, i, 2]; c = 3 * i
        B[:, 0, c] = gx; B[:, 1, c + 1] = gy; B[:, 2, c + 2] = gz
        B[:, 3, c] = gy; B[:, 3, c + 1] = gx
        B[:, 4, c + 1] = gz; B[:, 4, c + 2] = gy
        B[:, 5, c] = gz; B[:, 5, c + 2] = gx
    Ke0 = np.einsum('nki,kl,nlj->nij', B, D6, B) * V[:, None, None]
    edof = (tets[:, :, None] * 3 + np.arange(3)[None, None, :]).reshape(Ntet, 12)
    I = np.repeat(edof, 12, axis=1).reshape(-1); Jc = np.tile(edof, (1, 12)).reshape(-1)
    return dict(invJm=invJm, V=V, Ke0=Ke0, edof=edof, I=I, J=Jc, Ntet=Ntet,
                Xvec=X.reshape(Ntet, 12))


def polar_R(F):
    U, S, Vt = np.linalg.svd(F); R = np.einsum('nij,njk->nik', U, Vt)
    flip = np.linalg.det(R) < 0
    if np.any(flip):
        U2 = U.copy(); U2[flip, :, 2] *= -1
        R[flip] = np.einsum('nij,njk->nik', U2[flip], Vt[flip])
    return R


def apply_blockR(R, Vvec):
    Vr = Vvec.reshape(-1, 4, 3)
    return np.einsum('nij,nkj->nki', R, Vr).reshape(-1, 12)


def run_fea(p2d, tris, lm, verbose=True):
    nodes, tets, N2 = build_tets(p2d, tris)
    P = precompute(nodes, tets)
    nn = nodes.shape[0]; ndof = nn * 3; Xrest = nodes.copy(); u = np.zeros(ndof)
    # ---- CLAMP: the two pin-bore rims (C, D), all 3 translations ----
    C, D = np.array(lm["C"]), np.array(lm["D"]); rb = lm["r_bore"]
    dC = np.hypot(Xrest[:, 0] - C[0], Xrest[:, 1] - C[1])
    dD = np.hypot(Xrest[:, 0] - D[0], Xrest[:, 1] - D[1])
    clampnodes = (dC < rb + 0.4) | (dD < rb + 0.4)
    fixed = np.zeros(ndof, bool)
    for d in range(3): fixed[3 * np.where(clampnodes)[0] + d] = True
    free = np.where(~fixed)[0]
    if verbose: print(f"  clamp nodes={clampnodes.sum()} (2 bores)  ndof={ndof} tets={P['Ntet']}")

    Ke0 = P['Ke0']; invJm = P['invJm']; edof = P['edof']; Iidx = P['I']; Jidx = P['J']
    Xvec = P['Xvec']; Ntet = P['Ntet']
    xc0 = Xrest[:, 0].min() - R_NECK - GAP
    tipc = np.where(Xrest[:, 1] > Xrest[:, 1].max() - 1.0)[0]
    tip_node = tipc[np.argmin(np.abs(Xrest[tipc, 2] - (Z0 + Z1) / 2))]

    frames = []; vms_frames = []; grip = []; press_hist = []
    cforce_list = []; vmtet_list = []
    for s in range(1, NSTEPS + 1):
        press = PRESS_MAX * s / NSTEPS; cx = xc0 + press; cy = YC
        for it in range(16):
            x = (Xrest.reshape(-1) + u).reshape(nn, 3); xe = x[tets]
            Js = np.stack([xe[:, 1] - xe[:, 0], xe[:, 2] - xe[:, 0], xe[:, 3] - xe[:, 0]], axis=2)
            F = np.einsum('nij,njk->nik', Js, invJm); R = polar_R(F)
            RtX = apply_blockR(np.transpose(R, (0, 2, 1)), xe.reshape(Ntet, 12)) - Xvec
            f_e = apply_blockR(R, np.einsum('nij,nj->ni', Ke0, RtX))
            f_int = np.zeros(ndof); np.add.at(f_int, edof.reshape(-1), f_e.reshape(-1))
            Rb = np.zeros((Ntet, 12, 12))
            for k in range(4): Rb[:, 3 * k:3 * k + 3, 3 * k:3 * k + 3] = R
            Ke = np.einsum('nij,njk,nlk->nil', Rb, Ke0, Rb)
            dx = x[:, 0] - cx; dy = x[:, 1] - cy; rr = np.hypot(dx, dy) + 1e-9
            pen = R_NECK - rr; inside = pen > 0
            f_ext = np.zeros(ndof)
            K = coo_matrix((Ke.reshape(-1), (Iidx, Jidx)), shape=(ndof, ndof)).tocsr()
            if np.any(inside):
                nrm = np.zeros((nn, 3)); nrm[:, 0] = dx / rr; nrm[:, 1] = dy / rr
                fc = (KPEN * pen)[:, None] * nrm; fc[~inside] = 0
                f_ext[0::3] += fc[:, 0]; f_ext[1::3] += fc[:, 1]
                ii = np.where(inside)[0]; rows = []; cols = []; vals = []
                nno = np.einsum('ni,nj->nij', nrm, nrm) * KPEN
                for a in range(3):
                    for b in range(3):
                        rows.append(3 * ii + a); cols.append(3 * ii + b); vals.append(nno[ii, a, b])
                K = K + coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
                                   shape=(ndof, ndof)).tocsr()
            r = f_int - f_ext; rn = np.linalg.norm(r[free])
            if it > 0 and rn < 2e-3 * (1 + np.linalg.norm(f_ext[free])): break
            du = spsolve(K[free][:, free].tocsc(), -r[free])
            u[free] += (1.0 if it > 1 else 0.7) * du
        # record
        x = (Xrest.reshape(-1) + u).reshape(nn, 3); xe = x[tets]
        Js = np.stack([xe[:, 1] - xe[:, 0], xe[:, 2] - xe[:, 0], xe[:, 3] - xe[:, 0]], axis=2)
        F = np.einsum('nij,njk->nik', Js, invJm); R = polar_R(F)
        RtF = np.einsum('nij,njk->nik', np.transpose(R, (0, 2, 1)), F)
        eps = 0.5 * (RtF + np.transpose(RtF, (0, 2, 1))) - np.eye(3)[None]
        ev = np.stack([eps[:, 0, 0], eps[:, 1, 1], eps[:, 2, 2],
                       2 * eps[:, 0, 1], 2 * eps[:, 1, 2], 2 * eps[:, 2, 0]], axis=1)
        sig = ev @ D6.T; sx, sy, sz, sxy, syz, szx = sig.T
        vm = np.sqrt(0.5 * ((sx - sy)**2 + (sy - sz)**2 + (sz - sx)**2) + 3 * (sxy**2 + syz**2 + szx**2))
        nodal = np.zeros(nn); cnt = np.zeros(nn)
        np.add.at(nodal, tets.reshape(-1), np.repeat(vm, 4)); np.add.at(cnt, tets.reshape(-1), 1)
        nodal /= np.maximum(cnt, 1)
        dx = x[:, 0] - cx; dy = x[:, 1] - cy; rr = np.hypot(dx, dy) + 1e-9
        pen = R_NECK - rr; inside = pen > 0
        gfx = float(np.sum((KPEN * pen[inside]) * (dx[inside] / rr[inside]))) if inside.any() else 0.0
        cf = np.zeros(nn); cf[inside] = KPEN * pen[inside]
        frames.append(x.astype(np.float32)); vms_frames.append(nodal.astype(np.float32))
        cforce_list.append(cf.astype(np.float32)); vmtet_list.append(vm.astype(np.float32))
        grip.append(abs(gfx)); press_hist.append(press)
        if verbose:
            print(f"  step {s:2d}/{NSTEPS} press={press:5.2f} it={it+1} grip={abs(gfx):6.2f}N vmmax={nodal.max():.2f}", flush=True)
    # frame at the report closure (fair grasp condition = same actuator input)
    grip_arr = np.array(grip)
    tgt = int(np.argmin(np.abs(np.array(press_hist) - PRESS_AT_REPORT)))
    return dict(rest=Xrest, tets=tets, frames=np.array(frames), vms=np.array(vms_frames),
                grip=grip_arr, press=np.array(press_hist), N2=N2, nlayers=NLAYERS,
                yc=YC, R_neck=R_NECK, xc0=xc0, tip_node=tip_node,
                cforce_list=cforce_list, vmtet_list=vmtet_list, target_idx=tgt, lm=lm)


# ----------------------------------------------------------------- metrics
def metrics(sol):
    """Metrics at the target-grip frame (fair grasp condition across variants)."""
    Xr = sol['rest']; lm = sol['lm']; tgt = sol['target_idx']
    cf = sol['cforce_list'][tgt]; vm = sol['vmtet_list'][tgt]; xf = sol['frames'][tgt]
    base_y, tip_y = lm['base_y'], lm['tip_y']; L = tip_y - base_y
    inside = cf > 1e-9
    yk = Xr[inside, 1]; fk = cf[inside]
    engage = (yk.max() - yk.min()) / L if inside.any() else 0.0
    thirds = base_y + np.array([0, 1 / 3, 2 / 3, 1.0]) * L
    tot = fk.sum() + 1e-12
    bot = fk[yk < thirds[1]].sum() / tot
    mid = fk[(yk >= thirds[1]) & (yk < thirds[2])].sum() / tot
    top = fk[yk >= thirds[2]].sum() / tot
    tn = sol['tip_node']
    tip_inward = float(Xr[tn, 0] - xf[tn, 0])   # +ve = apex moved toward object
    spread = float((vm > 0.3 * vm.max()).mean())
    maxvm = float(vm.max()); margin = TPU_STRENGTH / maxvm
    g = float(sol['grip'][tgt])
    return dict(engage_y_frac=round(engage, 3),
                contact_nodes=int(inside.sum()),
                bot_third_force_frac=round(float(bot), 3),
                mid_third_force_frac=round(float(mid), 3),
                top_third_force_frac=round(float(top), 3),
                tip_inward_mm=round(tip_inward, 2),
                stress_spread_frac=round(spread, 3),
                max_von_mises_MPa=round(maxvm, 3),
                margin_x=round(float(margin), 2),
                grip_at_press_N=round(g, 2),
                press_mm=round(float(sol['press'][tgt]), 2),
                contact_y_min=round(float(yk.min()), 1) if inside.any() else None,
                contact_y_max=round(float(yk.max()), 1) if inside.any() else None)


# ----------------------------------------------------------------- plots
def plot_all(sol, m, outdir, title):
    Xr = sol['rest']; tets = sol['tets']; N2 = sol['N2']
    # mid-plane triangulation: first-layer nodes + original tris (reconstruct)
    # use the surface tris from layer 0 by taking tets' bottom faces is messy; instead
    # plot nodes colored by vM at 4 stages (scatter, like the reference image).
    F = sol['frames']; V = sol['vms']; pr = sol['press']; tgt = sol['target_idx']
    midz = (Z0 + Z1) / 2; layer = np.argmin(np.abs(np.unique(Xr[:, 2]) - midz))
    zlevels = np.unique(Xr[:, 2]); zsel = zlevels[layer]
    sel = np.abs(Xr[:, 2] - zsel) < 1e-6
    vmax = float(np.percentile(V[tgt][sel], 99)) + 1e-6
    idxs = [0, max(1, tgt // 2), tgt, len(F) - 1]   # 3rd panel = target-grip frame
    fig, axs = plt.subplots(1, 4, figsize=(15, 7))
    for ax, i in zip(axs, idxs):
        P = F[i][sel]
        sc = ax.scatter(P[:, 0], P[:, 1], c=V[i][sel], s=4, cmap='inferno', vmin=0, vmax=vmax)
        cx = sol['xc0'] + pr[i]; th = np.linspace(0, 2 * np.pi, 80)
        ax.plot(cx + R_NECK * np.cos(th), YC + R_NECK * np.sin(th), c='c', lw=1.5)
        ax.set_aspect('equal')
        tag = " (target grip)" if i == tgt else ""
        ax.set_title(f"press={pr[i]:.1f}mm grip={sol['grip'][i]:.1f}N{tag}", fontsize=8)
        ax.set_xlim(-30, 35); ax.set_ylim(20, 130)
    fig.suptitle(title, fontsize=11)
    fig.colorbar(sc, ax=axs, fraction=0.02, label="von Mises (MPa)")
    fig.savefig(os.path.join(outdir, "wrap_stages.png"), dpi=120); plt.close(fig)
    # force-vs-y distribution (at the target-grip frame)
    cf = sol['cforce_list'][tgt]; inside = cf > 1e-9; lm = sol['lm']
    fig2, ax2 = plt.subplots(figsize=(4, 6))
    if inside.any():
        ax2.hist(Xr[inside, 1], bins=18, weights=cf[inside], color='#c33',
                 orientation='horizontal')
    for yy, lab in [(lm['base_y'], 'base'), (lm['tip_y'], 'tip')]:
        ax2.axhline(yy, color='k', ls=':', lw=0.8)
    L = lm['tip_y'] - lm['base_y']
    ax2.axhline(lm['base_y'] + 2 / 3 * L, color='b', ls='--', lw=0.8, label='top third')
    ax2.set_ylim(20, 130); ax2.set_xlabel("contact force / bin"); ax2.set_ylabel("y (mm)")
    ax2.set_title(f"load vs height\nengage={m['engage_y_frac']} top={m['top_third_force_frac']}")
    ax2.legend(fontsize=7); fig2.tight_layout()
    fig2.savefig(os.path.join(outdir, "force_vs_y.png"), dpi=120); plt.close(fig2)


# ----------------------------------------------------------------- main
def main():
    global YC, R_NECK
    name = sys.argv[1]; params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    if "_R" in params:              # optional object-radius override (scenario test)
        R_NECK = float(params.pop("_R")); print(f"[{name}] R_NECK override = {R_NECK}")
    if len(sys.argv) > 3:            # optional override of the neck-centre y (scenario test)
        YC = float(sys.argv[3]); print(f"[{name}] YC override = {YC}")
    outdir = os.path.join(ITERDIR, name); os.makedirs(outdir, exist_ok=True)
    t0 = time.time()
    print(f"[{name}] params={params}")
    p2d, tris, lm = regen_section(params, outdir)
    print(f"  section: {p2d.shape[0]} nodes / {tris.shape[0]} tris")
    sol = run_fea(p2d, tris, lm)
    m = metrics(sol)
    plot_all(sol, m, outdir, f"{name}  {params}")
    np.savez_compressed(os.path.join(outdir, "fea3d_solution.npz"),
                        rest=sol['rest'], tets=sol['tets'].astype(np.int32),
                        frames=sol['frames'], vms=sol['vms'], grip=sol['grip'],
                        press=sol['press'])
    json.dump({k: getattr(gripper, k) for k in FR_KEYS},
              open(os.path.join(outdir, "params.json"), "w"), indent=2)
    json.dump(m, open(os.path.join(outdir, "metrics.json"), "w"), indent=2)
    print(f"[{name}] metrics: {json.dumps(m)}")
    print(f"[{name}] done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()

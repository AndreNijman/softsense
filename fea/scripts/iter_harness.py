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
  3 z-layers, gmsh size 0.5-1.3 mm, TPU E=9.8 MPa nu=0.42 (Bambu TPU 95A HF, X-Y).

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

# ---- optional GPU backend (CuPy / CUDA) --------------------------------------
# GRIPPER_FEA_GPU=1 + cupy installed -> the Newton solve runs on the GPU; otherwise
# the default NumPy/SciPy CPU path runs UNCHANGED. The CPU run_fea is never altered;
# the GPU path is a separate mirror (_run_fea_gpu) so the validated CPU results stand.
_np = np
# .strip()/lower so a stray trailing space (cmd.exe `set VAR=1 &&` quirk) still works
_WANT_GPU = os.environ.get("GRIPPER_FEA_GPU", "0").strip().lower() in ("1", "true", "yes", "on")
GPU = False
if _WANT_GPU:
    try:
        import cupy as _cp
        import cupyx
        import cupyx.scipy.sparse as _xsp
        import cupyx.scipy.sparse.linalg as _xspl
        _cp.cuda.runtime.getDeviceCount()
        GPU = True
    except Exception as _e:                       # no GPU / cupy -> silent CPU fallback
        print(f"  [GPU requested but unavailable: {type(_e).__name__}: {_e}; using CPU]")
        GPU = False


def _xp_of(a):
    """Array module of `a` — cupy if it's a device array, else numpy."""
    return _cp.get_array_module(a) if GPU else _np


def _to_np(a):
    return _cp.asnumpy(a) if (GPU and isinstance(a, _cp.ndarray)) else _np.asarray(a)


def _scatter_add(out, idx, vals):
    if GPU and isinstance(out, _cp.ndarray):
        cupyx.scatter_add(out, idx, vals)
    else:
        _np.add.at(out, idx, vals)


def _solve_reduced(data, rows, cols, rhs_full, free, dof_red, nfree):
    """Solve K_free du = rhs_full[free], building the reduced system from COO
    triplets (no fancy sparse slicing). GPU: CG + Jacobi precond (SPD system),
    with a CPU direct-solve fallback if CG doesn't converge."""
    keep = (dof_red[rows] >= 0) & (dof_red[cols] >= 0)
    rr = dof_red[rows[keep]]; cc = dof_red[cols[keep]]; vv = data[keep]
    b = rhs_full[free]
    if GPU and isinstance(data, _cp.ndarray):
        Kr = _xsp.coo_matrix((vv, (rr, cc)), shape=(nfree, nfree)).tocsr()
        d = Kr.diagonal(); d = _cp.where(d == 0, 1.0, d)
        M = _xspl.LinearOperator((nfree, nfree), matvec=lambda v: v / d)
        try:
            try:
                x, info = _xspl.cg(Kr, b, rtol=1e-7, maxiter=6000, M=M)
            except TypeError:
                x, info = _xspl.cg(Kr, b, tol=1e-7, maxiter=6000, M=M)
            if info == 0:
                return x
        except Exception:
            pass
        Kc = coo_matrix((_to_np(vv), (_to_np(rr), _to_np(cc))), shape=(nfree, nfree)).tocsc()
        return _cp.asarray(spsolve(Kc, _to_np(b)))
    Kr = coo_matrix((vv, (rr, cc)), shape=(nfree, nfree)).tocsc()
    return spsolve(Kr, b)

# REPO root: honour GRIPPER_REPO env var, else two-levels-up from this script,
# else fall back to the historical absolute path (preserves the previous default
# for callers that source the repo at /home/andre/gripper-cad).
_HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get(
    "GRIPPER_REPO",
    os.path.dirname(os.path.dirname(_HERE)) if os.path.isfile(
        os.path.join(os.path.dirname(os.path.dirname(_HERE)), "gripper.py")
    ) else "/home/andre/gripper-cad",
)
ITERDIR = os.path.join(REPO, "fea", "iterations")
# make `import gripper` work when iter_harness.py is invoked from any cwd
if REPO not in sys.path:
    sys.path.insert(0, REPO)

# ---- FROZEN FEA scenario ----
R_NECK = 22.0
YC = 80.0
PRESS_MAX = 10.0
NSTEPS = 24
# env override for sweep speed (param_sweep.py defaults to 12 for cheap sweeps;
# production fidelity is 24).
NSTEPS = int(os.environ.get("GRIPPER_NSTEPS_OVERRIDE", NSTEPS))
KPEN = 2000.0
NLAYERS = 3
Z0, Z1 = 13.0, 23.0
MESH_MIN, MESH_MAX = 0.5, 1.3
# Material = Bambu TPU 95A HF (the selected filament). Bambu's published TDS
# (ISO 527, PRINTED specimens -- not injection-moulded) gives an ANISOTROPIC
# Young's modulus: 9.8 +/- 0.7 MPa in-plane (X-Y) and 7.4 +/- 0.6 MPa through-Z.
# The finger prints FLAT (28x96 face on the bed; cells in the build plane), so its
# in-plane bending -- the grip mechanism -- is governed by the X-Y modulus 9.8 MPa.
# This REPLACES the old eSUN E=40 MPa GUESS with a measured, printed-specimen value.
# Caveat: 9.8 MPa is the ISO 527 initial-tangent modulus; a real Fin-Ray at finite
# wrap strain is hyperelastic, so absolute forces here are order-of-magnitude. The
# repo posture is rank/force-targeted (margins are modulus-insensitive at force-
# targeted reporting -- see PRINT_PROFILE_P1S_TPU.md / fea sensitivity E=7/9.8/12).
# nu~0.42 (TPU; Bambu publishes no Poisson value -- literature estimate, unchanged).
E_TPU, NU = 9.8, 0.42
# environment overrides (so locking/mesh sweeps don't have to monkey-patch globals):
E_TPU = float(os.environ.get("GRIPPER_E_TPU", E_TPU))
NU    = float(os.environ.get("GRIPPER_NU", NU))
NLAYERS = int(os.environ.get("GRIPPER_NLAYERS", NLAYERS))
TPU_STRENGTH = 27.3   # MPa -- Bambu TPU 95A HF in-plane (X-Y) tensile strength,
# ISO 527 printed specimen (the direction the finger is loaded in bending). The
# weak through-Z direction is 22.3 MPa (used for the underwater through-thickness
# crush). For a Shore-95A elastomer at >650% elongation this "strength" is a
# deformation/stress-ceiling proxy, not a brittle yield. See docs/MATERIALS.md.
GAP = 0.5
OBJ_SHAPE = "circle"  # "circle" (R=R_NECK) or "box" (square, half-size=R_NECK).
                      # A UNIVERSAL gripper must conform to non-round shapes too,
                      # so iterations are scored on circles AND a square block.


def obj_contact(x, cx, cy):
    """Rigid-object penetration for penalty contact. Returns (pen, nrm, inside):
    pen>=0 depth, nrm outward unit normal (nn,3), inside bool mask. Supports a
    circle (radius R_NECK) or an axis-aligned square (half-size R_NECK)."""
    xp = _xp_of(x)
    if OBJ_SHAPE == "box":
        dx = x[:, 0] - cx; dy = x[:, 1] - cy; H = R_NECK
        qx = xp.abs(dx) - H; qy = xp.abs(dy) - H
        inside = (qx < 0) & (qy < 0)
        usex = qx >= qy                                  # nearest face is an x-face
        pen = xp.where(usex, -qx, -qy)
        nrm = xp.zeros((x.shape[0], 3))
        sgx = xp.where(dx >= 0, 1.0, -1.0); sgy = xp.where(dy >= 0, 1.0, -1.0)
        nrm[usex, 0] = sgx[usex]; nrm[~usex, 1] = sgy[~usex]
        return xp.where(inside, pen, 0.0), nrm, inside
    dx = x[:, 0] - cx; dy = x[:, 1] - cy; rr = xp.hypot(dx, dy) + 1e-9
    pen = R_NECK - rr; inside = pen > 0
    nrm = xp.zeros((x.shape[0], 3)); nrm[:, 0] = dx / rr; nrm[:, 1] = dy / rr
    return xp.where(inside, pen, 0.0), nrm, inside

# FR_* parameters the harness is allowed to vary (captured from gripper at import).
FR_KEYS = ["FR_BLADE_LEN", "FR_BASE_WIDTH", "FR_TIP_WIDTH", "FR_WALL",
           "FR_N_RIBS", "FR_RIB_SLANT_DEG", "FR_RIB_DIR", "FR_INSET_BASE", "FR_INSET_TIP",
           "FR_CONTACT_OFFSET", "FR_BASE_DROP",
           "FR_CONTACT_WALL", "FR_CONTACT_WALL_TIP", "FR_SPINE_WALL",
           "FR_SPINE_WALL_TIP", "FR_RIB_WALL", "FR_RIB_WALL_TIP"]
REPORT_MODE = "closure"  # "closure" -> report at PRESS_AT_REPORT; "grip" -> report
                         # at the FIRST closure reaching TARGET_GRIP (fair across
                         # stiff/compliant fingers: same grip force, compare the wrap).
                         #
                         # DOC/CODE DISCLOSURE: docs/TESTING_AND_SIMULATION.md A.8
                         # presents force-targeted ("grip") reporting as THE
                         # fairness methodology, but the code default here is
                         # "closure" reporting at PRESS_AT_REPORT = 8.0 mm. Most
                         # per-family universal-score tables in the repo were
                         # generated with closure mode; force-targeted mode was
                         # used selectively in the swarm to handle the stiff-vs-
                         # compliant comparison. Toggle via env var REPORT_MODE.
TARGET_GRIP = 12.0       # N -- STRESS-PROBE LOAD used to rank designs at a closure
                         # the FEA can reach in software. NOT the operating force
                         # the shipped drivetrain can safely deliver -- the printed
                         # crown gear's root-bending ceiling caps the per-finger
                         # force at ~0.14..0.28 N (radial 2D bound) or ~0.35..0.73 N
                         # (single-station 2D bound), an order of magnitude below
                         # 12 N. Run motor/scripts/drivetrain_force_envelope.py
                         # for the live force band. Rank-only claim: in the small-
                         # strain corotational regime, the design ranking at 12 N
                         # is preserved at any sub-T_safe operating load.
PRESS_AT_REPORT = 8.0   # mm -- report metrics at this CLOSURE (the user's grasp
                        # scenario). Closure is the actuator input -> fair across
                        # variants; grip force is a reported result, not controlled.
                        # (Grip-controlled reporting washed out: at low grip the
                        # finger has barely closed and nothing can wrap yet.)
# environment overrides (so locking/mesh sweeps don't have to monkey-patch):
REPORT_MODE     = os.environ.get("GRIPPER_REPORT_MODE", REPORT_MODE)
TARGET_GRIP     = float(os.environ.get("GRIPPER_TARGET_GRIP", TARGET_GRIP))
PRESS_AT_REPORT = float(os.environ.get("GRIPPER_PRESS_AT_REPORT", PRESS_AT_REPORT))

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
    if gen == "finray2":               # free-topology Fin Ray generator
        import finray2
        solid, lm_g = finray2.build(C, D, gripper.Z_FINGER0, gripper.T_FINGER, params)
        top = solid.faces().filter_by(Axis.Z).sort_by(Axis.Z)[-1]
    elif gen == "flexure":             # monolithic compliant flexure generator
        import flexure_finger
        solid, lm_g = flexure_finger.build(C, D, gripper.Z_FINGER0, gripper.T_FINGER, params)
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
    xp = _xp_of(F)
    U, S, Vt = xp.linalg.svd(F); R = xp.einsum('nij,njk->nik', U, Vt)
    flip = xp.linalg.det(R) < 0
    if bool(xp.any(flip)):
        U2 = U.copy(); U2[flip, :, 2] *= -1
        R[flip] = xp.einsum('nij,njk->nik', U2[flip], Vt[flip])
    return R


def apply_blockR(R, Vvec):
    xp = _xp_of(R)
    Vr = Vvec.reshape(-1, 4, 3)
    return xp.einsum('nij,nkj->nki', R, Vr).reshape(-1, 12)


def _run_fea_gpu(p2d, tris, lm, verbose=True):
    """GPU (CuPy) mirror of run_fea: same finite-strain corotational contact solve,
    Newton linear systems solved on the GPU (CG + Jacobi precond). Mesh/precompute
    stay on CPU; arrays move to the device for the loop; results return as numpy."""
    cp = _cp
    nodes, tets, N2 = build_tets(p2d, tris)
    P = precompute(nodes, tets)
    nn = nodes.shape[0]; ndof = nn * 3
    C, D = np.array(lm["C"]), np.array(lm["D"]); rb = lm["r_bore"]
    dC = np.hypot(nodes[:, 0] - C[0], nodes[:, 1] - C[1])
    dD = np.hypot(nodes[:, 0] - D[0], nodes[:, 1] - D[1])
    clampnodes = (dC < rb + 0.4) | (dD < rb + 0.4)
    fixed = np.zeros(ndof, bool)
    for d in range(3): fixed[3 * np.where(clampnodes)[0] + d] = True
    free = np.where(~fixed)[0]
    if "obj_cx" in lm:
        xc0 = lm["obj_cx"] - PRESS_AT_REPORT
    else:
        band = np.abs(nodes[:, 1] - YC) < max(6.0, R_NECK * 0.8)
        mx = nodes[band, 0].min() if band.any() else nodes[:, 0].min()
        xc0 = mx - R_NECK - GAP
    tipc = np.where(nodes[:, 1] > nodes[:, 1].max() - 1.0)[0]
    tip_node = int(tipc[np.argmin(np.abs(nodes[tipc, 2] - (Z0 + Z1) / 2))])
    if verbose:
        print(f"  [GPU] clamp nodes={int(clampnodes.sum())} ndof={ndof} tets={P['Ntet']}", flush=True)
    # ---- move to device ----
    Ke0 = cp.asarray(P['Ke0']); invJm = cp.asarray(P['invJm']); Xvec = cp.asarray(P['Xvec'])
    edof = cp.asarray(P['edof']); Iidx = cp.asarray(P['I']); Jidx = cp.asarray(P['J'])
    Ntet = P['Ntet']
    tets_g = cp.asarray(tets); Xrest = cp.asarray(nodes); u = cp.zeros(ndof)
    D6g = cp.asarray(D6); free_g = cp.asarray(free); nfree = int(free.shape[0])
    dof_red = -cp.ones(ndof, dtype=cp.int64); dof_red[free_g] = cp.arange(nfree)
    eye3 = cp.eye(3)[None]
    frames = []; vms_frames = []; grip = []; press_hist = []
    cforce_list = []; vmtet_list = []
    newton_iters = []; did_converge = []; residual_final = []
    MAX_NEWTON = 16
    NEWTON_TOL_REL = 2e-3
    for s in range(1, NSTEPS + 1):
        press = PRESS_MAX * s / NSTEPS; cx = xc0 + press; cy = YC
        converged_this = False; last_rn = None
        for it in range(MAX_NEWTON):
            x = (Xrest.reshape(-1) + u).reshape(nn, 3); xe = x[tets_g]
            Js = cp.stack([xe[:, 1] - xe[:, 0], xe[:, 2] - xe[:, 0], xe[:, 3] - xe[:, 0]], axis=2)
            F = cp.einsum('nij,njk->nik', Js, invJm); R = polar_R(F)
            RtX = apply_blockR(cp.transpose(R, (0, 2, 1)), xe.reshape(Ntet, 12)) - Xvec
            f_e = apply_blockR(R, cp.einsum('nij,nj->ni', Ke0, RtX))
            f_int = cp.zeros(ndof); _scatter_add(f_int, edof.reshape(-1), f_e.reshape(-1))
            Rb = cp.zeros((Ntet, 12, 12))
            for k in range(4): Rb[:, 3 * k:3 * k + 3, 3 * k:3 * k + 3] = R
            Ke = cp.einsum('nij,njk,nlk->nil', Rb, Ke0, Rb)
            pen, nrm, inside = obj_contact(x, cx, cy)
            f_ext = cp.zeros(ndof)
            data = Ke.reshape(-1); rows = Iidx; cols = Jidx
            if bool(cp.any(inside)):
                fc = (KPEN * pen)[:, None] * nrm; fc[~inside] = 0
                f_ext[0::3] += fc[:, 0]; f_ext[1::3] += fc[:, 1]
                ii = cp.where(inside)[0]
                nno = cp.einsum('ni,nj->nij', nrm, nrm) * KPEN
                cr = []; cc_ = []; cv = []
                for a in range(3):
                    for b in range(3):
                        cr.append(3 * ii + a); cc_.append(3 * ii + b); cv.append(nno[ii, a, b])
                data = cp.concatenate([data] + cv)
                rows = cp.concatenate([rows] + cr)
                cols = cp.concatenate([cols] + cc_)
            r = f_int - f_ext; rn = float(cp.linalg.norm(r[free_g]))
            last_rn = rn
            if it > 0 and rn < NEWTON_TOL_REL * (1 + float(cp.linalg.norm(f_ext[free_g]))):
                converged_this = True
                break
            du = _solve_reduced(data, rows, cols, -r, free_g, dof_red, nfree)
            u[free_g] += (1.0 if it > 1 else 0.7) * du
        newton_iters.append(it + 1)
        did_converge.append(bool(converged_this))
        residual_final.append(last_rn if last_rn is not None else float("nan"))
        # ---- record (device -> host) ----
        x = (Xrest.reshape(-1) + u).reshape(nn, 3); xe = x[tets_g]
        Js = cp.stack([xe[:, 1] - xe[:, 0], xe[:, 2] - xe[:, 0], xe[:, 3] - xe[:, 0]], axis=2)
        F = cp.einsum('nij,njk->nik', Js, invJm); R = polar_R(F)
        RtF = cp.einsum('nij,njk->nik', cp.transpose(R, (0, 2, 1)), F)
        eps = 0.5 * (RtF + cp.transpose(RtF, (0, 2, 1))) - eye3
        ev = cp.stack([eps[:, 0, 0], eps[:, 1, 1], eps[:, 2, 2],
                       2 * eps[:, 0, 1], 2 * eps[:, 1, 2], 2 * eps[:, 2, 0]], axis=1)
        sig = ev @ D6g.T; sx, sy, sz, sxy, syz, szx = sig.T
        vm = cp.sqrt(0.5 * ((sx - sy)**2 + (sy - sz)**2 + (sz - sx)**2) + 3 * (sxy**2 + syz**2 + szx**2))
        nodal = cp.zeros(nn); cnt = cp.zeros(nn)
        _scatter_add(nodal, tets_g.reshape(-1), cp.repeat(vm, 4))
        _scatter_add(cnt, tets_g.reshape(-1), cp.ones(Ntet * 4))
        nodal = nodal / cp.maximum(cnt, 1)
        pen, nrm, inside = obj_contact(x, cx, cy)
        gfx = float(cp.sum(KPEN * pen[inside] * nrm[inside, 0])) if bool(cp.any(inside)) else 0.0
        cf = cp.zeros(nn); cf[inside] = KPEN * pen[inside]
        frames.append(_to_np(x).astype(np.float32)); vms_frames.append(_to_np(nodal).astype(np.float32))
        cforce_list.append(_to_np(cf).astype(np.float32)); vmtet_list.append(_to_np(vm).astype(np.float32))
        grip.append(abs(gfx)); press_hist.append(press)
        if verbose:
            print(f"  [GPU] step {s:2d}/{NSTEPS} press={press:5.2f} it={it+1} "
                  f"grip={abs(gfx):6.2f}N vmmax={float(nodal.max()):.2f}", flush=True)
    grip_arr = np.array(grip)
    if REPORT_MODE == "grip":
        idx = np.where(grip_arr >= TARGET_GRIP)[0]
        tgt = int(idx[0]) if len(idx) else int(np.argmax(grip_arr))
    else:
        tgt = int(np.argmin(np.abs(np.array(press_hist) - PRESS_AT_REPORT)))
    return dict(rest=nodes, tets=tets, frames=np.array(frames), vms=np.array(vms_frames),
                grip=grip_arr, press=np.array(press_hist), N2=N2, nlayers=NLAYERS,
                yc=YC, R_neck=R_NECK, xc0=xc0, tip_node=tip_node,
                cforce_list=cforce_list, vmtet_list=vmtet_list, target_idx=tgt, lm=lm,
                newton_iters=newton_iters, did_converge=did_converge,
                residual_final=residual_final,
                newton_max_iters=MAX_NEWTON, newton_tol_rel=NEWTON_TOL_REL)


def run_fea(p2d, tris, lm, verbose=True):
    if GPU:                                   # GPU path (mirror); CPU path below unchanged
        return _run_fea_gpu(p2d, tris, lm, verbose)
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
    # object placement: a concave-arc finger declares obj_cx so the rigid object
    # seats CONCENTRIC with the designed arc at the report frame (cx=obj_cx at
    # press=PRESS_AT_REPORT). Otherwise approach the finger's nearest face point.
    if "obj_cx" in lm:
        xc0 = lm["obj_cx"] - PRESS_AT_REPORT
    else:
        # place the object against the finger portion AT THE OBJECT'S HEIGHT (not the
        # global min-x, which for a curved/pre-curved finger is the tip) so every
        # candidate is pressed on its contact face, fairly.
        band = np.abs(Xrest[:, 1] - YC) < max(6.0, R_NECK * 0.8)
        mx = Xrest[band, 0].min() if band.any() else Xrest[:, 0].min()
        xc0 = mx - R_NECK - GAP
    tipc = np.where(Xrest[:, 1] > Xrest[:, 1].max() - 1.0)[0]
    tip_node = tipc[np.argmin(np.abs(Xrest[tipc, 2] - (Z0 + Z1) / 2))]

    frames = []; vms_frames = []; grip = []; press_hist = []
    cforce_list = []; vmtet_list = []
    newton_iters = []; did_converge = []; residual_final = []
    MAX_NEWTON = 16
    NEWTON_TOL_REL = 2e-3
    for s in range(1, NSTEPS + 1):
        press = PRESS_MAX * s / NSTEPS; cx = xc0 + press; cy = YC
        converged_this = False
        last_rn = None
        for it in range(MAX_NEWTON):
            x = (Xrest.reshape(-1) + u).reshape(nn, 3); xe = x[tets]
            Js = np.stack([xe[:, 1] - xe[:, 0], xe[:, 2] - xe[:, 0], xe[:, 3] - xe[:, 0]], axis=2)
            F = np.einsum('nij,njk->nik', Js, invJm); R = polar_R(F)
            RtX = apply_blockR(np.transpose(R, (0, 2, 1)), xe.reshape(Ntet, 12)) - Xvec
            f_e = apply_blockR(R, np.einsum('nij,nj->ni', Ke0, RtX))
            f_int = np.zeros(ndof); np.add.at(f_int, edof.reshape(-1), f_e.reshape(-1))
            Rb = np.zeros((Ntet, 12, 12))
            for k in range(4): Rb[:, 3 * k:3 * k + 3, 3 * k:3 * k + 3] = R
            Ke = np.einsum('nij,njk,nlk->nil', Rb, Ke0, Rb)
            pen, nrm, inside = obj_contact(x, cx, cy)
            f_ext = np.zeros(ndof)
            K = coo_matrix((Ke.reshape(-1), (Iidx, Jidx)), shape=(ndof, ndof)).tocsr()
            if np.any(inside):
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
            last_rn = float(rn)
            if it > 0 and rn < NEWTON_TOL_REL * (1 + np.linalg.norm(f_ext[free])):
                converged_this = True
                break
            du = spsolve(K[free][:, free].tocsc(), -r[free])
            u[free] += (1.0 if it > 1 else 0.7) * du
        newton_iters.append(it + 1)
        did_converge.append(bool(converged_this))
        residual_final.append(last_rn if last_rn is not None else float("nan"))
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
        pen, nrm, inside = obj_contact(x, cx, cy)
        gfx = float(np.sum(KPEN * pen[inside] * nrm[inside, 0])) if inside.any() else 0.0
        cf = np.zeros(nn); cf[inside] = KPEN * pen[inside]
        frames.append(x.astype(np.float32)); vms_frames.append(nodal.astype(np.float32))
        cforce_list.append(cf.astype(np.float32)); vmtet_list.append(vm.astype(np.float32))
        grip.append(abs(gfx)); press_hist.append(press)
        if verbose:
            print(f"  step {s:2d}/{NSTEPS} press={press:5.2f} it={it+1} grip={abs(gfx):6.2f}N vmmax={nodal.max():.2f}", flush=True)
    # report frame: force-targeted (first closure reaching TARGET_GRIP) or fixed closure
    grip_arr = np.array(grip)
    if REPORT_MODE == "grip":
        idx = np.where(grip_arr >= TARGET_GRIP)[0]
        tgt = int(idx[0]) if len(idx) else int(np.argmax(grip_arr))
    else:
        tgt = int(np.argmin(np.abs(np.array(press_hist) - PRESS_AT_REPORT)))
    return dict(rest=Xrest, tets=tets, frames=np.array(frames), vms=np.array(vms_frames),
                grip=grip_arr, press=np.array(press_hist), N2=N2, nlayers=NLAYERS,
                yc=YC, R_neck=R_NECK, xc0=xc0, tip_node=tip_node,
                cforce_list=cforce_list, vmtet_list=vmtet_list, target_idx=tgt, lm=lm,
                newton_iters=newton_iters, did_converge=did_converge,
                residual_final=residual_final,
                newton_max_iters=MAX_NEWTON, newton_tol_rel=NEWTON_TOL_REL)


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
    tip_inward = float(Xr[tn, 0] - xf[tn, 0])   # apex motion (NOT a success metric)
    spread = float((vm > 0.3 * vm.max()).mean())
    maxvm = float(vm.max()); margin = TPU_STRENGTH / maxvm
    g = float(sol['grip'][tgt])
    # --- WRAP-QUALITY metrics (the correct ones): how much of the object's arc the
    # contact face conforms to, and how evenly the pressure is distributed ---
    cx = sol['xc0'] + sol['press'][tgt]
    if inside.sum() >= 2:
        angd = np.degrees(np.arctan2(xf[inside, 1] - YC, xf[inside, 0] - cx))
        contact_arc = float(angd.max() - angd.min())
        pcov = float(fk.std() / (fk.mean() + 1e-12))
    else:
        contact_arc = 0.0; pcov = 0.0
    closure = float(sol['press'][tgt])
    # "locked" = the structure blew past target grip without graceful compliance and
    # is over-stressed -> a rigid jaw that crushes, not a gripper that conforms.
    locked = bool(maxvm > 0 and margin < 1.5 and g > 1.6 * TARGET_GRIP)
    # Newton-convergence telemetry per step (A14 of the critical review): persist
    # the did_converge flag, max iters used, and final residual so a downstream
    # reader can tell whether a result was a clean converged solve or a silently-
    # capped one at the 16-iter limit. `did_converge_all_steps` is the overall
    # gate; the per-step lists are kept in case any individual step needs
    # auditing (e.g. the first contact-engagement step often takes more iters).
    nit = sol.get("newton_iters", [])
    dc = sol.get("did_converge", [])
    rf = sol.get("residual_final", [])
    out_extra = dict(
        did_converge_all_steps=bool(all(dc)) if dc else None,
        n_steps_not_converged=int(sum(1 for x in dc if not x)) if dc else None,
        newton_iters_max_used=int(max(nit)) if nit else None,
        newton_iters_mean=round(sum(nit) / len(nit), 2) if nit else None,
        newton_iters_per_step=list(map(int, nit)) if nit else None,
        did_converge_per_step=[bool(x) for x in dc] if dc else None,
        residual_final_per_step=[float(x) for x in rf] if rf else None,
        newton_max_iters=int(sol.get("newton_max_iters", 0)),
        newton_tol_rel=float(sol.get("newton_tol_rel", 0.0)),
        report_mode=str(REPORT_MODE),
        target_grip_stress_probe_N=float(TARGET_GRIP),
        press_at_report_mm=float(PRESS_AT_REPORT),
        nu_used=float(NU),
        e_tpu_used=float(E_TPU),
        nlayers_used=int(NLAYERS),
    )
    return dict(contact_nodes=int(inside.sum()),
                contact_arc_deg=round(contact_arc, 1),
                pressure_cov=round(pcov, 2),
                closure_at_target=round(closure, 2),
                reached_target=bool(g >= 0.9 * TARGET_GRIP),
                locked=locked,
                stress_spread_frac=round(spread, 3),
                engage_y_frac=round(engage, 3),
                bot_third_force_frac=round(float(bot), 3),
                mid_third_force_frac=round(float(mid), 3),
                top_third_force_frac=round(float(top), 3),
                tip_inward_mm=round(tip_inward, 2),
                max_von_mises_MPa=round(maxvm, 3),
                margin_x=round(float(margin), 2),
                grip_at_press_N=round(g, 2),
                press_mm=round(float(sol['press'][tgt]), 2),
                contact_y_min=round(float(yk.min()), 1) if inside.any() else None,
                contact_y_max=round(float(yk.max()), 1) if inside.any() else None,
                **out_extra)


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
    global YC, R_NECK, OBJ_SHAPE
    name = sys.argv[1]; params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    if "_shape" in params:          # "circle" | "box" (universality test)
        OBJ_SHAPE = str(params.pop("_shape")); print(f"[{name}] OBJ_SHAPE = {OBJ_SHAPE}")
    if "_R" in params:              # optional object-radius/half-size override
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
                        press=sol['press'], xc0=sol['xc0'], yc=YC, R_neck=R_NECK,
                        obj_shape=OBJ_SHAPE)
    json.dump({k: getattr(gripper, k) for k in FR_KEYS},
              open(os.path.join(outdir, "params.json"), "w"), indent=2)
    json.dump(m, open(os.path.join(outdir, "metrics.json"), "w"), indent=2)
    print(f"[{name}] metrics: {json.dumps(m)}")
    print(f"[{name}] done in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()

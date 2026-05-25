"""Tier-2 verification: 2D plane-strain FEA of a grip-texture cross-section.

IMPORTANT SCOPE: this FEA validates ONLY the contact-mechanics sub-models that
every family shares -- (1) the real-contact / land-fraction phi_eff(load), and
(2) the root-stress durability estimate sigma_root = 6*tau*AR. It does NOT and
cannot validate the grip number itself (friction coefficient, wet drainage); that
rests on Tier-1 + literature. Do not read this as confirming the holding force.

Why 2D plane-strain: the texture is an extruded relief; a cross-section through
one pitch in plane strain is faithful and cheap, where the 1.3mm tet mesh of the
finger solver cannot resolve a 0.5mm post. Lengths mm, stress MPa.

Two studies on the SHIPPED crosshatch post (land 1.26, gap 0.54, height 0.9):
  A. CONTACT: press the post top with a rigid flat platen at increasing depth;
     measure real contact width / pitch = phi_eff(p_real). Confirms the lands
     carry load at ~the geometric fraction (=> p_real = p_nom/phi is right) and
     calibrates C_FLAT.
  B. DURABILITY: apply normal pressure + tangential traction tau=mu*p on the post
     top (sharp root = conservative, no fillet); measure peak von-Mises at the
     root and compare to the beam estimate 6*tau*AR and the Tier-1 margin.

Linear elastic plane strain, Q4 elements, penalty contact, scipy sparse direct.
"""
import sys, os, json, numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
sys.path.insert(0, os.path.dirname(__file__))

E_TPU, NU = 40.0, 0.42
ITER = os.path.join(os.path.dirname(__file__), "..", "iterations")


def plane_strain_D(E, nu):
    c = E / ((1 + nu) * (1 - 2 * nu))
    return c * np.array([[1 - nu, nu, 0],
                         [nu, 1 - nu, 0],
                         [0, 0, (1 - 2 * nu) / 2]])


def q4_ke(xy, D):
    """4-node bilinear quad stiffness, 2x2 Gauss."""
    ke = np.zeros((8, 8)); g = 1 / np.sqrt(3)
    for xi in (-g, g):
        for et in (-g, g):
            dN = 0.25 * np.array([[-(1 - et), (1 - et), (1 + et), -(1 + et)],
                                  [-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)]])
            J = dN @ xy
            dNxy = np.linalg.solve(J, dN)
            B = np.zeros((3, 8))
            B[0, 0::2] = dNxy[0]; B[1, 1::2] = dNxy[1]
            B[2, 0::2] = dNxy[1]; B[2, 1::2] = dNxy[0]
            ke += B.T @ D @ B * abs(np.linalg.det(J))
    return ke


def build_mesh(land, gap, height, base_h=2.0, n_pitch=1, ex=0.09):
    """Structured Q4 mesh: a base slab + n_pitch posts (land wide, height tall,
    gap between). Returns nodes (Nx2), elems (Mx4), and tag dict."""
    pitch = land + gap
    W = n_pitch * pitch
    nx = max(2, int(round(W / ex)))
    nyb = max(2, int(round(base_h / ex)))
    nyp = max(2, int(round(height / ex)))
    xs = np.linspace(0, W, nx + 1)
    # base rows 0..base_h, post rows base_h..base_h+height
    yb = np.linspace(0, base_h, nyb + 1)
    yp = np.linspace(base_h, base_h + height, nyp + 1)[1:]
    ys = np.concatenate([yb, yp])
    nodes = np.array([(x, y) for y in ys for x in xs])
    ncols = nx + 1

    def nid(ix, iy):
        return iy * ncols + ix

    elems = []
    is_post_col = np.zeros(nx, dtype=bool)
    for ix in range(nx):
        xc = 0.5 * (xs[ix] + xs[ix + 1])
        within = xc % pitch
        is_post_col[ix] = within <= land  # land occupies [0,land] of each pitch
    nrows_b = len(yb)
    for iy in range(len(ys) - 1):
        for ix in range(nx):
            # above the base, only keep columns that are post material
            if iy >= nrows_b - 1 and not is_post_col[ix]:
                continue
            elems.append([nid(ix, iy), nid(ix + 1, iy),
                          nid(ix + 1, iy + 1), nid(ix, iy + 1)])
    elems = np.array(elems)
    tags = dict(W=W, pitch=pitch, base_h=base_h, height=height, ncols=ncols,
                top_y=base_h + height, xs=xs, ys=ys)
    return nodes, elems, tags


def orphan_dofs(nodes, elems):
    """DOFs of nodes not referenced by any element (must be constrained out)."""
    ref = np.unique(elems.ravel())
    orph = np.setdiff1d(np.arange(len(nodes)), ref)
    return np.concatenate([2 * orph, 2 * orph + 1]).astype(int)


def assemble(nodes, elems, D):
    ndof = 2 * len(nodes)
    rows, cols, vals = [], [], []
    for el in elems:
        xy = nodes[el]
        ke = q4_ke(xy, D)
        dofs = np.array([[2 * n, 2 * n + 1] for n in el]).ravel()
        for a in range(8):
            for b in range(8):
                rows.append(dofs[a]); cols.append(dofs[b]); vals.append(ke[a, b])
    K = sp.csr_matrix((vals, (rows, cols)), shape=(ndof, ndof))
    return K


def vonmises_at_nodes(nodes, elems, U, D):
    """Element-centre von Mises (plane strain), averaged to nodes."""
    sig = np.zeros(len(nodes)); cnt = np.zeros(len(nodes))
    for el in elems:
        xy = nodes[el]
        dN = 0.25 * np.array([[-1, 1, 1, -1], [-1, -1, 1, 1]])  # at centre xi=et=0
        J = dN @ xy
        dNxy = np.linalg.solve(J, dN)
        B = np.zeros((3, 8))
        B[0, 0::2] = dNxy[0]; B[1, 1::2] = dNxy[1]
        B[2, 0::2] = dNxy[1]; B[2, 1::2] = dNxy[0]
        dofs = np.array([[2 * n, 2 * n + 1] for n in el]).ravel()
        s = D @ (B @ U[dofs])           # [sxx, syy, sxy]
        sxx, syy, sxy = s
        szz = NU * (sxx + syy)          # plane strain
        vm = np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 +
                            (szz - sxx) ** 2 + 6 * sxy ** 2))
        for n in el:
            sig[n] += vm; cnt[n] += 1
    cnt[cnt == 0] = 1
    return sig / cnt


def study_contact(land=1.26, gap=0.54, height=0.9):
    """Press a rigid flat platen onto the post top; phi_eff = contact_width/pitch."""
    D = plane_strain_D(E_TPU, NU)
    nodes, elems, T = build_mesh(land, gap, height, n_pitch=1, ex=0.06)
    K = assemble(nodes, elems, D)
    ndof = 2 * len(nodes)
    top_y = T["top_y"]
    top_nodes = np.where(np.abs(nodes[:, 1] - top_y) < 1e-6)[0]
    base_nodes = np.where(nodes[:, 1] < 1e-6)[0]
    fixed = np.concatenate([2 * base_nodes, 2 * base_nodes + 1, orphan_dofs(nodes, elems)])
    kpen = 1e4
    out = []
    for delta in [0.002, 0.005, 0.01, 0.02, 0.04]:    # platen descent (mm)
        Kc = K.tolil()
        F = np.zeros(ndof)
        for n in top_nodes:                            # penalty contact y-dir
            Kc[2 * n + 1, 2 * n + 1] += kpen
            F[2 * n + 1] += -kpen * delta              # platen pushes down by delta
        Kc = Kc.tocsr()
        free = np.setdiff1d(np.arange(ndof), fixed)
        U = np.zeros(ndof)
        U[free] = spla.spsolve(Kc[free][:, free], F[free])
        # physical transmitted load = vertical reaction at the clamped base
        # (the penalty force itself is contaminated by the penalty stiffness).
        Pn = abs(float((K @ U)[2 * base_nodes + 1].sum()))  # N/mm (total normal load)
        # contact width: top nodes actually in compression (flat top -> full land)
        cf = kpen * (U[2 * top_nodes + 1] + delta)
        active = cf > 1e-9
        cw = active.sum() / max(len(top_nodes) - 1, 1) * land
        phi_eff = cw / T["pitch"]
        p_nom = Pn / T["pitch"]                          # nominal pressure MPa
        p_real = Pn / max(cw, 1e-6)
        out.append(dict(delta=delta, p_nom=round(p_nom, 4), p_real=round(p_real, 4),
                        phi_eff=round(phi_eff, 3)))
    return out, land / (land + gap)


def study_durability(land=1.26, gap=0.54, height=0.9, mu=1.0, p_real=0.20):
    """Normal pressure + tangential traction on post top; peak von-Mises at root.
    Sharp root (no fillet) -> conservative upper bound on stress."""
    D = plane_strain_D(E_TPU, NU)
    nodes, elems, T = build_mesh(land, gap, height, n_pitch=1, ex=0.05)
    K = assemble(nodes, elems, D)
    ndof = 2 * len(nodes)
    top_y = T["top_y"]
    top_nodes = np.where(np.abs(nodes[:, 1] - top_y) < 1e-6)[0]
    base_nodes = np.where(nodes[:, 1] < 1e-6)[0]
    fixed = np.concatenate([2 * base_nodes, 2 * base_nodes + 1, orphan_dofs(nodes, elems)])
    F = np.zeros(ndof)
    tau = mu * p_real
    # consistent nodal loads for uniform traction over the top edge (land wide)
    seg = land / max(len(top_nodes) - 1, 1)
    for i, n in enumerate(sorted(top_nodes, key=lambda k: nodes[k, 0])):
        w = seg * (0.5 if i in (0, len(top_nodes) - 1) else 1.0)
        F[2 * n] += tau * w        # tangential (shear) +x
        F[2 * n + 1] += -p_real * w  # normal (down)
    free = np.setdiff1d(np.arange(ndof), fixed)
    U = np.zeros(ndof)
    U[free] = spla.spsolve(K[free][:, free], F[free])
    vm = vonmises_at_nodes(nodes, elems, U, D)
    # peak at the root region (within ~0.15mm of base_h, post material)
    root_band = (np.abs(nodes[:, 1] - T["base_h"]) < 0.15)
    peak_root = vm[root_band].max() if root_band.any() else vm.max()
    AR = height / land
    beam = 6 * tau * AR
    return dict(mu=mu, p_real=p_real, tau=round(tau, 4), AR=round(AR, 3),
                fea_root_vm=round(float(peak_root), 4), beam_estimate=round(beam, 4),
                conc_factor=round(float(peak_root) / max(beam, 1e-6), 2),
                fea_margin=round(25.0 / float(peak_root), 1),
                beam_margin=round(25.0 / max(beam, 1e-6), 1))


if __name__ == "__main__":
    print("=== Tier-2 FEA: SHIPPED crosshatch post (land 1.26, gap 0.54, h 0.9) ===")
    print("\n[A] CONTACT -- phi_eff(load) vs geometric land fraction")
    rows, phi_geo = study_contact()
    print(f"  geometric land fraction phi = {phi_geo:.3f}")
    for r in rows:
        print(f"  delta={r['delta']:.3f}mm  p_nom={r['p_nom']:.3f}  "
              f"p_real={r['p_real']:.3f}  phi_eff={r['phi_eff']:.3f}")

    print("\n[B] DURABILITY -- root von-Mises (sharp root = conservative)")
    dur = []
    for mu in (0.5, 1.0, 1.8):
        d = study_durability(mu=mu)
        dur.append(d)
        print(f"  mu={mu}: tau={d['tau']:.3f}MPa  FEA root vM={d['fea_root_vm']:.3f}MPa  "
              f"beam 6*tau*AR={d['beam_estimate']:.3f}  conc x{d['conc_factor']}  "
              f"FEA margin={d['fea_margin']}x (beam {d['beam_margin']}x)")

    os.makedirs(ITER, exist_ok=True)
    json.dump(dict(contact=rows, phi_geometric=round(phi_geo, 3), durability=dur),
              open(os.path.join(ITER, "_tier2_fea.json"), "w"), indent=2)
    print("\nwrote _tier2_fea.json")

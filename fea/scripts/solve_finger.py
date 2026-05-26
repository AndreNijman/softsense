"""Geometrically-nonlinear (finite-strain) plane-strain FEA of the Fin Ray finger.

PRECURSOR / CONSISTENCY-CHECK SOLVER, not the canonical production FEA. The
canonical 3D corotational solve lives in `iter_harness.py`; this 2D plane-
strain solve was the precursor and is retained as an order-of-magnitude
consistency check on peak von-Mises. It DOES NOT solve the same problem as
iter_harness:

  this (solve_finger.py)                vs    iter_harness.py
  -------------------------                   ----------------
  2D plane-strain                              3D corotational (3-layer extrude)
  St-Venant-Kirchhoff finite-strain            corotational small-strain
  ν = 0.45                                     ν = 0.42
  nodal force-controlled contact patch         rigid-cylinder displacement-
    (no rigid object, no contact search)        controlled, penalty contact
  load-control limit point at ~5.7 N           pushes through to 12 N stress probe
  P1 triangles                                 linear tets

So an apples-to-apples cross-validation has not been done; "two solves agree
on peak vM ~2.7 MPa" is an order-of-magnitude consistency claim, not a true
cross-derivation. See `docs/TESTING_AND_SIMULATION.md §A.11` for the table
and `OVERNIGHT_FIXES.md #3` for the framing fix.

Model: St.-Venant-Kirchhoff, total Lagrangian, analytic consistent tangent,
Newton iteration with load stepping. Mounts (C/D bores) clamped; a horizontal
contact load is applied on a patch of the contact face (the artifact push). The
slanted ribs make the tip curl inward -> the Fin Ray wrap, emergent (no contact
search needed -> robust). Outputs deformed configs + von Mises + force/closure.

TPU ~95A assumed: E, nu below (engineering ESTIMATES, not measured on the
print; see docs/MATERIALS.md and docs/PRINT_PROFILE_P1S_TPU.md for the
honest provenance).

Note: the 5.4 N F_TARGET is INTENTIONALLY just below the load-control limit
point at ~5.7 N — the geometry sits at the edge of a snap instability under
force control, which the 3D displacement-controlled solver can push past but
the 2D force-control here cannot. That itself is a finding worth knowing
about; it does not invalidate the precursor's peak-vM number.

Usage:
  python solve_finger.py selftest      # validate analytic tangent vs FD
  python solve_finger.py run           # full load-stepped solve -> results.npz
"""
import os, sys, json, time, numpy as np
import skfem
from skfem import (MeshTri, Basis, ElementVector, ElementTriP1,
                   LinearForm, BilinearForm, condense, solve)
from skfem.helpers import grad, transpose, ddot, trace, eye, mul

HERE = os.path.dirname(__file__)

# ---- material: TPU ~95A, plane strain (ASSUMED values) ----
E_TPU = 40.0          # MPa  (Shore 95A ~ tens of MPa; assumed)
NU_TPU = 0.45         # near-incompressible; 0.45 to limit P1 volumetric locking
MU = E_TPU / (2.0 * (1.0 + NU_TPU))
LAM = E_TPU * NU_TPU / ((1.0 + NU_TPU) * (1.0 - 2.0 * NU_TPU))   # plane strain


def load_mesh():
    d = np.load(os.path.join(HERE, "mesh.npz"))
    return MeshTri(d["p"], d["t"])


# ---- St.-Venant-Kirchhoff forms (total Lagrangian) ----
def _I(field):
    """2x2 identity broadcast to the quadrature-field shape of `field`."""
    return eye(np.ones_like(field[0, 0]), 2)


@LinearForm
def residual(v, w):
    du = w["disp"].grad                 # d u_i / d X_j   (2x2)
    I = _I(du)
    F = du + I
    Egl = 0.5 * (mul(transpose(F), F) - I)               # Green-Lagrange
    S = eye(LAM * trace(Egl), 2) + 2.0 * MU * Egl        # 2nd PK
    P = mul(F, S)                                         # 1st PK
    return ddot(P, grad(v))


@BilinearForm
def tangent(u, v, w):
    du = w["disp"].grad
    I = _I(du)
    F = du + I
    Egl = 0.5 * (mul(transpose(F), F) - I)
    S = eye(LAM * trace(Egl), 2) + 2.0 * MU * Egl
    dF = grad(u)                                          # variation (trial)
    dE = 0.5 * (mul(transpose(dF), F) + mul(transpose(F), dF))
    dS = eye(LAM * trace(dE), 2) + 2.0 * MU * dE
    dP = mul(dF, S) + mul(F, dS)                          # material + geometric
    return ddot(dP, grad(v))


def build():
    mesh = load_mesh()
    e = ElementVector(ElementTriP1())
    basis = Basis(mesh, e)
    return mesh, basis


def bc_and_load(mesh, basis):
    """Clamp mount-hole boundary nodes; pick contact-patch nodes for the load."""
    lm = json.load(open(os.path.join(HERE, "finger_landmarks.json")))
    C, D = np.array(lm["C"]), np.array(lm["D"])
    rmh = lm["mount_hole_r"]
    base_y, tip_y, blade = lm["base_y"], lm["tip_y"], lm["blade_len"]
    contact_x = lm["contact_x"]

    p = mesh.p
    bnodes = np.unique(mesh.facets[:, mesh.boundary_facets()])

    # clamp: boundary nodes ringing either mount bore
    def near(pt, r):
        return np.hypot(p[0] - pt[0], p[1] - pt[1]) <= r + 0.8
    clamp_nodes = bnodes[(near(C, rmh) | near(D, rmh))[bnodes]]

    # contact patch: boundary nodes on the contact face (low x), mid-blade band
    y0 = base_y + 0.42 * blade
    y1 = base_y + 0.62 * blade
    onface = (p[0] < contact_x + 1.2) & (p[1] > y0) & (p[1] < y1)
    patch_nodes = bnodes[onface[bnodes]]
    return clamp_nodes, patch_nodes, lm


def dofs_of_nodes(basis, nodes):
    """All (x,y) dof indices for a set of node ids (ElementVector P1)."""
    nodal = basis.nodal_dofs            # shape (2, n_nodes)
    return nodal[:, nodes].flatten()


def x_dofs_of_nodes(basis, nodes):
    return basis.nodal_dofs[0, nodes]


def selftest():
    mesh, basis = build()
    clamp_nodes, patch_nodes, _ = bc_and_load(mesh, basis)
    D = dofs_of_nodes(basis, clamp_nodes)
    rng = np.random.default_rng(0)
    u = 0.02 * rng.standard_normal(basis.N)
    u[D] = 0.0
    R0 = residual.assemble(basis, disp=basis.interpolate(u))
    K = tangent.assemble(basis, disp=basis.interpolate(u))
    free = np.setdiff1d(np.arange(basis.N), D)
    d = rng.standard_normal(basis.N); d[D] = 0.0
    errs = []
    for eps in (1e-4, 1e-5, 1e-6):
        Rp = residual.assemble(basis, disp=basis.interpolate(u + eps * d))
        fd = (Rp - R0)[free] / eps
        an = (K @ d)[free]
        errs.append(np.linalg.norm(fd - an) / max(np.linalg.norm(an), 1e-30))
    print("tangent FD relative error @ eps=1e-4,1e-5,1e-6:",
          ["%.2e" % e for e in errs])
    print("PASS" if min(errs) < 1e-4 else "FAIL")


def newton_step(basis, u, D, fext, tol=1e-8, maxit=40):
    for it in range(maxit):
        R = residual.assemble(basis, disp=basis.interpolate(u)) - fext
        K = tangent.assemble(basis, disp=basis.interpolate(u))
        # Dirichlet: zero rows/cols via condense with x=0 increments
        du = solve(*condense(K, -R, D=D))
        u = u + du
        rn = np.linalg.norm(R[np.setdiff1d(np.arange(basis.N), D)])
        dn = np.linalg.norm(du)
        if dn < tol * (1 + np.linalg.norm(u)):
            return u, it + 1, rn, True
    return u, maxit, rn, False


def von_mises_per_node(mesh, basis, u):
    """Cauchy von Mises (plane strain) averaged to nodes."""
    @LinearForm
    def vm_proj(v, w):
        du = w["disp"].grad
        I = _I(du)
        F = du + I
        J = F[0, 0] * F[1, 1] - F[0, 1] * F[1, 0]
        Egl = 0.5 * (mul(transpose(F), F) - I)
        S = eye(LAM * trace(Egl), 2) + 2.0 * MU * Egl
        P = mul(F, S)
        # Cauchy sigma = (1/J) P F^T
        sig = (1.0 / J) * mul(P, transpose(F))
        sxx, syy, sxy = sig[0, 0], sig[1, 1], sig[0, 1]
        szz = NU_TPU * (sxx + syy)        # plane strain out-of-plane
        vm = np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 +
                            (szz - sxx) ** 2 + 6.0 * sxy ** 2))
        return vm * v
    sb = basis.with_element(ElementTriP1())
    num = vm_proj.assemble(sb, disp=basis.interpolate(u))
    den = LinearForm(lambda v, w: 1.0 + 0.0 * w.x[0]).assemble(sb)
    return num / np.maximum(den, 1e-30)


def run():
    mesh, basis = build()
    clamp_nodes, patch_nodes, lm = bc_and_load(mesh, basis)
    D = dofs_of_nodes(basis, clamp_nodes)
    print(f"clamp nodes={len(clamp_nodes)}  patch nodes={len(patch_nodes)}  "
          f"dofs={basis.N}")
    if len(patch_nodes) == 0:
        print("ERROR: empty contact patch"); return

    xpd = x_dofs_of_nodes(basis, patch_nodes)
    NSTEP = 24
    F_TARGET = 5.4     # N total grip load (ramped) -- just below the load-control
                       # limit point at ~5.7 N; gives a clear ~24 mm tip wrap.
    fext = np.zeros(basis.N)

    p0 = mesh.p.copy()
    frames = [p0.copy()]
    vms = [von_mises_per_node(mesh, basis, np.zeros(basis.N))]
    curve = [(0.0, 0.0, 0.0)]   # (load, tip_dx, tip_dy)
    tip_node = int(np.argmax(mesh.p[1]))   # apex (max Y)

    u = np.zeros(basis.N)
    t0 = time.time()
    for s in range(1, NSTEP + 1):
        f = F_TARGET * s / NSTEP
        fext[:] = 0.0
        fext[xpd] = f / len(xpd)        # +X distributed over patch nodes
        u_try, nit, rn, ok = newton_step(basis, u.copy(), D, fext)
        if not ok:
            print(f"step {s:2d}/{NSTEP} load={f:4.2f}N NOconv |R|={rn:.2e} "
                  f"-> stopping (graceful), keeping converged frames."); break
        u = u_try
        ux = u[basis.nodal_dofs[0]]
        uy = u[basis.nodal_dofs[1]]
        defp = mesh.p + np.vstack([ux, uy])
        frames.append(defp.copy())
        vms.append(von_mises_per_node(mesh, basis, u))
        curve.append((f, ux[tip_node], uy[tip_node]))
        print(f"step {s:2d}/{NSTEP} load={f:4.2f}N  newton={nit:2d} "
              f"|R|={rn:.2e} ok  tip dx={ux[tip_node]:+.2f} dy={uy[tip_node]:+.2f}")
    print(f"solve time {time.time()-t0:.1f}s")

    np.savez(os.path.join(HERE, "results.npz"),
             frames=np.array(frames), vms=np.array(vms),
             tris=mesh.t, curve=np.array(curve),
             E=E_TPU, nu=NU_TPU, F_target=F_TARGET)
    print("wrote results.npz  frames=%d" % len(frames))


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "selftest"
    {"selftest": selftest, "run": run}[mode]()

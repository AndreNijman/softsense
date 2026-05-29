"""Hydrostatic-pressure sanity check on the flooded TPU finger (UNDERWATER FEA).

Question
--------
Does external water at depth measurably stress the TPU finger via hydrostatic
compression? The gripper is FULLY FLOODED (UNDERWATER.md §3): water is in
the Fin Ray rib cavities and on every exterior face simultaneously, so the
TPU sees water at the same pressure on every wetted surface.

Linear elasticity answer (free body): hydrostatic pressure P produces a pure
hydrostatic stress state σ_ij = -P δ_ij, ε_v = -P/K, and von Mises = 0.
The only place deviatoric stress can develop is at the rigid mount-bore
interface, where the PETG/PA12-GF mount holds the TPU and the TPU wants to
contract. A 1D Poisson-restraint bound gives σ_clamp ≲ (1-2ν)·P:

  ν = 0.42  →  σ_clamp ≲ 0.048 MPa  at 30 m  (1/500 of TPU yield ~25 MPa)
  ν = 0.45  →  σ_clamp ≲ 0.030 MPa
  ν = 0.48  →  σ_clamp ≲ 0.012 MPa

This script runs a 2D PLANE-STRAIN FEA on the existing finger section with
uniform hydrostatic pressure tractions on every boundary edge — both the
outer skin AND the inner Fin Ray rib cavities, since the cavities are
flooded too. Plane-strain ARTIFICIALLY constrains εz = 0, which over-
constrains the body (the real finger CAN compress in Z because its front
and back faces are also wetted). So this is a CONSERVATIVE UPPER BOUND on
the real 3D deviatoric stress.

Run:  python fea/scripts/underwater_pressure_probe.py
"""
import json
import os
import sys
import numpy as np
import skfem
from skfem import (MeshTri, Basis, ElementVector, ElementTriP1, FacetBasis,
                   LinearForm, BilinearForm, condense, solve)
from skfem.helpers import grad, transpose, ddot, trace, eye, mul

HERE = os.path.dirname(os.path.abspath(__file__))

# material — Bambu TPU 95A HF in-plane (X-Y), ISO 527 printed specimen. nu bracket
# 0.42..0.48 (Bambu publishes none). Flooded hydrostatic gives vM≈0 regardless of E;
# E only sets the (tiny) bulk-contraction displacement.
E_TPU = 9.8        # MPa  (X-Y, Bambu TDS — replaces old 40 MPa eSUN guess)
NU_LIST = [0.42, 0.45, 0.48]

# depths (m). Seawater ρ = 1025 kg/m³, g = 9.81 m/s² → P = 0.010054 MPa per m.
DEPTHS_M = [0.0, 10.0, 30.0, 100.0, 300.0, 600.0]
RHO_G = 1025.0 * 9.81e-6   # MPa/m


def material(nu):
    mu = E_TPU / (2.0 * (1.0 + nu))
    lam = E_TPU * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    K = E_TPU / (3.0 * (1.0 - 2.0 * nu))
    return mu, lam, K


def load_mesh_and_clamp():
    """Reuse solve_finger.py infrastructure: section mesh + clamp nodes."""
    d = np.load(os.path.join(HERE, "mesh.npz"))
    mesh = MeshTri(d["p"], d["t"])
    lm = json.load(open(os.path.join(HERE, "finger_landmarks.json")))
    C, D = np.array(lm["C"]), np.array(lm["D"])
    rmh = lm["mount_hole_r"]
    p = mesh.p
    bnodes = np.unique(mesh.facets[:, mesh.boundary_facets()])
    def near(pt, r): return np.hypot(p[0] - pt[0], p[1] - pt[1]) <= r + 0.8
    clamp = bnodes[(near(C, rmh) | near(D, rmh))[bnodes]]
    return mesh, lm, clamp


def assemble_forms(mu, lam):
    @LinearForm
    def residual(v, w):
        # linear infinitesimal-strain elasticity (the strain here is tiny)
        du = w["disp"].grad
        eps = 0.5 * (du + transpose(du))
        sig = eye(lam * trace(eps), 2) + 2.0 * mu * eps
        return ddot(sig, grad(v))

    @BilinearForm
    def tangent(u, v, w):
        du = grad(u)
        eps = 0.5 * (du + transpose(du))
        sig = eye(lam * trace(eps), 2) + 2.0 * mu * eps
        return ddot(sig, grad(v))
    return residual, tangent


def hydrostatic_traction(P):
    """Pressure boundary load on the SOLID material: t = -P n where n is the
    outward normal of the solid. Applied uniformly on every boundary facet —
    both the outer skin AND the inner Fin Ray rib cavities (cavities flood)."""
    @LinearForm
    def pload(v, w):
        # v is the test (vector) basis; w.n is the outward unit normal at the facet
        return -P * (w.n[0] * v[0] + w.n[1] * v[1])
    return pload


def von_mises_field(mesh, basis, u, nu):
    @LinearForm
    def vm_proj(v, w):
        du = w["disp"].grad
        eps = 0.5 * (du + transpose(du))
        # plane strain Cauchy stress (linear elastic)
        sxx = (E_TPU / ((1 + nu) * (1 - 2 * nu))) * ((1 - nu) * eps[0, 0] + nu * eps[1, 1])
        syy = (E_TPU / ((1 + nu) * (1 - 2 * nu))) * (nu * eps[0, 0] + (1 - nu) * eps[1, 1])
        sxy = (E_TPU / (1 + nu)) * eps[0, 1]
        szz = nu * (sxx + syy)  # plane strain out-of-plane (only the elastic part)
        vm = (0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2 +
                     6.0 * sxy ** 2)) ** 0.5
        return vm * v
    sb = basis.with_element(ElementTriP1())
    num = vm_proj.assemble(sb, disp=basis.interpolate(u))
    den = LinearForm(lambda v, w: 1.0 + 0.0 * w.x[0]).assemble(sb)
    return num / np.maximum(den, 1e-30)


def hydrostatic_pressure_field(mesh, basis, u, nu):
    """Mean pressure σ_h = (σxx + σyy + σzz)/3 for sanity check vs -P."""
    @LinearForm
    def sh_proj(v, w):
        du = w["disp"].grad
        eps = 0.5 * (du + transpose(du))
        sxx = (E_TPU / ((1 + nu) * (1 - 2 * nu))) * ((1 - nu) * eps[0, 0] + nu * eps[1, 1])
        syy = (E_TPU / ((1 + nu) * (1 - 2 * nu))) * (nu * eps[0, 0] + (1 - nu) * eps[1, 1])
        szz = nu * (sxx + syy)
        return ((sxx + syy + szz) / 3.0) * v
    sb = basis.with_element(ElementTriP1())
    num = sh_proj.assemble(sb, disp=basis.interpolate(u))
    den = LinearForm(lambda v, w: 1.0 + 0.0 * w.x[0]).assemble(sb)
    return num / np.maximum(den, 1e-30)


def run_one(P, nu):
    mesh, lm, clamp_nodes = load_mesh_and_clamp()
    e = ElementVector(ElementTriP1())
    basis = Basis(mesh, e)
    fbasis = FacetBasis(mesh, e, facets=mesh.boundary_facets())
    mu, lam, K = material(nu)
    res, tng = assemble_forms(mu, lam)
    pload = hydrostatic_traction(P)

    nodal = basis.nodal_dofs
    D = nodal[:, clamp_nodes].flatten()

    # one Newton step — problem is linear, so u solves Ku = f_pressure
    u = np.zeros(basis.N)
    K_mat = tng.assemble(basis)
    f = pload.assemble(fbasis)
    R = K_mat @ u - f
    du = solve(*condense(K_mat, -R, D=D))
    u = u + du

    vm = von_mises_field(mesh, basis, u, nu)
    sh = hydrostatic_pressure_field(mesh, basis, u, nu)
    ux = u[nodal[0]]
    uy = u[nodal[1]]
    disp_norm = np.sqrt(ux**2 + uy**2)
    return dict(
        nu=nu, P_MPa=P, K_MPa=K,
        peak_vM_MPa=float(vm.max()),
        median_vM_MPa=float(np.median(vm)),
        mean_sigh_MPa=float(sh.mean()),
        peak_disp_um=float(disp_norm.max() * 1000),  # mm -> μm
        eps_lin_analytical_pct=-100.0 * P / (3 * K),
        sigma_clamp_bound_MPa=(1 - 2 * nu) * P,
    )


def main():
    out = {
        "preface": ("Hydrostatic-pressure sanity check on the flooded TPU finger. "
                    "Plane-strain CONSERVATIVE UPPER BOUND for deviatoric stress "
                    "(real 3D body can also strain in Z, reducing the constraint)."),
        "material": {"E_TPU_MPa": E_TPU, "tpu_strength_MPa_inplane": 27.3,
                     "rho_seawater_kg_m3": 1025.0, "g_m_s2": 9.81},
        "physics_note": ("Free body: σ_ij = -P δ_ij → vM = 0. Only deviatoric "
                         "stress source is the rigid clamp at the mount bores."),
        "runs": [],
    }
    for nu in NU_LIST:
        for depth in DEPTHS_M:
            P = RHO_G * depth
            r = run_one(P, nu)
            r["depth_m"] = depth
            out["runs"].append(r)
            print(f"ν={nu:.2f}  depth={depth:5.0f}m  P={P:.3f}MPa  "
                  f"vM_peak={r['peak_vM_MPa']:.4f}MPa  "
                  f"σ_h={r['mean_sigh_MPa']:+.4f}MPa  "
                  f"|u|={r['peak_disp_um']:.1f}μm  "
                  f"ε_lin={r['eps_lin_analytical_pct']:+.3f}%")
    outdir = os.path.join(os.path.dirname(HERE), "iterations", "_underwater_pressure")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "results.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nwrote {os.path.join(outdir, 'results.json')}")


if __name__ == "__main__":
    main()

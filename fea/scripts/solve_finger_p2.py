"""Quadratic-element (P2 triangle) version of solve_finger.py.

The user-flagged 'volumetric locking' concern is real for the LINEAR-tet
3D solver in iter_harness.py. The shipped 2D precursor in solve_finger.py
uses linear (P1) triangles in plane strain, which is also a locking-prone
choice in the near-incompressible regime (ν → 0.5).

This script repeats solve_finger.py's 2D plane-strain finite-strain solve
(same St-Venant-Kirchhoff material, same BCs, same mesh, same load) but
with QUADRATIC (P2) triangles. P2/P1 elements are stable for the (nearly-)
incompressible problem on a triangulation; if the headline peak vM from the
P1 run survives the switch to P2 the locking concern is empirically bounded.

The headline test answers two questions:

  1. How much does the peak vM change between P1 and P2 at the same
     5.4 N load level on the same mesh?
  2. Does the load-control limit point ≈ 5.7 N shift under P2?
     (Locking would over-stiffen the body, hiding the snap instability;
     a P2 solve closer to the true compressibility should expose it sooner
     or later, depending on which way the locking error goes.)

Usage:
  python fea/scripts/solve_finger_p2.py run        # full load-stepped solve
  python fea/scripts/solve_finger_p2.py compare    # run P1 + P2 + report delta
"""
import json
import os
import sys
import time

import numpy as np
import skfem
from skfem import (MeshTri, Basis, ElementVector, ElementTriP1, ElementTriP2,
                   LinearForm, BilinearForm, condense, solve)
from skfem.helpers import grad, transpose, ddot, trace, eye, mul

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import solve_finger as sf2d   # reuse the BCs / landmarks helpers


# Material (mirror solve_finger.py)
E_TPU = sf2d.E_TPU
NU_TPU = sf2d.NU_TPU
MU = sf2d.MU
LAM = sf2d.LAM


def _I(field):
    return eye(np.ones_like(field[0, 0]), 2)


@LinearForm
def residual(v, w):
    du = w["disp"].grad
    I = _I(du)
    F = du + I
    Egl = 0.5 * (mul(transpose(F), F) - I)
    S = eye(LAM * trace(Egl), 2) + 2.0 * MU * Egl
    P = mul(F, S)
    return ddot(P, grad(v))


@BilinearForm
def tangent(u, v, w):
    du = w["disp"].grad
    I = _I(du)
    F = du + I
    Egl = 0.5 * (mul(transpose(F), F) - I)
    S = eye(LAM * trace(Egl), 2) + 2.0 * MU * Egl
    dF = grad(u)
    dE = 0.5 * (mul(transpose(dF), F) + mul(transpose(F), dF))
    dS = eye(LAM * trace(dE), 2) + 2.0 * MU * dE
    dP = mul(dF, S) + mul(F, dS)
    return ddot(dP, grad(v))


def build_p2():
    mesh = sf2d.load_mesh()
    e = ElementVector(ElementTriP2())
    basis = Basis(mesh, e)
    return mesh, basis


def dofs_of_nodes_p2(basis, nodes):
    """All x/y DOFs for the given P1 vertex indices, in the P2 basis."""
    nodal = basis.nodal_dofs                        # shape (2, n_nodes_p2)
    return nodal[:, nodes].flatten()


def x_dofs_of_nodes_p2(basis, nodes):
    return basis.nodal_dofs[0, nodes]


def vm_per_node_p2(mesh, basis, u):
    """Project element vM to vertex nodes (re-uses solve_finger's pattern)."""
    from skfem import LinearForm as LF
    @LF
    def vm_proj(v, w):
        du = w["disp"].grad
        I = _I(du)
        F = du + I
        Egl = 0.5 * (mul(transpose(F), F) - I)
        S = eye(LAM * trace(Egl), 2) + 2.0 * MU * Egl
        # plane-strain σ_zz = ν (σ_xx + σ_yy) [PK2 ≈ Cauchy at small strain]
        Sxx, Syy, Sxy = S[0, 0], S[1, 1], S[0, 1]
        Szz = NU_TPU * (Sxx + Syy)
        vm = ((Sxx - Syy)**2 + (Syy - Szz)**2 + (Szz - Sxx)**2 + 6 * Sxy**2) ** 0.5 / 2.0**0.5
        return vm * v
    # Use P1 basis for projection (one value per vertex)
    sb = basis.with_element(ElementTriP1())
    num = vm_proj.assemble(sb, disp=basis.interpolate(u))
    @LF
    def one(v, w):
        return 1.0 + 0.0 * w.x[0]
    den = one.assemble(sb)
    return num / np.maximum(den, 1e-30)


def newton_step_p2(basis, u, D, fext, tol=1e-8, maxit=40):
    for it in range(maxit):
        R = residual.assemble(basis, disp=basis.interpolate(u)) - fext
        K = tangent.assemble(basis, disp=basis.interpolate(u))
        du = solve(*condense(K, -R, D=D))
        u = u + du
        rn = np.linalg.norm(R[np.setdiff1d(np.arange(basis.N), D)])
        dn = np.linalg.norm(du)
        if dn < tol * (1 + np.linalg.norm(u)):
            return u, it + 1, rn, True
    return u, maxit, rn, False


def run_p2(NSTEP=24, F_TARGET=5.4):
    """Repeat solve_finger.py's run() with P2 elements. Returns the load-vs-tip
    history + the peak vM at each step + the converged frames."""
    mesh, basis = build_p2()
    clamp_nodes, patch_nodes, lm = sf2d.bc_and_load(mesh, basis.with_element(ElementTriP1()))
    D = dofs_of_nodes_p2(basis, clamp_nodes)
    if len(patch_nodes) == 0:
        raise RuntimeError("empty contact patch")
    xpd = x_dofs_of_nodes_p2(basis, patch_nodes)

    fext = np.zeros(basis.N)
    u = np.zeros(basis.N)
    curve = [(0.0, 0.0, 0.0, 0.0)]   # (load, tip_dx, tip_dy, peak_vm)
    converged_all = True
    t0 = time.time()
    tip_node = int(np.argmax(mesh.p[1]))
    for s in range(1, NSTEP + 1):
        f = F_TARGET * s / NSTEP
        fext[:] = 0.0
        fext[xpd] = f / len(xpd)
        u_try, nit, rn, ok = newton_step_p2(basis, u.copy(), D, fext)
        if not ok:
            print(f"step {s:2d}/{NSTEP} load={f:4.2f}N NOconv |R|={rn:.2e} -> stopping")
            converged_all = False
            break
        u = u_try
        ux = u[basis.nodal_dofs[0]]
        uy = u[basis.nodal_dofs[1]]
        vm = vm_per_node_p2(mesh, basis, u)
        curve.append((f, float(ux[tip_node]), float(uy[tip_node]), float(vm.max())))
        print(f"step {s:2d}/{NSTEP} load={f:4.2f}N newton={nit:2d} "
              f"|R|={rn:.2e} ok  tip dx={ux[tip_node]:+.2f} dy={uy[tip_node]:+.2f}  "
              f"peak_vM={vm.max():.3f} MPa")
    dt = time.time() - t0

    final = curve[-1]
    return dict(
        element="ElementTriP2 (quadratic plane-strain triangle)",
        n_dof=int(basis.N),
        n_steps_reached=len(curve) - 1,
        F_target_N=F_TARGET,
        converged_all=converged_all,
        max_load_reached_N=float(final[0]),
        tip_dx_at_max=float(final[1]),
        tip_dy_at_max=float(final[2]),
        peak_vm_MPa_at_max=float(final[3]),
        runtime_s=round(dt, 1),
        curve=curve,
    )


def compare():
    """Run BOTH P1 (the original) and P2 (this script) and report the delta."""
    print("=== P1 baseline (re-running solve_finger.run analogue) ===")
    # Run the P1 version via solve_finger's existing infrastructure
    # solve_finger.run() writes results.npz; let's just re-implement a quick
    # P1 step that mirrors run_p2 so we get clean diagnostics.
    mesh, basis_p1 = sf2d.build()
    clamp_nodes, patch_nodes, lm = sf2d.bc_and_load(mesh, basis_p1)
    D1 = sf2d.dofs_of_nodes(basis_p1, clamp_nodes)
    xpd1 = sf2d.x_dofs_of_nodes(basis_p1, patch_nodes)
    fext = np.zeros(basis_p1.N)
    u = np.zeros(basis_p1.N)
    F_TARGET = 5.4
    NSTEP = 24
    tip_node = int(np.argmax(mesh.p[1]))
    p1_curve = [(0.0, 0.0, 0.0, 0.0)]
    p1_conv = True
    for s in range(1, NSTEP + 1):
        f = F_TARGET * s / NSTEP
        fext[:] = 0.0
        fext[xpd1] = f / len(xpd1)
        u_try, nit, rn, ok = sf2d.newton_step(basis_p1, u.copy(), D1, fext)
        if not ok:
            p1_conv = False
            break
        u = u_try
        ux = u[basis_p1.nodal_dofs[0]]; uy = u[basis_p1.nodal_dofs[1]]
        vm = sf2d.von_mises_per_node(mesh, basis_p1, u)
        p1_curve.append((f, float(ux[tip_node]), float(uy[tip_node]), float(vm.max())))
        print(f"  P1 step {s:2d}/{NSTEP} load={f:4.2f}N peak_vM={vm.max():.3f}")
    p1_final = p1_curve[-1]
    p1 = dict(element="ElementTriP1 (linear)", n_dof=int(basis_p1.N),
              n_steps_reached=len(p1_curve) - 1, F_target_N=F_TARGET,
              converged_all=p1_conv, max_load_reached_N=float(p1_final[0]),
              peak_vm_MPa_at_max=float(p1_final[3]),
              tip_dx_at_max=float(p1_final[1]), tip_dy_at_max=float(p1_final[2]),
              curve=p1_curve)

    print()
    print("=== P2 run ===")
    p2 = run_p2()

    delta_vm = (p2["peak_vm_MPa_at_max"] - p1["peak_vm_MPa_at_max"]) / max(p1["peak_vm_MPa_at_max"], 1e-9) * 100
    delta_dx = p2["tip_dx_at_max"] - p1["tip_dx_at_max"]

    return dict(
        material=dict(E_TPU=E_TPU, NU=NU_TPU, mu=MU, lambda_=LAM),
        p1=p1,
        p2=p2,
        delta=dict(
            peak_vM_pct_change=round(delta_vm, 2),
            tip_dx_change_mm=round(delta_dx, 3),
            both_converged=p1["converged_all"] and p2["converged_all"],
        ),
        interpretation=[
            f"P1 (linear) reached F = {p1['max_load_reached_N']:.2f} N with "
            f"peak vM = {p1['peak_vm_MPa_at_max']:.3f} MPa.",
            f"P2 (quadratic) reached F = {p2['max_load_reached_N']:.2f} N with "
            f"peak vM = {p2['peak_vm_MPa_at_max']:.3f} MPa.",
            f"Δpeak vM (P2 vs P1) = {delta_vm:+.1f} % at the same load level. "
            "If P2 gives a SUBSTANTIALLY different peak vM than P1 then the P1 "
            "(linear-tet equivalent) is locking and the headline 2D peak vM is "
            "unreliable. If P2 agrees with P1 within ~10 %, the locking is not "
            "the dominant error.",
        ],
    )


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "run":
        out = run_p2()
        outpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "iterations", "_solve_finger_p2.json")
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        json.dump(out, open(outpath, "w"), indent=2)
        print(f"\nwrote {outpath}")
    elif mode == "compare":
        out = compare()
        print()
        print("=== Summary ===")
        for line in out["interpretation"]:
            print(f"  - {line}")
        outpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "iterations", "_p1_vs_p2.json")
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        json.dump(out, open(outpath, "w"), indent=2)
        print(f"\nwrote {outpath}")
    else:
        print(f"unknown mode: {mode}")
        sys.exit(2)

"""Genuine 3D linear-elastic FEA of one crown gear tooth + base disk sector.

Replaces the 2D plane-stress single-station model (`gear_fea.py`) and the
2D radial-stations model (`gear_fea_radial.py`) with an actual 3D solid
solve of the crown FACE tooth. The 2D models can't capture:

  * The base-disk bending compliance (the disk is not infinitely stiff under
    the tooth's bending moment — some of the deformation lives in the disk,
    relieving the tooth root).
  * The radially-varying tangential thickness s_root(r) and its effect on
    the moment-of-inertia of the tooth bending cross-section as a 3D solid.
  * The effect of neighbour-tooth restraint at the base disk (in this model
    we only solve ONE tooth + a ring sector of width = one pitch, with
    periodic-like BCs on the sector ends; sharing of load with neighbour
    teeth is NOT captured -- if anything that makes this an upper bound on
    stress, i.e. T_safe(3D) lower bound).

What is captured:
  * Real 3D linear-elastic deformation of the tooth + disk under a
    tangential face-load on the tooth top edge.
  * Variable s_root(r) along the radial direction.
  * Base-disk compliance under the tooth's bending reaction.

Method:
  * Build the geometry parametrically with build123d (the same toolchain as
    `gripper.py`), export STEP, mesh with gmsh as 3D linear tets.
  * Assemble the same 6x6 D matrix linear-elastic FEA used in iter_harness
    (without contact, without corotational — small-rotation linear case).
  * Clamp the disk bottom face. Apply a uniform tangential traction on the
    tooth top face (resultant = F_REF). Solve once.
  * Compute peak von Mises at the root band and rescale linearly to find
    T_safe(crown_3d) such that peak vM = SIGMA_ALLOW.

This is STILL not a full validation:
  * Linear elasticity only (no plasticity, no fracture).
  * Frictionless mesh contact line not modelled (uniform pressure on top
    face = the worst-case load distribution; actual contact runs as a line
    across the radial extent and sweeps).
  * Straight-flank face teeth — same as the shipped CAD; involute-vs-straight-
    flank distinction is moot here.
  * PA12-GF FDM print anisotropy and layer-adhesion knock-down are not modelled
    (the SIGMA_ALLOW = 30 MPa already includes a 30-40 % FDM derate from the
    PA12-GF bulk ~50-65 MPa per BOM.md).

The bench-grade ceiling is still `motor/BENCH_TEST.md`.
"""
import json
import math
import os
import sys
import tempfile

import numpy as np
import gmsh
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gripper as g  # noqa: E402

from build123d import (  # noqa: E402
    BuildPart, Box, Cylinder, Plane, Polygon, Compound, Part,
    Location, Mode, export_step, RegularPolygon, Pos, Rot, Axis,
    extrude,
)


HERE = os.path.dirname(os.path.abspath(__file__))
ITER = os.path.join(os.path.dirname(HERE), "iterations")

# Material (PA12-GF, same allowable as gear_fea.py)
E_GF = 3500.0
NU = 0.40
SIGMA_ALLOW = 30.0
F_REF = 10.0  # N tangential test load

# Geometry from gripper.py
CROWN_TEETH = g.CROWN_TEETH
CROWN_RC = g.CROWN_RC
CROWN_TOOTH_H = g.CROWN_TOOTH_H
CROWN_FACE_H = g.CROWN_FACE_H
PINION_T = g.PINION_T              # mating face = loaded tooth band
DISK_T = 4.0                       # local disk thickness around the tooth (mm)
LAND_FRAC = 0.5                    # tooth tangential thickness fraction


def build_geometry_step(stepfile):
    """Build a 3D solid: a ring sector (one tooth pitch wide) with one
    crown tooth standing on it. Returns path to the STEP."""
    r_in = CROWN_RC - CROWN_TOOTH_H
    r_out = CROWN_RC + CROWN_TOOTH_H
    step_ang = 2 * math.pi / CROWN_TEETH       # full pitch angle (rad)
    half_ang = step_ang / 2.0
    tooth_half = LAND_FRAC * half_ang          # tooth occupies LAND_FRAC of pitch

    # Sector polygon for the disk (vertices in xy plane, sweep along z)
    # We approximate the curved inner+outer radii with N straight segments.
    Nseg = 12
    angs = np.linspace(-half_ang, half_ang, Nseg + 1)
    inner = [(r_in * math.cos(a), r_in * math.sin(a)) for a in angs]
    outer = [(r_out * math.cos(a), r_out * math.sin(a)) for a in angs[::-1]]
    disk_poly_pts = inner + outer

    angs_t = np.linspace(-tooth_half, tooth_half, Nseg + 1)
    inner_t = [(r_in * math.cos(a), r_in * math.sin(a)) for a in angs_t]
    outer_t = [(r_out * math.cos(a), r_out * math.sin(a)) for a in angs_t[::-1]]
    tooth_poly_pts = inner_t + outer_t

    with BuildPart() as p:
        # Disk: extrude from z=0 to z=DISK_T
        with BuildPart(Plane.XY) as disk_sk:
            from build123d import BuildSketch, Polygon as Poly2D, make_face
            with BuildSketch(Plane.XY) as sk:
                Poly2D(*disk_poly_pts)
            extrude(amount=DISK_T)
        # Tooth: extrude from z=DISK_T to z=DISK_T+CROWN_FACE_H
        with BuildPart(Plane.XY.offset(DISK_T)) as tooth_sk:
            from build123d import BuildSketch, Polygon as Poly2D
            with BuildSketch(Plane.XY.offset(DISK_T)) as sk2:
                Poly2D(*tooth_poly_pts)
            extrude(amount=CROWN_FACE_H)
    export_step(p.part, stepfile)


def mesh_step(stepfile, mesh_max=0.6, mesh_min=0.25):
    """Mesh the STEP file as 3D linear tets. Returns (nodes (N,3), tets (M,4),
    tags for the disk-bottom and tooth-top faces)."""
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.open(stepfile)
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_max)
    gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_min)
    gmsh.model.mesh.generate(3)
    ntags, ncoords, _ = gmsh.model.mesh.getNodes()
    nodes = ncoords.reshape(-1, 3)
    tag2i = {int(t): i for i, t in enumerate(ntags)}
    etypes, _, enodes = gmsh.model.mesh.getElements(dim=3)
    tets = None
    for et, en in zip(etypes, enodes):
        if et == 4:                     # linear tet
            tets = np.array([[tag2i[int(n)] for n in tet]
                             for tet in en.reshape(-1, 4)], dtype=np.int64)
    if tets is None:
        gmsh.finalize()
        raise RuntimeError("no linear tets in mesh")
    gmsh.finalize()
    return nodes, tets


def Dmat(E, nu):
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    D = np.zeros((6, 6)); D[:3, :3] = lam
    D[0, 0] = D[1, 1] = D[2, 2] = lam + 2 * mu
    D[3, 3] = D[4, 4] = D[5, 5] = mu
    return D


def solve_linear(nodes, tets, F_top_total, top_z):
    """Linear-elastic 3D solve: clamp disk bottom (z=0), apply uniform
    tangential force (in +y direction; the rotation direction) on tooth top
    face nodes (z near top_z). Returns peak von Mises across all elements."""
    D6 = Dmat(E_GF, NU)
    nn = nodes.shape[0]
    ndof = nn * 3
    Ntet = tets.shape[0]

    # Per-element geometry, B matrix, K
    X = nodes[tets]
    Jm = np.stack([X[:, 1] - X[:, 0], X[:, 2] - X[:, 0], X[:, 3] - X[:, 0]], axis=2)
    invJm = np.linalg.inv(Jm)
    V = np.abs(np.linalg.det(Jm)) / 6.0
    # Flip negative-volume tets
    neg = np.linalg.det(Jm) < 0
    if neg.any():
        tets[neg] = tets[neg][:, [0, 2, 1, 3]]
        X = nodes[tets]
        Jm = np.stack([X[:, 1] - X[:, 0], X[:, 2] - X[:, 0], X[:, 3] - X[:, 0]], axis=2)
        invJm = np.linalg.inv(Jm)
        V = np.abs(np.linalg.det(Jm)) / 6.0

    dNref = np.array([[-1, -1, -1], [1, 0, 0], [0, 1, 0], [0, 0, 1]], float)
    dNdx = np.einsum('ij,njk->nik', dNref, invJm)
    B = np.zeros((Ntet, 6, 12))
    for i in range(4):
        gx, gy, gz = dNdx[:, i, 0], dNdx[:, i, 1], dNdx[:, i, 2]
        c = 3 * i
        B[:, 0, c] = gx; B[:, 1, c + 1] = gy; B[:, 2, c + 2] = gz
        B[:, 3, c] = gy; B[:, 3, c + 1] = gx
        B[:, 4, c + 1] = gz; B[:, 4, c + 2] = gy
        B[:, 5, c] = gz; B[:, 5, c + 2] = gx
    Ke = np.einsum('nki,kl,nlj->nij', B, D6, B) * V[:, None, None]
    edof = (tets[:, :, None] * 3 + np.arange(3)[None, None, :]).reshape(Ntet, 12)
    I = np.repeat(edof, 12, axis=1).reshape(-1)
    J = np.tile(edof, (1, 12)).reshape(-1)
    K = coo_matrix((Ke.reshape(-1), (I, J)), shape=(ndof, ndof)).tocsr()

    # BCs: clamp disk bottom (z near 0)
    z_min = nodes[:, 2].min()
    bottom = np.where(nodes[:, 2] < z_min + 1e-6)[0]
    fixed = np.zeros(ndof, bool)
    for d in range(3):
        fixed[3 * bottom + d] = True
    free = np.where(~fixed)[0]

    # Load: uniform tangential force on tooth top face nodes (z near top_z)
    # The tangential direction at angle 0 is +y. We apply force in +y.
    tooth_top = np.where(nodes[:, 2] > top_z - 1e-6)[0]
    if len(tooth_top) == 0:
        raise RuntimeError("no tooth-top nodes found")
    fext = np.zeros(ndof)
    fext[3 * tooth_top + 1] = F_top_total / len(tooth_top)     # +y direction

    # Solve
    Kf = K[free][:, free].tocsc()
    u = np.zeros(ndof)
    u[free] = spsolve(Kf, fext[free])

    # Element strain → stress → vM
    ue = u[edof]                                         # (Ntet, 12)
    eps = np.einsum('nij,nj->ni', B, ue)                 # (Ntet, 6)
    sig = eps @ D6.T
    sx, sy, sz, sxy, syz, szx = sig.T
    vm = np.sqrt(0.5 * ((sx - sy)**2 + (sy - sz)**2 + (sz - sx)**2)
                 + 3 * (sxy**2 + syz**2 + szx**2))

    # Peak vM in the "root band": elements near z = DISK_T (the tooth root).
    elem_z_mean = nodes[tets][:, :, 2].mean(axis=1)
    root_band = (elem_z_mean > DISK_T - 0.3 * CROWN_FACE_H) & \
                (elem_z_mean < DISK_T + 0.4 * CROWN_FACE_H)
    vm_peak_root = float(vm[root_band].max()) if root_band.any() else float(vm.max())
    vm_peak_overall = float(vm.max())
    return dict(vm_peak_root=vm_peak_root, vm_peak_overall=vm_peak_overall,
                ndof=ndof, ntet=Ntet, nnodes=nn,
                root_band_elements=int(root_band.sum()),
                top_nodes=int(len(tooth_top)),
                bottom_nodes=int(len(bottom)))


def run():
    with tempfile.NamedTemporaryFile(suffix=".step", delete=False) as f:
        stepfile = f.name
    try:
        build_geometry_step(stepfile)
        nodes, tets = mesh_step(stepfile, mesh_max=0.6, mesh_min=0.25)
    finally:
        if os.path.exists(stepfile):
            os.unlink(stepfile)

    # Tooth top is at z = DISK_T + CROWN_FACE_H
    top_z = DISK_T + CROWN_FACE_H
    sol = solve_linear(nodes, tets, F_REF, top_z)

    # Linear scaling: peak vM is linear in F. Find F_allow such that vM = SIGMA_ALLOW.
    F_allow_tooth = SIGMA_ALLOW / sol["vm_peak_root"] * F_REF
    # Crown contact-force lever = PINION_RP (same as gear_fea.py)
    T_safe_3d = F_allow_tooth * g.PINION_RP / 1000.0

    return dict(
        geometry=dict(CROWN_TEETH=CROWN_TEETH, CROWN_RC=CROWN_RC,
                      CROWN_TOOTH_H=CROWN_TOOTH_H, CROWN_FACE_H=CROWN_FACE_H,
                      DISK_T=DISK_T, LAND_FRAC=LAND_FRAC,
                      PINION_T_loaded=PINION_T),
        material=dict(E=E_GF, NU=NU, SIGMA_ALLOW=SIGMA_ALLOW),
        mesh=dict(nnodes=sol["nnodes"], ntet=sol["ntet"], ndof=sol["ndof"],
                  root_band_elements=sol["root_band_elements"],
                  top_loaded_nodes=sol["top_nodes"],
                  bottom_clamped_nodes=sol["bottom_nodes"]),
        load=dict(F_ref_tangential_N=F_REF, lever_mm=g.PINION_RP),
        peak_vM=dict(root_band_MPa=round(sol["vm_peak_root"], 3),
                     overall_MPa=round(sol["vm_peak_overall"], 3)),
        F_allow_tooth_N=round(F_allow_tooth, 2),
        T_safe_input_Nm=round(T_safe_3d, 4),
        interpretation=[
            f"3D linear-elastic FEA: {sol['ntet']} tets / {sol['ndof']} DOF.",
            f"Geometry: one crown tooth + a ring sector ({2*math.pi/CROWN_TEETH*180/math.pi:.1f}° pitch wide), "
            f"r ∈ [{CROWN_RC-CROWN_TOOTH_H:.1f}, {CROWN_RC+CROWN_TOOTH_H:.1f}] mm, "
            f"disk thickness {DISK_T} mm, tooth face height {CROWN_FACE_H} mm.",
            f"Disk bottom clamped (z=0); tangential force {F_REF} N applied uniformly to the tooth top face (z={DISK_T+CROWN_FACE_H} mm), +y direction.",
            f"Peak vM in the root band = {sol['vm_peak_root']:.2f} MPa at the 10 N reference load.",
            f"Linear-scale to SIGMA_ALLOW = {SIGMA_ALLOW} MPa: F_allow = {F_allow_tooth:.1f} N tooth tangential force.",
            f"T_safe(crown, 3D) = F_allow × PINION_RP / 1000 = {T_safe_3d:.4f} N·m input-shaft torque.",
            f"Comparison: gear_fea.py (single-station 2D) gives T_safe = 0.0340 N·m; "
            f"gear_fea_radial.py (radial 2D inner-edge bound) gives T_safe = 0.0131 N·m; "
            f"this 3D solve gives T_safe = {T_safe_3d:.4f} N·m.",
            "CAVEATS: linear-elastic (no plasticity, no fracture); no neighbour-tooth "
            "load sharing (the sector is one pitch wide with free-ish ends, so this is "
            "conservative); uniform tangential traction on the tooth top (a real moving "
            "contact line is non-uniform); straight-flank tooth shape (will edge-load "
            "and gall in PA12-GF in a real mesh, not roll cleanly). The bench-grade "
            "ceiling remains the printed-coupon torque-to-failure test in motor/BENCH_TEST.md.",
        ],
    )


if __name__ == "__main__":
    out = run()
    print("=== Crown-gear face-tooth 3D FEA ===")
    print(f"  mesh: {out['mesh']['nnodes']} nodes / {out['mesh']['ntet']} tets / {out['mesh']['ndof']} DOF")
    print(f"  geometry: CROWN_RC={out['geometry']['CROWN_RC']}  "
          f"CROWN_TOOTH_H={out['geometry']['CROWN_TOOTH_H']}  "
          f"CROWN_FACE_H={out['geometry']['CROWN_FACE_H']}  "
          f"DISK_T={out['geometry']['DISK_T']}")
    print(f"  peak vM (root band, @ F={out['load']['F_ref_tangential_N']} N) "
          f"= {out['peak_vM']['root_band_MPa']:.2f} MPa")
    print(f"  -> F_allow = {out['F_allow_tooth_N']:.1f} N tooth force")
    print(f"  -> T_safe(crown, 3D) = {out['T_safe_input_Nm']:.4f} N·m input-shaft torque")
    print()
    for line in out["interpretation"]:
        print(f"  - {line}")
    outpath = os.path.join(ITER, "_gear_fea_3d.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    json.dump(out, open(outpath, "w"), indent=2)
    print(f"\nwrote {outpath}")

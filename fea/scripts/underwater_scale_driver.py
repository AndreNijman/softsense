"""Scale-aware driver for the underwater FEA scripts (self-similar GRIPPER_SCALE study).

Runs the underwater crush-3D and pressure-probe analyses at a single GRIPPER_SCALE
WITHOUT modifying gripper.py or the shared iter_harness.py / the original underwater
scripts. It does this by importing the underwater modules as libraries and applying
two thin monkeypatches so the mesh TOPOLOGY is identical at every scale (only the
geometry grows ×k). This isolates the genuine similitude prediction from numerical
artifacts:

  1. Z-span: the crush script hardcodes Z0,Z1 = 13,23 (the 1x finger thickness).
     The 2D section already scales in XY via iter_harness.regen_section (it reads
     gripper.FR_BLADE_LEN etc., all ×SCALE). We rebind Z0,Z1 to the actual scaled
     finger thickness gripper.Z_FINGER0 .. +gripper.T_FINGER so the extrusion is
     self-similar. NLAYERS is left fixed → Z element count identical at every scale.

  2. In-plane mesh density: iter_harness uses fixed MESH_MIN/MAX = 0.5,1.3 mm. On a
     ×k part that is a RELATIVELY finer mesh (k× more triangles), which would resolve
     the clamp stress concentration better and FAKE a vM-vs-scale trend. We scale
     MESH_MIN/MAX ×k so the element topology (triangle count + relative size) is
     identical across scales. At SCALE=1.0 this is a no-op → 1x baseline unchanged.

For the 2D probe (which loads a baked, scale-free mesh.npz and never imports gripper)
we scale the loaded node coords AND the clamp landmarks (C, D, mount_hole_r) ×k in a
wrapper, so the geometry is self-similar. Its peak vM is the pressure-only clamp bound
~(1-2ν)·P — scale-free by inspection — so we expect identical vM and ×k displacement.

Usage (run ONE scale per process; SCALE is read at gripper import time):
    GRIPPER_SCALE=1.0 PYTHONPATH=/home/andre/Projects/softsense \
        python fea/scripts/underwater_scale_driver.py <out_dir>

Writes <out_dir>/underwater_crush_3d.json and <out_dir>/underwater_pressure_probe.json.
"""
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def run_crush(out_dir, scale):
    """Run the 3D trapped-air crush at the current GRIPPER_SCALE."""
    import gripper
    import iter_harness as ih
    import underwater_crush_3d as uc

    # --- patch 2: keep mesh topology identical across scales ---
    ih.MESH_MIN = uc.MESH_MIN * scale
    ih.MESH_MAX = uc.MESH_MAX * scale

    # --- patch 1: self-similar extrusion (scaled finger thickness, fixed NLAYERS) ---
    uc.Z0 = float(gripper.Z_FINGER0)
    uc.Z1 = float(gripper.Z_FINGER0 + gripper.T_FINGER)
    # crush script also has its own MESH_MIN/MAX literals used only for printing;
    # the actual mesh is built by ih.regen_section, so the ih patch above is what matters.
    uc.MESH_MIN = ih.MESH_MIN
    uc.MESH_MAX = ih.MESH_MAX

    t0 = time.time()
    p2d, tris, lm, workdir = uc.build_section_mesh()
    outer_edges, inner_edges, _, _, edge_outward_n2 = uc.classify_2d_boundary(p2d, tris)
    nodes, tets, N2 = uc.build_tets_3d(p2d, tris)
    K, B, V, edof = uc.assemble_stiffness(nodes, tets)
    faces_tagged = uc.enumerate_boundary_faces_with_normals(
        p2d, tris, outer_edges, inner_edges, edge_outward_n2, N2)
    clamp_d, n_clamp_2d = uc.clamp_dofs(nodes, lm, N2)
    nrows = nodes.shape[0] * 3

    out = {
        "scale": scale,
        "Z_span": [uc.Z0, uc.Z1],
        "mesh_min_max": [uc.MESH_MIN, uc.MESH_MAX],
        "mesh": {"n_nodes_2d": int(p2d.shape[0]), "n_tris": int(tris.shape[0]),
                 "n_nodes_3d": int(nodes.shape[0]), "n_tets": int(tets.shape[0]),
                 "n_layers": uc.NLAYERS, "ndof": int(nrows)},
        "material": {"E_TPU": uc.E_TPU, "nu": uc.NU, "yield": uc.TPU_YIELD},
        "load_case": "TRAPPED AIR — outer skin (perimeter + ±Z silhouette) wetted at "
                     "P_depth; inner cell walls traction-free",
        "runs": [],
    }

    contact_x = lm.get("contact_x", float(p2d[:, 0].min()))
    base_y, blade_len = lm["base_y"], lm["blade_len"]
    y0 = base_y + 0.30 * blade_len
    y1 = base_y + 0.70 * blade_len
    cmask_3d = ((nodes[:, 0] < contact_x + 1.5 * scale) &
                (nodes[:, 1] > y0) & (nodes[:, 1] < y1))

    # flooded sanity at 100 m: must give vM≈0
    P_check = uc.RHO_G * 100.0
    f_fl, st_fl = uc.pressure_load_vector(nodes, faces_tagged, p2d, outer_edges,
                                          N2, P_check, lm, flooded=True)
    u_fl = uc.solve_linear(K, f_fl, clamp_d, nrows)
    vm_fl, _ = uc.von_mises_per_tet(B, V, u_fl, edof)
    out["flooded_sanity"] = {
        "depth_m": 100.0,
        "f_net": st_fl["f_net"],
        "peak_vM_MPa": float(vm_fl.max()),
        "peak_disp_um": float(np.linalg.norm(u_fl.reshape(-1, 3), axis=1).max() * 1000),
    }
    print(f"  [scale {scale}] flooded sanity vM_peak = {float(vm_fl.max()):.5f} MPa "
          f"(expect ~0); |u| = {out['flooded_sanity']['peak_disp_um']:.1f} μm")

    for depth in uc.DEPTHS_M:
        P = uc.RHO_G * depth
        f, stats = uc.pressure_load_vector(nodes, faces_tagged, p2d, outer_edges, N2, P, lm)
        u = uc.solve_linear(K, f, clamp_d, nrows)
        vm_tet, sig = uc.von_mises_per_tet(B, V, u, edof)
        disp = u.reshape(-1, 3)
        disp_norm = np.linalg.norm(disp, axis=1)
        contact_disp_um = float(disp_norm[cmask_3d].max() * 1000) if cmask_3d.any() else 0.0
        r = dict(
            depth_m=depth, P_MPa=P,
            peak_vM_MPa=float(vm_tet.max()),
            median_vM_MPa=float(np.median(vm_tet)),
            peak_disp_um=float(disp_norm.max() * 1000),
            contact_wall_disp_um=contact_disp_um,
            margin_to_yield=float(uc.TPU_YIELD / max(vm_tet.max(), 1e-9)),
            survives=bool(vm_tet.max() < uc.TPU_YIELD),
        )
        out["runs"].append(r)
        print(f"  [scale {scale}] depth={depth:5.0f}m P={P:.3f}MPa "
              f"vM_peak={r['peak_vM_MPa']:7.3f}MPa "
              f"contact_disp={contact_disp_um:8.1f}μm margin={r['margin_to_yield']:5.1f}× "
              f"{'PASS' if r['survives'] else 'FAIL'}")

    # analytic yield depth: vM is linear in depth → vM = slope*depth; yield at TPU_YIELD
    nz = [r for r in out["runs"] if r["depth_m"] > 0]
    slope = np.mean([r["peak_vM_MPa"] / r["depth_m"] for r in nz])
    out["vM_slope_MPa_per_m"] = float(slope)
    out["yield_depth_m"] = float(uc.TPU_YIELD / slope)
    out["runtime_s"] = time.time() - t0

    path = os.path.join(out_dir, "underwater_crush_3d.json")
    json.dump(out, open(path, "w"), indent=2)
    print(f"  wrote {path}  (yield depth {out['yield_depth_m']:.1f} m, "
          f"vM slope {slope:.4f} MPa/m)")
    return out


def run_probe(out_dir, scale):
    """Run the 2D flooded pressure-probe at the current scale by scaling the baked
    mesh + landmarks ×k (the probe module itself is scale-free)."""
    import skfem
    from skfem import (MeshTri, Basis, ElementVector, ElementTriP1, FacetBasis,
                       LinearForm, solve, condense)
    import underwater_pressure_probe as up

    d = np.load(os.path.join(HERE, "mesh.npz"))
    p_scaled = d["p"] * scale                       # (2, N) node coords ×k
    mesh = MeshTri(p_scaled, d["t"])
    lm = json.load(open(os.path.join(HERE, "finger_landmarks.json")))
    C = np.array(lm["C"]) * scale
    D = np.array(lm["D"]) * scale
    rmh = lm["mount_hole_r"] * scale

    e = ElementVector(ElementTriP1())

    def run_one(P, nu):
        basis = Basis(mesh, e)
        fbasis = FacetBasis(mesh, e, facets=mesh.boundary_facets())
        mu, lam, K = up.material(nu)
        res, tng = up.assemble_forms(mu, lam)
        pload = up.hydrostatic_traction(P)
        nodal = basis.nodal_dofs
        p = mesh.p
        bnodes = np.unique(mesh.facets[:, mesh.boundary_facets()])

        def near(pt, r):
            return np.hypot(p[0] - pt[0], p[1] - pt[1]) <= r + 0.8 * scale
        clamp = bnodes[(near(C, rmh) | near(D, rmh))[bnodes]]
        Dbc = nodal[:, clamp].flatten()

        u = np.zeros(basis.N)
        K_mat = tng.assemble(basis)
        f = pload.assemble(fbasis)
        R = K_mat @ u - f
        du = solve(*condense(K_mat, -R, D=Dbc))
        u = u + du
        vm = up.von_mises_field(mesh, basis, u, nu)
        sh = up.hydrostatic_pressure_field(mesh, basis, u, nu)
        ux, uy = u[nodal[0]], u[nodal[1]]
        disp_norm = np.sqrt(ux ** 2 + uy ** 2)
        return dict(
            nu=nu, P_MPa=P, K_MPa=K,
            peak_vM_MPa=float(vm.max()),
            median_vM_MPa=float(np.median(vm)),
            mean_sigh_MPa=float(sh.mean()),
            peak_disp_um=float(disp_norm.max() * 1000),
            eps_lin_analytical_pct=-100.0 * P / (3 * K),
            sigma_clamp_bound_MPa=(1 - 2 * nu) * P,
            n_clamp=int(clamp.size),
        )

    out = {
        "scale": scale,
        "preface": ("Hydrostatic-pressure sanity check on the flooded TPU finger, "
                    "self-similar scale study. Mesh + clamp landmarks scaled ×k; "
                    "plane-strain CONSERVATIVE UPPER BOUND for deviatoric stress."),
        "material": {"E_TPU_MPa": up.E_TPU, "tpu_strength_MPa_inplane": 27.3,
                     "rho_seawater_kg_m3": 1025.0, "g_m_s2": 9.81},
        "physics_note": ("Free body: σ_ij = -P δ_ij → vM = 0. Only deviatoric source is "
                         "the rigid clamp at the mount bores; that bound ~(1-2ν)·P is "
                         "scale-free, so vM is scale-invariant and displacement scales ×k."),
        "runs": [],
    }
    for nu in up.NU_LIST:
        for depth in up.DEPTHS_M:
            P = up.RHO_G * depth
            r = run_one(P, nu)
            r["depth_m"] = depth
            out["runs"].append(r)
            print(f"  [scale {scale}] ν={nu:.2f} depth={depth:5.0f}m P={P:.3f}MPa "
                  f"vM_peak={r['peak_vM_MPa']:.4f}MPa σ_h={r['mean_sigh_MPa']:+.4f} "
                  f"|u|={r['peak_disp_um']:.1f}μm")

    path = os.path.join(out_dir, "underwater_pressure_probe.json")
    json.dump(out, open(path, "w"), indent=2)
    print(f"  wrote {path}")
    return out


def main():
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    scale = float(os.environ.get("GRIPPER_SCALE", "1.0"))
    print(f"=== underwater scale driver: GRIPPER_SCALE={scale} → {out_dir} ===")
    run_crush(out_dir, scale)
    run_probe(out_dir, scale)


if __name__ == "__main__":
    main()

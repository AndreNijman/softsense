"""Field-plot renders for the underwater FEA cases.

Two output sheets in fea/pictures/:

  underwater_pressure_FEA.png — FLOODED case (pressure on every TPU
    surface, inside & outside the Fin Ray cells, simultaneously). Shows
    the rest mesh + deformed mesh at 30/100/300 m, colored by von Mises.
    Story: vM ≈ 0 everywhere; finger just uniformly shrinks.

  underwater_crush_FEA.png — TRAPPED-AIR worst case (external water
    only; cells at 1 atm). Top row: 2D plane-strain (under-estimates
    the load — εz forced to 0). Bottom row: 3D mid-Z slice (correct;
    shows the foam-collapse mode the 2D missed).

Reuses the FEA assembly from the existing analysis scripts.

Run:  python fea/scripts/render_underwater_fields.py
"""
import json
import os
import sys
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation

import skfem
from skfem import (MeshTri, Basis, ElementVector, ElementTriP1, FacetBasis,
                   LinearForm, BilinearForm, condense, solve)
from skfem.helpers import grad, transpose, ddot, trace, eye, mul

import scipy.sparse as sp
import scipy.sparse.linalg as spla

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
PICS = os.path.join(ROOT, "fea", "pictures")

# ----- material -----
E_TPU = 40.0
NU = 0.45
TPU_YIELD = 25.0

# ----- depths to render -----
DEPTHS_2D_FLOOD = [30.0, 100.0, 300.0]
DEPTHS_2D_CRUSH = [10.0, 30.0, 100.0]
DEPTHS_3D_CRUSH = [10.0, 30.0, 100.0]

RHO_G = 1025.0 * 9.81e-6


# =============== 2D solve infrastructure ===============
def material():
    mu = E_TPU / (2.0 * (1.0 + NU))
    lam = E_TPU * NU / ((1.0 + NU) * (1.0 - 2.0 * NU))
    return mu, lam


def load_mesh_2d():
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


def classify_2d_loops(mesh):
    """Return outer_facets, inner_facets (skfem facet indices)."""
    p = mesh.p
    bfacets = mesh.boundary_facets()
    edges = mesh.facets[:, bfacets].T
    adj = {}
    for fi, (a, b) in zip(bfacets, edges):
        adj.setdefault(int(a), []).append((int(b), int(fi)))
        adj.setdefault(int(b), []).append((int(a), int(fi)))
    visited = set()
    loops = []
    for start in adj:
        if start in visited:
            continue
        seq, facets, prev, cur = [start], [], None, start
        while True:
            nbrs = adj[cur]
            cand = ([nbrs[0]] if prev is None
                    else [(n, f) for n, f in nbrs if n != prev])
            if not cand:
                break
            nxt_n, nxt_f = cand[0]
            facets.append(nxt_f)
            if nxt_n == start:
                break
            seq.append(nxt_n); visited.add(nxt_n)
            prev, cur = cur, nxt_n
            if len(seq) > len(adj) + 1:
                break
        visited.add(start)
        xs, ys = p[0, seq], p[1, seq]
        signed = 0.5 * float(np.sum(xs * np.roll(ys, -1) - np.roll(xs, -1) * ys))
        loops.append(dict(facets=facets, abs_area=abs(signed)))
    loops.sort(key=lambda L: L["abs_area"], reverse=True)
    outer = np.array(loops[0]["facets"], dtype=int)
    inner = np.array([f for L in loops[1:] for f in L["facets"]], dtype=int)
    return outer, inner


def solve_2d(P_external, mode, mesh, clamp_nodes, outer_f, inner_f):
    """mode='flooded' applies pressure on ALL boundary facets;
    mode='trapped_air' applies pressure only on the outer skin."""
    e = ElementVector(ElementTriP1())
    basis = Basis(mesh, e)
    mu, lam = material()

    @BilinearForm
    def tng(u, v, w):
        du = grad(u); eps = 0.5 * (du + transpose(du))
        sig = eye(lam * trace(eps), 2) + 2.0 * mu * eps
        return ddot(sig, grad(v))
    K = tng.assemble(basis)

    if mode == "flooded":
        facets = mesh.boundary_facets()
    elif mode == "trapped_air":
        facets = outer_f
    else:
        raise ValueError(mode)
    fbasis = FacetBasis(mesh, e, facets=facets)

    @LinearForm
    def pload(v, w):
        return -P_external * (w.n[0] * v[0] + w.n[1] * v[1])
    f = pload.assemble(fbasis)

    nodal = basis.nodal_dofs
    D = nodal[:, clamp_nodes].flatten()
    R = K @ np.zeros(basis.N) - f
    du = solve(*condense(K, -R, D=D))
    u = du   # one step solves the linear problem

    # element-averaged Cauchy von Mises (constant per element since P1)
    p = mesh.p; t = mesh.t
    ux = u[nodal[0]]; uy = u[nodal[1]]
    # compute strain per tri
    tri_pts = p[:, t].transpose(2, 0, 1)  # (n_tri, 2, 3)
    a = tri_pts[:, :, 0]; b = tri_pts[:, :, 1]; c = tri_pts[:, :, 2]
    v0 = b - a; v1 = c - a
    area2 = v0[:, 0] * v1[:, 1] - v0[:, 1] * v1[:, 0]
    # shape derivatives
    inv2A = 1.0 / area2
    # ∂N0/∂x = (y1 - y2)/(2A) etc.
    y12 = b[:, 1] - c[:, 1]; y20 = c[:, 1] - a[:, 1]; y01 = a[:, 1] - b[:, 1]
    x21 = c[:, 0] - b[:, 0]; x02 = a[:, 0] - c[:, 0]; x10 = b[:, 0] - a[:, 0]
    dNdx = np.stack([y12, y20, y01], axis=1) * inv2A[:, None]
    dNdy = np.stack([x21, x02, x10], axis=1) * inv2A[:, None]
    ux_tri = ux[t.T]   # (n_tri, 3)
    uy_tri = uy[t.T]
    exx = (dNdx * ux_tri).sum(axis=1)
    eyy = (dNdy * uy_tri).sum(axis=1)
    exy = 0.5 * ((dNdy * ux_tri).sum(axis=1) + (dNdx * uy_tri).sum(axis=1))
    sxx = (E_TPU / ((1 + NU) * (1 - 2 * NU))) * ((1 - NU) * exx + NU * eyy)
    syy = (E_TPU / ((1 + NU) * (1 - 2 * NU))) * (NU * exx + (1 - NU) * eyy)
    sxy = (E_TPU / (1 + NU)) * exy
    szz = NU * (sxx + syy)
    vm = np.sqrt(0.5 * ((sxx - syy)**2 + (syy - szz)**2 +
                        (szz - sxx)**2 + 6.0 * sxy**2))
    return ux, uy, vm


def plot_2d_panel(ax, mesh, ux, uy, vm, mag, title, vmin, vmax):
    p = mesh.p; t = mesh.t
    xy_def = p.copy()
    xy_def[0] += mag * ux
    xy_def[1] += mag * uy
    tri = Triangulation(xy_def[0], xy_def[1], t.T)
    pc = ax.tripcolor(tri, facecolors=vm, cmap="inferno",
                       vmin=vmin, vmax=vmax, edgecolors="none")
    ax.triplot(tri, color="black", lw=0.2, alpha=0.3)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=9)
    return pc


# =============== 3D solve infrastructure (reuse underwater_crush_3d) ===============
def run_3d_field(P_depth):
    """Run the 3D crush solve and return (nodes, tets, u_disp, vm_per_tet, N2)."""
    import underwater_crush_3d as uc
    workdir = os.path.join(os.path.dirname(HERE), "iterations", "_underwater_crush_3d")
    os.makedirs(workdir, exist_ok=True)
    sys.path.insert(0, HERE)
    import iter_harness as ih
    p2d, tris, lm = ih.regen_section({}, workdir)
    if "blade_len" not in lm: lm["blade_len"] = 90.0
    if "r_bore" not in lm and "mount_hole_r" in lm:
        lm["r_bore"] = lm["mount_hole_r"]
    if "contact_x" not in lm:
        lm["contact_x"] = float(p2d[:, 0].min())
    outer_e, inner_e, _, _, edge_n2 = uc.classify_2d_boundary(p2d, tris)
    nodes, tets, N2 = uc.build_tets_3d(p2d, tris)
    K, B, V, edof = uc.assemble_stiffness(nodes, tets)
    faces_tagged = uc.enumerate_boundary_faces_with_normals(
        p2d, tris, outer_e, inner_e, edge_n2, N2)
    clamp_d, _ = uc.clamp_dofs(nodes, lm, N2)
    f_load, _ = uc.pressure_load_vector(nodes, faces_tagged, p2d, outer_e,
                                         N2, P_depth, lm, flooded=False)
    u = uc.solve_linear(K, f_load, clamp_d, nodes.shape[0] * 3)
    vm_tet, _ = uc.von_mises_per_tet(B, V, u, edof)
    return nodes, tets, u, vm_tet, N2, p2d, tris


def plot_3d_midz_slice(ax, p2d, tris, nodes, u, vm_tet, N2, mag,
                       title, vmin, vmax):
    """Mid-Z slice rendered as the 2D triangulation deformed by the
    mid-layer displacement and colored by per-tri average vM."""
    n_layers = nodes.shape[0] // N2 - 1
    mid_layer = n_layers // 2
    base = mid_layer * N2
    ux = u[3 * (base + np.arange(N2)) + 0]
    uy = u[3 * (base + np.arange(N2)) + 1]
    # per-tri vM at mid-Z: average over tets whose centroid is at mid-Z layer
    tet_z = nodes[:, 2][np.array(np.arange(nodes.shape[0]))]
    tet_z_centroid = nodes[:, 2][np.array(np.arange(nodes.shape[0]))]  # placeholder
    # easier: just project vM onto 2D tris by aggregating tets at this layer
    # for each 2D tri, find all 3 tets in the mid-Z prism layer and average vM
    n_tets_per_prism = 3
    tets_per_layer = tris.shape[0] * n_tets_per_prism
    tets_start = mid_layer * tets_per_layer
    tets_end = (mid_layer + 1) * tets_per_layer
    vm_tris = np.zeros(tris.shape[0])
    for ti in range(tris.shape[0]):
        vm_tris[ti] = vm_tet[tets_start + ti * 3:tets_start + (ti + 1) * 3].mean()
    # deformed 2D positions at mid-Z
    xy_def = p2d.copy().T  # (2, N2)
    xy_def[0] += mag * ux
    xy_def[1] += mag * uy
    tri = Triangulation(xy_def[0], xy_def[1], tris)
    pc = ax.tripcolor(tri, facecolors=vm_tris, cmap="inferno",
                       vmin=vmin, vmax=vmax, edgecolors="none")
    ax.triplot(tri, color="black", lw=0.2, alpha=0.3)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=9)
    return pc


# =============== render sheets ===============
def render_pressure_sheet():
    """FLOODED case — show the rest mesh and deformed at 3 depths."""
    mesh, lm, clamp = load_mesh_2d()
    outer_f, inner_f = classify_2d_loops(mesh)
    print(f"flooded sheet: mesh {mesh.p.shape[1]} nodes, "
          f"{mesh.t.shape[1]} tris")
    cases = []
    for depth in DEPTHS_2D_FLOOD:
        P = RHO_G * depth
        ux, uy, vm = solve_2d(P, "flooded", mesh, clamp, outer_f, inner_f)
        disp = np.hypot(ux, uy)
        cases.append(dict(depth=depth, P=P, ux=ux, uy=uy, vm=vm,
                          max_disp_um=float(disp.max() * 1000),
                          max_vm=float(vm.max())))
        print(f"  flooded {depth:5.0f} m: max |u| = {disp.max()*1000:.1f} μm, "
              f"max vM = {vm.max():.4f} MPa")
    vmax = max(c["max_vm"] for c in cases)
    # 1 row × 4 cols: rest + 3 depths
    fig, axs = plt.subplots(1, 4, figsize=(16, 5))
    p = mesh.p; t = mesh.t
    tri0 = Triangulation(p[0], p[1], t.T)
    axs[0].tripcolor(tri0, facecolors=np.zeros(t.shape[1]),
                      cmap="inferno", vmin=0, vmax=vmax, edgecolors="none")
    axs[0].triplot(tri0, color="black", lw=0.2, alpha=0.4)
    axs[0].set_aspect("equal"); axs[0].set_xticks([]); axs[0].set_yticks([])
    axs[0].set_title("rest (no pressure)\nundeformed Fin Ray section", fontsize=9)
    # deformation is tiny so magnify it ×200 for visibility
    MAG = 200
    for i, c in enumerate(cases, start=1):
        pc = plot_2d_panel(axs[i], mesh, c["ux"], c["uy"], c["vm"], MAG,
                            f"flooded @ {c['depth']:.0f} m  "
                            f"(P = {c['P']:.2f} MPa)\n"
                            f"max |u| = {c['max_disp_um']:.0f} μm  "
                            f"max vM = {c['max_vm']:.3f} MPa\n"
                            f"(deformation ×{MAG} for visibility)",
                            vmin=0, vmax=vmax)
    # one colorbar
    cbar = fig.colorbar(pc, ax=axs.ravel().tolist(), fraction=0.02,
                         label="von Mises (MPa)")
    fig.suptitle("Underwater pressure FEA — FLOODED case "
                 "(water inside Fin Ray cells AND outside skin, "
                 "at the same pressure)\n"
                 "Bulk hydrostatic stress σ = −P·I → von Mises ≈ 0 everywhere; "
                 "finger just uniformly shrinks",
                 fontsize=11)
    fig.subplots_adjust(top=0.84, bottom=0.04, left=0.02, right=0.92,
                        wspace=0.05)
    fp = os.path.join(PICS, "underwater_pressure_FEA.png")
    fig.savefig(fp, dpi=120)
    print(f"wrote {fp}")
    plt.close(fig)


def render_crush_sheet():
    """TRAPPED-AIR case — show 2D plane-strain (under-estimate) + 3D
    mid-Z slice (correct) at each depth side-by-side."""
    mesh, lm, clamp = load_mesh_2d()
    outer_f, inner_f = classify_2d_loops(mesh)
    print(f"crush sheet: mesh {mesh.p.shape[1]} nodes")
    # ---- 2D trapped-air ----
    cases_2d = []
    for depth in DEPTHS_2D_CRUSH:
        P = RHO_G * depth
        ux, uy, vm = solve_2d(P, "trapped_air", mesh, clamp, outer_f, inner_f)
        cases_2d.append(dict(depth=depth, P=P, ux=ux, uy=uy, vm=vm,
                             max_disp_um=float(np.hypot(ux, uy).max() * 1000),
                             max_vm=float(vm.max())))
        print(f"  2D crush @ {depth:5.0f} m: max |u| = "
              f"{cases_2d[-1]['max_disp_um']:.1f} μm, "
              f"max vM = {cases_2d[-1]['max_vm']:.3f} MPa")
    # ---- 3D trapped-air ----
    cases_3d = []
    for depth in DEPTHS_3D_CRUSH:
        P = RHO_G * depth
        nodes, tets, u, vm_tet, N2, p2d_3d, tris_3d = run_3d_field(P)
        disp = np.linalg.norm(u.reshape(-1, 3), axis=1)
        cases_3d.append(dict(depth=depth, P=P, nodes=nodes, tets=tets,
                              u=u, vm_tet=vm_tet, N2=N2,
                              p2d=p2d_3d, tris=tris_3d,
                              max_disp_um=float(disp.max() * 1000),
                              max_vm=float(vm_tet.max())))
        print(f"  3D crush @ {depth:5.0f} m: max |u| = "
              f"{cases_3d[-1]['max_disp_um']:.1f} μm, "
              f"max vM = {cases_3d[-1]['max_vm']:.3f} MPa")

    # ---- common color scale per row (so colors are comparable across depths) ----
    vmax_2d = max(c["max_vm"] for c in cases_2d)
    vmax_3d = max(c["max_vm"] for c in cases_3d)

    fig, axs = plt.subplots(2, 4, figsize=(16, 9))
    # row 0: 2D plane-strain — rest + 3 depths
    p = mesh.p; t = mesh.t
    tri0 = Triangulation(p[0], p[1], t.T)
    axs[0, 0].tripcolor(tri0, facecolors=np.zeros(t.shape[1]),
                        cmap="inferno", vmin=0, vmax=vmax_2d, edgecolors="none")
    axs[0, 0].triplot(tri0, color="black", lw=0.2, alpha=0.4)
    axs[0, 0].set_aspect("equal")
    axs[0, 0].set_xticks([]); axs[0, 0].set_yticks([])
    axs[0, 0].set_title("rest (no pressure)\n2D plane-strain section", fontsize=9)
    MAG_2D = 20
    for i, c in enumerate(cases_2d, start=1):
        pc2 = plot_2d_panel(axs[0, i], mesh, c["ux"], c["uy"], c["vm"], MAG_2D,
                             f"2D trapped-air @ {c['depth']:.0f} m  "
                             f"(P = {c['P']:.2f} MPa)\n"
                             f"max sag = {c['max_disp_um']:.0f} μm  "
                             f"max vM = {c['max_vm']:.2f} MPa\n"
                             f"(deformation ×{MAG_2D})",
                             vmin=0, vmax=vmax_2d)
    axs[0, 0].set_ylabel("2D plane-strain\n(εz = 0; UNDER-estimates)",
                         fontsize=10, color="#ff7f0e")
    # row 1: 3D mid-Z slice — rest + 3 depths
    p2d_3d = cases_3d[0]["p2d"]
    tris_3d = cases_3d[0]["tris"]
    tri30 = Triangulation(p2d_3d[:, 0], p2d_3d[:, 1], tris_3d)
    axs[1, 0].tripcolor(tri30, facecolors=np.zeros(tris_3d.shape[0]),
                        cmap="inferno", vmin=0, vmax=vmax_3d, edgecolors="none")
    axs[1, 0].triplot(tri30, color="black", lw=0.2, alpha=0.4)
    axs[1, 0].set_aspect("equal")
    axs[1, 0].set_xticks([]); axs[1, 0].set_yticks([])
    axs[1, 0].set_title("rest (no pressure)\n3D mid-Z slice", fontsize=9)
    MAG_3D = 2
    for i, c in enumerate(cases_3d, start=1):
        pc3 = plot_3d_midz_slice(axs[1, i], c["p2d"], c["tris"], c["nodes"],
                                  c["u"], c["vm_tet"], c["N2"], MAG_3D,
                                  f"3D trapped-air @ {c['depth']:.0f} m  "
                                  f"(P = {c['P']:.2f} MPa)\n"
                                  f"max sag = {c['max_disp_um']:.0f} μm  "
                                  f"max vM = {c['max_vm']:.2f} MPa\n"
                                  f"(deformation ×{MAG_3D})",
                                  vmin=0, vmax=vmax_3d)
    axs[1, 0].set_ylabel("3D solid (correct)\nshows foam-collapse mode",
                         fontsize=10, color="#d62728")
    cbar = fig.colorbar(pc3, ax=axs.ravel().tolist(), fraction=0.02,
                         label="von Mises (MPa)")
    fig.suptitle("Underwater pressure FEA — TRAPPED-AIR worst case "
                 "(external water at P_depth, cells contain 1 atm air)\n"
                 "Top: 2D plane-strain misses the dominant mode (εz=0); "
                 "Bottom: 3D shows the cells collapse globally — finger "
                 "wrecked even at shallow depth",
                 fontsize=11)
    fig.subplots_adjust(top=0.90, bottom=0.04, left=0.04, right=0.92,
                        wspace=0.05, hspace=0.18)
    fp = os.path.join(PICS, "underwater_crush_FEA.png")
    fig.savefig(fp, dpi=120)
    print(f"wrote {fp}")
    plt.close(fig)


def main():
    t0 = time.time()
    os.makedirs(PICS, exist_ok=True)
    render_pressure_sheet()
    render_crush_sheet()
    print(f"\ntotal: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()

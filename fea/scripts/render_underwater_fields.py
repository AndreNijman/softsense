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


def plot_2d_panel(ax, mesh, ux, uy, vm, mag, title, vmin, vmax,
                  past_validity=False):
    """Plot deformed mesh colored by vM with undeformed outline overlaid in gray.

    Setting `past_validity=True` adds a watermark so the viewer knows the
    panel is showing a linear-FEA result that's outside its validity envelope.
    """
    p = mesh.p; t = mesh.t
    tri_rest = Triangulation(p[0], p[1], t.T)
    # undeformed outline (gray, no fill)
    ax.triplot(tri_rest, color="0.7", lw=0.4, alpha=0.7)
    # deformed mesh, colored by vM
    xy_def = p.copy()
    xy_def[0] += mag * ux
    xy_def[1] += mag * uy
    tri_def = Triangulation(xy_def[0], xy_def[1], t.T)
    pc = ax.tripcolor(tri_def, facecolors=vm, cmap="inferno",
                       vmin=vmin, vmax=vmax, edgecolors="none", alpha=0.95)
    ax.triplot(tri_def, color="black", lw=0.2, alpha=0.4)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=8.5)
    if past_validity:
        ax.text(0.5, 0.5, "LINEAR FEA\nPAST VALIDITY",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=11, color="red", weight="bold", alpha=0.85,
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="red",
                           boxstyle="round,pad=0.3"))
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
                       title, vmin, vmax, past_validity=False):
    """Mid-Z slice rendered as the 2D triangulation deformed by the
    mid-layer displacement and colored by per-tri average vM. The
    undeformed cross-section outline is overlaid in gray for reference."""
    n_layers = nodes.shape[0] // N2 - 1
    mid_layer = n_layers // 2
    base = mid_layer * N2
    ux = u[3 * (base + np.arange(N2)) + 0]
    uy = u[3 * (base + np.arange(N2)) + 1]
    # per-tri vM at mid-Z: average over the 3 tets of each prism in mid-Z layer
    n_tets_per_prism = 3
    tets_per_layer = tris.shape[0] * n_tets_per_prism
    tets_start = mid_layer * tets_per_layer
    vm_tris = np.zeros(tris.shape[0])
    for ti in range(tris.shape[0]):
        vm_tris[ti] = vm_tet[tets_start + ti * 3:tets_start + (ti + 1) * 3].mean()
    # undeformed outline (gray)
    tri_rest = Triangulation(p2d[:, 0], p2d[:, 1], tris)
    ax.triplot(tri_rest, color="0.7", lw=0.4, alpha=0.7)
    # deformed mesh
    xy_def = p2d.copy().T
    xy_def[0] += mag * ux
    xy_def[1] += mag * uy
    tri_def = Triangulation(xy_def[0], xy_def[1], tris)
    pc = ax.tripcolor(tri_def, facecolors=vm_tris, cmap="inferno",
                       vmin=vmin, vmax=vmax, edgecolors="none", alpha=0.95)
    ax.triplot(tri_def, color="black", lw=0.2, alpha=0.4)
    ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(title, fontsize=8.5)
    if past_validity:
        ax.text(0.5, 0.5, "LINEAR FEA\nPAST VALIDITY",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=11, color="red", weight="bold", alpha=0.85,
                bbox=dict(facecolor="white", alpha=0.7, edgecolor="red",
                           boxstyle="round,pad=0.3"))
    return pc


# =============== render sheets ===============
def render_pressure_sheet():
    """FLOODED case — show the rest mesh and deformed at 3 depths.

    Honest visualization: gray rest mesh outline OVERLAID on every panel
    so the viewer sees how small the real deformation is. Per-panel
    magnification is picked so each panel shows ~5 mm of visible
    deformation (roughly 1/20 of the 90 mm blade) — comparable across
    depths without faking the physics.
    """
    mesh, lm, clamp = load_mesh_2d()
    outer_f, inner_f = classify_2d_loops(mesh)
    print(f"flooded sheet: mesh {mesh.p.shape[1]} nodes")
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
    # pick magnification so max visible deformation = TARGET_VISIBLE mm
    TARGET_VISIBLE_MM = 5.0
    for c in cases:
        c["mag"] = max(1, int(round(TARGET_VISIBLE_MM * 1000 / c["max_disp_um"])))

    fig, axs = plt.subplots(1, 4, figsize=(16, 5))
    p = mesh.p; t = mesh.t
    # axis limits = rest bbox + margin
    x_pad = 5; y_pad = 5
    xlim = (p[0].min() - x_pad, p[0].max() + x_pad)
    ylim = (p[1].min() - y_pad, p[1].max() + y_pad)

    tri0 = Triangulation(p[0], p[1], t.T)
    axs[0].tripcolor(tri0, facecolors=np.zeros(t.shape[1]),
                      cmap="inferno", vmin=0, vmax=vmax, edgecolors="none")
    axs[0].triplot(tri0, color="black", lw=0.2, alpha=0.5)
    axs[0].set_aspect("equal"); axs[0].set_xticks([]); axs[0].set_yticks([])
    axs[0].set_xlim(xlim); axs[0].set_ylim(ylim)
    axs[0].set_title("rest (P = 0)\nundeformed", fontsize=9)

    for i, c in enumerate(cases, start=1):
        title = (f"flooded @ {c['depth']:.0f} m  (P = {c['P']:.2f} MPa)\n"
                 f"REAL max |u| = {c['max_disp_um']:.0f} μm  "
                 f"({100 * c['max_disp_um']/1000/90:.2f} % of blade length)\n"
                 f"max vM = {c['max_vm']:.3f} MPa  "
                 f"({TPU_YIELD/c['max_vm']:.0f}× yield margin)\n"
                 f"deformation drawn ×{c['mag']}; gray = undeformed")
        pc = plot_2d_panel(axs[i], mesh, c["ux"], c["uy"], c["vm"], c["mag"],
                            title, vmin=0, vmax=vmax)
        axs[i].set_xlim(xlim); axs[i].set_ylim(ylim)
    cbar = fig.colorbar(pc, ax=axs.ravel().tolist(), fraction=0.02,
                         label="von Mises (MPa)")
    fig.suptitle("Underwater pressure FEA — FLOODED case "
                 "(water inside Fin Ray cells AND outside skin at the same pressure)\n"
                 "Bulk hydrostatic state σ = −P·I → vM ≈ 0; finger uniformly shrinks. "
                 "Stress concentration shown is at the clamp pin-bore (where TPU "
                 "is prevented from shrinking by the rigid pin).",
                 fontsize=10.5)
    fig.subplots_adjust(top=0.84, bottom=0.04, left=0.02, right=0.92,
                        wspace=0.05)
    fp = os.path.join(PICS, "underwater_pressure_FEA.png")
    fig.savefig(fp, dpi=120)
    print(f"wrote {fp}")
    plt.close(fig)


def render_crush_sheet():
    """TRAPPED-AIR case — show 2D plane-strain (under-estimate) + 3D
    mid-Z slice (correct) at each depth side-by-side.

    Honest visualization rules:
      - undeformed rest mesh always overlaid in gray
      - per-row magnification picked so visible deformation is comparable
      - panels where linear FEA is past its validity envelope (max
        displacement > ~20% of smallest feature thickness, ~0.3 mm for
        a 1.6 mm rib) are stamped "LINEAR FEA PAST VALIDITY"
      - axis limits = rest bbox (deformation that exits the box is a
        visual cue that the linear-elastic prediction is unphysical)
    """
    LINEAR_VALID_LIMIT_UM = 300.0   # ~20% of 1.6 mm rib wall

    mesh, lm, clamp = load_mesh_2d()
    outer_f, inner_f = classify_2d_loops(mesh)
    print(f"crush sheet: mesh {mesh.p.shape[1]} nodes")
    # ---- 2D trapped-air ----
    cases_2d = []
    for depth in DEPTHS_2D_CRUSH:
        P = RHO_G * depth
        ux, uy, vm = solve_2d(P, "trapped_air", mesh, clamp, outer_f, inner_f)
        max_disp = float(np.hypot(ux, uy).max() * 1000)
        cases_2d.append(dict(depth=depth, P=P, ux=ux, uy=uy, vm=vm,
                             max_disp_um=max_disp,
                             max_vm=float(vm.max()),
                             past_validity=max_disp > LINEAR_VALID_LIMIT_UM))
        print(f"  2D crush @ {depth:5.0f} m: max |u| = {max_disp:.1f} μm, "
              f"vM = {vm.max():.3f} MPa "
              f"{'(past validity)' if max_disp > LINEAR_VALID_LIMIT_UM else ''}")
    # ---- 3D trapped-air ----
    cases_3d = []
    for depth in DEPTHS_3D_CRUSH:
        P = RHO_G * depth
        nodes, tets, u, vm_tet, N2, p2d_3d, tris_3d = run_3d_field(P)
        disp = np.linalg.norm(u.reshape(-1, 3), axis=1)
        max_disp = float(disp.max() * 1000)
        cases_3d.append(dict(depth=depth, P=P, nodes=nodes, tets=tets,
                              u=u, vm_tet=vm_tet, N2=N2,
                              p2d=p2d_3d, tris=tris_3d,
                              max_disp_um=max_disp,
                              max_vm=float(vm_tet.max()),
                              past_validity=max_disp > LINEAR_VALID_LIMIT_UM))
        print(f"  3D crush @ {depth:5.0f} m: max |u| = {max_disp:.1f} μm, "
              f"vM = {vm_tet.max():.3f} MPa "
              f"{'(past validity)' if max_disp > LINEAR_VALID_LIMIT_UM else ''}")

    # color scales — use the SMALLEST-depth max so colors are comparable
    # within the in-validity range; clip beyond
    vmax_2d = max(c["max_vm"] for c in cases_2d if not c["past_validity"]) \
        if any(not c["past_validity"] for c in cases_2d) else max(c["max_vm"] for c in cases_2d)
    vmax_3d = max(c["max_vm"] for c in cases_3d if not c["past_validity"]) \
        if any(not c["past_validity"] for c in cases_3d) else max(c["max_vm"] for c in cases_3d)
    vmax_shared = max(vmax_2d, vmax_3d)

    # picks magnification to give TARGET_VISIBLE_MM of visible deformation
    TARGET_VISIBLE_MM = 6.0
    for c in cases_2d + cases_3d:
        if c["max_disp_um"] > 1e-9:
            c["mag"] = max(1, int(round(TARGET_VISIBLE_MM * 1000 / c["max_disp_um"])))
        else:
            c["mag"] = 1

    fig, axs = plt.subplots(2, 4, figsize=(16, 9))
    p = mesh.p; t = mesh.t
    p2d_3d = cases_3d[0]["p2d"]; tris_3d = cases_3d[0]["tris"]
    # axis limits = rest bbox + margin (same for both rows, since same outline)
    x_pad = 6; y_pad = 6
    xlim = (p[0].min() - x_pad, p[0].max() + x_pad)
    ylim = (p[1].min() - y_pad, p[1].max() + y_pad)

    # row 0: 2D plane-strain
    tri0 = Triangulation(p[0], p[1], t.T)
    axs[0, 0].tripcolor(tri0, facecolors=np.zeros(t.shape[1]),
                        cmap="inferno", vmin=0, vmax=vmax_shared, edgecolors="none")
    axs[0, 0].triplot(tri0, color="black", lw=0.2, alpha=0.5)
    axs[0, 0].set_aspect("equal")
    axs[0, 0].set_xticks([]); axs[0, 0].set_yticks([])
    axs[0, 0].set_xlim(xlim); axs[0, 0].set_ylim(ylim)
    axs[0, 0].set_title("rest (P = 0)\nundeformed", fontsize=9)
    axs[0, 0].set_ylabel("2D plane-strain\nεz = 0  (UNDER-estimates)",
                          fontsize=9, color="#ff7f0e")
    for i, c in enumerate(cases_2d, start=1):
        title = (f"2D trapped-air @ {c['depth']:.0f} m  (P = {c['P']:.2f} MPa)\n"
                 f"REAL max sag = {c['max_disp_um']:.0f} μm  "
                 f"max vM = {c['max_vm']:.2f} MPa  "
                 f"({TPU_YIELD/max(c['max_vm'], 1e-9):.0f}× yield)\n"
                 f"drawn ×{c['mag']}; gray = undeformed")
        pc = plot_2d_panel(axs[0, i], mesh, c["ux"], c["uy"], c["vm"],
                            c["mag"], title, vmin=0, vmax=vmax_shared,
                            past_validity=c["past_validity"])
        axs[0, i].set_xlim(xlim); axs[0, i].set_ylim(ylim)

    # row 1: 3D mid-Z slice
    tri30 = Triangulation(p2d_3d[:, 0], p2d_3d[:, 1], tris_3d)
    axs[1, 0].tripcolor(tri30, facecolors=np.zeros(tris_3d.shape[0]),
                        cmap="inferno", vmin=0, vmax=vmax_shared, edgecolors="none")
    axs[1, 0].triplot(tri30, color="black", lw=0.2, alpha=0.5)
    axs[1, 0].set_aspect("equal")
    axs[1, 0].set_xticks([]); axs[1, 0].set_yticks([])
    axs[1, 0].set_xlim(xlim); axs[1, 0].set_ylim(ylim)
    axs[1, 0].set_title("rest (P = 0)\nundeformed", fontsize=9)
    axs[1, 0].set_ylabel("3D solid (CORRECT)\nfoam-collapse mode",
                          fontsize=9, color="#d62728")
    for i, c in enumerate(cases_3d, start=1):
        title = (f"3D trapped-air @ {c['depth']:.0f} m  (P = {c['P']:.2f} MPa)\n"
                 f"REAL max sag = {c['max_disp_um']:.0f} μm  "
                 f"max vM = {c['max_vm']:.2f} MPa  "
                 f"({TPU_YIELD/max(c['max_vm'], 1e-9):.0f}× yield)\n"
                 f"drawn ×{c['mag']}; gray = undeformed")
        pc3 = plot_3d_midz_slice(axs[1, i], c["p2d"], c["tris"], c["nodes"],
                                  c["u"], c["vm_tet"], c["N2"], c["mag"],
                                  title, vmin=0, vmax=vmax_shared,
                                  past_validity=c["past_validity"])
        axs[1, i].set_xlim(xlim); axs[1, i].set_ylim(ylim)

    cbar = fig.colorbar(pc3, ax=axs.ravel().tolist(), fraction=0.02,
                         label="von Mises (MPa)")
    fig.suptitle("Underwater pressure FEA — TRAPPED-AIR worst case "
                 "(external water at P_depth, cells contain 1 atm air)\n"
                 "Top: 2D plane-strain — εz=0 over-constraint misses the "
                 "foam-collapse mode. Bottom: 3D — correct physics, shows "
                 "cells curling. Panels stamped PAST VALIDITY have "
                 "displacement > 20% of rib thickness; linear FEA's the "
                 "wrong tool past that (no self-contact, no gas backpressure).",
                 fontsize=10)
    fig.subplots_adjust(top=0.88, bottom=0.04, left=0.04, right=0.92,
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

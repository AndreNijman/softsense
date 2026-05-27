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

# ----- depths to render (common across both sheets so each panel
#       has a flooded-vs-trapped-air comparison at the same depth) -----
DEPTHS_PRESSURE = [30.0, 100.0, 300.0]   # 2D plane-strain sheet
DEPTHS_CRUSH    = [30.0, 100.0, 300.0]   # 3D sheet

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
_3D_CACHE = {}


def build_3d_once():
    """Build the 3D mesh and stiffness ONCE — both flooded and trapped-air
    cases reuse the same K. Reduces 6-run wallclock from ~12 min to ~4 min."""
    if "K" in _3D_CACHE:
        return _3D_CACHE
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
    _3D_CACHE.update(dict(uc=uc, p2d=p2d, tris=tris, lm=lm, outer_e=outer_e,
                          nodes=nodes, tets=tets, N2=N2, K=K, B=B, V=V,
                          edof=edof, faces_tagged=faces_tagged,
                          clamp_d=clamp_d))
    return _3D_CACHE


def run_3d_field(P_depth, flooded=False):
    """Run the 3D solve for one depth + load case, return (u, vm_tet)."""
    c = build_3d_once()
    f_load, _ = c["uc"].pressure_load_vector(
        c["nodes"], c["faces_tagged"], c["p2d"], c["outer_e"],
        c["N2"], P_depth, c["lm"], flooded=flooded)
    u = c["uc"].solve_linear(c["K"], f_load, c["clamp_d"],
                              c["nodes"].shape[0] * 3)
    vm_tet, _ = c["uc"].von_mises_per_tet(c["B"], c["V"], u, c["edof"])
    return u, vm_tet


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
    """2D plane-strain — both load cases at common depths for direct comparison.

      Row 0: FLOODED      (rest, 30 m, 100 m, 300 m)
      Row 1: TRAPPED AIR  (rest, 30 m, 100 m, 300 m)

    Same color scale across both rows so vM is directly comparable.
    """
    LINEAR_VALID_LIMIT_UM = 300.0   # ~20% of 1.6 mm rib wall

    mesh, lm, clamp = load_mesh_2d()
    outer_f, inner_f = classify_2d_loops(mesh)
    print(f"pressure sheet (2D plane-strain): mesh {mesh.p.shape[1]} nodes")

    def solve_case(mode):
        out = []
        # past-validity stamp only meaningful for trapped_air (rib bending);
        # flooded is uniform bulk shrinkage with no nonlinear concerns
        check_validity = (mode == "trapped_air")
        for depth in DEPTHS_PRESSURE:
            P = RHO_G * depth
            ux, uy, vm = solve_2d(P, mode, mesh, clamp, outer_f, inner_f)
            max_disp = float(np.hypot(ux, uy).max() * 1000)
            pv = check_validity and (max_disp > LINEAR_VALID_LIMIT_UM)
            out.append(dict(depth=depth, P=P, ux=ux, uy=uy, vm=vm,
                            max_disp_um=max_disp,
                            max_vm=float(vm.max()),
                            past_validity=pv))
            print(f"  {mode:11s} @ {depth:4.0f} m: |u|={max_disp:7.1f} μm  "
                  f"vM={vm.max():.3f} MPa "
                  f"{'(past validity)' if pv else ''}")
        return out

    cases_fl = solve_case("flooded")
    cases_ta = solve_case("trapped_air")

    vmax = max(max(c["max_vm"] for c in cases_fl),
                max(c["max_vm"] for c in cases_ta if not c["past_validity"]
                    or True))  # include past-validity in colour cap
    TARGET_VISIBLE_MM = 5.0
    for c in cases_fl + cases_ta:
        c["mag"] = max(1, int(round(TARGET_VISIBLE_MM * 1000 / max(c["max_disp_um"], 1))))

    fig, axs = plt.subplots(2, 4, figsize=(16, 9))
    p = mesh.p; t = mesh.t
    x_pad, y_pad = 5, 5
    xlim = (p[0].min() - x_pad, p[0].max() + x_pad)
    ylim = (p[1].min() - y_pad, p[1].max() + y_pad)

    def rest_panel(ax, label):
        tri0 = Triangulation(p[0], p[1], t.T)
        ax.tripcolor(tri0, facecolors=np.zeros(t.shape[1]),
                      cmap="inferno", vmin=0, vmax=vmax, edgecolors="none")
        ax.triplot(tri0, color="black", lw=0.2, alpha=0.5)
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_xlim(xlim); ax.set_ylim(ylim)
        ax.set_title("rest (P = 0)\nundeformed", fontsize=9)

    rest_panel(axs[0, 0], "flooded")
    axs[0, 0].set_ylabel(
        "FLOODED\n(water inside cells AND outside)\n"
        "design intent — σ = −P·I",
        fontsize=9, color="#1f77b4")
    for i, c in enumerate(cases_fl, start=1):
        title = (f"flooded @ {c['depth']:.0f} m  (P = {c['P']:.2f} MPa)\n"
                 f"REAL max |u| = {c['max_disp_um']:.0f} μm  "
                 f"max vM = {c['max_vm']:.3f} MPa  "
                 f"({TPU_YIELD/max(c['max_vm'], 1e-9):.0f}× yield)\n"
                 f"drawn ×{c['mag']}; gray = undeformed")
        pc = plot_2d_panel(axs[0, i], mesh, c["ux"], c["uy"], c["vm"],
                            c["mag"], title, vmin=0, vmax=vmax,
                            past_validity=c["past_validity"])
        axs[0, i].set_xlim(xlim); axs[0, i].set_ylim(ylim)

    rest_panel(axs[1, 0], "trapped")
    axs[1, 0].set_ylabel(
        "TRAPPED AIR\n(cells contain 1 atm air;\n"
        "water only on outer skin)",
        fontsize=9, color="#d62728")
    for i, c in enumerate(cases_ta, start=1):
        title = (f"trapped @ {c['depth']:.0f} m  (P = {c['P']:.2f} MPa)\n"
                 f"REAL max |u| = {c['max_disp_um']:.0f} μm  "
                 f"max vM = {c['max_vm']:.3f} MPa  "
                 f"({TPU_YIELD/max(c['max_vm'], 1e-9):.0f}× yield)\n"
                 f"drawn ×{c['mag']}; gray = undeformed")
        pc = plot_2d_panel(axs[1, i], mesh, c["ux"], c["uy"], c["vm"],
                            c["mag"], title, vmin=0, vmax=vmax,
                            past_validity=c["past_validity"])
        axs[1, i].set_xlim(xlim); axs[1, i].set_ylim(ylim)

    cbar = fig.colorbar(pc, ax=axs.ravel().tolist(), fraction=0.02,
                         label="von Mises (MPa)")
    fig.suptitle("Underwater pressure FEA — 2D plane-strain  "
                 "(flooded design vs trapped-air worst case, same color scale)\n"
                 "Flooded: bulk hydrostatic state, vM essentially zero. "
                 "Trapped-air: cell walls bend; 2D plane-strain UNDER-predicts "
                 "(εz=0 over-constraint hides the 3D foam-collapse mode — see crush sheet).",
                 fontsize=10)
    fig.subplots_adjust(top=0.88, bottom=0.04, left=0.04, right=0.92,
                        wspace=0.05, hspace=0.18)
    fp = os.path.join(PICS, "underwater_pressure_FEA.png")
    fig.savefig(fp, dpi=120)
    print(f"wrote {fp}")
    plt.close(fig)


def render_crush_sheet():
    """3D solid — both load cases at common depths for direct comparison.

      Row 0: FLOODED 3D      (rest, 30 m, 100 m, 300 m)
      Row 1: TRAPPED AIR 3D  (rest, 30 m, 100 m, 300 m)

    Mesh built once; both load cases reuse the same K (cached).
    """
    LINEAR_VALID_LIMIT_UM = 300.0

    # build once
    c3d = build_3d_once()
    p2d_3d = c3d["p2d"]; tris_3d = c3d["tris"]
    nodes = c3d["nodes"]; tets = c3d["tets"]; N2 = c3d["N2"]
    print(f"crush sheet (3D): nodes={nodes.shape[0]}, tets={tets.shape[0]}")

    def run_case(mode):
        out = []
        flooded = (mode == "flooded")
        check_validity = (not flooded)   # flooded = uniform bulk, no nonlinear concerns
        for depth in DEPTHS_CRUSH:
            P = RHO_G * depth
            u, vm_tet = run_3d_field(P, flooded=flooded)
            disp = np.linalg.norm(u.reshape(-1, 3), axis=1)
            max_disp = float(disp.max() * 1000)
            pv = check_validity and (max_disp > LINEAR_VALID_LIMIT_UM)
            out.append(dict(depth=depth, P=P, u=u, vm_tet=vm_tet,
                            max_disp_um=max_disp,
                            max_vm=float(vm_tet.max()),
                            past_validity=pv))
            print(f"  3D {mode:11s} @ {depth:4.0f} m: |u|={max_disp:8.1f} μm "
                  f"vM={vm_tet.max():.3f} MPa "
                  f"{'(past validity)' if pv else ''}")
        return out

    cases_fl = run_case("flooded")
    cases_ta = run_case("trapped_air")

    vmax = max(max(c["max_vm"] for c in cases_fl),
                max(c["max_vm"] for c in cases_ta))
    TARGET_VISIBLE_MM = 6.0
    for c in cases_fl + cases_ta:
        c["mag"] = max(1, int(round(TARGET_VISIBLE_MM * 1000 / max(c["max_disp_um"], 1))))

    fig, axs = plt.subplots(2, 4, figsize=(16, 9))
    x_pad, y_pad = 6, 6
    xlim = (p2d_3d[:, 0].min() - x_pad, p2d_3d[:, 0].max() + x_pad)
    ylim = (p2d_3d[:, 1].min() - y_pad, p2d_3d[:, 1].max() + y_pad)

    def rest_panel(ax):
        tri0 = Triangulation(p2d_3d[:, 0], p2d_3d[:, 1], tris_3d)
        ax.tripcolor(tri0, facecolors=np.zeros(tris_3d.shape[0]),
                      cmap="inferno", vmin=0, vmax=vmax, edgecolors="none")
        ax.triplot(tri0, color="black", lw=0.2, alpha=0.5)
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_xlim(xlim); ax.set_ylim(ylim)
        ax.set_title("rest (P = 0)\nundeformed (mid-Z slice)", fontsize=9)

    rest_panel(axs[0, 0])
    axs[0, 0].set_ylabel(
        "FLOODED 3D\n(water inside cells AND outside)\n"
        "design intent — finger fine",
        fontsize=9, color="#1f77b4")
    for i, c in enumerate(cases_fl, start=1):
        title = (f"flooded 3D @ {c['depth']:.0f} m  (P = {c['P']:.2f} MPa)\n"
                 f"REAL max |u| = {c['max_disp_um']:.0f} μm  "
                 f"max vM = {c['max_vm']:.3f} MPa  "
                 f"({TPU_YIELD/max(c['max_vm'], 1e-9):.0f}× yield)\n"
                 f"drawn ×{c['mag']}; gray = undeformed")
        pc = plot_3d_midz_slice(axs[0, i], p2d_3d, tris_3d, nodes,
                                 c["u"], c["vm_tet"], N2, c["mag"],
                                 title, vmin=0, vmax=vmax,
                                 past_validity=c["past_validity"])
        axs[0, i].set_xlim(xlim); axs[0, i].set_ylim(ylim)

    rest_panel(axs[1, 0])
    axs[1, 0].set_ylabel(
        "TRAPPED AIR 3D\n(cells contain 1 atm air;\n"
        "water only on outer skin)\nFOAM-COLLAPSE mode",
        fontsize=9, color="#d62728")
    for i, c in enumerate(cases_ta, start=1):
        title = (f"trapped 3D @ {c['depth']:.0f} m  (P = {c['P']:.2f} MPa)\n"
                 f"REAL max sag = {c['max_disp_um']:.0f} μm  "
                 f"max vM = {c['max_vm']:.2f} MPa  "
                 f"({TPU_YIELD/max(c['max_vm'], 1e-9):.0f}× yield)\n"
                 f"drawn ×{c['mag']}; gray = undeformed")
        pc = plot_3d_midz_slice(axs[1, i], p2d_3d, tris_3d, nodes,
                                 c["u"], c["vm_tet"], N2, c["mag"],
                                 title, vmin=0, vmax=vmax,
                                 past_validity=c["past_validity"])
        axs[1, i].set_xlim(xlim); axs[1, i].set_ylim(ylim)

    cbar = fig.colorbar(pc, ax=axs.ravel().tolist(), fraction=0.02,
                         label="von Mises (MPa)")
    fig.suptitle("Underwater pressure FEA — 3D solid  "
                 "(flooded design vs trapped-air worst case, same color scale)\n"
                 "Flooded: bulk hydrostatic state σ = −P·I, vM ≈ 0, finger "
                 "essentially unchanged at any depth. Trapped-air: foam-collapse "
                 "mode, cells curl. PAST-VALIDITY stamp marks panels where "
                 "linear FEA breaks down (no self-contact, no gas backpressure).",
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

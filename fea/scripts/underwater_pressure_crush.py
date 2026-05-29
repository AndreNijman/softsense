"""WORST-CASE underwater pressure-crush check on the Fin Ray TPU finger.

The flooded model (`underwater_pressure_probe.py`) assumes water reaches
every TPU surface at the same pressure → σ = -P I, vM ≈ 0. This script
runs the OPPOSITE — and worse — load case:

  External skin   sees water at P_depth.
  Internal cells  trap air at 1 atm  (gauge pressure = 0).

This is what happens during a fast descent before the cells flood, or if
the geometry doesn't actually drain (capillary trap, blocked vent,
infill that closed off the rib openings, etc.). Now the finger has a
real PRESSURE DIFFERENTIAL across the contact wall, the spine wall, and
every rib — and that's a load the design has to survive.

Loading
-------
Boundary facets are classified by loop topology: build the boundary
graph, traverse each connected loop, signed-area-rank them. The largest
absolute area is the OUTER skin (gets external water pressure). All
smaller loops are INNER cavities (gauge pressure 0 → traction-free).

Output: peak vM, contact-wall deflection, per-depth survival check at
ν = 0.42 / 0.45 / 0.48. Compared head-to-head with the flooded case.

Run:  python fea/scripts/underwater_pressure_crush.py
"""
import json
import os
import numpy as np
import skfem
from skfem import (MeshTri, Basis, ElementVector, ElementTriP1, FacetBasis,
                   LinearForm, BilinearForm, condense, solve)
from skfem.helpers import grad, transpose, ddot, trace, eye, mul

HERE = os.path.dirname(os.path.abspath(__file__))

E_TPU = 9.8            # MPa  -- Bambu TPU 95A HF in-plane (X-Y), ISO 527 printed
TPU_YIELD = 27.3       # MPa  -- in-plane tensile strength (this 2D section is in-plane)
# NOTE: this 2D plane-strain model forbids the through-Z collapse and UNDER-predicts
# crush; underwater_crush_3d.py (E_Z=7.4, strength_Z=22.3) is the governing analysis.
NU_LIST = [0.42, 0.45, 0.48]
DEPTHS_M = [0.0, 10.0, 30.0, 100.0, 300.0, 600.0]
RHO_G = 1025.0 * 9.81e-6   # MPa/m


def material(nu):
    mu = E_TPU / (2.0 * (1.0 + nu))
    lam = E_TPU * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    return mu, lam


def load_mesh_and_clamp():
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


def classify_boundary_loops(mesh):
    """Return (outer_facets, inner_facets) by signed-area loop ranking.

    Loops are connected boundary edges. The loop with the largest absolute
    enclosed area is the outer skin. All other loops are cavities.
    """
    p = mesh.p   # (2, n_nodes)
    bfacets = mesh.boundary_facets()       # facet indices (1D)
    edges = mesh.facets[:, bfacets].T      # shape (n_b, 2) — node ids
    # adjacency by node
    adj = {}
    edge_to_facet = {}
    for fi, (a, b) in zip(bfacets, edges):
        adj.setdefault(int(a), []).append((int(b), int(fi)))
        adj.setdefault(int(b), []).append((int(a), int(fi)))
    # walk loops
    visited = set()
    loops = []   # list of (node_seq, facet_seq, signed_area)
    for start in adj:
        if start in visited:
            continue
        # walk
        node_seq = [start]
        facet_seq = []
        prev = None
        cur = start
        while True:
            nbrs = adj[cur]
            # pick the neighbour we didn't come from
            if prev is None:
                nxt_n, nxt_f = nbrs[0]
            else:
                cand = [(n, f) for n, f in nbrs if n != prev]
                if not cand:
                    break
                nxt_n, nxt_f = cand[0]
            facet_seq.append(nxt_f)
            if nxt_n == start:
                break
            node_seq.append(nxt_n)
            visited.add(nxt_n)
            prev = cur
            cur = nxt_n
            if len(node_seq) > len(adj) + 1:
                break  # safety
        visited.add(start)
        # signed area (shoelace)
        xs = p[0, node_seq]
        ys = p[1, node_seq]
        signed = 0.5 * float(np.sum(xs * np.roll(ys, -1) - np.roll(xs, -1) * ys))
        loops.append(dict(nodes=node_seq, facets=facet_seq,
                          signed_area=signed, abs_area=abs(signed)))
    if not loops:
        return np.array([], dtype=int), np.array([], dtype=int)
    loops.sort(key=lambda L: L["abs_area"], reverse=True)
    outer = np.array(loops[0]["facets"], dtype=int)
    inner = np.array([f for L in loops[1:] for f in L["facets"]], dtype=int)
    print(f"  boundary loops: {len(loops)}  (outer abs_area="
          f"{loops[0]['abs_area']:.1f}, inner loops: {len(loops)-1}, "
          f"inner abs_areas total {sum(L['abs_area'] for L in loops[1:]):.1f})")
    return outer, inner


def assemble_forms(mu, lam):
    @BilinearForm
    def tangent(u, v, w):
        du = grad(u)
        eps = 0.5 * (du + transpose(du))
        sig = eye(lam * trace(eps), 2) + 2.0 * mu * eps
        return ddot(sig, grad(v))
    return tangent


def pressure_traction(P_external):
    """External skin only: t = -P_ext n.  Inner cavity walls left
    traction-free (= 1 atm internal in gauge-pressure convention)."""
    @LinearForm
    def pload(v, w):
        return -P_external * (w.n[0] * v[0] + w.n[1] * v[1])
    return pload


def von_mises_field(basis, u, nu):
    @LinearForm
    def vm_proj(v, w):
        du = w["disp"].grad
        eps = 0.5 * (du + transpose(du))
        sxx = (E_TPU / ((1 + nu) * (1 - 2 * nu))) * ((1 - nu) * eps[0, 0] + nu * eps[1, 1])
        syy = (E_TPU / ((1 + nu) * (1 - 2 * nu))) * (nu * eps[0, 0] + (1 - nu) * eps[1, 1])
        sxy = (E_TPU / (1 + nu)) * eps[0, 1]
        szz = nu * (sxx + syy)
        vm = (0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2 +
                     6.0 * sxy ** 2)) ** 0.5
        return vm * v
    sb = basis.with_element(ElementTriP1())
    num = vm_proj.assemble(sb, disp=basis.interpolate(u))
    den = LinearForm(lambda v, w: 1.0 + 0.0 * w.x[0]).assemble(sb)
    return num / np.maximum(den, 1e-30)


def run_one(P_external, nu, mesh, lm, clamp_nodes, outer_facets):
    e = ElementVector(ElementTriP1())
    basis = Basis(mesh, e)
    fbasis_outer = FacetBasis(mesh, e, facets=outer_facets)
    mu, lam = material(nu)
    tng = assemble_forms(mu, lam)
    pload = pressure_traction(P_external)
    nodal = basis.nodal_dofs
    D = nodal[:, clamp_nodes].flatten()
    u = np.zeros(basis.N)
    K_mat = tng.assemble(basis)
    f = pload.assemble(fbasis_outer)
    R = K_mat @ u - f
    du = solve(*condense(K_mat, -R, D=D))
    u = u + du
    vm = von_mises_field(basis, u, nu)
    ux = u[nodal[0]]; uy = u[nodal[1]]
    disp = np.sqrt(ux**2 + uy**2)
    # contact-wall deflection: nodes near contact_x (contact face), mid-blade band
    contact_x = lm["contact_x"]
    base_y, blade_len = lm["base_y"], lm["blade_len"]
    y0 = base_y + 0.30 * blade_len; y1 = base_y + 0.70 * blade_len
    p2 = mesh.p
    cmask = (p2[0] < contact_x + 1.5) & (p2[1] > y0) & (p2[1] < y1)
    contact_disp = float(disp[cmask].max() * 1000) if cmask.any() else 0.0  # μm
    return dict(
        nu=nu, P_MPa=P_external,
        peak_vM_MPa=float(vm.max()),
        median_vM_MPa=float(np.median(vm)),
        peak_disp_um=float(disp.max() * 1000),
        contact_wall_disp_um=contact_disp,
        margin_to_yield=float(TPU_YIELD / max(vm.max(), 1e-9)),
        survives=bool(vm.max() < TPU_YIELD),
    )


def main():
    mesh, lm, clamp_nodes = load_mesh_and_clamp()
    print(f"mesh: {mesh.p.shape[1]} nodes, {mesh.t.shape[1]} tris")
    print(f"  clamp nodes: {len(clamp_nodes)}")
    outer_f, inner_f = classify_boundary_loops(mesh)
    print(f"  outer facets: {len(outer_f)}, inner facets: {len(inner_f)}")
    out = {
        "preface": ("WORST-CASE pressure-crush check: external water at P_depth, "
                    "internal Fin Ray cells TRAPPED AIR at 1 atm (gauge 0). "
                    "External skin only is loaded; inner cavity walls are "
                    "traction-free in gauge-pressure convention."),
        "boundary_topology": {
            "outer_facet_count": int(len(outer_f)),
            "inner_facet_count": int(len(inner_f)),
        },
        "material": {"E_TPU_MPa": E_TPU, "tpu_yield_MPa_estimate": TPU_YIELD},
        "runs": [],
    }
    for nu in NU_LIST:
        for depth in DEPTHS_M:
            P = RHO_G * depth
            r = run_one(P, nu, mesh, lm, clamp_nodes, outer_f)
            r["depth_m"] = depth
            out["runs"].append(r)
            survive_tag = "PASS" if r["survives"] else "FAIL"
            print(f"ν={nu:.2f}  depth={depth:5.0f}m  P={P:.3f}MPa  "
                  f"vM_peak={r['peak_vM_MPa']:7.3f}MPa  "
                  f"contact_disp={r['contact_wall_disp_um']:7.1f}μm  "
                  f"margin={r['margin_to_yield']:5.1f}×  {survive_tag}")
    outdir = os.path.join(os.path.dirname(HERE), "iterations", "_underwater_crush")
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "results.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nwrote {os.path.join(outdir, 'results.json')}")


if __name__ == "__main__":
    main()

"""3D underwater pressure-crush FEA — captures PLATE-BENDING of the
contact-face panels between ribs (the load case the 2D plane-strain
trapped-air analysis missed, because plane-strain forces εz = 0).

The Fin Ray contact face is a 1.2 mm thick TPU wall extruded 10 mm in Z,
supported by slanted ribs every ~6.4 mm in Y. In the trapped-air case
(cells fail to flood), external water at P_depth pushes the contact-face
panels INWARD between rib supports — a plate-bending mode that requires
3D resolution. Analytical bounds (Timoshenko 4-edge-supported plate):

  σ_max ≈ β · P · (b/t)²,  b/t = 6.4/1.2 = 5.33 → (b/t)² = 28.4
  simply supported:   β ≈ 0.11 → σ_max ≈ 3.1 · P
  clamped:            β ≈ 0.40 → σ_max ≈ 11 · P

The truth is somewhere in between (ribs are flexible, not rigid). This
3D FEA bounds it.

Mesh: extrude the 2D Fin Ray cross-section in N_LAYERS Z-layers (linear
tets). Pressure boundary tractions:
  outer XY perimeter (the skin):     -P · n  (external water at P_depth)
  +Z and -Z TPU silhouette faces:    -P · n  (external water also wets these)
  inner cell perimeters (cell walls): traction-free (1 atm air inside)

Run:  python fea/scripts/underwater_crush_3d.py
"""
import json
import os
import sys
import time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

# ----- material: Bambu TPU 95A HF, THROUGH-THICKNESS (Z / build) direction -----
# The dominant collapse mode here is the cells crushing through the finger's 10 mm
# thickness, which is the print build direction (Z). Bambu's ISO 527 printed-specimen
# TDS gives the WEAK Z values: E_Z = 7.4 MPa, tensile strength_Z = 22.3 MPa -- the
# honest, conservative basis for a through-thickness crush. (In-plane X-Y is stiffer:
# 9.8 MPa / 27.3 MPa.) NOTE: under load control the von Mises field is E-INDEPENDENT;
# lowering E from the old 40 -> 7.4 scales DISPLACEMENT ~5.4x (validity envelope moves
# much shallower) but leaves the stress/yield verdict driven only by strength 25 -> 22.3.
E_TPU = 7.4
NU = 0.45        # mid-value for the elastomer (0.42 ... 0.48 bracket); Bambu lists none
TPU_YIELD = 22.3

# ----- geometry / mesh -----
NLAYERS = 5      # Z layers (was 3 in iter_harness; bumped for plate-bend resolution)
Z0, Z1 = 13.0, 23.0
MESH_MIN, MESH_MAX = 0.5, 1.3

# ----- loading sweep -----
DEPTHS_M = [0.0, 10.0, 30.0, 100.0, 200.0, 300.0]
RHO_G = 1025.0 * 9.81e-6


def Dmat(nu):
    lam = E_TPU * nu / ((1 + nu) * (1 - 2 * nu)); mu = E_TPU / (2 * (1 + nu))
    D = np.zeros((6, 6)); D[:3, :3] = lam
    D[0, 0] = D[1, 1] = D[2, 2] = lam + 2 * mu
    D[3, 3] = D[4, 4] = D[5, 5] = mu
    return D


def build_section_mesh():
    """Use iter_harness's mesher to build the 2D Fin Ray section."""
    # iter_harness has a fully wired regen_section; just call it.
    sys.path.insert(0, HERE)
    import iter_harness as ih
    workdir = os.path.join(os.path.dirname(HERE), "iterations", "_underwater_crush_3d")
    os.makedirs(workdir, exist_ok=True)
    p2d, tris, lm = ih.regen_section({}, workdir)
    # iter_harness's lm has 'r_bore' as 'mount_hole_r' or similar — normalize
    if "mount_hole_r" in lm and "r_bore" not in lm:
        lm["r_bore"] = lm["mount_hole_r"]
    if "blade_len" not in lm:
        import gripper
        lm["blade_len"] = gripper.FR_BLADE_LEN
    if "contact_x" not in lm:
        lm["contact_x"] = float(p2d[:, 0].min())
    return p2d, tris, lm, workdir


def classify_2d_boundary(p2d, tris):
    """Return (outer_loop_facets, inner_loop_facets, edge_outward_n2) —
    edge sets classified by signed-area loop ranking, plus a dict of
    edge → outward-of-solid 2D normal computed via the local-triangle
    test (third vertex is on solid side; outward points away from it)."""
    # build edge list and counts
    edges = {}
    edge_to_third = {}      # edge -> third vertex of one adjacent tri
    for t in tris:
        for a, b, c in [(t[0], t[1], t[2]), (t[1], t[2], t[0]), (t[2], t[0], t[1])]:
            key = tuple(sorted((int(a), int(b))))
            edges[key] = edges.get(key, 0) + 1
            edge_to_third[key] = int(c)   # last write wins, but for boundary
                                          # edges there's only one tri so it's
                                          # always the same vertex
    bedges = [e for e, c in edges.items() if c == 1]
    # outward-of-solid 2D normal for each boundary edge
    edge_outward_n2 = {}
    for (i, j) in bedges:
        k = edge_to_third[(i, j)]
        edge_vec = p2d[j] - p2d[i]
        # 2D normal candidates: rotate edge by ±90°
        n_left = np.array([-edge_vec[1], edge_vec[0]])
        n_right = np.array([edge_vec[1], -edge_vec[0]])
        midpoint = 0.5 * (p2d[i] + p2d[j])
        # outward = away from third vertex
        away = midpoint - p2d[k]
        if np.dot(n_left, away) > np.dot(n_right, away):
            n_out = n_left
        else:
            n_out = n_right
        edge_outward_n2[(i, j)] = n_out / max(np.linalg.norm(n_out), 1e-12)
    # adjacency
    adj = {}
    for a, b in bedges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    visited = set()
    loops = []
    for start in list(adj.keys()):
        if start in visited:
            continue
        seq = [start]; visited.add(start)
        prev, cur = None, start
        while True:
            nbrs = adj[cur]
            cand = [n for n in nbrs if n != prev]
            if not cand:
                break
            nxt = cand[0]
            if nxt == start:
                break
            seq.append(nxt); visited.add(nxt)
            prev, cur = cur, nxt
            if len(seq) > len(adj) + 1:
                break
        xs = p2d[seq, 0]; ys = p2d[seq, 1]
        area = 0.5 * float(np.sum(xs * np.roll(ys, -1) - np.roll(xs, -1) * ys))
        loops.append(dict(nodes=seq, abs_area=abs(area)))
    loops.sort(key=lambda L: L["abs_area"], reverse=True)
    outer_nodes = set(loops[0]["nodes"])
    inner_nodes = set().union(*(set(L["nodes"]) for L in loops[1:]))
    # outer edges = edges with BOTH endpoints in outer_nodes; same for inner
    outer_edges = set()
    inner_edges = set()
    for e in bedges:
        a, b = e
        if a in outer_nodes and b in outer_nodes:
            outer_edges.add(e)
        elif a in inner_nodes and b in inner_nodes:
            inner_edges.add(e)
    print(f"  2D boundary: {len(loops)} loops "
          f"(outer area={loops[0]['abs_area']:.0f}, "
          f"{len(loops)-1} inner cells, "
          f"inner area total={sum(L['abs_area'] for L in loops[1:]):.0f})")
    print(f"  outer edges={len(outer_edges)}  inner edges={len(inner_edges)}")
    return outer_edges, inner_edges, outer_nodes, inner_nodes, edge_outward_n2


def build_tets_3d(p2d, tris):
    """Face-conforming prism-to-tet split.

    For each 2D triangle, sort node indices so a < b < c. Then split the
    prism (a, b, c)/(a', b', c') into 3 tets:
      (a, b, c, c'), (a, b, c', b'), (a, b', c', a')
    This uses the diagonal 'lower-bottom-index → higher-top-index' on
    every shared quad face, so adjacent prisms see matching diagonals
    and the resulting tet mesh is face-conforming (no hanging-node
    spurious modes in the FEA).
    """
    N2 = p2d.shape[0]
    zs = np.linspace(Z0, Z1, NLAYERS + 1)
    nodes = np.zeros((N2 * (NLAYERS + 1), 3))
    for k, zc in enumerate(zs):
        nodes[k * N2:(k + 1) * N2, :2] = p2d
        nodes[k * N2:(k + 1) * N2, 2] = zc
    tets = []
    for k in range(NLAYERS):
        lo, hi = k * N2, (k + 1) * N2
        for tri in tris:
            a, b, c = sorted(int(x) for x in tri)  # sort by 2D index
            a0, b0, c0 = lo + a, lo + b, lo + c
            a1, b1, c1 = hi + a, hi + b, hi + c
            tets += [(a0, b0, c0, c1), (a0, b0, c1, b1), (a0, b1, c1, a1)]
    tets = np.array(tets, np.int64)
    # ensure positive volume
    Jm = np.stack([nodes[tets][:, 1] - nodes[tets][:, 0],
                   nodes[tets][:, 2] - nodes[tets][:, 0],
                   nodes[tets][:, 3] - nodes[tets][:, 0]], axis=2)
    neg = np.linalg.det(Jm) < 0
    tets[neg] = tets[neg][:, [0, 2, 1, 3]]
    return nodes, tets, N2


def assemble_stiffness(nodes, tets):
    X = nodes[tets]
    Jm = np.stack([X[:, 1] - X[:, 0], X[:, 2] - X[:, 0], X[:, 3] - X[:, 0]], axis=2)
    invJm = np.linalg.inv(Jm); V = np.abs(np.linalg.det(Jm)) / 6.0
    dNref = np.array([[-1, -1, -1], [1, 0, 0], [0, 1, 0], [0, 0, 1]], float)
    dNdx = np.einsum('ij,njk->nik', dNref, invJm)
    Ntet = tets.shape[0]; B = np.zeros((Ntet, 6, 12))
    for i in range(4):
        gx, gy, gz = dNdx[:, i, 0], dNdx[:, i, 1], dNdx[:, i, 2]; c = 3 * i
        B[:, 0, c] = gx; B[:, 1, c + 1] = gy; B[:, 2, c + 2] = gz
        B[:, 3, c] = gy; B[:, 3, c + 1] = gx
        B[:, 4, c + 1] = gz; B[:, 4, c + 2] = gy
        B[:, 5, c] = gz; B[:, 5, c + 2] = gx
    D6 = Dmat(NU)
    Ke = np.einsum('nki,kl,nlj->nij', B, D6, B) * V[:, None, None]
    edof = (tets[:, :, None] * 3 + np.arange(3)[None, None, :]).reshape(Ntet, 12)
    nrows = nodes.shape[0] * 3
    II = np.repeat(edof, 12, axis=1).reshape(-1)
    JJ = np.tile(edof, (1, 12)).reshape(-1)
    K_data = Ke.reshape(-1)
    K = sp.csr_matrix((K_data, (II, JJ)), shape=(nrows, nrows))
    return K, B, V, edof


def enumerate_boundary_faces_with_normals(p2d, tris, outer_edges, inner_edges,
                                          edge_outward_n2, N2):
    """Enumerate boundary faces of the extruded 3D mesh DIRECTLY from the
    2D mesh — bypasses tet face-counting (which fails when adjacent prisms
    split shared quad faces along different diagonals → false boundaries).

    Each boundary face is tagged: 'z' (top/bottom TPU silhouette),
    'outer_side' (extruded outer skin), 'inner_side' (extruded cell wall).
    """
    """Return list of (n0, n1, n2, tag, outward_n3) where outward_n3 is the
    pre-computed outward-of-solid unit normal (3D vector)."""
    faces = []
    # ±Z faces — outward normals are ±Z
    n_bot = np.array([0.0, 0.0, -1.0])
    n_top = np.array([0.0, 0.0, 1.0])
    for (a, b, c) in tris:
        faces.append((int(a), int(c), int(b), "z_bot", n_bot))
        ka = NLAYERS * N2 + int(a)
        kb = NLAYERS * N2 + int(b)
        kc = NLAYERS * N2 + int(c)
        faces.append((ka, kb, kc, "z_top", n_top))
    def add_side(i, j, tag):
        n2d = edge_outward_n2[(i, j)]
        n3d = np.array([n2d[0], n2d[1], 0.0])
        for k in range(NLAYERS):
            n_i_k = k * N2 + int(i)
            n_j_k = k * N2 + int(j)
            n_j_k1 = (k + 1) * N2 + int(j)
            n_i_k1 = (k + 1) * N2 + int(i)
            faces.append((n_i_k, n_j_k, n_j_k1, tag, n3d))
            faces.append((n_i_k, n_j_k1, n_i_k1, tag, n3d))
    for (a, b) in outer_edges:
        add_side(a, b, "outer_side")
    for (a, b) in inner_edges:
        add_side(a, b, "inner_side")
    return faces


def face_area(nodes, face_tri):
    """Compute the (oriented-agnostic) area of a triangular face."""
    a, b, c = face_tri[0], face_tri[1], face_tri[2]
    Xa, Xb, Xc = nodes[a], nodes[b], nodes[c]
    nvec = np.cross(Xb - Xa, Xc - Xa)
    return 0.5 * float(np.linalg.norm(nvec))


def pressure_load_vector(nodes, faces_tagged, p2d, outer_edges, N2, P_depth, lm,
                         flooded=False):
    """Build f from pressure tractions on enumerated boundary faces.

    Trapped-air load rules (default, flooded=False):
      - z_top / z_bot:    TPU silhouette wetted by external water → -P n
      - outer_side:       extruded outer skin → -P n
      - inner_side:       Fin Ray cell wall, trapped air at 1 atm → 0

    Flooded sanity-check (flooded=True):
      - ALL faces (including inner cavity walls) → -P n.
      - Expected result: σ_ij = -P δ_ij, vM ≈ 0, |f_net| ≈ 0.
    """
    f = np.zeros(nodes.shape[0] * 3)
    stats = dict(n_z=0, n_outer=0, n_inner=0)
    f_net = np.zeros(3)
    for face_tri in faces_tagged:
        a, b, c, tag, n_unit = face_tri
        is_inner = (tag == "inner_side")
        if is_inner and not flooded:
            stats["n_inner"] += 1
            continue
        area = face_area(nodes, face_tri)
        if area < 1e-12:
            continue
        traction = -P_depth * n_unit
        for nd in (a, b, c):
            f[3 * nd:3 * nd + 3] += area / 3.0 * traction
        f_net += area * traction
        if tag.startswith("z"):
            stats["n_z"] += 1
        elif tag == "outer_side":
            stats["n_outer"] += 1
        else:
            stats["n_inner"] += 1
    stats["f_net"] = [float(x) for x in f_net]
    return f, stats


def clamp_dofs(nodes, lm, N2):
    """Clamp mount-bore nodes at every Z-layer."""
    C, D = np.array(lm["C"]), np.array(lm["D"])
    rmh = lm["r_bore"]
    p2 = nodes[:N2, :2]
    def near(pt, r): return np.hypot(p2[:, 0] - pt[0], p2[:, 1] - pt[1]) <= r + 0.8
    clamp_2d = np.where(near(C, rmh) | near(D, rmh))[0]
    # extend over all Z-layers
    dofs = []
    for k in range(NLAYERS + 1):
        for n2 in clamp_2d:
            n_global = k * N2 + n2
            dofs.extend([3 * n_global, 3 * n_global + 1, 3 * n_global + 2])
    return np.array(dofs, dtype=np.int64), len(clamp_2d)


def solve_linear(K, f, clamp_dofs_arr, nrows):
    """Solve K u = f with clamped DOFs."""
    keep = np.setdiff1d(np.arange(nrows), clamp_dofs_arr)
    Kr = K[keep, :][:, keep]
    fr = f[keep]
    u_red = spla.spsolve(Kr.tocsc(), fr)
    u = np.zeros(nrows)
    u[keep] = u_red
    return u


def von_mises_per_tet(B, V, u, edof):
    """Compute element-averaged Cauchy von Mises stress."""
    Ntet = B.shape[0]
    ue = u[edof]   # (Ntet, 12)
    eps = np.einsum('nij,nj->ni', B, ue)  # (Ntet, 6)  voigt strain
    D6 = Dmat(NU)
    sig = eps @ D6.T   # (Ntet, 6)
    sxx, syy, szz = sig[:, 0], sig[:, 1], sig[:, 2]
    sxy, syz, sxz = sig[:, 3], sig[:, 4], sig[:, 5]
    vm = np.sqrt(0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 +
                        (szz - sxx) ** 2 +
                        6.0 * (sxy ** 2 + syz ** 2 + sxz ** 2)))
    return vm, sig


def main():
    t0 = time.time()
    p2d, tris, lm, workdir = build_section_mesh()
    print(f"2D mesh: {p2d.shape[0]} nodes, {tris.shape[0]} tris")
    outer_edges, inner_edges, _, _, edge_outward_n2 = classify_2d_boundary(p2d, tris)
    nodes, tets, N2 = build_tets_3d(p2d, tris)
    print(f"3D mesh: {nodes.shape[0]} nodes, {tets.shape[0]} tets, {NLAYERS} Z-layers")
    print(f"  DOFs total: {nodes.shape[0] * 3}")
    print("  assembling stiffness ...")
    K, B, V, edof = assemble_stiffness(nodes, tets)
    print(f"  K nnz={K.nnz}, shape={K.shape}")
    print("  enumerating boundary faces from 2D mesh ...")
    faces_tagged = enumerate_boundary_faces_with_normals(
        p2d, tris, outer_edges, inner_edges, edge_outward_n2, N2)
    n_z = sum(1 for f in faces_tagged if f[3].startswith("z"))
    n_o = sum(1 for f in faces_tagged if f[3] == "outer_side")
    n_i = sum(1 for f in faces_tagged if f[3] == "inner_side")
    print(f"  total boundary tri faces: {len(faces_tagged)} "
          f"(z: {n_z}, outer_side: {n_o}, inner_side: {n_i})")
    clamp_d, n_clamp_2d = clamp_dofs(nodes, lm, N2)
    print(f"  clamp 2D nodes: {n_clamp_2d}, total clamp DOFs: {len(clamp_d)}")

    nrows = nodes.shape[0] * 3
    out = {
        "mesh": {"n_nodes_2d": int(p2d.shape[0]), "n_tris": int(tris.shape[0]),
                 "n_nodes_3d": int(nodes.shape[0]), "n_tets": int(tets.shape[0]),
                 "n_layers": NLAYERS, "ndof": int(nrows)},
        "material": {"E_TPU": E_TPU, "nu": NU, "yield": TPU_YIELD},
        "load_case": "TRAPPED AIR — outer skin (perimeter + ±Z TPU silhouette) "
                     "wetted at P_depth; inner cell walls traction-free",
        "runs": [],
    }

    contact_x = lm.get("contact_x", float(p2d[:, 0].min()))
    base_y, blade_len = lm["base_y"], lm["blade_len"]
    y0 = base_y + 0.30 * blade_len; y1 = base_y + 0.70 * blade_len
    # 3D contact-wall nodes (near contact_x, within mid-blade Y band, any Z)
    nodes_arr = nodes
    cmask_3d = ((nodes_arr[:, 0] < contact_x + 1.5) &
                (nodes_arr[:, 1] > y0) &
                (nodes_arr[:, 1] < y1))

    # ---- SANITY CHECK: flooded case at 100 m should give σ=-PI, vM≈0 ----
    print("\n  SANITY CHECK: flooded case (pressure on ALL surfaces)")
    P_check = RHO_G * 100.0
    f_fl, st_fl = pressure_load_vector(nodes, faces_tagged, p2d, outer_edges,
                                        N2, P_check, lm, flooded=True)
    print(f"    flooded f_net = {st_fl['f_net']} (should be ~0)")
    u_fl = solve_linear(K, f_fl, clamp_d, nrows)
    vm_fl, sig_fl = von_mises_per_tet(B, V, u_fl, edof)
    print(f"    flooded peak vM = {float(vm_fl.max()):.4f} MPa (should be ~0)")
    print(f"    flooded mean σ_xx = {float(sig_fl[:, 0].mean()):+.4f} MPa "
          f"(should be ~{-P_check:+.4f})")
    print(f"    flooded peak |u| = {float(np.linalg.norm(u_fl.reshape(-1,3), axis=1).max())*1000:.1f} μm")

    # also print trapped-air f_net at 100 m for diagnostic
    f_ta, st_ta = pressure_load_vector(nodes, faces_tagged, p2d, outer_edges,
                                        N2, RHO_G * 100.0, lm, flooded=False)
    print(f"    trapped-air f_net @ 100 m = {st_ta['f_net']} N (nonzero — net "
          f"inward force on solid from outside-pressure-without-inside-balance)")

    for depth in DEPTHS_M:
        P = RHO_G * depth
        f, stats = pressure_load_vector(nodes, faces_tagged, p2d,
                                         outer_edges, N2, P, lm)
        if depth == DEPTHS_M[0]:
            print(f"  boundary face classification: {stats}")
        u = solve_linear(K, f, clamp_d, nrows)
        vm_tet, sig = von_mises_per_tet(B, V, u, edof)
        disp = u.reshape(-1, 3)
        disp_norm = np.linalg.norm(disp, axis=1)
        contact_disp_um = float(disp_norm[cmask_3d].max() * 1000) if cmask_3d.any() else 0.0
        r = dict(
            depth_m=depth, P_MPa=P,
            peak_vM_MPa=float(vm_tet.max()),
            median_vM_MPa=float(np.median(vm_tet)),
            peak_disp_um=float(disp_norm.max() * 1000),
            contact_wall_disp_um=contact_disp_um,
            margin_to_yield=float(TPU_YIELD / max(vm_tet.max(), 1e-9)),
            survives=bool(vm_tet.max() < TPU_YIELD),
        )
        out["runs"].append(r)
        print(f"  depth={depth:5.0f}m  P={P:.3f}MPa  "
              f"vM_peak={r['peak_vM_MPa']:7.3f}MPa  "
              f"contact_disp={contact_disp_um:7.1f}μm  "
              f"margin={r['margin_to_yield']:5.1f}×  "
              f"{'PASS' if r['survives'] else 'FAIL'}")

    out_dir = os.path.join(os.path.dirname(HERE), "iterations", "_underwater_crush_3d")
    os.makedirs(out_dir, exist_ok=True)
    json.dump(out, open(os.path.join(out_dir, "results.json"), "w"), indent=2)
    print(f"\nwrote {os.path.join(out_dir, 'results.json')}")
    print(f"total runtime: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()

"""Bake the FEA Fin Ray wrap onto the real 3D finger meshes as Blender shape-key
targets. For each finger: write <finger>_base.obj and <finger>_wrap.obj from the
SAME vertex array (identical topology -> Blender shape keys just work). The wrap
displacement comes from the 2D plane-strain FEA (finray_morph.npz), applied by
nearest-node lookup in the section plane (z preserved -> the 2.5-D extrusion).

finger_R uses the FEA field directly; finger_L mirrors it about x=0.
"""
import os, numpy as np, meshio
from scipy.spatial import cKDTree

HERE = os.path.dirname(__file__)
GEO = os.path.normpath(os.path.join(HERE, "..", "render_bundle", "geometry"))
FEA = os.path.normpath(os.path.join(HERE, "..", "render_bundle", "fea"))

M = np.load(os.path.join(FEA, "finray_morph.npz"))
rest = M["rest"].astype(float)          # (2, N)
frames = M["frames"].astype(float)      # (F, 2, N)
full = frames[-1]                       # peak-wrap deformed section (2, N)
disp = (full - rest).T                  # (N, 2) per-FEA-node displacement
tree = cKDTree(rest.T)                  # FEA nodes in section xy


def bake(stl_path, out_base, out_wrap, mirror=False):
    m = meshio.read(stl_path)
    P = m.points.astype(float).copy()           # (V, 3), meshio vertex order
    cells = [c for c in m.cells if c.type == "triangle"]
    xy = P[:, :2].copy()
    if mirror:
        xy[:, 0] = -xy[:, 0]                     # map L finger onto R FEA field
    _, idx = tree.query(xy)
    d = disp[idx].copy()                         # (V, 2)
    if mirror:
        d[:, 0] = -d[:, 0]                       # mirror displacement back
    Pw = P.copy()
    Pw[:, 0] += d[:, 0]
    Pw[:, 1] += d[:, 1]
    meshio.write_points_cells(out_base, P, cells)
    meshio.write_points_cells(out_wrap, Pw, cells)
    tipmove = np.linalg.norm(d, axis=1).max()
    print(f"  {os.path.basename(stl_path)}: V={len(P)} max vertex move={tipmove:.1f} mm "
          f"{'(mirrored)' if mirror else ''}")


print("baking finger shape-key targets ...")
bake(os.path.join(GEO, "parts_open0", "finger_R.stl"),
     os.path.join(GEO, "finger_R_base.obj"),
     os.path.join(GEO, "finger_R_wrap.obj"), mirror=False)
bake(os.path.join(GEO, "parts_open0", "finger_L.stl"),
     os.path.join(GEO, "finger_L_base.obj"),
     os.path.join(GEO, "finger_L_wrap.obj"), mirror=True)
print("wrote finger_{R,L}_{base,wrap}.obj to", GEO)

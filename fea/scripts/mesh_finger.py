"""Mesh the finger section STEP with gmsh -> triangle mesh for scikit-fem.
Reports element count + quality, saves mesh.npz (p: 2xN nodes, t: 3xM tris)."""
import os, sys, numpy as np, gmsh

HERE = os.path.dirname(__file__)
STEP = os.path.join(HERE, "finger_section.step")
SIZE_MAX = float(sys.argv[1]) if len(sys.argv) > 1 else 1.3
SIZE_MIN = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5

gmsh.initialize()
gmsh.option.setNumber("General.Terminal", 0)
gmsh.open(STEP)
gmsh.model.occ.synchronize()
gmsh.option.setNumber("Mesh.MeshSizeMax", SIZE_MAX)
gmsh.option.setNumber("Mesh.MeshSizeMin", SIZE_MIN)
gmsh.option.setNumber("Mesh.Algorithm", 6)        # Frontal-Delaunay
gmsh.model.mesh.generate(2)
gmsh.model.mesh.optimize("Netgen")

ntags, ncoords, _ = gmsh.model.mesh.getNodes()
coords = ncoords.reshape(-1, 3)
tag2idx = {int(t): i for i, t in enumerate(ntags)}

etypes, etags, enodes = gmsh.model.mesh.getElements(dim=2)
tris = None
for et, en in zip(etypes, enodes):
    if et == 2:  # 3-node triangle
        tris = en.reshape(-1, 3)
assert tris is not None, "no triangles"
t = np.array([[tag2idx[int(n)] for n in tri] for tri in tris], dtype=np.int64)
p = coords[:, :2]

# quality: min/mean triangle area + min angle
def tri_quality(p, t):
    a = p[t[:, 0]]; b = p[t[:, 1]]; c = p[t[:, 2]]
    area = 0.5 * np.abs((b[:, 0]-a[:, 0])*(c[:, 1]-a[:, 1]) -
                        (c[:, 0]-a[:, 0])*(b[:, 1]-a[:, 1]))
    # min angle per tri
    def ang(u, v):
        cu = np.einsum('ij,ij->i', u, v)
        nu = np.linalg.norm(u, axis=1)*np.linalg.norm(v, axis=1)
        return np.degrees(np.arccos(np.clip(cu/np.maximum(nu, 1e-30), -1, 1)))
    A = ang(b-a, c-a); B = ang(a-b, c-b); C = 180-A-B
    return area, np.minimum(np.minimum(A, B), C)

area, minang = tri_quality(p, t)
print(f"mesh: {p.shape[0]} nodes, {t.shape[0]} tris (size {SIZE_MIN}-{SIZE_MAX})")
print(f"  area  min={area.min():.4f} mean={area.mean():.3f} mm^2")
print(f"  minangle  worst={minang.min():.1f} deg  (slivers<15deg: {(minang<15).sum()})")
print(f"  bbox X[{p[:,0].min():.2f},{p[:,0].max():.2f}] Y[{p[:,1].min():.2f},{p[:,1].max():.2f}]")

np.savez(os.path.join(HERE, "mesh.npz"), p=p.T, t=t.T)
print("wrote mesh.npz  (p shape 2xN, t shape 3xM)")
gmsh.finalize()

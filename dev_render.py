"""
Tiny software renderer for build123d solids -> PNG, no GUI deps.
Tessellates via OCP, projects with a simple camera, painter's-algorithm
fill + Lambert shading with Pillow. Enough to verify snap-pin geometry.
"""
from __future__ import annotations

import math
import numpy as np
from PIL import Image, ImageDraw
from build123d import Compound

from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.TopLoc import TopLoc_Location
from OCP.BRep import BRep_Tool
from OCP.TopoDS import TopoDS


def _tris_for_shape(shape, color):
    """Return (Nx3x3 verts, Nx3 face-color) triangle arrays for one shape."""
    BRepMesh_IncrementalMesh(shape, 0.25, False, 0.5, True)
    verts = []
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS.Face_s(exp.Current())
        loc = TopLoc_Location()
        tri = BRep_Tool.Triangulation_s(face, loc)
        if tri is not None:
            trsf = loc.Transformation()
            nb = tri.NbNodes()
            nodes = []
            for i in range(1, nb + 1):
                p = tri.Node(i).Transformed(trsf)
                nodes.append((p.X(), p.Y(), p.Z()))
            rev = face.Orientation().value == 1  # TopAbs_REVERSED
            for i in range(1, tri.NbTriangles() + 1):
                t = tri.Triangle(i)
                a, b, c = t.Get()
                if rev:
                    a, c = c, a
                verts.append((nodes[a - 1], nodes[b - 1], nodes[c - 1]))
        exp.Next()
    if not verts:
        return np.zeros((0, 3, 3)), color
    return np.array(verts, dtype=float), color


def collect(asm):
    """Walk a Compound -> list of (tris, rgb)."""
    out = []
    def rgb(c):
        if c is None:
            return (0.7, 0.7, 0.72)
        try:
            return (c.red, c.green, c.blue)
        except Exception:
            t = tuple(c)
            return (t[0], t[1], t[2])
    def walk(node):
        kids = getattr(node, "children", None)
        if kids:
            for k in kids:
                walk(k)
        else:
            tris, _ = _tris_for_shape(node.wrapped, None)
            if len(tris):
                out.append((tris, rgb(node.color)))
    walk(asm)
    return out


def render(tri_groups, path, eye, target, up=(0, 0, 1), size=(1100, 850),
           clip=None, bg=(250, 250, 252), fov_scale=1.0):
    """Project + paint. clip=('x'|'y'|'z', lo, hi) keeps only triangles whose
    centroid lies in [lo,hi] along that axis (for cut views)."""
    eye = np.array(eye, float)
    target = np.array(target, float)
    up = np.array(up, float)
    fwd = target - eye
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    trueup = np.cross(right, fwd)
    light = np.array([0.3, -0.5, 0.8])
    light = light / np.linalg.norm(light)

    W, H = size
    all_tris, all_col, all_depth = [], [], []
    axidx = {"x": 0, "y": 1, "z": 2}
    for tris, col in tri_groups:
        for tri in tris:
            cen = tri.mean(axis=0)
            if clip is not None:
                ax, lo, hi = clip
                v = cen[axidx[ax]]
                if v < lo or v > hi:
                    continue
            rel = tri - eye
            cam = np.stack([rel @ right, rel @ trueup, rel @ fwd], axis=1)
            if np.any(cam[:, 2] <= 0.05):
                continue
            n = np.cross(tri[1] - tri[0], tri[2] - tri[0])
            nn = np.linalg.norm(n)
            if nn < 1e-9:
                continue
            n = n / nn
            shade = 0.32 + 0.68 * max(0.0, abs(float(n @ light)))
            depth = float(np.linalg.norm(cen - eye))
            all_tris.append(cam)
            all_col.append(tuple(int(255 * min(1.0, c * shade)) for c in col))
            all_depth.append(depth)

    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)
    if not all_tris:
        img.save(path)
        return path
    order = np.argsort(all_depth)[::-1]  # far -> near
    allc = np.array([t[:, :2] for t in all_tris])  # (N,3,2) camera xy
    # scale to fit
    flat = allc.reshape(-1, 2)
    span = max(flat[:, 0].max() - flat[:, 0].min(),
               flat[:, 1].max() - flat[:, 1].min())
    scale = (min(W, H) * 0.82 / span) * fov_scale
    cx, cy = W / 2.0, H / 2.0
    mx = flat[:, 0].mean()
    my = flat[:, 1].mean()
    for idx in order:
        cam = all_tris[idx]
        pts = []
        for vx, vy, _ in cam:
            sx = cx + (vx - mx) * scale
            sy = cy - (vy - my) * scale
            pts.append((sx, sy))
        draw.polygon(pts, fill=all_col[idx])
    img.save(path)
    return path


if __name__ == "__main__":
    import dev_snappin
    asm = dev_snappin.gen_step()
    groups = collect(asm)
    # iso view
    render(groups, "dev_snappin_iso.png",
           eye=(45, -55, 70), target=(14, 0, 11))
    # side view (look along -X): shows head, shaft, barb lip + slot profile
    render(groups, "dev_snappin_side.png",
           eye=(120, 0, 11), target=(14, 0, 11), up=(0, 0, 1))
    # cut view: keep only y>=0 half so the slot + barb interior are visible
    render(groups, "dev_snappin_cut.png",
           eye=(70, -70, 30), target=(14, 0, 11), clip=("y", -0.01, 50))

    # close-up cut of JUST the internal axle barb springing past the far boss
    axle = dev_snappin.snap_pin((0, 0), -2.0, 22.0, head_at="z0",
                                label="axle", color=dev_snappin.PIN_COLOR)
    boss = dev_snappin.bore_block((0, 0), -2.0, 22.0,
                                  dev_snappin.AXLE_BORE_R, far_face_z=22.0)
    closeup = collect(Compound(label="cu", children=[axle, boss]))
    render(closeup, "dev_snappin_barb_closeup.png",
           eye=(34, -30, 30), target=(0, 0, 22.0), up=(0, 0, 1),
           clip=("y", -0.01, 50), fov_scale=1.5, size=(1000, 1000))

    # clean side profile of the internal-axle pin ALONE (no boss occluding):
    # head flange at the bottom, unbroken bearing shank, barb lip + split tip.
    pinonly = collect(Compound(label="po", children=[axle]))
    render(pinonly, "dev_snappin_pin_side.png",
           eye=(120, 0, 12.0), target=(0, 0, 12.0), up=(0, 0, 1),
           fov_scale=1.4, size=(700, 1000))
    print("wrote: dev_snappin_iso.png dev_snappin_side.png dev_snappin_cut.png "
          "dev_snappin_barb_closeup.png dev_snappin_pin_side.png")

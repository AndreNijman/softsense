#!/usr/bin/env python3
"""render_iso.py -- headless GPU (EGL) iso renders of the gripper / its parts.

Replaces the removed browser "snapshot" tool. Uses pyrender + EGL offscreen
(GPU at /dev/dri), trimesh for mesh handling, build123d to tessellate the live
parametric model with its per-part colors.

Sub-commands:
  assembly  --pose P --out X.png            render gripper.gen_step() at pose P
  exploded  --pose P --out X.png            same, pins+caps pulled out along their axis
  system    --variant V --pose P --out X.png  render motor/cad/system_assembly.py
  meshes    --glob 'parts/*.stl' --out X.png   quick render of loose STLs (pipeline test)

Common: --width --height --azim --elev --bg {studio,technical,dark}
"""
from __future__ import annotations
import os, sys, argparse, math, glob
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import trimesh
import pyrender
import imageio.v2 as imageio

BG = {
    "studio":   (0.93, 0.94, 0.96),
    "technical":(0.88, 0.90, 0.93),
    "dark":     (0.10, 0.11, 0.13),
}


def _tess_color(leaf, tol):
    """Tessellate a build123d leaf solid -> (verts Nx3, faces Mx3, rgba)."""
    try:
        verts, tris = leaf.tessellate(tolerance=tol)
    except Exception:
        return None
    if not tris:
        return None
    V = np.array([(v.X, v.Y, v.Z) for v in verts], dtype=np.float64)
    F = np.array(tris, dtype=np.int64)
    c = getattr(leaf, "color", None)
    if c is not None:
        try:
            rgba = (c.red, c.green, c.blue, getattr(c, "alpha", 1.0))
        except Exception:
            try:
                rgba = tuple(c)[:4]
            except Exception:
                rgba = (0.6, 0.62, 0.66, 1.0)
    else:
        rgba = (0.6, 0.62, 0.66, 1.0)
    if len(rgba) == 3:
        rgba = (*rgba, 1.0)
    return V, F, rgba


def assembly_meshes(pose, tol=0.4, explode=0.0):
    """Build gripper.gen_step() at `pose`, return [(trimesh, rgba)] with colors.
    explode>0 pulls pin_/cap_ parts outward along the world pin axis (+/-Y)."""
    os.environ["GRIPPER_OPEN"] = str(pose)
    for m in list(sys.modules):
        if m == "gripper":
            del sys.modules[m]
    import gripper
    asm = gripper.gen_step()
    out = []
    for leaf in asm.children:
        lbl = getattr(leaf, "label", "") or ""
        tc = _tess_color(leaf, tol)
        if tc is None:
            continue
        V, F, rgba = tc
        if explode and (lbl.startswith("pin_") or lbl.startswith("cap_")):
            # pins lie along world Y (model +Z -> world -Y); pull caps out further.
            d = explode * (1.6 if lbl.startswith("cap_") else 1.0)
            V = V.copy(); V[:, 1] -= d
        tm = trimesh.Trimesh(vertices=V, faces=F, process=False)
        out.append((tm, rgba, lbl))
    return out


def system_meshes(variant, pose, tol=0.5):
    os.environ["GRIPPER_CANISTER_VARIANT"] = variant
    os.environ["GRIPPER_CANISTER_SERVO"] = os.environ.get("GRIPPER_CANISTER_SERVO", "STS3250")
    os.environ["GRIPPER_OPEN"] = str(pose)
    for m in list(sys.modules):
        if m.startswith("gripper") or "system_assembly" in m:
            del sys.modules[m]
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "system_assembly", os.path.join(os.path.dirname(__file__), "..",
                                         "motor", "cad", "system_assembly.py"))
    sa = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sa)
    # pick the builder for the requested variant
    builder = {"T2_XRAY": "assemble_t2_xray",
               "T2_UNIBODY": "assemble_t2_unibody",
               "T2": "assemble_t2",
               "T3": "assemble_t3"}.get(variant.upper(), "assemble_t2_unibody")
    asm = getattr(sa, builder)()
    out = []
    leaves = asm.children if hasattr(asm, "children") and asm.children else [asm]
    for leaf in leaves:
        tc = _tess_color(leaf, tol)
        if tc is None:
            continue
        V, F, rgba = tc
        out.append((trimesh.Trimesh(vertices=V, faces=F, process=False), rgba,
                    getattr(leaf, "label", "")))
    return out


def stl_meshes(globpat):
    out = []
    palette = [(0.27,0.29,0.33,1),(0.58,0.61,0.65,1),(0.85,0.55,0.25,1),
               (0.12,0.13,0.15,1),(0.74,0.76,0.79,1)]
    for i, p in enumerate(sorted(glob.glob(globpat))):
        tm = trimesh.load(p, force="mesh")
        out.append((tm, palette[i % len(palette)], os.path.basename(p)))
    return out


def render(meshes, out_png, width=1400, height=1050, azim=35.0, elev=22.0,
           bg="studio", zoom=1.0):
    scene = pyrender.Scene(bg_color=(*BG[bg], 1.0), ambient_light=(0.35, 0.35, 0.38))
    allpts = []
    for tm, rgba, _ in meshes:
        mat = pyrender.MetallicRoughnessMaterial(
            baseColorFactor=list(rgba), metallicFactor=0.25, roughnessFactor=0.55,
            alphaMode="BLEND" if rgba[3] < 0.999 else "OPAQUE")
        pm = pyrender.Mesh.from_trimesh(tm, material=mat, smooth=False)
        scene.add(pm)
        allpts.append(tm.bounds)
    allpts = np.array(allpts)
    lo = allpts[:, 0, :].min(0); hi = allpts[:, 1, :].max(0)
    center = (lo + hi) / 2.0
    radius = float(np.linalg.norm(hi - lo)) / 2.0

    # iso camera looking at center
    a = math.radians(azim); e = math.radians(elev)
    dir_cam = np.array([math.cos(e)*math.sin(a), math.sin(e), math.cos(e)*math.cos(a)])
    dist = radius / max(0.2, zoom) * 2.6
    eye = center + dir_cam * dist
    # build look-at pose
    up = np.array([0, 1, 0], dtype=float)
    f = (center - eye); f /= np.linalg.norm(f)
    s = np.cross(f, up); s /= np.linalg.norm(s)
    u = np.cross(s, f)
    pose = np.eye(4)
    pose[:3, 0] = s; pose[:3, 1] = u; pose[:3, 2] = -f; pose[:3, 3] = eye
    cam = pyrender.PerspectiveCamera(yfov=math.radians(35), aspectRatio=width/height)
    scene.add(cam, pose=pose)
    # key + fill + rim
    for off, inten in (((1,1.4,1), 4.0), ((-1.2,0.6,0.4), 1.8), ((0.2,-0.6,-1), 1.2)):
        lp = np.eye(4); ld = np.array(off, float)
        leye = center + ld/np.linalg.norm(ld) * dist
        ff = (center-leye); ff/=np.linalg.norm(ff)
        ss = np.cross(ff, up);
        if np.linalg.norm(ss) < 1e-6: ss = np.array([1,0,0.])
        ss/=np.linalg.norm(ss); uu = np.cross(ss, ff)
        lp[:3,0]=ss; lp[:3,1]=uu; lp[:3,2]=-ff; lp[:3,3]=leye
        scene.add(pyrender.DirectionalLight(color=[1,1,1], intensity=inten), pose=lp)

    r = pyrender.OffscreenRenderer(width, height)
    color, _ = r.render(scene)
    r.delete()
    if out_png:
        imageio.imwrite(out_png, color)
        print(f"  wrote {out_png}  ({width}x{height}, {len(meshes)} parts)")
    return color


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("assembly", "exploded", "system", "meshes"):
        p = sub.add_parser(name)
        p.add_argument("--out", required=True)
        p.add_argument("--pose", type=float, default=0.0)
        p.add_argument("--variant", default="T2_UNIBODY")
        p.add_argument("--glob", default="parts/*.stl")
        p.add_argument("--width", type=int, default=1400)
        p.add_argument("--height", type=int, default=1050)
        p.add_argument("--azim", type=float, default=35.0)
        p.add_argument("--elev", type=float, default=22.0)
        p.add_argument("--bg", default="studio")
        p.add_argument("--explode", type=float, default=14.0)
        p.add_argument("--zoom", type=float, default=1.0)
    a = ap.parse_args()
    if a.cmd == "assembly":
        meshes = assembly_meshes(a.pose)
    elif a.cmd == "exploded":
        meshes = assembly_meshes(a.pose, explode=a.explode)
    elif a.cmd == "system":
        meshes = system_meshes(a.variant, a.pose)
    else:
        meshes = stl_meshes(a.glob)
    render(meshes, a.out, a.width, a.height, a.azim, a.elev, a.bg, a.zoom)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Proper-3D FEA renders: deformed finger tet-mesh + full-assembly composite.

Renders the actual 3D solution in fea/iterations/<name>/fea3d_solution.npz
(rest/tets/frames/vms per load step + the rigid grasped object) with VTK
offscreen, and composites the von-Mises-colored DEFORMED finger(s) into the
full gripper assembly built from gripper.py.

Subcommands
-----------
  finger         stills of the deformed finger (vM colormap) from 3 views
  finger-anim    closing animation over all load steps + turntable orbit
                 at the grasp frame -> MP4 + palette GIF
  assembly       full-gripper composite stills: CAD parts in neutral grey,
                 BOTH CAD fingers replaced by the FEA deformed surface
                 (right = as-solved, left = mirrored), grasped cylinder
                 on the centreline
  assembly-anim  closing sequence sweeping FEA load steps + assembly pose
                 together -> MP4 + palette GIF
  tess-worker    (internal) tessellate one gripper pose to a mesh cache

Coordinate frames
-----------------
The FEA mesh lives in gripper MODEL coords of the RIGHT finger at the CLOSED
pose (GRIPPER_OPEN=0): XY = kinematics plane, Z = finger thickness (13..23 mm),
object = rigid cylinder, axis || Z, centre (xc0 + press[k], yc).

Assembly mapping (per FEA step k):
  1. solve GRIPPER_OPEN o_k so that the rigidly-transported FEA object centre
     lands on the gripper centreline x=0 (bisection on the four-bar transform
     T(o) = Trans(C(o)) RotZ(ang(o)-ang(0)) Trans(-C(0)), exactly how
     gripper.finger() mounts the CAD finger);
  2. transport the WHOLE deformed FEA scene (finger surface + object) by
     T(o_k) for the right finger; mirror x -> -x for the left finger;
  3. reorient model->world like gen_step(): (x, y, z) -> (x, -z, y) (Z-up).
Honesty: the FEA was a single-finger displacement-controlled press, NOT the
four-bar closing on a free object — the caption on every assembly frame says
so. The pose mapping is plausible, not kinematically exact.

Backend: VTK 9.3 offscreen (verified to produce non-black frames on this box).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

DEFAULT_OUT = REPO / "renders" / "fea3d"
FFMPEG = "/usr/bin/ffmpeg"

# --------------------------------------------------------------------------- #
# Solution loading
# --------------------------------------------------------------------------- #
def load_solution(args):
    if args.npz:
        path = Path(args.npz)
        name = path.parent.name
    else:
        name = args.iter
        path = REPO / "fea" / "iterations" / name / "fea3d_solution.npz"
    if not path.exists():
        sys.exit(f"[err] no solution npz at {path}")
    d = np.load(path, allow_pickle=True)
    sol = dict(
        name=name,
        rest=np.asarray(d["rest"], float),
        tets=np.asarray(d["tets"], np.int64),
        frames=np.asarray(d["frames"], np.float32),
        vms=np.asarray(d["vms"], np.float32),
        grip=np.asarray(d["grip"], float),
        press=np.asarray(d["press"], float),
        xc0=float(d["xc0"]), yc=float(d["yc"]), R=float(d["R_neck"]),
        shape=str(d["obj_shape"]),
    )
    sol["nsteps"] = sol["frames"].shape[0]
    sol["vmax"] = max(0.5, float(sol["vms"].max()))
    return sol


def step_index(args, sol):
    k = args.step
    if k < 0:
        k = sol["nsteps"] + k
    return max(0, min(sol["nsteps"] - 1, k))


# --------------------------------------------------------------------------- #
# Boundary surface of the tet mesh (faces appearing exactly once), oriented
# outward via the opposite tet vertex (computed on the REST config).
# --------------------------------------------------------------------------- #
def boundary_faces(tets, rest):
    fi = np.array([[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]])
    opp = np.array([3, 2, 1, 0])
    tris = tets[:, fi].reshape(-1, 3)                 # (4M,3)
    opps = tets[:, opp].reshape(-1)                   # (4M,)
    key = np.sort(tris, axis=1)
    _, first, counts = np.unique(key, axis=0, return_index=True,
                                 return_counts=True)
    sel = first[counts == 1]
    tri = tris[sel].copy()
    ov = opps[sel]
    p0, p1, p2 = rest[tri[:, 0]], rest[tri[:, 1]], rest[tri[:, 2]]
    n = np.cross(p1 - p0, p2 - p0)
    inward = np.einsum("ij,ij->i", n, rest[ov] - p0) > 0.0
    tri[inward] = tri[inward][:, ::-1]               # flip so normals point OUT
    return np.ascontiguousarray(tri)


# --------------------------------------------------------------------------- #
# Kinematics: FEA(closed right finger) frame -> posed model frame -> world
# --------------------------------------------------------------------------- #
_grip_mod = None


def grip():
    global _grip_mod
    if _grip_mod is None:
        os.environ.setdefault("GRIPPER_OPEN", "0")
        import gripper as g
        _grip_mod = g
    return _grip_mod


def rigid_T(open_norm):
    """2D rigid transform (R, t) mapping the closed-pose right finger frame to
    the right finger at GRIPPER_OPEN=open_norm (same construction as
    gripper.finger())."""
    g = grip()
    ref = g.solve_side_right(0.0)
    cur = g.solve_side_right(open_norm)
    a = math.radians(cur["coupler_ang"] - ref["coupler_ang"])
    R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
    C0 = np.array(ref["C"])
    C1 = np.array(cur["C"])
    t = C1 - R @ C0
    return R, t


def apply_T(pts3, R, t):
    """Apply the planar rigid transform to (N,3) model-frame points (z kept).
    Left finger = x-mirror of the ALREADY-POSED right-side points (the
    assembly is symmetric about x=0), see assembly_scene()."""
    p = np.array(pts3, float)
    p[:, :2] = p[:, :2] @ R.T + t
    return p


def model_to_world(pts3):
    """gen_step() final reorient: RotX(+90): (x, y, z) -> (x, -z, y)."""
    p = np.asarray(pts3, float)
    return np.stack([p[:, 0], -p[:, 2], p[:, 1]], axis=1)


def solve_open_for_step(sol, k):
    """GRIPPER_OPEN o so the transported FEA object centre lands on x=0."""
    ctr = np.array([[sol["xc0"] + sol["press"][k], sol["yc"], 0.0]])

    def fx(o):
        R, t = rigid_T(o)
        return apply_T(ctr.copy(), R, t)[0, 0]

    lo, hi = 0.0, 1.0
    if fx(lo) > 0.0:
        return 0.0
    if fx(hi) < 0.0:
        return 1.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if fx(mid) < 0.0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# --------------------------------------------------------------------------- #
# VTK scene
# --------------------------------------------------------------------------- #
THEMES = {
    "dark": dict(bg=(0.082, 0.090, 0.105), fg=(0.92, 0.93, 0.95),
                 fg2=(0.62, 0.65, 0.70), accent=(0.18, 0.72, 0.68)),
    "white": dict(bg=(1.0, 1.0, 1.0), fg=(0.13, 0.15, 0.17),
                  fg2=(0.45, 0.48, 0.52), accent=(0.08, 0.55, 0.52)),
}

GREY_BODY = (0.62, 0.645, 0.685)
GREY_HOUSING = (0.55, 0.58, 0.64)
GREY_PIN = (0.74, 0.76, 0.80)
GREY_OBJ = (0.62, 0.67, 0.73)
HOUSING_LABELS = {"enclosure", "front_cover"}
SKIP_LABELS = {"finger_R", "finger_L"}


def make_lut(cmap_name, vmax):
    import vtk
    from matplotlib import colormaps
    cm = colormaps[cmap_name]
    lut = vtk.vtkLookupTable()
    lut.SetNumberOfTableValues(256)
    lut.SetRange(0.0, vmax)
    for i in range(256):
        r, g, b, _ = cm(i / 255.0)
        lut.SetTableValue(i, r, g, b, 1.0)
    lut.Build()
    return lut


def np_polydata(verts, tris, scalars=None):
    import vtk
    from vtk.util import numpy_support as ns
    pd = vtk.vtkPolyData()
    pts = vtk.vtkPoints()
    pts.SetData(ns.numpy_to_vtk(np.ascontiguousarray(verts, np.float64),
                                deep=True))
    pd.SetPoints(pts)
    n = len(tris)
    cells = np.hstack([np.full((n, 1), 3, np.int64),
                       np.ascontiguousarray(tris, np.int64)]).ravel()
    ca = vtk.vtkCellArray()
    ca.SetCells(n, ns.numpy_to_vtkIdTypeArray(cells, deep=True))
    pd.SetPolys(ca)
    if scalars is not None:
        arr = ns.numpy_to_vtk(np.ascontiguousarray(scalars, np.float32),
                              deep=True)
        arr.SetName("vM")
        pd.GetPointData().SetScalars(arr)
    return pd


class Scene:
    """One reusable offscreen render window; renderer rebuilt per frame."""

    def __init__(self, width, height, theme):
        import vtk
        self.vtk = vtk
        self.W, self.H = width, height
        self.theme = THEMES[theme]
        rw = vtk.vtkRenderWindow()
        rw.SetOffScreenRendering(1)
        rw.SetSize(width, height)
        # NOTE: depth peeling silently DROPS translucent actors on this GL
        # stack (llvmpipe) -- verified. Plain alpha blending + FXAA works.
        rw.SetMultiSamples(0)
        rw.SetAlphaBitPlanes(1)
        self.rw = rw

    def new_renderer(self):
        vtk = self.vtk
        if self.rw.GetRenderers().GetNumberOfItems():
            self.rw.GetRenderers().RemoveAllItems()
        ren = vtk.vtkRenderer()
        ren.SetBackground(*self.theme["bg"])
        ren.UseFXAAOn()
        self.rw.AddRenderer(ren)
        kit = vtk.vtkLightKit()
        kit.SetKeyLightIntensity(1.0)
        kit.SetKeyLightWarmth(0.55)
        kit.SetFillLightWarmth(0.45)
        kit.SetKeyToFillRatio(2.6)
        kit.SetKeyToHeadRatio(4.0)
        kit.AddLightsToRenderer(ren)
        return ren

    def add_mesh(self, ren, verts, tris, color=None, opacity=1.0,
                 scalars=None, lut=None, vmax=None, feature_angle=46.0):
        vtk = self.vtk
        pd = np_polydata(verts, tris, scalars)
        nrm = vtk.vtkPolyDataNormals()
        nrm.SetInputData(pd)
        nrm.SplittingOn()
        nrm.SetFeatureAngle(feature_angle)
        nrm.ConsistencyOff()
        nrm.AutoOrientNormalsOff()
        nrm.ComputePointNormalsOn()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(nrm.GetOutputPort())
        if scalars is not None:
            mapper.SetLookupTable(lut)
            mapper.SetScalarRange(0.0, vmax)
            mapper.SetColorModeToMapScalars()
            mapper.InterpolateScalarsBeforeMappingOn()
        else:
            mapper.ScalarVisibilityOff()
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        pr = actor.GetProperty()
        if color is not None:
            pr.SetColor(*color)
        pr.SetOpacity(opacity)
        pr.SetAmbient(0.16)
        pr.SetDiffuse(0.86)
        if scalars is not None:
            # broad sheen so near-zero-stress (black in inferno) regions still
            # read as 3D shape on the dark background
            pr.SetSpecular(0.42)
            pr.SetSpecularPower(18)
        else:
            pr.SetSpecular(0.22)
            pr.SetSpecularPower(28)
        pr.SetInterpolationToPhong()
        ren.AddActor(actor)
        return actor

    def add_cylinder(self, ren, center, radius, height, axis="z",
                     color=GREY_OBJ, opacity=0.32, resolution=120):
        """Translucent rigid object. axis 'z' (FEA frame) or 'y' (world)."""
        vtk = self.vtk
        src = vtk.vtkCylinderSource()          # native axis = Y
        src.SetRadius(radius)
        src.SetHeight(height)
        src.SetResolution(resolution)
        src.CappingOn()
        src.Update()
        tf = vtk.vtkTransform()
        tf.Translate(*center)
        if axis == "z":
            tf.RotateX(90.0)
        tpd = vtk.vtkTransformPolyDataFilter()
        tpd.SetTransform(tf)
        tpd.SetInputConnection(src.GetOutputPort())
        nrm = vtk.vtkPolyDataNormals()
        nrm.SetInputConnection(tpd.GetOutputPort())
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(nrm.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        pr = actor.GetProperty()
        pr.SetColor(*color)
        pr.SetOpacity(opacity)
        pr.SetSpecular(0.35)
        pr.SetSpecularPower(40)
        pr.SetInterpolationToPhong()
        ren.AddActor(actor)
        return actor

    def add_box(self, ren, center, half, axis="z", color=GREY_OBJ,
                opacity=0.32, length=60.0):
        vtk = self.vtk
        src = vtk.vtkCubeSource()
        if axis == "z":
            src.SetXLength(2 * half); src.SetYLength(2 * half)
            src.SetZLength(length)
        else:
            src.SetXLength(2 * half); src.SetZLength(2 * half)
            src.SetYLength(length)
        src.SetCenter(*center)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(src.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        pr = actor.GetProperty()
        pr.SetColor(*color)
        pr.SetOpacity(opacity)
        ren.AddActor(actor)
        return actor

    def add_scalar_bar(self, ren, lut, title="von Mises (MPa)"):
        vtk = self.vtk
        sb = vtk.vtkScalarBarActor()
        sb.SetLookupTable(lut)
        sb.SetTitle(title)
        sb.SetNumberOfLabels(6)
        sb.SetLabelFormat("%.2f")
        sb.UnconstrainedFontSizeOn()
        fg = self.theme["fg"]
        for tp, size in ((sb.GetTitleTextProperty(), int(self.H * 0.016)),
                         (sb.GetLabelTextProperty(), int(self.H * 0.014))):
            tp.SetColor(*fg)
            tp.SetFontFamilyToArial()
            tp.BoldOff()
            tp.ItalicOff()
            tp.ShadowOff()
            tp.SetFontSize(max(12, size))
        sb.GetTitleTextProperty().BoldOn()
        sb.SetPosition(0.875, 0.30)
        sb.SetWidth(0.045)
        sb.SetHeight(0.52)
        ren.AddActor2D(sb)
        return sb

    def set_camera(self, ren, bounds, direction, up, zoom=1.0, view_angle=28.0,
                   fixed=None):
        cam = ren.GetActiveCamera()
        cam.SetViewAngle(view_angle)
        if fixed is not None:
            cam.SetFocalPoint(*fixed["focal"])
            cam.SetPosition(*fixed["pos"])
            cam.SetViewUp(*fixed["up"])
            ren.ResetCameraClippingRange()
            return cam
        cx = [(bounds[0] + bounds[1]) / 2, (bounds[2] + bounds[3]) / 2,
              (bounds[4] + bounds[5]) / 2]
        d = np.asarray(direction, float)
        d /= np.linalg.norm(d)
        cam.SetFocalPoint(*cx)
        cam.SetPosition(*(np.array(cx) + d * 100.0))
        cam.SetViewUp(*up)
        ren.ResetCamera(bounds)
        cam.Zoom(zoom)
        ren.ResetCameraClippingRange()
        return cam

    def snap(self, path):
        import vtk
        self.rw.Render()
        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(self.rw)
        w2i.ReadFrontBufferOff()
        w2i.Update()
        wr = vtk.vtkPNGWriter()
        wr.SetFileName(str(path))
        wr.SetInputConnection(w2i.GetOutputPort())
        wr.Write()


# --------------------------------------------------------------------------- #
# Caption overlay (PIL) — styled after scripts/assembly_anim.py
# --------------------------------------------------------------------------- #
def _font_paths():
    try:
        import matplotlib
        d = Path(matplotlib.__file__).parent / "mpl-data/fonts/ttf"
        return str(d / "DejaVuSans.ttf"), str(d / "DejaVuSans-Bold.ttf")
    except Exception:
        return None, None


_FONT_R, _FONT_B = _font_paths()
_font_cache = {}


def _font(size, bold=False):
    key = (size, bold)
    if key not in _font_cache:
        from PIL import ImageFont
        path = _FONT_B if bold else _FONT_R
        try:
            _font_cache[key] = ImageFont.truetype(path, size)
        except Exception:
            _font_cache[key] = ImageFont.load_default()
    return _font_cache[key]


def _spaced(text):
    return " ".join(list(text))


def overlay_caption(png_path, caption, tag, theme, progress=None, header=None):
    from PIL import Image, ImageDraw
    th = THEMES[theme]
    to255 = lambda c: tuple(int(round(v * 255)) for v in c)
    fg, fg2, accent = to255(th["fg"]), to255(th["fg2"]), to255(th["accent"])
    bar_bg = (58, 62, 70) if theme == "dark" else (224, 227, 231)
    img = Image.open(png_path).convert("RGB")
    W, H = img.size
    d = ImageDraw.Draw(img, "RGBA")
    s = W / 1600.0
    d.text((int(44 * s), int(34 * s)),
           _spaced(header or "GRIPPER · FEA 3D"),
           font=_font(int(26 * s), True), fill=fg2)
    fx = int(44 * s)
    d.text((fx, int(H - 150 * s)), _spaced(tag),
           font=_font(int(28 * s), True), fill=accent)
    cap_size = int(40 * s)
    max_w = W - int(96 * s)
    while cap_size > 16:
        cf = _font(cap_size, True)
        if d.textlength(caption, font=cf) <= max_w:
            break
        cap_size -= 1
    d.text((fx, int(H - 108 * s)), caption, font=_font(cap_size, True), fill=fg)
    if progress is not None:
        bx0, bx1 = int(44 * s), int(W - 44 * s)
        by, h = int(H - 34 * s), max(3, int(7 * s))
        d.rounded_rectangle([bx0, by, bx1, by + h], radius=h // 2, fill=bar_bg)
        fillx = int(bx0 + (bx1 - bx0) * max(0.0, min(1.0, progress)))
        if fillx > bx0 + h:
            d.rounded_rectangle([bx0, by, fillx, by + h], radius=h // 2,
                                fill=accent)
    img.save(png_path)


# --------------------------------------------------------------------------- #
# Assembly pose mesh cache (tessellated gripper parts at GRIPPER_OPEN=o)
# --------------------------------------------------------------------------- #
def pose_cache_path(cache_dir, o, quality):
    scale = os.environ.get("GRIPPER_SCALE", "1.0")
    return Path(cache_dir) / f"pose_o{o:.4f}_q{quality:g}_s{scale}.npz"


def cmd_tess_worker(args):
    """Internal: build the gripper at one pose and dump tessellated meshes."""
    os.environ["GRIPPER_OPEN"] = f"{args.open:.6f}"
    import gripper  # env read at import
    asm = gripper.gen_step()         # world Z-up coords (children carry reorient)
    labels, packs = [], {}
    for i, ch in enumerate(asm.children):
        v, f = ch.tessellate(args.quality)
        labels.append(ch.label)
        packs[f"v{i}"] = np.array([(p.X, p.Y, p.Z) for p in v], np.float32)
        packs[f"f{i}"] = np.array(f, np.int32)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, labels=np.array(labels), n=len(labels), **packs)
    print(f"[tess-worker] open={args.open:.4f} -> {out} ({len(labels)} parts)")


def ensure_pose_caches(opens, cache_dir, quality, workers):
    """Build any missing pose caches in parallel subprocesses (~3-4 min each)."""
    todo = []
    for o in opens:
        p = pose_cache_path(cache_dir, o, quality)
        if not p.exists():
            todo.append((o, p))
    if not todo:
        return
    print(f"[tess] building {len(todo)} pose cache(s) with {workers} workers "
          f"(~3-4 min each; cached for reuse)")
    from concurrent.futures import ThreadPoolExecutor

    def run(item):
        o, p = item
        r = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "tess-worker",
             "--open", f"{o:.6f}", "--out", str(p),
             "--quality", str(quality)],
            capture_output=True, text=True, cwd=str(REPO))
        if r.returncode != 0 or not p.exists():
            raise RuntimeError(f"tess-worker open={o:.4f} failed:\n"
                               f"{r.stdout[-800:]}\n{r.stderr[-800:]}")
        return o

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for o in ex.map(run, todo):
            print(f"[tess] pose open={o:.4f} done")


def load_pose_cache(cache_dir, o, quality):
    d = np.load(pose_cache_path(cache_dir, o, quality), allow_pickle=True)
    parts = []
    labels = [str(x) for x in d["labels"]]
    for i, lbl in enumerate(labels):
        parts.append((lbl, d[f"v{i}"], d[f"f{i}"]))
    return parts


# --------------------------------------------------------------------------- #
# Scene assembly helpers
# --------------------------------------------------------------------------- #
def deformed_surface(sol, k):
    """(verts, tris, scalars) of the deformed boundary at step k (FEA frame)."""
    if "_btris" not in sol:
        sol["_btris"] = boundary_faces(sol["tets"], sol["rest"])
    return (np.asarray(sol["frames"][k], float), sol["_btris"],
            np.asarray(sol["vms"][k], np.float32))


def finger_scene(scene, sol, k, lut, with_object=True):
    """Renderer with the deformed finger + rigid object, FEA frame."""
    ren = scene.new_renderer()
    verts, tris, vms = deformed_surface(sol, k)
    scene.add_mesh(ren, verts, tris, scalars=vms, lut=lut, vmax=sol["vmax"])
    if with_object:
        cx = sol["xc0"] + sol["press"][k]
        zmid = 0.5 * (sol["rest"][:, 2].min() + sol["rest"][:, 2].max())
        zlen = (sol["rest"][:, 2].max() - sol["rest"][:, 2].min()) * 3.2
        if sol["shape"] == "circle":
            scene.add_cylinder(ren, (cx, sol["yc"], zmid), sol["R"] - 0.05,
                               zlen, axis="z")
        else:
            scene.add_box(ren, (cx, sol["yc"], zmid), sol["R"] - 0.05,
                          axis="z", length=zlen)
    scene.add_scalar_bar(ren, lut)
    b = np.concatenate([sol["rest"], sol["frames"][-1]], axis=0)
    pad = 6.0
    bounds = (b[:, 0].min() - pad - 4, b[:, 0].max() + pad,
              b[:, 1].min() - pad, b[:, 1].max() + pad,
              b[:, 2].min() - pad, b[:, 2].max() + pad)
    return ren, bounds


def assembly_scene(scene, sol, k, o, lut, parts, solid_housing=False):
    """Renderer with grey CAD parts + both FEA fingers + centreline object."""
    ren = scene.new_renderer()
    R, t = rigid_T(o)
    # CAD parts (skip the CAD fingers — replaced by the FEA surfaces)
    allv = []
    for lbl, v, f in parts:
        if lbl in SKIP_LABELS:
            continue
        if lbl in HOUSING_LABELS:
            scene.add_mesh(ren, v, f, color=GREY_HOUSING,
                           opacity=1.0 if solid_housing else 0.40)
        else:
            col = GREY_PIN if lbl.startswith(("pin_", "input_")) else GREY_BODY
            scene.add_mesh(ren, v, f, color=col)
        allv.append(v)
    # FEA fingers: pose right scene rigidly, mirror x for the left
    verts, tris, vms = deformed_surface(sol, k)
    posed = apply_T(verts.copy(), R, t)               # model frame, right
    wr = model_to_world(posed)
    wl = wr.copy()
    wl[:, 0] = -wl[:, 0]
    tris_l = tris[:, ::-1]                            # mirror flips winding
    scene.add_mesh(ren, wr, tris, scalars=vms, lut=lut, vmax=sol["vmax"])
    scene.add_mesh(ren, wl, tris_l, scalars=vms, lut=lut, vmax=sol["vmax"])
    # rigid object transported with the right-finger scene -> ~centreline
    ctr = apply_T(np.array([[sol["xc0"] + sol["press"][k], sol["yc"], 18.0]]),
                  R, t)
    cw = model_to_world(ctr)[0]                       # axis model z -> world Y
    zlen = 64.0
    if sol["shape"] == "circle":
        scene.add_cylinder(ren, tuple(cw), sol["R"] - 0.05, zlen, axis="y")
    else:
        scene.add_box(ren, tuple(cw), sol["R"] - 0.05, axis="y", length=zlen)
    scene.add_scalar_bar(ren, lut)
    allv.append(wr)
    b = np.concatenate([v for v in allv], axis=0)
    pad = 5.0
    bounds = (b[:, 0].min() - pad, b[:, 0].max() + pad,
              b[:, 1].min() - pad, b[:, 1].max() + pad,
              b[:, 2].min() - pad, b[:, 2].max() + pad)
    return ren, bounds


VIEWS_FINGER = {  # FEA frame: finger along +Y, thickness Z, up = +Y
    "front": dict(dir=(0.06, 0.10, 1.0), up=(0, 1, 0), zoom=1.05),
    "threequarter": dict(dir=(0.85, 0.30, 1.0), up=(0, 1, 0), zoom=1.05),
    "side": dict(dir=(1.0, 0.12, 0.10), up=(0, 1, 0), zoom=1.0),
}
VIEWS_ASM = {  # world Z-up (fingers point +Z); front = -Y like assembly_anim
    "front": dict(dir=(0.04, -1.0, 0.16), up=(0, 0, 1), zoom=1.0),
    "threequarter": dict(dir=(0.95, -1.0, 0.72), up=(0, 0, 1), zoom=1.02),
    "side": dict(dir=(1.0, -0.18, 0.22), up=(0, 0, 1), zoom=1.0),
}


def stats_tag(sol, k, o=None):
    tag = (f"STEP {k + 1}/{sol['nsteps']} · press {sol['press'][k]:.1f} mm · "
           f"grip {sol['grip'][k]:.1f} N · vM max {sol['vms'][k].max():.2f} MPa")
    if o is not None:
        tag += f" · pose OPEN={o:.2f}"
    return tag


def obj_desc(sol):
    return (f"R{sol['R']:g} cylinder" if sol["shape"] == "circle"
            else f"{2 * sol['R']:g} mm box")


def asm_caption(sol):
    return (f"Finger stress field from the canonical single-finger FEA "
            f"({obj_desc(sol)}, Bambu TPU 95A HF E=9.8 MPa), "
            f"mapped onto assembly pose")


# --------------------------------------------------------------------------- #
# ffmpeg encode (libx264 crf18 yuv420p + palette GIF), per assembly_anim.py
# --------------------------------------------------------------------------- #
def encode(frame_dir, pattern, fps, mp4, gif):
    pat = str(Path(frame_dir) / pattern)
    subprocess.run([
        FFMPEG, "-y", "-framerate", str(fps), "-i", pat,
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
        "-c:v", "libx264", "-crf", "18", "-preset", "slow",
        "-movflags", "+faststart", str(mp4),
    ], check=True, capture_output=True)
    pal = Path(frame_dir) / "_palette.png"
    gfps = min(fps, 16)
    subprocess.run([
        FFMPEG, "-y", "-framerate", str(fps), "-i", pat,
        "-vf", f"fps={gfps},scale=900:-1:flags=lanczos,"
               f"palettegen=stats_mode=diff", str(pal),
    ], check=True, capture_output=True)
    subprocess.run([
        FFMPEG, "-y", "-framerate", str(fps), "-i", pat, "-i", str(pal),
        "-lavfi", f"fps={gfps},scale=900:-1:flags=lanczos[x];"
                  f"[x][1:v]paletteuse=dither=bayer:bayer_scale=3",
        "-loop", "0", str(gif),
    ], check=True, capture_output=True)
    print(f"[video] {mp4}\n[video] {gif}")


# --------------------------------------------------------------------------- #
# Subcommands
# --------------------------------------------------------------------------- #
def cmd_finger(args):
    sol = load_solution(args)
    k = step_index(args, sol)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    scene = Scene(args.width, args.height, args.bg)
    lut = make_lut(args.cmap, sol["vmax"])
    views = [v.strip() for v in args.views.split(",") if v.strip()]
    for view in views:
        vw = VIEWS_FINGER[view]
        ren, bounds = finger_scene(scene, sol, k, lut)
        scene.set_camera(ren, bounds, vw["dir"], vw["up"], zoom=vw["zoom"])
        png = outdir / f"{sol['name']}_finger_{view}_step{k:02d}.png"
        scene.snap(png)
        if not args.no_captions:
            overlay_caption(
                png, f"Deformed Fin Ray finger vs rigid {obj_desc(sol)} — "
                     f"3D corotational contact FEA", stats_tag(sol, k),
                args.bg, header="GRIPPER · FEA 3D · FINGER")
        print(f"[finger] {png}")


def cmd_finger_anim(args):
    sol = load_solution(args)
    kgrasp = step_index(args, sol)
    outdir = Path(args.outdir)
    fdir = outdir / f"_frames_finger_{sol['name']}"
    fdir.mkdir(parents=True, exist_ok=True)
    for old in fdir.glob("f_*.png"):
        old.unlink()
    scene = Scene(args.width, args.height, args.bg)
    lut = make_lut(args.cmap, sol["vmax"])
    vw = VIEWS_FINGER[args.view]
    # lock the camera on the grasp-frame scene
    ren, bounds = finger_scene(scene, sol, kgrasp, lut)
    cam = scene.set_camera(ren, bounds, vw["dir"], vw["up"], zoom=vw["zoom"])
    fixed = dict(focal=cam.GetFocalPoint(), pos=cam.GetPosition(),
                 up=cam.GetViewUp())
    center = np.array(fixed["focal"])
    rad = np.linalg.norm(np.array(fixed["pos"]) - center)
    n_total = sol["nsteps"] + args.hold + args.orbit_frames
    fi = 0
    # 1) closing sweep
    for k in list(range(sol["nsteps"])) + [kgrasp] * args.hold:
        ren, bounds = finger_scene(scene, sol, k, lut)
        scene.set_camera(ren, bounds, vw["dir"], vw["up"], fixed=fixed)
        png = fdir / f"f_{fi:04d}.png"
        scene.snap(png)
        if not args.no_captions:
            overlay_caption(png, "Closing — 3D FEA load steps",
                            stats_tag(sol, k), args.bg,
                            progress=fi / max(1, n_total - 1),
                            header="GRIPPER · FEA 3D · FINGER")
        fi += 1
    # 2) turntable orbit at the grasp frame (around the finger's +Y axis)
    elev = math.radians(16.0)
    a0 = math.atan2(fixed["pos"][0] - center[0], fixed["pos"][2] - center[2])
    for j in range(args.orbit_frames):
        a = a0 + 2.0 * math.pi * j / args.orbit_frames
        pos = center + rad * np.array([math.sin(a) * math.cos(elev),
                                       math.sin(elev),
                                       math.cos(a) * math.cos(elev)])
        fx = dict(focal=fixed["focal"], pos=tuple(pos), up=(0, 1, 0))
        ren, bounds = finger_scene(scene, sol, kgrasp, lut)
        scene.set_camera(ren, bounds, vw["dir"], vw["up"], fixed=fx)
        png = fdir / f"f_{fi:04d}.png"
        scene.snap(png)
        if not args.no_captions:
            overlay_caption(png, "Grasp frame — turntable",
                            stats_tag(sol, kgrasp), args.bg,
                            progress=fi / max(1, n_total - 1),
                            header="GRIPPER · FEA 3D · FINGER")
        fi += 1
    encode(fdir, "f_%04d.png", args.fps,
           outdir / f"{sol['name']}_finger_anim.mp4",
           outdir / f"{sol['name']}_finger_anim.gif")


def cmd_assembly(args):
    sol = load_solution(args)
    k = step_index(args, sol)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    cache_dir = outdir / "_pose_cache"
    o = solve_open_for_step(sol, k)
    ensure_pose_caches([o], cache_dir, args.quality, args.tess_workers)
    parts = load_pose_cache(cache_dir, o, args.quality)
    scene = Scene(args.width, args.height, args.bg)
    lut = make_lut(args.cmap, sol["vmax"])
    views = [v.strip() for v in args.views.split(",") if v.strip()]
    for view in views:
        vw = VIEWS_ASM[view]
        ren, bounds = assembly_scene(scene, sol, k, o, lut, parts,
                                     solid_housing=args.solid_housing)
        scene.set_camera(ren, bounds, vw["dir"], vw["up"], zoom=vw["zoom"])
        png = outdir / f"{sol['name']}_assembly_{view}_step{k:02d}.png"
        scene.snap(png)
        if not args.no_captions:
            overlay_caption(png, asm_caption(sol), stats_tag(sol, k, o),
                            args.bg, header="GRIPPER · FEA 3D · ASSEMBLY")
        print(f"[assembly] {png}")


def cmd_assembly_anim(args):
    sol = load_solution(args)
    outdir = Path(args.outdir)
    fdir = outdir / f"_frames_assembly_{sol['name']}"
    fdir.mkdir(parents=True, exist_ok=True)
    for old in fdir.glob("f_*.png"):
        old.unlink()
    cache_dir = outdir / "_pose_cache"
    # subsample FEA steps to at most --max-poses (each pose = ~3-4 min CAD build,
    # cached) and solve the matching GRIPPER_OPEN per step
    nk = min(args.max_poses, sol["nsteps"])
    ks = sorted(set(int(round(i)) for i in
                    np.linspace(0, sol["nsteps"] - 1, nk)))
    opens = {k: solve_open_for_step(sol, k) for k in ks}
    ensure_pose_caches(sorted(set(opens.values())), cache_dir, args.quality,
                       args.tess_workers)
    scene = Scene(args.width, args.height, args.bg)
    lut = make_lut(args.cmap, sol["vmax"])
    vw = VIEWS_ASM[args.view]
    # lock the camera on the union of the most-open and grasp scenes
    parts0 = load_pose_cache(cache_dir, opens[ks[0]], args.quality)
    _, b0 = assembly_scene(scene, sol, ks[0], opens[ks[0]], lut, parts0)
    partsN = load_pose_cache(cache_dir, opens[ks[-1]], args.quality)
    renN, bN = assembly_scene(scene, sol, ks[-1], opens[ks[-1]], lut, partsN)
    bounds = tuple(min(b0[i], bN[i]) if i % 2 == 0 else max(b0[i], bN[i])
                   for i in range(6))
    cam = scene.set_camera(renN, bounds, vw["dir"], vw["up"], zoom=vw["zoom"])
    fixed = dict(focal=cam.GetFocalPoint(), pos=cam.GetPosition(),
                 up=cam.GetViewUp())
    seq = ks + [ks[-1]] * args.hold
    n_total = len(seq)
    for fi, k in enumerate(seq):
        parts = load_pose_cache(cache_dir, opens[k], args.quality)
        ren, _ = assembly_scene(scene, sol, k, opens[k], lut, parts,
                                solid_housing=args.solid_housing)
        scene.set_camera(ren, bounds, vw["dir"], vw["up"], fixed=fixed)
        png = fdir / f"f_{fi:04d}.png"
        scene.snap(png)
        if not args.no_captions:
            overlay_caption(png, asm_caption(sol), stats_tag(sol, k, opens[k]),
                            args.bg, progress=fi / max(1, n_total - 1),
                            header="GRIPPER · FEA 3D · ASSEMBLY")
        print(f"[assembly-anim] frame {fi + 1}/{n_total} (step {k})")
    encode(fdir, "f_%04d.png", args.fps,
           outdir / f"{sol['name']}_assembly_anim.mp4",
           outdir / f"{sol['name']}_assembly_anim.gif")


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, anim=False, asm=False):
        p.add_argument("--iter", default="ms_R22",
                       help="fea/iterations/<name>/fea3d_solution.npz")
        p.add_argument("--npz", default="", help="explicit npz path (overrides --iter)")
        p.add_argument("--outdir", default=str(DEFAULT_OUT))
        p.add_argument("--width", type=int, default=1600)
        p.add_argument("--height", type=int, default=1200)
        p.add_argument("--cmap", default="inferno", help="inferno|turbo|...")
        p.add_argument("--bg", default="dark", choices=("dark", "white"))
        p.add_argument("--step", type=int, default=-1,
                       help="load step (negative = from end; default last = grasp)")
        p.add_argument("--no-captions", action="store_true")
        if anim:
            p.add_argument("--fps", type=int, default=10)
            p.add_argument("--hold", type=int, default=8,
                           help="extra hold frames at the grasp pose")
        if asm:
            p.add_argument("--quality", type=float, default=0.2,
                           help="CAD tessellation tolerance (mm)")
            p.add_argument("--tess-workers", type=int, default=6,
                           help="parallel gripper-pose tessellation subprocesses")
            p.add_argument("--solid-housing", action="store_true",
                           help="opaque enclosure/front cover (default translucent)")

    p = sub.add_parser("finger", help="deformed-finger stills (3 views)")
    common(p)
    p.add_argument("--views", default="front,threequarter,side")

    p = sub.add_parser("finger-anim", help="closing anim + turntable -> mp4/gif")
    common(p, anim=True)
    p.add_argument("--view", default="threequarter", choices=tuple(VIEWS_FINGER))
    p.add_argument("--orbit-frames", type=int, default=72)

    p = sub.add_parser("assembly", help="full-assembly composite stills")
    common(p, asm=True)
    p.add_argument("--views", default="front,threequarter,side")

    p = sub.add_parser("assembly-anim", help="closing sweep composite -> mp4/gif")
    common(p, anim=True, asm=True)
    p.add_argument("--view", default="threequarter", choices=tuple(VIEWS_ASM))
    p.add_argument("--max-poses", type=int, default=24,
                   help="max distinct gripper poses (FEA steps subsampled)")

    p = sub.add_parser("tess-worker")
    p.add_argument("--open", type=float, required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--quality", type=float, default=0.2)

    args = ap.parse_args()
    {"finger": cmd_finger, "finger-anim": cmd_finger_anim,
     "assembly": cmd_assembly, "assembly-anim": cmd_assembly_anim,
     "tess-worker": cmd_tess_worker}[args.cmd](args)


if __name__ == "__main__":
    main()

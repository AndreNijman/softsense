#!/usr/bin/env python3
"""assembly_video.py -- high-quality step-by-step assembly animation of the
gripper, INCLUDING the heat-stake caps being melted on.

Headless GPU (pyrender + EGL). Builds gripper.gen_step() ONCE, caches each part's
tessellated mesh + colour, then animates: parts fly into place in assembly order,
the pins slide in, the caps slide onto the studs, and finally the caps MUSHROOM +
glow as they are heat-staked (soldering iron). Fixed camera with a gentle orbit;
PIL stage captions. Writes renders/gripper_assembly.{mp4,gif}.

  python scripts/assembly_video.py            # full render
  python scripts/assembly_video.py --frame 150  # render one frame -> /tmp (tuning)
"""
import os, sys, math, argparse
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import numpy as np, trimesh, pyrender, imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont

POSE = 0.14          # slightly open so the mechanism reads
W, H = 1600, 1200
FPS = 30
BG = (0.93, 0.94, 0.96)
TESS = 0.3

# ------------------------------------------------------------------ build once
os.environ["GRIPPER_OPEN"] = str(POSE)
import gripper
print("[build] gen_step ...", flush=True)
asm = gripper.gen_step()
PARTS = []   # (label, trimesh_home, rgba)
for leaf in asm.children:
    lbl = getattr(leaf, "label", "") or ""
    try:
        V, Tr = leaf.tessellate(tolerance=TESS)
    except Exception:
        continue
    if not Tr:
        continue
    verts = np.array([(v.X, v.Y, v.Z) for v in V], float)
    faces = np.array(Tr, np.int64)
    c = getattr(leaf, "color", None)
    rgba = [0.6, 0.62, 0.66, 1.0]
    if c is not None:
        try:
            t = tuple(c)
            rgba = [t[0], t[1], t[2], t[3] if len(t) > 3 else 1.0]
        except Exception:
            pass
    PARTS.append([lbl, trimesh.Trimesh(verts, faces, process=False), rgba])
print(f"[build] {len(PARTS)} parts", flush=True)

mins = np.array([p[1].bounds[0] for p in PARTS]).min(0)
maxs = np.array([p[1].bounds[1] for p in PARTS]).max(0)
CENTER = (mins + maxs) / 2.0
RADIUS = float(np.linalg.norm(maxs - mins)) / 2.0

# ------------------------------------------------------------------ timeline
# Each entry: group test -> (phase index). Phases play in order; a part slides
# from home+offset to home over [t0,t1]. All pins are along the world pin axis
# (-Y); caps trail in from +Y (the stud side). Offsets are (unit_vec, distance).
def spec(lbl):
    if lbl == "enclosure":            return 0, (0, 0, 1), 30
    if lbl == "input_pinion_shaft":   return 0, (0, 0, -1), 60
    if lbl.startswith("drive_arm"):   return 1, (0, 0, 1), 46
    if lbl.startswith("follower"):    return 1, (0, 0, 1), 38
    if lbl.startswith("finger"):      return 2, (0, 0, 1), 80
    if lbl.startswith("pin_A") or lbl.startswith("pin_B"): return 3, (0, -1, 0), 46
    if lbl.startswith("pin_C") or lbl.startswith("pin_D"): return 3, (0, -1, 0), 46
    if lbl.startswith("cap_"):        return 4, (0, 1, 0), 60
    if lbl == "front_cover":          return 5, (0, 0, 1), 55
    return 1, (0, 0, 1), 40

# phase frame windows [appear, seat]
PHASE = {
    0: (6, 30),     # enclosure + shaft
    1: (28, 62),    # gears/arms + followers
    2: (60, 90),    # fingers
    3: (88, 122),   # all pins
    4: (120, 146),  # caps slide on
    5: (176, 198),  # cover
}
MELT = (146, 176)   # caps mushroom + glow
HOLD_END = 214
NFRAMES = HOLD_END

CAPTIONS = [  # (start_frame, text)
    (0,   "Flooded enclosure + input drive shaft"),
    (28,  "Crown/gear arms + coupler followers"),
    (60,  "Fin-Ray compliant fingers"),
    (88,  "Heat-stake journal pins slide in"),
    (120, "Retaining caps onto the pin studs"),
    (146, "Heat-stake: melt each cap with a soldering iron"),
    (176, "Snap-on front cover"),
    (198, "Assembled — all-printed, zero fasteners"),
]


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def caption_for(f):
    out = CAPTIONS[0][1]
    for sf, txt in CAPTIONS:
        if f >= sf:
            out = txt
    return out


# ------------------------------------------------------------------ pyrender scene (persistent)
scene = pyrender.Scene(bg_color=(*BG, 1.0), ambient_light=(0.34, 0.34, 0.37))
NODES = []   # (label, node, mesh, rgba, phase, off_vec, dist, center)
for lbl, tm, rgba in PARTS:
    ph, uv, dist = spec(lbl)
    mat = pyrender.MetallicRoughnessMaterial(
        baseColorFactor=list(rgba), metallicFactor=0.25, roughnessFactor=0.55,
        emissiveFactor=[0, 0, 0])
    pm = pyrender.Mesh.from_trimesh(tm, material=mat, smooth=False)
    node = pyrender.Node(mesh=pm, matrix=np.eye(4))
    scene.add_node(node)
    cen = (tm.bounds[0] + tm.bounds[1]) / 2.0
    NODES.append([lbl, node, pm, rgba, ph, np.array(uv, float), float(dist), cen])

# fixed camera
a0 = math.radians(18); e = math.radians(17)
dist_cam = RADIUS * 3.0
cam = pyrender.PerspectiveCamera(yfov=math.radians(34), aspectRatio=W / H)
cam_node = scene.add(cam, pose=np.eye(4))
# lights (added at fixed world directions)
def look_pose(eye, tgt, up=np.array([0, 1, 0.])):
    f = tgt - eye; f /= np.linalg.norm(f)
    s = np.cross(f, up); s /= (np.linalg.norm(s) + 1e-9)
    u = np.cross(s, f)
    M = np.eye(4); M[:3, 0] = s; M[:3, 1] = u; M[:3, 2] = -f; M[:3, 3] = eye
    return M
for off, inten in (((1, 1.5, 1.0), 4.0), ((-1.3, 0.7, 0.5), 1.9), ((0.2, -0.5, -1.2), 1.2)):
    d = np.array(off, float); le = CENTER + d / np.linalg.norm(d) * dist_cam
    scene.add(pyrender.DirectionalLight(color=[1, 1, 1], intensity=inten),
              pose=look_pose(le, CENTER))

renderer = pyrender.OffscreenRenderer(W, H)
HIDE = np.eye(4); HIDE[:3, 3] = [0, 0, 1e5]   # park off-screen when not yet appeared

# font
FONT = None
for fp in ("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
           "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
    if os.path.exists(fp):
        FONT = ImageFont.truetype(fp, 40); FONT_S = ImageFont.truetype(fp, 26); break
if FONT is None:
    try:
        import matplotlib
        mp = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data/fonts/ttf/DejaVuSans-Bold.ttf")
        FONT = ImageFont.truetype(mp, 40); FONT_S = ImageFont.truetype(mp, 26)
    except Exception:
        FONT = ImageFont.load_default(); FONT_S = FONT


def overlay(arr, f):
    im = Image.fromarray(arr).convert("RGB")
    d = ImageDraw.Draw(im)
    # title
    d.text((40, 28), "Underwater gripper — assembly", font=FONT_S, fill=(70, 74, 82))
    # caption bar
    txt = caption_for(f)
    melt = MELT[0] <= f < MELT[1]
    col = (200, 90, 20) if melt else (40, 44, 52)
    d.text((40, H - 70), txt, font=FONT, fill=col)
    # progress bar
    p = f / (NFRAMES - 1)
    d.rectangle([40, H - 14, W - 40, H - 8], fill=(210, 213, 218))
    d.rectangle([40, H - 14, 40 + int((W - 80) * p), H - 8], fill=(90, 120, 200))
    return np.array(im)


def frame(f):
    orbit = math.radians(18 + 34 * (f / (NFRAMES - 1)))   # gentle pan
    eye = CENTER + np.array([math.cos(e) * math.sin(orbit), math.sin(e),
                             math.cos(e) * math.cos(orbit)]) * dist_cam
    scene.set_pose(cam_node, look_pose(eye, CENTER))
    for lbl, node, pm, rgba, ph, uv, dist, cen in NODES:
        t0, t1 = PHASE[ph]
        if f < t0:
            scene.set_pose(node, HIDE); continue
        s = smooth((f - t0) / max(1, (t1 - t0)))
        offset = uv * dist * (1.0 - s)
        M = np.eye(4); M[:3, 3] = offset
        # x-ray the body during the melt phase so the glowing caps read through
        if lbl == "enclosure" or lbl.startswith("finger") or lbl == "front_cover":
            mat = pm.primitives[0].material
            a = 1.0
            if MELT[0] <= f < MELT[1]:
                mt = (f - MELT[0]) / (MELT[1] - MELT[0])
                a = 1.0 - 0.6 * math.sin(mt * math.pi)   # dip to ~0.4 mid-melt
            mat.baseColorFactor = [rgba[0], rgba[1], rgba[2], a]
            mat.alphaMode = "BLEND" if a < 0.99 else "OPAQUE"
        # melt morph for caps
        if lbl.startswith("cap_"):
            pm.primitives[0].material.emissiveFactor = [0, 0, 0]
            pm.primitives[0].material.baseColorFactor = list(rgba)
            if f >= MELT[0]:
                mt = smooth((f - MELT[0]) / (MELT[1] - MELT[0]))
                # flatten along pin axis (Y), spread in X/Z -> mushroomed rivet head
                sy = 1.0 - 0.55 * mt; sxz = 1.0 + 0.45 * mt
                S = np.diag([sxz, sy, sxz, 1.0])
                T1 = np.eye(4); T1[:3, 3] = cen
                T0 = np.eye(4); T0[:3, 3] = -cen
                M = M @ T1 @ S @ T0
                glow = math.sin(min(1.0, mt) * math.pi)   # up then down
                pm.primitives[0].material.emissiveFactor = [0.9 * glow, 0.35 * glow, 0.05 * glow]
        scene.set_pose(node, M)
    color, _ = renderer.render(scene)
    return overlay(color, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", default="")   # comma list for tuning, e.g. 100,160,200
    a = ap.parse_args()
    if a.frame:
        for fs in a.frame.split(","):
            fnum = int(fs)
            img = frame(fnum)
            p = f"/tmp/asm_f{fnum:03d}.png"; imageio.imwrite(p, img)
            print("wrote", p)
        return
    print(f"[render] {NFRAMES} frames @ {W}x{H}", flush=True)
    import tempfile, subprocess, shutil
    fdir = tempfile.mkdtemp(prefix="asmvid_")
    for f in range(NFRAMES):
        imageio.imwrite(os.path.join(fdir, f"f_{f:04d}.png"), frame(f))
        if f % 20 == 0:
            print(f"  frame {f}/{NFRAMES}", flush=True)
    renderer.delete()
    out = os.path.join(os.path.dirname(HERE), "renders")
    mp4 = os.path.join(out, "gripper_assembly.mp4")
    gif = os.path.join(out, "gripper_assembly.gif")
    # encode with the system ffmpeg (binary present; robust, high quality)
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{fdir}/f_%04d.png",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", mp4],
                   check=True, capture_output=True)
    print("  wrote", mp4, flush=True)
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{fdir}/f_%04d.png",
                    "-vf", "fps=16,scale=820:-1:flags=lanczos,split[a][b];"
                           "[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                    "-loop", "0", gif], check=True, capture_output=True)
    print("  wrote", gif, flush=True)
    shutil.rmtree(fdir, ignore_errors=True)
    print("ASSEMBLY_VIDEO_DONE", flush=True)


if __name__ == "__main__":
    main()

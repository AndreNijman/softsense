#!/usr/bin/env python3
"""Step-by-step exploded-assembly + x-ray animation of the gripper.

Pipeline (three sub-commands so render iteration is cheap):

    assembly_anim.py gen     # build per-frame STEPs + frames.json manifest
    assembly_anim.py render  # snapshot every frame -> PNG (reads manifest)
    assembly_anim.py video   # ffmpeg PNG sequence -> looping GIF + MP4
    assembly_anim.py all     # gen + render + video

Storyboard
----------
1. Mechanism assembles in free space (always solid, always visible):
   pinion -> drive arms -> axle pins -> followers -> fingers -> pivot pins.
2. Housing comes last: enclosure wraps around, front cover snaps on.
3. X-ray finale: the assembled gripper goes glassy (global transparency)
   and actuates (real GRIPPER_OPEN kinematics), then a wireframe spin,
   settling back to a solid hero hold.

Why this shape: the snapshot renderer only supports GLOBAL transparency
(no per-occurrence opacity), so we never need a transparent shell over a
solid mechanism -- the housing is simply absent while the mechanism builds,
and the whole assembly is uniformly glassy only in the dedicated x-ray beat.

The base build pose is generated ONCE (gen_step caches geometry); per-frame
work is only cheap Location transforms. Actuation poses are generated via
subprocess `scripts/step` calls at swept GRIPPER_OPEN values.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAD = Path("/home/andre/.claude/skills/cad/scripts")
PY = sys.executable
sys.path.insert(0, str(REPO))  # so `import gripper` resolves regardless of cwd

# ---- base build pose: set BEFORE importing gripper (env read at import) -----
BASE_OPEN = 0.35
os.environ.setdefault("GRIPPER_OPEN", str(BASE_OPEN))

# --------------------------------------------------------------------------- #
# Storyboard data
# --------------------------------------------------------------------------- #
# Per-part insertion: unit-ish direction the part travels FROM (exploded start
# = home + dir*dist) and the travel distance in mm. Directions chosen along
# each part's real insertion axis (pins drop along Z, plates fan sideways,
# fingers rise, housing wraps from below / front).
EXPLODE = {
    "input_pinion_shaft": ((0.0, -1.0, -0.25), 60.0),
    "drive_arm_R":        (( 1.0, 0.0, 0.45), 52.0),
    "drive_arm_L":        ((-1.0, 0.0, 0.45), 52.0),
    "pin_A_R":            ((0.2, 0.0, 1.0), 48.0),
    "pin_A_L":            ((-0.2, 0.0, 1.0), 48.0),
    "pin_B_R":            ((0.35, 0.0, 1.0), 48.0),
    "pin_B_L":            ((-0.35, 0.0, 1.0), 48.0),
    "follower_R":         (( 1.0, 0.15, 0.3), 58.0),
    "follower_L":         ((-1.0, 0.15, 0.3), 58.0),
    "finger_R":           (( 0.55, 0.0, 1.0), 62.0),
    "finger_L":           ((-0.55, 0.0, 1.0), 62.0),
    "pin_C_R":            ((0.3, 0.0, 1.0), 52.0),
    "pin_C_L":            ((-0.3, 0.0, 1.0), 52.0),
    "pin_D_R":            ((0.5, 0.0, 1.0), 52.0),
    "pin_D_L":            ((-0.5, 0.0, 1.0), 52.0),
    "enclosure":          ((0.0, -0.35, -1.0), 58.0),
    "front_cover":        ((0.0, -1.0, 0.25), 66.0),
}

# Reveal stages: (caption, [labels animated in this stage]).
STAGES = [
    ("Input pinion + drive shaft",        ["input_pinion_shaft"]),
    ("Crown + spur drive arms",           ["drive_arm_L", "drive_arm_R"]),
    ("Internal axle pins",                ["pin_A_R", "pin_A_L", "pin_B_R", "pin_B_L"]),
    ("Coupler links (followers)",         ["follower_R", "follower_L"]),
    ("Fin-Ray compliant fingers",         ["finger_R", "finger_L"]),
    ("Finger-pivot snap pins",            ["pin_C_R", "pin_C_L", "pin_D_R", "pin_D_L"]),
    ("Flooded enclosure (housing)",       ["enclosure"]),
    ("Front cover snaps on",              ["front_cover"]),
]

CAPTION_FULL = "Geared four-bar Fin-Ray gripper"


def smootherstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0)


# --------------------------------------------------------------------------- #
# Caption overlay (PIL): step tag + part name + timeline progress bar
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
    return " ".join(list(text))  # light letter-spacing for labels


def overlay_caption(png_path, caption, tag, progress, W, H):
    from PIL import Image, ImageDraw

    img = Image.open(png_path).convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    accent = (20, 158, 150)
    dark = (34, 37, 42)
    gray = (140, 146, 155)
    s = W / 800.0

    d.text((int(30 * s), int(22 * s)), _spaced("GRIPPER · ASSEMBLY SEQUENCE"),
           font=_font(int(15 * s), True), fill=gray)

    fx = int(30 * s)
    d.text((fx, int(H - 100 * s)), _spaced(tag), font=_font(int(19 * s), True), fill=accent)
    # auto-fit the caption so long titles never clip the right edge
    cap_size = int(31 * s)
    max_w = W - int(58 * s)
    while cap_size > 14:
        cf = _font(cap_size, True)
        if d.textlength(caption, font=cf) <= max_w:
            break
        cap_size -= 1
    d.text((fx, int(H - 72 * s)), caption, font=_font(cap_size, True), fill=dark)

    bx0, bx1 = int(30 * s), int(W - 30 * s)
    by, h = int(H - 22 * s), max(3, int(5 * s))
    d.rounded_rectangle([bx0, by, bx1, by + h], radius=h // 2, fill=(224, 227, 231))
    fillx = int(bx0 + (bx1 - bx0) * max(0.0, min(1.0, progress)))
    if fillx > bx0 + h:
        d.rounded_rectangle([bx0, by, fillx, by + h], radius=h // 2, fill=accent)
    img.save(png_path)


# --------------------------------------------------------------------------- #
# Geometry helpers
# --------------------------------------------------------------------------- #
def _norm(v):
    m = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / m for c in v)


def load_base():
    """Import gripper at BASE_OPEN, return {label: Solid} home parts + facts."""
    import gripper
    from build123d import Compound

    asm = gripper.gen_step()
    parts = {}
    for ch in asm.children:
        parts[ch.label] = ch
    centers = {}
    for lbl, s in parts.items():
        c = s.bounding_box().center()
        centers[lbl] = (c.X, c.Y, c.Z)
    return parts, centers, Compound


def moved_copy(solid, offset):
    """Translate a cached Solid by offset, preserving label + color."""
    from build123d import Location, Vector

    m = solid.moved(Location(Vector(*offset)))
    m.label = solid.label
    try:
        m.color = solid.color
    except Exception:
        pass
    return m


# --------------------------------------------------------------------------- #
# Camera (locked across every frame so framing never jumps)
# --------------------------------------------------------------------------- #
def iso_camera(view_center, radius, zoom, az_deg=None):
    """Explicit perspective iso camera looking at view_center.

    az_deg lets the finale spin the camera around Z while target/zoom hold.
    """
    if az_deg is None:
        # front-right-above 3/4 view (camera on -Y / +X / +Z side)
        d = _norm((0.95, -1.0, 0.72))
    else:
        a = math.radians(az_deg)
        # spin in XY, keep the same elevation as the base 3/4 view
        elev = 0.72
        horiz = math.sqrt(0.95 ** 2 + 1.0 ** 2)
        d = _norm((horiz * math.sin(a), -horiz * math.cos(a), elev))
    pos = [view_center[i] + d[i] * radius for i in range(3)]
    return {
        "position": [round(p, 3) for p in pos],
        "target": [round(c, 3) for c in view_center],
        "up": [0, 0, 1],
        "zoom": round(zoom, 4),
    }


# --------------------------------------------------------------------------- #
# gen: build per-frame STEPs + manifest
# --------------------------------------------------------------------------- #
def cmd_gen(args):
    from build123d import export_step

    work = REPO / args.outdir / "work"
    work.mkdir(parents=True, exist_ok=True)
    # Clear stale geometry/frames from prior runs; KEEP poses/ (expensive) and
    # _raw/ (content-addressed, self-invalidating).
    for old in (list(work.glob("geom_*.step")) + list(work.glob("frame_*.step"))
                + list(work.glob("frame_*.png"))):
        old.unlink()
    parts, centers, Compound = load_base()

    # Locked camera: fixed distance (low perspective distortion) + tunable zoom.
    # view_center sits a touch above the geometric center so the upward-pointing
    # fingers stay balanced in frame.
    view_center = (0.0, -6.0, 50.0)
    radius = 460.0
    zoom = args.zoom

    # frame-count scaling (prototype small via --fps-scale<1, full large).
    # Tuned for an unhurried, watchable pace at ~20 fps (~23 s full length).
    s = args.fps_scale
    STAGE_F = max(3, round(16 * s))    # per-stage slide-in (deliberate)
    HOLD_AFTER = max(3, round(24 * s))  # long caption dwell (reuses geom -> free)
    SETTLE = max(3, round(30 * s))
    XRAY_F = max(8, round(80 * s))     # slow open/close x-ray cycle
    HERO_F = max(3, round(30 * s))
    POSE_LEVELS = 11                   # fixed: distinct actuation poses (not scaled)

    frames = []  # each: dict(step, appearance, display, camera, caption)
    order_done = []  # labels already fully placed

    def home_children(extra=None):
        kids = [moved_copy(parts[l], (0, 0, 0)) for l in order_done]
        if extra:
            kids += extra
        return kids

    # Geometry STEPs are written once and referenced by (possibly many) frames;
    # hold/settle/hero frames reuse a prior STEP so render dedup makes them free.
    geom_count = [0]

    def new_geom(children):
        p = work / f"geom_{geom_count[0]:04d}.step"
        export_step(Compound(label="anim", children=children), str(p))
        geom_count[0] += 1
        return str(p.relative_to(REPO))

    def add(step_rel, caption, appearance, display, cam, tag):
        stem = f"frame_{len(frames):04d}"
        frames.append({"step": step_rel, "png": f"{stem}.png", "caption": caption,
                       "tag": tag, "appearance": appearance, "display": display,
                       "camera": cam})

    SOLID_APP = "workbench"
    GLASS_APP = {"materials": {"opacity": args.xray_opacity, "transparent": True}}
    cam_static = iso_camera(view_center, radius, zoom)

    # ---- build stages: slide each group in, then dwell on the caption ----
    last_geom = None
    for si, (caption, labels) in enumerate(STAGES, start=1):
        tag = f"STEP {si} / {len(STAGES)}"
        for f in range(STAGE_F):
            t = smootherstep((f + 1) / STAGE_F)
            extra = []
            for lbl in labels:
                d = _norm(EXPLODE[lbl][0])
                dist = EXPLODE[lbl][1]
                off = tuple(d[i] * dist * (1.0 - t) for i in range(3))
                extra.append(moved_copy(parts[lbl], off))
            last_geom = new_geom(home_children(extra))
            add(last_geom, caption, SOLID_APP, "solid", cam_static, tag)
        order_done.extend(labels)
        for _ in range(HOLD_AFTER):  # readable dwell (reuses last_geom -> free)
            add(last_geom, caption, SOLID_APP, "solid", cam_static, tag)

    # ---- settle hold: full solid assembly (reuses last_geom) ----
    for _ in range(SETTLE):
        add(last_geom, CAPTION_FULL, SOLID_APP, "solid", cam_static, "ASSEMBLED")

    # ---- x-ray actuation: glassy + real kinematics over a fixed pose set ----
    levels = [round(j / (POSE_LEVELS - 1), 3) for j in range(POSE_LEVELS)]
    pose_steps = gen_pose_steps(work, sorted(set(levels + [BASE_OPEN])), args)
    for k in range(XRAY_F):
        u = k / (XRAY_F - 1)
        o = 0.5 - 0.5 * math.cos(2 * math.pi * u)  # closed->open->closed loop
        key = min(pose_steps, key=lambda kk: abs(kk - o))
        add(str(pose_steps[key].relative_to(REPO)),
            "X-ray — mechanism actuating", GLASS_APP, "solid", cam_static, "X-RAY")

    # ---- final solid hero hold (reuses the assembled build geometry) ----
    for _ in range(HERO_F):
        add(last_geom, CAPTION_FULL, SOLID_APP, "solid", cam_static, "ASSEMBLED")

    manifest = {
        "width": args.width,
        "height": args.height,
        "fps": args.fps,
        "n_frames": len(frames),
        "frames": frames,
    }
    (work / "frames.json").write_text(json.dumps(manifest, indent=2))
    print(f"[gen] {len(frames)} frames, view radius={radius:.0f}, "
          f"manifest -> {work/'frames.json'}")


def gen_pose_steps(work, opens, args):
    """Generate full-assembly STEPs at the given GRIPPER_OPEN values (cached)."""
    out = {}
    posedir = work / "poses"
    posedir.mkdir(exist_ok=True)
    for o in opens:
        p = posedir / f"pose_{o:.3f}.step"
        if not p.exists():
            env = dict(os.environ, GRIPPER_OPEN=f"{o:.3f}")
            subprocess.run(
                [PY, str(CAD / "step"), str(REPO / "gripper.py"), "-o", str(p)],
                check=True, env=env, cwd=str(REPO),
                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
            )
        out[o] = p
    return out


# --------------------------------------------------------------------------- #
# render: snapshot every frame
# --------------------------------------------------------------------------- #
def cmd_render(args):
    work = REPO / args.outdir / "work"
    manifest = json.loads((work / "frames.json").read_text())
    W, H = manifest["width"], manifest["height"]
    frames = manifest["frames"]
    only = set()
    if args.only:
        for tok in args.only.split(","):
            if "-" in tok:
                a, b = tok.split("-")
                only |= set(range(int(a), int(b) + 1))
            else:
                only.add(int(tok))
    import hashlib
    import shutil
    from concurrent.futures import ThreadPoolExecutor

    sel = [i for i in range(len(frames)) if not only or i in only]

    # Dedup: many frames share the same view (holds/settle/hero). Render each
    # unique (step, appearance, display, camera) ONCE to an uncaptioned master,
    # then copy + caption per frame -- captions/progress differ but are cheap.
    # Masters are content-addressed (key + resolution) so caches never collide
    # across runs or resolutions.
    raw = work / "_raw"
    raw.mkdir(exist_ok=True)

    def view_key(fr):
        return json.dumps([fr["step"], fr["appearance"], fr["display"],
                           fr["camera"], W, H], sort_keys=True)

    keys = {}
    for i in sel:
        k = view_key(frames[i])
        keys.setdefault(k, i)  # representative frame for this unique view

    def render_master(item):
        k, i = item
        fr = frames[i]
        h = hashlib.md5(k.encode()).hexdigest()[:16]
        master = raw / f"m_{h}.png"
        if master.exists() and not args.force:
            return (k, master, True)
        job = {
            "input": str((REPO / fr["step"]).resolve()),
            "mode": "view",
            "outputs": [{"path": str(master), "width": W, "height": H,
                         "camera": fr["camera"]}],
            "appearance": fr["appearance"],
            "display": {"mode": fr["display"]},
            "render": {"sizeProfile": "presentation"},
        }
        r = subprocess.run([PY, str(CAD / "snapshot"), "--job", "-"],
                           input=json.dumps(job), text=True,
                           capture_output=True, cwd=str(REPO))
        saved = None
        for line in (r.stdout + r.stderr).splitlines():
            if "saved snapshot:" in line:
                saved = line.split("saved snapshot:")[1].strip()
        if saved and Path(saved).exists():
            Path(saved).replace(master)
            return (k, master, True)
        return (k, r.stderr[-400:], False)

    masters = {}
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for k, res, ok in ex.map(render_master, list(keys.items())):
            done += 1
            if ok:
                masters[k] = res
                print(f"[render] master {done}/{len(keys)} ok")
            else:
                print(f"[render] master {done}/{len(keys)} FAILED: {res}")
                if not args.keep_going:
                    sys.exit(1)

    # Compose every selected frame from its master + caption.
    for i in sel:
        fr = frames[i]
        k = view_key(fr)
        if k not in masters:
            continue
        out_png = work / fr["png"]
        shutil.copyfile(masters[k], out_png)
        if not args.no_captions:
            prog = i / max(1, len(frames) - 1)
            try:
                overlay_caption(out_png, fr["caption"], fr.get("tag", ""), prog, W, H)
            except Exception as e:
                print(f"[render] caption overlay failed on {i}: {e}")
    print(f"[render] composed {len(sel)} frames from {len(masters)} unique views")


# --------------------------------------------------------------------------- #
# video: ffmpeg -> gif + mp4
# --------------------------------------------------------------------------- #
def cmd_video(args):
    work = REPO / args.outdir / "work"
    manifest = json.loads((work / "frames.json").read_text())
    fps = manifest["fps"]
    pat = str(work / "frame_%04d.png")
    outdir = REPO / args.outdir
    mp4 = outdir / "gripper_assembly.mp4"
    gif = outdir / "gripper_assembly.gif"
    # MP4 (high quality, yuv420p for broad playback)
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps), "-i", pat,
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
        "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-movflags", "+faststart",
        str(mp4),
    ], check=True)
    # GIF with palette
    pal = work / "palette.png"
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps), "-i", pat,
        "-vf", "fps=%d,scale=900:-1:flags=lanczos,palettegen=stats_mode=diff" % min(fps, 20),
        str(pal),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps), "-i", pat, "-i", str(pal),
        "-lavfi", "fps=%d,scale=900:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3"
        % min(fps, 20),
        "-loop", "0", str(gif),
    ], check=True)
    print(f"[video] {mp4}\n[video] {gif}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("gen", "render", "video", "all"):
        p = sub.add_parser(name)
        p.add_argument("--outdir", default="anim")
        p.add_argument("--width", type=int, default=1280)
        p.add_argument("--height", type=int, default=960)
        p.add_argument("--fps", type=int, default=20)
        p.add_argument("--fps-scale", type=float, default=1.0,
                       help="<1 shrinks frame counts for fast prototypes")
        p.add_argument("--zoom", type=float, default=2.1)
        p.add_argument("--xray-opacity", type=float, default=0.32)
        p.add_argument("--only", default="", help="render: frame subset e.g. 0,5,40-44")
        p.add_argument("--keep-going", action="store_true")
        p.add_argument("--no-captions", action="store_true")
        p.add_argument("--workers", type=int, default=3, help="parallel render workers")
        p.add_argument("--force", action="store_true", help="re-render cached masters")
    args = ap.parse_args()
    if args.cmd in ("gen", "all"):
        cmd_gen(args)
    if args.cmd in ("render", "all"):
        cmd_render(args)
    if args.cmd in ("video", "all"):
        cmd_video(args)


if __name__ == "__main__":
    main()

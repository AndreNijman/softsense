#!/usr/bin/env python3
"""Outward-splay animation for presentation use.

Just the GRIPPER (geared four-bar body + Fin-Ray fingers + pins + cover, i.e.
gripper.py's gen_step) opening from closed -> full outward splay. NO canister,
servo, shaft, penetrators, cable or other under-mount tubing/wiring (that lives
in motor/cad/system_assembly.py and is deliberately excluded here).

Three sub-commands so render iteration is cheap:

    splay_anim.py gen      # ensure pose STEPs exist on the open grid (cached)
    splay_anim.py render   # snapshot each UNIQUE pose once -> per-frame PNGs
    splay_anim.py video    # ffmpeg PNG sequence -> renders/gripper_splay.{mp4,gif}
    splay_anim.py all      # gen + render + video

Camera is LOCKED (explicit position/target/up/zoom) so the framing never jumps
as the fingers swing out -- it sits on the X=0 plane so the V-splay stays
left/right symmetric, tilted down-from-front for 3D depth. Tuned to contain both
the tall closed pose and the wide open splay with margin.

Motion is one-way: short closed hold -> eased open -> hold on the splay (ideal
for a slide that ends parked on the open pose). Pass --pingpong for a seamless
looping GIF (open then close).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAD = Path("/home/andre/.claude/skills/cad/scripts")
PY = sys.executable

# --- locked camera (see module docstring; tuned against the gripper-alone bbox:
#     X splay +/-60, fingers along +Y up to ~123, thin in Z, center ~ (0,44,10)) -
VIEW_CENTER = (0.1, 44.0, 9.5)
VIEW_RADIUS = 460.0
VIEW_DIR = (0.0, -0.45, -1.0)   # symmetric (no X), down-from-front for depth
VIEW_UP = [0, 1, 0]             # fingers point up on screen
VIEW_ZOOM = 2.75


def smootherstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (6.0 * t - 15.0) + 10.0)


def _norm(v):
    m = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / m for c in v)


def locked_camera(zoom: float):
    d = _norm(VIEW_DIR)
    pos = [VIEW_CENTER[i] - d[i] * VIEW_RADIUS for i in range(3)]
    return {"position": [round(p, 3) for p in pos],
            "target": list(VIEW_CENTER), "up": VIEW_UP, "zoom": round(zoom, 4)}


# --------------------------------------------------------------------------- #
# gen: build gripper.py pose STEPs on the open grid (cached, parallel)
# --------------------------------------------------------------------------- #
def grid_values(step: float):
    n = int(round(1.0 / step))
    return [round(i * step, 3) for i in range(n + 1)]


def pose_path(work: Path, o: float) -> Path:
    return work / "poses" / f"pose_{o:.3f}.step"


def cmd_gen(args):
    work = REPO / args.outdir / "work"
    (work / "poses").mkdir(parents=True, exist_ok=True)
    want = grid_values(args.grid)
    missing = [o for o in want if not pose_path(work, o).exists()]
    print(f"[gen] grid={args.grid} -> {len(want)} poses, {len(missing)} missing")

    def build(o):
        p = pose_path(work, o)
        env = dict(os.environ, GRIPPER_OPEN=f"{o:.3f}")
        r = subprocess.run([PY, str(CAD / "step"), str(REPO / "gripper.py"),
                            "-o", str(p)], env=env, cwd=str(REPO),
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return o, r.returncode, (r.stderr or b"").decode()[-300:]

    if missing:
        with ThreadPoolExecutor(max_workers=args.jobs) as ex:
            for o, rc, err in ex.map(build, missing):
                print(f"[gen]   pose {o:.3f}: {'ok' if rc == 0 else 'FAIL ' + err}")
    print("[gen] done")


# --------------------------------------------------------------------------- #
# timeline: one rendered open-value per output frame (pre-interpolation)
# --------------------------------------------------------------------------- #
def build_timeline(args):
    grid = grid_values(args.grid)

    def snap(o):
        return min(grid, key=lambda g: abs(g - o))

    fps = args.fps
    tl = []
    tl += [0.0] * max(1, round(args.hold_start * fps))
    nopen = max(2, round(args.open_secs * fps))
    for k in range(nopen):
        u = (k + 1) / nopen
        tl.append(snap(smootherstep(u)))      # eased closed -> open
    tl += [1.0] * max(1, round(args.hold_open * fps))
    if args.pingpong:
        nclose = max(2, round(args.open_secs * fps))
        for k in range(nclose):
            u = (k + 1) / nclose
            tl.append(snap(1.0 - smootherstep(u)))
        tl += [0.0] * max(1, round(args.hold_start * fps))
    return tl


# --------------------------------------------------------------------------- #
# render: snapshot each UNIQUE pose once, compose every frame
# --------------------------------------------------------------------------- #
def cmd_render(args):
    work = REPO / args.outdir / "work"
    raw = work / "_raw"
    raw.mkdir(parents=True, exist_ok=True)
    for old in work.glob("frame_*.png"):
        old.unlink()

    tl = build_timeline(args)
    (work / "timeline.json").write_text(json.dumps(
        {"fps": args.fps, "width": args.width, "height": args.height,
         "n_frames": len(tl), "opens": tl}))
    cam = locked_camera(args.zoom)
    uniq = sorted(set(tl))
    print(f"[render] {len(tl)} frames, {len(uniq)} unique poses @ {args.width}x{args.height}")

    def render_master(o):
        step = pose_path(work, o)
        if not step.exists():
            return o, None, f"missing {step.name}"
        key = json.dumps([str(step), cam, args.width, args.height], sort_keys=True)
        h = hashlib.md5(key.encode()).hexdigest()[:16]
        master = raw / f"m_{h}.png"
        if master.exists() and not args.force:
            return o, master, None
        job = {"input": str(step.resolve()), "mode": "view",
               "outputs": [{"path": str(master), "width": args.width,
                            "height": args.height, "camera": cam}],
               "appearance": args.appearance, "display": {"mode": args.display},
               "render": {"sizeProfile": "presentation"}}
        r = subprocess.run([PY, str(CAD / "snapshot"), "--job", "-"],
                           input=json.dumps(job), text=True,
                           capture_output=True, cwd=str(REPO))
        saved = None
        for line in (r.stdout + r.stderr).splitlines():
            if "saved snapshot:" in line:
                saved = line.split("saved snapshot:")[1].strip()
        if saved and Path(saved).exists():
            Path(saved).replace(master)
            return o, master, None
        return o, None, r.stderr[-300:]

    masters = {}
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, (o, m, err) in enumerate(ex.map(render_master, uniq), 1):
            if m:
                masters[o] = m
                print(f"[render] master {i}/{len(uniq)} pose {o:.3f} ok")
            else:
                print(f"[render] master {i}/{len(uniq)} pose {o:.3f} FAIL: {err}")
                sys.exit(1)

    for i, o in enumerate(tl):
        shutil.copyfile(masters[o], work / f"frame_{i:04d}.png")
    print(f"[render] composed {len(tl)} frames")


# --------------------------------------------------------------------------- #
# video: ffmpeg -> mp4 + gif (optional motion-interpolation smoothing)
# --------------------------------------------------------------------------- #
def cmd_video(args):
    work = REPO / args.outdir / "work"
    meta = json.loads((work / "timeline.json").read_text())
    fps = meta["fps"]
    pat = str(work / "frame_%04d.png")
    outdir = REPO / args.video_dir
    outdir.mkdir(parents=True, exist_ok=True)
    mp4 = outdir / "gripper_splay.mp4"
    gif = outdir / "gripper_splay.gif"

    smooth = ""
    if args.smooth_fps and args.smooth_fps > fps:
        # motion-compensated interpolation up to a higher fps for buttery motion
        smooth = ("minterpolate=fps=%d:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:"
                  "vsbmc=1," % args.smooth_fps)
    out_fps = args.smooth_fps if smooth else fps

    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps), "-i", pat,
        "-vf", smooth + "scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p",
        "-r", str(out_fps), "-c:v", "libx264", "-crf", "17", "-preset", "slow",
        "-movflags", "+faststart", str(mp4)], check=True)

    gif_fps = min(out_fps, 25)
    pal = work / "palette.png"
    gscale = "scale=%d:-1:flags=lanczos" % args.gif_width
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps), "-i", pat,
        "-vf", smooth + "fps=%d,%s,palettegen=stats_mode=diff" % (gif_fps, gscale),
        str(pal)], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(fps), "-i", pat, "-i", str(pal),
        "-lavfi", smooth + "fps=%d,%s[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3"
        % (gif_fps, gscale), "-loop", "0", str(gif)], check=True)
    print(f"[video] {mp4}\n[video] {gif}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("gen", "render", "video", "all"):
        p = sub.add_parser(name)
        p.add_argument("--outdir", default="anim", help="work dir (poses + frames)")
        p.add_argument("--video-dir", default="renders", help="final mp4/gif dir")
        p.add_argument("--grid", type=float, default=0.05,
                       help="pose spacing in GRIPPER_OPEN (0.05 -> 21 poses)")
        p.add_argument("--jobs", type=int, default=4, help="parallel pose builds (gen)")
        p.add_argument("--width", type=int, default=1280)
        p.add_argument("--height", type=int, default=960)
        p.add_argument("--zoom", type=float, default=VIEW_ZOOM)
        p.add_argument("--fps", type=int, default=30, help="base timeline fps")
        p.add_argument("--smooth-fps", type=int, default=60,
                       help="motion-interpolate up to this fps (0 disables)")
        p.add_argument("--hold-start", type=float, default=0.4, help="closed hold (s)")
        p.add_argument("--open-secs", type=float, default=2.6, help="open sweep (s)")
        p.add_argument("--hold-open", type=float, default=1.5, help="splay hold (s)")
        p.add_argument("--pingpong", action="store_true", help="open then close (loops)")
        p.add_argument("--appearance", default="workbench")
        p.add_argument("--display", default="solid")
        p.add_argument("--gif-width", type=int, default=900)
        p.add_argument("--workers", type=int, default=3, help="parallel render workers")
        p.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.cmd in ("gen", "all"):
        cmd_gen(args)
    if args.cmd in ("render", "all"):
        cmd_render(args)
    if args.cmd in ("video", "all"):
        cmd_video(args)


if __name__ == "__main__":
    main()

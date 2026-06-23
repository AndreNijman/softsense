#!/usr/bin/env python3
"""render_pinfix.py -- heat-stake pin renders, building each pose ONCE.

Builds gripper.gen_step() at closed + open a single time each, then renders all
stills + a pin-seating GIF from the cached meshes (translating only the pin_/cap_
parts per frame -- no rebuild). Outputs to renders/.
"""
import os, sys
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np, imageio.v2 as imageio
import render_iso as ri

OUT = os.path.join(os.path.dirname(HERE), "renders")
W, H = 1500, 1100


def shifted(meshes, dy):
    """Copy meshes, pulling pin_/cap_ parts out along -Y by dy (caps 1.7x)."""
    out = []
    for tm, rgba, lbl in meshes:
        if lbl.startswith("cap_") or lbl.startswith("pin_"):
            t = tm.copy()
            t.apply_translation([0.0, -dy * (1.7 if lbl.startswith("cap_") else 1.0), 0.0])
            out.append((t, rgba, lbl))
        else:
            out.append((tm, rgba, lbl))
    return out


print("[build] closed pose ...", flush=True)
m0 = ri.assembly_meshes(0.0, tol=0.35)
print(f"[build] closed: {len(m0)} parts", flush=True)
print("[build] open pose ...", flush=True)
m1 = ri.assembly_meshes(1.0, tol=0.35)
print(f"[build] open: {len(m1)} parts", flush=True)

# ---- stills ----
ri.render(m0, os.path.join(OUT, "gripper_pins_closed.png"), W, H, azim=35, elev=22, bg="studio")
ri.render(m1, os.path.join(OUT, "gripper_pins_open.png"),   W, H, azim=35, elev=22, bg="studio")
ri.render(shifted(m0, 17), os.path.join(OUT, "gripper_pins_exploded.png"), W, H, azim=28, elev=20, bg="studio")
# back-side view: the axle-pin caps riveted on the exterior back wall (+Y side)
ri.render(m0, os.path.join(OUT, "gripper_pins_back.png"), W, H, azim=215, elev=14, bg="studio")

# ---- pin-seating GIF: caps+pins fly in (explode -> 0), ping-pong ----
print("[gif] pin-seating frames ...", flush=True)
seq = list(np.linspace(20, 0, 16)) + [0.0] * 5
frames = []
for k, e in enumerate(seq):
    img = ri.render(shifted(m0, float(e)), None, 1100, 825, azim=30, elev=20, bg="studio")
    frames.append(img)
    print(f"  frame {k+1}/{len(seq)} explode={e:4.1f}", flush=True)
frames = frames + frames[-1:] + frames[::-1]   # seat, hold, un-seat
imageio.mimsave(os.path.join(OUT, "gripper_pins_assembly.gif"), frames, fps=10, loop=0)
print("  wrote renders/gripper_pins_assembly.gif", flush=True)

# ---- open/close motion GIF (mid pose included) ----
print("[gif] motion (open/close) ...", flush=True)
mm = ri.assembly_meshes(0.5, tol=0.4)
mfr = []
for label, mset in (("c", m0), ("m", mm), ("o", m1), ("m2", mm)):
    mfr.append(ri.render(mset, None, 1100, 825, azim=35, elev=22, bg="studio"))
imageio.mimsave(os.path.join(OUT, "gripper_motion_pins.gif"), mfr + mfr[:1], fps=3, loop=0)
print("  wrote renders/gripper_motion_pins.gif", flush=True)
print("PINFIX_RENDERS_DONE", flush=True)

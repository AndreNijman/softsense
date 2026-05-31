"""Render a wrap_stages.png for the self-similar scale-up study.

eval_finger.py only writes eval.json (no figure). This driver mirrors
eval_finger's EXACT scaling logic (eff = gripper.SCALE * _scale; press stroke,
mesh size, and object size/height all scale by eff) and then solves a single
representative object so iter_harness.plot_all() can draw the von-Mises wrap
stages. It is a RENDER-ONLY helper for SCALABILITY.md -- it changes no design and
re-uses the same solver path eval_finger uses.

Usage:
  GRIPPER_SCALE=1.5 python render_selfsim_wrap.py selfsim_1p5 [grip_N]
    grip_N optional (default 12) -- pass the force-proportional target to render
    the force-proportional case instead of the fixed-12 N case.
The representative object is the small circle R=12 (the discriminator the old
study used -- round objects expose floppiness most).
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))
import iter_harness as H

name = sys.argv[1]
grip_t = float(sys.argv[2]) if len(sys.argv) > 2 else 12.0
outdir = os.path.join(H.ITERDIR, name)
os.makedirs(outdir, exist_ok=True)

# mirror eval_finger.evaluate() scaling (screen mode, _scale=1.0)
H.REPORT_MODE = "grip"
H.TARGET_GRIP = grip_t
H.NSTEPS = 12
mmax, mmin = 2.4, 1.1
H.gripper.FINGER_SCALE = 1.0
eff = H.gripper.SCALE * 1.0
H.PRESS_MAX = 10.0 * eff
H.MESH_MAX, H.MESH_MIN = mmax * eff, mmin * eff
refR = H.gripper.solve_side_right(0.0)
base_y = max(refR["C"][1], refR["D"][1]) - H.gripper.FR_BASE_DROP
base_y_1x = base_y / H.gripper.SCALE
# representative object: small circle R12 @ y80 (1x-frame), scaled by eff
R0, yc0 = 12.0, 80.0
H.OBJ_SHAPE = "circle"
H.R_NECK = R0 * eff
H.YC = base_y + (yc0 - base_y_1x) * eff

t0 = time.time()
p2d, tris, lm = H.regen_section({}, outdir)
sol = H.run_fea(p2d, tris, lm, verbose=False)
m = H.metrics(sol)
H.plot_all(sol, m, outdir,
           f"{name}  SCALE={H.gripper.SCALE} eff={eff:.2f}  circle R{H.R_NECK:.0f} "
           f"grip~{grip_t:.0f}N target")
print(f"[{name}] wrap_stages.png written  eff={eff:.2f}  "
      f"grip={m['grip_at_press_N']:.1f}N press={m['press_mm']:.1f}mm "
      f"arc={m['contact_arc_deg']:.1f} margin={m['margin_x']:.1f}  in {time.time()-t0:.0f}s")

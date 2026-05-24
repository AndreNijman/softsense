"""Extract the Fin Ray finger 2D cross-section (plane-strain domain) from gripper.py.

The finger is a Z-constant 2.5-D extrusion, so the planar top face IS the exact
2D profile (outer triangle + spine + ribs/cells as holes + the two mount bores).
Export that face to STEP for gmsh, and dump the key geometric landmarks the FEA
needs (mount points C/D, base/tip Y, contact-face X band) to JSON.
"""
import os, json
os.environ["GRIPPER_OPEN"] = "0"
os.environ["GRIPPER_FINGER_SCALE"] = "1.0"

import gripper
from build123d import Axis, export_step

OUT = os.path.dirname(__file__)

refR = gripper.solve_side_right(0.0)
C0, D0 = refR["C"], refR["D"]
inner_dir = -1
z0, th = gripper.Z_FINGER0, gripper.T_FINGER

fng = gripper.finray_finger_closed(C0, D0, inner_dir, z0, th)
bb = fng.bounding_box()
print(f"finger bbox: X[{bb.min.X:.2f},{bb.max.X:.2f}] "
      f"Y[{bb.min.Y:.2f},{bb.max.Y:.2f}] Z[{bb.min.Z:.2f},{bb.max.Z:.2f}]")
print(f"mount C0={C0}  D0={D0}  z0={z0} thickness={th}")

# Z-normal planar faces, by z-level + area
zfaces = fng.faces().filter_by(Axis.Z)
info = []
for f in zfaces:
    c = f.center()
    info.append((round(c.Z, 3), f.area, f))
info.sort(key=lambda r: (r[0], -r[1]))
print(f"\n{len(zfaces)} Z-normal planar faces (z, area):")
for z, a, _ in info:
    print(f"  z={z:7.3f}  area={a:8.2f}")

# top face = largest-area face at the max z level
zmax = max(r[0] for r in info)
top_candidates = [r for r in info if abs(r[0] - zmax) < 1e-3]
top = max(top_candidates, key=lambda r: r[1])[2]
inner = top.inner_wires() if hasattr(top, "inner_wires") else []
try:
    n_holes = len(top.inner_wires())
except Exception:
    n_holes = "?"
print(f"\ntop face: z={zmax:.3f} area={top.area:.2f} holes={n_holes}")

step_path = os.path.join(OUT, "finger_section.step")
export_step(top, step_path)
print(f"wrote {step_path}")

# landmarks for FEA boundary conditions
into = -inner_dir
contact_x = -inner_dir * gripper.FR_CONTACT_OFFSET
grip_tip_x = contact_x - into * gripper.FR_GRIP_DEPTH
base_y = max(C0[1], D0[1]) - gripper.FR_BASE_DROP
tip_y = base_y + gripper.FR_BLADE_LEN * gripper.FINGER_SCALE
landmarks = dict(
    C=list(C0), D=list(D0), z0=z0, thickness=th, inner_dir=inner_dir,
    contact_x=contact_x, grip_tip_x=grip_tip_x,
    base_y=base_y, tip_y=tip_y,
    mount_hole_r=gripper.MOUNT_HOLE_R,
    blade_len=gripper.FR_BLADE_LEN * gripper.FINGER_SCALE,
    bbox=dict(xmin=bb.min.X, xmax=bb.max.X, ymin=bb.min.Y, ymax=bb.max.Y),
)
with open(os.path.join(OUT, "finger_landmarks.json"), "w") as fh:
    json.dump(landmarks, fh, indent=2)
print("landmarks:", json.dumps(landmarks, indent=2))

"""Export old-ridge vs new-crosshatch finger_R (closed pose) to STEP for rendering.
The OLD finger is reproduced by reverting the grip-texture params on the imported
module before building (the rest of the geometry is identical)."""
import os, sys
sys.path.insert(0, "/home/andre/gripper-cad")
os.environ["GRIPPER_OPEN"] = "0"
import gripper as g
from build123d import export_step

PIC = "/home/andre/gripper-cad/grip/pictures"


def build_finger():
    refR = g.solve_side_right(0.0)
    R = g.solve_side_right(0.0)
    return g.finger(R, refR, -1, g.TPU, "finger_R").solid()


# NEW (crosshatch, current params)
new = build_finger()
export_step(new, os.path.join(PIC, "finger_new_crosshatch.step"))
print("new crosshatch finger vol=%.0f -> finger_new_crosshatch.step" % new.volume)

# OLD (single-axis ridges): revert the texture params and rebuild
g.FR_GRIP_CROSS = False
g.FR_GRIP_PITCH = 2.2
g.FR_GRIP_DEPTH = 0.6
g.FR_GRIP_FLAT = 0.4
g.FR_GRIP_TIP_FLAT = 0.2
old = build_finger()
export_step(old, os.path.join(PIC, "finger_old_ridge.step"))
print("old ridge finger vol=%.0f -> finger_old_ridge.step" % old.volume)

"""Finger-only build for the render pipeline (step skill -> STEP+GLB -> snapshot).
GRIP_OLD=1 reverts to the legacy single-axis ridge texture for the before/after."""
import os, sys
sys.path.insert(0, "/home/andre/Projects/softsense")
os.environ.setdefault("GRIPPER_OPEN", "0")
import gripper as g


def gen_step():
    if os.environ.get("GRIP_OLD"):
        g.FR_GRIP_CROSS = False
        g.FR_GRIP_PITCH = 2.2
        g.FR_GRIP_DEPTH = 0.6
        g.FR_GRIP_FLAT = 0.4
        g.FR_GRIP_TIP_FLAT = 0.2
    refR = g.solve_side_right(0.0)
    R = g.solve_side_right(0.0)
    return g.finger(R, refR, -1, g.TPU, "finger_R")

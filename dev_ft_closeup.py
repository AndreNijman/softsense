"""Close-up exporter: single right finger in the AUTHORED frame (no Z-up
rotation) so 'top' camera looks straight down the extrusion axis at the XY
truss (cell fillets, tooth tips, tip apex), and 'front' shows the z0/z1 edge
profile (base chamfer). Also crops to sub-regions by clipping with a box so
the auto-framer zooms in on the detail."""
from __future__ import annotations

import os

from build123d import Box, Compound, Location

import dev_fingertune as d

# CLOSEUP env: "tip" | "cells" | "base" | "" (whole finger)
REGION = os.environ.get("CLOSEUP", "")


def _clip(f, x0, x1, y0, y1):
    """Keep only the XY box [x0,x1]x[y0,y1] (authored frame), full Z."""
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    keep = Box(x1 - x0, y1 - y0, 100.0).moved(Location((cx, cy, d.Z_FINGER0 + 5.0)))
    return f & keep


def _finger():
    R = d.solve_closed_right()
    f = d.finray_finger_closed(R["C"], R["D"], -1, d.Z_FINGER0, d.T_FINGER)
    f.label = "finger_R"
    f.color = d.TPU
    return f, R


def gen_step():
    f, R = _finger()
    base_y = max(R["C"][1], R["D"][1]) - d.FR_BASE_DROP
    tip_y = base_y + d.FR_BLADE_LEN
    if REGION == "tip":
        f = _clip(f, -2, 8, tip_y - 14, tip_y + 2)
    elif REGION == "cells":
        f = _clip(f, -2, 18, base_y + 25, base_y + 55)
    elif REGION == "base":
        f = _clip(f, -5, 25, base_y - 12, base_y + 14)
    f.label = "finger_R"
    f.color = d.TPU
    # authored frame, no Z-up rotation -> top camera = look down extrusion (Z)
    return Compound(label="finger", children=[f])

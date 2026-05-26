"""adapter_iso13628_d_handle.py — ISO 13628-8 / API 17H Class A D-handle
unibody pod adapter for Schilling / Kraft / ECA / Hydro-Lek work-class
manipulator arms.

Operating principle: the work-class arm's existing standard jaws clamp the
Ø19 mm bar of this printed handle as if it were any other subsea tool —
no bolt-on, no scale mismatch (we're 0.3 % of TITAN 4's lift rating; bolting
to a 170 N·m wrist would crush a polymer gripper). The bar absorbs the
clamp force; the unibody hangs below the bar.

Geometry:
- Bottom Ø100 × 14 mm pod base — matches pod_cap_shroud OD.
- Ø100 cylindrical riser (~12 mm) up to the flange.
- Ø70 × 6 mm ISO 13628-8 Class A flange disc (decorative — 4 × M6
  clearance holes on Ø56 PCD).
- Two buttresses lift the Ø19 bar 35 mm above the flange so the jaws can
  fully enclose the bar without contacting the flange face.
- Ø19 × 100 mm graspable bar, axis along adapter +Y, centred on adapter X=0.

Total height ~62 mm (bar centre at Z ≈ 55). PA12-GF, single solid.

Cross-refs: `motor/interfaces/schilling-kraft.md` §6 + §9 Option B.
"""
from __future__ import annotations

import math
import os
import sys

from build123d import (
    Box,
    Cylinder,
    Compound,
    Location,
)

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    from adapters._base import (  # type: ignore
        pod_base, POD_OD, C_PA12_GF, m_clearance_radius,
    )
else:
    from ._base import (
        pod_base, POD_OD, C_PA12_GF, m_clearance_radius,
    )

BAR_OD: float = 19.0
BAR_LEN: float = 100.0
FLANGE_OD: float = 70.0
FLANGE_T: float = 6.0
FLANGE_PCD: float = 56.0
FLANGE_M6: float = 6.0
FLANGE_M6_COUNT: int = 4

POD_T: float = 14.0
RISER_T: float = 12.0
BAR_CLEARANCE: float = 35.0
BUTTRESS_W: float = 14.0
BUTTRESS_T: float = 10.0

Z_FLANGE_BOT = POD_T + RISER_T
Z_FLANGE_TOP = Z_FLANGE_BOT + FLANGE_T
Z_BAR_CTR = Z_FLANGE_TOP + BAR_CLEARANCE + BAR_OD / 2


def gen_step() -> Compound:
    # Lower body — pod base + riser + flange — as a single boolean solid
    lower = pod_base(thickness=POD_T)
    lower += Cylinder(radius=POD_OD / 2, height=RISER_T).moved(
        Location((0, 0, POD_T + RISER_T / 2)))
    lower += Cylinder(radius=FLANGE_OD / 2, height=FLANGE_T).moved(
        Location((0, 0, (Z_FLANGE_BOT + Z_FLANGE_TOP) / 2)))
    # 4 × M6 clearance holes on the flange (decorative — held tool)
    m6_r = m_clearance_radius(6)
    for k in range(FLANGE_M6_COUNT):
        ang = math.radians(360.0 / FLANGE_M6_COUNT * k + 45)
        cx = (FLANGE_PCD / 2) * math.cos(ang)
        cy = (FLANGE_PCD / 2) * math.sin(ang)
        lower -= Cylinder(radius=m6_r, height=FLANGE_T + 1).moved(
            Location((cx, cy, (Z_FLANGE_BOT + Z_FLANGE_TOP) / 2)))
    # Upper body — buttresses + bar — as a separate solid (the buttresses
    # overlap the bar; pod base is far below so they're a disjoint chunk).
    butt_h = Z_BAR_CTR - Z_FLANGE_TOP
    upper = Box(BUTTRESS_T, BUTTRESS_W, butt_h).moved(
        Location((0, +(BAR_LEN / 2 - BUTTRESS_W / 2),
                  Z_FLANGE_TOP + butt_h / 2)))
    upper += Box(BUTTRESS_T, BUTTRESS_W, butt_h).moved(
        Location((0, -(BAR_LEN / 2 - BUTTRESS_W / 2),
                  Z_FLANGE_TOP + butt_h / 2)))
    upper += Cylinder(radius=BAR_OD / 2, height=BAR_LEN).moved(
        Location((0, 0, 0), (1, 0, 0), 90)).moved(
        Location((0, 0, Z_BAR_CTR)))
    lower.color = C_PA12_GF
    upper.color = C_PA12_GF
    return Compound(label="adapter_iso13628_d_handle",
                    children=[lower, upper])


if __name__ == "__main__":
    gen_step()

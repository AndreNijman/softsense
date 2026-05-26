"""adapter_br2_bottom_newton.py — BlueROV2 Newton-footprint unibody pod adapter.

Bridges the gripper-canister unibody (Ø100 dry-cap end) to the BlueROV2's
bottom HDPE panel via the Newton-gripper drilling template R1:
2 × M5 holes, 100 mm pitch, **16° canted axis** so the gripper jaws aim
into the BR2 front-camera frustum.

Geometry:
- Bottom Ø100 × 14 mm pod base — matches pod_cap_shroud OD.
- Vertical top plate carrying the 2 × M5 Newton pattern.
- Top plate 30 × 140 × 10 mm, centred on canister axis, rotated 16°
  about Z to bake the tilt into the geometry.
- 2 × Ø5.5 (M5 clearance) through-holes on 100 mm pitch along the plate.

Total height 24 mm (pod 14 + plate 10). PA12-GF.

Cross-refs: `motor/interfaces/fixed-rov-chassis.md` §3c.
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
        pod_base, C_PA12_GF, m_clearance_radius,
    )
else:
    from ._base import (
        pod_base, C_PA12_GF, m_clearance_radius,
    )

BR2_PITCH: float = 100.0
BR2_TILT_DEG: float = 16.0
PLATE_L: float = 140.0       # along Newton pitch direction
PLATE_W: float = 30.0        # across
PLATE_T: float = 10.0

POD_T: float = 14.0
TOTAL_H: float = POD_T + PLATE_T


def gen_step() -> Compound:
    body = pod_base(thickness=POD_T)
    # Top plate, centred at (0, 0, POD_T + PLATE_T/2), rotated +16° about Z
    plate = Box(PLATE_L, PLATE_W, PLATE_T).moved(
        Location((0, 0, POD_T + PLATE_T / 2),
                 (0, 0, 1), BR2_TILT_DEG))
    body += plate
    # 2 × M5 clearance holes along the canted axis at ±(PITCH/2)
    tilt = math.radians(BR2_TILT_DEG)
    m5_r = m_clearance_radius(5)
    for sign in (-1, +1):
        hx = sign * (BR2_PITCH / 2) * math.cos(tilt)
        hy = sign * (BR2_PITCH / 2) * math.sin(tilt)
        h = Cylinder(radius=m5_r, height=PLATE_T + 2).moved(
            Location((hx, hy, POD_T + PLATE_T / 2)))
        body -= h
    body.color = C_PA12_GF
    body.label = "adapter_br2_bottom_newton"
    return Compound(label="adapter_br2_bottom_newton", children=[body])


if __name__ == "__main__":
    gen_step()

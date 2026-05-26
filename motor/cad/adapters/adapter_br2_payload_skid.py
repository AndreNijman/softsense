"""adapter_br2_payload_skid.py — BlueROV2 Payload Skid unibody pod adapter.

Production "full kit" path for our 3"-canister gripper on a BlueROV2 Payload
Skid (BR-100233). The skid bottom panel uses the same Newton 2-hole
M5 / 100 mm pitch / 16° canted footprint as the BR2 bottom panel; this
adapter is geometrically identical to `adapter_br2_bottom_newton.py` except
for the docstring context.

See `motor/interfaces/fixed-rov-chassis.md` §3e for the skid datasheet
(475 × 338 × 197 mm, 1200 g, 12 × 200 g ballast slots = 2.4 kg compensation
budget).
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

SKID_PN: str = "BR-100233"
BR2_PITCH: float = 100.0
BR2_TILT_DEG: float = 16.0
PLATE_L: float = 140.0
PLATE_W: float = 30.0
PLATE_T: float = 10.0

POD_T: float = 14.0
TOTAL_H: float = POD_T + PLATE_T


def gen_step() -> Compound:
    body = pod_base(thickness=POD_T)
    plate = Box(PLATE_L, PLATE_W, PLATE_T).moved(
        Location((0, 0, POD_T + PLATE_T / 2),
                 (0, 0, 1), BR2_TILT_DEG))
    body += plate
    tilt = math.radians(BR2_TILT_DEG)
    m5_r = m_clearance_radius(5)
    for sign in (-1, +1):
        hx = sign * (BR2_PITCH / 2) * math.cos(tilt)
        hy = sign * (BR2_PITCH / 2) * math.sin(tilt)
        h = Cylinder(radius=m5_r, height=PLATE_T + 2).moved(
            Location((hx, hy, POD_T + PLATE_T / 2)))
        body -= h
    body.color = C_PA12_GF
    body.label = "adapter_br2_payload_skid"
    return Compound(label="adapter_br2_payload_skid", children=[body])


if __name__ == "__main__":
    gen_step()

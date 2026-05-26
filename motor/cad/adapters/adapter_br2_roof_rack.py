"""adapter_br2_roof_rack.py — BlueROV2 Roof Rack unibody pod adapter.

Vertical-cylinder adapter: the gripper-canister unibody hangs DOWN from
the BR2 Roof Rack (BR-200126). The adapter is a Ø100 PA12-GF cylinder
that visually continues the unibody up to a horizontal mounting plate at
the top, carrying the 2 × M5 Newton-pattern bolts into the rack.

Geometry:
- Bottom Ø100 × 14 mm pod base — matches pod_cap_shroud OD.
- Ø100 cylindrical extension (~16 mm) up to the plate.
- Horizontal top plate 50 × 140 × 10 mm carrying 2 × Ø5.5 Newton holes
  on 100 mm pitch. **10° default tilt** is a rack-side fitment choice (the
  rack itself has two top-mount bolt-hole pairs at 0° and 10° per BR docs);
  here the plate is flat in the adapter's local frame.

Total height 40 mm. PA12-GF.

Cross-refs: `motor/interfaces/fixed-rov-chassis.md` §3d.
"""
from __future__ import annotations

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

BR2_PITCH: float = 100.0
BR2_TILT_DEG: float = 10.0   # documented; rack-side fitment choice

POD_T: float = 14.0
RISER_T: float = 16.0        # Ø100 cylindrical riser between pod and plate
PLATE_L: float = 140.0
PLATE_W: float = 50.0
PLATE_T: float = 10.0
TOTAL_H: float = POD_T + RISER_T + PLATE_T


def gen_step() -> Compound:
    body = pod_base(thickness=POD_T)
    # Ø100 cylindrical riser (continues the unibody body)
    riser = Cylinder(radius=POD_OD / 2, height=RISER_T).moved(
        Location((0, 0, POD_T + RISER_T / 2)))
    body += riser
    # Top plate (length along X axis = ROV fore-aft equivalent)
    plate = Box(PLATE_L, PLATE_W, PLATE_T).moved(
        Location((0, 0, POD_T + RISER_T + PLATE_T / 2)))
    body += plate
    # 2 × M5 clearance holes on 100 mm pitch along X
    m5_r = m_clearance_radius(5)
    for sign in (-1, +1):
        h = Cylinder(radius=m5_r, height=PLATE_T + 2).moved(
            Location((sign * BR2_PITCH / 2, 0,
                      POD_T + RISER_T + PLATE_T / 2)))
        body -= h
    body.color = C_PA12_GF
    body.label = "adapter_br2_roof_rack"
    return Compound(label="adapter_br2_roof_rack", children=[body])


if __name__ == "__main__":
    gen_step()

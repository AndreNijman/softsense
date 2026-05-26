"""adapter_iso9409_80_6_M8.py — ISO 9409-1-80-6-M8 unibody-style pod adapter.

**DRY ONLY** — for dry-bench validation on UR20 and 10 kg+ payload cobots.

Geometry (ISO 9409-1 Table 1):
- Bottom Ø100 × 14 mm pod base.
- No taper (face d2 = Ø100 matches the pod OD).
- Top Ø100 × 6 mm disc.
- Spigot Ø50 H7, projects +5 mm (d3).
- 6 × M8 clearance through-holes on Ø80 BC (d1, d4).
- Ø8 H7 dowel hole on Ø80 BC at +X axis (d5).

Total height 25 mm. PA12-GF.

Cross-refs: `motor/interfaces/iso-9409-1.md` §5.
"""
from __future__ import annotations

import math
import os
import sys

from build123d import (
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

ISO_BC_D1: float = 80.0
ISO_FACE_D2: float = 100.0
ISO_SPIGOT_D3: float = 50.0
ISO_M8: float = 8.0
ISO_DOWEL_D5: float = 8.0
SPIGOT_PROJ: float = 5.0

POD_T: float = 14.0
DISC_T: float = 6.0
TOTAL_H: float = POD_T + DISC_T + SPIGOT_PROJ


def gen_step() -> Compound:
    body = pod_base(thickness=POD_T)
    disc = Cylinder(radius=ISO_FACE_D2 / 2, height=DISC_T).moved(
        Location((0, 0, POD_T + DISC_T / 2)))
    body += disc
    spigot = Cylinder(radius=ISO_SPIGOT_D3 / 2, height=SPIGOT_PROJ).moved(
        Location((0, 0, POD_T + DISC_T + SPIGOT_PROJ / 2)))
    body += spigot
    m8_r = m_clearance_radius(8)
    for k in range(6):
        ang = math.radians(30 + 60 * k)
        cx = (ISO_BC_D1 / 2) * math.cos(ang)
        cy = (ISO_BC_D1 / 2) * math.sin(ang)
        h = Cylinder(radius=m8_r,
                     height=DISC_T + SPIGOT_PROJ + 2).moved(
            Location((cx, cy, POD_T + (DISC_T + SPIGOT_PROJ) / 2)))
        body -= h
    dowel = Cylinder(radius=ISO_DOWEL_D5 / 2,
                     height=DISC_T + SPIGOT_PROJ + 2).moved(
        Location((ISO_BC_D1 / 2, 0,
                  POD_T + (DISC_T + SPIGOT_PROJ) / 2)))
    body -= dowel
    body.color = C_PA12_GF
    body.label = "adapter_iso9409_80_6_M8"
    return Compound(label="adapter_iso9409_80_6_M8", children=[body])


if __name__ == "__main__":
    gen_step()

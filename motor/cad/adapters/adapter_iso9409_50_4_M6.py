"""adapter_iso9409_50_4_M6.py — ISO 9409-1-50-4-M6 unibody-style pod adapter.

**DRY ONLY** — cobot wrists are not waterproof. For dry-bench validation
on UR3/5/10/16, Franka FR3, Doosan A-series, Fanuc CRX, ABB GoFa
(4-of-7 holes), KUKA LBR iiwa (4-of-7), and Kinova Gen3 (with Kinova's
own 4×M5 → 50-4-M6 conversion plate).

Geometry (ISO 9409-1 Table 1, 1996 edition; unchanged in 2004):
- Bottom Ø100 × 14 mm pod base.
- Tapered transition Ø100 → Ø63 over 8 mm.
- Top Ø63 × 6 mm disc (d2, h8).
- Spigot Ø31.5 H7, projects +5 mm (d3 — into cobot recess).
- 4 × M6 clearance through-holes on Ø50 BC (d1, d4).
- Ø6 H7 dowel hole on Ø50 BC at +X axis (d5, ISO 9787 +Xm).

Total height 33 mm. PA12-GF.

Cross-refs: `motor/interfaces/iso-9409-1.md` §4.
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
        pod_base, pod_taper, C_PA12_GF, m_clearance_radius,
    )
else:
    from ._base import (
        pod_base, pod_taper, C_PA12_GF, m_clearance_radius,
    )

ISO_BC_D1: float = 50.0
ISO_FACE_D2: float = 63.0
ISO_SPIGOT_D3: float = 31.5
ISO_M6: float = 6.0
ISO_DOWEL_D5: float = 6.0
SPIGOT_PROJ: float = 5.0

POD_T: float = 14.0
TAPER_T: float = 8.0
DISC_T: float = 6.0
TOTAL_H: float = POD_T + TAPER_T + DISC_T + SPIGOT_PROJ


def gen_step() -> Compound:
    body = pod_base(thickness=POD_T)
    body += pod_taper(z_start=POD_T,
                      z_end=POD_T + TAPER_T,
                      r_start=50.0,
                      r_end=ISO_FACE_D2 / 2)
    z_disc_bot = POD_T + TAPER_T
    z_disc_top = z_disc_bot + DISC_T
    disc = Cylinder(radius=ISO_FACE_D2 / 2, height=DISC_T).moved(
        Location((0, 0, (z_disc_bot + z_disc_top) / 2)))
    body += disc
    spigot = Cylinder(radius=ISO_SPIGOT_D3 / 2, height=SPIGOT_PROJ).moved(
        Location((0, 0, z_disc_top + SPIGOT_PROJ / 2)))
    body += spigot
    m6_r = m_clearance_radius(6)
    for k in range(4):
        ang = math.radians(45 + 90 * k)
        cx = (ISO_BC_D1 / 2) * math.cos(ang)
        cy = (ISO_BC_D1 / 2) * math.sin(ang)
        h = Cylinder(radius=m6_r,
                     height=DISC_T + SPIGOT_PROJ + 2).moved(
            Location((cx, cy,
                      (z_disc_bot + z_disc_top + SPIGOT_PROJ) / 2)))
        body -= h
    dowel = Cylinder(radius=ISO_DOWEL_D5 / 2,
                     height=DISC_T + SPIGOT_PROJ + 2).moved(
        Location((ISO_BC_D1 / 2, 0,
                  (z_disc_bot + z_disc_top + SPIGOT_PROJ) / 2)))
    body -= dowel
    body.color = C_PA12_GF
    body.label = "adapter_iso9409_50_4_M6"
    return Compound(label="adapter_iso9409_50_4_M6", children=[body])


if __name__ == "__main__":
    gen_step()

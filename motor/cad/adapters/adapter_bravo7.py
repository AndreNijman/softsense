"""adapter_bravo7.py — Reach Bravo 7 RB-1054 unibody-style pod adapter.

Visually continues the gripper-canister unibody (Ø100 PA12-GF) up to the
Reach Bravo 7 Payload Interface (RB-1054, Ø71 mm plate). Mates onto the
canister's BR dry end-cap via the shared `pod_base()` from `_base.py`.

Geometry:
- Bottom Ø100 × 14 mm pod base — matches the pod_cap_shroud OD.
- Tapered transition Ø100 → Ø71 over 8 mm.
- Top Ø71 × 6 mm disc — Bravo RB-1054 mating face per dossier §3c.
- 6 × M6 clearance holes (Ø6.6) on **Ø56 PCD** [ESTIMATE — see dossier
  §11 Q6; range 52–56 mm, upper end picked].
- 6 × M5 CSK holes on **Ø56 PCD** at the opposite phasing [ESTIMATE].
- 2 × Ø3 H7 dowel holes on **Ø48 PCD** [ESTIMATE].

Total height 28 mm. PA12-GF. Single solid, no moving parts. Bolts to BR
dry cap via 4 × M5 SHCS through the pod base on Ø78 PCD (see `pod_base`).

Cross-refs: `motor/interfaces/reach-bravo-alpha.md` §3,
`motor/INTERFACES.md` Q6.
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

BRAVO_PLATE_OD: float = 71.0
BRAVO_M6_PCD: float = 56.0
BRAVO_M5_CSK_PCD: float = 56.0
BRAVO_DOWEL_PCD: float = 48.0
BRAVO_DOWEL_PHASE_DEG: float = 30.0

POD_T: float = 14.0
TAPER_T: float = 8.0
DISC_T: float = 6.0
TOTAL_H: float = POD_T + TAPER_T + DISC_T


def gen_step() -> Compound:
    body = pod_base(thickness=POD_T)
    body += pod_taper(z_start=POD_T,
                      z_end=POD_T + TAPER_T,
                      r_start=50.0,
                      r_end=BRAVO_PLATE_OD / 2)
    disc = Cylinder(radius=BRAVO_PLATE_OD / 2, height=DISC_T).moved(
        Location((0, 0, POD_T + TAPER_T + DISC_T / 2)))
    body += disc
    m6_r = m_clearance_radius(6)
    z_disc_mid = POD_T + TAPER_T + DISC_T / 2
    for k in range(6):
        ang = math.radians(60 * k)
        cx = (BRAVO_M6_PCD / 2) * math.cos(ang)
        cy = (BRAVO_M6_PCD / 2) * math.sin(ang)
        h = Cylinder(radius=m6_r, height=DISC_T + 1).moved(
            Location((cx, cy, z_disc_mid)))
        body -= h
    m5_r = m_clearance_radius(5)
    for k in range(6):
        ang = math.radians(60 * k + 30)
        cx = (BRAVO_M5_CSK_PCD / 2) * math.cos(ang)
        cy = (BRAVO_M5_CSK_PCD / 2) * math.sin(ang)
        h = Cylinder(radius=m5_r, height=DISC_T + 1).moved(
            Location((cx, cy, z_disc_mid)))
        body -= h
    for k in (0, 1):
        ang = math.radians(BRAVO_DOWEL_PHASE_DEG + 180 * k)
        cx = (BRAVO_DOWEL_PCD / 2) * math.cos(ang)
        cy = (BRAVO_DOWEL_PCD / 2) * math.sin(ang)
        h = Cylinder(radius=1.5, height=DISC_T + 1).moved(
            Location((cx, cy, z_disc_mid)))
        body -= h
    body.color = C_PA12_GF
    body.label = "adapter_bravo7"
    return Compound(label="adapter_bravo7", children=[body])


if __name__ == "__main__":
    gen_step()

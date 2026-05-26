"""adapter_br2_roof_rack.py — BlueROV2 Roof Rack FRONT-mount adapter.

Forward-mount adapter for the BlueROV2 Roof Rack accessory (BR-200126),
bridging the gripper's 4× M4 bottom flange to the rack's pre-drilled
Newton-gripper hole pair (×2). In this configuration the gripper jaws
point along ROV +X (forward) — i.e. INTO the BR2 main-camera frustum —
so the adapter is an L-shaped bridge from a vertical gripper-rear face
to a horizontal rack underside.

Dossier reference: `motor/interfaces/fixed-rov-chassis.md` §3d and §9a;
shared gripper-side flange geometry lives in `_base.py` (do not redefine).

Rack-side hole pattern (top of the L)
=====================================
Per dossier §3d, the Roof Rack has *pre-drilled* Newton hole positions
(×2) at the **same 100 mm pitch** as the BR2 bottom-panel Newton mount.
The rack offers two top-mount fitment angles selected by **which** rack-
side bolt-hole pair you fasten to:

- **0° (flat)** — gripper canister stays level with the rack.
- **10° tilt** — gripper canes forward-down ~10° (the design default here).

The 10° tilt is the canonical front-mount Newton orientation because it
aims the gripper jaws into the lower portion of the main camera frame.
**The adapter geometry itself is identical for either choice** — only
the rack-side bolt pair the user picks changes. We document the 10°
default; if you need 0° pick the flat pair on the rack instead.

> **Q4 — unverified.** Per-feature Roof Rack hole coordinates are NOT
> published by BR in a form we could parse (dossier §11 Q4). The 100 mm
> pitch is reliable (it matches the Newton drilling template). The
> exact 0°/10° hole positions on the rack must be **measured against a
> physical Roof Rack before final printing**. Treat any pre-drilled
> position offset as an estimate.

Gripper-side hole pattern (bottom of the L)
===========================================
4× M4 clearance on the standard 76 × 16 mm gripper rectangle, plus a
Ø16 shaft clearance bore at (X = −12, Y = 0). All from `_base.py`.

Geometry
========
L-bracket in YZ cross-section:

    Y (= ROV +Z, up)
    ^
    |  +---------------------------+
    |  | TOP PLATE — rack-mating   |   <- normal +Y, 2× M5 on 100 mm pitch
    |  | (10° tilt = rack-side     |      pitch axis lies along adapter +Z
    |  |  fitment, not built in)   |      (= ROV fore-aft)
    |  +---+-----------------------+
    |      |
    |      | VERTICAL WEB —
    |      | gripper-mating slab
    |      | (4× M4 + Ø16 shaft)
    +------+-----------------------> Z (away from gripper = ROV −X = backward)
            \\
             gripper sits in Z < 0 (forward of adapter, ROV +X = jaws forward)

The vertical web carries the gripper bolt pattern at Z = 0. The top
horizontal plate extends back in +Z to reach the rack's Newton hole
pair, and sits at Y_top above the gripper so the gripper canister
hangs below the rack underside.

Forward-mount semantics
=======================
Jaws point along ROV +X. The gripper canister extends forward of the
adapter (adapter −Z = ROV +X). The rack is above (adapter +Y = ROV +Z).
The adapter cable cut-out is on the rear (+Z) end so the canister cable
can exit toward the BR2 main electronics bottle without crossing under
the rack.

Material: PA12-GF printed, ~10 mm walls. Drain holes per `§9a`.
"""
from __future__ import annotations

from build123d import (
    Axis,
    Box,
    Color,
    Compound,
    Cylinder,
    Location,
    Part,
    fillet,
)

import os
import sys

# Make `_base` importable both when run as a script (the STEP CLI
# loads this file via importlib.util.spec_from_file_location and adds
# the parent dir to sys.path) and when imported as a package member.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from _base import (  # noqa: E402
    C_PA12_GF,
    GRIPPER_FLANGE_FOOTPRINT_X,
    finalize,
    gripper_bolt_holes,
    m_clearance_radius,
    shaft_clearance_bore,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Rack-side bolt pattern (Newton footprint on the Roof Rack).
BR2_PITCH: float = 100.0          # mm, Newton 100 mm pitch [dossier §3c, §3d]
BR2_TILT_DEG: float = 10.0        # documented default; rack-side fitment choice
ROOF_M5_R: float = m_clearance_radius(5)   # Ø5.5 clearance for M5×16/×20

# Vertical web (gripper-mating slab).
ADAPTER_BASE_T: float = 10.0      # web thickness (Z direction)
WEB_X: float = 100.0              # ≥ GRIPPER_FLANGE_FOOTPRINT_X (96 mm) + skin
WEB_Y_LOW: float = -22.0          # extend below shaft/flange centroid
WEB_Y_HIGH: float = 130.0         # extend up to the top plate

# Top horizontal plate (rack-mating slab).
TOP_PLATE_T: float = 10.0         # plate thickness (Y direction)
TOP_PLATE_X: float = 50.0         # width (X) — wide enough around the M5 holes
TOP_PLATE_Z: float = 140.0        # length (Z, fore-aft) — ≥ pitch + edge margin
TOP_PLATE_Y_TOP: float = WEB_Y_HIGH         # top plate top face at Y = WEB_Y_HIGH
TOP_PLATE_Y_BOT: float = WEB_Y_HIGH - TOP_PLATE_T

# Place the 2× M5 pitch along adapter Z, centred in the top plate.
M5_Z1: float = (TOP_PLATE_Z - BR2_PITCH) / 2.0
M5_Z2: float = M5_Z1 + BR2_PITCH

# Drain holes (flooded gripper policy, dossier §9a).
DRAIN_R: float = 1.5              # Ø3
DRAIN_COUNT: int = 2

# Edge fillet (visual + stress relief on PA12-GF print).
EDGE_RADIUS: float = 3.0


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build() -> Part:
    """Construct the Roof-Rack forward-mount adapter as a single Part."""
    # Vertical web: the gripper-mating slab. Centred in X, spans Y ∈
    # [WEB_Y_LOW, WEB_Y_HIGH], lives in Z ∈ [0, ADAPTER_BASE_T].
    web_y_len = WEB_Y_HIGH - WEB_Y_LOW
    web_y_mid = (WEB_Y_HIGH + WEB_Y_LOW) / 2.0
    web = Box(WEB_X, web_y_len, ADAPTER_BASE_T).moved(
        Location((0.0, web_y_mid, ADAPTER_BASE_T / 2.0)))

    # Top plate: the rack-mating slab. Sits at the top of the web and
    # extends back in +Z to host the 2× M5 pair on 100 mm pitch.
    top_y_mid = (TOP_PLATE_Y_TOP + TOP_PLATE_Y_BOT) / 2.0
    top = Box(TOP_PLATE_X, TOP_PLATE_T, TOP_PLATE_Z).moved(
        Location((0.0, top_y_mid, TOP_PLATE_Z / 2.0)))

    body: Part = web + top

    # Gripper-side: 4× M4 clearance through the vertical web at Z = 0.
    for hole in gripper_bolt_holes(ADAPTER_BASE_T):
        body -= hole

    # Gripper-side: Ø16 shaft clearance bore at (X=-12, Y=0).
    body -= shaft_clearance_bore(ADAPTER_BASE_T)

    # Rack-side: 2× M5 clearance through the top plate (axis along Y).
    for z_pos in (M5_Z1, M5_Z2):
        hole = Cylinder(
            radius=ROOF_M5_R,
            height=TOP_PLATE_T + 1.0,
        ).moved(Location((0.0, top_y_mid, z_pos), (90.0, 0.0, 0.0)))
        body -= hole

    # Drain holes: small Ø3 through the vertical web's lower region so
    # the cavity behind the gripper doesn't trap water (flooded policy).
    drain_y = WEB_Y_LOW + 8.0
    for sign in (-1.0, 1.0):
        d = Cylinder(radius=DRAIN_R, height=ADAPTER_BASE_T + 1.0).moved(
            Location((sign * 28.0, drain_y, ADAPTER_BASE_T / 2.0)))
        body -= d

    # Fillet vertical (Z-axis) edges of the web for the printed-PA12-GF
    # aesthetic. Edges of the top plate are left sharp for a positive
    # contact with the rack underside.
    if EDGE_RADIUS > 0:
        try:
            body = fillet(
                body.edges().filter_by(Axis.Z).group_by(Axis.Z)[0],
                radius=EDGE_RADIUS,
            )
        except Exception:
            # Fillet is cosmetic; never let it block STEP export.
            pass

    body.color = C_PA12_GF
    body.label = "adapter_br2_roof_rack"
    return body


def gen_step() -> Compound:
    """STEP CLI entry — return a Compound wrapping the adapter Part."""
    return finalize(build(), label="adapter_br2_roof_rack", colour=C_PA12_GF)


if __name__ == "__main__":
    import os
    from build123d import export_step

    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.abspath(os.path.join(here, "..", "output"))
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "adapter_br2_roof_rack.step")
    export_step(gen_step(), out)
    print(f"wrote {out}")

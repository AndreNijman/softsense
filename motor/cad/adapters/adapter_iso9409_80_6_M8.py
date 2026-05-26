"""adapter_iso9409_80_6_M8.py — ISO 9409-1-80-6-M8 cobot tool-flange adapter.

> **DRY ONLY.** This adapter mates the gripper's bottom M4 flange to a
> cobot's ISO 9409-1-80-6-M8 wrist (e.g. UR20, 10+ kg payload arms). The
> gripper canister is sealed at the BR wet end cap, but the cobot wrist
> is not rated for the gripper's flooded operating envelope. Use for dry
> bench testing, demos, and lab integration ONLY. Per dossier §10.5,
> stamp "DRY USE ONLY" on the printed part.

Dossier: `motor/interfaces/iso-9409-1.md` — §5 "80-6-M8 detailed geometry"
and §10.2 "80-6-M8 variant — geometry table". This module is the build123d
realisation of the §10.2 spec.

Geometry summary (cobot side, +Z is +away from the gripper, into the arm):
- Ø100 face OD (h8)                            — dossier §5 d2 / §10.2
- Ø80 bolt circle, 6 × Ø9 (M8 clearance)       — dossier §5 d1, d4
- Ø50 H7 centering spigot, projects +5 mm      — dossier §5 d3, §10.2 spigot height
- Ø8 H7 dowel-pin hole on +Xm axis, 30° off
  the nearest bolt                              — dossier §5 d5 + ISO 9787 +Xm rule
- Adapter thickness 14 mm                       — dossier §10.2 (14 mm + M8×20 SHCS
  gives 6 mm thread into robot, 4 mm under UR20 ceiling)

Gripper side (Z = 0 face), inherited verbatim from `_base.py`:
- 4× M4 clearance holes on a 76 × 16 rectangle
- Ø16 shaft clearance bore at (X = -12, Y = 0)
- 96 × 28 mm rectangular footprint

Transition: lofted from the rectangular gripper footprint (Z = 0) up to
the Ø100 disc (Z = adapter_thickness), filling the M8 counter-bore region
above the bolt circle.

Local frame convention (matches `_base.py`):
- Origin at the gripper-side bolt-pattern centroid on the Z = 0 face.
- +Z = away from gripper, toward the cobot wrist.
- +X = gripper's jaw open/close axis; also = ISO 9787 +Xm (dowel direction).
- +Y = gripper depth axis.
"""
from __future__ import annotations

import math
import os
from typing import Iterable

from build123d import (
    Axis,
    Box,
    Circle,
    Color,
    Compound,
    Cylinder,
    Location,
    Part,
    Plane,
    Polyline,
    Rectangle,
    RegularPolygon,
    chamfer,
    export_step,
    fillet,
    loft,
    make_face,
)

# Import `_base` from the adapters package. The module may be loaded either
# as part of the `motor.cad.adapters` package (normal Python import) or as a
# standalone script by the `scripts/step` CLI, which puts the parent
# directory on `sys.path` but does NOT establish a package. Try the
# absolute-import path first (works when loaded standalone); fall back to
# the relative-import path (works when imported as a package member).
try:
    from _base import (  # type: ignore[import-not-found]
        C_PA12_GF,
        GRIPPER_FLANGE_FOOTPRINT_X,
        GRIPPER_FLANGE_FOOTPRINT_Y,
        finalize,
        gripper_bolt_holes,
        m_clearance_radius,
        shaft_clearance_bore,
    )
except ImportError:  # pragma: no cover — package-import fallback
    from ._base import (
        C_PA12_GF,
        GRIPPER_FLANGE_FOOTPRINT_X,
        GRIPPER_FLANGE_FOOTPRINT_Y,
        finalize,
        gripper_bolt_holes,
        m_clearance_radius,
        shaft_clearance_bore,
    )

# ---------------------------------------------------------------------------
# ISO 9409-1-80-6-M8 nominal dimensions
#
# All values from dossier `motor/interfaces/iso-9409-1.md` §5 (ISO 9409-1
# Table 1 row "Series 2, 80-6-M8" — geometry identical between the 1996
# and 2004 editions; see dossier sources [1], [2]).
# ---------------------------------------------------------------------------
ISO_BC_D1: float    = 80.0      # bolt-circle diameter (d1) — dossier §5
ISO_FACE_D2: float  = 100.0     # face OD (d2, h8) — dossier §5
ISO_SPIGOT_D3: float = 50.0     # centering spigot (d3, H7) — dossier §5
ISO_M8: float       = 8.0       # thread (d4 = M8) — dossier §5
ISO_DOWEL_D5: float = 8.0       # dowel-pin hole (d5, H7) — dossier §5
ISO_BOLTS_N: int    = 6         # threaded hole count — dossier §5
ISO_PIN_ANGLE_DEG: float = 30.0 # dowel between bolt 1 and 2 (60° spacing,
                                # so pin is halfway = 30° off the nearest
                                # bolt) — dossier §5 "Pin position"

# ---------------------------------------------------------------------------
# Adapter-specific dimensions — chosen per dossier §10.2 and §10.0
# ---------------------------------------------------------------------------
ADAPTER_T: float     = 14.0     # puck thickness (mm) — dossier §10.2 range
                                # 12–16; 14 = recommended primary so M8×20
                                # SHCS gives ~6 mm engagement into the robot
                                # (1×D minimum), 4 mm under UR20's 10 mm
                                # protrusion ceiling — dossier §10.0 table.
SPIGOT_H: float      = 5.0      # +Z projection of the Ø50 spigot —
                                # dossier §10.2 (4–5 mm; recess t1 ≥ 6 mm).
M8_COUNTERBORE_D: float = 13.0  # M8 SHCS head clearance Ø — dossier §10.2
M8_COUNTERBORE_T: float = 8.0   # M8 SHCS head depth — dossier §10.2
TOP_DISC_R: float    = ISO_FACE_D2 / 2.0     # Ø100 → R50
BOT_RECT_X: float    = GRIPPER_FLANGE_FOOTPRINT_X   # 96 mm
BOT_RECT_Y: float    = GRIPPER_FLANGE_FOOTPRINT_Y   # 28 mm
BOT_RECT_FILLET: float = 3.0    # printed-PA12-GF corner radius


def _iso_bolt_clearance_holes(adapter_thickness: float,
                              counterbore_depth: float) -> list[Cylinder]:
    """6× M8 clearance through-holes on Ø80 + Ø13 counter-bores from +Z.

    Bolts head-down from the cobot side. Counter-bore depth must be ≥ M8
    SHCS head height (8 mm) so the head sits below the cobot's mating
    face. Dossier §10.2.

    Pattern is 60°-spaced; bolt 1 is rotated +30° off +Xm so the dowel
    hole sits exactly on +Xm and the bolts straddle that axis (matching
    ISO 9787 + dossier §5 "Pin position: 30° off adjacent bolts").
    """
    holes: list[Cylinder] = []
    clearance_r = m_clearance_radius(ISO_M8)         # Ø9.0 close-fit
    bc_r = ISO_BC_D1 / 2.0
    h_through = adapter_thickness + 1.0              # +0.5 overshoot per side
    h_cb = counterbore_depth + 0.25                  # tiny overshoot

    for k in range(ISO_BOLTS_N):
        angle_deg = ISO_PIN_ANGLE_DEG + 360.0 * k / ISO_BOLTS_N  # 30, 90, 150, ...
        a = math.radians(angle_deg)
        cx, cy = bc_r * math.cos(a), bc_r * math.sin(a)
        through = Cylinder(radius=clearance_r, height=h_through).moved(
            Location((cx, cy, adapter_thickness / 2.0)))
        # Counter-bore from the +Z (cobot-side) face inward.
        cb = Cylinder(radius=M8_COUNTERBORE_D / 2.0, height=h_cb).moved(
            Location((cx, cy, adapter_thickness - counterbore_depth / 2.0
                      + 0.125)))
        holes.append(through)
        holes.append(cb)
    return holes


def _iso_dowel_hole(adapter_thickness: float) -> Cylinder:
    """Ø8 H7 dowel pin hole on +Xm axis, on the Ø80 bolt circle.

    Per ISO 9787 / dossier §5, the dowel hole is co-radial with the bolt
    circle (d1 = Ø80) and aligned with +Xm. We pierce the full puck so
    the hole prints reliably; in practice the cobot dowel projects only
    ~5 mm so depth-of-engagement is set by the robot, not the adapter.
    """
    bc_r = ISO_BC_D1 / 2.0
    h = adapter_thickness + 1.0
    return Cylinder(radius=ISO_DOWEL_D5 / 2.0, height=h).moved(
        Location((bc_r, 0.0, adapter_thickness / 2.0)))


def _spigot(adapter_thickness: float) -> Cylinder:
    """Ø50 h7 centering spigot projecting +SPIGOT_H above the Ø100 face.

    Dossier §10.2 / §10.0: tool-side spigot mates the cobot's Ø50 H7
    recess. The dossier notes that the printed PA12-GF spigot OD should
    be Ø50 h7 (-0.025/0) — we model the nominal Ø50 here; print
    compensation lives in the manufacturing notes, not the CAD.
    """
    return Cylinder(radius=ISO_SPIGOT_D3 / 2.0, height=SPIGOT_H).moved(
        Location((0.0, 0.0, adapter_thickness + SPIGOT_H / 2.0)))


def _lofted_body(adapter_thickness: float) -> Part:
    """Solid lofted body from the rectangular gripper footprint at Z = 0
    to the Ø100 disc at Z = adapter_thickness.

    Two-step build: (1) loft the transition between Z = 0 (rect) and
    Z = adapter_thickness/2 (intermediate rounded-square sketch) up to
    Z = adapter_thickness (circle). build123d's `loft()` takes a list of
    coplanar wires/sketches and produces a single solid.
    """
    z_top = adapter_thickness

    # Sketch 1: rectangular gripper footprint at Z = 0 (filleted corners).
    bottom = Plane.XY * Rectangle(BOT_RECT_X, BOT_RECT_Y)

    # Sketch 2: full Ø100 disc at Z = adapter_thickness.
    top = Plane.XY.offset(z_top) * Circle(radius=TOP_DISC_R)

    body = loft([bottom.face(), top.face()])
    return body


def build(adapter_thickness: float = ADAPTER_T) -> Compound:
    """Build the ISO 9409-1-80-6-M8 adapter Compound.

    Parameters
    ----------
    adapter_thickness :
        Puck thickness in mm. Default `ADAPTER_T = 14.0` per dossier
        §10.2 recommended primary pairing. Valid range 12–16 mm.

    Returns
    -------
    Compound coloured PA12-GF, label = "adapter_iso9409_80_6_M8".
    """
    body = _lofted_body(adapter_thickness)

    # Add the Ø50 centering spigot (projects +SPIGOT_H above the disc).
    body = body + _spigot(adapter_thickness)

    # Subtract cobot-side features.
    for hole in _iso_bolt_clearance_holes(adapter_thickness, M8_COUNTERBORE_T):
        body = body - hole
    body = body - _iso_dowel_hole(adapter_thickness)

    # Subtract gripper-side features (from `_base.py`).
    for hole in gripper_bolt_holes(adapter_thickness):
        body = body - hole
    body = body - shaft_clearance_bore(adapter_thickness)

    return finalize(body, label="adapter_iso9409_80_6_M8", colour=C_PA12_GF)


def gen_step() -> Compound:
    """STEP CLI entry point — returns the default-thickness adapter
    Compound for `scripts/step` to export."""
    return build()


if __name__ == "__main__":
    cwd = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    out_dir = os.path.join(cwd, "cad", "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "adapter_iso9409_80_6_M8.step")
    export_step(build(), out_path)
    print(f"wrote {out_path}")

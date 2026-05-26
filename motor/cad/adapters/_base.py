"""_base.py — the shared gripper-side mating geometry.

Every adapter under `motor/cad/adapters/` mates to the gripper's bottom M4
flange (see `gripper.py` BOT_FLANGE_*). Constants and helpers below are the
single source of truth for that interface; an adapter module imports from
here and never re-derives the flange geometry.

The flange (gripper-local frame, taken from `gripper.py`):
- 4× M4 clearance holes (Ø4.5) at (x, z) in [(-38, 2), (38, 2), (-38, 18),
  (38, 18)] on the Y = -25 face. Pattern is rectangular 76 × 16 mm,
  centroid at (X=0, Z=10).
- The drive shaft (D-coupler) exits through the SAME face at
  (X = -12, Z ≈ 10.52) — i.e. **12 mm offset in X from the bolt centroid**.
  Adapters must clear that bore (Ø ≥ 14 H7 to seat the lip seal; see
  `motor/ROV_INTEGRATION.md §2d`).

Adapter local frame convention:
- Origin at the bolt-pattern centroid on the gripper-side mating face.
- +Z = away from gripper, toward arm / chassis / D-handle.
- +X = gripper's jaw open/close axis (right +). Matches gripper-local X.
- +Y = depth (= gripper-local Z). Matches gripper-local Z so the shaft
  offset stays at X = -12 and Y ≈ +0.5.
- Mating face Z = 0; adapter body lives in Z > 0.

So an adapter is centred on its **bolt pattern**, not on the gripper shaft.
The shaft therefore enters the adapter off-centre at (X = -12, Y ≈ 0).
"""
from __future__ import annotations

import math
from typing import Iterable

from build123d import (
    Box,
    Circle,
    Color,
    Compound,
    Cylinder,
    Location,
    Part,
    Rectangle,
    fillet,
)

# ---------------------------------------------------------------------------
# Constants — the gripper-side mating face
# ---------------------------------------------------------------------------

# 4× M4 clearance hole positions in the adapter local frame (X, Y) on the
# Z = 0 mating face. Pattern centroid is the adapter origin.
GRIPPER_FLANGE_BOLT_XY: list[tuple[float, float]] = [
    (-38.0, -8.0),
    (+38.0, -8.0),
    (-38.0, +8.0),
    (+38.0, +8.0),
]
GRIPPER_FLANGE_BOLT_R: float = 2.25         # M4 clearance hole radius (Ø4.5)
GRIPPER_FLANGE_BOLT_M: float = 4.0          # nominal thread (informational)
GRIPPER_FLANGE_FOOTPRINT_X: float = 96.0    # enclosure width ENC_X span = 96 mm
GRIPPER_FLANGE_FOOTPRINT_Y: float = 28.0    # BOT_FLANGE_Z span = 28 mm

# Drive shaft pass-through. The shaft + lip-seal stack from
# `motor/ROV_INTEGRATION.md §2d` is Ø14 H7 (the seal seat); use Ø16 clearance
# in the adapter so the cap's seal boss seats without the adapter constraining
# its diameter.
GRIPPER_SHAFT_OFFSET_X: float = -12.0       # X position of shaft axis
GRIPPER_SHAFT_OFFSET_Y: float = 0.0         # ~0.5 in gripper-local, simplified to 0
GRIPPER_SHAFT_CLEARANCE_R: float = 8.0      # Ø16 clearance through-bore

# Galvanic-isolation bushing OD recommendation (per ROV_INTEGRATION §1b).
# Adapters that bolt to metal arms should use a nylon/PTFE shoulder bushing.
GALVANIC_BUSHING_OD: float = 6.0            # Ø6 nylon shoulder bushing (recommend)

# Material colours
C_PA12_GF = Color(0.35, 0.32, 0.28)         # printed PA12-GF (default for all)
C_AL6082  = Color(0.78, 0.78, 0.80)         # machined aluminium (optional variant)


def gripper_bolt_holes(adapter_thickness: float,
                       hole_r: float = GRIPPER_FLANGE_BOLT_R,
                       overshoot: float = 0.5) -> list[Cylinder]:
    """Return 4 cylinders for the M4 clearance holes — subtract from your
    adapter body to make the gripper-side bolt-pattern. Cylinders are
    positioned so they pass cleanly through Z = -overshoot..(thickness+overshoot)."""
    holes: list[Cylinder] = []
    h = adapter_thickness + 2 * overshoot
    for (x, y) in GRIPPER_FLANGE_BOLT_XY:
        c = Cylinder(radius=hole_r, height=h).moved(
            Location((x, y, adapter_thickness / 2)))
        holes.append(c)
    return holes


def shaft_clearance_bore(adapter_thickness: float,
                         radius: float = GRIPPER_SHAFT_CLEARANCE_R,
                         overshoot: float = 0.5) -> Cylinder:
    """A Ø16 (default) clearance bore for the shaft + lip-seal stack,
    centred at (X = -12, Y = 0). Subtract from the adapter body."""
    h = adapter_thickness + 2 * overshoot
    return Cylinder(radius=radius, height=h).moved(
        Location((GRIPPER_SHAFT_OFFSET_X, GRIPPER_SHAFT_OFFSET_Y,
                  adapter_thickness / 2)))


def rect_blank(width: float, depth: float, thickness: float,
               edge_radius: float = 3.0) -> Part:
    """A rectangular blank centred on the adapter origin, sitting in
    Z ≥ 0 (mating face at Z = 0). Filleted vertical edges for the printed
    PA12-GF aesthetic; pass edge_radius=0 to disable."""
    blank = Box(width, depth, thickness).moved(
        Location((0, 0, thickness / 2)))
    if edge_radius > 0:
        # vertical edges only
        from build123d import Axis
        blank = fillet(blank.edges().filter_by(Axis.Z), radius=edge_radius)
    return blank


def disc_blank(radius: float, thickness: float) -> Part:
    """A circular disc centred on the adapter origin, sitting in Z ≥ 0
    (mating face at Z = 0)."""
    return Cylinder(radius=radius, height=thickness).moved(
        Location((0, 0, thickness / 2)))


# ---------------------------------------------------------------------------
# Convenience: standard adapter cleanup that every module ends with
# ---------------------------------------------------------------------------

def finalize(part: Part,
             label: str,
             colour: Color = C_PA12_GF) -> Compound:
    """Wrap a Part in a Compound with the printed colour + label."""
    part.color = colour
    part.label = label
    return Compound(label=label, children=[part])


def m_clearance_radius(thread: float, fit: str = "close") -> float:
    """Standard metric clearance-hole radius for printed PA12-GF.

    Returns the radius (mm) for a clearance hole of the given thread
    (e.g. 4.0 for M4). `fit` is "close" (ISO H12/h13) or "free"
    (ISO H13/h14). Default "close" matches gripper.py's BOLT_R = 2.25
    for M4."""
    # Close clearance, ISO 273. Diameters in mm:
    close = {2.5: 2.9, 3: 3.4, 4: 4.5, 5: 5.5, 6: 6.6, 8: 9.0, 10: 11.0}
    free  = {2.5: 3.2, 3: 3.6, 4: 4.8, 5: 5.8, 6: 7.0, 8: 10.0, 10: 12.0}
    table = close if fit == "close" else free
    if thread not in table:
        raise ValueError(f"Unknown clearance for M{thread}")
    return table[thread] / 2.0

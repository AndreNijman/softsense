"""adapter_iso13628_d_handle.py — ISO 13628-8 / API 17H Class A D-handle
mounted onto the gripper as a "held tool, not bolt-on" interface for
Schilling / Kraft / ECA / Hydro-Lek work-class manipulator arms.

Operating principle (per ../../interfaces/schilling-kraft.md §6 + §9-B):
the arm's *existing standard parallel-acting jaws* clamp this printed
handle as if it were any other subsea tool. The handle absorbs the jaw's
clamp force; the arm never bolts to anything. This is the mass-appropriate,
vendor-agnostic, ISO-standardised answer to the question "can we work
with a TITAN 4" — we are 0.3 % of TITAN 4's lift envelope, so we deploy
the way every other lightweight subsea tool deploys: a passive bar inside
the arm's standard jaws.

Geometry (ISO 13628-8 / API 17H "Class A" subsea D-handle, dossier §6 + §9):
- Ø19 mm bar, ≥ 100 mm graspable length (the part the arm's jaws grip)
- Ø70 mm circular flange, Ø56 mm PCD, 4 × M6 clearance holes
- Bar parallel to the flange face, supported above it by two buttresses
- Gap between bar and flange face large enough that the jaw fully encloses
  the bar without contacting the flange (we use ~35 mm clearance)

Adapter stack (gripper-local frame from `_base.py`):
- Z = 0 .. transition_T: rectangular-to-circular transition body that
  bolts onto the gripper bottom flange (4× M4 on rectangular 76×16 pattern)
  and grows to the Ø70 ISO D-handle flange face.
- Z = transition_T: Ø70 disc with the ISO 4× M6 bolt pattern (decorative
  on a one-piece print — kept so the geometry is dimensionally
  ISO-compliant and the bar piece could be split off as a bolted sub-part
  for a "real" build).
- Z = transition_T .. transition_T + bar_clearance: two buttresses lifting
  the bar above the flange face.
- Bar axis: parallel to adapter +Y (perpendicular to the gripper jaw
  open/close axis +X). Rationale: the arm clamps the bar with its jaws
  closing along X, perpendicular to our gripper's own jaw motion — the
  snag-free configuration recommended by ISO 13628-8 (T-bar handles can
  snag on intermeshing jaws; the D-form does not). Bar is centred on the
  flange centroid in X and offset above the flange in Z.

Gripper-side bolt pattern note: the M4 holes at X = ±38 sit on the very
edge of a 76 mm-wide rectangle. We therefore use FOOTPRINT_X = 96 (the
established `_base.py` convention) for the base of the transition and
narrow up to the Ø70 disc above. The brief's "76×28 rectangle" is the
*upper* starting profile of the transition, not the gripper-mating
footprint; clarified here so the bolts have a sane 10 mm side-margin.

Mass estimate (PA12-GF, 1.05 g/cc):
- Bar         Ø19 × 100  ≈  30 g
- Flange      Ø70 × 6    ≈  25 g
- Transition  96×28 → Ø70 over 12 mm  ≈  30 g
- Buttresses  2 × small  ≈  10 g
- TOTAL                  ≈  95 g  (within the 80–120 g target)
"""
from __future__ import annotations

import os

from build123d import (
    Axis,
    Box,
    Color,
    Compound,
    Cylinder,
    Location,
    Part,
    Plane,
    Rectangle,
    Circle,
    Vector,
    loft,
    fillet,
    export_step,
)

from _base import (
    C_PA12_GF,
    GRIPPER_FLANGE_FOOTPRINT_X,   # 96
    GRIPPER_FLANGE_FOOTPRINT_Y,   # 28
    finalize,
    gripper_bolt_holes,
    m_clearance_radius,
    shaft_clearance_bore,
)

# ---------------------------------------------------------------------------
# ISO 13628-8 / API 17H Class A D-handle geometry (dossier §6 + §9)
# ---------------------------------------------------------------------------
BAR_OD: float = 19.0          # standard "large" handle bar diameter
BAR_LEN: float = 100.0        # ≥ 100 mm graspable length per ISO 13628-8

FLANGE_OD: float = 70.0       # ISO D-handle flange OD
FLANGE_T: float = 6.0         # flange thickness
FLANGE_PCD: float = 56.0      # ISO PCD for the M6 mounting pattern
FLANGE_M6: float = 6.0        # M6 mounting fasteners
FLANGE_M6_COUNT: int = 4      # 4× M6 (Class A); 8× M6 is the higher-load variant

# Transition body: gripper-flange footprint → Ø70 disc
TRANSITION_T: float = 12.0    # axial thickness of the transition body
TRANSITION_TOP_X: float = 76.0   # upper rectangle width (per brief)
TRANSITION_TOP_Y: float = GRIPPER_FLANGE_FOOTPRINT_Y  # 28 mm (per brief)

# Bar mounting: how far the bar sits above the flange face
BAR_CLEARANCE: float = 35.0   # 30–50 mm per brief — jaw envelopes the bar
BUTTRESS_W: float = 14.0      # width along bar axis of each buttress
BUTTRESS_T: float = 10.0      # thickness perpendicular to bar axis

# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build(include_flange_bolts: bool = True) -> Compound:
    """Build the ISO 13628-8 D-handle adapter Compound.

    `include_flange_bolts`: if True (default), the Ø70 flange face carries
    4× M6 clearance holes on Ø56 PCD — keeps the part dimensionally
    ISO-compliant, and lets a future variant split the bar off as a
    bolted sub-assembly.
    """
    # 1) Base of the transition: a 96×28 rectangular pad on the gripper
    #    flange face (Z = 0). The full FOOTPRINT_X width is required so
    #    the M4 bolts at X = ±38 sit inside the part with a side margin.
    base_t = 4.0   # short plinth before the rect-to-circle transition begins
    base = Box(GRIPPER_FLANGE_FOOTPRINT_X, GRIPPER_FLANGE_FOOTPRINT_Y, base_t)
    base = base.moved(Location((0, 0, base_t / 2)))

    # 2) Rectangle (76×28) → Ø70 circle loft, height = TRANSITION_T.
    z_bot = base_t
    z_top = base_t + TRANSITION_T
    bot_sk = Plane.XY.offset(z_bot) * Rectangle(TRANSITION_TOP_X,
                                                TRANSITION_TOP_Y)
    top_sk = Plane.XY.offset(z_top) * Circle(radius=FLANGE_OD / 2)
    transition = loft([bot_sk, top_sk])

    # 3) The Ø70 × 6 mm ISO flange disc sitting on top of the transition.
    flange_z0 = z_top
    flange = Cylinder(radius=FLANGE_OD / 2, height=FLANGE_T).moved(
        Location((0, 0, flange_z0 + FLANGE_T / 2)))

    body: Part = base + transition + flange

    # 4) Bar: Ø19 × 100 mm, axis parallel to adapter +Y, centred on
    #    the flange centroid in X. Held above the flange by BAR_CLEARANCE.
    flange_top_z = flange_z0 + FLANGE_T
    bar_axis_z = flange_top_z + BAR_CLEARANCE + BAR_OD / 2
    bar = Cylinder(radius=BAR_OD / 2, height=BAR_LEN).moved(
        Location((0, 0, bar_axis_z), (90, 0, 0)))  # rotate so axis = Y

    # 5) Two buttresses connect the bar ends down to the flange top face.
    #    Each is a small box from the flange face up to the bar centre,
    #    centred on the bar axis in X and located near the bar ends in Y.
    butt_h = BAR_CLEARANCE + BAR_OD / 2   # from flange top to bar centre
    butt_y_offset = (BAR_LEN / 2) - (BUTTRESS_W / 2) - 4.0  # 4 mm inset from bar end
    for sign in (-1, +1):
        butt = Box(BUTTRESS_T, BUTTRESS_W, butt_h)
        butt = butt.moved(Location(
            (0, sign * butt_y_offset, flange_top_z + butt_h / 2)))
        body = body + butt
    body = body + bar

    # 6) Subtract gripper-side features.
    #    - 4× M4 clearance through the base + transition.
    #    - Shaft clearance Ø16 through the base + transition at (X=-12, Y=0).
    feature_T = base_t + TRANSITION_T + FLANGE_T   # full stack height
    for h in gripper_bolt_holes(feature_T):
        body = body - h
    body = body - shaft_clearance_bore(feature_T)

    # 7) Optional ISO M6 flange bolt pattern through the Ø70 disc.
    if include_flange_bolts:
        m6_r = m_clearance_radius(FLANGE_M6, fit="close")  # 3.3 mm
        for k in range(FLANGE_M6_COUNT):
            import math
            a = math.radians(360.0 / FLANGE_M6_COUNT * k + 45.0)
            cx = (FLANGE_PCD / 2) * math.cos(a)
            cy = (FLANGE_PCD / 2) * math.sin(a)
            # only punch through the flange disc (not the transition below)
            hole = Cylinder(radius=m6_r, height=FLANGE_T + 1.0).moved(
                Location((cx, cy, flange_z0 + FLANGE_T / 2)))
            body = body - hole

    # 8) Light edge fillet on the transition top corners for the printed look.
    try:
        body = fillet(
            body.edges().filter_by(Axis.Z).group_by(Axis.Z)[-1],
            radius=1.5,
        )
    except Exception:
        # fillet is cosmetic — don't fail STEP export if topology rejects it
        pass

    return finalize(body, label="adapter_iso13628_d_handle", colour=C_PA12_GF)


# ---------------------------------------------------------------------------
# STEP CLI entry
# ---------------------------------------------------------------------------

def gen_step() -> Compound:
    return build()


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.normpath(os.path.join(out_dir, "adapter_iso13628_d_handle.step"))
    export_step(gen_step(), out)
    print(f"wrote {out}")

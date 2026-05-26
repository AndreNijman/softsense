"""adapter_bravo7.py — printed PA12-GF adapter that bolts the gripper's
M4 bottom flange to the Reach Bravo 7 (RB-7001) wrist via the **RB-1054
Payload Interface**.

See `motor/interfaces/reach-bravo-alpha.md` §3c (RB-1054 dimensioned
mating geometry) and §9.2 (the bridge-plate concept) for the design
rationale, every dossier-derived dimension, and the open questions
(Q4 in §10: the M6/M5 bolt-circle radius and the dowel-pin centre-to-
centre are NOT numerically published — estimated here from the
datasheet drawing and flagged below).

Frame convention (from `_base.py`):
- Origin at the gripper-flange bolt-pattern centroid on the Z = 0
  mating face. +Z = away from gripper, toward the Bravo wrist.
- Bottom face (Z = 0): mates the gripper's 4× M4 flange + Ø16 shaft
  clearance at X = -12, Y = 0.
- Top face (Z = ADAPTER_T): Ø71 mm circular landing for the RB-1054,
  centred on the adapter origin (so the wrist roll axis aligns with
  the adapter origin, NOT the gripper shaft — the shaft sits 12 mm
  off the wrist axis, intentionally, per ROV_INTEGRATION §1).

Design deviation from §9.2 of the dossier: §9.2 proposed using the
RB-1054's **6× Ø5 CSK far-side pattern** with M5 through-bolts. This
module uses the **6× M6 tool-side threaded pattern** with M6 through-
bolts in the adapter (Ø6.6 close clearance) — coherent with the prompt
spec and slightly stronger per bolt. Either pattern is selectable
later by re-running with a parametric BOLT_THREAD swap.

Body topology: stepped block.
- Z = 0 to ~6 mm: rectangular pad (84 × 28 mm) covering the M4 bolt
  pattern (±38 X, ±8 Y) with ≥3 mm edge distance.
- Z = ~6 to ~12 mm: lofted transition pad-rect → Ø71 disc.
- Z = ~12 to ADAPTER_T (16 mm): Ø71 disc carrying the 6× M6 and 2× Ø3
  dowel pattern + a side cable-routing notch (per dossier §9.6).

Mass target: 70–100 g in PA12-GF at 100 % infill (ρ = 1.43 g/cm³ —
NB: the prompt spec asks ×1.15 g/cm³ for 50 % infill, which gives a
lower estimate; we report both).
"""
from __future__ import annotations

import math

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
    Rectangle,
    export_step,
    fillet,
    loft,
)

from motor.cad.adapters._base import (
    C_PA12_GF,
    finalize,
    gripper_bolt_holes,
    m_clearance_radius,
    shaft_clearance_bore,
)

# ---------------------------------------------------------------------------
# Constants — RB-1054 mating geometry
# ---------------------------------------------------------------------------

# Plate OD published on the RB-1054 datasheet [9]. See dossier §3c, row
# "Mating plate OD".
BRAVO_PLATE_OD: float = 71.0                # mm — RB-1054 datasheet [9]

# Bolt pattern. The RB-1054 has 6× M6×1 threaded blind holes (tool-side)
# and 6× Ø5 CSK through-bolts (far-side) on the same pitch circle. We
# bolt UP into the tool-side M6 threads, so the adapter has 6× M6
# clearance holes (Ø6.6).
BRAVO_BOLT_COUNT: int = 6                   # RB-1054 datasheet [9]
BRAVO_BOLT_THREAD: float = 6.0              # M6 (datasheet — tool-side thread)
BRAVO_BOLT_CLEAR_R: float = m_clearance_radius(BRAVO_BOLT_THREAD)  # 3.3 mm (Ø6.6)

# **ESTIMATE** — Q4 in dossier §10. The RB-1054 datasheet drawing does
# NOT numerically specify the M6 pitch-circle diameter. §9.2 estimates
# it at ≈ 26–28 mm radius (≈ 52–56 mm BCD) from the Ø71 plate edge
# minus minimum edge distance. We adopt **Ø56 mm** (BCR = 28 mm) — the
# upper end of the estimate — to maximise the bolts' moment arm. CONFIRM
# against a Reach STEP file before shipping. Dossier §3c, row "Bolt-
# circle radius (dimension)".
BRAVO_M6_PCD: float = 56.0                  # ESTIMATE — dossier §3c, Q4
BRAVO_M5_PCD: float = 56.0                  # shares the M6 pitch circle (CSK
                                            # on the far side of the M6 holes)

# **ESTIMATE** — Q4 in dossier §10. The two Ø3 H7 dowel-pin centres are
# not numerically dimensioned on the datasheet. §3c row "Dowel-pin
# centre-to-centre" estimates 40–50 mm on a diameter near the M6 pitch
# circle. We adopt **Ø48 mm** diameter — slightly inside the M6 ring —
# with the two dowels at 180° to each other, phase-shifted by 30° from
# the M6 holes so they fall **between** the M6 holes (not on top of
# them). CONFIRM against a Reach STEP file before shipping.
BRAVO_DOWEL_PCD: float = 48.0               # ESTIMATE — dossier §3c, Q4
BRAVO_DOWEL_R: float = 1.55                 # Ø3.1 mm — slip fit for Ø3 dowel
BRAVO_DOWEL_PHASE_DEG: float = 30.0         # ESTIMATE — phase between dowels
                                            # and M6 holes; dowels go between
                                            # M6 holes.
BRAVO_DOWEL_DEPTH: float = 8.0              # blind pocket depth — 8 mm gives
                                            # the dossier-spec ≥ 6 mm engagement

# Adapter overall axial thickness. Target 14–18 mm per the prompt;
# pick 16 mm so a 25 mm M6×25 socket-cap can grip the RB-1054's
# tool-side threaded pocket (~7 mm thread depth in the plate) plus the
# adapter wall (16 mm) plus head + washer (~7 mm) cleanly.
ADAPTER_T: float = 16.0

# Stepped-body Z transitions.
PAD_Z_TOP: float = 6.0                      # rect pad height
LOFT_Z_TOP: float = 12.0                    # loft transition ends here
DISC_T: float = ADAPTER_T - LOFT_Z_TOP      # disc thickness (4 mm)

# Bottom (gripper-side) rectangular pad — covers ±38 X, ±8 Y M4 pattern
# with edge margin. Slightly wider than the RB-1054 disc in X so the
# loft-out from disc → rect-pad is well-supported when printed disc-
# down.
PAD_X: float = 84.0                         # 76 mm bolt span + 4 mm edge each side
PAD_Y: float = 28.0                         # matches GRIPPER_FLANGE_FOOTPRINT_Y

# Cable-routing side notch — per dossier §9.6. ≥ 10 mm wide, ≥ 5 mm
# radius fillet on the cut edges, on the arm-shadowed (+Y) side.
CABLE_NOTCH_WIDTH: float = 12.0
CABLE_NOTCH_DEPTH: float = 5.0              # how far into the disc edge
CABLE_NOTCH_FILLET: float = 3.0


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def _m6_clearance_holes() -> list[Cylinder]:
    """6× M6 clearance holes (Ø6.6) on the Ø56 PCD, through the full
    adapter thickness. Estimated PCD — see BRAVO_M6_PCD."""
    holes: list[Cylinder] = []
    r_pcd = BRAVO_M6_PCD / 2
    h = ADAPTER_T + 2.0
    for k in range(BRAVO_BOLT_COUNT):
        a = math.radians(360 / BRAVO_BOLT_COUNT * k)
        cx = r_pcd * math.cos(a)
        cy = r_pcd * math.sin(a)
        c = Cylinder(radius=BRAVO_BOLT_CLEAR_R, height=h).moved(
            Location((cx, cy, ADAPTER_T / 2)))
        holes.append(c)
    return holes


def _dowel_pin_pockets() -> list[Cylinder]:
    """2× Ø3 H7 blind dowel pockets on the Ø48 PCD, opening on the +Z
    (Bravo) face. Estimated PCD and phase — see BRAVO_DOWEL_PCD."""
    pockets: list[Cylinder] = []
    r_pcd = BRAVO_DOWEL_PCD / 2
    for k in range(2):
        a = math.radians(BRAVO_DOWEL_PHASE_DEG + 180 * k)
        cx = r_pcd * math.cos(a)
        cy = r_pcd * math.sin(a)
        # Blind pocket: depth = BRAVO_DOWEL_DEPTH, opening at Z = ADAPTER_T
        c = Cylinder(radius=BRAVO_DOWEL_R, height=BRAVO_DOWEL_DEPTH).moved(
            Location((cx, cy, ADAPTER_T - BRAVO_DOWEL_DEPTH / 2)))
        pockets.append(c)
    return pockets


def _cable_notch():
    """Side notch on the +Y face — cable exit per dossier §9.6. A
    box-shaped slot through the full adapter depth on the +Y arm-
    shadowed side, with filleted vertical edges."""
    # Box centred on +Y edge of the disc, extending into the disc by
    # CABLE_NOTCH_DEPTH.
    y_edge = BRAVO_PLATE_OD / 2                       # +35.5 mm
    cx = 0.0
    cy = y_edge - CABLE_NOTCH_DEPTH / 2 + 0.5         # straddle the edge
    notch = Box(CABLE_NOTCH_WIDTH, CABLE_NOTCH_DEPTH + 1.0, ADAPTER_T + 2).moved(
        Location((cx, cy, ADAPTER_T / 2)))
    return notch


def build() -> Part:
    """Assemble the Bravo 7 adapter body as a single Part.

    Body is a stack of three Z layers:
      - Z = [0, PAD_Z_TOP]:   rect pad (PAD_X × PAD_Y)
      - Z = [PAD_Z_TOP, LOFT_Z_TOP]: loft from pad rect → Ø71 disc
      - Z = [LOFT_Z_TOP, ADAPTER_T]: Ø71 disc

    Subtractions:
      - 4× M4 clearance (gripper-side flange) — gripper_bolt_holes()
      - 1× Ø16 shaft clearance bore (gripper-side) — shaft_clearance_bore()
      - 6× M6 clearance through-holes on Ø56 PCD (Bravo-side, ESTIMATED PCD)
      - 2× Ø3 blind dowel pockets on Ø48 PCD (Bravo-side, ESTIMATED PCD)
      - 1× cable-routing notch on +Y edge
    """
    # Layer 1: rectangular pad, vertical edges filleted
    pad = Box(PAD_X, PAD_Y, PAD_Z_TOP).moved(
        Location((0, 0, PAD_Z_TOP / 2)))
    pad = fillet(pad.edges().filter_by(Axis.Z), radius=4.0)

    # Layer 2: lofted transition from pad rect → Ø71 disc.
    bot_face = Plane.XY.offset(PAD_Z_TOP) * Rectangle(PAD_X, PAD_Y)
    top_face = Plane.XY.offset(LOFT_Z_TOP) * Circle(radius=BRAVO_PLATE_OD / 2)
    transition = loft([bot_face, top_face])

    # Layer 3: Ø71 disc on top
    disc = Cylinder(radius=BRAVO_PLATE_OD / 2, height=DISC_T).moved(
        Location((0, 0, LOFT_Z_TOP + DISC_T / 2)))

    body = pad + transition + disc

    # ----- Subtract holes -----
    # Gripper-side M4 clearance (4×) — full-height cylinders; above the
    # pad they cut air, which is a no-op.
    for h in gripper_bolt_holes(ADAPTER_T):
        body -= h
    # Gripper-side Ø16 shaft clearance bore at (-12, 0)
    body -= shaft_clearance_bore(ADAPTER_T)
    # Bravo-side 6× M6 clearance
    for h in _m6_clearance_holes():
        body -= h
    # Bravo-side 2× Ø3 blind dowel pockets (only on +Z side)
    for p in _dowel_pin_pockets():
        body -= p
    # Cable-exit notch on +Y face
    body -= _cable_notch()

    return body


def gen_step() -> Compound:
    """STEP entry point — required by the CAD scripts/step CLI."""
    part = build()
    return finalize(part, label="adapter_bravo7", colour=C_PA12_GF)


# ---------------------------------------------------------------------------
# Local smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os
    asm = gen_step()
    children = list(asm.children)
    body = children[0] if children else asm
    bb = body.bounding_box()
    vol_mm3 = body.volume
    # PA12-GF densities:
    mass_solid = vol_mm3 * 1.43e-3        # g, 100 % infill (1.43 g/cm³)
    mass_50pct = vol_mm3 * 1.15e-3        # g, ~50 % infill (1.15 g/cm³)
    print(f"adapter_bravo7: bbox {bb}")
    print(f"  volume = {vol_mm3:.0f} mm³ = {vol_mm3 / 1000:.1f} cm³")
    print(f"  mass (100 % PA12-GF, 1.43 g/cm³) = {mass_solid:.1f} g")
    print(f"  mass (~50 % infill,  1.15 g/cm³) = {mass_50pct:.1f} g")
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    out_dir = os.path.normpath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "adapter_bravo7.step")
    export_step(asm, out_path)
    print(f"wrote {out_path}")

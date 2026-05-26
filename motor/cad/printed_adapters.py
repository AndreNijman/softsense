"""
printed_adapters.py — the FOUR printed parts that the BOM mentions but
the existing gripper.py does not model. Each is parameterised against
the gripper's input D-coupler (`SHAFT_COUPLER_R 5.0 / SHAFT_DFLAT 1.4 /
SHAFT_COUPLER_LEN 12`) and the chosen servo's horn pattern.

1. `servo_horn_adapter` — dry-side. Mates the servo horn (X-series serrated
   horn OR Feetech 25T spline) to the upper end of the Ø8 mm goBILDA
   shaft. Printed PA12-GF or PETG-HF.

2. `wet_d_socket` — wet-side. Mates the lower end of the Ø8 mm shaft
   to the gripper's D-coupler. Female Ø10 D-bore (matching the gripper)
   above, Ø8 H7 press-fit below. Printed PA12-GF or PETG-HF.

3. `servo_cradle` — printed sleeve that locates the servo case coaxially
   inside the 3" canister and constrains it against the dry-side end
   cap. Surfaces a design gap that the BOM hadn't yet itemised; we model
   it explicitly so the integrated assembly is realisable.

4. `cradle_endcap_spacer` — short printed disc between the servo cradle
   and the dry end cap interior face, drilled clear for cable routing.

All parts: origin at their natural mating face, local +Z = axis of
symmetry / servo-output direction.
"""

from __future__ import annotations

import math

from build123d import (
    Box,
    Color,
    Compound,
    Cylinder,
    Location,
    Plane,
)

# Tube ID from external_parts.py (kept hardcoded here so this module
# stays independently importable for visual QA):
TUBE_ID_3IN_ACR = 76.2

# Gripper D-coupler (read out of gripper.py):
GRIPPER_DCOUP_R    = 5.0
GRIPPER_DCOUP_DFLT = 1.4
GRIPPER_DCOUP_LEN  = 12.0

# Adapter shaft:
SHAFT_OD = 8.0
SHAFT_LEN = 50.0

C_PRINTED = Color(0.35, 0.32, 0.28)   # PA12-GF
C_PRINT_T = Color(0.55, 0.50, 0.45, 0.95)  # PETG-HF


# ==========================================================================
# 1. Servo horn adapter (dry side, on top of the servo)
# ==========================================================================
def servo_horn_adapter(label: str = "servo_horn_adapter",
                       horn_od: float = 19.0,
                       horn_pcd: float = 15.0,
                       pcd_screws: int = 4) -> Compound:
    """Disc that clamps to the servo horn (4 × M2.5 through a Ø15 PCD for the
    X-series; 1× M3 centre for 25T Feetech), with a Ø8 H7 axial press-fit
    bore for the shaft. Printed PA12-GF.

    Geometry: Ø22 disc, 12 mm thick. Bottom Ø19 counterbore matches the
    servo horn boss. Centre Ø8 bore for the shaft, depth 10 mm from the
    top (leaves 2 mm of bottom for the horn screws to bottom out).
    Four Ø2.8 (M2.5 clearance) screw holes on a Ø15 PCD through the
    bottom 4 mm.

    +Z = up (toward the dry end of the shaft); origin = bottom face that
    sits on the servo horn.
    """
    DISC_OD = 22.0
    DISC_T  = 12.0
    HORN_BORE_T = 3.0     # depth of the Ø19 counterbore that locates the horn
    body = Cylinder(radius=DISC_OD / 2, height=DISC_T).moved(
        Location((0, 0, DISC_T / 2)))
    # horn counterbore (open at bottom)
    horn_cb = Cylinder(radius=horn_od / 2 + 0.2, height=HORN_BORE_T).moved(
        Location((0, 0, HORN_BORE_T / 2)))
    body -= horn_cb
    # central shaft press-fit bore (from top, leaves 2 mm at bottom for screws)
    shaft_bore = Cylinder(radius=SHAFT_OD / 2 - 0.005, height=DISC_T - 2.0).moved(
        Location((0, 0, 2.0 + (DISC_T - 2.0) / 2)))
    body -= shaft_bore
    # M2.5 horn screw clearance — Ø2.8 through the bottom 4 mm
    for k in range(pcd_screws):
        a = math.radians(360 / pcd_screws * k + 45.0)
        cx = horn_pcd / 2 * math.cos(a)
        cy = horn_pcd / 2 * math.sin(a)
        s = Cylinder(radius=1.4, height=DISC_T + 1).moved(
            Location((cx, cy, DISC_T / 2)))
        body -= s
    body.color = C_PRINTED
    body.label = label
    return Compound(label=label, children=[body])


# ==========================================================================
# 2. Wet D-socket (wet side, on top of the shaft, takes the gripper coupler)
# ==========================================================================
def wet_d_socket(label: str = "wet_d_socket") -> Compound:
    """Female D-socket on top of the Ø8 shaft.
    Top end: Ø10 D-bore (gripper coupler), 12 mm engagement, D-flat 1.4 mm
        on +X (matches gripper.py SHAFT_DFLAT side).
    Bottom end: Ø8 H7 press-fit on the shaft, 6 mm engagement.

    Geometry: Ø16 cylinder, 20 mm overall.
    +Z = up (toward the gripper); origin = bottom face (sits on the shaft top).
    """
    OD = 16.0
    LEN = 20.0
    D_DEPTH = 12.0          # the gripper coupler engagement
    SHAFT_DEPTH = 6.0       # the shaft press-fit
    body = Cylinder(radius=OD / 2, height=LEN).moved(
        Location((0, 0, LEN / 2)))
    # D-bore from +Z top: Ø10 round with a 1.4 mm flat on +X
    d_bore = Cylinder(radius=GRIPPER_DCOUP_R + 0.2, height=D_DEPTH).moved(
        Location((0, 0, LEN - D_DEPTH / 2)))
    # flat: subtract a +X box that intrudes by GRIPPER_DCOUP_DFLT from the bore wall
    flat_in_x = GRIPPER_DCOUP_R - GRIPPER_DCOUP_DFLT   # 3.6 mm from centreline
    flat_box = Box(
        2 * (GRIPPER_DCOUP_R + 0.5 - flat_in_x),     # x extent
        2 * (GRIPPER_DCOUP_R + 0.5),                 # y extent
        D_DEPTH + 1,                                  # z extent
    ).moved(Location((
        flat_in_x + (GRIPPER_DCOUP_R + 0.5 - flat_in_x),
        0,
        LEN - D_DEPTH / 2,
    )))
    # the bore = a Ø10 cylinder, MINUS the flat box (the flat REMOVES nothing
    # extra by intersecting; we just keep the bore as a normal Ø10 hole AND
    # leave an extra sliver of material on +X equal to the D-flat depth.
    # Net effect: the bore is a Ø10 circle minus a chord of depth 1.4 mm
    # on +X — i.e. an axisymmetric D-shape, mating the gripper coupler.)
    # Build it as bore_keep_volume = bore - flat_keep
    body -= d_bore
    # Re-add the chord of material on +X that forms the D-flat surface
    chord = Box(GRIPPER_DCOUP_DFLT + 0.5,
                2 * (GRIPPER_DCOUP_R + 0.5),
                D_DEPTH).moved(Location((
        GRIPPER_DCOUP_R - GRIPPER_DCOUP_DFLT + (GRIPPER_DCOUP_DFLT + 0.5) / 2,
        0,
        LEN - D_DEPTH / 2,
    )))
    body += chord
    # Bottom Ø8 H7 shaft bore (press-fit, 5 µm interference)
    shaft_bore = Cylinder(radius=SHAFT_OD / 2 - 0.005, height=SHAFT_DEPTH).moved(
        Location((0, 0, SHAFT_DEPTH / 2)))
    body -= shaft_bore
    body.color = C_PRINTED
    body.label = label
    return Compound(label=label, children=[body])


# ==========================================================================
# 3. Servo cradle (locates the servo inside the 3" tube)
# ==========================================================================
def servo_cradle(label: str = "servo_cradle",
                 servo_w: float = 33.5,
                 servo_l: float = 58.5,
                 servo_h: float = 45.9,
                 horn_oh: float = 4.0,
                 ext_margin: float = 0.5) -> Compound:
    """Printed sleeve, ID = tube ID − slip clearance, OD = servo bounding
    box + radial clearance; rectangular pocket through the centre captures
    the servo body. Servo bolts to the cradle's underside via 4 × M2.5
    on the standard X-series 30×22 mm rect; cradle in turn rests against
    the dry-side end cap.

    Defaults are sized for the DYNAMIXEL XW540 / XM540 envelope (the
    longest of the four). Pass the appropriate servo_* dims for STS3250
    or STS3215. The Feetech bodies are narrower (20 mm) so the same
    cradle OD remains valid; only the pocket changes.

    +Z = horn axis (up = output side). Origin = bottom face of the
    cradle (the face that contacts the dry end cap interior).
    """
    od = TUBE_ID_3IN_ACR - 2 * ext_margin
    h = servo_h + horn_oh + 6.0   # 6 mm wall below the servo body
    body = Cylinder(radius=od / 2, height=h).moved(Location((0, 0, h / 2)))
    # rectangular pocket the servo case sits in (full height of the case)
    pocket = Box(servo_w + 1.0, servo_l + 1.0, servo_h).moved(
        Location((0, 0, 6.0 + servo_h / 2)))
    body -= pocket
    # horn clearance counterbore (Ø servo horn OD + 2 mm) above the pocket
    horn_cb = Cylinder(radius=12.0, height=horn_oh + 2.0).moved(
        Location((0, 0, 6.0 + servo_h + horn_oh / 2)))
    body -= horn_cb
    # cable-run notch out the -Y face for the servo cable
    cable_notch = Box(8.0, 12.0, 8.0).moved(
        Location((0, -(od / 2) + 4.0, 6.0 + servo_h - 4.0)))
    body -= cable_notch
    body.color = C_PRINTED
    body.label = label
    return Compound(label=label, children=[body])


# ==========================================================================
# 4. Cradle ↔ dry-end-cap spacer (thin disc, cable feed-through)
# ==========================================================================
def cradle_endcap_spacer(label: str = "cradle_endcap_spacer") -> Compound:
    """Thin disc (≈ 4 mm) sitting between the dry-side end cap interior
    face and the servo cradle's bottom face, with a Ø10 central hole for
    the cable bundle to pass through to the M10 penetrator. Indexes the
    cradle's angular orientation.

    +Z = up (toward the cradle); origin = bottom face (on the end cap).
    """
    t = 4.0
    od = TUBE_ID_3IN_ACR - 1.5
    body = Cylinder(radius=od / 2, height=t).moved(Location((0, 0, t / 2)))
    cable_hole = Cylinder(radius=5.0, height=t + 1).moved(
        Location((0, -CENTER_TO_CABLE_HOLE_OFFSET, t / 2)))
    body -= cable_hole
    body.color = C_PRINT_T
    body.label = label
    return Compound(label=label, children=[body])


CENTER_TO_CABLE_HOLE_OFFSET = 12.0   # cable feed offset from canister axis


# ==========================================================================
# Self-export when run as a script.
# ==========================================================================
if __name__ == "__main__":
    import os
    from build123d import export_step
    out = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out, exist_ok=True)
    parts = {
        "servo_horn_adapter":  servo_horn_adapter(),
        "wet_d_socket":        wet_d_socket(),
        "servo_cradle_xw540":  servo_cradle(),
        "servo_cradle_sts3250": servo_cradle(servo_w=20.0, servo_l=54.0, servo_h=47.0),
        "cradle_endcap_spacer": cradle_endcap_spacer(),
    }
    for name, p in parts.items():
        f = os.path.join(out, f"{name}.step")
        export_step(p, f)
        print(f"wrote {f}")

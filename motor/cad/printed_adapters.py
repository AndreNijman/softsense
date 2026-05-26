"""
printed_adapters.py — the printed PA12-GF / PETG-HF parts that the BOM
mentions but `gripper.py` does not model. Two families:

A. Drivetrain parts (the gripper's input shaft path):
   1. `servo_horn_adapter` — dry-side. Mates the servo horn (X-series serrated
      horn OR Feetech 25T spline) to the upper end of the Ø8 mm goBILDA shaft.
   2. `wet_d_socket` — wet-side. Mates the lower end of the Ø8 shaft to the
      gripper's D-coupler. Female Ø10 D-bore + 1.4 mm flat above, Ø8 H7
      press-fit below.
   3. `servo_cradle` — locates the servo case coaxially inside the 3" canister.
   4. `cradle_endcap_spacer` — short disc with a cable feed-through.

B. Visual-unibody shrouds — printed PA12-GF, ALL SNAP-FIT, all cosmetic
   (NOT pressure-bearing — the BR canister underneath stays the pressure
   boundary). Match the `gripper.py` philosophy: 3D printed, foolproof,
   snap-on, zero maintenance.
   5. `wrist_plate` — printed PA12-GF block. Captures the BR wet end cap on
      its canister face, presents a flat mating face to the gripper's M4 bottom
      flange. Filleted edges. The shaft passes through a clearance hole — the
      lip seal in the BR cap below it is still the pressure seal.
   6. `canister_fairing` — printed PA12-GF 2-piece snap-clip sleeve that slides
      over the BR tube. Cosmetic dark-CFRP look; the BR tube inside stays
      the pressure vessel.
   7. `pod_cap_shroud` — printed PA12-GF shroud over the BR dry end cap.
      Single cable exit (the WetLink penetrator sits in 1 hole; 3 blank
      plugs sit in the others, all hidden by the shroud).

All parts: origin at their natural mating face, local +Z = axis of
symmetry / servo-output direction.
"""

from __future__ import annotations

import math

from build123d import (
    Box,
    Circle,
    Color,
    Compound,
    Cylinder,
    Location,
    Plane,
    Rectangle,
    loft,
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
# 5. wrist_plate — printed transition between canister wet cap and gripper
# ==========================================================================
# Geometry: a chamfered/filleted block. Top face is a rectangle that mates
# the gripper's bottom flange (4 × M4 clearance bores at ±38 × {2,18} —
# matches gripper.py BOLT_XZ). Bottom face has a circular recess that
# accepts the BR-100949-999 wet end cap's flange (Ø98 → recess Ø99).
# A Ø10 clearance bore at the centre lets the adapter shaft pass through;
# the lip seal in the BR cap below stays the pressure seal.
#
# Snap-fit retention: 4 internal hooks at the four corners of the cap
# recess that grip the BR cap's outer flange. NO bolts to the cap, NO
# adhesive, NO maintenance.
#
# Origin: centre of TOP face (the face that mates the gripper flange).
# +Z = down toward the canister.

WRIST_PLATE_OD  = 100.0  # ≥ BR cap OD 98 so the cap fits inside the recess; matches canister_fairing OD
WRIST_PLATE_H   = 54.0   # axial thickness — tall enough to bridge gripper flange to BR wet cap (1 housing, not a disc)
BR_CAP_OD       = 98.0
BR_CAP_FLANGE_T = 16.0
GRIPPER_FLANGE_BOLT_R = 2.25
GRIPPER_FLANGE_BOLT_XZ = [(-38.0, 2.0), (38.0, 2.0), (-38.0, 18.0), (38.0, 18.0)]


def wrist_plate(label: str = "wrist_plate",
                shaft_offset_x: float = 0.0,
                shaft_offset_y: float = 0.0,
                bolt_offset_x: float = 0.0,
                bolt_offset_y: float = 0.0) -> Compound:
    """Printed PA12-GF wrist plate. Snap-fits onto the BR wet end cap;
    presents a flat face that the gripper bolts onto via its existing
    4×M4 bottom-flange pattern.

    Cylindrical OD = 96 mm — same as the `canister_fairing`, so the wrist
    reads as a smooth continuation of the canister silhouette rather than
    a wider pedestal sticking out at the sides.

    `shaft_offset_x` / `shaft_offset_y` place the Ø10 shaft clearance hole
    off the wrist's own centre (used by the UNIBODY assembly where the
    wrist is centred on the canister body but the drive shaft is off-centre).
    `bolt_offset_x` / `bolt_offset_y` similarly shift the 4×M4 bolt pattern
    so the gripper flange holes still align with the gripper's own off-centre
    flange (-38/+38 from the gripper enclosure centre, not from the canister
    body centre — so apply +SHAFT_OFFSET_X to shift the bolt pattern with
    the gripper).

    The plate is purely cosmetic + structural-bracket — it carries the
    gripper's mounting load, not the pressure load.
    """
    body = Cylinder(radius=WRIST_PLATE_OD / 2, height=WRIST_PLATE_H).moved(
        Location((0, 0, WRIST_PLATE_H / 2)))

    # cap recess on -Z side: Ø99 cylindrical pocket, depth = cap flange thickness
    cap_recess = Cylinder(radius=(BR_CAP_OD + 1.0) / 2,
                          height=BR_CAP_FLANGE_T + 1.0).moved(
        Location((0, 0, BR_CAP_FLANGE_T / 2 + 0.5)))
    body -= cap_recess

    # Through-bore at the off-centre shaft position. Ø22 (wider than the
    # Ø16 wet D-socket) so the D-socket + shaft + lip seal all fit through
    # the housing. The housing is purely cosmetic structural — nothing
    # contacts the bore wall.
    shaft_clearance = Cylinder(radius=11.0, height=WRIST_PLATE_H + 2).moved(
        Location((shaft_offset_x, shaft_offset_y, WRIST_PLATE_H / 2)))
    body -= shaft_clearance

    # 4×M4 clearance holes for the gripper flange. gripper.py BOLT_XZ is
    # in MODEL (X,Z); after the gripper's +90X reorient (model+Z → world-Y)
    # the bolt holes land at world (X, Y) = (bx, -bz). Since the wrist's
    # local frame is centred on the canister body at world (0, -12), the
    # wrist-local coordinate is (bx - 0, -bz - (-12)) = (bx, 12 - bz).
    for bx, bz in GRIPPER_FLANGE_BOLT_XZ:
        cy = 12.0 - bz   # bz=2→cy=10, bz=18→cy=-6
        h = Cylinder(radius=GRIPPER_FLANGE_BOLT_R + 0.2,
                     height=WRIST_PLATE_H + 1).moved(
            Location((bx + bolt_offset_x, cy + bolt_offset_y, WRIST_PLATE_H / 2)))
        body -= h

    body.color = Color(0.78, 0.80, 0.83)   # brushed-aluminium look
    body.label = label
    return Compound(label=label, children=[body])


# ==========================================================================
# 6. canister_fairing — 2-piece snap-clip cosmetic sleeve over the BR tube
# ==========================================================================
CANISTER_FAIRING_OD = 100.0   # matches wrist_plate OD so wrist→fairing reads as one body
CANISTER_FAIRING_ID = 87.0    # BR tube OD + 0.5 mm slip fit per side


def canister_fairing(length: float = 150.0,
                     label: str = "canister_fairing") -> Compound:
    """Printed PA12-GF cosmetic sleeve over the BR tube. Two halves that
    snap together along their split lines (the snap geometry is internal
    and not modelled at this fidelity — the visible silhouette is what
    matters here). OD = 96 mm (matches `wrist_plate` width), ID = 87 mm
    (slip fit over BR 86.5 mm tube OD).

    Renders as one Compound (the two halves abstracted) since the snap
    join is internal.
    """
    od_r = CANISTER_FAIRING_OD / 2
    id_r = CANISTER_FAIRING_ID / 2
    outer = Cylinder(radius=od_r, height=length)
    inner = Cylinder(radius=id_r, height=length + 2)
    sleeve = outer - inner
    sleeve.color = Color(0.18, 0.18, 0.20)   # dark CFRP-look
    sleeve.label = label
    return Compound(label=label, children=[sleeve])


# ==========================================================================
# 7. pod_cap_shroud — printed PA12-GF shroud over the BR dry end cap
# ==========================================================================
POD_CAP_OD       = 100.0   # matches the pod silhouette
POD_CAP_T        = 14.0
POD_CABLE_BORE_R = 5.0
POD_CABLE_OFFSET = 18.0


# ==========================================================================
# 8. gripper_taper_cover — printed PA12-GF tapered shroud that snaps over
#    the gripper enclosure and visually continues the pod silhouette down
#    until just above the fingers. Round at top (mates wrist_plate bottom),
#    rounded-rectangle at bottom (just bigger than the gripper enclosure).
# ==========================================================================
GRIPPER_TAPER_COVER_H       = 50.0   # axial height — covers the enclosure body
GRIPPER_TAPER_COVER_TOP_OD  = 100.0  # matches wrist_plate / fairing
GRIPPER_TAPER_COVER_BOT_W   = 108.0  # enclosure 96 + 6 mm wall clearance per side
GRIPPER_TAPER_COVER_BOT_D   = 42.0   # enclosure depth ~30 + 6 mm wall clearance per side
GRIPPER_TAPER_COVER_WALL    = 3.0    # PA12-GF wall thickness


def gripper_taper_cover(label: str = "gripper_taper_cover") -> Compound:
    """Tapered printed PA12-GF cover. Snap-fits over the gripper enclosure body
    by friction + four internal hook clips (geometry abstracted at this fidelity).

    Top face: Ø100 mm circle — mates the bottom face of the `wrist_plate`
    flush, so the canister → wrist → cover silhouette reads as one continuous
    pod from above. Bottom face: rounded-rectangle (108 × 42 mm), slightly
    larger than the gripper enclosure (96 × 30) so the cover slides down
    over it. The fingers emerge UNCOVERED below the bottom face.

    Hollow inside (3 mm wall) so the existing gripper enclosure body slides
    up into it without modification. No pressure-bearing role — purely the
    visual unibody continuation.

    +Z = UP (toward wrist plate). Origin = top face centre.
    """
    # Outer profile: top circle, bottom rounded-rect at offset
    top_face = Plane.XY * Circle(radius=GRIPPER_TAPER_COVER_TOP_OD / 2)
    bot_plane = Plane.XY.offset(-GRIPPER_TAPER_COVER_H)
    bot_face = bot_plane * Rectangle(
        GRIPPER_TAPER_COVER_BOT_W, GRIPPER_TAPER_COVER_BOT_D)
    outer = loft([top_face.sketch, bot_face.sketch] if hasattr(top_face, "sketch")
                 else [top_face, bot_face])

    # Inner cavity (wall-shrunk version) — opens through both top and bottom so
    # the gripper enclosure body slides up from below, and the input shaft +
    # D-coupler pass through the top.
    W = GRIPPER_TAPER_COVER_WALL
    top_in_face = Plane.XY.offset(+0.5) * Circle(
        radius=GRIPPER_TAPER_COVER_TOP_OD / 2 - W)
    bot_in_face = Plane.XY.offset(-GRIPPER_TAPER_COVER_H - 0.5) * Rectangle(
        GRIPPER_TAPER_COVER_BOT_W - 2 * W,
        GRIPPER_TAPER_COVER_BOT_D - 2 * W)
    inner = loft([top_in_face.sketch, bot_in_face.sketch] if hasattr(top_in_face, "sketch")
                 else [top_in_face, bot_in_face])

    cover = outer - inner
    cover.color = Color(0.62, 0.65, 0.70)   # slightly darker than wrist plate
    cover.label = label
    return Compound(label=label, children=[cover])


def pod_cap_shroud(label: str = "pod_cap_shroud") -> Compound:
    """Printed PA12-GF cap shroud. Snap-fits over the BR dry end cap so
    the BR flange OD (98 mm) and the 4 × M10 penetrator/plug heads are
    visually hidden. One off-centre hole lets the single cable exit;
    the other three M10 holes carry BR blank plugs (still pressure-sealed),
    hidden by the shroud.

    Origin: centre of the wet (top) face that mates the BR cap.
    +Z = into the canister (the BR cap's exterior face is at local z = 0;
    the shroud body extends in +Z).
    """
    body = Cylinder(radius=POD_CAP_OD / 2, height=POD_CAP_T).moved(
        Location((0, 0, POD_CAP_T / 2)))
    # Single cable exit hole at +Y offset (above one of the BR M10 hole
    # positions on the Ø60 PCD)
    cable = Cylinder(radius=POD_CABLE_BORE_R, height=POD_CAP_T + 2).moved(
        Location((0, POD_CABLE_OFFSET, POD_CAP_T / 2)))
    body -= cable
    body.color = Color(0.78, 0.80, 0.83)   # brushed-aluminium look
    body.label = label
    return Compound(label=label, children=[body])


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
        "wrist_plate":         wrist_plate(),
        "canister_fairing":    canister_fairing(),
        "pod_cap_shroud":      pod_cap_shroud(),
    }
    for name, p in parts.items():
        f = os.path.join(out, f"{name}.step")
        export_step(p, f)
        print(f"wrote {f}")

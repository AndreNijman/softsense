"""
system_assembly.py — the FULL gripper-plus-canister-plus-actuator
integrated assembly. Brings every bought + printed + existing-gripper
part into one Compound, in world coordinates.

Two variants, mirroring `motor/ROV_INTEGRATION.md` §2d:

    T2 (primary, ≤30 m): Option A — Ø8 stainless shaft through Ø14 lip seal
                          in a blank BR end cap. Worked example: STS3250.
    T3 (fallback, >30 m): Option B — magnetic coupling; no shaft penetrates
                          the canister wall. Inner & outer N52 rotors with
                          a thin printed barrier.

Note on bracketry (per advisor):
    The gripper has a 4 × M4 bolt pattern on its base flange sized for the
    ROV arm. The Blue Robotics 3" end cap has a 6 × M3 perimeter pattern
    around its flange. These do NOT mate directly; in service both the
    gripper and the canister are independently fixed to the ROV arm with
    user-supplied arm-side bracketry, and the shaft is the only mechanical
    link between them. Here we position them coaxially with a small air
    gap and leave the bracketry as a user-supplied item.

Coordinate frame (matches gripper.py final world frame, +90X reoriented):
    +X horizontal, +Z up (fingers point up), gripper flange face at z=-25,
    shaft / canister axis along world Z, centred on (DRIVE_X, -DRIVE_Z)
    = (-12, -11.72).

Run from repo root:
    python motor/cad/system_assembly.py             # T2 variant (default)
    GRIPPER_CANISTER_VARIANT=T3 python motor/cad/system_assembly.py
Outputs to motor/cad/output/.
"""

from __future__ import annotations

import os
import sys

# import gripper.py from the repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.insert(0, os.path.dirname(__file__))

import math

from build123d import (
    Box,
    Color,
    Compound,
    Cylinder,
    Location,
    Plane,
    export_step,
)

# Existing gripper:
import gripper as G

# Purchased + printed parts (this folder)
from external_parts import (
    dynamixel_xw540,
    feetech_sts3250,
    feetech_sts3215,
    dynamixel_xm540,
    br_tube_3in_240,
    br_end_cap_wet_lipseal,
    br_end_cap_dry_4xm10,
    wetlink_penetrator,
    wetlink_blank_m10,
    lip_seal_8x14x4,
    gobilda_shaft_8x50,
    n52_magnet_ring_80mm,
    ktr_minex_sa_60_8,
    TUBE_LEN_240,
    CAP_FLANGE_T,
    CAP_BOSS_LEN,
    CAP_TOTAL_LEN,
    TUBE_ID_3IN_ACR,
)
from printed_adapters import (
    servo_horn_adapter,
    wet_d_socket,
    servo_cradle,
    cradle_endcap_spacer,
)

VARIANT = os.environ.get("GRIPPER_CANISTER_VARIANT", "T2").upper()
SERVO   = os.environ.get("GRIPPER_CANISTER_SERVO", "STS3250").upper()
OUT_DIR = os.path.join(os.path.dirname(__file__), "output")

# --------------------------------------------------------------------------
# World-frame anchors (post the gripper's +90X reorient)
# --------------------------------------------------------------------------
# Gripper input D-coupler exits the flange bottom face at:
SHAFT_X_W = G.DRIVE_X                              # -12
SHAFT_Y_W = -G.DRIVE_Z                             # -11.72
FLANGE_BOT_Z = G.BOT_FLANGE_Y[0]                   # -25 (flange bottom face)
GRIPPER_COUPLER_BOT_Z = (G.BOT_FLANGE_Y[0]
                         - G.SHAFT_SHOULDER_T
                         - G.SHAFT_COUPLER_LEN)    # -25 - 2 - 12 = -39

# Canister hangs below the gripper. We leave a small air gap between the
# bottom of the gripper coupler and the top of the wet D-socket: the D-socket
# is what RECEIVES that coupler, so they overlap, not abut.
#
# The wet D-socket's TOP is the gripper-coupler-engagement face; it must
# sit at z = FLANGE_BOT_Z so the gripper coupler (which extends from
# z=FLANGE_BOT_Z-2 down to FLANGE_BOT_Z-14) engages by 12 mm of the
# socket's 20 mm height. So:
WET_DSOCKET_TOP_Z = FLANGE_BOT_Z - 2.0             # leave 2 mm air-gap to flange face
WET_DSOCKET_LEN = 20.0
WET_DSOCKET_BOT_Z = WET_DSOCKET_TOP_Z - WET_DSOCKET_LEN

# The shaft press-fits into the bottom of the wet D-socket 6 mm. Its top
# end is therefore 6 mm below the socket top; shaft hangs down from there
# for 50 mm. The lip seal sits ON the shaft mid-length, captured in the
# end cap.
SHAFT_TOP_Z = WET_DSOCKET_BOT_Z + 6.0              # press-fit overlap
SHAFT_BOT_Z = SHAFT_TOP_Z - 50.0                   # 50 mm goBILDA shaft

# The wet end cap exterior (wet, +Z) face sits roughly midway down the
# shaft (so ~25 mm of shaft sits in the canister, ~25 mm carries the
# wet D-socket above the cap). With cap total length 23 mm, the cap
# spans:
WET_CAP_EXT_FACE_Z = SHAFT_TOP_Z - 22.0            # cap top face (wet side)
WET_CAP_INT_FACE_Z = WET_CAP_EXT_FACE_Z - CAP_TOTAL_LEN

# Tube butts against the cap's interior shoulder (flange ↔ boss step at
# z = WET_CAP_EXT_FACE_Z - CAP_FLANGE_T). Boss extends CAP_BOSS_LEN
# into the tube. Tube length 240 mm.
WET_CAP_FLANGE_BOT_Z = WET_CAP_EXT_FACE_Z - CAP_FLANGE_T
TUBE_TOP_Z = WET_CAP_FLANGE_BOT_Z                  # tube butts against flange
TUBE_BOT_Z = TUBE_TOP_Z - TUBE_LEN_240
TUBE_CENTRE_Z = (TUBE_TOP_Z + TUBE_BOT_Z) / 2.0

# Dry end cap is the mirror at the bottom.
DRY_CAP_FLANGE_TOP_Z = TUBE_BOT_Z
DRY_CAP_EXT_FACE_Z = DRY_CAP_FLANGE_TOP_Z - CAP_FLANGE_T   # cap bottom (dry, exterior)
DRY_CAP_INT_FACE_Z = DRY_CAP_FLANGE_TOP_Z + CAP_BOSS_LEN   # interior shoulder inside the tube

# Cradle + spacer sit on top of the dry cap interior.
SPACER_T = 4.0
SPACER_BOT_Z = DRY_CAP_INT_FACE_Z
SPACER_TOP_Z = SPACER_BOT_Z + SPACER_T
CRADLE_BOT_Z = SPACER_TOP_Z


def _move_to_canister_axis(part, z_centre):
    """Move a part whose local origin is on its symmetry axis (z = 0) to
    sit centred on the canister axis at world z=z_centre."""
    return part.moved(Location((SHAFT_X_W, SHAFT_Y_W, z_centre)))


def _move_bottom_at(part, z_bot):
    """Move a part whose local origin is on its BOTTOM face to sit on the
    canister axis with that bottom face at world z=z_bot."""
    return part.moved(Location((SHAFT_X_W, SHAFT_Y_W, z_bot)))


def _make_gripper():
    """Build the existing gripper assembly and return it (already in world
    frame from gripper.py gen_step's +90X reorient)."""
    return G.gen_step()


def _select_servo():
    if SERVO == "XW540":     return dynamixel_xw540(), 33.5, 58.5, 45.9, 4.0, 19.0
    if SERVO == "XM540":     return dynamixel_xm540(), 33.5, 58.5, 44.0, 4.0, 19.0
    if SERVO == "STS3250":   return feetech_sts3250(), 20.0, 54.0, 47.0, 4.0, 14.0
    if SERVO == "STS3215":   return feetech_sts3215(), 20.0, 40.0, 40.5, 4.0, 14.0
    raise SystemExit(f"unknown servo {SERVO}")


def assemble_t2():
    """T2 lip-seal integrated assembly (the PRIMARY architecture).

    Anchor strategy: the shaft is a fixed-length goBILDA (50 mm). The wet
    D-socket and lip seal are fixed by the cap geometry. So the SERVO must
    sit at whatever Z makes its horn adapter mate the BOTTOM of the shaft.
    Everything else hangs from that constraint. The cable run from the
    servo's rear face down to the dry-side penetrators is the remaining
    free length (~150–200 mm of slack at T2 — generous).
    """
    parts = []

    # 1. The gripper (already in world frame, finger-up).
    parts.append(_make_gripper())

    # 2. Wet D-socket — receives the gripper coupler from above.
    socket = wet_d_socket()
    parts.append(_move_bottom_at(socket, WET_DSOCKET_BOT_Z))

    # 3. Ø8 × 50 mm goBILDA stainless adapter shaft.
    shaft_centre_z = (SHAFT_TOP_Z + SHAFT_BOT_Z) / 2.0
    parts.append(_move_to_canister_axis(gobilda_shaft_8x50(), shaft_centre_z))

    # 4. Lip seal in the wet end cap's centre bore.
    seal_z = WET_CAP_EXT_FACE_Z - CAP_FLANGE_T / 2.0
    parts.append(_move_to_canister_axis(lip_seal_8x14x4(), seal_z))

    # 5. Wet-side end cap.
    parts.append(_move_bottom_at(br_end_cap_wet_lipseal(), WET_CAP_EXT_FACE_Z))

    # 6. Acrylic tube.
    parts.append(_move_to_canister_axis(br_tube_3in_240(), TUBE_CENTRE_Z))

    # 7. Dry end cap (4 × M10), origin flipped so exterior face points -Z.
    dry_cap = br_end_cap_dry_4xm10()
    dry_cap = dry_cap.moved(Location((0, 0, 0), (1, 0, 0), 180))
    parts.append(_move_bottom_at(dry_cap, DRY_CAP_EXT_FACE_Z))

    # 8. WetLink penetrators + plugs on the dry cap.
    PCD = 60.0
    pen_pos = [(math.radians(45),     wetlink_penetrator()),
               (math.radians(135),    wetlink_penetrator(cable_l=60.0)),
               (math.radians(225),    wetlink_blank_m10()),
               (math.radians(315),    wetlink_blank_m10())]
    for ang, part in pen_pos:
        cx = SHAFT_X_W + PCD / 2 * math.cos(ang)
        cy = SHAFT_Y_W + PCD / 2 * math.sin(ang)
        part_flipped = part.moved(Location((0, 0, 0), (1, 0, 0), 180))
        parts.append(part_flipped.moved(Location((cx, cy, DRY_CAP_EXT_FACE_Z))))

    # 9. Servo + horn-adapter + cradle — anchored to the SHAFT BOTTOM.
    # The horn adapter's top engages the shaft bottom by SHAFT_ENGAGE mm
    # (the press-fit bore depth in printed_adapters.py is 10 mm).
    servo_part, sw, sl, sh, horn_h, horn_od = _select_servo()
    SHAFT_ENGAGE = 10.0
    HORN_ADAPTER_T = 12.0

    horn_adapter_top_z = SHAFT_BOT_Z + SHAFT_ENGAGE       # 10 mm of shaft inside adapter
    horn_adapter_bot_z = horn_adapter_top_z - HORN_ADAPTER_T
    servo_horn_top_z = horn_adapter_bot_z                  # adapter sits ON the horn
    servo_body_top_z = servo_horn_top_z - horn_h
    servo_bot_z = servo_body_top_z - sh
    cradle_bot_z = servo_bot_z - 6.0                       # 6 mm cradle floor below servo
    cradle_top_z = cradle_bot_z + (sh + horn_h + 6.0)      # matches servo_cradle h calc

    # Connectivity assertions — the real check (advisor's call): mating, not just fit.
    assert abs(horn_adapter_top_z - SHAFT_BOT_Z - SHAFT_ENGAGE) < 0.01, (
        f"shaft bottom {SHAFT_BOT_Z:.2f} does not engage horn adapter "
        f"top {horn_adapter_top_z:.2f}")
    assert WET_CAP_INT_FACE_Z - cradle_top_z >= 0.5, (
        f"cradle top {cradle_top_z:.2f} too close to / inside wet cap "
        f"interior {WET_CAP_INT_FACE_Z:.2f}")
    assert cradle_bot_z - DRY_CAP_INT_FACE_Z > 5.0, (
        f"cradle bottom {cradle_bot_z:.2f} penetrates / touches dry cap "
        f"interior {DRY_CAP_INT_FACE_Z:.2f}")

    parts.append(_move_bottom_at(
        servo_cradle(servo_w=sw, servo_l=sl, servo_h=sh, horn_oh=horn_h),
        cradle_bot_z))
    parts.append(_move_bottom_at(servo_part, servo_bot_z))
    parts.append(_move_bottom_at(
        servo_horn_adapter(horn_od=horn_od), horn_adapter_bot_z))

    cable_run_mm = cradle_bot_z - DRY_CAP_INT_FACE_Z
    cap_top_clear = WET_CAP_INT_FACE_Z - cradle_top_z
    print(f"  shaft bot z         = {SHAFT_BOT_Z:.2f}")
    print(f"  horn adapter top z  = {horn_adapter_top_z:.2f}  (engages 10 mm of shaft)")
    print(f"  servo body bot z    = {servo_bot_z:.2f}")
    print(f"  cradle bot z        = {cradle_bot_z:.2f}")
    print(f"  wet cap clearance   = {cap_top_clear:.2f} mm (top side, ≥ 0.5)")
    print(f"  dry cap cable run   = {cable_run_mm:.2f} mm (bottom side, free cable space)")

    asm = Compound(label=f"gripper_canister_T2_{SERVO}", children=parts)
    return asm


def assemble_t3():
    """T3 magnetic-coupling integrated assembly (the FALLBACK)."""
    parts = []
    parts.append(_make_gripper())

    # T3 layout: NO shaft penetration. The wet-side end cap is REPLACED
    # by a thin printed barrier; the gripper's D-coupler is gripped by a
    # short stub-D-socket fused into the OUTER rotor on the wet side.
    #
    # Stack (top-down):
    #   gripper flange (z=-25)
    #   small air gap
    #   short wet D-socket (10 mm engagement) — fused to outer rotor
    #   outer rotor (PETG/PA12-GF carrier + N52 ring)        ~21 mm
    #   barrier (3 mm PETG/PA12-GF; this REPLACES the wet end cap)
    #   inner rotor (mirror of outer)                         ~21 mm
    #   stub coupler from inner rotor → servo horn
    #   servo cradle + servo + dry cap (as T2)

    # Short wet D-socket
    short_socket_top_z = FLANGE_BOT_Z - 2.0
    socket = wet_d_socket()
    parts.append(_move_bottom_at(socket, short_socket_top_z - 20.0))

    # Outer rotor (wet side); its bottom face sits just under the socket
    outer_rotor = n52_magnet_ring_80mm()
    outer_rotor = outer_rotor.moved(Location((0, 0, 0), (1, 0, 0), 180))  # flip pucks down
    outer_bot_z = short_socket_top_z - 20.0   # under the socket
    parts.append(_move_bottom_at(outer_rotor, outer_bot_z))

    # Barrier (thin printed PETG/PA12-GF replacing the wet end cap)
    barrier_t = 3.0
    barrier_z = outer_bot_z - 22.0    # pucks 15 mm + carrier 6 mm + 1 mm gap
    barrier = Cylinder(radius=TUBE_ID_3IN_ACR / 2 - 0.5, height=barrier_t).moved(
        Location((SHAFT_X_W, SHAFT_Y_W, barrier_z + barrier_t / 2)))
    barrier.color = Color(0.75, 0.55, 0.25, 0.85)   # PETG amber
    parts.append(barrier)

    # Inner rotor (dry side, inside canister); pucks face up
    inner_rotor = n52_magnet_ring_80mm()
    inner_top_z = barrier_z - 1.0     # 1 mm magnetic gap below barrier
    parts.append(_move_bottom_at(inner_rotor, inner_top_z - 21.0))

    # Tube spans from below the barrier down to the dry cap
    tube_top_z = barrier_z
    tube_bot_z = tube_top_z - TUBE_LEN_240
    tube_centre_z = (tube_top_z + tube_bot_z) / 2.0
    parts.append(_move_to_canister_axis(br_tube_3in_240(), tube_centre_z))

    # Dry cap
    dry_cap = br_end_cap_dry_4xm10()
    dry_cap = dry_cap.moved(Location((0, 0, 0), (1, 0, 0), 180))
    dry_cap_ext_z = tube_bot_z - CAP_FLANGE_T
    parts.append(_move_bottom_at(dry_cap, dry_cap_ext_z))

    # Penetrators (same as T2)
    PCD = 60.0
    pen_pos = [(math.radians(45),     wetlink_penetrator()),
               (math.radians(135),    wetlink_penetrator(cable_l=60.0)),
               (math.radians(225),    wetlink_blank_m10()),
               (math.radians(315),    wetlink_blank_m10())]
    for ang, part in pen_pos:
        cx = SHAFT_X_W + PCD / 2 * math.cos(ang)
        cy = SHAFT_Y_W + PCD / 2 * math.sin(ang)
        part_flipped = part.moved(Location((0, 0, 0), (1, 0, 0), 180))
        parts.append(part_flipped.moved(Location((cx, cy, dry_cap_ext_z))))

    # Servo + cradle (same as T2 but on the dry side of the inner rotor)
    servo_part, sw, sl, sh, horn_h, horn_od = _select_servo()
    spacer_bot_z = tube_bot_z + CAP_BOSS_LEN
    parts.append(_move_bottom_at(cradle_endcap_spacer(), spacer_bot_z))
    cradle_bot_z = spacer_bot_z + 4.0
    cradle = servo_cradle(servo_w=sw, servo_l=sl, servo_h=sh, horn_oh=horn_h)
    parts.append(_move_bottom_at(cradle, cradle_bot_z))
    servo_bot_z = cradle_bot_z + 6.0
    parts.append(_move_bottom_at(servo_part, servo_bot_z))
    horn_top_z = servo_bot_z + sh + horn_h
    parts.append(_move_bottom_at(servo_horn_adapter(horn_od=horn_od), horn_top_z))

    # The servo horn adapter on the dry side rigidly connects to the
    # INNER rotor (modelled here as the printed adapter ↔ inner rotor
    # being two stacked parts; in fab they're a single printed assembly).

    asm = Compound(label=f"gripper_canister_T3_{SERVO}", children=parts)
    return asm


def assemble_servo_choices():
    """Side-by-side display of all four servo options (no canister).
    Each servo is laid out along world X with a label-distance step."""
    parts = []
    parts.append(_make_gripper().moved(Location((-180, 0, 0))))
    for k, (lbl, fn, dx) in enumerate([
        ("XW540",   dynamixel_xw540, -60),
        ("XM540",   dynamixel_xm540,   0),
        ("STS3250", feetech_sts3250,  +60),
        ("STS3215", feetech_sts3215, +120),
    ]):
        parts.append(fn().moved(Location((dx, 0, 0))))
    return Compound(label="servo_lineup", children=parts)


def assemble_t2_xray():
    """T2 lip-seal assembly with the ACRYLIC TUBE OMITTED — the literal 'xray'
    view. Same coordinate frame, same parts, same connectivity asserts; just
    no opaque cylinder hiding the servo + shaft + lip seal.

    We override `br_tube_3in_240` in the assemble_t2 path by post-filtering
    the Compound. Simpler than splitting the assembly logic.
    """
    asm = assemble_t2()
    keep = [c for c in asm.children
            if not (isinstance(c, Compound) and "br_acrylic_tube_240" in (c.label or ""))]
    return Compound(label=asm.label + "_XRAY", children=keep)


_ASM = {"T2": assemble_t2,
        "T3": assemble_t3,
        "LINEUP": assemble_servo_choices,
        "T2_XRAY": assemble_t2_xray}


def gen_step():
    """Entry-point matching gripper.py — selects the variant from
    GRIPPER_CANISTER_VARIANT (T2 | T3 | LINEUP) and the servo from
    GRIPPER_CANISTER_SERVO. Returns one Compound usable directly by
    the repo's `step` CLI (which writes both .step and the Explorer
    GLB sidecar)."""
    return _ASM[VARIANT]()


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    asm = gen_step()
    if VARIANT == "LINEUP":
        out = os.path.join(OUT_DIR, "servo_lineup.step")
    else:
        out = os.path.join(OUT_DIR, f"system_assembly_{VARIANT}_{SERVO}.step")
    export_step(asm, out)
    print(f"wrote {out}")

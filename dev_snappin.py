"""
Dev harness for the 3D-printed SNAP PIN that replaces all metal pivot pins
in the gripper. Standalone (does NOT import gripper.py) but mirrors its
constants exactly so the pin is drop-in.

Run:
    source /home/andre/.cad-venv/bin/activate
    python dev_snappin.py
Produces dev_snappin.step + renders (iso + cut/side) for visual review.
"""

from __future__ import annotations

import math

from build123d import (
    Axis,
    Box,
    Color,
    Compound,
    Cylinder,
    Cone,
    Location,
    Plane,
    Pos,
    extrude,
    export_step,
    make_face,
    Polyline,
)

# ---- constants mirrored from gripper.py ----------------------------------
PIN_R = 2.3
PRINT_CLEAR = 0.25
AXLE_BORE_R = PIN_R + PRINT_CLEAR        # 2.55  (links/arms ride here)
MOUNT_HOLE_R = PIN_R + 0.15              # 2.45  (finger bores)
PIN_HEAD_R = 3.6
PIN_COLOR = Color(0.74, 0.76, 0.79)

# Z layers (authored frame, pins run along +Z = depth)
Z_CRANK0 = 1.0
T_CRANK = 5.0
Z_FOLLOW0 = 7.0
T_FOLLOW = 5.0
Z_FINGER0 = 13.0
T_FINGER = 10.0
BACK_BOSS_Z = (-2.0, 1.0)
COVER_BOSS_Z = (20.0, 22.0)

# =====================================================================
#  SNAP PIN  -- the deliverable
# =====================================================================
# Snap-pin geometry parameters (mm)
SNAP_HEAD_R = PIN_R + 1.6        # 3.9  flange that stops pull-through
SNAP_HEAD_T = 1.8                # flange thickness (sits OUTSIDE the near face)
SNAP_BARB_PROUD = 0.7            # lip sticks this far past PIN_R (-> r 3.0)
SNAP_BARB_LIP_T = 1.0            # axial length of the flat locking-lip face
SNAP_BARB_LEAD = 3.0            # length of the tapered lead-in cone
SNAP_TIP_R = 1.0               # rounded-ish flat at the very tip (printable)
SNAP_SLOT_W = 1.0               # split-slot width (lets the tip flex)
SNAP_SLOT_LEN = 7.0             # slot depth, measured back from the tip
SNAP_BARB_SEAT = 0.30          # catch face sits this far PAST the far face
                               #   (small gap = positive snap, no slop)


def snap_pin(p, z0, z1, head_at="z0", label="snap_pin", color=PIN_COLOR,
             shank_r=PIN_R):
    """A fully 3D-printed push-to-snap pivot pin (no fasteners).

    Built in the AUTHORED frame at XY point ``p=(x,y)``, running along +Z
    from ``z0`` to ``z1``.  One end is a HEAD flange (stops pull-through);
    the opposite end is a SPLIT, BARBED, compliant tip that squeezes going
    in and springs out PAST the far bore face to lock the pin in place.

    Axial layout (head end -> barb end):
      [ head flange ]  outside the near face
      [   shank     ]  z0..z1, fills the bore stack, UNBROKEN (bearing zone)
      [ lip catch   ]  flat back face seats just past the far face (+SEAT)
      [ lead-in cone]  cams the split fingers inward on insertion
    The cross slot + relief live entirely in the barb end, so the bearing
    length of the shank is solid.

    Parameters
    ----------
    p        : (x, y) pin centre.
    z0, z1   : axial span of the SHANK (z1 > z0) = the bore stack it fills.
    head_at  : "z0" -> head at the low-Z end, barb springs out beyond z1.
               "z1" -> head at the high-Z end, barb springs out beyond z0.
    shank_r  : pivot shank radius (default PIN_R).

    Returns a single build123d solid (.label/.color set).
    """
    x, y = p
    L = z1 - z0
    barb_max_r = shank_r + SNAP_BARB_PROUD          # lip outer radius (~3.0)

    # LOCAL frame: head face at local z=0, shank 0..L, barb beyond L.
    # Flip at the end if head_at == "z1".

    # --- head flange: OUTSIDE the near face (local z in [-SNAP_HEAD_T, 0]) ---
    # so it never intrudes into the bore. Top face flush with z0.
    head = Cylinder(radius=SNAP_HEAD_R, height=SNAP_HEAD_T).moved(
        Location((0, 0, -SNAP_HEAD_T / 2.0)))

    # --- shank: fills the bore stack, solid bearing surface 0..L ----------
    shank = Cylinder(radius=shank_r, height=L).moved(Location((0, 0, L / 2.0)))

    # --- barb beyond the far face (local z = L) ---------------------------
    #   lip back/catch face at L + SEAT (just past the far face),
    #   flat lip of length LIP_T, then a lead-in cone narrowing to the tip.
    lip_back_z = L + SNAP_BARB_SEAT
    lip_front_z = lip_back_z + SNAP_BARB_LIP_T
    tip_z = lip_front_z + SNAP_BARB_LEAD
    # short shank stub bridges z=L..lip_back_z so the catch is continuous
    stub = Cylinder(radius=shank_r, height=(lip_back_z - L) + 0.01).moved(
        Location((0, 0, (L + lip_back_z) / 2.0)))
    # locking lip: flat-backed cylinder (the BACK ring face is the catch)
    lip = Cylinder(radius=barb_max_r, height=SNAP_BARB_LIP_T).moved(
        Location((0, 0, (lip_back_z + lip_front_z) / 2.0)))
    # lead-in cone: base barb_max_r at lip_front -> small flat at tip
    lead = Cone(bottom_radius=barb_max_r, top_radius=SNAP_TIP_R,
                height=SNAP_BARB_LEAD).moved(
        Location((0, 0, (lip_front_z + tip_z) / 2.0)))

    body = head + shank + stub + lip + lead

    # --- split slot: '+' cross slot through the barb tip so the four
    # fingers flex inward as the lip is cammed through the bore. The slot is
    # confined to the BARB END: it starts at the tip and runs back only
    # SNAP_SLOT_LEN, with its root (and the relief bore) ABOVE z=L so the
    # bearing region of the shank (0..L) stays solid.
    slot_root_z = tip_z - SNAP_SLOT_LEN
    slot_root_z = max(slot_root_z, L + 0.6)   # never break the bearing shank
    slot_h = (tip_z - slot_root_z) + 1.0
    slot_zc = (slot_root_z + tip_z + 1.0) / 2.0
    slot_a = Box(SNAP_SLOT_W, 4 * barb_max_r, slot_h).moved(
        Location((0, 0, slot_zc)))
    slot_b = Box(4 * barb_max_r, SNAP_SLOT_W, slot_h).moved(
        Location((0, 0, slot_zc)))
    # relief bore at the slot root: rounds the hinge so fingers bend, not crack
    relief = Cylinder(radius=SNAP_SLOT_W * 0.7, height=SNAP_SLOT_W * 2).moved(
        Location((0, 0, slot_root_z)))
    body = body - slot_a - slot_b - relief

    # --- orient into the requested authored-frame span -------------------
    if head_at == "z0":
        body = body.moved(Location((0, 0, z0)))
    else:  # head_at == "z1": flip so head is at the high-Z end (barb below z0)
        body = body.moved(Location((0, 0, 0), (1, 0, 0), 180.0))
        body = body.moved(Location((0, 0, z1)))

    body = body.moved(Location((x, y, 0)))
    body.label = label
    body.color = color
    return body


# =====================================================================
#  Test bore block: a stack that mimics the real bores so we can SEE the
#  barb spring past the far face. Internal axle = two bosses (back + cover).
# =====================================================================
def bore_block(p, z0, z1, bore_r, far_face_z, thickness=3.0):
    """A pair of slab 'bosses' the pin passes through: a near boss at z0
    and a far boss whose OUTER face is at far_face_z (the barb must clear
    this face)."""
    x, y = p
    near = Box(14, 14, thickness).moved(Location((x, y, z0 + thickness / 2.0)))
    far = Box(14, 14, thickness).moved(
        Location((x, y, far_face_z - thickness / 2.0)))
    blk = near + far
    blk -= Cylinder(radius=bore_r, height=(z1 - z0) + 20).moved(
        Location((x, y, (z0 + z1) / 2.0)))
    blk.color = Color(0.4, 0.6, 0.85, 0.4)
    blk.label = "bore_block"
    return blk


def gen_step():
    parts = []

    # 1) internal axle pin (A_R/B_R/B_L): shank z -2..22 (back-wall boss ->
    #    cover-boss), head at z0 (back wall), barb springs out past z22.
    parts.append(snap_pin((0, 0), -2.0, 22.0, head_at="z0",
                          label="axle_internal", color=PIN_COLOR))

    # 2) finger pin (C/D): shank z 0..23 (crank layer -> finger top), head at
    #    z1 (visible cap above the finger), barb springs out below z0.
    parts.append(snap_pin((16, 0), 0.0, 23.0, head_at="z1",
                          label="finger_pin", color=Color(0.8, 0.55, 0.3)))

    # 3) a short pin variant for scale
    parts.append(snap_pin((32, 0), 7.0, 18.0, head_at="z0",
                          label="short_pin", color=Color(0.5, 0.8, 0.5)))

    # test bore block around the internal axle to prove the barb clears z22:
    # bore_r = AXLE_BORE_R (2.55); the lip (r~3.0) must protrude above z22.
    parts.append(bore_block((0, 0), -2.0, 22.0, AXLE_BORE_R, far_face_z=22.0))

    asm = Compound(label="snap_pins_dev", children=parts)
    return asm


if __name__ == "__main__":
    asm = gen_step()
    export_step(asm, "dev_snappin.step")
    print("wrote dev_snappin.step")
    # quick volume sanity per child
    for c in asm.children:
        try:
            print(f"  {c.label:18s} vol={c.volume:9.2f} mm^3")
        except Exception as e:
            print(f"  {c.label:18s} ERR {e}")

    # ---- numeric snap geometry check (internal axle, z -2..22) ----
    barb_max_r = PIN_R + SNAP_BARB_PROUD
    print("\nsnap geometry check:")
    print(f"  shank R          = {PIN_R:.2f}  (bore AXLE={AXLE_BORE_R:.2f}, "
          f"MOUNT={MOUNT_HOLE_R:.2f}) -> radial clearance "
          f"{AXLE_BORE_R - PIN_R:.2f}/{MOUNT_HOLE_R - PIN_R:.2f}")
    print(f"  barb lip R       = {barb_max_r:.2f}  > bore "
          f"{AXLE_BORE_R:.2f} by {barb_max_r - AXLE_BORE_R:.2f} (catch)")
    print(f"  finger squeeze   = {barb_max_r - AXLE_BORE_R:.2f} mm radial "
          f"(each finger flexes in this far to pass)")
    z1 = 22.0
    print(f"  lip catch face   z = {z1 + SNAP_BARB_SEAT:.2f}  (far face "
          f"z={z1:.2f}, seats +{SNAP_BARB_SEAT:.2f})")
    tip_z = z1 + SNAP_BARB_SEAT + SNAP_BARB_LIP_T + SNAP_BARB_LEAD
    print(f"  barb tip         z = {tip_z:.2f}")
    print(f"  slot width {SNAP_SLOT_W:.2f}  slot depth {SNAP_SLOT_LEN:.2f}  "
          f"(confined to barb end, bearing shank solid)")
    # confirm each pin is a single solid
    for c in asm.children:
        if c.label == "bore_block":
            continue
        n = len(c.solids())
        print(f"  {c.label:18s} solids={n} "
              f"{'OK (single solid)' if n == 1 else 'WARN multi-body'}")

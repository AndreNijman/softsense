"""
Geared four-bar parallel-splay gripper — single-DOF motion model.

Coordinate convention
---------------------
  X : horizontal, jaw open/close direction (right = +X)
  Y : vertical, toward the fingertips (up = +Y)
  Z : depth / out of the gripper plane = the common revolute & gear axis,
      also the extrusion axis.

Mechanism (one DOF)
-------------------
Two equal SECTOR GEARS mesh each other on the centerline (X=0). The LEFT
gear is driven by the input SHAFT (coaxial with the left crank pivot A_L);
the mesh forces the right gear to counter-rotate, so both fingers move as a
perfect mirror pair from a single shaft. (The drive is therefore off-centre
at A_L, not in the middle of the plate.)

Each sector gear is the CRANK of a NON-parallelogram FOUR-BAR linkage:
    A  : crank (gear) pivot, fixed on the base   -> C : crank-coupler pin
    B  : follower pivot,      fixed on the base   -> D : follower-coupler pin
    C->D is the coupler; the FINGER is rigid with the coupler CD.
Link lengths were chosen by a design-space search so the finger both
translates apart and rotates ~18 deg OUTWARD as it opens (funnel mouth),
staying well clear of any four-bar dead-point in range.

Drive parameter
---------------
  OPEN_NORM in [0, 1]   0 = closed (jaws together), 1 = fully open.
Read from the GRIPPER_OPEN env var so poses can be swept without editing
source. Everything else is derived from the kinematics.
"""

from __future__ import annotations

import math
import os

from build123d import (
    Axis,
    Box,
    Color,
    Compound,
    Cylinder,
    GeomType,
    Location,
    Plane,
    Polyline,
    Pos,
    Rotation,
    chamfer,
    extrude,
    fillet,
    make_face,
)

# --------------------------------------------------------------------------
# Drive parameter
# --------------------------------------------------------------------------
def _env_float(var, default, lo, hi):
    """Read a float from env var `var`, clamp to [lo, hi]. On a non-numeric
    value warn and fall back to `default` instead of crashing the build."""
    try:
        return max(lo, min(hi, float(os.environ.get(var, str(default)))))
    except ValueError:
        import warnings
        warnings.warn(f"{var}={os.environ.get(var)!r} not a float; using {default}")
        return default


OPEN_NORM = _env_float("GRIPPER_OPEN", 0.5, 0.0, 1.0)

# Finger size scale factor (GRIPPER_FINGER_SCALE env var). Scales the FINGER
# blade in-plane (length, width, tip) only; the mount interface (pin bores,
# C/D spacing), wall thickness, clearances and grip-tooth size stay FIXED so
# the fingers still bolt onto the linkage and stay printable at any scale.
FINGER_SCALE = _env_float("GRIPPER_FINGER_SCALE", 1.0, 0.6, 2.5)

# --------------------------------------------------------------------------
# GLOBAL SELF-SIMILAR SCALE (GRIPPER_SCALE env var). Multiplies EVERY linear
# design dimension below -- lengths, radii, thicknesses, positions, walls,
# gear pitch radii / tooth heights / face widths -- so the WHOLE gripper grows
# geometrically (true mechanical similitude), NOT the old blade-only FINGER_SCALE.
# This is the fix flagged in fea/SCALABILITY.md: scaling the blade alone left the
# walls fixed (relatively thinner -> floppy >1.1x); scaling self-similarly keeps
# the wall/blade ratio constant so a 1.5x / 2x finger stays as stiff as the 1x.
#
# DELIBERATELY HELD (NOT scaled by SCALE) -- these are NOT part-size functions:
#   * print/tolerance process constants (PRINT_CLEAR, DFM_EDGE, CROWN_MESH_CLEAR,
#     SNAP_CB_* clearances, SNAP_GAP/CLEAR, the running-fit gaps): set by the
#     0.4 mm FDM nozzle, not the part. Pattern: scale the NOMINAL at its
#     definition (e.g. PIN_R*=SCALE) and leave the additive clearance literal,
#     so AXLE_BORE_R = PIN_R + PRINT_CLEAR holds the gap at every scale.
#   * gear/rib COUNTS (GEAR_TEETH, CROWN_TEETH, PINION_TEETH, FR_N_RIBS): fixed
#     counts + scaled radii => the gear MODULE scales and the mesh RATIO is intact.
#   * ANGLES (THETA_CLOSED, OPEN_TRAVEL, *_DEG, slants): similitude preserves angles.
#   * FASTENER sizes (BOLT_R / tap / clearance): an M4 is M4 at any scale; only the
#     bolt-pattern POSITIONS scale. (Higher loads at >1x -> consider M5/M6 manually.)
#   * flood-hole RADII (AXLE_FLOOD_R; the drilled drains + cover vents were removed):
#     sized by absolute bubble/surface-tension + FDM floor physics, not part size.
#   * grip MICRO-TEXTURE (FR_GRIP_*): a LOCKED, separately-validated wet-grip optimum
#     whose drainage is set by water-film physics (absolute), not part size -> a
#     bigger finger simply carries MORE posts of the same size.
#   * finish chamfers/fillets (DFM_EDGE, CHAM_*, R_VERT, R_TOP, FR_*_FILLET/CHAMFER):
#     edge-break / anti-elephant-foot finishes; held (also keeps fillet ops robust).
# Note: the mounting flange + D-coupler DO scale (must transmit ~k^2 torque), so the
# separate motor/cad/adapters subsystem needs re-scaling downstream to re-mate.
SCALE = _env_float("GRIPPER_SCALE", 1.0, 0.5, 3.0)

# --------------------------------------------------------------------------
# Kinematic parameters (mm, deg)  -- locked
# --------------------------------------------------------------------------
R_GEAR = 12.0 * SCALE         # sector-gear pitch radius -> sets pivot spacing
PIVOT_SPACING = 2.0 * R_GEAR  # |A_L A_R| so the gears mesh on the centerline

A_R = (PIVOT_SPACING / 2.0, 0.0)     # crank / gear pivot  = (12, 0)
B_R = (26.0 * SCALE, 10.0 * SCALE)   # follower pivot, outboard & low

R_CRANK = 34.0 * SCALE    # |A->C|  crank (gear arm) length
R_FOLLOW = 32.0 * SCALE   # |B->D|  follower length
R_COUPLER = 20.0 * SCALE  # |C->D|  coupler length (finger base bracket span)

THETA_CLOSED = 102.0   # crank up & slightly inward: jaws nearly touch closed
                       # (was 104.0; lowered 2deg so the closed C/D mount pins
                       # sit far enough apart that the pin heads/shanks clear at
                       # open=0.0 -- base_gap 7.55 was < 2*SNAP_HEAD_R 7.80. The
                       # blade contact face is anchored to FR_CONTACT_OFFSET so
                       # grip closure is preserved.)
OPEN_TRAVEL = 46.0     # crank rotates this many deg from closed to full open

# --------------------------------------------------------------------------
# Geometry parameters (mm)
# --------------------------------------------------------------------------
# Z layers (back -> front) so moving parts never share a plane
T_CRANK = 5.0 * SCALE
Z_CRANK0 = 1.0 * SCALE                # crank + gear layer (Z 1..6)
T_FOLLOW = 5.5 * SCALE               # was 5.0: longer follower journal; its top now reaches
                                     # close under the finger so the D-pin barely cantilevers
Z_FOLLOW0 = 6.5 * SCALE              # was 7.0: follower Z 6.5..12 (0.5mm gap above the crank
                                     # layer; top just below the finger, no finger overlap)
T_FINGER = 10.0 * SCALE              # Fin Ray finger depth in Z (z 13..23)
Z_FINGER0 = 13.0 * SCALE              # finger layer
FINGER_THRUST_GAP = 0.12 * SCALE     # running gap between each C/D eye-journal-boss TOP (the
                                     # new under-finger thrust shoulder) and the finger bottom
                                     # -- collapses the old ~1mm finger axial float to a
                                     # running gap and squares the finger on both bosses
LINK_W = 7.0 * SCALE  # link bar half-lobe width
PIN_R = 2.3 * SCALE   # pivot pin radius
PIN_HEAD_R = 3.6 * SCALE  # socket-head cap radius
PIN_HEAD_T = 1.2 * SCALE  # cap height (sits ~flush in a counterbore)

# production / printability (FDM design-for-AM standards) -- HELD (process, not scaled)
PRINT_CLEAR = 0.3     # mating clearance per side (FDM standard ~0.3 mm)
PIN_FIT_CLEAR = 0.15  # fat finger-NECK fit per side in the LOCKED 2.6mm TPU finger bore
                      # (FP_NECK_R = MOUNT_HOLE_R - PIN_FIT_CLEAR). Bounded by the locked
                      # bore + FDM tolerance: it CANNOT go tighter (the neck must still enter
                      # the finger at +0.15 print oversize). HELD (process).
AXLE_FIT_CLEAR = 0.10  # TIGHTENED 0.15->0.10: the rigid four-bar axle running fit (gear/arm/
                      # follower on its PETG-on-PETG pivot pin). Halves the base-pivot lost
                      # motion (0.30->0.20mm diametral) at the A/B pivots that sit at the base
                      # of the 124mm tip lever, where slop is most amplified. The element bore
                      # carries this running clearance; the non-rotating pin's housing/cover
                      # holes reuse it (the pin is melt-riveted, so it doesn't run). HELD.
DFM_EDGE = 0.4        # universal edge-break chamfer: no sharp edges
AXLE_BORE_R = PIN_R + AXLE_FIT_CLEAR  # link/arm/gear runs on its axle pin: snug running fit
                                      # (scaled pin + held gap). NOTE: the FINGER bore stays
                                      # MOUNT_HOLE_R = PIN_R+PRINT_CLEAR (already-printed TPU).

# --------------------------------------------------------------------------
# RIGHT-ANGLE INPUT DRIVE (vertical input shaft + crown/pinion stage)
# --------------------------------------------------------------------------
# The proven four-bar + spur-mesh mechanism is UNCHANGED. To get the input
# shaft out the BOTTOM (world -Z after the +90X reorient = MODEL -Y) while the
# fingers stay UP, we add a 90deg gear stage at the LEFT crank gear A_L:
#   * a CROWN gear (radial face teeth) rigid on A_L's +Z gear face (axis MODEL-Z)
#   * a small spur INPUT PINION whose axis is MODEL -Y (-> world DOWN), meshing
#     the crown at its -Y azimuth, integral with the input shaft (one printed
#     part: pinion + journal + shaft + D-coupler).
# Like the simplified spur gears already in this model, this right-angle mesh is
# REPRESENTATIVE geometry (involute-free straight flanks, nominal pitch) meant
# to be coupon-tuned for backlash/contact on the target printer -- NOT a final
# tooth form. A_L keeps its spur rim teeth meshing A_R (drive is unbroken).
SHAFT_R = 4.0 * SCALE # vertical input-shaft radius


def _involute_tip_r(m, z, pa_deg, x, backlash, a_coef=1.0, b_coef=1.25,
                    tip_land_deg=2.0):
    """The actual (auto-truncated) involute tip radius -- the same number the gear
    generator below produces, but available up here at constant-definition time so
    the crown valley / pitch-tangency math keys off the REAL pinion tip, not the
    nominal addendum (a profile-shifted low-z pinion is tip-truncated, so its real
    tip is shorter than r_p + (1+x)*m)."""
    pa = math.radians(pa_deg)
    r_p = m * z / 2.0
    r_b = r_p * math.cos(pa)
    r_a = r_p + m * (a_coef + x)
    r_f = r_p - m * (b_coef - x)
    r_lo = max(r_b, r_f) + 1e-4
    s_p = m * (math.pi / 2.0 + 2.0 * x * math.tan(pa)) - backlash
    half_p = s_p / (2.0 * r_p)

    def off(r):
        ac = math.acos(min(1.0, r_b / r))
        return (half_p + (math.tan(pa) - pa)) - (math.tan(ac) - ac)

    tip_land = math.radians(tip_land_deg)
    if off(r_a) < tip_land:
        lo, hi = r_lo, r_a
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if off(mid) < tip_land:
                hi = mid
            else:
                lo = mid
        r_a = lo
    return r_a


# --- crown / face-gear stage geometry (genuine shallow face mesh) -----------
# This is a RADIAL-PINION FACE-GEAR mesh, NOT two interpenetrating bodies:
#   * the CROWN is a thin FACE RING on the A_L gear's +Z face. Its teeth are
#     short axial-proud blocks around the pitch circle CROWN_RC, pointing in +Z.
#   * the PINION (axis model-Y, pointing radially at the crown centre) sits
#     ABOVE the crown face at the crown's -Y azimuth (model-Y = -CROWN_RC). Its
#     pitch cylinder rolls on the crown pitch circle; only its BOTTOM TOOTH TIPS
#     dip ~one tooth-depth into the crown teeth. The pinion ROOT cylinder, hub
#     and shaft all clear the crown ring body and root.
# The disengagement direction is +Z (lift the pinion off the crown face): the
# tooth-tip overlap then collapses to ~0, proving this is a real tooth mesh and
# not buried bodies. The PINION is now a TRUE INVOLUTE (the conjugate master, see
# below); the CROWN stays representative proud radial blocks, sized + phase-locked
# to that involute pinion and kept block-form so the gear-FEA cantilever model
# (motor/scripts/gear_fea*.py) stays conservative. The pitch planes are made
# tangent (DRIVE_Z) so contact rolls at mid-tooth instead of tip-gouging.
CROWN_RC = 8.0 * SCALE  # crown-gear pitch radius on the A_L gear face (HELD: ratio + motor FEA)
CROWN_TEETH = 24      # crown face-tooth count (HELD -> ratio CROWN/PINION = 24/9 = 8/3 exact)
CROWN_TOOTH_H = 3.0 * SCALE  # crown tooth RADIAL band half-width about the pitch circle -- the
                      # load-bearing FACE WIDTH in bending (the gear-FEA lever, held). Crown ring
                      # outer = CROWN_RC + this = 11.0 < the involute gear tip 13.5 -> clears.
CROWN_FACE_H = 2.8 * SCALE  # crown tooth AXIAL proud height -- gear-FEA REFERENCE height
                      # (conservative; the actual meshing proud teeth are computed shorter from
                      # the real pinion so the crown tips clear the pinion root and the valley
                      # floor sits below the pinion tip -- a real face mesh, not buried bodies).
CROWN_MESH_CLEAR = 0.2  # radial mesh clearance crown<->pinion (TIGHTENED 0.4->0.2: the old 0.4
                      # was a loose graze that read as backlash; 0.2 is a snug printed face mesh).

# --- input PINION: now a TRUE INVOLUTE spur (the conjugate master of the face mesh) ---
# The old straight-flank pinion had ~0deg pressure angle at pitch -> non-conjugate; it
# tip-gouged then ran in a loose gap = the input-stage ripple, multiplied 8/3 downstream.
# Pitch radius PINION_RP and the 9T count are HELD, which keeps (a) the 8/3 ratio + motor
# T_safe/torque chain, and (b) one-piece-shaft installability -- the pinion tip stays < the
# journal bore so the shaft still drops in pinion-first through the journals (a bigger
# re-module would make the pinion wider than the bore and break that). The fix is the FORM.
PINION_RP = 3.0 * SCALE  # input-pinion pitch radius (HELD)
PINION_TEETH = 9      # pinion tooth count (HELD -> ratio CROWN/PINION = 24/9 = 8/3)
PINION_MODULE = 2.0 * PINION_RP / PINION_TEETH   # = 0.667*SCALE (pitch dia / teeth)
PINION_PA_DEG = 25.0  # involute pressure angle (no-undercut floor 11.2T; 9T needs a small shift)
PINION_X = 0.25       # profile shift to clear the 9T undercut (x_min ~ +0.20 at 25deg)
PINION_BACKLASH = 0.15  # total circular backlash (mm) -- printed-fit flank thinning, ratio held
PINION_PHASE_DEG = 360.0 / PINION_TEETH / 2.0    # = 20 -> a pinion VALLEY faces the crown tooth
                      # on the -Y mesh azimuth (EXPLICIT phase lock; mirrors the spur half_tooth
                      # trick instead of relying on the old accidental 270/15-deg interleave).
PINION_TIP = _involute_tip_r(PINION_MODULE, PINION_TEETH, PINION_PA_DEG,
                             PINION_X, PINION_BACKLASH)   # real (auto-truncated) tooth-tip radius
PINION_ROOT_R = PINION_RP - PINION_MODULE * (1.25 - PINION_X)   # involute root radius
PINION_TOOTH_H = PINION_TIP - PINION_ROOT_R      # involute whole depth (motor-FEA interface)
PINION_T = 8.0 * SCALE  # pinion thickness (face width) along its axis (model Y) -- strength lever
assert PINION_TIP < SHAFT_R + PRINT_CLEAR + 1e-9, \
    "pinion tip >= journal bore -> one-piece input shaft would no longer install pinion-first"
assert abs(CROWN_RC / PINION_RP - 8.0 / 3.0) < 1e-9, "right-angle ratio drifted off 8/3"

DRIVE_X = -A_R[0]                    # shaft/pinion model-X = A_L x = -12
# CROWN ring base sits ON the A_L gear's +Z top face, so it MUST track the gear thickness
# (Z_CRANK0 + T_CRANK) -- a literal would float if T_CRANK ever changes. PITCH-PLANE
# TANGENCY: set DRIVE_Z so the pinion pitch cylinder's bottom (DRIVE_Z - PINION_RP) lands on
# the crown pitch plane, with the (truncated) pinion tip clearing the gear face by a small
# valley standoff + CROWN_MESH_CLEAR. This rolls contact to mid-tooth instead of the old
# ~0.45-module tip/edge gouge.
CROWN_BASE_Z = Z_CRANK0 + T_CRANK                # crown ring base = A_L gear top face
CROWN_VALLEY_FLOOR = CROWN_BASE_Z + 0.3 * SCALE  # crown valley floor (just above the gear face)
DRIVE_Z = CROWN_VALLEY_FLOOR + PINION_TIP + CROWN_MESH_CLEAR   # == crown_pitch_Z + PINION_RP
CROWN_Z = (CROWN_BASE_Z, DRIVE_Z - PINION_ROOT_R - CROWN_MESH_CLEAR)  # ring base .. proud tooth top
# Pinion centred at the crown -Y azimuth (model-Y = -CROWN_RC), straddling it so the pinion
# face width sweeps the crown teeth at that azimuth.
PINION_YC = -CROWN_RC                 # pinion centre model-Y = -8 (the mesh azimuth)
PINION_Y = (PINION_YC - PINION_T / 2.0, PINION_YC + PINION_T / 2.0)  # -12 .. -4
SHAFT_R_BORE = SHAFT_R + PRINT_CLEAR  # journal-bore radius (running clearance)
# TWO JOURNAL BEARINGS along model -Y, now a CONTINUOUS running bore (no mid
# pocket -> one uninterrupted bearing length). Stack (model-Y, +Y up/cavity, -Y
# down/exit), bore radius SHAFT_R_BORE throughout:
#   UPPER bore : DRIVE_UBORE_Y  (in the boss)        -- alignment guide near pinion
#   MID  bore  : DRIVE_MBORE_Y  (straddles the cavity floor)
#   LOWER bore : DRIVE_LBORE_Y  (wall + flange)      -- the long load-bearing exit
DRIVE_UBORE_Y = (-15.5 * SCALE, -13.5 * SCALE)  # upper journal bore: len 2.0
DRIVE_MBORE_Y = (-18.0 * SCALE, -15.5 * SCALE)  # mid journal bore (straddles floor -17)
DRIVE_LBORE_Y = (-25.0 * SCALE, -18.0 * SCALE)  # lower journal bore: len 7.0
# AXIAL CAPTURE (revised so the one-piece shaft is actually INSTALLABLE). The old
# design trapped a mid-shaft COLLAR (OD > both bores) in a pocket -- geometrically
# captured but with NO assembly path: the collar could not pass either journal, so
# the part could never be fitted. The collar is GONE. The shaft is now a plain
# cylinder through the journals: everything from the pinion down is <= SHAFT_R <
# bore, so the part installs FROM BELOW (-Y) -- pinion-first up into the cavity
# (pinion tip < bore -> it passes the journals) until the bottom shoulder lands.
# Capture:
#   +Y push-in : the bottom SHOULDER (OD > bore) bottoms on the flange outer face.
#   -Y pull-out: the D-coupler is engaged in the actuator horn-adapter / wet D-socket
#                bolted under the flange -> geometric retention once the servo is on.
SHAFT_SHOULDER_R = SHAFT_R + 1.8 * SCALE  # bottom shoulder OD (> bore -> +Y push-in stop)
SHAFT_SHOULDER_T = 2.0 * SCALE       # shoulder axial length (model Y)
SHAFT_COUPLER_R = 5.0 * SCALE  # bottom coupler radius (D-profile for a servo/motor)
SHAFT_COUPLER_LEN = 12.0 * SCALE
SHAFT_DFLAT = 1.4 * SCALE  # D-flat depth on the coupler

# --- 3D-printed HEAT-STAKE (melt-rivet) pin geometry ------------------------
# Replaces BOTH the old barbed snap pins (which kept snapping -- the split
# cantilever broke instead of flexing) AND the loose axle dowels (which slid and
# wobbled out of their bores). Every pivot is now a plain printed JOURNAL pin
# retained by a SEPARATE printed CAP: the user slips the cap over the pin's
# protruding melt-STUD and fuses it with a soldering iron -> a thermal-rivet head
# wider than the bore. Retention is GEOMETRIC (a formed head larger than the
# hole), NOT an elastic snap (nothing flexes -> nothing breaks) and NOT a press
# fit (nothing relies on friction -> nothing slides out). The formed head is also
# creep-proof: it is a solid shape larger than the hole, not a held preload.
# PETG-HF for the pins AND the caps -- it mushrooms cleanly under a hot iron and
# resists creep at the loaded shank.
SNAP_HEAD_R = PIN_R + 1.6 * SCALE  # pre-formed flange (insertion stop / one axial stop)
SNAP_HEAD_T = 1.8 * SCALE          # flange thickness (sits OUTSIDE the near face)

# Melt-stud (on the pin) + cap (separate printed part melted onto the stud):
MELT_STUD_R     = 1.3 * SCALE  # reduced tip-stud the cap melts onto (also threads the
                               # back-wall flood hole on the axle pins)
MELT_STUD_PROUD = 1.0 * SCALE  # stud tip sits this far PAST the retaining face (inside the cap)
MELT_CAP_OR   = 2.6 * SCALE    # cap outer radius -- wider than every bore it retains so it
                               # cannot pull through (finger eye 1.60 -> 1.0 mm shoulder;
                               # axle flood hole 1.5 -> 1.1 mm shoulder)
MELT_CAP_H    = 2.6 * SCALE    # cap (cup) height
MELT_CAP_HOLE_R = MELT_STUD_R + 0.20   # blind-pocket radius: slip fit over the stud (1.5)
MELT_CAP_HOLE_H = 2.2 * SCALE          # blind-pocket depth (the cup swallows the stud; the
                                       # closed crown above it is the soldering-iron melt zone)
MELT_RECESS_R = MELT_CAP_OR + 0.30     # recess in the retaining face that nests + radially
                                       # confines the cap rim (creep-proof, ends ~flush)
MELT_RECESS_DEPTH = 1.0 * SCALE        # recess depth cut into the retaining face
# cap self-consistency (a future edit that breaks the rivet fails loudly here):
assert MELT_CAP_HOLE_R > MELT_STUD_R, "melt cap blind hole must clear the stud"
assert MELT_CAP_H - MELT_CAP_HOLE_H >= 0.3, "melt cap crown wall too thin to print/melt"
assert MELT_RECESS_R >= MELT_CAP_OR, "melt recess must nest the cap"

GEAR_TEETH = 16       # COUNT held (scaled radius + fixed count -> module scales, ratio intact)
# --- spur sector-gear TOOTH FORM (A_L <-> A_R sync mesh): now a TRUE INVOLUTE ---
# The old 4-point straight-flank trapezoid was non-conjugate (~0deg pressure angle at
# pitch) -> it tip-gouged then ran in a loose gap = the visible mesh ripple/rattle and
# the bulk of the "wonky/loose" feel (this is the prominent, on-centreline mesh). It is
# replaced by a sampled involute (involute_gear_points) with a designed printed
# backlash. Pitch radius R_GEAR and centre distance 2*R_GEAR are unchanged, so the 1:1
# synced mirror and the half-tooth interleave (gen_step) are preserved exactly.
GEAR_MODULE = 2.0 * R_GEAR / GEAR_TEETH   # = 1.5*SCALE  (pitch diameter / teeth)
GEAR_PA_DEG = 25.0        # involute pressure angle: 25deg drops the no-undercut floor to
                          # 11.2T so the 16T gear needs zero profile shift (held process)
GEAR_BACKLASH = 0.15      # total circular backlash (mm) removed as symmetric flank
                          # thinning -- a printed-fit allowance, ratio untouched (held)
GEAR_TIP_R = R_GEAR + GEAR_MODULE         # true involute tip radius (= 13.5 at SCALE 1;
                                          # was 0.45*GEAR_TOOTH_H -> 13.35). Used for the
                                          # crown-ring + journal-boss clearance gates.
GEAR_TOOTH_H = 3.0 * SCALE  # (legacy radial tooth height -- retained only where old
                            # clearance refs still read it; the involute uses GEAR_MODULE)
GEAR_SECTOR_DEG = 150.0   # gears are sectors, not full discs -- ANGLE held

# --- Fin Ray finger (TPU compliant jaw) parameters ---
FR_BRACKET_W = 13.0 * SCALE  # mounting-bracket eye diameter
FR_BLADE_LEN = 90.0 * SCALE  # contact beam length, base -> tip
FR_BASE_WIDTH = 22.0 * SCALE  # triangle base width in X
FR_CONTACT_OFFSET = 1.0 * SCALE  # contact face sits this far inboard of the centreline
FR_BASE_DROP = 9.0 * SCALE  # triangle base sits this far below the top pin
FR_WALL = 2.8 * SCALE  # beam / rib wall thickness (uniform default)
FR_TIP_WIDTH = 2.0 * SCALE  # blade width at the blunt tip (sharp compliant taper)
FR_N_RIBS = 14         # number of internal ribs (all same-direction slant) -- COUNT held
FR_RIB_SLANT_DEG = 38.0
FR_RIB_DIR = -1        # rib slant direction (+1 = up-toward-spine; -1 = reversed)
# Directional / graded wall thickness. None -> fall back to FR_WALL (the original
# uniform behaviour). Per-member walls + a sharp spine taper set the finger's
# compliance distribution.
# UNIVERSAL-FINGER FEA result (fea/UNIVERSAL_FINGER.md): tested across a battery of
# objects (small+large circles AND square blocks, several heights). The winner is a
# thin compliant CONTACT beam (1.2 mm) + a sharply tapered (FR_TIP_WIDTH 2) compliant
# SPINE (1.8 mm) + fine ribs (1.6 mm, 14 of them, reversed slant). It distributes
# pressure far more evenly than the old finger (circle pressure-CoV 0.8->0.35), wraps
# BOTH square sizes (88 deg, old finger wrapped only the one it was tuned for), and
# grips every size a consistent safe ~12 N (old finger swung 7x). Universal score
# 0.65 vs 0.56 (old). All walls >= the ~1.0 mm / 2.5-perimeter FDM-TPU floor.
# SELF-SIMILAR walls: these scale with SCALE (the SCALABILITY.md fix -- walls grow
# with the blade so the wall/blade ratio is constant and the big finger stays stiff).
FR_CONTACT_WALL = 1.2 * SCALE  # contact-beam wall (thin -> conforms, even pressure)
FR_CONTACT_WALL_TIP = 1.2 * SCALE  # contact-beam wall at tip
FR_SPINE_WALL = 1.8 * SCALE  # spine-beam wall at base
FR_SPINE_WALL_TIP = 1.8 * SCALE  # spine-beam wall at tip
FR_RIB_WALL = 1.6 * SCALE   # rib wall at base
FR_RIB_WALL_TIP = 1.6 * SCALE  # rib wall at tip
FR_INSET_BASE = 4.0 * SCALE  # solid floor across the bottom
FR_INSET_TIP = 3.0 * SCALE  # solid cap at the apex
MOUNT_HOLE_R = PIN_R + PRINT_CLEAR   # finger pin bore (FDM clearance)
# !!! FIXED GEOMETRY: the TPU fingers are ALREADY PRINTED. MOUNT_HOLE_R (r 2.6 at
# SCALE 1, a 10 mm-deep through-bore in stiff 100%-dense TPU) MUST NOT CHANGE -- the
# pin redesign below works WITHIN this bore, never against it. Do not "fix" wobble or
# the snap by re-boring the finger; fix it on the pin / the rigid arm+follower eyes.

# --------------------------------------------------------------------------
# FINGER PIVOT PINS (C, D) -- HEAT-STAKE redesign (2026-06). The barbed snap pin
# kept SNAPPING: the split cantilever broke instead of flexing (twice -- the
# 2026-06 "gentle-transit" barb was a partial fix that still failed in the
# field). It is replaced by a plain stepped JOURNAL pin + a melted cap. The two
# jobs the barb did badly are now separate rigid features:
#   * HEAD (pre-formed) seats on the finger TOP -- the clean visible far stop.
#   * FAT NECK runs a close fit in the FIXED 2.6 TPU finger bore + bridges the
#     support gap -> kills the pivot wobble (the part the 2026-06 pass got right;
#     it stays).
#   * SLIM LAND journals in the rigid arm/follower eye (PETG-on-PETG).
#   * a reduced MELT-STUD protrudes past the eye's exit (bottom) face; a separate
#     printed cap is slipped on and fused -> the geometric pull-out stop, formed
#     (not sprung) in rigid PETG so it cannot creep-relax OR break.
# The cap is melted at the arm/follower-eye BOTTOM, so {finger + crank-arm +
# follower + the two C/D pins + caps} is staked as a BENCH SUB-ASSEMBLY (both pin
# ends reachable) and then dropped into the housing -- see docs/ASSEMBLY.md.
# The already-printed TPU finger bore (MOUNT_HOLE_R) is NEVER touched.
FP_NECK_R = MOUNT_HOLE_R - PIN_FIT_CLEAR   # fat finger-bearing neck (2.45): close
                                           # running fit in the FIXED 2.6 finger bore
FP_ARM_BORE_R = 1.60 * SCALE   # rigid C/D eye bore: kept NARROW so the cap (MELT_CAP_OR)
                               # catches a fat ~1.0 mm pull-out shoulder around it
FP_ARM_LAND_R = FP_ARM_BORE_R - 0.075  # pin's snug journal land in the rigid eye (1.525):
                                       # tightened 0.10->0.075/side. With the new journal boss
                                       # the land is now long (L/D ~ 4 at C), so this fit + the
                                       # length together kill the finger out-of-plane tilt.
# the cap recess reuses link_bar's counterbore plumbing, cut into the eye exit face:
FP_CB_R = MELT_RECESS_R           # eye-exit recess radius that nests the cap (2.9)
FP_CB_DEPTH = MELT_RECESS_DEPTH   # recess depth (1.0)
FP_EYE_BOSS_R = MELT_RECESS_R + 1.0   # local boss so a >=1 mm confining ring survives (3.9)
# Hard guards, checked at the +/-0.15 design tolerance:
assert (FP_NECK_R + 0.15) <= MOUNT_HOLE_R + 1e-9, "fat neck won't pass the finger bore"
assert (MELT_STUD_R + 0.15) <= FP_ARM_BORE_R + 1e-9, "melt stud won't pass the rigid eye"
assert (MELT_CAP_OR - 0.15) - (FP_ARM_BORE_R + 0.15) >= 0.5 - 1e-9, \
    "melt cap would not catch a solid pull-out shoulder on the rigid arm/follower eye"

# --------------------------------------------------------------------------
# CROSS-PIN (cotter) retention for the AXLE pins -- tool-free, geometric, REMOVABLE
# alternative to the heat-stake melt cap (no soldering iron, no operator skill, no
# permanent weld). Each axle pin's protruding stud (behind the OPEN back wall) carries
# a TRANSVERSE cross-bore; a separate printed straight COTTER slips through it and
# reaches past the flood-hole rim on BOTH sides = a clevis-pin pull-out stop. Geometric:
# it CANNOT fracture like the barb (a solid pin -- nothing flexes) nor slide out like the
# loose dowel (a positive cross member, not friction). The cotter is radially confined in
# the back-face recess so it stays seated; pull it to service the joint.
# AXLE PINS ONLY: the back wall is open + accessible and the fixed pivot post is lightly
# loaded. The FINGER pins stay heat-stake -- their stud is smaller and grip-loaded, and
# the buried eye-bottom has no clean access -- per docs/PIN_RETENTION_ALTERNATIVES.md.
USE_CROSS_PIN   = True
XPIN_STUD_R     = 1.35 * SCALE   # protruding stud radius: passes the back flood hole (1.5) even
                                 # at +0.15 mm FDM oversize; still leaves a 0.75 mm cross-bore wall
XBORE_R         = 0.6 * SCALE    # cross-bore radius (1.2 mm dia) -> 0.8 mm wall each side
XCOTTER_R       = 0.5 * SCALE    # cotter shaft radius (1.0 mm dia) -> 0.1 mm slip in the bore
XCOTTER_PROUD   = 0.85 * SCALE   # cotter reaches this far past the stud on each side (the catch)
XCOTTER_LEN     = 2.0 * XPIN_STUD_R + 2.0 * XCOTTER_PROUD   # tip-to-tip (4.5 mm)
XRECESS_R       = XCOTTER_LEN / 2.0 + 0.3 * SCALE   # back-face recess radius confining the cotter
XRECESS_DEPTH   = 1.6 * SCALE    # recess depth into the back face (seats the cotter + the bore Z)
XBORE_FROM_FACE = XRECESS_DEPTH - XCOTTER_R - 0.1 * SCALE   # cross-bore centre this far in from the
                                 # retaining face -> the cotter's catch face sits ~0.1 mm below the
                                 # recess-floor shoulder (so pin axial play stays ~0.1 mm)
assert XPIN_STUD_R - XBORE_R >= 0.7 - 1e-9, "cross-bore wall too thin to print (<0.7 mm)"
assert XBORE_R - XCOTTER_R >= 0.08 - 1e-9, "cotter won't slip through the cross-bore"
assert XRECESS_DEPTH >= 2.0 * XCOTTER_R + 0.4 - 1e-9, "recess too shallow to seat the cotter"
# grip texture: CROSSHATCH micro-posts on the contact face (so objects don't slip).
# Optimised by a dedicated grip-texture FEA/swarm campaign (see grip/GRIP_TEXTURE.md):
# a square-post array out-drains and out-grips the old single-axis ridges on WET
# objects (the gripper runs underwater and as-printed TPU is slick), grips in two
# directions (M_worst 0.72 vs a ridge's 0.18), and tiles the blade perfectly. The
# crossing 0.54 mm channels squeeze the water film out (tyre-tread / tree-frog
# mechanism) and the post edges break the glossy printed-TPU skin. Conservative
# (>= 0.5 mm channel) variant: universal grip score 0.75 vs the smooth-face 0.25.
# Grip micro-texture SCALES self-similarly with the gripper (×SCALE). The wet-grip
# campaign found grip is grip-NEUTRAL above a ~0.3 mm channel (drainage saturates), and
# the scaled channels stay above that at every scale (0.54 -> 0.81 -> 1.08 mm), so scaling
# the cell is grip-safe (coarser channels drain at least as well) AND keeps the post COUNT
# constant -- holding it absolute quadrupled the post count at 2x and made the finger build
# ~10x slower. The closed-pose finger-finger gap also scales proportionally (no collision).
FR_GRIP_DEPTH = 0.6 * SCALE  # post height proud of the contact face (mm)
FR_GRIP_PITCH = 1.8 * SCALE  # post pitch along the blade length Y (mm); land = pitch-FLAT
FR_GRIP_Y0_FRAC = 0.15  # texture starts at this fraction of the blade length -- FRACTION held
FR_GRIP_Y1_FRAC = 0.95  # texture ends at this fraction of the blade length -- FRACTION held
FR_GRIP_ROOT_IN = 0.2 * SCALE  # post root sits this far INTO the body (fuses cleanly)
FR_GRIP_FLAT = 0.54 * SCALE  # channel width between posts along Y (mm) -> land 1.26 mm
FR_GRIP_CROSS = True    # crosshatch: chop the Y-ridges into posts with Z-channels
FR_GRIP_CROSS_PITCH = 1.8 * SCALE  # post pitch across the finger depth Z (mm)
FR_GRIP_CROSS_GAP = 0.54 * SCALE   # channel width between posts along Z (mm)
# print-friendly rounding (FDM TPU, prints flat on the z0 face)
FR_BASE_CHAMFER = 0.5    # bottom-edge (bed face) chamfer: kills elephant-foot
FR_CELL_FILLET = 0.8     # fillet radius on internal rib-cell / spar corners
FR_TIP_FILLET = 1.5      # round the blade tip apex
FR_GRIP_TIP_FLAT = 0.5 * SCALE  # half-width of the flat at each post tip (slight draft)

# --------------------------------------------------------------------------
# Colours (clean industrial: dark slate body, matte-black TPU jaws, steel)
# --------------------------------------------------------------------------
STEEL_L = Color(0.55, 0.58, 0.62)   # internal links / gears (hidden in housing)
STEEL_R = Color(0.58, 0.61, 0.65)
PIN_COLOR = Color(0.74, 0.76, 0.79)  # pivot pins (bright steel)
CAP_COLOR = Color(0.85, 0.55, 0.25)  # melt-on retaining caps (amber PETG -> visible)
DARK = Color(0.20, 0.21, 0.24)       # drive shaft
TPU = Color(0.12, 0.13, 0.15)        # Fin Ray fingers (matte black TPU)
ENC = Color(0.27, 0.29, 0.33)        # enclosure body (dark slate)


# ==========================================================================
# Kinematics  (verified: continuous branch, no dead-points, monotonic splay)
# ==========================================================================
def mirror_x(p):
    return (-p[0], p[1])


def circle_intersect_both(c0, r0, c1, r1):
    dx = c1[0] - c0[0]
    dy = c1[1] - c0[1]
    d = math.hypot(dx, dy)
    if d > r0 + r1 + 1e-9 or d < abs(r0 - r1) - 1e-9 or d == 0:
        raise ValueError(f"four-bar locks: d={d:.3f} r0={r0} r1={r1}")
    a = (r0 * r0 - r1 * r1 + d * d) / (2.0 * d)
    h = math.sqrt(max(0.0, r0 * r0 - a * a))
    xm = c0[0] + a * dx / d
    ym = c0[1] + a * dy / d
    px = -dy / d
    py = dx / d
    return [(xm + h * px, ym + h * py), (xm - h * px, ym - h * py)]


def _crank_point(open_norm):
    theta = math.radians(THETA_CLOSED - OPEN_TRAVEL * open_norm)
    return (A_R[0] + R_CRANK * math.cos(theta),
            A_R[1] + R_CRANK * math.sin(theta))


def crank_angle_deg(open_norm):
    return THETA_CLOSED - OPEN_TRAVEL * open_norm


def solve_side_right(open_norm):
    """Right-side joint world points + coupler angle. Integrates from the
    closed pose, choosing the continuous assembly branch each step."""
    C0 = _crank_point(0.0)
    d_par = (B_R[0] + (C0[0] - A_R[0]) * (R_FOLLOW / R_CRANK),
             B_R[1] + (C0[1] - A_R[1]) * (R_FOLLOW / R_CRANK))
    cands = circle_intersect_both(C0, R_COUPLER, B_R, R_FOLLOW)
    D = min(cands, key=lambda p: (p[0] - d_par[0]) ** 2 + (p[1] - d_par[1]) ** 2)
    C = C0
    if open_norm > 0.0:
        n = max(1, int(math.ceil(open_norm / 0.02)))
        for i in range(1, n + 1):
            o = open_norm * i / n
            C = _crank_point(o)
            cands = circle_intersect_both(C, R_COUPLER, B_R, R_FOLLOW)
            D = min(cands, key=lambda p: (p[0] - D[0]) ** 2 + (p[1] - D[1]) ** 2)
    coupler_ang = math.degrees(math.atan2(D[1] - C[1], D[0] - C[0]))
    return {"A": A_R, "B": B_R, "C": C, "D": D, "coupler_ang": coupler_ang}


def solve_side_left(open_norm):
    r = solve_side_right(open_norm)
    return {"A": mirror_x(r["A"]), "B": mirror_x(r["B"]),
            "C": mirror_x(r["C"]), "D": mirror_x(r["D"]),
            "coupler_ang": 180.0 - r["coupler_ang"]}


# ==========================================================================
# Geometry helpers
# ==========================================================================
def _ccw(pts):
    """Return pts wound CCW. Mirrored (left) parts produce CW polygons whose
    extruded solids have inverted orientation -> booleans silently fail to
    fuse. Normalising winding fixes both sides uniformly."""
    area = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return pts if area >= 0 else list(reversed(pts))


def _poly_solid(pts, z0, thickness):
    """Extrude a closed XY polygon (list of (x,y)) to a Z slab at z0."""
    face = make_face(Polyline(*_ccw(pts), close=True))
    sol = extrude(face, amount=thickness)
    return sol.moved(Location((0, 0, z0)))


def _inv(a):
    """Involute function inv(a) = tan(a) - a (radians)."""
    return math.tan(a) - a


def involute_gear_points(m, z, pa_deg=25.0, x=0.0, backlash=0.15,
                         a_coef=1.0, b_coef=1.25, n_inv=12, phase_deg=0.0,
                         n_root=3, tip_land_deg=2.0):
    """One closed CCW (x,y) loop for a TRUE INVOLUTE spur gear centred at origin,
    axis +Z -- a drop-in for the old 4-point straight-flank tooth (feed straight to
    _poly_solid(pts, z0, thickness), which re-winds CCW + bores + .moves).

        m         module (mm) = 2*pitch_radius/z   (spur: 2*R_GEAR/GEAR_TEETH=1.5)
        z         tooth count
        pa_deg    pressure angle (25deg: no-undercut floor 11.2T, so 16T needs no
                  shift and the profile-shifted 6T pinion clears undercut)
        x         profile shift coef (+ for low z to kill undercut)
        backlash  TOTAL circular backlash (mm) removed symmetrically off both flanks
                  as tooth-THINNING -- a fit allowance, NOT a centre-distance change,
                  so pitch radii and the ratio are untouched
        phase_deg tooth phase (pass the spur half_tooth=11.25 to the LEFT gear so the
                  pair interleaves; pass PINION_PHASE_DEG to the pinion)

    Each tooth is a monotone-polar sweep up the left involute flank, across the tip,
    down the right flank, then a rounded root land to the next tooth -> never
    self-intersects. A profile-shifted low-z tooth goes POINTED at full addendum, so
    the tip is auto-truncated to a `tip_land_deg` half-angle flat (binary search on
    r_a). Representative-but-real conjugate flanks: this is what makes the mesh roll
    smoothly with tight, even backlash instead of the old tip-gouge/loose-gap ripple.
    """
    pa = math.radians(pa_deg)
    r_p = m * z / 2.0                       # pitch radius
    r_b = r_p * math.cos(pa)                # base radius (involute starts here)
    r_a = r_p + m * (a_coef + x)            # addendum / tip radius
    r_f = r_p - m * (b_coef - x)            # dedendum / root radius
    r_lo = max(r_b, r_f) + 1e-4             # involute is undefined below the base circle
    s_p = m * (math.pi / 2.0 + 2.0 * x * math.tan(pa)) - backlash  # tooth thickness @ pitch
    half_p = s_p / (2.0 * r_p)              # half tooth thickness as an angle at pitch

    def off(r):                            # flank angular offset from the tooth centreline
        return (half_p + _inv(pa)) - _inv(math.acos(min(1.0, r_b / r)))

    # low-z auto tip-truncation: shrink r_a until the tip keeps a tip_land half-angle
    tip_land = math.radians(tip_land_deg)
    if off(r_a) < tip_land:
        lo, hi = r_lo, r_a
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if off(mid) < tip_land:
                hi = mid
            else:
                lo = mid
        r_a = lo
    assert r_a > r_lo + 1e-6 and off(r_lo) > 0.0, \
        f"involute tooth degenerate (m={m} z={z} x={x}): no positive-area flank"

    step = 2.0 * math.pi / z
    ph = math.radians(phase_deg)
    radii = [r_lo + (r_a - r_lo) * (i / (n_inv - 1)) for i in range(n_inv)]
    off_lo = off(r_lo)
    pts = []
    for k in range(z):
        c = ph + k * step
        if r_f < r_lo - 1e-3:               # radial stub down to the true root (left side)
            pts.append((r_f * math.cos(c - off_lo), r_f * math.sin(c - off_lo)))
        for r in radii:                     # LEFT flank: root -> tip
            a = c - off(r)
            pts.append((r * math.cos(a), r * math.sin(a)))
        for r in reversed(radii):           # RIGHT flank: tip -> root
            a = c + off(r)
            pts.append((r * math.cos(a), r * math.sin(a)))
        if r_f < r_lo - 1e-3:               # radial stub (right side)
            pts.append((r_f * math.cos(c + off_lo), r_f * math.sin(c + off_lo)))
        a_here, a_next = c + off_lo, (c + step) - off_lo   # rounded root arc to next tooth
        for j in range(1, n_root):
            t = j / n_root
            aa = a_here + (a_next - a_here) * t
            pts.append((r_f * math.cos(aa), r_f * math.sin(aa)))
    return pts


def _counterbore_cut(p, z_face, depth, into_plus_z, pocket_r):
    """Solid to subtract from a receiving eye so a MELT CAP nests in a recess cut
    into the eye's EXIT face. The bore is WIDENED to pocket_r over `depth` of the
    eye thickness measured from `z_face`. into_plus_z=True cuts upward into the
    eye (exit face is the eye bottom); False cuts downward. The remaining ring of
    eye material at radius pocket_r..outer (a) radially confines the cap so the
    rivet cannot creep out, and (b) the step where the bore narrows back to the
    pin bore is the rigid SHOULDER the cap rim bears on (the axial pull-out load)."""
    if into_plus_z:
        zc = z_face + depth / 2.0
    else:
        zc = z_face - depth / 2.0
    return Cylinder(radius=pocket_r, height=depth).moved(
        Location((p[0], p[1], zc)))


def link_bar(p0, p1, width, z0, thickness, label, color, counterbores=None,
             bore0_r=None, bore1_r=None, eye1_boss_top=None):
    """Rounded-end link bar from p0 to p1 (eyes at both ends). Each eye is bored
    at bore0_r (p0) / bore1_r (p1), defaulting to AXLE_BORE_R; a finger-pin eye
    passes bore=FP_ARM_BORE_R so the melt cap catches a fat shoulder around it.
    `counterbores` is an optional list of (point, z_face, depth, into_plus_z,
    pocket_r, boss_r) specs cut into the eye exit face to nest a melt cap
    (see _counterbore_cut); each gets a local boss_r boss so a solid confining
    ring + axial shoulder survives around the widened pocket.

    `eye1_boss_top` (Z, optional): grow an ANTI-WOBBLE JOURNAL BOSS upward off the
    bore1 (finger-pin) eye to this Z -- just under the finger -- so the slim pin LAND
    journals continuously from the arm body up to the finger instead of cantilevering
    across the empty gap (the old out-of-plane finger wobble). The boss TOP is the
    under-finger thrust shoulder (axial capture). It grows in build +Z -> supportless."""
    if bore0_r is None:
        bore0_r = AXLE_BORE_R
    if bore1_r is None:
        bore1_r = AXLE_BORE_R
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(dy, dx))
    # straight bar with circular eyes
    body = Box(L, width, thickness).moved(Location((L / 2.0, 0, 0)))
    eye0 = Cylinder(radius=width / 2.0, height=thickness)
    eye1 = Cylinder(radius=width / 2.0, height=thickness).moved(Location((L, 0, 0)))
    bar = body + eye0 + eye1
    bar = bar.moved(Location((0, 0, z0 + thickness / 2.0)))
    bar = bar.moved(Location((p0[0], p0[1], 0), (0, 0, 1), ang))
    # local bosses around counterbored eyes (so the pocket has a solid wall ring)
    if counterbores:
        for (cp, zf, depth, into_pz, pocket_r, boss_r) in counterbores:
            bar += Cylinder(radius=boss_r, height=thickness).moved(
                Location((cp[0], cp[1], z0 + thickness / 2.0)))
    # anti-wobble journal boss grown UP off the bore1 (finger) eye to just under the finger
    boss_top1 = None
    if eye1_boss_top is not None and eye1_boss_top > z0 + thickness + 0.2:
        boss_top1 = eye1_boss_top
        h = boss_top1 - (z0 + thickness)
        bar += Cylinder(radius=FP_EYE_BOSS_R, height=h).moved(
            Location((p1[0], p1[1], (z0 + thickness + boss_top1) / 2.0)))
    # bore the pin holes (per-eye fit radius); bore1 runs through any journal boss
    bar -= Cylinder(radius=bore0_r, height=thickness * 3).moved(
        Location((p0[0], p0[1], z0 + thickness / 2.0)))
    b1_lo = z0 - thickness
    b1_hi = (boss_top1 if boss_top1 is not None else z0 + thickness) + thickness
    bar -= Cylinder(radius=bore1_r, height=(b1_hi - b1_lo)).moved(
        Location((p1[0], p1[1], (b1_lo + b1_hi) / 2.0)))
    # cap-nesting recesses (the geometric melt-cap capture pockets)
    if counterbores:
        for (cp, zf, depth, into_pz, pocket_r, boss_r) in counterbores:
            bar -= _counterbore_cut(cp, zf, depth, into_pz, pocket_r)
    # DFM: break the top & bottom face edges (no sharp edges; bore lead-ins).
    # Use _safe_round so one unchamferable edge can't abort the whole bar.
    zf = bar.edges().group_by(Axis.Z)
    bar = _safe_round(bar, zf[0] + zf[-1], DFM_EDGE, chamfer)
    bar.label = label
    bar.color = color
    return bar


def gear(center, phase_deg, z0, thickness, label, color, bore=True):
    """A full toothed gear disc centred at `center`, axis Z. Pitch radius
    R_GEAR; with centres at +/-R_GEAR the pitch circles touch on the
    centreline so the pair meshes. `phase_deg` rotates the teeth (the right
    and left gears are offset half a tooth so the teeth interleave).
    `bore=False` leaves the hub solid (for a gear with an integral shaft)."""
    # TRUE INVOLUTE flanks (replaces the 4-point straight-flank trapezoid). phase_deg
    # carries the L/R half-tooth interleave from gen_step so the pair still meshes.
    pts = involute_gear_points(GEAR_MODULE, GEAR_TEETH, pa_deg=GEAR_PA_DEG,
                               x=0.0, backlash=GEAR_BACKLASH, phase_deg=phase_deg)
    sol = _poly_solid(pts, z0, thickness)
    if bore:
        sol -= Cylinder(radius=AXLE_BORE_R, height=thickness * 3).moved(
            Location((0, 0, z0 + thickness / 2.0)))
    sol = sol.moved(Location((center[0], center[1], 0)))
    sol.label = label
    sol.color = color
    return sol


def _crown_gear(center, z_lo, z_hi, label, color):
    """CROWN gear: a thin BASE RING at `center` (axis model-Z) carrying RADIAL FACE
    TEETH that stand PROUD in +Z -- axial blocks repeating around the pitch circle.
    It meshes a spur pinion whose axis is perpendicular (model -Y), giving the 90deg
    turn. Representative tooth form (coupon-tunable), like the spur gears in this
    model. The ring sits ON the A_L gear's +Z face (z_lo..) and fuses into it; its
    bore is left to drive_arm (it shares the A_L axle bore).

    NOTE: the base ring is only (thickness - CROWN_FACE_H) tall; the teeth stand
    CROWN_FACE_H PROUD above it with OPEN VALLEYS between them, so the input pinion's
    tips drop into real tooth gaps. (Previously the ring was built full-height and
    the teeth lived entirely inside it -> they added ~0 volume and the crown rendered
    as a smooth washer with nothing for the pinion to mesh.)"""
    ro = CROWN_RC + CROWN_TOOTH_H        # outer radius of the toothed band
    ri = CROWN_RC - CROWN_TOOTH_H        # inner radius of the toothed band
    # Tooth Z extents set from the PINION so the mesh is real but does not bind:
    #   valley floor sits CROWN_MESH_CLEAR below the pinion tip (the tip drops into
    #   the gap); tooth top sits CROWN_MESH_CLEAR below the pinion ROOT cylinder, so
    #   the proud crown tips clear the spinning pinion core (no interference bind).
    pin_tip_z = DRIVE_Z - PINION_TIP                            # real involute pinion tip
    pin_root_z = DRIVE_Z - PINION_ROOT_R                        # real involute pinion root
    valley_top = max(z_lo + 0.3, pin_tip_z - CROWN_MESH_CLEAR)   # base-ring top / floor
    tooth_top = pin_root_z - CROWN_MESH_CLEAR                    # proud tooth tip
    base_h = valley_top - z_lo
    ring = Cylinder(radius=ro, height=base_h).moved(
        Location((0, 0, z_lo + base_h / 2.0)))
    ring -= Cylinder(radius=ri, height=base_h * 3).moved(
        Location((0, 0, z_lo + base_h / 2.0)))
    # proud face teeth standing from the base-ring top (valley_top) up to tooth_top,
    # with OPEN valleys between them down to valley_top -> a real face mesh.
    step = 2 * math.pi / CROWN_TEETH
    crown = ring
    for k in range(CROWN_TEETH):
        c = k * step
        # wedge tooth between two radii, half a pitch wide
        pts = []
        for frac, r in ((-0.25, ri), (-0.12, ro), (0.12, ro), (0.25, ri)):
            aa = c + frac * step
            pts.append((r * math.cos(aa), r * math.sin(aa)))
        crown = crown + _poly_solid(pts, valley_top, tooth_top - valley_top)
    crown = crown.moved(Location((center[0], center[1], 0)))
    crown.label = label
    crown.color = color
    return crown


def drive_arm(A, C, spin_deg, z0, thickness, label, color, with_crown=False):
    """Input link = gear sector fused with the crank arm (one rigid part, so
    no gear-vs-crank clip). Pivots about A; the arm reaches the coupler pin C.
    Both sides now ride on a separate snap-pin axle (clearance bore at A).
    with_crown=True (LEFT side) fuses a CROWN gear onto the A_L gear's +Z face so
    the input pinion can drive it via the right-angle stage. The crown is rigid
    with the crank gear -> the proven spur mesh A_L<->A_R is unchanged."""
    g = gear(A, spin_deg, z0, thickness, label + "_gear", color, bore=True)
    # C-eye = the FINGER PIN's rigid catch: bore it NARROW (FP_ARM_BORE_R) and
    # recess the exit (bottom) face so the melted cap rim bears on a fat rigid
    # shoulder here (in rigid material), not against the TPU finger. A-eye keeps
    # the axle running fit.
    cb = [(C, z0, FP_CB_DEPTH, True, FP_CB_R, FP_EYE_BOSS_R)]
    arm = link_bar(A, C, LINK_W, z0, thickness, label + "_arm", color,
                   counterbores=cb, bore0_r=AXLE_BORE_R, bore1_r=FP_ARM_BORE_R,
                   eye1_boss_top=Z_FINGER0 - FINGER_THRUST_GAP)
    part = g + arm
    if with_crown:
        part += _crown_gear(A, CROWN_Z[0], CROWN_Z[1], label + "_crown", color)
    # clearance bore so the arm rides on its axle pin (re-cut after crown fuse)
    part -= Cylinder(radius=AXLE_BORE_R, height=thickness * 6 + 8).moved(
        Location((A[0], A[1], z0 + thickness / 2.0)))
    # Note: the arm portion already carries link_bar's 0.4 mm edge-break. The
    # gear-tooth flanks are deliberately left crisp -- they are functional
    # meshing surfaces (sealed inside the housing, printed in-plane so no
    # overhang), and rounding them would degrade tooth engagement.
    part = part.moved(Location((0, 0, 0)))   # already in world coords
    part.label = label
    part.color = color
    return part


def pin(p, label, visible):
    """Pivot pin. visible=True (finger pins C,D): reaches the finger layer with
    a steel cap, seen above the housing. visible=False (fixed pivots A,B):
    short internal axle, hidden inside the enclosure."""
    if visible:
        z0, z1 = Z_CRANK0 - 1.0, Z_FINGER0 + T_FINGER       # ~0 .. 23
        shaft = Cylinder(radius=PIN_R, height=(z1 - z0)).moved(
            Location((p[0], p[1], (z0 + z1) / 2.0)))
        head = Cylinder(radius=PIN_HEAD_R, height=PIN_HEAD_T).moved(
            Location((p[0], p[1], z1)))          # centred on finger top -> flush
        c = shaft + head
    else:
        z0, z1 = -2.0, 22.0   # full axle: back-wall boss -> front-cover boss
        c = Cylinder(radius=PIN_R, height=(z1 - z0)).moved(
            Location((p[0], p[1], (z0 + z1) / 2.0)))
    c.label = label
    c.color = PIN_COLOR
    return c


# Axle-pin LOCATING COLLAR ----------------------------------------------------
# The rotating elements (gear/arm at A, follower at B) rode on a bare PIN_R shank
# with ~12 mm of EMPTY pin above them, so they rocked and slid axially ("the
# elements slide up and down"). Fix: a fat collar on the pin in that empty space,
# just ABOVE each element. The element is then trapped between the back-boss face
# (below) and the collar (above) and can only spin, not slide. Feasible on a
# one-piece pin because the axle pin inserts stud-FIRST: the collar approaches
# from above and never has to pass through the element's bore.
AXLE_COLLAR_R = PIN_R + 0.75 * SCALE   # 3.05: > AXLE_BORE_R (2.40) -> a 0.65 mm up-stop shoulder
AXLE_COLLAR_GAP = 0.12 * SCALE         # TIGHTENED 0.25->0.12: a true running thrust clearance
                                       # above the element -- halves the residual axial shuffle
                                       # (it still spins free; a collar-root relief keeps the
                                       # flat printed thrust faces from print-welding/dragging)
assert AXLE_COLLAR_R > AXLE_BORE_R + 0.4, "axle collar too small to stop the element sliding up"


def axle_pin(p, head_inner_z, shank_end_z, stud_tip_z, elem_top_z,
             tip_z1=None, tip_r=None, xbore_z=None, label="axle_pin", color=PIN_COLOR):
    """Axle pivot pin (A/B) -- HEAT-STAKE, replaces the loose dowel that slid and
    wobbled out. Built directly in world coords at XY p. Inserted from the FRONT
    (open cavity), stud-first:
        SPIGOT (tip_r)       head-top .. tip_z1            -- reduced tip that threads
                                                             up into the cover-boss bore
                                                             = the located +Z end (kills
                                                             the cantilever wobble)
        HEAD  (SNAP_HEAD_R)  inner face at head_inner_z   -- seats under the cover
                                                             boss = the +Z axial stop
        SHANK (PIN_R)        head_inner_z .. shank_end_z   -- journals the gear/arm;
                                                             flat end bottoms on the
                                                             back-bore step
        COLLAR (AXLE_COLLAR_R) elem_top_z+gap .. head-0.5  -- fat band filling the empty
                                                             pin above the element so it
                                                             cannot slide/rock up
        MELT-STUD (MELT_STUD_R) shank_end_z .. stud_tip_z  -- threads the back-wall
                                                             flood hole and protrudes
                                                             past the exterior back face
    A separate cap is melted onto the stud from OUTSIDE the back wall -> the pin is
    riveted to the wall = a fixed pivot post the gear/arm runs on. The element is
    axially trapped between the back-boss face (below) and the collar (above), and
    the pin itself is now journaled at BOTH ends (back-wall bore + the SPIGOT in the
    cover-boss bore) so it no longer rocks. tip_z1=None omits the spigot."""
    x, y = p
    head = Cylinder(radius=SNAP_HEAD_R, height=SNAP_HEAD_T).moved(
        Location((x, y, head_inner_z + SNAP_HEAD_T / 2.0)))
    shank = Cylinder(radius=PIN_R, height=(head_inner_z - shank_end_z)).moved(
        Location((x, y, (head_inner_z + shank_end_z) / 2.0)))
    # CROSS-PIN: a fatter solid stud whose bottom sits one wall below the cross-bore.
    # HEAT-STAKE: the reduced melt-stud down to the passed tip. (xbore_z selects.)
    cross = USE_CROSS_PIN and xbore_z is not None
    stud_rad = XPIN_STUD_R if cross else MELT_STUD_R
    stud_bot = (xbore_z - XBORE_R - 0.6 * SCALE) if cross else stud_tip_z
    stud = Cylinder(radius=stud_rad, height=(shank_end_z - stud_bot)).moved(
        Location((x, y, (shank_end_z + stud_bot) / 2.0)))
    body = head + shank + stud
    # LOCATING SPIGOT: a reduced tip above the head that threads up into the
    # cover-boss bore so the pin is supported at BOTH ends instead of cantilevering
    # off the back wall. A lead-in chamfer (added to the rim list below) lets the
    # cover drop onto all four spigots as it snaps home.
    head_top_z = head_inner_z + SNAP_HEAD_T
    if tip_z1 is not None and tip_z1 > head_top_z + 0.3:
        spig_r = tip_r if tip_r is not None else PIN_R
        body = body + Cylinder(radius=spig_r, height=(tip_z1 - head_top_z)).moved(
            Location((x, y, (head_top_z + tip_z1) / 2.0)))
    # LOCATING COLLAR: fat band just above the element up toward the head, so the
    # element is trapped (back-boss face below + collar bottom above) and can no
    # longer slide or rock up the bare shank. Its bottom face is the running stop.
    c_lo = elem_top_z + AXLE_COLLAR_GAP
    c_hi = head_inner_z - 0.5
    if c_hi - c_lo > 0.6:
        body = body + Cylinder(radius=AXLE_COLLAR_R, height=(c_hi - c_lo)).moved(
            Location((x, y, (c_lo + c_hi) / 2.0)))
    # DFM: break the head rim, the stud tip, the collar TOP rim (its bottom stays
    # crisp -- it is the axial stop), and the SPIGOT tip (a lead-in for the cover).
    # Bearing surfaces stay crisp.
    rim = [e for e in body.edges().filter_by(GeomType.CIRCLE)
           if abs(e.center().Z - (head_inner_z + SNAP_HEAD_T)) < 0.2
           or abs(e.center().Z - stud_bot) < 0.2
           or abs(e.center().Z - c_hi) < 0.2
           or (tip_z1 is not None and abs(e.center().Z - tip_z1) < 0.2)]
    body = _safe_round(body, rim, min(DFM_EDGE, SNAP_HEAD_T * 0.5), chamfer)
    # CROSS-PIN: the TRANSVERSE cross-bore through the protruding stud (the cotter
    # rides this). Subtract last so the bore mouth stays crisp for the cotter slip-fit.
    if cross:
        body = body - Cylinder(radius=XBORE_R, height=4.0 * XPIN_STUD_R).moved(
            Location((x, y, xbore_z), (0, 1, 0), 90.0))
    body.label = label
    body.color = color
    return body


def melt_cap(p, z_face, label="melt_cap", color=CAP_COLOR):
    """Separate printed retaining cap (the SAME part for every pin -> qty 8). The
    user slips it over a pin's protruding melt-stud (open end toward the part) and
    fuses it with a soldering iron: the cup welds to the stud and forms a head
    wider than the bore = geometric, creep-proof retention (replaces the barb that
    broke and the dowel sandwich that slid). Built seated in the retaining-face
    recess: rim at z_face + MELT_RECESS_DEPTH, cup body extending -Z (outward,
    toward the iron). z_face is the eye-exit (bottom) face for finger pins, or the
    exterior back-wall face for axle pins."""
    x, y = p
    rim_z = z_face + MELT_RECESS_DEPTH
    cup = Cylinder(radius=MELT_CAP_OR, height=MELT_CAP_H).moved(
        Location((x, y, rim_z - MELT_CAP_H / 2.0)))        # rim (+Z top) at rim_z
    pocket = Cylinder(radius=MELT_CAP_HOLE_R, height=MELT_CAP_HOLE_H).moved(
        Location((x, y, rim_z - MELT_CAP_HOLE_H / 2.0)))   # blind, opens at the rim
    body = cup - pocket
    # break the exposed outer (-Z) rim; leave the pocket mouth crisp for the stud.
    outer = [e for e in body.edges().filter_by(GeomType.CIRCLE)
             if abs(e.center().Z - (rim_z - MELT_CAP_H)) < 0.25]
    body = _safe_round(body, outer, DFM_EDGE, chamfer)
    body.label = label
    body.color = color
    return body


def cotter(p, z_face, label="cotter", color=CAP_COLOR):
    """Separate printed straight COTTER (cross-pin) -- the CROSS-PIN retention's pull-out
    stop (the SAME part for every axle pin -> qty 4). It slips through the transverse
    cross-bore in the axle pin's protruding stud and reaches past the flood-hole rim on
    both sides = a geometric clevis-pin stop (no soldering iron; pull it to service). Built
    lying ACROSS the stud (axis = world X) at the cross-bore Z, sized + confined by the
    back-face recess so it cannot slide off the bore. z_face = the exterior back-wall face.
    Insert by tilting it into the recess and pushing it through the cross-bore."""
    x, y = p
    xbore_z = z_face + XBORE_FROM_FACE
    shaft = Cylinder(radius=XCOTTER_R, height=XCOTTER_LEN).moved(
        Location((x, y, xbore_z), (0, 1, 0), 90.0))   # stand the +Z cylinder along +X
    ends = list(shaft.edges().filter_by(GeomType.CIRCLE))   # break both end rims (lead-in)
    body = _safe_round(shaft, ends, min(DFM_EDGE, XCOTTER_R * 0.6), chamfer)
    body.label = label
    body.color = color
    return body


def finger_pin(p, eye_bottom_z, eye_top_z, finger_top_z, label="finger_pin",
               color=PIN_COLOR):
    """C/D finger pivot pin (printed, single piece) -- HEAT-STAKE. Built directly
    in world coords at XY p, axis +Z = toward the finger top. Profile, finger-top
    HEAD down to the melt-stud (top -> bottom in world +Z -> -Z):

        HEAD  (SNAP_HEAD_R)   at finger_top_z              -- seats on the finger top
        NECK  (FP_NECK_R, fat) eye_top_z .. finger_top_z   -- close fit in the FIXED
                                                              2.6 TPU finger bore +
                                                              bridges the support gap
                                                              (this kills the wobble)
        LAND  (FP_ARM_LAND_R, slim) recess_floor .. eye_top_z -- journals the rigid
                                                              arm/follower eye
        MELT-STUD (MELT_STUD_R) recess_floor .. eye_bottom_z - MELT_STUD_PROUD
                                                           -- protrudes past the eye
                                                              exit face for the cap

    The neck->land step seats on the rigid eye TOP face (a down-stop); the HEAD on
    the finger top is the visible far stop; a separate cap melted onto the stud at
    the eye BOTTOM is the pull-out stop. recess_floor = eye_bottom_z +
    MELT_RECESS_DEPTH (the cap recess occupies the bottom of the eye)."""
    x, y = p
    recess_floor = eye_bottom_z + MELT_RECESS_DEPTH
    head = Cylinder(radius=SNAP_HEAD_R, height=SNAP_HEAD_T).moved(
        Location((x, y, finger_top_z + SNAP_HEAD_T / 2.0)))   # seats ON the finger top
    neck = Cylinder(radius=FP_NECK_R, height=(finger_top_z - eye_top_z)).moved(
        Location((x, y, (eye_top_z + finger_top_z) / 2.0)))
    land = Cylinder(radius=FP_ARM_LAND_R, height=(eye_top_z - recess_floor) + 0.01).moved(
        Location((x, y, (recess_floor + eye_top_z) / 2.0)))
    stud_tip_z = eye_bottom_z - MELT_STUD_PROUD
    stud = Cylinder(radius=MELT_STUD_R, height=(recess_floor - stud_tip_z)).moved(
        Location((x, y, (recess_floor + stud_tip_z) / 2.0)))
    body = head + neck + land + stud
    # DFM: break the head rim and the stud tip; bearing surfaces stay crisp.
    rim = [e for e in body.edges().filter_by(GeomType.CIRCLE)
           if abs(e.center().Z - (finger_top_z + SNAP_HEAD_T)) < 0.2
           or abs(e.center().Z - stud_tip_z) < 0.2]
    body = _safe_round(body, rim, min(DFM_EDGE, SNAP_HEAD_T * 0.5), chamfer)
    body.label = label
    body.color = color
    return body


# --------------------------------------------------------------------------
# Fin Ray-style compliant finger (TPU) — defined in world @ CLOSED pose,
# then rigid-moved with the coupler. The triangular truss of same-direction
# slanted ribs makes the tip curl AROUND a grasped object.
# --------------------------------------------------------------------------
def _safe_round(part, edges, radius, op):
    """Robustly fillet/chamfer a set of edges. build123d's fillet/chamfer are
    free functions: op(edges, radius) -> NEW Part. They are fragile on complex
    booleans -- a bulk call fails if ANY edge is unroundable. Try bulk first;
    on failure fall back to per-edge, re-resolving each target by (center,
    length) against the live part. One bad edge can't abort the build."""
    if not edges:
        return part
    try:
        return op(edges, radius)
    except Exception:
        pass
    targets = [(e.center(), e.length) for e in edges]
    for (tc, tl) in targets:
        best, best_d = None, 0.5
        for e in part.edges():
            try:
                if abs(e.length - tl) > 0.4:
                    continue
                c = e.center()
                d = ((c.X - tc.X) ** 2 + (c.Y - tc.Y) ** 2 + (c.Z - tc.Z) ** 2) ** 0.5
                if d < best_d:
                    best_d, best = d, e
            except Exception:
                pass
        if best is None:
            continue
        try:
            part = op([best], radius)
        except Exception:
            pass
    return part


def finray_finger_closed(C0, D0, inner_dir, z0, thickness):
    """Fin Ray-style compliant finger as a build123d solid in world coords at
    the CLOSED pose. C0, D0 are the mounting-pin centres; the finger points
    +Y with its CONTACT face on the inner side (toward the centreline):
      inner_dir = -1 -> right finger (contact faces -X)
      inner_dir = +1 -> left finger  (contact faces +X)
    Mount holes (MOUNT_HOLE_R) at C0/D0; extruded in Z from z0.
    Print-friendly rounding (FDM TPU): base chamfer kills elephant-foot,
    internal rib-cell corners filleted (TPU stress relief), grip-tooth tips and
    blade apex rounded. 2.5D extrusion -> no Z-direction overhang added."""
    # finger-size scale: blade length/width/tip scale; mount, walls, grip-tooth
    # size and clearances stay fixed (so it still fits the linkage & prints).
    blade_len = FR_BLADE_LEN * FINGER_SCALE
    base_width = FR_BASE_WIDTH * FINGER_SCALE
    tip_width = FR_TIP_WIDTH * FINGER_SCALE

    contact_x = -inner_dir * FR_CONTACT_OFFSET
    spine_base_x = contact_x - inner_dir * base_width
    base_y = max(C0[1], D0[1]) - FR_BASE_DROP
    tip_y = base_y + blade_len
    into = -inner_dir                       # interior direction: contact -> spine

    p_base_spine = (spine_base_x, base_y)
    spine_tip_x = contact_x + into * tip_width         # blunt tip on spine side
    p_tip = (spine_tip_x, tip_y)

    def spine_x_at(yy):
        t = (yy - base_y) / (tip_y - base_y)
        return p_base_spine[0] + (p_tip[0] - p_base_spine[0]) * t

    # solid blade triangle: contact edge + slanting spine + blunt flat tip
    tri = [(contact_x, base_y), (spine_base_x, base_y),
           (spine_tip_x, tip_y), (contact_x, tip_y)]
    blade = _poly_solid(tri, z0, thickness)

    bracket = link_bar(C0, D0, FR_BRACKET_W, z0, thickness, "bracket", TPU)
    shell = blade + bracket

    # hollow it: subtract the inner cavity (leaves contact/spine/base/tip spars).
    # Wall thicknesses may grade base->tip (directional compliance). None -> FR_WALL,
    # which reproduces the original uniform quadrilateral cavity exactly.
    cwb = FR_CONTACT_WALL if FR_CONTACT_WALL is not None else FR_WALL
    cwt = FR_CONTACT_WALL_TIP if FR_CONTACT_WALL_TIP is not None else cwb
    swb = FR_SPINE_WALL if FR_SPINE_WALL is not None else FR_WALL
    swt = FR_SPINE_WALL_TIP if FR_SPINE_WALL_TIP is not None else swb

    def _frac(yy):
        return min(1.0, max(0.0, (yy - base_y) / (tip_y - base_y)))

    def cav_contact_x(yy):
        return contact_x + into * (cwb + (cwt - cwb) * _frac(yy))

    def cav_spine_x(yy):
        return spine_x_at(yy) - into * (swb + (swt - swb) * _frac(yy))

    def cav_w(yy):
        return (cav_spine_x(yy) - cav_contact_x(yy)) * into

    y_cav_lo = base_y + FR_INSET_BASE
    MIN_CAV_W = 2.0
    y_cav_hi = tip_y - FR_INSET_TIP
    while y_cav_hi > y_cav_lo and cav_w(y_cav_hi) < MIN_CAV_W:
        y_cav_hi -= 0.5
    # sample both cavity edges (a graded wall tapers smoothly; with uniform walls
    # the samples are collinear -> the same quadrilateral as before)
    nseg = 12
    ys = [y_cav_lo + (y_cav_hi - y_cav_lo) * i / nseg for i in range(nseg + 1)]
    cav_pts = ([(cav_contact_x(y), y) for y in ys] +
               [(cav_spine_x(y), y) for y in reversed(ys)])
    cavity = _poly_solid(cav_pts, z0 - 2.0, thickness + 4.0)
    finger = shell - cavity

    # add back the slanted parallel ribs (all same slant = Fin Ray signature).
    # Rib wall may grade base->tip (thinner ribs near tip = more compliant lattice).
    slant = math.radians(FR_RIB_SLANT_DEG)
    shear = FR_RIB_DIR * (math.cos(slant) / math.sin(slant)) * into
    rwb = FR_RIB_WALL if FR_RIB_WALL is not None else FR_WALL
    rwt = FR_RIB_WALL_TIP if FR_RIB_WALL_TIP is not None else rwb
    y_rib_lo = base_y + FR_INSET_BASE
    y_rib_hi = tip_y - FR_INSET_TIP
    pitch = (y_rib_hi - y_rib_lo) / FR_N_RIBS
    x_a = contact_x + into * 0.3
    ribs = []
    for i in range(FR_N_RIBS + 1):
        yc = y_rib_lo + i * pitch
        rw = rwb + (rwt - rwb) * _frac(yc)        # graded rib thickness
        half = rw / 2.0
        x_b = spine_x_at(yc) - into * (rw * 0.4)
        if (x_b - x_a) * into <= 2.0:
            continue
        quad = [(x_a, yc - half), (x_b, yc - half),
                (x_b + shear * rw, yc + half), (x_a + shear * rw, yc + half)]
        try:
            ribs.append(_poly_solid(quad, z0, thickness))
        except Exception:
            pass
    if ribs:
        ribs_all = ribs[0]
        for r in ribs[1:]:
            ribs_all = ribs_all + r
        finger = finger + (ribs_all & blade)        # trim rib ends to the blade

    # --- grip texture (CROSSHATCH micro-posts) ---
    # Step 1 builds Y-ridges (X-Y trapezoids extruded the full Z depth), exactly
    # as the legacy single-axis texture. Step 2 (FR_GRIP_CROSS) then cuts channels
    # that run along Y and repeat across Z, CHOPPING the ridges into a grid of
    # square posts -- the crosshatch winner from the grip-texture campaign. The two
    # channel families (0.54 mm wide) drain the water film in both directions; the
    # post edges grip in both directions and break the slick printed-TPU skin.
    # Roots sit FR_GRIP_ROOT_IN inside the spar so the posts fuse cleanly; tips stay
    # clear of the centreline at the closed pose (right finger: contact_x=+1.0,
    # tips at +1.0-0.6 = +0.4 -> 0.8 mm finger-finger gap).
    grip_root_x = contact_x + into * FR_GRIP_ROOT_IN
    grip_tip_x = contact_x - into * FR_GRIP_DEPTH
    gy0 = base_y + FR_GRIP_Y0_FRAC * blade_len
    gy1 = base_y + FR_GRIP_Y1_FRAC * blade_len
    n_teeth = max(1, int((gy1 - gy0) / FR_GRIP_PITCH))
    teeth = []
    for i in range(n_teeth):
        yb = gy0 + i * FR_GRIP_PITCH
        yflat = yb + FR_GRIP_FLAT
        ypeak = yb + 0.5 * (FR_GRIP_PITCH + FR_GRIP_FLAT)
        ytop = yb + FR_GRIP_PITCH
        # blunt the apex into a small flat (4-pt trapezoid, not a knife-edge)
        quad = [(grip_root_x, yflat),
                (grip_tip_x, ypeak - FR_GRIP_TIP_FLAT),
                (grip_tip_x, ypeak + FR_GRIP_TIP_FLAT),
                (grip_root_x, ytop)]
        try:
            teeth.append(_poly_solid(quad, z0, thickness))
        except Exception:
            pass
    if teeth:
        teeth_all = teeth[0]
        for t in teeth[1:]:
            teeth_all = teeth_all + t
        finger = finger + teeth_all

    # Step 2: chop the Y-ridges into a CROSSHATCH post grid by subtracting channels
    # that run along Y (blade length) and repeat across the finger depth Z. Each cut
    # removes only the proud material (tip -> contact face), leaving the fused root
    # base inside the body intact, so the posts stay anchored.
    if teeth and FR_GRIP_CROSS:
        xa, xb = sorted([grip_tip_x, contact_x])     # proud region spans face..tip
        xlo = xa - 0.4                               # start beyond the tip
        xhi = xb                                     # stop at the contact face plane
        xc, xw = 0.5 * (xlo + xhi), (xhi - xlo)
        yc, yw = 0.5 * (gy0 + gy1), (gy1 - gy0) + 2.0
        cutters = []
        z = z0 + (FR_GRIP_CROSS_PITCH - FR_GRIP_CROSS_GAP)   # first channel after a land
        while z < z0 + thickness:
            cutters.append(Box(xw, yw, FR_GRIP_CROSS_GAP).moved(
                Location((xc, yc, z + FR_GRIP_CROSS_GAP / 2.0))))
            z += FR_GRIP_CROSS_PITCH
        if cutters:
            comb = cutters[0]
            for c in cutters[1:]:
                comb = comb + c
            finger = finger - comb
    # --- end grip texture ---

    # Trim anything that crosses the centreline (just inboard of the tooth tips)
    # so the two opposing fingers can NEVER collide at the closed pose. This
    # clips the inboard side of the C bracket flat without touching the pin bore.
    tooth_tip_x = contact_x - into * FR_GRIP_DEPTH
    keep_x = tooth_tip_x - into * 0.1
    BIG = 600.0
    cut = Box(BIG, BIG, BIG).moved(
        Location((keep_x - into * BIG / 2.0,
                  base_y + blade_len / 2.0, z0 + thickness / 2.0)))
    finger -= cut

    for hp in (C0, D0):
        finger -= Cylinder(radius=MOUNT_HOLE_R, height=thickness * 3).moved(
            Location((hp[0], hp[1], z0 + thickness / 2.0)))

    # ---- print-friendly fillets & chamfers (applied last, after booleans) ----
    # Fillet internal rib-cell / spar-junction corners (where TPU cracks).
    cell_edges = []
    for e in finger.edges().filter_by(Axis.Z):
        try:
            if abs(e.length - thickness) > 0.25:
                continue
            c = e.center()
            yy = c.Y
            if not (y_cav_lo - 0.5 < yy < y_cav_hi + 0.5):
                continue
            xin = (c.X - cav_contact_x(yy)) * into
            xout = (cav_spine_x(yy) - c.X) * into
            if xin < -0.5 or xout < -0.5:
                continue
            if any(math.hypot(c.X - hp[0], c.Y - hp[1]) < MOUNT_HOLE_R + 0.6
                   for hp in (C0, D0)):
                continue
            cell_edges.append(e)
        except Exception:
            pass
    finger = _safe_round(finger, cell_edges, FR_CELL_FILLET, fillet)

    # Round the blade tip apex (two vertical edges at the blunt tip corners).
    tip_pts = [(contact_x, tip_y), (spine_tip_x, tip_y)]
    tip_edges = []
    for e in finger.edges().filter_by(Axis.Z):
        try:
            if abs(e.length - thickness) > 0.25:
                continue
            c = e.center()
            if any(math.hypot(c.X - px, c.Y - py) < 1.0 for (px, py) in tip_pts):
                tip_edges.append(e)
        except Exception:
            pass
    finger = _safe_round(finger, tip_edges, FR_TIP_FILLET, fillet)

    # Chamfer the bottom (bed) face edges at Z=z0 to kill elephant-foot.
    bottom_edges = []
    for e in finger.edges():
        try:
            if e.length < FR_BASE_CHAMFER * 1.5:
                continue
            if abs(e.center().Z - z0) < 1e-3:
                bottom_edges.append(e)
        except Exception:
            pass
    finger = _safe_round(finger, bottom_edges, FR_BASE_CHAMFER, chamfer)

    return finger


def finger(side_pose, ref_pose, inner_dir, color, label):
    f = finray_finger_closed(ref_pose["C"], ref_pose["D"], inner_dir,
                             Z_FINGER0, T_FINGER)
    C0 = ref_pose["C"]
    a0 = ref_pose["coupler_ang"]
    C1 = side_pose["C"]
    a1 = side_pose["coupler_ang"]
    loc = (Location((C1[0], C1[1], 0.0))
           * Location((0, 0, 0), (0, 0, 1), a1 - a0)
           * Location((-C0[0], -C0[1], 0.0)))
    f = f.moved(loc)
    f.label = label
    f.color = color
    return f


# --------------------------------------------------------------------------
# Enclosure (UNDERWATER / flooded gearbox housing) -- encloses gears, pivots
# & lower links; the four-bar arms emerge through two WIDENED top slots that
# clear the full arm sweep (no clipping); drive shaft exits the back-wall
# bore; back mounting flange with 4x M4 holes. The housing FLOODS and DRAINS
# through round through-holes (no trapped air -> no buoyancy / pressure
# problems). Slot x-ranges come from the measured link sweep at the top wall.
# --------------------------------------------------------------------------
ENC_X = (-48.0 * SCALE, 48.0 * SCALE)  # outer width
ENC_Y = (-20.0 * SCALE, 16.0 * SCALE)  # bottom -> top of top wall (top LOWERED to 16)
ENC_Z = (-6.0 * SCALE, 24.0 * SCALE)   # back -> front (back wall slimmed 10->4 mm: the old
                             # 10 mm back wall was legacy from the removed horizontal
                             # shaft; the vertical drive needs no depth there. Cuts
                             # the housing depth 36->30 mm for a slimmer profile. The
                             # stepped axle flood hole (nz0 = ENC_Z[0]-3) still exits.
WALL = 3.0 * SCALE
TOP_WALL_Y0 = 14.5 * SCALE   # inside face of the thin top wall (y 14.5..16)
CAV_X = (-45.0 * SCALE, 45.0 * SCALE)  # interior clear cavity (holds the mechanism)
CAV_Y = (-17.0 * SCALE, 14.5 * SCALE)
CAV_Z = (-2.0 * SCALE, 22.0 * SCALE)
SLOT_Z = (0.0, 22.0 * SCALE)  # slots cut the full cavity depth in Z
SLOT_R = (2.5 * SCALE, 41.0 * SCALE)  # right top slot x-span (WIDENED so arms clear)
SLOT_L = (-41.0 * SCALE, -2.5 * SCALE)  # left top slot x-span  (WIDENED so arms clear)
# --- VERTICAL input-shaft journals through the model -Y BOTTOM wall ---------
# World-down = model -Y. The shaft runs along model -Y at (x=DRIVE_X, z=DRIVE_Z),
# through the bottom wall (y in [-20,-17]), and exits into a bottom mounting
# flange + D-coupler. TWO journal bearings capture it:
#   UPPER journal: a boss standing UP (+Y) off the inside bottom-wall face into
#     the cavity, bored SHAFT_R_BORE; carries the load near the pinion.
#   LOWER journal: the bottom wall itself + the flange thickness, bored
#     SHAFT_R_BORE; the long exit bearing.
# The two bores are continuous (no mid pocket). Axial capture is at the ends: the
# bottom SHOULDER bottoms on the flange (+Y), the coupler-in-servo takes -Y.
# Upper journal boss: stand it up off the cavity floor toward the pinion, but cap
# its top so it CLEARS the A_L crank-gear teeth tips. With the pinion stage raised
# (PINION higher in -Y), the boss can no longer reach to 0.3 mm below the pinion --
# that would drive the boss radius into the gear teeth (radius R_GEAR+tip from A_L,
# i.e. straight down to model-Y = -(R_GEAR + 0.45*GEAR_TOOTH_H)). So cap the boss
# top at that gear-tip Y minus 0.3 mm running clearance. The shaft simply spans the
# short gap from the boss top up to the pinion (this upper boss is the alignment
# journal; the long lower bore carries the load).
_GEAR_TIP_Y = -GEAR_TIP_R            # -13.5: involute gear teeth reach this far down model-Y
DRIVE_BOSS_Y = (CAV_Y[0], min(PINION_Y[0] - 0.3, _GEAR_TIP_Y - 0.3))  # -17 .. -13.65
DRIVE_BOSS_R = SHAFT_R + 2.4 * SCALE         # boss OD -> >=2 mm wall around bore
BOT_FLANGE_Y = (-25.0 * SCALE, ENC_Y[0])    # bottom mounting flange: y -25 .. -20
BOT_FLANGE_X = ENC_X                          # flush with the body sides: the base is
                                             # a seamless continuation of the shell
                                             # (no tacked-on narrower lip, and no
                                             # downward side-overhang to support)
BOT_FLANGE_Z = (ENC_Z[0], 22.0 * SCALE)      # back flush with the body; front stops at
                                             # the cavity (front frame + cover above)
FLANGE_TY = (BOT_FLANGE_Y[1] - BOT_FLANGE_Y[0])   # flange thickness in Y (5)
BOLT_R = 2.25                # M4 clearance
# bolt holes on the bottom flange: a clean symmetric 4 at the flange corners, clear
# of the shaft exit (x=-12, z=10.52) and its lower bore (was an asymmetric 5 that
# read as random).
BOLT_XZ = [(-38.0 * SCALE, 2.0 * SCALE), (38.0 * SCALE, 2.0 * SCALE),
           (-38.0 * SCALE, 18.0 * SCALE), (38.0 * SCALE, 18.0 * SCALE)]
R_VERT = 6.0                 # vertical corner radius (4->6: rounder uprights read
                             # as a designed enclosure, not a brick; still clears the
                             # cavity wall at the slim back corners)
R_TOP = 2.0
CHAM_EDGE = 1.5              # break/finish chamfer for the body & base perimeter edges
CHAM_COVER = 1.2            # matching chamfer on the front-cover outer perimeter
                            # (shared edge language -> the body/cover seam reads as an
                            # intentional shadow line, not a parts mismatch)

# --- underwater drainage / flood holes ---
# The 12 drilled drains (8 bottom-flange + 4 side-wall, Ø5) were REMOVED (2026-06,
# cosmetic). The flood-vent sim showed flooding is never flow-limited: the kinematic
# openings alone (the two +Y top slots + the four snap-clip windows, which the code
# notes "also act as drains") purge the ~84 mL void in <1 s and equalise pressure
# (water is incompressible once flooded). Worst-case trapped-air pocket rises only
# from ~6 mL to ~14 mL (+4 g -> +10 g buoyancy, still under the +23 g near-neutral
# baseline). The melt-stud axle-flood holes (back wall) and the shaft journal remain
# as flood paths. Trade-off accepted by the user; see the flood-vent analysis.

# --- assembly split: open-front body + bolt-on front cover ---------------
COVER_COLOR = Color(0.33, 0.35, 0.40)   # cover: slightly lighter than ENC
FRONT_WALL_Z = (22.0 * SCALE, 24.0 * SCALE)  # old solid front wall, now removed
AXLE_PIVOTS = [A_R, B_R, mirror_x(B_R), mirror_x(A_R)]  # captured-axle pivots
# (A_L now rides on its OWN snap-pin axle too: the old integral input shaft is
#  gone -- A_L is driven by the crown gear, so it needs a normal pivot axle.)
AXLE_SCREW_R = AXLE_BORE_R              # snap-pin shank clearance (was M3)
BOSS_OD_R = AXLE_SCREW_R + 2.0 * SCALE  # axle boss OD -> 2 mm wall around bore (DFM min)
BACK_BOSS_Z = (-2.0 * SCALE, 1.0 * SCALE)  # back-wall boss into cavity (top = crank-layer floor)
# AXIAL DOWN-STOP per pivot. The crank/gear sits in the LOW Z layer (Z_CRANK0..), so it
# rests directly on the BACK_BOSS_Z[1]=1 boss top (trapped: boss below + collar above).
# The FOLLOWER sits in a HIGHER layer (Z_FOLLOW0=6.5..), so a boss capped at Z=1 left its
# bottom floating ~5.5 mm above any support -> it slid axially down the pin (the 2026-06
# collar pass only added the UP-stop and only the crank happened to land on the boss). Fix:
# give the B (follower) pivots a TALLER back-boss whose top is a DOWN THRUST SHOULDER just
# under the follower, so the follower is trapped boss-below + collar-above like the crank.
B_BOSS_TOP = Z_FOLLOW0 - AXLE_COLLAR_GAP   # follower down-stop top (running thrust gap) = 6.38
_B_PIVOTS = (B_R, mirror_x(B_R))           # the follower pivots (vs the A crank pivots)


def _back_boss_top(px, py):
    """Back-boss top Z for a pivot: tall (B_BOSS_TOP) at the follower pivots so the
    follower has a down thrust shoulder; the crank-layer default elsewhere."""
    return B_BOSS_TOP if (px, py) in _B_PIVOTS else BACK_BOSS_Z[1]


def _axle_back_boss(px, py):
    """Back-wall boss for one pivot. A (crank) pivots get a plain full cylinder capped at
    the crank-layer floor. B (follower) pivots get a full base (below the crank layer) plus
    a TALL D-SHAPED thrust stem that reaches up to a down-shoulder just under the follower:
    the crank arm sweeps the INBOARD side of B near full open (no radial room there -- it
    nearly touches the pin), so the stem is cut to the OUTBOARD ~180deg where B stays clear
    at every pose. The half-annulus thrust shoulder still traps the follower axially."""
    btop = _back_boss_top(px, py)
    if (px, py) not in _B_PIVOTS:
        return Cylinder(radius=BOSS_OD_R, height=(btop - BACK_BOSS_Z[0])).moved(
            Location((px, py, (BACK_BOSS_Z[0] + btop) / 2.0)))
    base = Cylinder(radius=BOSS_OD_R, height=(BACK_BOSS_Z[1] - BACK_BOSS_Z[0])).moved(
        Location((px, py, (BACK_BOSS_Z[0] + BACK_BOSS_Z[1]) / 2.0)))
    sh = btop - BACK_BOSS_Z[1]
    stem = Cylinder(radius=BOSS_OD_R, height=sh).moved(
        Location((px, py, (BACK_BOSS_Z[1] + btop) / 2.0)))
    # keep the OUTBOARD half: outboard = B - A (this pivot's crank centre), rotated ~45deg
    # away from the arm's up-sweep (measured clear-sector centre; CW on the right side).
    ax = math.copysign(A_R[0], px)
    keep = math.degrees(math.atan2(py - A_R[1], px - ax)) + (45.0 if px < 0 else -45.0)
    kx, ky = math.cos(math.radians(keep)), math.sin(math.radians(keep))
    L, margin = 4.0 * BOSS_OD_R, 0.4
    keephalf = Box(L, L, sh + 2.0).moved(
        Location((px + kx * (L / 2.0 + margin), py + ky * (L / 2.0 + margin),
                  (BACK_BOSS_Z[1] + btop) / 2.0), (0, 0, 1), keep))
    return base + (stem & keephalf)


COVER_BOSS_Z = (20.0 * SCALE, 22.0 * SCALE)  # cover inner-face boss into cavity
# --- axle pin HEAT-STAKE capture (replaces the old loose dowel sandwich) -----
# The plain dowel was meant to be trapped between the back boss and the cover boss,
# but the running-fit bores + the 0.20 mm seating gap left real slop -> it wobbled
# and slid out (worst before the cover was on). Now the axle pin is RIVETED to the
# back wall: a pre-formed HEAD seats just under the cover boss (the +Z stop) and a
# reduced MELT-STUD threads the back-wall flood hole and protrudes past the EXTERIOR
# back face, where a separate cap is melted on (the -Z stop). The gear/arm runs on
# the shank; the pin itself no longer moves -> no wobble, cannot fall out.
AXLE_DOWEL_CLR = 0.05                       # head-to-cover-boss seating gap: TIGHTENED 0.20->0.05.
                                            # The old 0.20 was below the printed segment-length
                                            # tolerance -> a fictional, ambiguous seat. 0.05 gives
                                            # ONE firm +Z datum (head under the cover boss); the
                                            # melt-rivet cap is the -Z datum; the spigot is now a
                                            # pure radial locator. So every pin lands at the same
                                            # Z and the assembly reads even.
AXLE_DOWEL_Z1 = COVER_BOSS_Z[0] - AXLE_DOWEL_CLR - SNAP_HEAD_T   # 18.0 (head inner face / shank top)
# The back axle bore is STEPPED: a wide (AXLE_SCREW_R) running bore from the cavity
# down to AXLE_STOP_Z, then a flood hole (AXLE_FLOOD_R) on through the back wall. The
# shank's flat end (r=PIN_R) is too wide for the flood hole, so it BOTTOMS on the
# rigid step (the insertion depth stop); the MELT-STUD (MELT_STUD_R < flood) then
# continues through the flood hole and out the back face. The hole still floods/drains.
AXLE_STOP_Z = 0.0                           # back-bore step (shank flat end bottoms here)
AXLE_FLOOD_R = 1.5                          # flood hole below the step; also the stud clearance
AXLE_DOWEL_Z0 = AXLE_STOP_Z                 # shank flat end seats on the step
# stud tip: ~0.2 mm shy of the cap-pocket bottom, the cap nested in the back-face recess.
AXLE_STUD_TIP_Z = ENC_Z[0] + MELT_RECESS_DEPTH - MELT_CAP_HOLE_H + 0.2   # ~ -7.0
assert (MELT_STUD_R + 0.15) <= AXLE_FLOOD_R + 1e-9, "melt stud won't pass the back flood hole"
assert (MELT_CAP_OR - 0.15) - (AXLE_FLOOD_R + 0.15) >= 0.5 - 1e-9, \
    "melt cap would not catch a solid shoulder on the exterior back face"
# CROSS-PIN cross-checks (now that AXLE_FLOOD_R is known):
assert (XPIN_STUD_R + 0.15) <= AXLE_FLOOD_R + 1e-9, "cross-pin stud won't pass the back flood hole"
assert (XCOTTER_LEN / 2.0) - AXLE_FLOOD_R >= 0.4 - 1e-9, \
    "cotter not wide enough to catch the flood-hole rim"
# (the old back-wall A_L shaft bore + plain-bushing seat -- SHAFT_C/SHAFT_BORE_R/
#  BUSH_* -- are REMOVED: A_L is now driven by the crown gear, not a coaxial
#  horizontal shaft; the vertical input shaft journals through the bottom wall.)
CORNER_XY = [(-43.0, -15.0), (43.0, -15.0), (-43.0, 13.0), (43.0, 13.0)]
CORNER_BOSS_R = 3.0                     # screw-boss outer radius
CORNER_TAP_R = 1.35                    # M3 tap (self-tap into body column)
CORNER_CLEAR_R = 1.7                   # M3 clearance hole in the cover
CORNER_BOSS_Z = (-2.0, 22.0)           # (legacy; replaced by snap clips)
COVER_Z = (22.0 * SCALE, 25.0 * SCALE)  # bolt-on cover plate

# --- axle-pin LOCATING SPIGOT (anti-wobble) ---------------------------------
# The pin used to be riveted ONLY at the back wall (stud + melt-cap + a short
# 2.5 mm shank journal); its HEAD just floated under the cover-boss face with a
# 0.20 mm gap and NO radial location -> the pin was a cantilever and its top
# rocked ("wobble"). Fix: a reduced TIP SPIGOT above the head that threads up
# into the cover-boss bore (the "proper mounting hole" on the cover side). The
# pin is now journaled at BOTH ends (back-wall bore + cover-boss bore) so it can
# no longer rock. The spigot also registers the cover onto all four pins as it
# snaps home. The cover-boss bore (AXLE_SCREW_R) is reused as the locating hole
# (0.15 mm running fit on the PIN_R spigot, same as the back journal); a short
# lead-in mouth lets the cover self-align onto the four spigots.
AXLE_TIP_R = PIN_R                          # spigot Ø = shank: runs in the AXLE_SCREW_R cover bore
AXLE_TIP_PROUD = 2.5 * SCALE                # spigot engages this far up into the cover-boss bore
AXLE_TIP_Z1 = COVER_BOSS_Z[0] + AXLE_TIP_PROUD   # spigot tip Z (drainage gap left above it)
AXLE_TIP_LEADIN = 0.5                       # cover-boss mouth lead-in (radial widen, held literal)
assert AXLE_TIP_R < AXLE_SCREW_R, "axle locating spigot must clear the cover-boss bore"
assert AXLE_TIP_Z1 < COVER_Z[1] - (CHAM_COVER + 0.8), \
    "axle spigot would punch the cover skin / leave no drainage above the tip"

# --- front-cover vent holes: REMOVED (2026-06, cosmetic) ---
# The 3 × Ø1.8 cover vents were the underwater audit-C-6 fix for trapped air in the
# FRONT-UP attitude (air pools against the cover where the mechanism blocks it from
# reaching the top slots). Removing them gives up that front-up venting: only safe if
# the gripper is not operated front-up. Trade-off explicitly accepted by the user.

# --- snap-clip front cover (tool-free, zero hardware) -------------------
SNAP_Y = [-9.0 * SCALE, 7.0 * SCALE]  # clip y-centres on each side wall
SNAP_ARM_W = 9.0 * SCALE             # clip width along Y (flexing beam width)
SNAP_ARM_T = 2.0 * SCALE             # arm radial thickness (X) -- thinned 2.8->2.0:
                                     # cuts outward protrusion 3.2->2.4 mm (sleeker,
                                     # blade-like tab) AND, since bending strain is
                                     # LINEAR in thickness (eps = 3*t*d/(2*L^2)),
                                     # DROPS worst-tight strain 1.90%->1.36% -- more
                                     # PA12-GF margin, not less. Cost is a softer
                                     # click (stiffness ~ t^3); retention is the
                                     # geometric hook-in-window, not the spring.
SNAP_TIP_CHAM = 1.0                  # bevel on the free-tip proud edge so the tab
                                     # reads as an intentional blade, not a nub
                                     # (free tip = print-top -> self-supporting)
SNAP_GAP = 0.40                      # standoff: arm inner face clears wall outer
SNAP_Z0 = 1.5 * SCALE                # arm root region near hook (back end)
                                     # (was 6.5; lowered to lengthen the clip
                                     # cantilever -> bending strain drops from
                                     # ~3.32% to ~1.9% so PA12-GF (brittle,
                                     # allowable ~1.5-2.0%) survives insertion.)
SNAP_HOOK_Z = (7.0 * SCALE, 10.0 * SCALE)  # hook lip Z-span
SNAP_HOOK_ENGAGE = 1.5 * SCALE       # how far the hook reaches inward into wall
SNAP_CLEAR = 0.35                    # engagement clearance -- HELD (process)
SNAP_LEADIN = 2.0 * SCALE            # lead-in chamfer run at the hook back end
SNAP_WIN_Z = (SNAP_HOOK_Z[0] - SNAP_CLEAR, SNAP_HOOK_Z[1] + SNAP_CLEAR)
SNAP_WIN_DY = 11.0 * SCALE           # window length along Y (clears arm width)
_WALL_OUT_R = ENC_X[1]               # +48 outer face of right wall
_ARM_IN_R = _WALL_OUT_R + SNAP_GAP   # inner face of the arm
_ARM_OUT_R = _ARM_IN_R + SNAP_ARM_T  # outer face of the arm
_HOOK_TIP_R = ENC_X[1] - SNAP_HOOK_ENGAGE   # hook tip (clear of cavity)
SNAP_ARM_Z1 = COVER_Z[0] + 1.0       # arm overlaps INTO the cover so it fuses

# --- build-time strain gate (brittle PA12-GF cantilever, weakest across-layer) ---
# Insertion bends the arm out by the hook engagement (+FDM tolerance worst-tight).
# eps = 3*t*delta / (2*L^2), L = free cantilever length (root at cover -> free tip).
# Fail the build LOUD if the worst-tight strain leaves the conservative allowable, so
# nobody can re-thicken the arm or shorten it past the brittle limit unnoticed.
SNAP_FREE_L = COVER_Z[0] - SNAP_Z0                       # 20.5 mm cantilever length
SNAP_DELTA_WORST = SNAP_HOOK_ENGAGE + 2 * 0.2           # 1.9 mm (eng + FDM each side)
SNAP_STRAIN_WORST = 3 * SNAP_ARM_T * SNAP_DELTA_WORST / (2 * SNAP_FREE_L ** 2)
SNAP_STRAIN_ALLOW = 0.015                               # 1.5% conservative PA12-GF gate
assert SNAP_STRAIN_WORST < SNAP_STRAIN_ALLOW, (
    f"snap-clip worst-tight bending strain {SNAP_STRAIN_WORST*100:.2f}% exceeds the "
    f"{SNAP_STRAIN_ALLOW*100:.1f}% PA12-GF gate (t={SNAP_ARM_T}, L={SNAP_FREE_L}); "
    f"thin the arm or lengthen it (lower SNAP_Z0) -- never reduce SNAP_HOOK_ENGAGE")


def _box_between(x0, x1, y0, y1, z0, z1):
    return Box(x1 - x0, y1 - y0, z1 - z0).moved(
        Location(((x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0)))


def _one_clip(side, yc):
    """One cantilever snap clip (arm + hook) for one side & y-centre, world
    coords. side=+1 right wall (hook points -X inward); side=-1 mirror."""
    s = side
    arm_in = s * _ARM_IN_R
    arm_out = s * _ARM_OUT_R
    x_lo, x_hi = sorted((arm_in, arm_out))
    arm = _box_between(x_lo, x_hi, yc - SNAP_ARM_W / 2.0, yc + SNAP_ARM_W / 2.0,
                       SNAP_Z0, COVER_Z[0])
    root_in = s * ENC_X[1]
    rx_lo, rx_hi = sorted((root_in, arm_out))
    root = _box_between(rx_lo, rx_hi, yc - SNAP_ARM_W / 2.0, yc + SNAP_ARM_W / 2.0,
                        COVER_Z[0] - 3.0, SNAP_ARM_Z1)
    arm = arm + root
    tip = s * _HOOK_TIP_R
    hx_lo, hx_hi = sorted((arm_in, tip))
    hook = _box_between(hx_lo, hx_hi, yc - SNAP_ARM_W / 2.0, yc + SNAP_ARM_W / 2.0,
                        SNAP_HOOK_Z[0], SNAP_HOOK_Z[1])
    clip = arm + hook
    try:
        edges = clip.edges().filter_by(Axis.Y).group_by(Axis.Z)[0]
        inner_edge = sorted(edges, key=lambda e: abs(e.center().X))[0]
        clip = fillet([inner_edge], radius=min(SNAP_LEADIN, SNAP_HOOK_ENGAGE - 0.2))
    except Exception:
        pass
    # free-tip bevel on the OUTER (proud) edge -> the tab end reads as a blade, not a
    # nub. Free tip = lowest Z = print-top in the flipped cover orientation, so the
    # bevel is self-supporting. OUTER edge only: never the high-stress root (rounding
    # the root would shorten the effective cantilever and raise strain). Fail loud.
    tip_ys = clip.edges().filter_by(Axis.Y).group_by(Axis.Z)[0]
    outer_edge = sorted(tip_ys, key=lambda e: abs(e.center().X))[-1]
    clip = chamfer([outer_edge], length=SNAP_TIP_CHAM)
    clip.label = f"snap_clip_{'R' if side > 0 else 'L'}_{yc:+.0f}"
    clip.color = COVER_COLOR
    return clip


def _all_snap_clips():
    return [_one_clip(side, yc) for side in (+1, -1) for yc in SNAP_Y]


def build_enclosure():
    """Hollow flooded gearbox housing (underwater), SPLIT for assembly: open
    front so the mechanism drops in; the snap-clip cover supports the far axle
    ends. Keeps the cavity, two top slots, captured-axle bosses, and the back-wall
    axle-flood holes. The old back-wall A_L horizontal shaft bore + plain-bushing seat are
    GONE; instead the BOTTOM (model -Y) wall carries the two-bearing journal for
    the VERTICAL input shaft (upper boss bore + flange exit bore) and the mounting
    flange + bolt holes moved to the bottom around that exit. The 4 corner screw
    bosses are REPLACED by snap-clip catch windows in the long side walls (zero
    hardware, tool-free cover)."""
    body = _box_between(*ENC_X, *ENC_Y, *ENC_Z)
    body = fillet(body.edges().filter_by(Axis.Y), radius=R_VERT)
    top_edges = body.edges().filter_by(Axis.Y, reverse=True).group_by(Axis.Y)[-1]
    body = fillet(top_edges, radius=R_TOP)
    body -= _box_between(*CAV_X, *CAV_Y, *CAV_Z)
    body -= _box_between(CAV_X[0], CAV_X[1], CAV_Y[0], CAV_Y[1],
                         FRONT_WALL_Z[0] - 0.5, ENC_Z[1] + 1.0)
    # Remove the FULL front-wall perimeter rim (Z COVER_Z[0]..front), not just the
    # cavity footprint. The "old solid front wall, now removed" cut above only spans
    # the cavity, so a 2 mm perimeter rim (Z 22..24) was left behind and the bolt-on
    # cover plate (Z 22..25) interpenetrated it by ~740 mm^3 -> the cover could not
    # seat. Cutting the rim down to COVER_Z[0] makes that face the cover's flush -Z
    # seating datum. (Bottoms at exactly COVER_Z[0], not -0.5, so there is no gap.)
    body -= _box_between(ENC_X[0] - 1.0, ENC_X[1] + 1.0, ENC_Y[0] - 1.0, ENC_Y[1] + 1.0,
                         COVER_Z[0], ENC_Z[1] + 1.0)
    body -= _box_between(SLOT_R[0], SLOT_R[1], TOP_WALL_Y0 - 1.0, ENC_Y[1] + 1.0,
                         SLOT_Z[0] - 0.5, SLOT_Z[1] + 0.5)
    body -= _box_between(SLOT_L[0], SLOT_L[1], TOP_WALL_Y0 - 1.0, ENC_Y[1] + 1.0,
                         SLOT_Z[0] - 0.5, SLOT_Z[1] + 0.5)
    # BOTTOM mounting flange (model -Y wall = world DOWN), around the shaft exit
    flange = _box_between(*BOT_FLANGE_X, *BOT_FLANGE_Y, *BOT_FLANGE_Z)
    flange = fillet(flange.edges().filter_by(Axis.Y), radius=R_VERT)
    body += flange

    # finishing chamfer around the base (bed-face) perimeter -> a crisp, polished
    # bottom edge instead of a raw 90 deg corner. Lowest-Y edge group; fail loud if
    # the selection is empty (a silent miss is how rough edges have shipped before).
    base_edges = [e for e in body.edges().group_by(Axis.Y)[0] if e.length > 1.0]
    if not base_edges:
        raise RuntimeError("base perimeter chamfer: no bottom edges selected")
    body = chamfer(base_edges, length=CHAM_EDGE)

    for (px, py) in AXLE_PIVOTS:
        body += _axle_back_boss(px, py)   # A: full cylinder; B: full base + D-shaped thrust stem

    # UPPER journal boss: stands +Y off the inside bottom-wall face into the cavity
    # at the shaft XY (model x=DRIVE_X, z=DRIVE_Z). Axis = model Y.
    body += Cylinder(radius=DRIVE_BOSS_R, height=(DRIVE_BOSS_Y[1] - DRIVE_BOSS_Y[0])).moved(
        Location((DRIVE_X, (DRIVE_BOSS_Y[0] + DRIVE_BOSS_Y[1]) / 2.0, DRIVE_Z),
                 (1, 0, 0), -90.0))

    for e in body.edges().filter_by(GeomType.CIRCLE):
        if abs(e.center().Z - CAV_Z[0]) < 0.05:
            try:
                body = fillet([e], radius=0.8)
            except Exception:
                pass

    # VERTICAL input-shaft journal: one CONTINUOUS running bore (SHAFT_R_BORE) from
    # the flange bottom up through the wall and the boss, all at (x=DRIVE_X,
    # z=DRIVE_Z), axis model -Y. No pocket (the old collar is gone): an uninterrupted
    # bearing the shaft slides up into from below.
    def _bore_y(r, y0, y1):
        return Cylinder(radius=r, height=(y1 - y0)).moved(
            Location((DRIVE_X, (y0 + y1) / 2.0, DRIVE_Z), (1, 0, 0), -90.0))
    body -= _bore_y(SHAFT_R_BORE, DRIVE_UBORE_Y[0], DRIVE_BOSS_Y[1] + 0.02)  # upper bore
    body -= _bore_y(SHAFT_R_BORE, DRIVE_MBORE_Y[0], DRIVE_MBORE_Y[1])        # mid bore
    body -= _bore_y(SHAFT_R_BORE, BOT_FLANGE_Y[0] - 1.0, DRIVE_LBORE_Y[1])   # lower bore

    # STEPPED back axle bore: wide running bore (AXLE_SCREW_R) from the cavity down
    # to AXLE_STOP_Z, then a narrow flood hole (AXLE_FLOOD_R) on through the back wall.
    # The step (annular shoulder at AXLE_STOP_Z) is the rigid -Z stop the dowel shank
    # bottoms on; the narrow hole keeps the socket flooding/draining.
    for (px, py) in AXLE_PIVOTS:
        # wide bore runs from the back step UP through the (per-pivot) boss into the cavity,
        # so the pin shank still passes the now-taller follower boss
        wz0, wz1 = AXLE_STOP_Z, _back_boss_top(px, py) + 1.5
        body -= Cylinder(radius=AXLE_SCREW_R, height=(wz1 - wz0)).moved(
            Location((px, py, (wz0 + wz1) / 2.0)))
        nz0, nz1 = ENC_Z[0] - 3.0, AXLE_STOP_Z + 0.01   # flood hole + melt-stud clearance through back
        body -= Cylinder(radius=AXLE_FLOOD_R, height=(nz1 - nz0)).moved(
            Location((px, py, (nz0 + nz1) / 2.0)))
        # exterior back-face recess: confines the retainer + gives the catch shoulder.
        # CROSS-PIN -> a deeper/wider pocket that traps the cotter across the stud; the
        # recess floor is the annular shoulder the cotter catches when the pin pulls out.
        # HEAT-STAKE -> the melt-cap nesting recess. (Same flush, accessible back face.)
        _rec_r = XRECESS_R if USE_CROSS_PIN else MELT_RECESS_R
        _rec_d = XRECESS_DEPTH if USE_CROSS_PIN else MELT_RECESS_DEPTH
        body -= Cylinder(radius=_rec_r, height=_rec_d + 0.02).moved(
            Location((px, py, ENC_Z[0] + _rec_d / 2.0)))

    # snap-clip catch windows: a through-window in each long side wall so the
    # cover's hook latches behind the window's top edge (also act as drains).
    for side in (+1, -1):
        for yc in SNAP_Y:
            wx_lo, wx_hi = sorted((side * (ENC_X[1] - WALL - 2.0),
                                   side * (ENC_X[1] + 2.0)))
            body -= _box_between(wx_lo, wx_hi,
                                 yc - SNAP_WIN_DY / 2.0, yc + SNAP_WIN_DY / 2.0,
                                 SNAP_WIN_Z[0], SNAP_WIN_Z[1])

    # bolt holes through the BOTTOM mounting flange (axis model -Y), around the
    # shaft exit at (x=DRIVE_X, z=DRIVE_Z); they clear the shaft + its lower bore.
    for (bx, bz) in BOLT_XZ:
        body -= Cylinder(radius=BOLT_R, height=(FLANGE_TY) + 4.0).moved(
            Location((bx, (BOT_FLANGE_Y[0] + BOT_FLANGE_Y[1]) / 2.0, bz),
                     (1, 0, 0), -90.0))

    # (the 8 bottom-flange + 4 side-wall Ø5 drain holes were removed -- cosmetic;
    # see the drainage note above. Flooding/venting still works via the top slots,
    # the snap-clip windows, the back-wall axle-flood holes, and the shaft journal.)

    body.label = "enclosure"
    body.color = ENC
    return body


def build_front_cover():
    """Tool-free SNAP-ON front cover: closes the open front, supports the far
    axle ends (bosses at A_R/B_R/B_L), and carries 4 integral cantilever snap
    clips (2 per long side) that hook into the body side-wall windows. No
    screws. Push on (cams in + clicks); flex the 4 hooks outward to release."""
    plate = _box_between(*ENC_X, *ENC_Y, *COVER_Z)
    z_lo, z_hi = COVER_Z
    for e in plate.edges().filter_by(Axis.Z):
        c = e.center()
        if abs(c.X) > ENC_X[1] - 1.0 and z_lo - 0.1 <= c.Z <= z_hi + 0.1:
            try:
                plate = fillet([e], radius=R_VERT)
            except Exception:
                pass
    # matching chamfer on the cover's EXPOSED outer-face perimeter (Z = COVER_Z[1]);
    # shared edge language with the body so the cover/body seam reads as a deliberate
    # shadow line. The INNER mating face (COVER_Z[0]) is left flat so it seats.
    cover_outer = [e for e in plate.edges().group_by(Axis.Z)[-1] if e.length > 1.0]
    if not cover_outer:
        raise RuntimeError("cover perimeter chamfer: no outer-face edges selected")
    plate = chamfer(cover_outer, length=CHAM_COVER)
    for (px, py) in AXLE_PIVOTS:
        plate += Cylinder(radius=BOSS_OD_R, height=(COVER_BOSS_Z[1] - COVER_BOSS_Z[0])).moved(
            Location((px, py, (COVER_BOSS_Z[0] + COVER_BOSS_Z[1]) / 2.0)))
    for e in plate.edges().filter_by(GeomType.CIRCLE):
        if abs(e.center().Z - COVER_Z[0]) < 0.05:
            try:
                plate = fillet([e], radius=0.8)
            except Exception:
                pass
    # axle-boss bores are now the pin's LOCATING HOLE: the pin's reduced TIP SPIGOT
    # (AXLE_TIP_R) threads up into this bore at a 0.15 mm running fit, so the pin is
    # journaled at both ends and no longer rocks. The bore stays BLIND (does NOT
    # pierce the exposed outer face -> clean front) and ends CHAM_COVER+0.3 short of
    # the outer face, leaving a drainage gap above the spigot tip + a solid skin. The
    # head still seats on the boss FACE (z=COVER_BOSS_Z[0]). A short widened MOUTH at
    # the boss face is a lead-in so the cover self-aligns onto all four spigots.
    blind_top = COVER_Z[1] - (CHAM_COVER + 0.3)
    for (px, py) in AXLE_PIVOTS:
        plate -= Cylinder(radius=AXLE_SCREW_R, height=(blind_top - COVER_BOSS_Z[0]) + 0.02).moved(
            Location((px, py, (COVER_BOSS_Z[0] + blind_top) / 2.0)))
        # lead-in mouth (chamfer-equivalent): a short wider counterbore at the bore
        # entry so each spigot finds its hole as the cover snaps home.
        plate -= Cylinder(radius=AXLE_SCREW_R + AXLE_TIP_LEADIN, height=AXLE_TIP_LEADIN + 0.02).moved(
            Location((px, py, COVER_BOSS_Z[0] + AXLE_TIP_LEADIN / 2.0)))
    # (front-cover vent holes removed -- cosmetic; see the cover-vent note above)
    for clip in _all_snap_clips():
        plate += clip
    plate.label = "front_cover"
    plate.color = COVER_COLOR
    return plate


def _spur_pinion(thickness, label, color):
    """Small INPUT PINION as a build123d solid, built with its axis along +Z (caller
    rotates it to model -Y). Now a TRUE INVOLUTE spur (PINION_PA_DEG, profile-shifted
    PINION_X to clear the 9T undercut, auto tip-truncated), matching the conjugate
    flanks of the spur pair so the right-angle mesh rolls instead of gouges. The
    PINION_PHASE_DEG offset clocks a tooth VALLEY onto the crown's -Y mesh azimuth."""
    pts = involute_gear_points(PINION_MODULE, PINION_TEETH, pa_deg=PINION_PA_DEG,
                               x=PINION_X, backlash=PINION_BACKLASH,
                               phase_deg=PINION_PHASE_DEG)
    return _poly_solid(pts, 0.0, thickness)


def _pinion_spin_deg(open_norm):
    """Pinion rotation about its (model -Y) axis, geared to the crank delta so the
    GIF reads as a real drive: crank turns by `crank_delta`, the crown (rc) turns
    with it, the pinion (rp) turns crank_delta*(rc/rp). Sign chosen so the pinion
    rolls along the crown; flip if it reads wrong on the meshing flank."""
    crank_delta = -(crank_angle_deg(open_norm) - THETA_CLOSED)  # A_L turns -spin
    return -crank_delta * (CROWN_RC / PINION_RP)


def build_input_drive(open_norm):
    """ONE printed part: input PINION integral with the vertical input SHAFT +
    coupler. Axis = model -Y (-> world DOWN after +90X reorient).
    Stack (model-Y, +Y is up/cavity, -Y is down/exit):
        pinion        y in PINION_Y          (-4 .. -12)   meshes the crown
        journal shaft y -12 .. -25 (SHAFT_R)  rides the continuous UPPER+LOWER bore
        shoulder      y just below the flange (-25 .. -27)  +Y push-in stop
        D-coupler     y below the shoulder    (-27 .. -39)  servo/motor interface
    INSTALLABLE one-piece shaft: every feature from the pinion down is <= SHAFT_R <
    bore, so the part drops IN FROM BELOW (-Y), pinion-first up through the journals
    into the cavity, until the bottom SHOULDER (OD > bore) bottoms on the flange
    outer face (the +Y push-in stop). -Y pull-out is taken by the D-coupler engaged
    in the actuator horn-adapter bolted under the flange. (The old mid-shaft collar
    was geometrically captured but un-installable -- it could not pass either bore;
    it is gone, which also gives a longer uninterrupted journal.) Printed, zero
    hardware. Material PA12-GF (stiff, low-creep) so the journals stay round."""
    # --- pinion (axis model -Y) ---
    pin_t = PINION_T
    pinion = _spur_pinion(pin_t, "pinion", color=DARK)
    pinion = pinion.moved(Location((0, 0, 0), (1, 0, 0), -90.0))   # axis +Z -> +Y
    # after -90X the slab z[0,pin_t] maps to y[0,pin_t]; shift so the disc spans
    # PINION_Y = (PINION_YC -/+ pin_t/2), i.e. straddling the crown -Y azimuth.
    pinion = pinion.moved(Location((0, PINION_Y[0], 0)))

    def _cyl_y(r, y0, y1):
        return Cylinder(radius=r, height=(y1 - y0)).moved(
            Location((0, (y0 + y1) / 2.0, 0), (1, 0, 0), -90.0))

    # --- journal shaft: one running diameter SHAFT_R through both bores ---
    # from the pinion bottom (y=PINION_Y[0]) down through both journals to the
    # flange bottom (BOT_FLANGE_Y[0]); journals are the boss + flange bore spans.
    shaft = _cyl_y(SHAFT_R, BOT_FLANGE_Y[0], PINION_Y[0] + 0.01)

    # --- shoulder just below the flange bottom face (the +Y push-in stop) ---
    sh_y0 = BOT_FLANGE_Y[0] - SHAFT_SHOULDER_T
    shoulder = _cyl_y(SHAFT_SHOULDER_R, sh_y0, BOT_FLANGE_Y[0] + 0.01)

    # --- D-profile coupler at the very bottom (the actuator interface) ---
    cp_y1 = sh_y0
    cp_y0 = cp_y1 - SHAFT_COUPLER_LEN
    coupler = _cyl_y(SHAFT_COUPLER_R, cp_y0, cp_y1)
    # flat the D on the +X side
    coupler -= Box(SHAFT_DFLAT * 2, SHAFT_COUPLER_LEN + 2, 4 * SHAFT_COUPLER_R).moved(
        Location((SHAFT_COUPLER_R, (cp_y0 + cp_y1) / 2.0, 0)))

    part = pinion + shaft + shoulder + coupler
    part = part.moved(Location((0, 0, 0), (0, 1, 0), _pinion_spin_deg(open_norm)))
    part = part.moved(Location((DRIVE_X, 0.0, DRIVE_Z)))
    part.label = "input_pinion_shaft"
    part.color = DARK
    return part


# ==========================================================================
# Assembly
# ==========================================================================
def gen_step():
    refR, refL = solve_side_right(0.0), solve_side_left(0.0)
    R, L = solve_side_right(OPEN_NORM), solve_side_left(OPEN_NORM)
    parts = []

    parts.append(build_enclosure())

    # Drive arms = gear sector fused with crank arm (one part -> no gear/crank
    # clip). The LEFT arm carries the CROWN gear of the right-angle stage; the
    # input pinion (build_input_drive) turns the crown -> turns A_L; the spur mesh
    # A_L<->A_R counter-rotates the RIGHT arm -> one (now VERTICAL) shaft moves
    # both jaws. Both arms ride on their own snap-pin axles (the old integral
    # horizontal shaft is gone).
    half_tooth = 360.0 / GEAR_TEETH / 2.0
    spin = crank_angle_deg(OPEN_NORM) - THETA_CLOSED      # crank rotation
    parts.append(drive_arm(R["A"], R["C"], spin, Z_CRANK0, T_CRANK,
                           "drive_arm_R", STEEL_R, with_crown=False))
    parts.append(drive_arm(L["A"], L["C"], -spin + half_tooth, Z_CRANK0, T_CRANK,
                           "drive_arm_L", STEEL_L, with_crown=True))

    # followers B->D. Recess the D-eye exit (bottom) face so the finger pin's
    # (pin_D) melt cap nests in a rigid confining pocket (geometric capture).
    # D-eye = the finger pin's rigid catch: bore NARROW (FP_ARM_BORE_R) + cap
    # recess; B-eye keeps the axle running fit.
    parts.append(link_bar(R["B"], R["D"], LINK_W, Z_FOLLOW0, T_FOLLOW, "follower_R", STEEL_R,
                          counterbores=[(R["D"], Z_FOLLOW0, FP_CB_DEPTH, True, FP_CB_R, FP_EYE_BOSS_R)],
                          bore0_r=AXLE_BORE_R, bore1_r=FP_ARM_BORE_R,
                          eye1_boss_top=Z_FINGER0 - FINGER_THRUST_GAP))
    parts.append(link_bar(L["B"], L["D"], LINK_W, Z_FOLLOW0, T_FOLLOW, "follower_L", STEEL_L,
                          counterbores=[(L["D"], Z_FOLLOW0, FP_CB_DEPTH, True, FP_CB_R, FP_EYE_BOSS_R)],
                          bore0_r=AXLE_BORE_R, bore1_r=FP_ARM_BORE_R,
                          eye1_boss_top=Z_FINGER0 - FINGER_THRUST_GAP))

    # Fin Ray fingers (TPU) rigid with coupler CD
    parts.append(finger(R, refR, -1, TPU, "finger_R"))
    parts.append(finger(L, refL, +1, TPU, "finger_L"))

    # axle pins: A_R/A_L (crank axles) and B_R/B_L (follower axles) are hidden
    # internal axle dowels; C/D finger pins are visible. Both crank arms now ride
    # a snap-pin axle (the left arm no longer carries an integral shaft -- the
    # bottom-exit input drive replaced it), so there IS a pin_A_L.
    for tag, pose, joints in (("R", R, ("A", "B", "C", "D")),
                              ("L", L, ("A", "B", "C", "D"))):
        for j in joints:
            lbl = f"pin_{j}_{tag}"
            cap_lbl = f"cap_{j}_{tag}"
            if j in ("C", "D"):    # finger pins: HEAT-STAKE journal pin + melt cap.
                # Fat neck = the anti-wobble bearing in the FIXED 2.6 TPU finger
                # bore; slim land journals the rigid eye; a melt-stud past the eye
                # EXIT (bottom) face takes a separate cap -> the pull-out stop.
                # far = the rigid eye exit (bottom) face (C -> crank eye @Z_CRANK0;
                # D -> follower @Z_FOLLOW0); far + thickness = the eye top. The cap
                # is melted at this bottom face -> finger+arms+pins are a BENCH
                # SUB-ASSEMBLY (see docs/ASSEMBLY.md).
                # The rigid eye now extends UP via link_bar's anti-wobble journal boss
                # to (Z_FINGER0 - FINGER_THRUST_GAP) -- the under-finger thrust shoulder.
                # The pin's slim LAND journals that FULL height (cap recess floor -> boss
                # top), so it no longer cantilevers across the old empty gap. far = the
                # eye EXIT (bottom) face where the melt cap nests (C -> crank @Z_CRANK0;
                # D -> follower @Z_FOLLOW0). finger+arms+pins stay a BENCH SUB-ASSEMBLY.
                # eye_top = Z_FINGER0 (the finger BOTTOM): the slim LAND journals the rigid
                # eye+boss all the way up to the finger; the fat NECK then fills exactly the
                # finger bore (Z13..23) and its neck->land step floats FINGER_THRUST_GAP above
                # the boss-top thrust face, so the FINGER (not the pin) seats on the shoulder
                # -- no rotating thrust face to drag.
                far = Z_CRANK0 if j == "C" else Z_FOLLOW0
                parts.append(finger_pin(pose[j], far, Z_FINGER0,
                                        Z_FINGER0 + T_FINGER, label=lbl))
                parts.append(melt_cap(pose[j], far, label=cap_lbl))
            else:                  # axles: pin riveted/cross-pinned to the back wall.
                # Dropped in from the front; head seats under the cover boss, the stud
                # exits the back-wall flood hole. CROSS-PIN: a cotter slips through the
                # stud's cross-bore behind the wall = a tool-free, removable pull-out stop
                # (no soldering iron). HEAT-STAKE: a cap melted on the stud. Either way a
                # fixed pivot post (no wobble/fall-out).
                # elem_top = top of the element this pin carries, so the locating
                # collar sits just above it: A -> crank gear/arm top (the LEFT side
                # also carries the crown gear, so its element is taller); B -> follower top.
                if j == "A":
                    elem_top = CROWN_Z[1] if tag == "L" else Z_CRANK0 + T_CRANK
                else:
                    elem_top = Z_FOLLOW0 + T_FOLLOW
                xbz = ENC_Z[0] + XBORE_FROM_FACE if USE_CROSS_PIN else None
                parts.append(axle_pin(pose[j], AXLE_DOWEL_Z1, AXLE_STOP_Z,
                                      AXLE_STUD_TIP_Z, elem_top, tip_z1=AXLE_TIP_Z1,
                                      tip_r=AXLE_TIP_R, xbore_z=xbz, label=lbl))
                if USE_CROSS_PIN:
                    parts.append(cotter(pose[j], ENC_Z[0], label=cap_lbl))
                else:
                    parts.append(melt_cap(pose[j], ENC_Z[0], label=cap_lbl))

    # bolt-on front cover (keep existing occurrence ids stable up to here)
    parts.append(build_front_cover())

    # NEW right-angle-stage input part appended LAST (after build_front_cover) so
    # all pre-existing occurrence ids are unchanged: the vertical input pinion +
    # shaft + D-coupler, exits the model -Y bottom (world DOWN).
    parts.append(build_input_drive(OPEN_NORM))

    asm = Compound(label="gripper", children=parts)
    # reorient to Z-up for printing & viewing: fingers point world +Z (up); the
    # vertical input shaft (model -Y) exits world -Z (straight DOWN out the
    # bottom). (Model is authored Y-up; +90X maps model+Y->world+Z, model-Y->-Z.)
    asm = asm.moved(Location((0, 0, 0), (1, 0, 0), 90))
    return asm


# ==========================================================================
# Numeric self-check
# ==========================================================================
def _tip_world(side_pose, ref_pose):
    C0 = ref_pose["C"]
    a0 = ref_pose["coupler_ang"]
    tip0 = (C0[0], C0[1] + FR_BLADE_LEN * FINGER_SCALE)
    d_ang = math.radians(side_pose["coupler_ang"] - a0)
    vx, vy = tip0[0] - C0[0], tip0[1] - C0[1]
    rx = vx * math.cos(d_ang) - vy * math.sin(d_ang)
    ry = vx * math.sin(d_ang) + vy * math.cos(d_ang)
    C1 = side_pose["C"]
    return (C1[0] + rx, C1[1] + ry)


if __name__ == "__main__":
    refR = solve_side_right(0.0)
    a0 = refR["coupler_ang"]
    for o in (0.0, 0.25, 0.5, 0.75, 1.0):
        R = solve_side_right(o)
        tip = _tip_world(R, refR)
        print(f"open={o:.2f}  base_gap={2*R['C'][0]:6.2f}  tip_gap={2*tip[0]:7.2f}  "
              f"finger_rot={R['coupler_ang']-a0:7.2f}")

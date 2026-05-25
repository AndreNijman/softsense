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
    Cone,
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
# Kinematic parameters (mm, deg)  -- locked
# --------------------------------------------------------------------------
R_GEAR = 12.0                 # sector-gear pitch radius -> sets pivot spacing
PIVOT_SPACING = 2.0 * R_GEAR  # |A_L A_R| so the gears mesh on the centerline

A_R = (PIVOT_SPACING / 2.0, 0.0)     # crank / gear pivot  = (12, 0)
B_R = (26.0, 10.0)                   # follower pivot, outboard & low

R_CRANK = 34.0    # |A->C|  crank (gear arm) length
R_FOLLOW = 32.0   # |B->D|  follower length
R_COUPLER = 20.0  # |C->D|  coupler length (finger base bracket span)

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
T_CRANK = 5.0
Z_CRANK0 = 1.0                        # crank + gear layer
T_FOLLOW = 5.0
Z_FOLLOW0 = 7.0                       # follower layer
T_FINGER = 10.0                      # Fin Ray finger depth in Z (z 13..23)
Z_FINGER0 = 13.0                      # finger layer
LINK_W = 7.0          # link bar half-lobe width
PIN_R = 2.3           # pivot pin radius
PIN_HEAD_R = 3.6      # socket-head cap radius
PIN_HEAD_T = 1.2      # cap height (sits ~flush in a counterbore)

# production / printability (FDM design-for-AM standards)
PRINT_CLEAR = 0.3     # mating clearance per side (FDM standard ~0.3 mm)
DFM_EDGE = 0.4        # universal edge-break chamfer: no sharp edges
AXLE_BORE_R = PIN_R + PRINT_CLEAR   # link/arm rides on its axle with clearance

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
SHAFT_R = 4.0         # vertical input-shaft radius
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
# not buried bodies. Representative straight-flank form (coupon-tunable), like
# the spur gears elsewhere in this model.
CROWN_RC = 8.0        # crown-gear pitch radius on the A_L gear face
CROWN_Z = (6.0, 9.0)  # crown ring model-Z span (sits on the A_L gear +Z face)
CROWN_TOOTH_H = 1.6   # crown tooth RADIAL band half-width about the pitch circle
CROWN_FACE_H = 2.8    # crown tooth AXIAL proud height (teeth stand this far in +Z
                      # from CROWN_Z[1] downward; the rest of the band is solid base).
                      # Tall teeth + deep MESH_DEPTH -> the pinion tips sit well down
                      # in the crown valleys (real interleave, not a tip graze).
CROWN_TEETH = 24      # crown face-tooth count (representative)
PINION_RP = 3.0       # input-pinion pitch radius
PINION_TEETH = 9      # pinion tooth count (representative; ratio CROWN/PINION)
PINION_TOOTH_H = 1.6
PINION_T = 4.0        # pinion thickness along its axis (model Y)
PINION_TIP = PINION_RP + 0.45 * PINION_TOOTH_H   # pinion tooth-tip radius
MESH_DEPTH = 2.2      # how far the pinion tips dip into the crown teeth (deep enough
                      # that the tip sits in the valley with flank contact, not a graze)
DRIVE_X = -A_R[0]                    # shaft/pinion model-X = A_L x = -12
# Shaft/pinion axis model-Z: raise it so the pinion sits ABOVE the crown face and
# only its bottom tips reach MESH_DEPTH into the crown teeth (top at CROWN_Z[1]):
#   pinion_bottom_tip_Z = CROWN_Z[1] - MESH_DEPTH = DRIVE_Z - PINION_TIP
DRIVE_Z = CROWN_Z[1] - MESH_DEPTH + PINION_TIP    # = 9 - 1 + 3.72 = 11.72
# Pinion centred at the crown -Y azimuth (model-Y = -CROWN_RC), straddling it so
# the pinion face width sweeps the crown teeth at that azimuth.
PINION_YC = -CROWN_RC                 # pinion centre model-Y = -8 (the mesh azimuth)
PINION_Y = (PINION_YC - PINION_T / 2.0, PINION_YC + PINION_T / 2.0)  # -10 .. -6
SHAFT_R_BORE = SHAFT_R + PRINT_CLEAR  # journal-bore radius (running clearance)
# TWO JOURNAL BEARINGS along model -Y, with a CAPTURED-COLLAR POCKET between them
# (the same head+step-shoulder idea as the captured axle dowels). Stack (model-Y,
# +Y up/cavity, -Y down/exit), bore radius SHAFT_R_BORE throughout:
#   UPPER bore  : DRIVE_UBORE_Y  (in the boss)         -- alignment guide
#   POCKET      : DRIVE_POCKET_Y (widened, straddles the cavity floor) -- holds collar
#   LOWER bore  : DRIVE_LBORE_Y  (wall + flange)       -- the long load-bearing exit
DRIVE_UBORE_Y = (-15.5, -13.5)       # upper journal bore: len 2.0
DRIVE_POCKET_Y = (-18.0, -15.5)      # collar pocket: height 2.5 (straddles floor -17)
DRIVE_LBORE_Y = (-25.0, -18.0)       # lower journal bore: len 7.0
# AXIAL CAPTURE (the known failure point): a single integral SHAFT COLLAR (OD >
# bore -> cannot pass either bore) sits in the pocket and is trapped between the
# two bore-mouth shoulders -> NO pull-out (-Y), NO push-in (+Y), NO wobble. This
# replaces depending on the pinion as a stop (pinion tip < bore, so it would slip
# straight through). Plus a bottom SHOULDER under the flange for redundant +Y
# capture and a clean coupler land.
SHAFT_COLLAR_R = SHAFT_R + 1.8       # captured collar OD (5.8 > bore 4.3 -> 1.5 mm seat)
SHAFT_COLLAR_T = 2.0                 # collar axial length (model Y); 0.25 mm play each side
SHAFT_COLLAR_YC = (DRIVE_POCKET_Y[0] + DRIVE_POCKET_Y[1]) / 2.0   # -16.75 (pocket centre)
SHAFT_COLLAR_Y = (SHAFT_COLLAR_YC - SHAFT_COLLAR_T / 2.0,
                  SHAFT_COLLAR_YC + SHAFT_COLLAR_T / 2.0)          # -17.75 .. -15.75
POCKET_R = SHAFT_COLLAR_R + 0.2      # pocket radius (collar spins free inside)
SHAFT_SHOULDER_R = SHAFT_R + 1.8     # redundant bottom shoulder OD (> bore -> can't pass)
SHAFT_SHOULDER_T = 2.0               # shoulder axial length (model Y)
SHAFT_COUPLER_R = 5.0 # bottom coupler radius (D-profile for a servo/motor)
SHAFT_COUPLER_LEN = 12.0
SHAFT_DFLAT = 1.4     # D-flat depth on the coupler

# --- 3D-printed snap-pin geometry (replaces ALL metal pivot pins) ---
SNAP_HEAD_R = PIN_R + 1.6        # flange that stops pull-through
SNAP_HEAD_T = 1.8                # flange thickness (sits OUTSIDE the near face)
SNAP_BARB_PROUD = 0.9            # lip sticks this far past PIN_R (-> r 3.2);
                                 # raised 0.7->0.9 so the lip catches 0.6 mm of
                                 # rigid counterbore shoulder (was 0.4 mm) while
                                 # keeping insertion strain in PETG's elastic band
SNAP_BARB_LIP_T = 1.0            # axial length of the flat locking-lip face
                                 # (FLOOR: 2.5 perimeters @0.4 nozzle -- do NOT
                                 # reduce; the only marginal wall in the design)
SNAP_BARB_LEAD = 3.0             # length of the tapered lead-in cone
SNAP_TIP_R = 1.0                 # small flat at the very tip (printable)
SNAP_SLOT_W = 1.0                # split-slot width (lets the tip flex)
SNAP_SLOT_LEN = 9.0             # slot depth back from tip; lengthened 7->9 so the
                                 # split cantilever is long enough that the larger
                                 # SEAT+PROUD insertion deflection stays <~3% strain
SNAP_BARB_SEAT = 1.2           # catch-face axial overlap PAST the far face;
                                 # raised 0.30->1.2 (audit floor >=1.0) so the lip
                                 # has real axial capture vs creep + hygroscopic drift

# --- confined counterbore: the GEOMETRIC capture for the barbed finger pins ---
# The expanded lip drops into a rigid counterbore pocket cut into the EXIT face
# of the receiving eye. The pocket wall RADIALLY confines the lip (it cannot
# creep-relax inward to re-enter the bore and escape) and the pocket SHOULDER
# (step from bore radius up to pocket radius) takes the axial pull-out load in
# rigid material -- so retention no longer depends on the sprung tip staying
# expanded. This is the creep-proof fix per UNDERWATER audit C-items 1-3.
SNAP_CB_RCLEAR = 0.45           # radial gap pocket-wall to lip; 0.45 keeps the
                                # worst-case-TIGHT gap (+/-0.2 FDM) non-negative so
                                # the lip never jams on assembly, while the shoulder
                                # still grows 1.05 mm wide (robust axial bearing)
SNAP_CB_FLOOR_CLEAR = 0.30      # axial gap lip-front-face to pocket floor

GEAR_TEETH = 16
GEAR_TOOTH_H = 3.0    # radial tooth height
GEAR_SECTOR_DEG = 150.0   # gears are sectors, not full discs

# --- Fin Ray finger (TPU compliant jaw) parameters ---
FR_BRACKET_W = 13.0    # mounting-bracket eye diameter
FR_BLADE_LEN = 90.0    # contact beam length, base -> tip
FR_BASE_WIDTH = 22.0   # triangle base width in X
FR_CONTACT_OFFSET = 1.0  # contact face sits this far inboard of the centreline
FR_BASE_DROP = 9.0     # triangle base sits this far below the top pin
FR_WALL = 2.8          # beam / rib wall thickness (uniform default)
FR_TIP_WIDTH = 2.0     # blade width at the blunt tip (sharp compliant taper)
FR_N_RIBS = 14         # number of internal ribs (all same-direction slant)
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
FR_CONTACT_WALL = 1.2       # contact-beam wall (thin -> conforms, even pressure)
FR_CONTACT_WALL_TIP = 1.2   # contact-beam wall at tip
FR_SPINE_WALL = 1.8         # spine-beam wall at base
FR_SPINE_WALL_TIP = 1.8     # spine-beam wall at tip
FR_RIB_WALL = 1.6           # rib wall at base
FR_RIB_WALL_TIP = 1.6       # rib wall at tip
FR_INSET_BASE = 4.0    # solid floor across the bottom
FR_INSET_TIP = 3.0     # solid cap at the apex
MOUNT_HOLE_R = PIN_R + PRINT_CLEAR   # finger pin bore (FDM clearance)
# grip texture: CROSSHATCH micro-posts on the contact face (so objects don't slip).
# Optimised by a dedicated grip-texture FEA/swarm campaign (see grip/GRIP_TEXTURE.md):
# a square-post array out-drains and out-grips the old single-axis ridges on WET
# objects (the gripper runs underwater and as-printed eTPU is slick), grips in two
# directions (M_worst 0.72 vs a ridge's 0.18), and tiles the blade perfectly. The
# crossing 0.54 mm channels squeeze the water film out (tyre-tread / tree-frog
# mechanism) and the post edges break the glossy printed-TPU skin. Conservative
# (>= 0.5 mm channel) variant: universal grip score 0.75 vs the smooth-face 0.25.
FR_GRIP_DEPTH = 0.6     # post height proud of the contact face (mm); grip-neutral
                        # above ~0.3 (drainage saturates) so kept at 0.6 for the
                        # safe closed-pose finger-finger gap and a low post aspect
FR_GRIP_PITCH = 1.8     # post pitch along the blade length Y (mm); land = pitch-FLAT
FR_GRIP_Y0_FRAC = 0.15  # texture starts at this fraction of the blade length
FR_GRIP_Y1_FRAC = 0.95  # texture ends at this fraction of the blade length
FR_GRIP_ROOT_IN = 0.2   # post root sits this far INTO the body (fuses cleanly)
FR_GRIP_FLAT = 0.54     # channel width between posts along Y (mm) -> land 1.26 mm
FR_GRIP_CROSS = True    # crosshatch: chop the Y-ridges into posts with Z-channels
FR_GRIP_CROSS_PITCH = 1.8  # post pitch across the finger depth Z (mm)
FR_GRIP_CROSS_GAP = 0.54   # channel width between posts along Z (mm)
# print-friendly rounding (FDM TPU, prints flat on the z0 face)
FR_BASE_CHAMFER = 0.5    # bottom-edge (bed face) chamfer: kills elephant-foot
FR_CELL_FILLET = 0.8     # fillet radius on internal rib-cell / spar corners
FR_TIP_FILLET = 1.5      # round the blade tip apex
FR_GRIP_TIP_FLAT = 0.5   # half-width of the flat at each post tip (slight draft)

# --------------------------------------------------------------------------
# Colours (clean industrial: dark slate body, matte-black TPU jaws, steel)
# --------------------------------------------------------------------------
STEEL_L = Color(0.55, 0.58, 0.62)   # internal links / gears (hidden in housing)
STEEL_R = Color(0.58, 0.61, 0.65)
PIN_COLOR = Color(0.74, 0.76, 0.79)  # pivot pins (bright steel)
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


# Pocket depth of the lip-confining counterbore (rigid, cut into the eye exit
# face). Deep enough to swallow the full locking lip plus a small floor gap:
SNAP_CB_DEPTH = SNAP_BARB_LIP_T + SNAP_CB_FLOOR_CLEAR   # 1.0 + 0.30 = 1.30 mm
SNAP_CB_R = (PIN_R + SNAP_BARB_PROUD) + SNAP_CB_RCLEAR  # pocket radius (3.2 + 0.45 = 3.65)


def _counterbore_cut(p, z_face, depth, into_plus_z):
    """Solid to subtract from a receiving eye so the snap-pin lip drops into a
    rigid confining pocket. The pocket is the eye bore WIDENED to SNAP_CB_R over
    `depth` of the eye thickness measured from `z_face` (the eye's EXIT face).
    into_plus_z=True cuts upward into the eye (exit face is the eye bottom);
    False cuts downward. The remaining ring of eye material at radius
    SNAP_CB_R..outer (a) radially confines the expanded lip so it cannot
    creep-relax inward and escape, and (b) the step where the bore narrows back
    to AXLE_BORE_R is the rigid SHOULDER that takes the axial pull-out load."""
    if into_plus_z:
        zc = z_face + depth / 2.0
    else:
        zc = z_face - depth / 2.0
    return Cylinder(radius=SNAP_CB_R, height=depth).moved(
        Location((p[0], p[1], zc)))


# Local eye boss OD so a counterbored eye keeps a solid ring OUTSIDE the pocket:
# pocket radius + a >=1 mm confining/shoulder wall. The plain LINK_W eye (r 3.5)
# is too small for the SNAP_CB_R (3.65) pocket -- without this boss the pocket
# would blow through the eye wall and lose both the radial confinement and the
# axial shoulder. Same idea as the housing's BOSS_OD_R around its axle bores.
SNAP_EYE_BOSS_R = SNAP_CB_R + 1.0


def link_bar(p0, p1, width, z0, thickness, label, color, counterbores=None):
    """Rounded-end link bar from p0 to p1 (eyes at both ends). `counterbores` is
    an optional list of (point, z_face, depth, into_plus_z) specs cut into the
    eye exit face to confine a snap-pin lip (see _counterbore_cut). Each
    counterbored eye gets a local SNAP_EYE_BOSS_R boss so a solid confining ring
    + axial shoulder survives around the widened pocket."""
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
        for (cp, zf, depth, into_pz) in counterbores:
            bar += Cylinder(radius=SNAP_EYE_BOSS_R, height=thickness).moved(
                Location((cp[0], cp[1], z0 + thickness / 2.0)))
    # bore the pin holes (FDM clearance fit)
    bar -= Cylinder(radius=AXLE_BORE_R, height=thickness * 3).moved(
        Location((p0[0], p0[1], z0 + thickness / 2.0)))
    bar -= Cylinder(radius=AXLE_BORE_R, height=thickness * 3).moved(
        Location((p1[0], p1[1], z0 + thickness / 2.0)))
    # lip-confining counterbores (the geometric snap-pin capture pockets)
    if counterbores:
        for (cp, zf, depth, into_pz) in counterbores:
            bar -= _counterbore_cut(cp, zf, depth, into_pz)
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
    pitch = R_GEAR
    root = pitch - 0.55 * GEAR_TOOTH_H
    tip = pitch + 0.45 * GEAR_TOOTH_H
    step = 2 * math.pi / GEAR_TEETH
    ph = math.radians(phase_deg)
    pts = []
    for k in range(GEAR_TEETH):
        c = ph + k * step
        # one tooth: root-left, tip-left, tip-right, root-right
        for frac, r in ((-0.34, root), (-0.18, tip), (0.18, tip), (0.34, root)):
            aa = c + frac * step
            pts.append((r * math.cos(aa), r * math.sin(aa)))
    sol = _poly_solid(pts, z0, thickness)
    if bore:
        sol -= Cylinder(radius=AXLE_BORE_R, height=thickness * 3).moved(
            Location((0, 0, z0 + thickness / 2.0)))
    sol = sol.moved(Location((center[0], center[1], 0)))
    sol.label = label
    sol.color = color
    return sol


def _crown_gear(center, z_lo, z_hi, label, color):
    """CROWN gear: a ring at `center` (axis model-Z) carrying RADIAL FACE TEETH on
    its +Z face -- axial-proud blocks repeating around the pitch circle. It meshes
    a spur pinion whose axis is perpendicular (model -Y), giving the 90deg turn.
    Representative tooth form (coupon-tunable), like the spur gears in this model.
    The ring sits ON the A_L gear's +Z face (z_lo..z_hi) and fuses into it; its
    bore is left to drive_arm (it shares the A_L axle bore)."""
    thickness = z_hi - z_lo
    ro = CROWN_RC + CROWN_TOOTH_H        # outer radius of the toothed band
    ri = CROWN_RC - CROWN_TOOTH_H        # inner radius of the toothed band
    ring = Cylinder(radius=ro, height=thickness).moved(
        Location((0, 0, z_lo + thickness / 2.0)))
    ring -= Cylinder(radius=ri, height=thickness * 3).moved(
        Location((0, 0, z_lo + thickness / 2.0)))
    # axial face teeth: short proud blocks standing CROWN_FACE_H in +Z off the top
    # of the band. The lower (thickness - CROWN_FACE_H) of the band is a solid base
    # fused to the A_L gear face. Only these short teeth stick up to mesh the
    # pinion's bottom tooth tips -> a thin face ring, not a thick disc.
    tooth_z = CROWN_FACE_H               # axial proud height of the face teeth
    step = 2 * math.pi / CROWN_TEETH
    teeth = []
    for k in range(CROWN_TEETH):
        c = k * step
        # wedge tooth between two radii, half a pitch wide
        pts = []
        for frac, r in ((-0.25, ri), (-0.12, ro), (0.12, ro), (0.25, ri)):
            aa = c + frac * step
            pts.append((r * math.cos(aa), r * math.sin(aa)))
        teeth.append(_poly_solid(pts, z_hi - tooth_z, tooth_z))
    if teeth:
        crown = ring
        for t in teeth:
            crown = crown + t
    else:
        crown = ring
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
    # Counterbore the C-eye exit (bottom) face so the finger pin (pin_C) lip drops
    # into a rigid confining pocket -> geometric, creep-proof capture.
    cb = [(C, z0, SNAP_CB_DEPTH, True)]
    arm = link_bar(A, C, LINK_W, z0, thickness, label + "_arm", color, counterbores=cb)
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


def snap_pin(p, z0, z1, head_at="z0", label="snap_pin", color=PIN_COLOR,
             shank_r=PIN_R, barb=True):
    """Fully 3D-printed pivot pin (no fasteners). Built in the authored frame at
    XY point p, shank +Z from z0..z1, head flange at the head_at end.
    barb=True : the far end is a SPLIT BARBED tip that squeezes in and springs
                out PAST the far bore face to self-lock (finger pins -> the far
                end exits into free space).
    barb=False: a plain headed DOWEL with a small lead tip (axle pins -> the
                dowel is captured between the back-wall socket and the cover
                boss, so it needs no barb and nothing has to expand in a bore)."""
    x, y = p
    L = z1 - z0
    barb_max_r = shank_r + SNAP_BARB_PROUD

    head = Cylinder(radius=SNAP_HEAD_R, height=SNAP_HEAD_T).moved(
        Location((0, 0, -SNAP_HEAD_T / 2.0)))
    shank = Cylinder(radius=shank_r, height=L).moved(Location((0, 0, L / 2.0)))

    if barb:
        lip_back_z = L + SNAP_BARB_SEAT
        lip_front_z = lip_back_z + SNAP_BARB_LIP_T
        tip_z = lip_front_z + SNAP_BARB_LEAD
        stub = Cylinder(radius=shank_r, height=(lip_back_z - L) + 0.01).moved(
            Location((0, 0, (L + lip_back_z) / 2.0)))
        lip = Cylinder(radius=barb_max_r, height=SNAP_BARB_LIP_T).moved(
            Location((0, 0, (lip_back_z + lip_front_z) / 2.0)))
        lead = Cone(bottom_radius=barb_max_r, top_radius=SNAP_TIP_R,
                    height=SNAP_BARB_LEAD).moved(
            Location((0, 0, (lip_front_z + tip_z) / 2.0)))
        body = head + shank + stub + lip + lead
        # '+' cross slot confined to the barb end (bearing shank stays solid)
        slot_root_z = max(tip_z - SNAP_SLOT_LEN, L + 0.6)
        slot_h = (tip_z - slot_root_z) + 1.0
        slot_zc = (slot_root_z + tip_z + 1.0) / 2.0
        slot_a = Box(SNAP_SLOT_W, 4 * barb_max_r, slot_h).moved(Location((0, 0, slot_zc)))
        slot_b = Box(4 * barb_max_r, SNAP_SLOT_W, slot_h).moved(Location((0, 0, slot_zc)))
        relief = Cylinder(radius=SNAP_SLOT_W * 0.7, height=SNAP_SLOT_W * 2).moved(
            Location((0, 0, slot_root_z)))
        body = body - slot_a - slot_b - relief
    else:
        # plain dowel: head + shank + a NARROW pilot tip that fits the back flood
        # hole, so the FLAT shank-end shoulder (r=shank_r) bottoms cleanly on the
        # stepped-bore shoulder (the geometric -Z stop) while the pilot self-centres
        # in the flood hole. Pilot radius < AXLE_FLOOD_R so it never jams.
        pilot_r = min(shank_r * 0.55, AXLE_FLOOD_R - 0.25)
        tip = Cone(bottom_radius=pilot_r, top_radius=pilot_r * 0.7,
                   height=1.0).moved(Location((0, 0, L + 0.5)))
        body = head + shank + tip

    # DFM edge-break: soften the head-flange rim (handled during insertion). The
    # barb catch face is deliberately left crisp so the lock stays positive.
    hd = [e for e in body.edges().filter_by(GeomType.CIRCLE)
          if abs(e.center().Z) < 0.05]
    body = _safe_round(body, hd, min(DFM_EDGE, SNAP_HEAD_T * 0.5), chamfer)

    if head_at == "z0":
        body = body.moved(Location((0, 0, z0)))
    else:
        body = body.moved(Location((0, 0, 0), (1, 0, 0), 180.0))
        body = body.moved(Location((0, 0, z1)))
    body = body.moved(Location((x, y, 0)))
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
    # post edges grip in both directions and break the slick printed-eTPU skin.
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
ENC_X = (-48.0, 48.0)        # outer width
ENC_Y = (-20.0, 16.0)        # bottom -> top of top wall (top LOWERED to 16)
ENC_Z = (-6.0, 24.0)         # back -> front (back wall slimmed 10->4 mm: the old
                             # 10 mm back wall was legacy from the removed horizontal
                             # shaft; the vertical drive needs no depth there. Cuts
                             # the housing depth 36->30 mm for a slimmer profile. The
                             # stepped axle flood hole (nz0 = ENC_Z[0]-3) still exits.
WALL = 3.0
TOP_WALL_Y0 = 14.5           # inside face of the thin top wall (y 14.5..16)
CAV_X = (-45.0, 45.0)        # interior clear cavity (holds the mechanism)
CAV_Y = (-17.0, 14.5)
CAV_Z = (-2.0, 22.0)
SLOT_Z = (0.0, 22.0)         # slots cut the full cavity depth in Z
SLOT_R = (2.5, 41.0)         # right top slot x-span (WIDENED so arms clear)
SLOT_L = (-41.0, -2.5)       # left top slot x-span  (WIDENED so arms clear)
# --- VERTICAL input-shaft journals through the model -Y BOTTOM wall ---------
# World-down = model -Y. The shaft runs along model -Y at (x=DRIVE_X, z=DRIVE_Z),
# through the bottom wall (y in [-20,-17]), and exits into a bottom mounting
# flange + D-coupler. TWO journal bearings capture it:
#   UPPER journal: a boss standing UP (+Y) off the inside bottom-wall face into
#     the cavity, bored SHAFT_R_BORE; carries the load near the pinion.
#   LOWER journal: the bottom wall itself + the flange thickness, bored
#     SHAFT_R_BORE; the long exit bearing.
# Between them the shaft's captured SHOULDER (OD > bore) sits in the gap and is
# trapped against both bore mouths -> no pull-out, no wobble (axial capture).
# Upper journal boss: stand it up off the cavity floor toward the pinion, but cap
# its top so it CLEARS the A_L crank-gear teeth tips. With the pinion stage raised
# (PINION higher in -Y), the boss can no longer reach to 0.3 mm below the pinion --
# that would drive the boss radius into the gear teeth (radius R_GEAR+tip from A_L,
# i.e. straight down to model-Y = -(R_GEAR + 0.45*GEAR_TOOTH_H)). So cap the boss
# top at that gear-tip Y minus 0.3 mm running clearance. The shaft simply spans the
# short gap from the boss top up to the pinion (it is captured by the collar + the
# long lower bore; this upper boss is only the alignment journal).
_GEAR_TIP_Y = -(R_GEAR + 0.45 * GEAR_TOOTH_H)            # -13.35 (gear teeth reach here)
DRIVE_BOSS_Y = (CAV_Y[0], min(PINION_Y[0] - 0.3, _GEAR_TIP_Y - 0.3))  # -17 .. -13.65
DRIVE_BOSS_R = SHAFT_R + 2.4                 # boss OD -> >=2 mm wall around bore
BOT_FLANGE_Y = (-25.0, ENC_Y[0])            # bottom mounting flange: y -25 .. -20
BOT_FLANGE_X = ENC_X                          # flush with the body sides: the base is
                                             # a seamless continuation of the shell
                                             # (no tacked-on narrower lip, and no
                                             # downward side-overhang to support)
BOT_FLANGE_Z = (ENC_Z[0], 22.0)              # back flush with the body; front stops at
                                             # the cavity (front frame + cover above)
FLANGE_TY = (BOT_FLANGE_Y[1] - BOT_FLANGE_Y[0])   # flange thickness in Y (5)
BOLT_R = 2.25                # M4 clearance
# bolt holes on the bottom flange: a clean symmetric 4 at the flange corners, clear
# of the shaft exit (x=-12, z=10.52), its lower bore, and the drains (was an
# asymmetric 5 that read as random).
BOLT_XZ = [(-38.0, 2.0), (38.0, 2.0), (-38.0, 18.0), (38.0, 18.0)]
R_VERT = 6.0                 # vertical corner radius (4->6: rounder uprights read
                             # as a designed enclosure, not a brick; still clears the
                             # cavity wall at the slim back corners)
R_TOP = 2.0
CHAM_EDGE = 1.5              # break/finish chamfer for the body & base perimeter edges
CHAM_COVER = 1.2            # matching chamfer on the front-cover outer perimeter
                            # (shared edge language -> the body/cover seam reads as an
                            # intentional shadow line, not a parts mismatch)

# --- underwater drainage / flood holes (so the housing floods & drains) ---
# With model -Y now WORLD-DOWN, the model -Y bottom wall is the low point. Drains
# there let water in/out; the +Y top slots are the high vent (no trapped pocket).
DRAIN_R = 2.5
DRAIN_BOTTOM_X = [-30.0, 0.0, 16.0, 30.0]   # bottom-wall rows (clear of shaft x=-12
                                            # and of the corner bolts at x=+-38)
DRAIN_SIDE_YZ = [(-14.0, 4.0), (-14.0, 16.0)]      # low side-wall holes (along X)

# --- assembly split: open-front body + bolt-on front cover ---------------
COVER_COLOR = Color(0.33, 0.35, 0.40)   # cover: slightly lighter than ENC
FRONT_WALL_Z = (22.0, 24.0)             # old solid front wall, now removed
AXLE_PIVOTS = [A_R, B_R, mirror_x(B_R), mirror_x(A_R)]  # captured-axle pivots
# (A_L now rides on its OWN snap-pin axle too: the old integral input shaft is
#  gone -- A_L is driven by the crown gear, so it needs a normal pivot axle.)
AXLE_SCREW_R = AXLE_BORE_R              # snap-pin shank clearance (was M3)
BOSS_OD_R = AXLE_SCREW_R + 2.0          # axle boss OD -> 2 mm wall around bore (DFM min)
BACK_BOSS_Z = (-2.0, 1.0)              # back-wall boss into cavity
COVER_BOSS_Z = (20.0, 22.0)            # cover inner-face boss into cavity
# --- axle dowel axial sandwich (geometric capture, no barb) ---
# The plain axle dowel is trapped between the BACK boss and the COVER boss with no
# slop: its head (SNAP_HEAD_R, wider than the AXLE_SCREW_R bore) cannot pass the
# back boss bore (=> cannot fall out the back, -Z stop) and its head top face
# seats against the cover boss inner face (=> +Z stop). Sizing puts the head top
# just clear of the cover boss and the tip just into the back boss bore.
AXLE_DOWEL_CLR = 0.20                       # head-to-cover-boss seating gap
AXLE_DOWEL_Z1 = COVER_BOSS_Z[0] - AXLE_DOWEL_CLR - SNAP_HEAD_T   # 18.0 (shank top)
# The back axle bore is STEPPED: a wide (AXLE_SCREW_R) running bore from the cavity
# down to AXLE_STOP_Z, then a narrow flood hole (AXLE_FLOOD_R) on through the back
# wall. The dowel's flat shank end (r=PIN_R) is too wide for the flood hole, so it
# BOTTOMS on the rigid step (annular shoulder) -> the -Z stop. The narrow hole still
# floods/drains (3 mm dia > 1.5 mm vent floor). With head_at='z1' the shank end is at
# z0; set z0 = AXLE_STOP_Z so the shank end seats on the step with the head clamped
# against the cover boss above -> the dowel is sandwiched with NO axial slop.
AXLE_STOP_Z = 0.0                           # back-bore step (shank bottoms here)
AXLE_FLOOD_R = 1.5                          # narrow flood hole below the step
AXLE_DOWEL_Z0 = AXLE_STOP_Z                 # shank flat end seats on the step
# (the old back-wall A_L shaft bore + plain-bushing seat -- SHAFT_C/SHAFT_BORE_R/
#  BUSH_* -- are REMOVED: A_L is now driven by the crown gear, not a coaxial
#  horizontal shaft; the vertical input shaft journals through the bottom wall.)
CORNER_XY = [(-43.0, -15.0), (43.0, -15.0), (-43.0, 13.0), (43.0, 13.0)]
CORNER_BOSS_R = 3.0                     # screw-boss outer radius
CORNER_TAP_R = 1.35                    # M3 tap (self-tap into body column)
CORNER_CLEAR_R = 1.7                   # M3 clearance hole in the cover
CORNER_BOSS_Z = (-2.0, 22.0)           # (legacy; replaced by snap clips)
COVER_Z = (22.0, 25.0)                 # bolt-on cover plate

# --- front-cover vent holes (underwater audit C-6): let trapped air escape when
# the gripper is front-up. Placed over the OPEN cavity (Y in [-17,14.5], X in
# [-45,45]), biased +Y so they are the high point fingers-up, one near each side
# to cover roll, clear of the 3 cover axle bosses and the snap-clip windows. ---
COVER_VENT_R = 0.9                      # 1.8 mm dia (> 1.5 mm bubble/FDM floor)
COVER_VENT_XY = [(-34.0, 12.0), (0.0, 12.0), (34.0, 12.0)]   # clean symmetric row,
                                        # >=8 mm from any boss centre

# --- snap-clip front cover (tool-free, zero hardware) -------------------
SNAP_Y = [-9.0, 7.0]                 # clip y-centres on each side wall
SNAP_ARM_W = 9.0                     # clip width along Y (flexing beam width)
SNAP_ARM_T = 2.0                     # arm radial thickness (X) -- thinned 2.8->2.0:
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
SNAP_Z0 = 1.5                        # arm root region near hook (back end)
                                     # (was 6.5; lowered to lengthen the clip
                                     # cantilever -> bending strain drops from
                                     # ~3.32% to ~1.9% so PA12-GF (brittle,
                                     # allowable ~1.5-2.0%) survives insertion.)
SNAP_HOOK_Z = (7.0, 10.0)            # hook lip Z-span
SNAP_HOOK_ENGAGE = 1.5               # how far the hook reaches inward into wall
SNAP_CLEAR = 0.35                    # engagement clearance
SNAP_LEADIN = 2.0                    # lead-in chamfer run at the hook back end
SNAP_WIN_Z = (SNAP_HOOK_Z[0] - SNAP_CLEAR, SNAP_HOOK_Z[1] + SNAP_CLEAR)
SNAP_WIN_DY = 11.0                   # window length along Y (clears arm width)
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
    ends. Keeps the cavity, two top slots, captured-axle bosses, and drain/flood
    holes. The old back-wall A_L horizontal shaft bore + plain-bushing seat are
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
        body += Cylinder(radius=BOSS_OD_R, height=(BACK_BOSS_Z[1] - BACK_BOSS_Z[0])).moved(
            Location((px, py, (BACK_BOSS_Z[0] + BACK_BOSS_Z[1]) / 2.0)))

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

    # VERTICAL input-shaft journal: UPPER bore + COLLAR POCKET + LOWER bore, all
    # at (x=DRIVE_X, z=DRIVE_Z), axis model -Y. The pocket (POCKET_R > bore) sits
    # between the two bores; its two bore-mouth shoulders are the rigid axial stops
    # that trap the shaft collar (geometric capture, like the axle dowels' step).
    def _bore_y(r, y0, y1):
        return Cylinder(radius=r, height=(y1 - y0)).moved(
            Location((DRIVE_X, (y0 + y1) / 2.0, DRIVE_Z), (1, 0, 0), -90.0))
    body -= _bore_y(SHAFT_R_BORE, DRIVE_UBORE_Y[0], DRIVE_BOSS_Y[1] + 0.02)  # upper bore
    body -= _bore_y(POCKET_R, DRIVE_POCKET_Y[0], DRIVE_POCKET_Y[1])          # collar pocket
    body -= _bore_y(SHAFT_R_BORE, BOT_FLANGE_Y[0] - 1.0, DRIVE_LBORE_Y[1])   # lower bore

    # STEPPED back axle bore: wide running bore (AXLE_SCREW_R) from the cavity down
    # to AXLE_STOP_Z, then a narrow flood hole (AXLE_FLOOD_R) on through the back wall.
    # The step (annular shoulder at AXLE_STOP_Z) is the rigid -Z stop the dowel shank
    # bottoms on; the narrow hole keeps the socket flooding/draining.
    for (px, py) in AXLE_PIVOTS:
        wz0, wz1 = AXLE_STOP_Z, BACK_BOSS_Z[1] + 1.5    # wide bore: step -> cavity
        body -= Cylinder(radius=AXLE_SCREW_R, height=(wz1 - wz0)).moved(
            Location((px, py, (wz0 + wz1) / 2.0)))
        nz0, nz1 = ENC_Z[0] - 3.0, AXLE_STOP_Z + 0.01   # narrow flood hole through back
        body -= Cylinder(radius=AXLE_FLOOD_R, height=(nz1 - nz0)).moved(
            Location((px, py, (nz0 + nz1) / 2.0)))

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

    # bottom flood/drain holes (axis model -Y); now the housing LOW point. They
    # must pass through BOTH the bottom wall AND the mounting flange below it to
    # reach the outside, so make them full through-holes from cavity floor to the
    # flange outer face. x positions clear the shaft exit (x=DRIVE_X=-12).
    d_y0 = BOT_FLANGE_Y[0] - 2.0
    d_y1 = CAV_Y[0] + 0.5
    for dx in DRAIN_BOTTOM_X:
        for dz in (4.0, 16.0):
            body -= Cylinder(radius=DRAIN_R, height=(d_y1 - d_y0)).moved(
                Location((dx, (d_y0 + d_y1) / 2.0, dz), (1, 0, 0), -90.0))
    for (sy, sz) in DRAIN_SIDE_YZ:
        for sx in (ENC_X[0] + WALL / 2.0, ENC_X[1] - WALL / 2.0):
            body -= Cylinder(radius=DRAIN_R, height=(WALL + 6.0)).moved(
                Location((sx, sy, sz), (0, 1, 0), 90.0))

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
    # axle-boss bores are BLIND drainage/clearance pockets (they do NOT pierce the
    # exposed outer face -> clean front). The dowel head seats on the boss FACE
    # (z=COVER_BOSS_Z[0]); these bores hold nothing. They open to the flooded cavity
    # and stop CHAM_COVER+0.3 short of the outer face so a solid skin remains.
    blind_top = COVER_Z[1] - (CHAM_COVER + 0.3)
    for (px, py) in AXLE_PIVOTS:
        plate -= Cylinder(radius=AXLE_SCREW_R, height=(blind_top - COVER_BOSS_Z[0]) + 0.02).moved(
            Location((px, py, (COVER_BOSS_Z[0] + blind_top) / 2.0)))
    # vent holes through the cover plate (front-up air escape, audit C-6)
    for (vx, vy) in COVER_VENT_XY:
        plate -= Cylinder(radius=COVER_VENT_R, height=(COVER_Z[1] - COVER_Z[0]) + 4.0).moved(
            Location((vx, vy, (COVER_Z[0] + COVER_Z[1]) / 2.0)))
    for clip in _all_snap_clips():
        plate += clip
    plate.label = "front_cover"
    plate.color = COVER_COLOR
    return plate


def _spur_pinion(thickness, label, color):
    """Small spur INPUT PINION as a build123d solid, built with its axis along +Z
    (caller rotates it to model -Y). Pitch radius PINION_RP, straight-flank
    representative teeth (coupon-tunable, matching the model's other gears)."""
    pitch = PINION_RP
    root = pitch - 0.55 * PINION_TOOTH_H
    tip = pitch + 0.45 * PINION_TOOTH_H
    step = 2 * math.pi / PINION_TEETH
    pts = []
    for k in range(PINION_TEETH):
        c = k * step
        for frac, r in ((-0.30, root), (-0.16, tip), (0.16, tip), (0.30, root)):
            aa = c + frac * step
            pts.append((r * math.cos(aa), r * math.sin(aa)))
    return _poly_solid(pts, 0.0, thickness)


def _pinion_spin_deg(open_norm):
    """Pinion rotation about its (model -Y) axis, geared to the crank delta so the
    GIF reads as a real drive: crank turns by `crank_delta`, the crown (rc) turns
    with it, the pinion (rp) turns crank_delta*(rc/rp). Sign chosen so the pinion
    rolls along the crown; flip if it reads wrong on the meshing flank."""
    crank_delta = -(crank_angle_deg(open_norm) - THETA_CLOSED)  # A_L turns -spin
    return -crank_delta * (CROWN_RC / PINION_RP)


def build_input_drive(open_norm):
    """ONE printed part: input PINION integral with the vertical input SHAFT,
    captured collar + coupler. Axis = model -Y (-> world DOWN after +90X reorient).
    Stack (model-Y, +Y is up/cavity, -Y is down/exit):
        pinion        y in PINION_Y          (-9 .. -13)   meshes the crown
        upper journal y in DRIVE_UBORE_Y     (-13.5 .. -15.5)  rides UPPER bore
        CAPTURE COLLAR y in SHAFT_COLLAR_Y   (-15.75 .. -17.75) trapped in POCKET
        lower journal y in DRIVE_LBORE_Y     (-18 .. -25)  rides LOWER bore (load)
        shoulder      y just below the flange (-25 .. -27)  redundant +Y stop
        D-coupler     y below the shoulder    (-27 .. -39)  servo/motor interface
    AXIAL CAPTURE (the known failure point, now solved geometrically): the COLLAR
    (OD SHAFT_COLLAR_R > bore) sits in the housing POCKET between the two journal
    bores and is trapped by both bore-mouth shoulders -> stops BOTH -Y pull-out
    AND +Y push-in, no wobble. (Same head+step idea as the captured axle dowels;
    the pinion itself is too small to act as a stop.) Printed, zero hardware.
    Material PA12-GF (stiff, low-creep) so the journals stay round."""
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

    # --- captured COLLAR in the housing pocket (the primary axial capture) ---
    collar = _cyl_y(SHAFT_COLLAR_R, SHAFT_COLLAR_Y[0], SHAFT_COLLAR_Y[1])

    # --- captured shoulder just below the flange bottom face (+Y push-in stop) ---
    sh_y0 = BOT_FLANGE_Y[0] - SHAFT_SHOULDER_T
    shoulder = _cyl_y(SHAFT_SHOULDER_R, sh_y0, BOT_FLANGE_Y[0] + 0.01)

    # --- D-profile coupler at the very bottom (the actuator interface) ---
    cp_y1 = sh_y0
    cp_y0 = cp_y1 - SHAFT_COUPLER_LEN
    coupler = _cyl_y(SHAFT_COUPLER_R, cp_y0, cp_y1)
    # flat the D on the +X side
    coupler -= Box(SHAFT_DFLAT * 2, SHAFT_COUPLER_LEN + 2, 4 * SHAFT_COUPLER_R).moved(
        Location((SHAFT_COUPLER_R, (cp_y0 + cp_y1) / 2.0, 0)))

    part = pinion + shaft + collar + shoulder + coupler
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

    # followers B->D. Counterbore the D-eye exit (bottom) face so the finger pin
    # (pin_D) lip drops into a rigid confining pocket (geometric capture).
    parts.append(link_bar(R["B"], R["D"], LINK_W, Z_FOLLOW0, T_FOLLOW, "follower_R", STEEL_R,
                          counterbores=[(R["D"], Z_FOLLOW0, SNAP_CB_DEPTH, True)]))
    parts.append(link_bar(L["B"], L["D"], LINK_W, Z_FOLLOW0, T_FOLLOW, "follower_L", STEEL_L,
                          counterbores=[(L["D"], Z_FOLLOW0, SNAP_CB_DEPTH, True)]))

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
            if j in ("C", "D"):    # finger pins: barbed, head caps above finger.
                # The locking lip drops into the rigid confining counterbore cut
                # into the receiving eye's EXIT (bottom) face (C -> crank eye
                # @Z_CRANK0; D -> follower @Z_FOLLOW0). Place the pin so the lip
                # BACK (pull-out) face seats SNAP_CB_FLOOR_CLEAR (0.30 mm) BELOW
                # the pocket shoulder (the wide->narrow step at far+SNAP_CB_DEPTH)
                # -- a real breathing gap so the lip does not bottom out on the
                # shoulder before the shank seats, while the lip still overlaps
                # the shoulder ring (SNAP_CB_R - AXLE_BORE_R wide) for capture.
                #   lip_back(world) = pin_z1 - (L + SEAT) = z1 - ((z1-pin_z0)+SEAT)
                #                   = pin_z0 - SEAT
                #   want lip_back = shoulder - FLOOR_CLEAR = (far+CB_DEPTH) - FLOOR_CLEAR
                #   CB_DEPTH = LIP_T + FLOOR_CLEAR  =>  lip_back = far + LIP_T
                #   so pin_z0 = lip_back + SEAT = far + SNAP_BARB_LIP_T + SNAP_BARB_SEAT
                # (was far + SNAP_CB_DEPTH + SNAP_BARB_SEAT, which left 0 gap.)
                far = Z_CRANK0 if j == "C" else Z_FOLLOW0
                pin_z0 = far + SNAP_BARB_LIP_T + SNAP_BARB_SEAT
                parts.append(snap_pin(pose[j], pin_z0, 23.0, head_at="z1", label=lbl))
            else:                  # axles: plain dowels dropped in from the front,
                                   # SANDWICHED with no slop between the back boss
                                   # (head too wide to pass its bore -> -Z stop) and
                                   # the cover boss (head seats on it -> +Z stop).
                parts.append(snap_pin(pose[j], AXLE_DOWEL_Z0, AXLE_DOWEL_Z1,
                                      head_at="z1", barb=False, label=lbl))

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

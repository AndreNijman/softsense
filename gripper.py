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
OPEN_NORM = float(os.environ.get("GRIPPER_OPEN", "0.5"))
OPEN_NORM = max(0.0, min(1.0, OPEN_NORM))

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

THETA_CLOSED = 104.0   # crank up & slightly inward: jaws nearly touch closed
OPEN_TRAVEL = 46.0     # crank rotates this many deg from closed to full open

# --------------------------------------------------------------------------
# Geometry parameters (mm)
# --------------------------------------------------------------------------
# Z layers (back -> front) so moving parts never share a plane
Z_BASE0, Z_BASE1 = -6.0, 0.0          # base plate slab
T_CRANK = 5.0
Z_CRANK0 = 1.0                        # crank + gear layer
T_FOLLOW = 5.0
Z_FOLLOW0 = 7.0                       # follower layer
T_FINGER = 10.0                      # Fin Ray finger depth in Z (z 13..23)
Z_FINGER0 = 13.0                      # finger layer
Z_PIN0, Z_PIN1 = -6.0, 25.0          # pins span the stack (stay inside housing)
SHAFT_BACK = -34.0                   # input shaft extends to here (behind)

LINK_W = 7.0          # link bar half-look width
PIN_R = 2.3           # pivot pin radius
PIN_HEAD_R = 3.6      # socket-head cap radius
PIN_HEAD_T = 1.2      # cap height (sits ~flush in a counterbore)

# production / printability
PRINT_CLEAR = 0.25    # FDM clearance on moving bores & slots (per side)
AXLE_BORE_R = PIN_R + PRINT_CLEAR   # link/arm rides on its axle with clearance
SHAFT_R = 4.0         # integral input-shaft radius
SHAFT_COUPLER_R = 5.0 # rear coupler radius (D-profile for a servo/motor)
SHAFT_COUPLER_LEN = 12.0
SHAFT_DFLAT = 1.4     # D-flat depth on the coupler

# --- 3D-printed snap-pin geometry (replaces ALL metal pivot pins) ---
SNAP_HEAD_R = PIN_R + 1.6        # flange that stops pull-through
SNAP_HEAD_T = 1.8                # flange thickness (sits OUTSIDE the near face)
SNAP_BARB_PROUD = 0.7            # lip sticks this far past PIN_R (-> r ~3.0)
SNAP_BARB_LIP_T = 1.0            # axial length of the flat locking-lip face
SNAP_BARB_LEAD = 3.0             # length of the tapered lead-in cone
SNAP_TIP_R = 1.0                 # small flat at the very tip (printable)
SNAP_SLOT_W = 1.0                # split-slot width (lets the tip flex)
SNAP_SLOT_LEN = 7.0             # slot depth, measured back from the tip
SNAP_BARB_SEAT = 0.30          # catch face sits this far PAST the far face

GEAR_TEETH = 16
GEAR_TOOTH_H = 3.0    # radial tooth height
GEAR_SECTOR_DEG = 150.0   # gears are sectors, not full discs

# --- Fin Ray finger (TPU compliant jaw) parameters ---
FR_BRACKET_W = 13.0    # mounting-bracket eye diameter
FR_BLADE_LEN = 90.0    # contact beam length, base -> tip
FR_BASE_WIDTH = 22.0   # triangle base width in X
FR_CONTACT_OFFSET = 1.0  # contact face sits this far inboard of the centreline
FR_BASE_DROP = 9.0     # triangle base sits this far below the top pin
FR_WALL = 2.8          # beam / rib wall thickness
FR_TIP_WIDTH = 5.0     # blade width at the blunt tip
FR_N_RIBS = 10         # number of internal ribs (all same-direction slant)
FR_RIB_SLANT_DEG = 38.0
FR_INSET_BASE = 4.0    # solid floor across the bottom
FR_INSET_TIP = 3.0     # solid cap at the apex
MOUNT_HOLE_R = PIN_R + 0.15   # = 2.45 mm pin bore
# grip texture: friction ridges on the contact face (so objects don't slip)
FR_GRIP_DEPTH = 0.6     # ridge protrusion toward the object (mm)
FR_GRIP_PITCH = 2.2     # ridge spacing along the blade length Y (mm)
FR_GRIP_Y0_FRAC = 0.15  # texture starts at this fraction of the blade length
FR_GRIP_Y1_FRAC = 0.95  # texture ends at this fraction of the blade length
FR_GRIP_ROOT_IN = 0.2   # tooth root sits this far INTO the body from the face
FR_GRIP_FLAT = 0.4      # flat valley between teeth (mm)
# print-friendly rounding (FDM TPU, prints flat on the z0 face)
FR_BASE_CHAMFER = 0.5    # bottom-edge (bed face) chamfer: kills elephant-foot
FR_CELL_FILLET = 0.8     # fillet radius on internal rib-cell / spar corners
FR_TIP_FILLET = 1.5      # round the blade tip apex
FR_GRIP_TIP_FLAT = 0.2   # half-height of the flat at each grip-tooth tip

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


def link_bar(p0, p1, width, z0, thickness, label, color):
    """Rounded-end link bar from p0 to p1 (eyes at both ends)."""
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
    # bore the pin holes
    bar -= Cylinder(radius=PIN_R + 0.15, height=thickness * 3).moved(
        Location((p0[0], p0[1], z0 + thickness / 2.0)))
    bar -= Cylinder(radius=PIN_R + 0.15, height=thickness * 3).moved(
        Location((p1[0], p1[1], z0 + thickness / 2.0)))
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


def drive_arm(A, C, spin_deg, z0, thickness, label, color, with_shaft=False):
    """Input link = gear sector fused with the crank arm (one rigid part, so
    no gear-vs-crank clip). Pivots about A; the arm reaches the coupler pin C.
    with_shaft=True adds the integral input shaft + rear D-coupler (this is the
    driven left side); that side's shaft IS the axle, so its hub is left solid.
    The right side has a clearance bore and rides on a separate axle pin."""
    g = gear(A, spin_deg, z0, thickness, label + "_gear", color, bore=not with_shaft)
    arm = link_bar(A, C, LINK_W, z0, thickness, label + "_arm", color)
    part = g + arm
    if with_shaft:
        # integral shaft along -Z (out the back) + D-profile coupler
        sh_len = (z0 + thickness) - SHAFT_BACK
        part += Cylinder(radius=SHAFT_R, height=sh_len).moved(
            Location((A[0], A[1], (SHAFT_BACK + z0 + thickness) / 2.0)))
        coupler = Cylinder(radius=SHAFT_COUPLER_R, height=SHAFT_COUPLER_LEN).moved(
            Location((A[0], A[1], SHAFT_BACK + SHAFT_COUPLER_LEN / 2.0)))
        coupler -= Box(SHAFT_DFLAT * 2, 4 * SHAFT_COUPLER_R, SHAFT_COUPLER_LEN + 2).moved(
            Location((A[0] + SHAFT_COUPLER_R, A[1], SHAFT_BACK + SHAFT_COUPLER_LEN / 2.0)))
        part += coupler
    else:
        # clearance bore so the arm rides on its axle pin
        part -= Cylinder(radius=AXLE_BORE_R, height=thickness * 4).moved(
            Location((A[0], A[1], z0 + thickness / 2.0)))
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
             shank_r=PIN_R):
    """Fully 3D-printed push-to-snap pivot pin (no fasteners). Built in the
    authored frame at XY point p, shank +Z from z0..z1. One end is a HEAD
    flange (stop); the other is a SPLIT, BARBED compliant tip that squeezes
    going in and springs out PAST the far bore face to lock. head_at="z0" ->
    head at low-Z, barb beyond z1; "z1" -> head at high-Z, barb beyond z0."""
    x, y = p
    L = z1 - z0
    barb_max_r = shank_r + SNAP_BARB_PROUD

    head = Cylinder(radius=SNAP_HEAD_R, height=SNAP_HEAD_T).moved(
        Location((0, 0, -SNAP_HEAD_T / 2.0)))
    shank = Cylinder(radius=shank_r, height=L).moved(Location((0, 0, L / 2.0)))

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
    contact_x = -inner_dir * FR_CONTACT_OFFSET
    spine_base_x = contact_x - inner_dir * FR_BASE_WIDTH
    base_y = max(C0[1], D0[1]) - FR_BASE_DROP
    tip_y = base_y + FR_BLADE_LEN
    into = -inner_dir                       # interior direction: contact -> spine

    p_base_spine = (spine_base_x, base_y)
    spine_tip_x = contact_x + into * FR_TIP_WIDTH       # blunt tip on spine side
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

    # hollow it: subtract the inner cavity (leaves contact/spine/base/tip spars)
    cav_contact_x = contact_x + into * FR_WALL
    y_cav_lo = base_y + FR_INSET_BASE

    def cav_spine_x(yy):
        return spine_x_at(yy) - into * FR_WALL

    def cav_w(yy):
        return (cav_spine_x(yy) - cav_contact_x) * into

    MIN_CAV_W = 2.0
    y_cav_hi = tip_y - FR_INSET_TIP
    while y_cav_hi > y_cav_lo and cav_w(y_cav_hi) < MIN_CAV_W:
        y_cav_hi -= 0.5
    cavity = _poly_solid(
        [(cav_contact_x, y_cav_lo), (cav_spine_x(y_cav_lo), y_cav_lo),
         (cav_spine_x(y_cav_hi), y_cav_hi), (cav_contact_x, y_cav_hi)],
        z0 - 2.0, thickness + 4.0)
    finger = shell - cavity

    # add back the slanted parallel ribs (all same slant = Fin Ray signature)
    slant = math.radians(FR_RIB_SLANT_DEG)
    shear = (math.cos(slant) / math.sin(slant)) * into
    y_rib_lo = base_y + FR_INSET_BASE
    y_rib_hi = tip_y - FR_INSET_TIP
    pitch = (y_rib_hi - y_rib_lo) / FR_N_RIBS
    half = FR_WALL / 2.0
    x_a = contact_x + into * 0.3
    ribs = []
    for i in range(FR_N_RIBS + 1):
        yc = y_rib_lo + i * pitch
        x_b = spine_x_at(yc) - into * (FR_WALL * 0.4)
        if (x_b - x_a) * into <= 2.0:
            continue
        quad = [(x_a, yc - half), (x_b, yc - half),
                (x_b + shear * FR_WALL, yc + half), (x_a + shear * FR_WALL, yc + half)]
        try:
            ribs.append(_poly_solid(quad, z0, thickness))
        except Exception:
            pass
    if ribs:
        ribs_all = ribs[0]
        for r in ribs[1:]:
            ribs_all = ribs_all + r
        finger = finger + (ribs_all & blade)        # trim rib ends to the blade

    # --- grip texture ---
    # Fine friction ridges (pliers-style teeth) on the CONTACT face. They run
    # across the finger depth (full Z) and repeat along the blade length (Y),
    # protruding toward the object. Roots sit just inside the contact spar so
    # they fuse cleanly; tips stay clear of the centreline at the closed pose
    # (right finger: contact_x=+1.0, tips at +1.0-0.6 = +0.4 -> 0.8 mm gap).
    grip_root_x = contact_x + into * FR_GRIP_ROOT_IN
    grip_tip_x = contact_x - into * FR_GRIP_DEPTH
    gy0 = base_y + FR_GRIP_Y0_FRAC * FR_BLADE_LEN
    gy1 = base_y + FR_GRIP_Y1_FRAC * FR_BLADE_LEN
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
    # --- end grip texture ---

    # Trim anything that crosses the centreline (just inboard of the tooth tips)
    # so the two opposing fingers can NEVER collide at the closed pose. This
    # clips the inboard side of the C bracket flat without touching the pin bore.
    tooth_tip_x = contact_x - into * FR_GRIP_DEPTH
    keep_x = tooth_tip_x - into * 0.1
    BIG = 600.0
    cut = Box(BIG, BIG, BIG).moved(
        Location((keep_x - into * BIG / 2.0,
                  base_y + FR_BLADE_LEN / 2.0, z0 + thickness / 2.0)))
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
            xin = (c.X - cav_contact_x) * into
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
ENC_Z = (-12.0, 24.0)        # back -> front
WALL = 3.0
TOP_WALL_Y0 = 14.5           # inside face of the thin top wall (y 14.5..16)
CAV_X = (-45.0, 45.0)        # interior clear cavity (holds the mechanism)
CAV_Y = (-17.0, 14.5)
CAV_Z = (-2.0, 22.0)
SLOT_Z = (0.0, 22.0)         # slots cut the full cavity depth in Z
SLOT_R = (2.5, 41.0)         # right top slot x-span (WIDENED so arms clear)
SLOT_L = (-41.0, -2.5)       # left top slot x-span  (WIDENED so arms clear)
SHAFT_C = (-12.0, 0.0)       # shaft bore centre (= A_L)
SHAFT_BORE_R = 5.0
FLANGE_Z = (-16.0, -12.0)    # raised back mounting flange
FLANGE_X = (-42.0, 42.0)
FLANGE_Y = (-18.0, 12.0)
BOLT_R = 2.25                # M4 clearance
BOLT_XY = [(-37.0, -14.0), (37.0, -14.0), (-37.0, 8.0), (37.0, 8.0)]
R_VERT = 4.0
R_TOP = 2.0

# --- underwater drainage / flood holes (so the housing floods & drains) ---
DRAIN_R = 2.5
DRAIN_BOTTOM_X = [-32.0, -16.0, 0.0, 16.0, 32.0]   # bottom-face row (along Y)
DRAIN_SIDE_YZ = [(-14.0, 4.0), (-14.0, 16.0)]      # low side-wall holes (along X)

# --- assembly split: open-front body + bolt-on front cover ---------------
COVER_COLOR = Color(0.33, 0.35, 0.40)   # cover: slightly lighter than ENC
FRONT_WALL_Z = (22.0, 24.0)             # old solid front wall, now removed
AXLE_PIVOTS = [A_R, B_R, mirror_x(B_R)]  # captured-axle pivots (not A_L = shaft)
BOSS_OD_R = 3.5                         # axle boss outer radius (OD ~7)
AXLE_SCREW_R = 1.7                      # M3 axle clearance/self-tap
BACK_BOSS_Z = (-2.0, 1.0)              # back-wall boss into cavity
COVER_BOSS_Z = (20.0, 22.0)            # cover inner-face boss into cavity
BUSH_OD_R = 6.0                         # bushing-seat boss outer radius (OD ~12)
BUSH_BORE_R = 4.4                       # flooded plain-bushing clearance
BUSH_BOSS_Z = (-2.0, 1.0)
CORNER_XY = [(-43.0, -15.0), (43.0, -15.0), (-43.0, 13.0), (43.0, 13.0)]
CORNER_BOSS_R = 3.0                     # screw-boss outer radius
CORNER_TAP_R = 1.35                    # M3 tap (self-tap into body column)
CORNER_CLEAR_R = 1.7                   # M3 clearance hole in the cover
CORNER_BOSS_Z = (-2.0, 22.0)           # (legacy; replaced by snap clips)
COVER_Z = (22.0, 25.0)                 # bolt-on cover plate

# --- snap-clip front cover (tool-free, zero hardware) -------------------
SNAP_Y = [-9.0, 7.0]                 # clip y-centres on each side wall
SNAP_ARM_W = 9.0                     # clip width along Y (flexing beam width)
SNAP_ARM_T = 2.8                     # arm radial thickness (X)
SNAP_GAP = 0.40                      # standoff: arm inner face clears wall outer
SNAP_Z0 = 6.5                        # arm root region near hook (back end)
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
    clip.label = f"snap_clip_{'R' if side > 0 else 'L'}_{yc:+.0f}"
    clip.color = COVER_COLOR
    return clip


def _all_snap_clips():
    return [_one_clip(side, yc) for side in (+1, -1) for yc in SNAP_Y]


def build_enclosure():
    """Hollow flooded gearbox housing (underwater), SPLIT for assembly: open
    front so the mechanism drops in; the snap-clip cover supports the far axle
    ends. Keeps the cavity, two top slots, back flange + M4 holes, A_L shaft
    bore + bushing seat, captured-axle bosses, and all drain/flood holes. The
    4 corner screw bosses are REPLACED by snap-clip catch windows in the long
    side walls (zero hardware, tool-free cover)."""
    body = _box_between(*ENC_X, *ENC_Y, *ENC_Z)
    body = fillet(body.edges().filter_by(Axis.Y), radius=R_VERT)
    top_edges = body.edges().filter_by(Axis.Y, reverse=True).group_by(Axis.Y)[-1]
    body = fillet(top_edges, radius=R_TOP)
    body -= _box_between(*CAV_X, *CAV_Y, *CAV_Z)
    body -= _box_between(CAV_X[0], CAV_X[1], CAV_Y[0], CAV_Y[1],
                         FRONT_WALL_Z[0] - 0.5, ENC_Z[1] + 1.0)
    body -= _box_between(SLOT_R[0], SLOT_R[1], TOP_WALL_Y0 - 1.0, ENC_Y[1] + 1.0,
                         SLOT_Z[0] - 0.5, SLOT_Z[1] + 0.5)
    body -= _box_between(SLOT_L[0], SLOT_L[1], TOP_WALL_Y0 - 1.0, ENC_Y[1] + 1.0,
                         SLOT_Z[0] - 0.5, SLOT_Z[1] + 0.5)
    flange = _box_between(*FLANGE_X, *FLANGE_Y, *FLANGE_Z)
    flange = fillet(flange.edges().filter_by(Axis.Z), radius=R_VERT)
    body += flange

    for (px, py) in AXLE_PIVOTS:
        body += Cylinder(radius=BOSS_OD_R, height=(BACK_BOSS_Z[1] - BACK_BOSS_Z[0])).moved(
            Location((px, py, (BACK_BOSS_Z[0] + BACK_BOSS_Z[1]) / 2.0)))
    body += Cylinder(radius=BUSH_OD_R, height=(BUSH_BOSS_Z[1] - BUSH_BOSS_Z[0])).moved(
        Location((SHAFT_C[0], SHAFT_C[1], (BUSH_BOSS_Z[0] + BUSH_BOSS_Z[1]) / 2.0)))

    for e in body.edges().filter_by(GeomType.CIRCLE):
        if abs(e.center().Z - CAV_Z[0]) < 0.05:
            try:
                body = fillet([e], radius=0.8)
            except Exception:
                pass

    bz0, bz1 = FLANGE_Z[0] - 2.0, CAV_Z[0]
    body -= Cylinder(radius=SHAFT_BORE_R, height=(bz1 - bz0)).moved(
        Location((SHAFT_C[0], SHAFT_C[1], (bz0 + bz1) / 2.0)))
    body -= Cylinder(radius=BUSH_BORE_R, height=(BUSH_BOSS_Z[1] - CAV_Z[0]) + 4.0).moved(
        Location((SHAFT_C[0], SHAFT_C[1], (CAV_Z[0] - 2.0 + BUSH_BOSS_Z[1]) / 2.0)))

    for (px, py) in AXLE_PIVOTS:
        body -= Cylinder(radius=AXLE_SCREW_R, height=(BACK_BOSS_Z[1] - ENC_Z[0]) + 6.0).moved(
            Location((px, py, (ENC_Z[0] - 3.0 + BACK_BOSS_Z[1]) / 2.0)))

    # snap-clip catch windows: a through-window in each long side wall so the
    # cover's hook latches behind the window's top edge (also act as drains).
    for side in (+1, -1):
        for yc in SNAP_Y:
            wx_lo, wx_hi = sorted((side * (ENC_X[1] - WALL - 2.0),
                                   side * (ENC_X[1] + 2.0)))
            body -= _box_between(wx_lo, wx_hi,
                                 yc - SNAP_WIN_DY / 2.0, yc + SNAP_WIN_DY / 2.0,
                                 SNAP_WIN_Z[0], SNAP_WIN_Z[1])

    for (bx, by) in BOLT_XY:
        body -= Cylinder(radius=BOLT_R, height=(FLANGE_Z[1] - FLANGE_Z[0]) + 4.0).moved(
            Location((bx, by, (FLANGE_Z[0] + FLANGE_Z[1]) / 2.0)))

    for dx in DRAIN_BOTTOM_X:
        body -= Cylinder(radius=DRAIN_R, height=(WALL + 6.0)).moved(
            Location((dx, ENC_Y[0] + WALL / 2.0, 10.0), (1, 0, 0), 90.0))
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
    for (px, py) in AXLE_PIVOTS:
        plate += Cylinder(radius=BOSS_OD_R, height=(COVER_BOSS_Z[1] - COVER_BOSS_Z[0])).moved(
            Location((px, py, (COVER_BOSS_Z[0] + COVER_BOSS_Z[1]) / 2.0)))
    for e in plate.edges().filter_by(GeomType.CIRCLE):
        if abs(e.center().Z - COVER_Z[0]) < 0.05:
            try:
                plate = fillet([e], radius=0.8)
            except Exception:
                pass
    for (px, py) in AXLE_PIVOTS:
        plate -= Cylinder(radius=AXLE_SCREW_R, height=(COVER_Z[1] - COVER_BOSS_Z[0]) + 4.0).moved(
            Location((px, py, (COVER_BOSS_Z[0] + COVER_Z[1]) / 2.0)))
    for clip in _all_snap_clips():
        plate += clip
    plate.label = "front_cover"
    plate.color = COVER_COLOR
    return plate


# --------------------------------------------------------------------------
# Drive shaft (coaxial with the LEFT crank pivot A_L; the input you rotate)
# --------------------------------------------------------------------------
def drive_shaft():
    aL = mirror_x(A_R)
    shaft = Cylinder(radius=PIN_R + 1.2, height=(Z_CRANK0 + T_CRANK) - SHAFT_BACK)
    zc = (SHAFT_BACK + (Z_CRANK0 + T_CRANK)) / 2.0
    shaft = shaft.moved(Location((aL[0], aL[1], zc)))
    # knurl-ish drive knob at the back
    knob = Cylinder(radius=6.0, height=8.0).moved(
        Location((aL[0], aL[1], SHAFT_BACK + 4.0)))
    # flat on the knob to signal "rotate here"
    knob -= Box(2.0, 14, 10).moved(Location((aL[0] + 4.0, aL[1], SHAFT_BACK + 4.0)))
    s = shaft + knob
    s.label = "drive_shaft"
    s.color = DARK
    return s


# ==========================================================================
# Assembly
# ==========================================================================
def gen_step():
    refR, refL = solve_side_right(0.0), solve_side_left(0.0)
    R, L = solve_side_right(OPEN_NORM), solve_side_left(OPEN_NORM)
    parts = []

    parts.append(build_enclosure())

    # Drive arms = gear sector fused with crank arm (one part -> no gear/crank
    # clip). The LEFT arm is driven by its integral input shaft (out the back);
    # the gear mesh counter-rotates the RIGHT arm -> one shaft moves both jaws.
    half_tooth = 360.0 / GEAR_TEETH / 2.0
    spin = crank_angle_deg(OPEN_NORM) - THETA_CLOSED      # crank rotation
    parts.append(drive_arm(R["A"], R["C"], spin, Z_CRANK0, T_CRANK,
                           "drive_arm_R", STEEL_R, with_shaft=False))
    parts.append(drive_arm(L["A"], L["C"], -spin + half_tooth, Z_CRANK0, T_CRANK,
                           "drive_arm_L", STEEL_L, with_shaft=True))

    # followers B->D
    parts.append(link_bar(R["B"], R["D"], LINK_W, Z_FOLLOW0, T_FOLLOW, "follower_R", STEEL_R))
    parts.append(link_bar(L["B"], L["D"], LINK_W, Z_FOLLOW0, T_FOLLOW, "follower_L", STEEL_L))

    # Fin Ray fingers (TPU) rigid with coupler CD
    parts.append(finger(R, refR, -1, TPU, "finger_R"))
    parts.append(finger(L, refL, +1, TPU, "finger_L"))

    # axle pins: A_R (right-arm axle), B_R, B_L (follower axles) are hidden
    # internal axles; C/D finger pins are visible. The LEFT arm's axle is its
    # integral shaft, so there is no pin_A_L.
    for tag, pose, joints in (("R", R, ("A", "B", "C", "D")),
                              ("L", L, ("B", "C", "D"))):
        for j in joints:
            lbl = f"pin_{j}_{tag}"
            if j in ("C", "D"):    # finger pins: head caps above the finger
                parts.append(snap_pin(pose[j], 0.0, 23.0, head_at="z1", label=lbl))
            else:                  # internal axles: head at back, barb at cover
                parts.append(snap_pin(pose[j], -2.0, 22.0, head_at="z0", label=lbl))

    # bolt-on front cover LAST so existing occurrence ids stay stable
    parts.append(build_front_cover())

    asm = Compound(label="gripper", children=parts)
    # reorient to Z-up for printing & viewing: fingers point +Z, the input
    # shaft exits the back horizontally (+Y). (Model is authored Y-up.)
    asm = asm.moved(Location((0, 0, 0), (1, 0, 0), 90))
    return asm


# ==========================================================================
# Numeric self-check
# ==========================================================================
def _tip_world(side_pose, ref_pose):
    C0 = ref_pose["C"]
    a0 = ref_pose["coupler_ang"]
    tip0 = (C0[0], C0[1] + FR_BLADE_LEN)
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

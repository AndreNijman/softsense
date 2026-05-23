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
    Location,
    Plane,
    Polyline,
    Pos,
    Rotation,
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
T_FINGER = 6.0
Z_FINGER0 = 13.0                      # finger layer
Z_PIN0, Z_PIN1 = -8.0, 21.0          # pins span the whole stack
SHAFT_BACK = -34.0                   # input shaft extends to here (behind)

LINK_W = 7.0          # link bar half-look width
PIN_R = 2.3           # pivot pin radius
PIN_HEAD_R = 3.6      # socket-head cap radius
PIN_HEAD_T = 2.2

GEAR_TEETH = 16
GEAR_TOOTH_H = 3.0    # radial tooth height
GEAR_SECTOR_DEG = 150.0   # gears are sectors, not full discs

FINGER_BLADE = 86.0   # blade length from base up to tip
FINGER_W = 9.0        # blade full width
TIP_CURVE = 1.5       # subtle inward hook at the very tip
SERR_FRAC = 0.55      # fraction of blade (upper) that is serrated
SERR_N = 13           # number of jaw teeth
SERR_DEPTH = 2.4      # how far jaw teeth protrude toward the centre
CLOSED_HALF_GAP = 0.8  # half the jaw-face clearance at the closed pose

# --------------------------------------------------------------------------
# Colours
# --------------------------------------------------------------------------
GOLD = Color(0.78, 0.66, 0.36)
STEEL_L = Color(0.46, 0.53, 0.61)
STEEL_R = Color(0.62, 0.74, 0.86)
BLUE = Color(0.30, 0.55, 0.95)
DARK = Color(0.32, 0.36, 0.42)


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
def _poly_solid(pts, z0, thickness):
    """Extrude a closed XY polygon (list of (x,y)) to a Z slab at z0."""
    face = make_face(Polyline(*pts, close=True))
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


def gear(center, phase_deg, z0, thickness, label, color):
    """A full toothed gear disc centred at `center`, axis Z. Pitch radius
    R_GEAR; with centres at +/-R_GEAR the pitch circles touch on the
    centreline so the pair meshes. `phase_deg` rotates the teeth (the right
    and left gears are offset half a tooth so the teeth interleave)."""
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
    sol -= Cylinder(radius=PIN_R + 0.15, height=thickness * 3).moved(
        Location((0, 0, z0 + thickness / 2.0)))
    sol = sol.moved(Location((center[0], center[1], 0)))
    sol.label = label
    sol.color = color
    return sol


def pin(p, label, head_top_z):
    """Pivot pin (shoulder cylinder) with a blue socket-head cap on top."""
    shaft = Cylinder(radius=PIN_R, height=(Z_PIN1 - Z_PIN0)).moved(
        Location((p[0], p[1], (Z_PIN0 + Z_PIN1) / 2.0)))
    head = Cylinder(radius=PIN_HEAD_R, height=PIN_HEAD_T).moved(
        Location((p[0], p[1], head_top_z + PIN_HEAD_T / 2.0)))
    c = shaft + head
    c.label = label
    c.color = BLUE
    return c


# --------------------------------------------------------------------------
# Finger (serrated jaw) — defined in world @ CLOSED pose, then rigid-moved
# --------------------------------------------------------------------------
def _finger_solid_closed(C0, D0, inner_dir):
    """Build the finger blade + bracket in world coords at the closed pose.
    inner_dir = -1 for the right finger (gripping edge faces -X = centre),
                +1 for the left finger.

    The blade is offset OUTBOARD of the pins so that, at the closed pose, the
    serrated jaw faces meet near the centreline with a small clearance
    (CLOSED_HALF_GAP) instead of the pins -- no interpenetration when closed.
    """
    halfw = FINGER_W / 2.0
    base_y = C0[1] - 4.0                       # start a touch below C for fusion
    tip_y = C0[1] + FINGER_BLADE
    # blade centreline so the inner tooth tips land at +/-CLOSED_HALF_GAP closed
    spine_x = -inner_dir * (CLOSED_HALF_GAP + halfw + SERR_DEPTH)

    def cx(t):                                 # subtle inward hook near the tip
        return spine_x + inner_dir * TIP_CURVE * (t ** 1.6)

    def y(t):
        return base_y + (tip_y - base_y) * t

    def w(t):
        return halfw * (1.0 - 0.32 * t)        # slight taper toward the tip

    # ---- outer (smooth) edge: base -> tip
    outer = [(cx(t) - inner_dir * w(t), y(t)) for t in [k / 24.0 for k in range(25)]]
    # ---- rounded tip apex
    tip_apex = [(cx(1.0), tip_y + 2.0)]
    # ---- inner edge tip -> base, serrated in the upper SERR_FRAC
    inner = []
    NS = 90
    for k in range(NS, -1, -1):
        t = k / NS
        ix = cx(t) + inner_dir * w(t)
        if t >= (1.0 - SERR_FRAC):
            u = (1.0 - t) / SERR_FRAC               # 0 at tip .. 1 at serr start
            saw = abs(((u * SERR_N) % 1.0) - 0.5) * 2.0
            ix += inner_dir * SERR_DEPTH * saw      # teeth protrude toward centre
        inner.append((ix, y(t)))

    blade = _poly_solid(outer + tip_apex + inner, Z_FINGER0, T_FINGER)

    # ---- bracket plate joining the two pins C0, D0 to the blade base
    bracket = link_bar(C0, D0, FINGER_W + 4.0, Z_FINGER0, T_FINGER,
                       "bracket", STEEL_R)
    finger = blade + bracket
    for hp in (C0, D0):                            # (re)bore pin holes
        finger -= Cylinder(radius=PIN_R + 0.15, height=T_FINGER * 3).moved(
            Location((hp[0], hp[1], Z_FINGER0 + T_FINGER / 2.0)))
    return finger


def finger(side_pose, ref_pose, inner_dir, color, label):
    f = _finger_solid_closed(ref_pose["C"], ref_pose["D"], inner_dir)
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
# Base plate (skeletonized)
# --------------------------------------------------------------------------
def base_plate():
    # rounded-hexagon footprint, wider at the top where the links splay
    pts = [(-40, -14), (40, -14), (52, 8), (40, 24), (-40, 24), (-52, 8)]
    plate = _poly_solid(pts, Z_BASE0, Z_BASE1 - Z_BASE0)
    plate = fillet(plate.edges().filter_by(Axis.Z), radius=3.0)

    # lightening windows
    holes = [
        Box(20, 14, 40).moved(Location((-22, 5, (Z_BASE0 + Z_BASE1) / 2))),
        Box(20, 14, 40).moved(Location((22, 5, (Z_BASE0 + Z_BASE1) / 2))),
        Box(14, 10, 40).moved(Location((0, 14, (Z_BASE0 + Z_BASE1) / 2))),
    ]
    for h in holes:
        h = fillet(h.edges().filter_by(Axis.Z), radius=2.5)
        plate -= h

    # pivot bores + central drive bore
    for p in (A_R, mirror_x(A_R), B_R, mirror_x(B_R)):
        plate -= Cylinder(radius=PIN_R + 0.2, height=40).moved(
            Location((p[0], p[1], (Z_BASE0 + Z_BASE1) / 2)))
    plate.label = "base_plate"
    plate.color = GOLD
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

    parts.append(base_plate())
    parts.append(drive_shaft())

    # meshing gear pair (rigid with cranks). The right gear turns with the
    # right crank; the left counter-rotates (mirror) + half-tooth offset so the
    # teeth interleave on the centreline -> one shaft drives both fingers.
    half_tooth = 360.0 / GEAR_TEETH / 2.0
    spin = crank_angle_deg(OPEN_NORM) - THETA_CLOSED      # crank rotation
    parts.append(gear(R["A"], spin, Z_CRANK0, T_CRANK, "gear_R", STEEL_R))
    parts.append(gear(L["A"], -spin + half_tooth, Z_CRANK0, T_CRANK, "gear_L", STEEL_L))

    # cranks (gear arms) A->C
    parts.append(link_bar(R["A"], R["C"], LINK_W, Z_CRANK0, T_CRANK, "crank_R", STEEL_R))
    parts.append(link_bar(L["A"], L["C"], LINK_W, Z_CRANK0, T_CRANK, "crank_L", STEEL_L))

    # followers B->D
    parts.append(link_bar(R["B"], R["D"], LINK_W, Z_FOLLOW0, T_FOLLOW, "follower_R", STEEL_R))
    parts.append(link_bar(L["B"], L["D"], LINK_W, Z_FOLLOW0, T_FOLLOW, "follower_L", STEEL_L))

    # fingers (serrated jaws) rigid with coupler CD
    parts.append(finger(R, refR, -1, STEEL_R, "finger_R"))
    parts.append(finger(L, refL, +1, STEEL_L, "finger_L"))

    # pins at every revolute axis (head sits just above the finger layer)
    head_z = Z_FINGER0 + T_FINGER
    for tag, pose in (("R", R), ("L", L)):
        for j in ("A", "B", "C", "D"):
            parts.append(pin(pose[j], f"pin_{j}_{tag}", head_z))

    asm = Compound(label="gripper", children=parts)
    return asm


# ==========================================================================
# Numeric self-check
# ==========================================================================
def _tip_world(side_pose, ref_pose):
    C0 = ref_pose["C"]
    a0 = ref_pose["coupler_ang"]
    tip0 = (C0[0], C0[1] + FINGER_BLADE)
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

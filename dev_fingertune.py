"""Dev harness: isolate the Fin Ray finger and iterate on printability
fillets/chamfers. Copies the relevant deps + finray_finger_closed from
gripper.py. Builds right+left fingers as a Compound for STEP export.
"""
from __future__ import annotations

import math

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

# ---- constants copied from gripper.py (only what the finger needs) ----
PIN_R = 2.3
LINK_W = 7.0
T_FINGER = 10.0
Z_FINGER0 = 13.0
TPU = Color(0.12, 0.13, 0.15)

FR_BRACKET_W = 13.0
FR_BLADE_LEN = 90.0
FR_BASE_WIDTH = 22.0
FR_CONTACT_OFFSET = 1.0
FR_BASE_DROP = 9.0
FR_WALL = 2.8
FR_TIP_WIDTH = 5.0
FR_N_RIBS = 10
FR_RIB_SLANT_DEG = 38.0
FR_INSET_BASE = 4.0
FR_INSET_TIP = 3.0
MOUNT_HOLE_R = PIN_R + 0.15
FR_GRIP_DEPTH = 0.6
FR_GRIP_PITCH = 2.2
FR_GRIP_Y0_FRAC = 0.15
FR_GRIP_Y1_FRAC = 0.95
FR_GRIP_ROOT_IN = 0.2
FR_GRIP_FLAT = 0.4

# --- print-friendly rounding (NEW) ---
FR_BASE_CHAMFER = 0.5    # bottom-edge (bed face) chamfer: kills elephant-foot
FR_CELL_FILLET = 0.8     # fillet radius on internal rib-cell / spar corners
FR_TIP_FILLET = 1.5      # round the blade tip apex
FR_GRIP_TIP_FLAT = 0.2   # half-height of the flat at each grip-tooth tip


# ---- helpers copied from gripper.py ----
def _ccw(pts):
    area = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return pts if area >= 0 else list(reversed(pts))


def _poly_solid(pts, z0, thickness):
    face = make_face(Polyline(*_ccw(pts), close=True))
    sol = extrude(face, amount=thickness)
    return sol.moved(Location((0, 0, z0)))


def link_bar(p0, p1, width, z0, thickness, label, color):
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    L = math.hypot(dx, dy)
    ang = math.degrees(math.atan2(dy, dx))
    body = Box(L, width, thickness).moved(Location((L / 2.0, 0, 0)))
    eye0 = Cylinder(radius=width / 2.0, height=thickness)
    eye1 = Cylinder(radius=width / 2.0, height=thickness).moved(Location((L, 0, 0)))
    bar = body + eye0 + eye1
    bar = bar.moved(Location((0, 0, z0 + thickness / 2.0)))
    bar = bar.moved(Location((p0[0], p0[1], 0), (0, 0, 1), ang))
    bar -= Cylinder(radius=PIN_R + 0.15, height=thickness * 3).moved(
        Location((p0[0], p0[1], z0 + thickness / 2.0)))
    bar -= Cylinder(radius=PIN_R + 0.15, height=thickness * 3).moved(
        Location((p1[0], p1[1], z0 + thickness / 2.0)))
    bar.label = label
    bar.color = color
    return bar


def _safe_round(part, edges, radius, op):
    """Robustly fillet/chamfer a set of edges. build123d's fillet/chamfer are
    FREE functions: op(edges, radius) -> NEW Part (parent solid inferred from
    the edges). They are fragile on complex booleans -- a bulk call fails if
    ANY edge is unroundable.

    Strategy: try the cheap bulk call first; if it raises, fall back to
    per-edge. In the fallback the part is a fresh object after every op, so the
    original edge references go stale -- we RE-RESOLVE each target by matching
    its (center, length) against the live part each pass. One bad edge can't
    abort the build; every good edge still rounds."""
    if not edges:
        return part
    try:
        return op(edges, radius)
    except Exception:
        pass
    # per-edge fallback with re-resolution
    targets = [(e.center(), e.length) for e in edges]
    for (tc, tl) in targets:
        best, best_d = None, 0.5   # 0.5mm tol: loose enough after neighbour moves
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

    Print-friendly rounding (FDM TPU, ~0.2mm layers, prints flat on the z0
    face): bottom-edge chamfer kills elephant-foot, internal rib-cell corners
    are filleted to relieve TPU stress concentrations, grip-tooth tips and the
    blade apex are rounded so they aren't fragile knife-edges. The part is a
    2.5D extrusion along Z, so none of this introduces a Z-direction overhang."""
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
    # Fine friction ridges (pliers-style teeth) on the CONTACT face. Tooth tips
    # are a tiny FLAT (4-pt trapezoid, not a 3-pt knife-edge) so they print
    # cleanly and grip better without being fragile. Solving the round in 2D
    # here avoids fragile 3D fillets on dozens of tiny tooth edges.
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
        # blunt the apex into a small flat of half-height FR_GRIP_TIP_FLAT
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

    # ======================================================================
    # PRINT-FRIENDLY FILLETS & CHAMFERS  (applied last, after all booleans)
    # ----------------------------------------------------------------------
    # The finger is a pure extrusion in Z (z0 .. z0+thickness). Edge classes:
    #   * vertical edges (parallel to Axis.Z, length ~= thickness) = the XY
    #     corners of the truss -> fillet the internal cell corners here.
    #   * planar edges at Z=z0 (bottom/bed face) and Z=z0+thickness (top) =
    #     the print-direction caps -> chamfer the bottom for elephant-foot.
    # Selectors are conservative (Axis + position + length) and every op is
    # wrapped per-edge so a single bad edge can't abort the build.
    # ======================================================================
    z_top = z0 + thickness

    # (2) Fillet internal rib-cell / spar-junction corners. Select VERTICAL
    # edges whose XY centre falls inside the hollow cavity footprint -- these
    # are exactly the inner truss corners where TPU Fin Ray fingers crack.
    # Skip the contact face (x at/inboard of cav_contact_x) and the mount-hole
    # bores so we don't touch the grip teeth or the kinematic pins.
    # Band spans the cavity INCLUDING its contact & spine walls (tol 0.5) so we
    # catch the rib<->spine and rib<->contact junctions -- the corners where TPU
    # Fin Ray fingers actually crack -- not just the strictly-interior ones. The
    # grip teeth (well inboard of the contact wall, xin <~ -2.6) are excluded by
    # xin >= -0.5; the spine outer perimeter is excluded by xout >= -0.5.
    # Non-corner edges that happen to fall in the band are harmless: fillet just
    # skips them (per-edge try/except in _safe_round).
    cell_edges = []
    for e in finger.edges().filter_by(Axis.Z):
        try:
            if abs(e.length - thickness) > 0.25:
                continue
            c = e.center()
            yy = c.Y
            if not (y_cav_lo - 0.5 < yy < y_cav_hi + 0.5):
                continue
            # within the cavity X-band (contact wall .. spine wall, incl. walls)
            xin = (c.X - cav_contact_x) * into
            xout = (cav_spine_x(yy) - c.X) * into
            if xin < -0.5 or xout < -0.5:
                continue
            # keep clear of the mount-hole bores
            if any(math.hypot(c.X - hp[0], c.Y - hp[1]) < MOUNT_HOLE_R + 0.6
                   for hp in (C0, D0)):
                continue
            cell_edges.append(e)
        except Exception:
            pass
    finger = _safe_round(finger, cell_edges, FR_CELL_FILLET, fillet)

    # (4) Round the tip apex of the blade: the two vertical edges at the blunt
    # tip's top corners (contact_x, tip_y) and (spine_tip_x, tip_y).
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

    # (1) Chamfer the BOTTOM (bed) face edges at Z=z0 to kill elephant-foot.
    # Select planar edges lying in the z0 plane (their centre Z ~= z0). A
    # chamfer over a 0.5mm rise is a 45-deg feature -> still printable.
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


# ---- minimal kinematics to get the closed-pose C/D points ----
R_GEAR = 12.0
A_R = (R_GEAR, 0.0)
B_R = (26.0, 10.0)
R_CRANK = 34.0
R_FOLLOW = 32.0
R_COUPLER = 20.0
THETA_CLOSED = 104.0


def mirror_x(p):
    return (-p[0], p[1])


def circle_intersect_both(c0, r0, c1, r1):
    dx = c1[0] - c0[0]
    dy = c1[1] - c0[1]
    d = math.hypot(dx, dy)
    a = (r0 * r0 - r1 * r1 + d * d) / (2.0 * d)
    h = math.sqrt(max(0.0, r0 * r0 - a * a))
    xm = c0[0] + a * dx / d
    ym = c0[1] + a * dy / d
    px = -dy / d
    py = dx / d
    return [(xm + h * px, ym + h * py), (xm - h * px, ym - h * py)]


def _crank_point(open_norm):
    theta = math.radians(THETA_CLOSED)
    return (A_R[0] + R_CRANK * math.cos(theta), A_R[1] + R_CRANK * math.sin(theta))


def solve_closed_right():
    C0 = _crank_point(0.0)
    d_par = (B_R[0] + (C0[0] - A_R[0]) * (R_FOLLOW / R_CRANK),
             B_R[1] + (C0[1] - A_R[1]) * (R_FOLLOW / R_CRANK))
    cands = circle_intersect_both(C0, R_COUPLER, B_R, R_FOLLOW)
    D = min(cands, key=lambda p: (p[0] - d_par[0]) ** 2 + (p[1] - d_par[1]) ** 2)
    return {"C": C0, "D": D}


def gen_step():
    R = solve_closed_right()
    Cr, Dr = R["C"], R["D"]
    Cl, Dl = mirror_x(Cr), mirror_x(Dr)
    fr = finray_finger_closed(Cr, Dr, -1, Z_FINGER0, T_FINGER)
    fr.label = "finger_R"
    fr.color = TPU
    fl = finray_finger_closed(Cl, Dl, +1, Z_FINGER0, T_FINGER)
    fl.label = "finger_L"
    fl.color = TPU
    asm = Compound(label="fingers", children=[fr, fl])
    asm = asm.moved(Location((0, 0, 0), (1, 0, 0), 90))
    return asm

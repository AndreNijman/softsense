"""
dev_snapcover.py -- iteration harness for the tool-free SNAP-CLIP front cover.

Replaces the 4 corner bolt-on screws of the gripper's front cover with integral
3D-printed cantilever snap clips (zero hardware). This file does NOT edit
gripper.py: it imports the constants/helpers it needs and re-defines the two
target functions (build_enclosure / build_front_cover) locally for fast iterate.

Run:
    cd /home/andre/gripper-cad
    source /home/andre/.cad-venv/bin/activate
    python dev_snapcover.py

Produces:
    dev_snapcover_assembled.step   (enclosure + snapped-on cover)
    dev_snapcover_exploded.step    (cover lifted +Z to show the clips)
"""
from __future__ import annotations

import os

os.environ.setdefault("GRIPPER_OPEN", "0")

from build123d import (  # noqa: E402
    Axis,
    Box,
    Color,
    Compound,
    Cylinder,
    GeomType,
    Location,
    Pos,
    export_gltf,
    export_step,
    fillet,
)

import gripper as G  # noqa: E402

# ==========================================================================
# Pull in the constants we depend on from gripper.py (single source of truth)
# ==========================================================================
ENC_X, ENC_Y, ENC_Z = G.ENC_X, G.ENC_Y, G.ENC_Z
WALL = G.WALL
CAV_X, CAV_Y, CAV_Z = G.CAV_X, G.CAV_Y, G.CAV_Z
SLOT_Z, SLOT_R, SLOT_L = G.SLOT_Z, G.SLOT_R, G.SLOT_L
TOP_WALL_Y0 = G.TOP_WALL_Y0
SHAFT_C, SHAFT_BORE_R = G.SHAFT_C, G.SHAFT_BORE_R
FLANGE_X, FLANGE_Y, FLANGE_Z = G.FLANGE_X, G.FLANGE_Y, G.FLANGE_Z
BOLT_R, BOLT_XY = G.BOLT_R, G.BOLT_XY
R_VERT, R_TOP = G.R_VERT, G.R_TOP
DRAIN_R, DRAIN_BOTTOM_X, DRAIN_SIDE_YZ = G.DRAIN_R, G.DRAIN_BOTTOM_X, G.DRAIN_SIDE_YZ
COVER_COLOR = G.COVER_COLOR
FRONT_WALL_Z = G.FRONT_WALL_Z
AXLE_PIVOTS = G.AXLE_PIVOTS
BOSS_OD_R = G.BOSS_OD_R
AXLE_SCREW_R = G.AXLE_SCREW_R
BACK_BOSS_Z = G.BACK_BOSS_Z
COVER_BOSS_Z = G.COVER_BOSS_Z
BUSH_OD_R, BUSH_BORE_R, BUSH_BOSS_Z = G.BUSH_OD_R, G.BUSH_BORE_R, G.BUSH_BOSS_Z
COVER_Z = G.COVER_Z
ENC = G.ENC
_box_between = G._box_between

# ==========================================================================
# NEW: snap-clip constants  (authored Y-up frame; cover is the front face Z=22..25)
# ==========================================================================
# 4 cantilever clips, 2 per LONG side wall (the X = +/-48 walls, 96 mm long in Y).
# Arms are integral to the COVER, hang back (-Z) OUTSIDE the body side wall, and
# end in inward hooks that snap through a through-window in the 3 mm side wall.
# The top wall (Y 14.5..16) is only 1.5 mm thick -> never put a clip there.
SNAP_Y = [-9.0, 7.0]                 # clip y-centres on each side wall
SNAP_ARM_W = 9.0                     # clip width along Y (the flexing beam width)
SNAP_ARM_T = 2.8                     # arm radial thickness (X), prints easily
SNAP_GAP = 0.40                      # standoff: arm inner face clears wall outer
SNAP_Z0 = 6.5                        # arm root region near hook (back end)
SNAP_HOOK_Z = (7.0, 10.0)            # hook lip Z-span (engages window TOP edge)
SNAP_HOOK_ENGAGE = 1.5               # how far the hook reaches inward past wall
SNAP_CLEAR = 0.35                    # engagement clearance (hook top -> window top)
SNAP_LEADIN = 2.0                    # lead-in chamfer run (Z) at hook back end
# window in the body side wall (through-cut). Sized to hug the hook lip with
# SNAP_CLEAR all round so the latch is TIGHT (minimal cover lift before the
# hook's upper face catches the window's upper edge on pull-out).
SNAP_WIN_Z = (SNAP_HOOK_Z[0] - SNAP_CLEAR, SNAP_HOOK_Z[1] + SNAP_CLEAR)  # 6.65 .. 10.35
SNAP_WIN_DY = 11.0                   # window length along Y (clears arm width)

# arm geometry in X (right side; mirror for left)
_WALL_OUT_R = ENC_X[1]               # +48 outer face of right wall
_ARM_IN_R = _WALL_OUT_R + SNAP_GAP   # 48.40 inner face of the arm
_ARM_OUT_R = _ARM_IN_R + SNAP_ARM_T  # 51.20 outer face of the arm
# hook tip reaches INWARD into the 3 mm wall (x 45..48), engaging it behind the
# window edge. Tip at 46.5 = 1.5 mm into the wall, still OUTSIDE the cavity-clear
# region (x<=45), so the mechanism space stays clear.
_HOOK_TIP_R = ENC_X[1] - SNAP_HOOK_ENGAGE
# arm top overlaps INTO the cover plate (z 22..25) by 1 mm so the union fuses
# into a single solid (coincident faces alone don't merge in OCC).
SNAP_ARM_Z1 = COVER_Z[0] + 1.0


def _snap_clip(side):
    """One cantilever snap clip as a build123d solid in world coords (Y-up).
    `side`=+1 right wall (x=+48), -1 left wall. The clip is built per y-centre
    in _all_snap_clips; this returns the union for a single y-centre via closure.
    (kept as a thin builder; the loop lives in _all_snap_clips)."""
    raise NotImplementedError


def _one_clip(side, yc):
    """Build a single cantilever clip (arm + hook) for one side & y-centre.
    Right side (+1): arm sits OUTSIDE the +X wall, hook points -X (inward).
    Left side (-1): mirror.  Returns a solid in world coordinates."""
    s = side
    arm_in = s * _ARM_IN_R     # inner face of arm (toward body), standoff gap
    arm_out = s * _ARM_OUT_R   # outer face of arm
    x_lo, x_hi = sorted((arm_in, arm_out))
    # ---- cantilever arm: a slab from hook region up to the cover face. The arm
    # stands off the body wall by SNAP_GAP so it can flex outward when latching.
    arm = _box_between(x_lo, x_hi, yc - SNAP_ARM_W / 2.0, yc + SNAP_ARM_W / 2.0,
                       SNAP_Z0, COVER_Z[0])
    # ---- ROOT block: bridges the standoff gap to the cover plate edge (x=+/-48)
    # and overlaps INTO the plate (z 22..23) so the union fuses to ONE solid.
    # This is the fixed (non-flexing) root of the cantilever.
    root_in = s * ENC_X[1]            # plate edge
    rx_lo, rx_hi = sorted((root_in, arm_out))
    root = _box_between(rx_lo, rx_hi, yc - SNAP_ARM_W / 2.0, yc + SNAP_ARM_W / 2.0,
                        COVER_Z[0] - 3.0, SNAP_ARM_Z1)
    arm = arm + root
    # ---- hook lip: reaches inward from the arm inner face to the tip ----
    tip = s * _HOOK_TIP_R
    hx_lo, hx_hi = sorted((arm_in, tip))
    hook = _box_between(hx_lo, hx_hi, yc - SNAP_ARM_W / 2.0, yc + SNAP_ARM_W / 2.0,
                        SNAP_HOOK_Z[0], SNAP_HOOK_Z[1])
    clip = arm + hook
    # ---- lead-in chamfer on the BACK (-Z) underside of the hook so it cams in
    # as the cover is pushed on (cover travels -Z). 45deg printable overhang.
    # Cut a wedge off the -Z / inner corner of the hook.
    lead = SNAP_LEADIN
    # cutter box placed then we rely on per-edge chamfer instead for robustness
    try:
        # chamfer the inner-bottom edge of the hook (the -Z, inner-X edge)
        z_face = SNAP_HOOK_Z[0]
        edges = clip.edges().filter_by(Axis.Y).group_by(Axis.Z)[0]
        # among lowest-Z edges, pick the innermost (closest to centreline)
        inner_edge = sorted(edges, key=lambda e: abs(e.center().X))[0]
        clip = fillet([inner_edge], radius=min(lead, SNAP_HOOK_ENGAGE - 0.2))
    except Exception:
        pass
    clip.label = f"snap_clip_{'R' if side > 0 else 'L'}_{yc:+.0f}"
    clip.color = COVER_COLOR
    return clip


def _all_snap_clips():
    clips = []
    for side in (+1, -1):
        for yc in SNAP_Y:
            clips.append(_one_clip(side, yc))
    return clips


# ==========================================================================
# MODIFIED build_enclosure  (corner bosses/taps removed; snap windows added)
# ==========================================================================
def build_enclosure():
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

    # (corner screw bosses REMOVED -- replaced by snap clips on the cover)

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

    # (corner tap holes REMOVED)

    # SNAP-CLIP CATCH WINDOWS: cut a through-window in each long side wall so the
    # cover's hook latches behind the window's top (+Z) edge. The window is wider
    # in Z than the hook (so the hook drops in) and in Y than the arm.
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


# ==========================================================================
# MODIFIED build_front_cover  (corner clearance holes removed; clips added)
# ==========================================================================
def build_front_cover():
    plate = _box_between(*ENC_X, *ENC_Y, *COVER_Z)
    # fillet only the outer vertical edges of the plate (filter by Z position so
    # later-added clip edges are never selected) -- robust per-edge.
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

    # (corner M3 clearance holes REMOVED)

    # integral cantilever SNAP CLIPS (fuse into the cover inner face at z=22)
    for clip in _all_snap_clips():
        plate += clip

    plate.label = "front_cover"
    plate.color = COVER_COLOR
    return plate


# ==========================================================================
# Dev assembly + checks
# ==========================================================================
def gen_step(exploded=False):
    enc = build_enclosure()
    cov = build_front_cover()
    if exploded:
        cov = cov.moved(Location((0, 0, 25.0)))
    asm = Compound(label="snapcover", children=[enc, cov])
    asm = asm.moved(Location((0, 0, 0), (1, 0, 0), 90))
    return asm


def gen_section(yc=-9.0, slab=4.0, right_only=True):
    """Thin-slab section through a clip at y=yc: keep only material in
    yc <= y <= yc+slab AND (optionally) x>0, so the arm/hook/window engagement is
    exposed clearly in cross-section. Returns cut enclosure + cut cover (Z-up)."""
    x0 = 0.0 if right_only else ENC_X[0] - 10
    keep = _box_between(x0, ENC_X[1] + 10, yc, yc + slab,
                        ENC_Z[0] - 10, COVER_Z[1] + 10)
    enc = build_enclosure().intersect(keep)
    cov = build_front_cover().intersect(keep)
    enc.color = ENC
    cov.color = COVER_COLOR
    asm = Compound(label="snapcover_section", children=[enc, cov])
    asm = asm.moved(Location((0, 0, 0), (1, 0, 0), 90))
    return asm


def _check():
    enc = build_enclosure()
    cov = build_front_cover()
    print("enclosure solids:", len(enc.solids()), " volume:", round(enc.volume, 1))
    print("front_cover solids:", len(cov.solids()), " volume:", round(cov.volume, 1))
    # cavity-clear box must not be touched by the cover/clips
    clear = _box_between(-45, 45, -17, 14.5, -2, 22)
    inter = cov.intersect(clear)
    iv = inter.volume if inter is not None else 0.0
    print("cover ∩ cavity-clear volume:", round(iv, 4), "(must be ~0)")
    # confirm cover does not poke above z=22 seat (clips run alongside body)
    bb = cov.bounding_box()
    print("cover Z extent:", round(bb.min.Z, 2), "..", round(bb.max.Z, 2),
          " X extent:", round(bb.min.X, 2), "..", round(bb.max.X, 2))
    return enc, cov


def _write(name, asm):
    export_step(asm, f"{name}.step")
    # inline GLB sidecar in the form the CAD Explorer snapshot tool expects
    try:
        export_gltf(asm, f".{name}.step.glb", binary=True)
    except Exception as exc:
        print(f"GLB export failed for {name}: {exc}")


if __name__ == "__main__":
    enc, cov = _check()
    _write("dev_snapcover_assembled", gen_step(exploded=False))
    _write("dev_snapcover_exploded", gen_step(exploded=True))
    _write("dev_snapcover_section", gen_section(-9.0))
    print("wrote dev_snapcover_assembled / _exploded / _section .step (+GLB)")

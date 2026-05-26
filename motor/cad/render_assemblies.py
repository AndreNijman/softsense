"""render_assemblies.py — emit STEPs showing each of the 7 mounting adapters
ACTUALLY CONNECTED between our gripper and the arm/chassis it's designed for.

Each assembly includes:
- The gripper at mid pose (imported from `derived/gripper_mid.step`).
- The adapter (imported from `motor/cad/output/adapter_<NAME>.step`),
  flipped 180° about X and translated so its mating face seats on the
  gripper's bottom M4 flange (world plane Z=-25, bolt centroid at world
  (0, -10, -25)).
- 4× M4 socket-head cap screws shown at the gripper-adapter interface
  (the attachment points — user-supplied per `docs/BOM.md §4`).
- A representative arm-side silhouette per adapter (Reach wrist, cobot
  wrist, BR2 panel, etc.) — translucent / contrasting colour so it reads
  as "representative, not part of our build".
- Arm-side fasteners where applicable.

Run with `--all` to build all 7 STEPs:
    python motor/cad/render_assemblies.py --all
"""
from __future__ import annotations

import math
import os
import sys
from pathlib import Path

from build123d import (
    Box,
    Color,
    Compound,
    Cylinder,
    Location,
    Part,
    export_step,
    import_step,
)

ROOT = Path(__file__).resolve().parent.parent.parent
GRIPPER_STEP = ROOT / "derived" / "gripper_mid.step"
OUTPUT_DIR = ROOT / "motor" / "cad" / "output"

# Mate-up constants (verified — see _base.py + gripper.py BOT_FLANGE_*).
# The gripper STEP has gen_step's +90°X reorient applied: fingers world +Z,
# bottom flange face at world Z=-25, bolt centroid at world (0, -10, -25).
WORLD_FLANGE_Z = -25.0
WORLD_BOLT_X = 0.0
WORLD_BOLT_Y = -10.0

# Colours
C_STAINLESS = Color(0.85, 0.85, 0.88)
C_ALU_DARK = Color(0.30, 0.30, 0.32, 0.90)        # cobot wrist
C_ALU_BRAVO = Color(0.72, 0.75, 0.80, 0.85)       # Reach Bravo wrist
C_ALU_5052 = Color(0.80, 0.82, 0.85, 0.92)        # BR2 Roof Rack
C_HDPE = Color(0.05, 0.05, 0.05, 0.95)            # BR2 panels
C_ACRYLIC = Color(0.65, 0.70, 0.75, 0.45)         # BR2 3" canister
C_JAW = Color(0.55, 0.55, 0.58, 0.95)             # ROV-arm jaw silhouette


# ---------------------------------------------------------------------------
# Common helpers
# ---------------------------------------------------------------------------

def _shcs(thread_d: float, length: float) -> Part:
    """Metric socket-head cap screw. Shank along +Z, head at -Z."""
    shank = Cylinder(radius=thread_d / 2, height=length).moved(
        Location((0, 0, length / 2)))
    head_d = thread_d * 1.7
    head_h = thread_d * 0.9
    head = Cylinder(radius=head_d / 2, height=head_h).moved(
        Location((0, 0, -head_h / 2)))
    p = shank + head
    p.color = C_STAINLESS
    return p


def _gripper_m4_bolts() -> list[Part]:
    """4× M4 SHCS at the gripper bottom-flange holes (the visible attachment
    to the adapter). Shank points world -Z so the bolt threads INTO the
    adapter from below the gripper, head visible underneath."""
    bolts: list[Part] = []
    for x, y in [(-38, -2), (38, -2), (-38, -18), (38, -18)]:
        b = _shcs(4.0, 16.0)
        # flip so shank points -Z (downward into the adapter)
        b = b.moved(Location((0, 0, 0), (1, 0, 0), 180))
        # head sits ~5 mm below the gripper mating plane (visible)
        b = b.moved(Location((x, y, WORLD_FLANGE_Z - 5.0)))
        bolts.append(b)
    return bolts


def _load_adapter(name: str) -> Compound:
    """Load adapter STEP and mate it to the gripper. Adapter native: Z=0
    mating face, +Z away from gripper. Mate-up: flip 180° about X, then
    translate to (0, -10, -25)."""
    step_path = OUTPUT_DIR / f"{name}.step"
    a = import_step(str(step_path))
    a = a.moved(Location((0, 0, 0), (1, 0, 0), 180))
    a = a.moved(Location((WORLD_BOLT_X, WORLD_BOLT_Y, WORLD_FLANGE_Z)))
    return a


def _load_gripper() -> Compound:
    return import_step(str(GRIPPER_STEP))


# ---------------------------------------------------------------------------
# Arm-side silhouettes
# ---------------------------------------------------------------------------

def _bravo_wrist(adapter_t: float = 16.0) -> Compound:
    arm_z = WORLD_FLANGE_Z - adapter_t
    parts: list[Part] = []
    disc = Cylinder(radius=71 / 2, height=6).moved(
        Location((0, WORLD_BOLT_Y, arm_z - 3)))
    disc.color = C_ALU_BRAVO
    parts.append(disc)
    tube = Cylinder(radius=40 / 2, height=80).moved(
        Location((0, WORLD_BOLT_Y, arm_z - 6 - 40)))
    tube.color = C_ALU_BRAVO
    parts.append(tube)
    # 6× M6 on Ø56 PCD, 30° phased
    for k in range(6):
        ang = math.radians(60 * k + 30)
        cx = (56 / 2) * math.cos(ang)
        cy = WORLD_BOLT_Y + (56 / 2) * math.sin(ang)
        b = _shcs(6.0, 18.0)
        # head visible on adapter arm-side face, shank into Bravo disc
        b = b.moved(Location((cx, cy, arm_z + 5.4)))
        parts.append(b)
    return Compound(label="bravo_wrist_silhouette", children=parts)


def _iso_cobot_wrist(face_d: float, spigot_d: float,
                     bolts_n: int, bolt_pcd: float, bolt_thread: float,
                     adapter_t: float = 14.0) -> Compound:
    arm_z = WORLD_FLANGE_Z - adapter_t
    parts: list[Part] = []
    disc_t = 8.0
    disc = Cylinder(radius=face_d / 2, height=disc_t).moved(
        Location((0, WORLD_BOLT_Y, arm_z - disc_t / 2)))
    # spigot recess opening world +Z (toward adapter)
    recess = Cylinder(radius=spigot_d / 2 + 0.05, height=5.5).moved(
        Location((0, WORLD_BOLT_Y, arm_z - 2.75)))
    disc -= recess
    disc.color = C_ALU_DARK
    parts.append(disc)
    cyl_d = face_d * 0.8
    cyl = Cylinder(radius=cyl_d / 2, height=70).moved(
        Location((0, WORLD_BOLT_Y, arm_z - disc_t - 35)))
    cyl.color = C_ALU_DARK
    parts.append(cyl)
    head_h = bolt_thread * 0.9
    for k in range(bolts_n):
        ang = math.radians(360 / bolts_n * k + (360 / bolts_n / 2))
        cx = (bolt_pcd / 2) * math.cos(ang)
        cy = WORLD_BOLT_Y + (bolt_pcd / 2) * math.sin(ang)
        b = _shcs(bolt_thread, bolt_thread * 3)
        b = b.moved(Location((cx, cy, arm_z + head_h)))
        parts.append(b)
    return Compound(label="cobot_wrist_silhouette", children=parts)


def _br2_bottom_panel(adapter_t: float = 10.0) -> Compound:
    """BR2 bottom HDPE panel with 16°-canted 2× M5 Newton holes."""
    arm_z = WORLD_FLANGE_Z - adapter_t
    parts: list[Part] = []
    panel = Box(320, 90, 12.7).moved(
        Location((0, WORLD_BOLT_Y, arm_z - 12.7 / 2)))
    tilt = math.radians(16)
    h1 = (50 * math.cos(tilt), 50 * math.sin(tilt))
    h2 = (-50 * math.cos(tilt), -50 * math.sin(tilt))
    for (x, y) in (h1, h2):
        hole = Cylinder(radius=5.5 / 2, height=14).moved(
            Location((x, WORLD_BOLT_Y + y, arm_z - 12.7 / 2)))
        panel -= hole
    panel.color = C_HDPE
    parts.append(panel)
    for (x, y) in (h1, h2):
        b = _shcs(5.0, 22.0)
        b = b.moved(Location((x, WORLD_BOLT_Y + y, arm_z + 4.5)))
        parts.append(b)
    return Compound(label="br2_bottom_panel_silhouette", children=parts)


def _br2_roof_rack() -> Compound:
    """BR2 Roof Rack — flat aluminium plate aligned with the L-bracket's
    top plate at adapter local Y=+130 (world Y=-140 after the mate-up
    flip+translate). 2× M5 holes 100 mm apart along world Z."""
    # Adapter local M5 hole positions (per adapter_br2_roof_rack.py):
    #   (X=0, Y=130, Z=20)   and   (X=0, Y=130, Z=120)
    # After 180°X flip about origin: (0, -130, -20), (0, -130, -120)
    # After translate (0, -10, -25): (0, -140, -45), (0, -140, -145)
    hole_world = [(0, -140, -45), (0, -140, -145)]
    parts: list[Part] = []
    # Rack plate at world Y = -141 (just outside the adapter's top plate),
    # horizontal (X-Z plane), thin in Y, 140 mm in Z and 100 mm in X
    rack_t = 1.5
    rack_y_face = -141.0      # plate centred ~1.5 mm outboard of adapter top
    rack = Box(100, rack_t, 140).moved(
        Location((0, rack_y_face - rack_t / 2, -95)))  # mid Z between holes
    # drill the 2× M5 holes through Y direction
    for (hx, hy, hz) in hole_world:
        hole = Cylinder(radius=5.5 / 2, height=4).moved(
            Location((hx, rack_y_face - rack_t / 2, hz),
                     (1, 0, 0), 90))   # cylinder axis along Y
        rack -= hole
    rack.color = C_ALU_5052
    parts.append(rack)
    # 2× M5 SHCS pointing in +Y direction (head outboard, shank into adapter)
    for (hx, hy, hz) in hole_world:
        b = _shcs(5.0, 18.0)
        # default shank +Z; rotate so shank +Y
        b = b.moved(Location((0, 0, 0), (1, 0, 0), -90))
        # head outboard (world -Y from the rack plate)
        b = b.moved(Location((hx, rack_y_face - rack_t - 4.5, hz)))
        parts.append(b)
    return Compound(label="br2_roof_rack_silhouette", children=parts)


def _br2_payload_skid(adapter_t: float = 12.0) -> Compound:
    """BR2 Payload Skid: bottom HDPE panel + 3"-canister cradle half-pipe."""
    arm_z = WORLD_FLANGE_Z - adapter_t
    parts: list[Part] = []
    panel = Box(280, 100, 12.7).moved(
        Location((0, WORLD_BOLT_Y, arm_z - 12.7 / 2)))
    tilt = math.radians(16)
    h1 = (50 * math.cos(tilt), 50 * math.sin(tilt))
    h2 = (-50 * math.cos(tilt), -50 * math.sin(tilt))
    for (x, y) in (h1, h2):
        hole = Cylinder(radius=5.5 / 2, height=14).moved(
            Location((x, WORLD_BOLT_Y + y, arm_z - 12.7 / 2)))
        panel -= hole
    panel.color = C_HDPE
    parts.append(panel)
    for (x, y) in (h1, h2):
        b = _shcs(5.0, 22.0)
        b = b.moved(Location((x, WORLD_BOLT_Y + y, arm_z + 4.5)))
        parts.append(b)
    # 3" canister cradle half-band below the panel (representative)
    cradle_r = 91 / 2
    cradle_l = 80
    cradle = Cylinder(radius=cradle_r, height=cradle_l).moved(
        Location((0, WORLD_BOLT_Y, arm_z - 12.7 - cradle_l / 2 - 5)))
    inside = Cylinder(radius=cradle_r - 2.5, height=cradle_l + 1).moved(
        Location((0, WORLD_BOLT_Y, arm_z - 12.7 - cradle_l / 2 - 5)))
    cradle -= inside
    # cut top half off (keep lower half — the bowl the canister rests in)
    cutter = Box(2 * cradle_r + 4, 2 * cradle_r + 4, cradle_l + 4).moved(
        Location((0, WORLD_BOLT_Y, arm_z - 12.7 - cradle_l / 2 - 5
                  + cradle_r + 0.01)))
    cradle -= cutter
    cradle.color = C_ACRYLIC
    parts.append(cradle)
    return Compound(label="br2_payload_skid_silhouette", children=parts)


def _arm_jaws_for_dhandle() -> Compound:
    """Two parallel-jaw blocks clamping the D-handle bar from opposite
    sides. The bar (from adapter_iso13628_d_handle.py) sits at adapter
    local (X=0, Y axis ±50, Z ≈ 66.5). After 180°X flip + translate
    (0, -10, -25): bar centre at world (0, -10, -91.5), axis along world Y,
    endpoints at world Y = -60 .. +40."""
    bar_z_world = WORLD_FLANGE_Z - 66.5
    bar_y_world = WORLD_BOLT_Y
    bar_od = 19.0
    jaw_w = 50.0    # width along the bar (world Y)
    jaw_d = 30.0    # thickness across the bar (world X) — the clamp direction
    jaw_h = 25.0    # height (world Z)
    parts: list[Part] = []
    for sign in (-1, +1):
        cx = sign * (bar_od / 2 + jaw_d / 2)
        j = Box(jaw_d, jaw_w, jaw_h).moved(
            Location((cx, bar_y_world, bar_z_world)))
        j.color = C_JAW
        parts.append(j)
    return Compound(label="arm_jaws_silhouette", children=parts)


# ---------------------------------------------------------------------------
# Per-adapter assembly
# ---------------------------------------------------------------------------

ASSEMBLY_FNS = {
    "adapter_bravo7":            lambda: _bravo_wrist(adapter_t=16.0),
    "adapter_iso9409_50_4_M6":   lambda: _iso_cobot_wrist(
        face_d=63, spigot_d=31.5, bolts_n=4, bolt_pcd=50, bolt_thread=6.0,
        adapter_t=14.0),
    "adapter_iso9409_80_6_M8":   lambda: _iso_cobot_wrist(
        face_d=100, spigot_d=50, bolts_n=6, bolt_pcd=80, bolt_thread=8.0,
        adapter_t=14.0),
    "adapter_br2_bottom_newton": lambda: _br2_bottom_panel(adapter_t=10.0),
    "adapter_br2_roof_rack":     lambda: _br2_roof_rack(),
    "adapter_br2_payload_skid":  lambda: _br2_payload_skid(adapter_t=12.0),
    "adapter_iso13628_d_handle": lambda: _arm_jaws_for_dhandle(),
}


def build_assembly(name: str) -> Compound:
    children: list = []
    children.append(_load_gripper())
    children.append(_load_adapter(name))
    children.extend(_gripper_m4_bolts())
    children.append(ASSEMBLY_FNS[name]())
    return Compound(label=f"{name}_assembled", children=children)


def gen_step() -> Compound:
    name = os.environ.get("GRIPPER_ASM_NAME", "adapter_bravo7")
    return build_assembly(name)


if __name__ == "__main__":
    if "--all" in sys.argv:
        for name in ASSEMBLY_FNS:
            out = OUTPUT_DIR / f"{name}_assembled.step"
            print(f"[build] {name}", flush=True)
            asm = build_assembly(name)
            export_step(asm, str(out))
            print(f"  -> {out}  ({out.stat().st_size // 1024} KB)")
    else:
        gen_step()

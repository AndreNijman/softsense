"""render_assemblies.py — emit STEPs showing each of the 7 mounting adapters
ACTUALLY CONNECTED between the FULL unibody (gripper + canister + servo +
shaft + lip seal + caps + penetrators + cosmetic shrouds) and the arm/
chassis it's designed for.

Each assembly:
- Imports the full unibody from
  `motor/cad/output/system_assembly_T2_UNIBODY_STS3250.step`. In its
  "as-mounted" world frame, fingers point world -Z (down) and the BR dry
  cap is at world Z ≈ +333 (top). Canister axis at world (X=0, Y=-12).
- Places the adapter on top of the dry cap at world (0, -12, +333). The
  adapter's +Z direction (away from gripper, toward arm) matches world +Z
  in this position, so NO flip is applied.
- Adds 4× representative M5 SHCS going from the adapter face down into
  the BR dry cap (the arm-to-canister attachment — the BR cap's existing
  M10 holes can be repurposed, or PA12-GF threaded inserts added; this is
  the visual intent).
- Adds an arm-side silhouette above the adapter (the arm wrist that
  bolts/clamps to the adapter's arm-side face), in a contrasting colour
  so it reads as "external context, not part of our build."
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
SYSTEM_STEP = ROOT / "motor" / "cad" / "output" / \
    "system_assembly_T2_UNIBODY_STS3250.step"
OUTPUT_DIR = ROOT / "motor" / "cad" / "output"

# Unibody world frame (verified by bbox 2026-05-26):
#   fingers at world Z ≈ -123 (down)
#   BR dry cap top at world Z ≈ +333 (up — where the ROV arm attaches)
#   canister axis at world (X=0, Y=-12)
WORLD_DRY_CAP_Z = 333.0
WORLD_CANISTER_X = 0.0
WORLD_CANISTER_Y = -12.0

# Colours
C_STAINLESS = Color(0.85, 0.85, 0.88)
C_ALU_DARK = Color(0.30, 0.30, 0.32, 0.90)
C_ALU_BRAVO = Color(0.72, 0.75, 0.80, 0.90)
C_ALU_5052 = Color(0.80, 0.82, 0.85, 0.92)
C_HDPE = Color(0.05, 0.05, 0.05, 0.95)
C_ACRYLIC = Color(0.65, 0.70, 0.75, 0.45)
C_JAW = Color(0.55, 0.55, 0.58, 0.95)


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


def _dry_cap_bolts() -> list[Part]:
    """4× M5 SHCS at corners of an 80 mm square pattern around the canister
    axis on the dry cap (representative — BR cap M10 PCD is approx square
    pattern; the actual mount uses 4 of those holes or printed inserts)."""
    bolts: list[Part] = []
    pcd = 80.0 / math.sqrt(2)   # corner distance for 80 mm square
    for k in range(4):
        ang = math.radians(45 + 90 * k)
        cx = WORLD_CANISTER_X + pcd * math.cos(ang)
        cy = WORLD_CANISTER_Y + pcd * math.sin(ang)
        b = _shcs(5.0, 22.0)
        # Shank pointing DOWN into the dry cap (world -Z); default +Z so flip
        b = b.moved(Location((0, 0, 0), (1, 0, 0), 180))
        # Head visible just above the dry cap (5 mm above dry cap top)
        b = b.moved(Location((cx, cy, WORLD_DRY_CAP_Z + 5.0)))
        bolts.append(b)
    return bolts


def _load_adapter_at_dry_cap(name: str) -> Compound:
    """Load adapter STEP and place it at the dry-cap end of the unibody.
    Adapter native: Z=0 mating face, +Z away from gripper. At the dry-cap
    end (top of as-mounted unibody), +Z away from gripper = world +Z, so
    NO flip is needed. Translate to (0, -12, WORLD_DRY_CAP_Z)."""
    step_path = OUTPUT_DIR / f"{name}.step"
    a = import_step(str(step_path))
    a = a.moved(Location((WORLD_CANISTER_X, WORLD_CANISTER_Y,
                          WORLD_DRY_CAP_Z)))
    return a


def _load_unibody() -> Compound:
    return import_step(str(SYSTEM_STEP))


# ---------------------------------------------------------------------------
# Arm-side silhouettes (positioned ABOVE the adapter's arm-side face)
# ---------------------------------------------------------------------------

def _bravo_wrist(adapter_t: float = 16.0) -> Compound:
    arm_z = WORLD_DRY_CAP_Z + adapter_t           # adapter arm-side face
    parts: list[Part] = []
    # Ø71 Bravo Payload Interface disc
    disc = Cylinder(radius=71 / 2, height=8).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, arm_z + 4)))
    disc.color = C_ALU_BRAVO
    parts.append(disc)
    # Bravo wrist body — Ø60 × 120 mm representing the arm
    body = Cylinder(radius=60 / 2, height=120).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, arm_z + 8 + 60)))
    body.color = C_ALU_BRAVO
    parts.append(body)
    # 6× M6 SHCS into the Ø56 PCD, heads visible on the disc top
    for k in range(6):
        ang = math.radians(60 * k + 30)
        cx = WORLD_CANISTER_X + (56 / 2) * math.cos(ang)
        cy = WORLD_CANISTER_Y + (56 / 2) * math.sin(ang)
        b = _shcs(6.0, 18.0)
        # head above the Bravo disc (world +Z side), shank into adapter (down)
        b = b.moved(Location((0, 0, 0), (1, 0, 0), 180))
        b = b.moved(Location((cx, cy, arm_z + 8 + 5.4)))
        parts.append(b)
    return Compound(label="bravo_wrist_silhouette", children=parts)


def _iso_cobot_wrist(face_d: float, spigot_d: float,
                     bolts_n: int, bolt_pcd: float, bolt_thread: float,
                     adapter_t: float = 14.0) -> Compound:
    arm_z = WORLD_DRY_CAP_Z + adapter_t
    parts: list[Part] = []
    disc_t = 8.0
    # cobot wrist mounting disc with the spigot recess opening world -Z
    disc = Cylinder(radius=face_d / 2, height=disc_t).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, arm_z + disc_t / 2)))
    recess = Cylinder(radius=spigot_d / 2 + 0.05, height=5.5).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, arm_z + 2.75)))
    disc -= recess
    disc.color = C_ALU_DARK
    parts.append(disc)
    # cobot wrist cylinder
    cyl_d = face_d * 0.8
    cyl = Cylinder(radius=cyl_d / 2, height=90).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y,
                  arm_z + disc_t + 45)))
    cyl.color = C_ALU_DARK
    parts.append(cyl)
    # bolt heads visible on top of the cobot disc
    head_h = bolt_thread * 0.9
    for k in range(bolts_n):
        ang = math.radians(360 / bolts_n * k + (360 / bolts_n / 2))
        cx = WORLD_CANISTER_X + (bolt_pcd / 2) * math.cos(ang)
        cy = WORLD_CANISTER_Y + (bolt_pcd / 2) * math.sin(ang)
        b = _shcs(bolt_thread, bolt_thread * 3)
        b = b.moved(Location((0, 0, 0), (1, 0, 0), 180))
        b = b.moved(Location((cx, cy, arm_z + disc_t + head_h)))
        parts.append(b)
    return Compound(label="cobot_wrist_silhouette", children=parts)


def _br2_chassis(adapter_t: float = 10.0) -> Compound:
    """BR2 black HDPE chassis panel above the adapter, with 2× Ø5.5 holes
    on 100 mm pitch / 16° tilt."""
    arm_z = WORLD_DRY_CAP_Z + adapter_t
    parts: list[Part] = []
    panel = Box(360, 100, 12.7).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, arm_z + 12.7 / 2)))
    tilt = math.radians(16)
    h1 = (50 * math.cos(tilt), 50 * math.sin(tilt))
    h2 = (-50 * math.cos(tilt), -50 * math.sin(tilt))
    for (x, y) in (h1, h2):
        hole = Cylinder(radius=5.5 / 2, height=14).moved(
            Location((WORLD_CANISTER_X + x, WORLD_CANISTER_Y + y,
                      arm_z + 12.7 / 2)))
        panel -= hole
    panel.color = C_HDPE
    parts.append(panel)
    for (x, y) in (h1, h2):
        b = _shcs(5.0, 22.0)
        b = b.moved(Location((0, 0, 0), (1, 0, 0), 180))
        b = b.moved(Location((WORLD_CANISTER_X + x, WORLD_CANISTER_Y + y,
                              arm_z + 12.7 + 4.5)))
        parts.append(b)
    return Compound(label="br2_chassis_silhouette", children=parts)


def _br2_roof_rack_chassis(adapter_t: float = 10.0) -> Compound:
    """BR2 Roof Rack aluminium chassis above the adapter."""
    arm_z = WORLD_DRY_CAP_Z + adapter_t
    parts: list[Part] = []
    rack_t = 1.5
    rack = Box(140, 100, rack_t).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, arm_z + rack_t / 2)))
    # 2× M5 holes on 100 mm Z-pitch (along rack length) — but in this
    # config (rack above adapter, rack horizontal) put holes along X axis
    for sign in (-1, +1):
        hole = Cylinder(radius=5.5 / 2, height=rack_t + 1).moved(
            Location((WORLD_CANISTER_X + sign * 50, WORLD_CANISTER_Y,
                      arm_z + rack_t / 2)))
        rack -= hole
    rack.color = C_ALU_5052
    parts.append(rack)
    # 2× M5 SHCS heads visible on top of rack
    for sign in (-1, +1):
        b = _shcs(5.0, 18.0)
        b = b.moved(Location((0, 0, 0), (1, 0, 0), 180))
        b = b.moved(Location((WORLD_CANISTER_X + sign * 50,
                              WORLD_CANISTER_Y, arm_z + rack_t + 4.5)))
        parts.append(b)
    return Compound(label="br2_roof_rack_silhouette", children=parts)


def _br2_payload_skid_chassis(adapter_t: float = 12.0) -> Compound:
    """BR2 Payload Skid bottom HDPE panel + 3" cradle clamp ring above
    the adapter."""
    arm_z = WORLD_DRY_CAP_Z + adapter_t
    parts: list[Part] = []
    panel = Box(360, 100, 12.7).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, arm_z + 12.7 / 2)))
    tilt = math.radians(16)
    h1 = (50 * math.cos(tilt), 50 * math.sin(tilt))
    h2 = (-50 * math.cos(tilt), -50 * math.sin(tilt))
    for (x, y) in (h1, h2):
        hole = Cylinder(radius=5.5 / 2, height=14).moved(
            Location((WORLD_CANISTER_X + x, WORLD_CANISTER_Y + y,
                      arm_z + 12.7 / 2)))
        panel -= hole
    panel.color = C_HDPE
    parts.append(panel)
    for (x, y) in (h1, h2):
        b = _shcs(5.0, 22.0)
        b = b.moved(Location((0, 0, 0), (1, 0, 0), 180))
        b = b.moved(Location((WORLD_CANISTER_X + x, WORLD_CANISTER_Y + y,
                              arm_z + 12.7 + 4.5)))
        parts.append(b)
    # 3" canister cradle clamp ring (decorative, suggests the skid's 3"
    # enclosure clamp position)
    cradle_outer = 95
    cradle_inner = 91
    cradle_h = 16
    cradle_z = arm_z + 12.7 + cradle_h / 2 + 4
    ring_outer = Cylinder(radius=cradle_outer / 2, height=cradle_h).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, cradle_z)))
    ring_inner = Cylinder(radius=cradle_inner / 2, height=cradle_h + 1).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, cradle_z)))
    ring = ring_outer - ring_inner
    ring.color = C_ACRYLIC
    parts.append(ring)
    return Compound(label="br2_payload_skid_silhouette", children=parts)


def _arm_jaws_for_dhandle() -> Compound:
    """Two parallel-jaw blocks clamping the D-handle bar. The d-handle
    adapter, placed at the dry-cap end, has its bar at world Z ≈ +333 +
    66.5 = +399.5 (bar centre). Bar axis along world Y."""
    bar_z_world = WORLD_DRY_CAP_Z + 66.5
    bar_y_world = WORLD_CANISTER_Y
    bar_od = 19.0
    jaw_w = 50.0       # along bar (world Y)
    jaw_d = 30.0       # across bar (world X) — clamp direction
    jaw_h = 25.0       # vertical (world Z)
    parts: list[Part] = []
    for sign in (-1, +1):
        cx = WORLD_CANISTER_X + sign * (bar_od / 2 + jaw_d / 2)
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
    "adapter_br2_bottom_newton": lambda: _br2_chassis(adapter_t=10.0),
    "adapter_br2_roof_rack":     lambda: _br2_roof_rack_chassis(adapter_t=10.0),
    "adapter_br2_payload_skid":  lambda: _br2_payload_skid_chassis(adapter_t=12.0),
    "adapter_iso13628_d_handle": lambda: _arm_jaws_for_dhandle(),
}


def build_assembly(name: str) -> Compound:
    children: list = []
    # The full unibody — gripper + canister + servo + shaft + lip seal + caps
    # + penetrators + cosmetic shrouds
    children.append(_load_unibody())
    # Adapter on top of the dry cap
    children.append(_load_adapter_at_dry_cap(name))
    # 4× M5 SHCS on the dry-cap-to-adapter interface
    children.extend(_dry_cap_bolts())
    # Arm-side silhouette + arm-to-adapter fasteners
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

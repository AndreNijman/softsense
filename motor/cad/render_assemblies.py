"""render_assemblies.py — emit STEPs showing each of the 7 unibody pod
adapters ACTUALLY MOUNTED on the gripper-canister unibody, with arm-side
silhouettes representing where the ROV arm / chassis would attach.

Adapters are now Ø100 PA12-GF pieces that visually continue the unibody
cylindrical body. Each sits on top of the pod_cap_shroud / BR dry cap and
carries its arm-specific interface (Bravo Ø71 + 6×M6, ISO 9409, BR2 plate
+ Newton holes, or ISO 13628-8 D-handle).

Mating:
- Unibody as-mounted has BR dry cap at world Z = +333 (top of bbox).
- Canister axis at world (X=0, Y=-12).
- Each adapter's local Z=0 face is placed at world Z = +333, no flip.
- Adapter +Z (away from canister) = world +Z (toward arm).
- 4× M5 SHCS visible going from the pod base DOWN into the BR dry cap
  via the existing M10 penetrator holes (or M10→M5 PA12-GF inserts).
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

WORLD_POD_CAP_TOP_Z = 275.0   # top face of pod_cap_shroud in as-mounted world frame
WORLD_CANISTER_X = 0.0
WORLD_CANISTER_Y = -12.0

# Back-compat alias (some helpers below still reference the old name).
WORLD_DRY_CAP_Z = WORLD_POD_CAP_TOP_Z

# Pod-base bolt PCD (per _base.py POD_BOLT_PCD)
POD_BOLT_PCD = 78.0

# Per-adapter total height (must match each module's TOTAL_H; if changed,
# update here too).
ADAPTER_HEIGHTS = {
    "adapter_bravo7":            28.0,
    "adapter_iso9409_50_4_M6":   33.0,
    "adapter_iso9409_80_6_M8":   25.0,
    "adapter_br2_bottom_newton": 24.0,
    "adapter_br2_roof_rack":     40.0,
    "adapter_br2_payload_skid":  24.0,
    "adapter_iso13628_d_handle": 86.0,
}

C_STAINLESS = Color(0.85, 0.85, 0.88)
C_ALU_DARK = Color(0.30, 0.30, 0.32, 0.90)
C_ALU_BRAVO = Color(0.72, 0.75, 0.80, 0.90)
C_ALU_5052 = Color(0.80, 0.82, 0.85, 0.92)
C_HDPE = Color(0.05, 0.05, 0.05, 0.95)
C_ACRYLIC = Color(0.65, 0.70, 0.75, 0.45)
C_JAW = Color(0.55, 0.55, 0.58, 0.95)


def _shcs(thread_d: float, length: float) -> Part:
    shank = Cylinder(radius=thread_d / 2, height=length).moved(
        Location((0, 0, length / 2)))
    head_d = thread_d * 1.7
    head_h = thread_d * 0.9
    head = Cylinder(radius=head_d / 2, height=head_h).moved(
        Location((0, 0, -head_h / 2)))
    p = shank + head
    p.color = C_STAINLESS
    return p


def _pod_to_drycap_bolts() -> list[Part]:
    """4× M5 SHCS on Ø78 PCD (matches pod_base) — heads visible on top of
    the adapter pod base, shanks going DOWN into the BR dry cap."""
    bolts: list[Part] = []
    for k in range(4):
        ang = math.radians(360.0 / 4 * k)
        cx = WORLD_CANISTER_X + (POD_BOLT_PCD / 2) * math.cos(ang)
        cy = WORLD_CANISTER_Y + (POD_BOLT_PCD / 2) * math.sin(ang)
        b = _shcs(5.0, 22.0)
        # Default shank +Z; flip 180°X so shank points -Z (down into dry cap)
        b = b.moved(Location((0, 0, 0), (1, 0, 0), 180))
        # Head visible 4.5 mm above the adapter top of pod base (Z=14 in adapter)
        b = b.moved(Location((cx, cy, WORLD_DRY_CAP_Z + 14.0 + 4.5)))
        bolts.append(b)
    return bolts


def _load_adapter_at_dry_cap(name: str) -> Compound:
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

def _bravo_wrist() -> Compound:
    arm_z = WORLD_DRY_CAP_Z + ADAPTER_HEIGHTS["adapter_bravo7"]
    parts: list[Part] = []
    # Bravo mounting disc Ø75 × 6 (slightly bigger than Ø71 to make seating
    # visible) on top of the adapter
    disc = Cylinder(radius=75 / 2, height=6).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, arm_z + 3)))
    disc.color = C_ALU_BRAVO
    parts.append(disc)
    # Bravo arm — Ø60 × 140 mm cylindrical body
    body = Cylinder(radius=60 / 2, height=140).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, arm_z + 6 + 70)))
    body.color = C_ALU_BRAVO
    parts.append(body)
    # 6× M6 SHCS on Ø56 PCD
    for k in range(6):
        ang = math.radians(60 * k)
        cx = WORLD_CANISTER_X + (56 / 2) * math.cos(ang)
        cy = WORLD_CANISTER_Y + (56 / 2) * math.sin(ang)
        b = _shcs(6.0, 18.0)
        b = b.moved(Location((0, 0, 0), (1, 0, 0), 180))
        b = b.moved(Location((cx, cy, arm_z + 6 + 5.4)))
        parts.append(b)
    return Compound(label="bravo_arm_silhouette", children=parts)


def _iso_cobot_wrist(face_d: float, spigot_d: float,
                     bolts_n: int, bolt_pcd: float, bolt_thread: float,
                     adapter_h: float) -> Compound:
    arm_z = WORLD_DRY_CAP_Z + adapter_h
    parts: list[Part] = []
    disc_t = 8.0
    disc = Cylinder(radius=face_d / 2 + 2, height=disc_t).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y,
                  arm_z + disc_t / 2)))
    # Recess for the spigot
    recess = Cylinder(radius=spigot_d / 2 + 0.1, height=5.5).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, arm_z + 2.75)))
    disc -= recess
    disc.color = C_ALU_DARK
    parts.append(disc)
    # Cobot wrist body
    cyl_d = face_d * 0.85
    cyl = Cylinder(radius=cyl_d / 2, height=120).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y,
                  arm_z + disc_t + 60)))
    cyl.color = C_ALU_DARK
    parts.append(cyl)
    # Bolt heads
    head_h = bolt_thread * 0.9
    for k in range(bolts_n):
        ang = math.radians(360 / bolts_n * k + (360 / bolts_n / 2))
        cx = WORLD_CANISTER_X + (bolt_pcd / 2) * math.cos(ang)
        cy = WORLD_CANISTER_Y + (bolt_pcd / 2) * math.sin(ang)
        b = _shcs(bolt_thread, bolt_thread * 3)
        b = b.moved(Location((0, 0, 0), (1, 0, 0), 180))
        b = b.moved(Location((cx, cy, arm_z + disc_t + head_h)))
        parts.append(b)
    return Compound(label="cobot_arm_silhouette", children=parts)


def _br2_chassis(adapter_h: float) -> Compound:
    """BR2 black HDPE bottom panel above the adapter top plate."""
    arm_z = WORLD_DRY_CAP_Z + adapter_h
    parts: list[Part] = []
    panel = Box(360, 100, 12.7).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y,
                  arm_z + 12.7 / 2)))
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


def _br2_roof_rack_chassis(adapter_h: float) -> Compound:
    arm_z = WORLD_DRY_CAP_Z + adapter_h
    parts: list[Part] = []
    rack_t = 1.5
    rack = Box(180, 120, rack_t).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y,
                  arm_z + rack_t / 2)))
    for sign in (-1, +1):
        hole = Cylinder(radius=5.5 / 2, height=rack_t + 1).moved(
            Location((WORLD_CANISTER_X + sign * 50, WORLD_CANISTER_Y,
                      arm_z + rack_t / 2)))
        rack -= hole
    rack.color = C_ALU_5052
    parts.append(rack)
    for sign in (-1, +1):
        b = _shcs(5.0, 18.0)
        b = b.moved(Location((0, 0, 0), (1, 0, 0), 180))
        b = b.moved(Location((WORLD_CANISTER_X + sign * 50,
                              WORLD_CANISTER_Y,
                              arm_z + rack_t + 4.5)))
        parts.append(b)
    return Compound(label="br2_roof_rack_silhouette", children=parts)


def _br2_payload_skid_chassis(adapter_h: float) -> Compound:
    arm_z = WORLD_DRY_CAP_Z + adapter_h
    parts: list[Part] = []
    panel = Box(360, 100, 12.7).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y,
                  arm_z + 12.7 / 2)))
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
    # 3" canister cradle clamp ring (decorative)
    cradle_outer = 95
    cradle_inner = 91
    cradle_h = 16
    cradle_z = arm_z + 12.7 + cradle_h / 2 + 4
    ring_outer = Cylinder(radius=cradle_outer / 2, height=cradle_h).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, cradle_z)))
    ring_inner = Cylinder(radius=cradle_inner / 2,
                          height=cradle_h + 1).moved(
        Location((WORLD_CANISTER_X, WORLD_CANISTER_Y, cradle_z)))
    ring = ring_outer - ring_inner
    ring.color = C_ACRYLIC
    parts.append(ring)
    return Compound(label="br2_payload_skid_silhouette", children=parts)


def _arm_jaws_for_dhandle() -> Compound:
    """Two parallel-jaw blocks clamping the D-handle bar. With the new
    adapter, bar centre is at adapter local Z = Z_BAR_CTR = 76.5 (from
    `adapter_iso13628_d_handle.py`). Placed at world: bar Z = 333 + 76.5
    = 409.5, axis along world Y."""
    bar_z_world = WORLD_DRY_CAP_Z + 76.5
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


ASSEMBLY_FNS = {
    "adapter_bravo7":            lambda: _bravo_wrist(),
    "adapter_iso9409_50_4_M6":   lambda: _iso_cobot_wrist(
        face_d=63, spigot_d=31.5, bolts_n=4, bolt_pcd=50, bolt_thread=6.0,
        adapter_h=ADAPTER_HEIGHTS["adapter_iso9409_50_4_M6"]),
    "adapter_iso9409_80_6_M8":   lambda: _iso_cobot_wrist(
        face_d=100, spigot_d=50, bolts_n=6, bolt_pcd=80, bolt_thread=8.0,
        adapter_h=ADAPTER_HEIGHTS["adapter_iso9409_80_6_M8"]),
    "adapter_br2_bottom_newton": lambda: _br2_chassis(
        adapter_h=ADAPTER_HEIGHTS["adapter_br2_bottom_newton"]),
    "adapter_br2_roof_rack":     lambda: _br2_roof_rack_chassis(
        adapter_h=ADAPTER_HEIGHTS["adapter_br2_roof_rack"]),
    "adapter_br2_payload_skid":  lambda: _br2_payload_skid_chassis(
        adapter_h=ADAPTER_HEIGHTS["adapter_br2_payload_skid"]),
    "adapter_iso13628_d_handle": lambda: _arm_jaws_for_dhandle(),
}


def build_assembly(name: str) -> Compound:
    children: list = []
    children.append(_load_unibody())
    children.append(_load_adapter_at_dry_cap(name))
    children.extend(_pod_to_drycap_bolts())
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

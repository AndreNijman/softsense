"""adapter_iso9409_50_4_M6.py — ISO 9409-1-50-4-M6 cobot tool-flange adapter.

DRY ONLY — for bench/lab use on cobots whose wrists are not waterproof
(UR e-Series IP54, Franka FR3 IP40, ABB GoFa CRB 15000 IP54). This part
mates the gripper's bottom M4 flange to the dominant cobot tool-flange
pattern (UR3e/5e/10e/16e, Franka FR3/Panda, Doosan A-series, Fanuc CRX,
ABB GoFa via 4-of-7, KUKA LBR iiwa via 4-of-7). Underwater the gripper
continues to use its sealed ROV penetrator interface — this adapter is
**not** the subsea interface.

Geometry summary (see `motor/interfaces/iso-9409-1.md §4` and §10.1):

- Top face (cobot side, +Z normal):
  * Ø63 face OD  (= d2, h8) — see dossier §4 (d2 = Ø63 mm).
  * Ø31.5 spigot (= d3, h7) projecting +5 mm above the top face — the
    cobot's mating recess is the H7 feature, so the *tool* side carries
    the corresponding h7 spigot (dossier §10.1: "adapter has a Ø31.5 h7
    spigot protruding 4–5 mm"). +Z (away from gripper) is the cobot-mating
    direction per ISO 9787 / UR5e tool-flange convention (dossier §4).
  * 4 × Ø6.6 (M6 close clearance) through-holes on the Ø50 bolt circle
    (= d1) at 45°/135°/225°/315° from +X — see dossier §4 + §10.1.
    Counter-bored Ø11 × 6.4 mm on the top face for M6 SHCS heads.
  * 1 × Ø6 H7 dowel hole (= d5) on the d1 = Ø50 bolt-circle, on the +X
    axis (ISO 9787 +Xm), 45° between bolts — see dossier §4 ("dowel pin
    hole d5 is on the same bolt circle d1 ... between two adjacent
    holes, with its centre aligned with the +Xm axis"). The cobot
    projects the dowel pin, the adapter carries the hole (dossier §6,
    "All common cobots project the pin from the robot side").
  * 0.04 mm face flatness over Ø63 — **fabrication spec, not a CAD
    constraint**. PA12-GF off the printer is ~0.10–0.15 mm flat; use a
    0.5 mm PTFE shim or post-machine the top face (dossier §10.4).

- Transition body: loft from top Ø63 disc to bottom 76 × 28 mm
  rectangle (matches `_base.GRIPPER_FLANGE_FOOTPRINT_*`). Adapter
  thickness ADAPTER_T = 14 mm — chosen per dossier §10 "recommended
  primary pair: 10 mm adapter + M6×18 SHCS", bumped to 14 mm to give
  loft volume above the rectangular bolt pattern (76 × 28) for stress
  flow and counter-bore depth. Pair with M6 × 20 SHCS (8 mm thread into
  the robot — safe within the 6–10 mm UR window, dossier §10 table).

- Bottom face (gripper side, Z = 0): 4 × M4 clearance via
  `_base.gripper_bolt_holes()`, Ø16 shaft clearance via
  `_base.shaft_clearance_bore()` at X = -12. These constants are
  imported verbatim and not re-derived — see `_base.py` docstring.

**Off-centre shaft note.** The gripper shaft sits at X = -12 mm; the
ISO spigot is centred at X = 0. The Ø16 shaft bore therefore cuts a
D-shaped notch through the -X side of the spigot (spigot spans
X ∈ [-15.75, +15.75]; bore spans X ∈ [-20, -4]). The remaining ~10 mm
of intact spigot circumference on the +X half is still sufficient to
index the cobot's Ø31.5 H7 recess for centering, and the dowel pin at
(+25, 0) provides the anti-rotation datum independently. This is the
genuine consequence of an off-centre gripper shaft on an ISO 9409 face.

Sources for every dimension: `motor/interfaces/iso-9409-1.md` §4
(geometry table) and §10.1 (50-4-M6 variant table).
"""
from __future__ import annotations

import math
import os

from build123d import (
    Box,
    Circle,
    Compound,
    Cylinder,
    Location,
    Part,
    Plane,
    Rectangle,
    export_step,
    loft,
)

from motor.cad.adapters._base import (
    C_PA12_GF,
    finalize,
    gripper_bolt_holes,
    m_clearance_radius,
    shaft_clearance_bore,
)

# ---------------------------------------------------------------------------
# ISO 9409-1-50-4-M6 dimension constants (dossier §4 Table)
# ---------------------------------------------------------------------------

ISO_BC_D1: float     = 50.0    # bolt-circle diameter (d1)
ISO_FACE_D2: float   = 63.0    # face OD, h8 (d2)
ISO_SPIGOT_D3: float = 31.5    # centering spigot OD, h7 (d3)
ISO_M6: float        = 6.0     # nominal thread (d4)
ISO_DOWEL_D5: float  = 6.0     # dowel-pin hole diameter, H7 (d5)

# Adapter geometry choices (dossier §10.1)
ADAPTER_T: float        = 14.0   # adapter total thickness (mm)
SPIGOT_H: float         = 5.0    # spigot projection above top face (4–5 mm range)
COUNTERBORE_D: float    = 11.0   # M6 SHCS head clearance Ø
COUNTERBORE_DEPTH: float = 6.4   # leaves ~7.6 mm of full-section under each bolt
DOWEL_DEPTH: float      = 6.0    # dowel hole depth (= d5 nominal engagement)
EDGE_R: float           = 3.0    # fillet on rectangular bottom edge (cosmetic)

# Loft-body rectangular bottom footprint — matches _base.GRIPPER_FLANGE_FOOTPRINT_*
BOT_X: float = 76.0
BOT_Y: float = 28.0

# Dowel pin position on +Xm axis (ISO 9787), at d1/2 radius
DOWEL_X: float = ISO_BC_D1 / 2.0   # = 25.0
DOWEL_Y: float = 0.0


def _bolt_xy() -> list[tuple[float, float]]:
    """4 bolts on Ø50 BCD at 45°/135°/225°/315° so the dowel at +X (0°)
    sits between bolt #1 (45°) and bolt #4 (315°), per dossier §4."""
    r = ISO_BC_D1 / 2.0
    out: list[tuple[float, float]] = []
    for k in range(4):
        ang = math.radians(45.0 + 90.0 * k)
        out.append((r * math.cos(ang), r * math.sin(ang)))
    return out


def build() -> Part:
    """Construct the adapter as a single `Part`. See module docstring for
    full geometry rationale; key spec source is `motor/interfaces/iso-9409-1.md`."""

    # --- Lofted body: 76×28 rectangle at Z=0 → Ø63 disc at Z=ADAPTER_T ---
    bot_sketch = Plane.XY * Rectangle(BOT_X, BOT_Y)
    top_sketch = Plane.XY.offset(ADAPTER_T) * Circle(radius=ISO_FACE_D2 / 2.0)
    body: Part = loft([bot_sketch, top_sketch])

    # --- Add the Ø31.5 h7 spigot projecting upward (+Z) from the top face ---
    spigot = Cylinder(radius=ISO_SPIGOT_D3 / 2.0, height=SPIGOT_H).moved(
        Location((0.0, 0.0, ADAPTER_T + SPIGOT_H / 2.0)))
    body = body + spigot

    # --- Subtract gripper-side bolt + shaft clearances (from _base) ---
    for hole in gripper_bolt_holes(ADAPTER_T):
        body = body - hole
    body = body - shaft_clearance_bore(ADAPTER_T)

    # The shaft bore must also pierce the spigot so the lip-seal stack can
    # pass cleanly — extend an extra Ø16 cylinder through the spigot height.
    # (The base helper only goes through the body thickness.)
    from motor.cad.adapters._base import (
        GRIPPER_SHAFT_OFFSET_X,
        GRIPPER_SHAFT_OFFSET_Y,
        GRIPPER_SHAFT_CLEARANCE_R,
    )
    spigot_pierce = Cylinder(
        radius=GRIPPER_SHAFT_CLEARANCE_R,
        height=SPIGOT_H + 1.0,
    ).moved(Location((
        GRIPPER_SHAFT_OFFSET_X,
        GRIPPER_SHAFT_OFFSET_Y,
        ADAPTER_T + (SPIGOT_H + 1.0) / 2.0 - 0.5,
    )))
    body = body - spigot_pierce

    # --- ISO bolt clearance through-holes (4 × Ø6.6) on Ø50 BCD ---
    iso_bolt_r = m_clearance_radius(ISO_M6)   # = 3.3
    h_through = ADAPTER_T + 1.0
    for (bx, by) in _bolt_xy():
        bore = Cylinder(radius=iso_bolt_r, height=h_through).moved(
            Location((bx, by, ADAPTER_T / 2.0)))
        body = body - bore

    # --- M6 SHCS counter-bores on the top face (sink Ø11 × 6.4 mm) ---
    for (bx, by) in _bolt_xy():
        cb = Cylinder(radius=COUNTERBORE_D / 2.0,
                      height=COUNTERBORE_DEPTH + 0.001).moved(
            Location((bx, by, ADAPTER_T - COUNTERBORE_DEPTH / 2.0 + 0.0005)))
        body = body - cb

    # --- Dowel pin hole (Ø6 H7) on +X axis at d1/2 radius ---
    # Hole opens from the top face and goes DOWEL_DEPTH deep.
    dowel = Cylinder(radius=ISO_DOWEL_D5 / 2.0,
                     height=DOWEL_DEPTH + 0.001).moved(
        Location((DOWEL_X, DOWEL_Y,
                  ADAPTER_T - DOWEL_DEPTH / 2.0 + 0.0005)))
    body = body - dowel

    return body


def gen_step() -> Compound:
    """Entry point for the repo's `step` CLI. Returns the adapter wrapped
    in a labelled, coloured `Compound` (PA12-GF print colour)."""
    part = build()
    return finalize(part, label="adapter_iso9409_50_4_M6", colour=C_PA12_GF)


if __name__ == "__main__":
    asm = gen_step()
    out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
    out_dir = os.path.normpath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "adapter_iso9409_50_4_M6.step")
    export_step(asm, out_path)
    print(f"wrote {out_path}")

# 3D-printing guide

How to print the geared four-bar / Fin Ray gripper (`gripper.py`, `README.md`).
This gripper is **fully 3D-printed with ZERO hardware** — no screws, no bolts, no
metal dowels. Every pivot is a printed snap pin and the front cover clicks on with
integral cantilever clips. This guide covers material profiles, per-part settings,
supportless orientations, and the fit-tuning workflow.

Companion documents:
- `UNDERWATER.md` — material chemistry and seawater prep.
- `ASSEMBLY.md` — assembly order and snap-fit insertion.
- `PRINT_PLATES.md` — plate layout, regeneration commands, bbox table.
- `MATERIALS.md` — when it exists: full material comparison, creep/UV/salt
  performance data. PETG-HF test prints defer long-term performance to that doc.

---

## Pinned materials (final build)

| Part(s) | Final material | Test-print substitute |
|---|---|---|
| `enclosure`, `front_cover` | **PA12-GF** (Nylon 12 glass-filled) | PETG-HF |
| `drive_arm_L`, `drive_arm_R`, `follower` (×2) | **PA12-GF** | PETG-HF |
| `input_pinion_shaft` | **PA12-GF** | PETG-HF |
| `snap_pin_axle` (×4) | **PA12-GF** | PETG-HF |
| `snap_pin_finger` (×4) | **PETG-HF** (final build) | — (already final material) |
| `finger_L`, `finger_R` | **TPU ether-based** (~95A Shore) | TPU ether-based (no substitute) |

PA12-GF is rigid and structural throughout; TPU is the compliant jaw.
`snap_pin_finger` is **PETG-HF in both test and final builds**: the snap barb
must flex repeatedly through the finger-pivot bore; PA12-GF is too brittle and
would crack the barb. The load-bearing counterbore socket in the PA12-GF enclosure
carries the structural load — the pin itself only needs ductility, not stiffness.
`input_pinion_shaft` is PA12-GF: the shaft journals benefit from glass-filled
stiffness and low creep to stay round under sustained load.

PETG-HF is **not** suitable for the seawater-structural parts (enclosure, cover,
arms, followers, axle dowels) — see `MATERIALS.md` when available.

---

## Drop-into-slicer plates (start here)

```bash
source /home/andre/.cad-venv/bin/activate
python export_parts.py          # parts/*.stl  (CLOSED pose, from gripper.py)
python make_print_plates.py     # print_plates/  (oriented + plated STLs)
```

Outputs (full layout in `PRINT_PLATES.md`):

- `print_plates/plate_rigid_1.stl` — all 15 rigid parts (PA12-GF or PETG-HF).
- `print_plates/plate_tpu_1.stl` — the 2 TPU Fin Ray fingers (separate material).
- `print_plates/oriented/<part>.stl` — each part alone, already oriented.

> **REGENERATE after any `gripper.py` geometry change:** `python export_parts.py
> && python make_print_plates.py`. The script wipes `print_plates/` on every run.

---

## Material profiles

### 1. PA12-GF — Nylon 12 glass-filled (final build: structural rigid parts)

PA12-GF is stiff, dimensionally stable, low creep, seawater-compatible and
pressure-cycle resistant. It is also hygroscopic and abrasive.

#### Nozzle — HARDENED STEEL OR RUBY IS MANDATORY

Glass fibre destroys brass nozzles within a few hundred grams. A brass nozzle is
not optional-upgrade territory; it will fail mid-print. Use a hardened-steel or
ruby-tipped nozzle.

**Critical: use a 0.4 mm hardened nozzle specifically for the axle snap pins.**
`SNAP_BARB_LIP_T = 1.0 mm` — the locking-lip axial wall is exactly 1.0 mm (see
`gripper.py` comment: "FLOOR: 2.5 perimeters @ 0.4 nozzle — do NOT reduce"). At
a 0.5 mm hardened nozzle this wall falls to 2.0 perimeters; at 0.6 mm it is only
1.67 perimeters. **The 0.4 mm hardened nozzle is required to keep the `snap_pin_axle`
lip wall robustly printed.** You may use a 0.4 mm hardened for the whole PA12-GF
rigid plate, or switch to it specifically for the `snap_pin_axle` oriented STLs.
(`snap_pin_finger` prints in PETG-HF with a brass 0.4 mm nozzle — same 0.4 mm
constraint applies, but brass is fine for non-abrasive PETG-HF.)

#### Filament drying — MANDATORY

PA12-GF is very hygroscopic. Wet filament causes:
- Stringing, bubbles, and poor layer adhesion (weakens snap barbs and clip roots).
- Dimensional errors that tighten bores (creep-proofing the snap fit depends on
  tight tolerances; wet PA12-GF drifts them).

**Drying protocol:**
- Dry all spools at **80°C for 8–12 hours** before printing (a convection oven or
  dedicated filament dryer; a food dehydrator at 80°C works).
- If your print runs more than 6–8 hours, run the spool live from a **dry box
  (desiccant box)** to maintain low moisture during the print.
- After drying: load into the dry box, begin printing within ~2 hours. Nylon
  re-saturates quickly in humid air.

#### Temperature and bed

| Parameter | Range | Notes |
|---|---|---|
| Nozzle | 270–290°C | Start at 275°C; raise to 290°C for better layer adhesion at the barb/clip region |
| Bed | 70–90°C | PEI textured sheet is reliable; or use Magigoo PA / glue stick on bare glass |
| Enclosure / chamber | 40–50°C | An enclosed chamber reduces warping significantly; if you have an open printer, a draft shield is required |
| Cooling fan | 10–20% max | High cooling causes layer delamination and warping; keep it minimal |

#### Warping mitigation

PA12-GF has higher shrinkage (~0.6–1.0%) than PETG (~0.3–0.5%) and warps if
the bed environment is uncontrolled.

- **Brim: 5–8 mm on all parts.** Mandatory on `enclosure` (large footprint),
  `front_cover` (wide), and the snap pins (tall, narrow).
- **Draft shield:** use a 2–3 layer draft shield on the enclosure; it reduces
  the in-print ambient temperature gradient around the large housing.
- **First layer:** slow (20–25 mm/s), slight over-extrusion (1.0–1.05 flow).
  A well-adhered first layer is the single most important warp-reduction step.
- **Don't open the chamber mid-print** on the large parts.

#### Shrinkage and bore calibration

Because PA12-GF shrinks ~0.6–1.0%, bores may print tighter than the PETG test
prints. **Before printing the full plate, print one `snap_pin_axle` and a scrap
bore coupon** (through-hole at nominal AXLE_BORE_R = 2.6 mm → Ø5.2 mm, matching
the real bore length). If the coupon bore is tight, increase `PRINT_CLEAR` to
0.35–0.40 in `gripper.py` and regenerate. Do this coupon test in PA12-GF
specifically — PETG-HF coupon results do not transfer.

#### Layer height, walls, infill

| Setting | Snap pins | Drive arms / followers | Enclosure / cover |
|---|---|---|---|
| Layer height | 0.15–0.20 mm | 0.15–0.20 mm (0.15 for gear teeth) | 0.20 mm |
| Perimeters/walls | **Solid (100%)** | **5–6** (shaft region: 6) | 4–5 |
| Infill | **100%** | 40–60% (shaft: 100%) | 15–25% (flange area: 25%) |
| Speed | Slow at barb: 20–25 mm/s | 40–50 mm/s | 40–50 mm/s |
| Cooling | Off at barb region | 10–20% | 10–20% |

The `SNAP_BARB_LIP_T = 1.0 mm` wall runs for the full locking-lip length. Keep
perimeters at ≥4 (0.4 mm nozzle = 2.5 perimeters minimum; 4 is safer). Do not
reduce wall count to speed the print.

For `input_pinion_shaft`: print with the shaft axis vertical (shaft pointing up).
This makes the shaft a self-supporting cylinder with strong layers along the
torque axis. The pinion and collar print as rings at various heights. Use
**100% infill + 6 perimeters** throughout. Print slow with minimal cooling at
the collar and pinion regions. Do not print shaft-horizontal — the cantilever
overhang would be too large.

#### Supports

**None required.** All orientations are supportless as determined by
`make_print_plates.py` (see §Supportless orientation table below and
`PRINT_PLATES.md`). One exception: the `enclosure` bottom mounting flange may
want a few support pillars under its outer edge — check the slicer preview; if it
droops, add 2–3 column supports there only. Also check the journal-bore overhangs
in the bottom wall.

#### Optional annealing

After printing, PA12-GF parts can be annealed at 80°C for 4 hours (free-air,
supported on a flat surface or packed in sand/cornstarch to prevent distortion).
Annealing relieves internal stress and raises crystallinity, improving stiffness
and creep resistance. Recommended for the drive arms and snap pins that will see
sustained load. Check dimensions after annealing — enclosure bore centres may
shift slightly; ream bores if needed.

#### Post-print moisture conditioning

Paradoxically, dry PA12-GF (just off the dryer) is slightly more brittle than
conditioned PA12-GF. Nylon reaches peak toughness after it has re-absorbed
~2–3% ambient moisture (equilibrium at ~50% RH). For the snap pins and cover
clips, where flex-fatigue is the failure mode, leave parts to condition at room
humidity for 24–48 hours before assembly or mechanical testing. Seawater
immersion will drive conditioning further; this is expected and beneficial.

---

### 2. PETG-HF — High-flow PETG (test prints + final `snap_pin_finger`)

PETG-HF is used for **fit testing, bore calibration, and assembly dry-runs** for
most parts, and is also the **final production material for the 4 `snap_pin_finger`
pins**. It prints fast, requires no special nozzle, and tolerates humidity.

**PETG-HF does NOT substitute for PA12-GF in the structural underwater parts.**
PETG creeps under sustained load, has poor UV resistance, and is not seawater-rated
for long-term submersion in a load-bearing role. The `snap_pin_finger` exception is
intentional: the barb must flex without cracking; PA12-GF is too brittle for that
snap-fit cycling, and the rigid PA12-GF counterbore socket handles the structural
load. All long-term performance data, creep margins, and underwater life for the
housing and drive parts are based on the PA12-GF parts. See `MATERIALS.md` once it
exists.

#### Temperature and bed

| Parameter | Range | Notes |
|---|---|---|
| Nozzle | 235–260°C | High-flow grades need the upper end (245–260°C) to keep up with print speed |
| Bed | 70–85°C | PEI textured or smooth glass with light hair-spray; PETG tends to over-stick to bare PEI — a release agent helps |
| Cooling | 30–60% | More than PA12-GF; PETG bridges better with cooling |
| Enclosure | Open OK | PETG does not warp badly at room temperature |

#### Nozzle for test prints

Standard brass 0.4 mm nozzle is fine — PETG is not abrasive.
**Exception:** if you are printing test snap pins to verify the `SNAP_BARB_LIP_T`
lip geometry, use 0.4 mm specifically so the wall count matches the final print
condition (0.4 mm for both the PETG-HF finger pins and the PA12-GF axle pins).
A 0.5 mm test-pin barb behaves differently from a 0.4 mm final pin.

#### Speed and layer height

PETG-HF can run faster than standard PETG. Use:
- Layer height: 0.2 mm (fast test); drop to 0.15 mm for gear-teeth test prints
  where you want realistic tooth-flank geometry.
- Speed: 60–80 mm/s perimeters, 100+ mm/s infill.
- Barb region: still slow to 25–30 mm/s and reduce cooling to 20–30% — a
  delaminated barb in the test print is a false failure signal.

#### Brim

A 3–5 mm brim is sufficient for PETG-HF (less warping than PA12-GF). Still use a
brim on the snap pins and enclosure for adhesion.

#### What to verify with PETG-HF test prints

1. **Snap-pin click** — print one `snap_pin_finger` + bore coupon. Confirm: inserts
   with moderate force, barb clicks past far face, resists pull-out. Tune
   `PRINT_CLEAR` here. Note: `snap_pin_finger` is **final build PETG-HF**, so a
   passing PETG-HF test pin is a valid final pin. For the `snap_pin_axle` pins
   (which are PA12-GF in the final build), also run a separate PA12-GF coupon
   — PA12-GF shrinks more and may need a higher `PRINT_CLEAR`.
2. **Cover snap engagement** — print `front_cover` in PETG-HF and snap it onto the
   PETG-HF enclosure. Check the four hooks seat positively and the cover removes
   without permanent deformation.
3. **Pivot clearance** — assemble drive arms / followers on snap pins and confirm
   they pivot freely without excessive slop.
4. **Finger fit** — snap the TPU fingers onto their pin pairs (these are the final
   TPU; print them once, skip PETG-HF substitution for fingers).

---

### 3. TPU ether-based — ~95A Shore (fingers, final material)

> **Selected filament: eSUN eTPU-95A on a Bambu Lab P1S (0.4 mm hardened nozzle).**
> For the complete, importable Bambu Studio profiles (filament + process) and every
> setting with rationale, see **`PRINT_PROFILE_P1S_TPU.md`**. The section below is the
> general (slicer-agnostic) TPU guidance.

The Fin Ray fingers are the compliance elements of the grip. They must flex
repeatedly without fatigue cracking. Use **ether-based** TPU (not ester-based) —
ether-based grades resist hydrolysis in seawater; ester-based grades degrade.
There is no test-print substitute: print the fingers in final TPU from the start.

#### Direct drive is required, not optional

High-retraction Bowden setups cannot handle TPU reliably at the wall thicknesses
and infill densities needed. The thin finger walls (contact beam **1.2 mm**, ribs
**1.6 mm**, spine **1.8 mm**) and the `FR_GRIP_DEPTH = 0.6 mm` grip teeth require
consistent extrusion control that only a direct-drive extruder provides.

#### Temperature and bed

| Parameter | Range | Notes |
|---|---|---|
| Nozzle | 220–235°C | Start at 225°C; raise if under-extrusion in the thin ribs |
| Bed | 30–50°C | Textured PEI, unheated also works; lightly wipe with IPA |
| Cooling | Off or 10% max | TPU needs interlayer adhesion; high cooling causes delamination at flex cycles |

#### Retraction

Use **0–1 mm retraction** (0.5 mm is a safe starting point). More retraction pulls
the soft filament back into the heatbreak and causes jams. If stringing is a
concern, manage it with temperature and print speed rather than retraction.

#### Print speed

**20–30 mm/s for all moves.** TPU requires slow, consistent extrusion. Faster
speeds cause inconsistent walls and poor rib-to-spar adhesion, which is the
fatigue failure origin. Infill can go slightly faster (30–40 mm/s) but keep
perimeters slow.

#### Layer height, walls, infill

| Setting | Value |
|---|---|
| Layer height | 0.15–0.20 mm |
| Perimeters | **wall-count = solid** at 0.4 mm nozzle: contact beam 1.2 mm = 3 perimeters, ribs 1.6 mm = 4, spine 1.8 mm ≈ 4–5. Set perimeters ≥ wall/0.4 so every member prints fully solid (no gaps inside a wall). |
| Infill | **100%** (the thin walls are perimeter-only anyway; 100% keeps the solid base floor/cap, bracket and grip-ridge insets dense — and **all FEA stats assume 100%-dense walls**, `fea/UNIVERSAL_FINGER.md`). |
| Seam | Rear/aligned; keep off the grip-ridge face |

The Fin Ray truss prints flat on its 28×96 Z-face (build height = 10 mm, cells in
the build plane). This orientation is self-supporting: the triangular cells,
ribs, and hollow interior need no supports — there are none to remove from the
flexible truss anyway.

The bending stress runs **along the layers** (in-plane) in this orientation — the
strong direction for fatigue. Do not rotate the fingers to print them standing up;
the rib overhangs would require internal supports that are impossible to extract
cleanly from a compliant part.

#### Brim and first layer

- **Brim: 3–5 mm.** TPU has moderate bed adhesion; a brim prevents the narrow
  finger from peeling during the print.
- **First-layer squish:** moderate squish on a textured PEI. Avoid over-squish —
  it closes up the bottom grip ridges and the `FR_BASE_CHAMFER = 0.5 mm` chamfer
  is there to give elephant's foot somewhere to go, but it has limits.
- **No heated bed above 50°C** — excessive bed heat makes TPU too tacky and the
  part is hard to remove without stretching.

#### Print-friendly geometry already in the model

Do not simplify these features:
- `FR_CELL_FILLET = 0.8 mm` — rounds interior rib-cell corners to eliminate
  fatigue-crack stress risers; also smooths the nozzle path.
- `FR_BASE_CHAMFER = 0.5 mm` — gives elephant's foot a relief on the bed face.
- `FR_TIP_FILLET = 1.5 mm` — rounds the blade apex so it prints as multi-bead
  geometry, not a single fragile line.
- `FR_GRIP_TIP_FLAT = 0.2 mm` — gives each grip tooth a printable flat tip.

---

## Supportless orientation table

All orientations were mesh-audited by `make_print_plates.py` (45° threshold).
The oriented STLs in `print_plates/oriented/` have these rotations pre-applied;
import the plate STLs directly and set "no supports" in your slicer.

| Part | Qty | Rotation from export pose | Build height | Support area | Notes |
|---|---|---|---|---|---|
| `enclosure` | 1 | None (as-exported) | 40.0 mm | ~1272 mm² (bridges interior ceilings) | Bottom flange down; check slicer for journal-bore overhangs |
| `front_cover` | 1 | 180° about X | 18.5 mm | 184 mm² (hook underlips bridge) | Flat outer face on bed; the 4 slim (2.0 mm) clips point up, their chamfered free tips at the print-top and self-supporting (hook-underlip bridge area unchanged) |
| `drive_arm_L` | 1 | None (as-exported) | 5.0 mm | 0 | Flat plate face-down (no integral shaft; crown ring prints as a ring at the top face) |
| `drive_arm_R` | 1 | None (as-exported) | 5.0 mm | 0 | Flat plate face-down |
| `input_pinion_shaft` | 1 | Shaft-axis vertical (coupler down) | ~40–50 mm | ~12 mm² (collar ring bridge) | Shaft as self-supporting vertical cylinder; pinion and collar print as rings; 100% infill, 6 perimeters, slow |
| `follower` | 2 | None (as-exported) | 5.0 mm | 0 | Flat bar face-down |
| `snap_pin_axle` | 4 | 180° about X | 23.0 mm | 0 | Head flange on bed; barb tip up |
| `snap_pin_finger` | 4 | 180° about X | 29.1 mm | 12 mm² (0.7 mm barb lip bridge) | Head flange on bed; barb tip up |
| `finger_R` | 1 | None (as-exported) | 10.0 mm | ~0 | Flat on 28×96 face; Fin Ray cells in build plane |
| `finger_L` | 1 | None (as-exported) | 10.0 mm | ~0 | Mirror of `finger_R` |

**Note on `drive_arm_L`:** now a flat gear plate like `drive_arm_R` — the crown
ring is a thin annular feature on its +Z face and prints cleanly face-up at the
plate surface. No shaft; no tall vertical feature. Same print settings as
`drive_arm_R`.

---

## Per-part quick-reference table

| Part | Qty | Material | Plate file | Orientation (Z-up in slicer) | Layer ht | Walls | Infill |
|---|---|---|---|---|---|---|---|
| `enclosure` | 1 | PA12-GF / PETG-HF | `plate_rigid_1` | Bottom-flange face down, cavity up | 0.20 mm | 4–5 | 15–25% |
| `front_cover` | 1 | PA12-GF / PETG-HF | `plate_rigid_1` | Flat outer face on bed, clips up | 0.20 mm | 4–5 | 30–50% |
| `drive_arm_L` | 1 | PA12-GF / PETG-HF | `plate_rigid_1` | Flat gear+arm plate face-down (crown ring face up) | 0.15–0.20 mm | 5–6 | 40–60% |
| `drive_arm_R` | 1 | PA12-GF / PETG-HF | `plate_rigid_1` | Flat gear+arm plate face-down | 0.15–0.20 mm | 5–6 | 40–60% |
| `input_pinion_shaft` | 1 | **PA12-GF** / PETG-HF | `plate_rigid_1` | Shaft-axis vertical, coupler end down | 0.15–0.20 mm | 6, solid | 100% |
| `follower` | 2 | PA12-GF / PETG-HF | `plate_rigid_1` | Flat bar face-down | 0.20 mm | 5–6 | 30–50% |
| `snap_pin_axle` | 4 | PA12-GF / PETG-HF | `plate_rigid_1` | Head on bed, barb up | 0.15–0.20 mm | solid | 100% |
| `snap_pin_finger` | 4 | **PETG-HF** (test + **final**) | `plate_rigid_1` | Head on bed, barb up | 0.15–0.20 mm | solid | 100% |
| `finger_R` | 1 | TPU ether-based | `plate_tpu_1` | Flat on 28×96 face | 0.15–0.20 mm | 3–4 | ≥80% |
| `finger_L` | 1 | TPU ether-based | `plate_tpu_1` | Flat on 28×96 face | 0.15–0.20 mm | 3–4 | ≥80% |
| **Total** | **17** | — | **2 plates** | — | — | — | — |

**Nozzle reminder:** 0.4 mm hardened steel/ruby for PA12-GF throughout. Brass 0.4
mm for PETG-HF and TPU test/production prints.

### Final-build material batches

The full build splits across three print batches:

**(a) PA12-GF batch** — `enclosure` ×1, `front_cover` ×1, `drive_arm_L` ×1,
`drive_arm_R` ×1, `input_pinion_shaft` ×1, `follower` ×2, `snap_pin_axle` ×4.
Dry spool 80°C/8–12 h, 0.4 mm hardened nozzle, brim + draft shield on the
enclosure. Print `input_pinion_shaft` shaft-axis vertical.

**(b) PETG-HF batch** — `snap_pin_finger` ×4. These 4 small finger pins print in
PETG-HF for the final build (barb ductility — see "Pinned materials" note above).
Because PETG-HF is already loaded for the test set, the finger pins can be added
to the PETG-HF test-print run as a small separate batch; no material change-over needed.

**(c) TPU batch** — `finger_L` ×1, `finger_R` ×1. Print once; reuse from test
set if test-print fingers passed fit check.

---

## Current clearance constants (from `gripper.py`)

These are the live values. Earlier prose versions of this doc had stale numbers;
trust the table below and `gripper.py` lines 107–133.

| Constant | Value | Controls |
|---|---|---|
| `PRINT_CLEAR` | **0.3 mm/side** | Pin-in-bore turning fit (pivot bore vs shank): `AXLE_BORE_R = 2.6 mm` → bore **Ø5.2 mm**, shank **Ø4.6 mm** |
| `SNAP_CLEAR` | 0.35 mm | Front-cover clip hook vs side-wall window engagement |
| `SNAP_BARB_PROUD` | **0.9 mm** | Snap-pin locking-lip protrusion past PIN_R (retention force) |
| `SNAP_BARB_LIP_T` | **1.0 mm** | Axial length of the locking-lip face — **2.5 perimeters @ 0.4 mm nozzle; do not reduce** |
| `SNAP_BARB_SEAT` | **1.2 mm** | Axial capture overlap of lip past far bore face |
| `SNAP_CB_RCLEAR` | 0.45 mm | Radial gap: counterbore pocket wall to lip |
| `SNAP_CB_FLOOR_CLEAR` | 0.30 mm | Axial gap: lip front face to pocket floor |

---

## Fit tuning — do this first

**Print ONE snap pin and a scrap bore coupon before printing the full sets.**

1. Print one `snap_pin_finger` in **PETG-HF** (brass 0.4 mm nozzle; head-down,
   axis-vertical, barb-up, 100% solid, slow at the barb). This is both a fit test
   and a valid final-build pin — `snap_pin_finger` stays in PETG-HF for the final
   build.
2. Print a scrap bore coupon: a small block with one through-hole at `AXLE_BORE_R =
   2.6 mm` → **Ø5.2 mm**. Match the bore length to the real joint stack so the
   lip emerges at the correct depth.
3. Push the pin through and feel for the click. You want: moderate insertion force,
   barb flexes and compresses, **audible/tactile click** as the lip springs into the
   counterbore pocket, and the pin resists pull-back.
   - No click / pulls out → raise `SNAP_BARB_PROUD` and/or `SNAP_BARB_SEAT`.
   - Too tight / barb shears → loosen `PRINT_CLEAR` or fix barb layer adhesion
     (hotter, slower, less cooling at the barb region).
   - Clicks but impossible to remove → lower `SNAP_BARB_PROUD`.
4. **For `snap_pin_axle` (PA12-GF final)**: run a separate coupon in PA12-GF.
   PA12-GF shrinks 0.6–1.0% vs PETG's 0.3–0.5%; bores will likely be tighter. If
   the coupon bore is tight, bump `PRINT_CLEAR` to 0.35–0.40 in `gripper.py` and
   regenerate before printing the full plate. PETG-HF coupon results do not
   transfer to PA12-GF axle pins.
5. Only once the single pin clicks cleanly, print the remaining 6 (and the
   `front_cover`, whose clips use the same flex principle).

---

## Quick start — print then assemble

### Step 1: PETG-HF test set (fit verification)

1. Generate plates:
   ```bash
   source /home/andre/.cad-venv/bin/activate
   python export_parts.py && python make_print_plates.py
   ```
2. Print `plate_rigid_1.stl` in **PETG-HF** (brass 0.4 mm nozzle, 0.2 mm layers,
   no supports, 3–5 mm brim).
3. Print `plate_tpu_1.stl` in **TPU ether-based** (direct drive, 0.15–0.20 mm, slow).
4. Run the fit-tuning checklist: snap-pin click, cover snap, pivot clearances.
5. Adjust `PRINT_CLEAR` / `SNAP_BARB_PROUD` if needed, then regenerate.

### Step 2: PA12-GF final build (structural parts)

1. Dry PA12-GF spools: **80°C / 8–12 h**. Load into dry box.
2. Install **0.4 mm hardened-steel or ruby nozzle**.
3. Print the PA12-GF parts from `plate_rigid_1.stl` — all parts **except** the 4
   `snap_pin_finger` pins — in **PA12-GF**:
   - Nozzle 275–290°C, bed 75–85°C (Magigoo PA or PEI textured).
   - 5–8 mm brim + draft shield on enclosure.
   - 0.20 mm layers (0.15 mm option for gear teeth).
   - Slow the snap-pin-axle barb region to 20–25 mm/s, cooling ≤20%.
4. Print the 4 `snap_pin_finger` pins in **PETG-HF** (same profile as Step 1 —
   add them to that run or print as a small separate batch). These are **final
   build** pins; PETG-HF is correct here for barb ductility (see "Pinned
   materials" and "Final-build material batches" above).
5. Run bore coupon in PA12-GF (see Fit tuning) before the full plate.
6. TPU fingers are already printed; reuse them.
7. Optional: anneal PA12-GF structural parts at 80°C / 4 h, then condition 24–48 h
   at room humidity before assembly (toughness peaks after re-absorbed moisture).

### Step 3: Assemble

See `ASSEMBLY.md` for the full sequence. Brief order:
1. Deburr all pivot bores (countersink bit by hand); clear snap-pin `+` slots.
2. Snap `snap_pin_finger` pins through each finger mounting eye; fingers click onto
   the coupler.
3. Drop drive arms and followers into the enclosure on the `snap_pin_axle` pins.
4. Push-on the `front_cover` — 4 hooks click; no tools needed.
5. Function check: rotate `input_pinion_shaft` bottom D-coupler; both fingers
   open/close symmetrically.

---

## Post-processing checklist

- **Deburr all pivot bores.** A countersink bit or a drill run by hand chamfers the
  bore mouth so the snap-pin lead-in cone starts cleanly. Burrs shave the barb
  on insertion.
- **Clear the snap-pin `+` split slots.** If a slot fused shut, open it with a
  fine blade. A fused slot doesn't flex; the barb won't compress on insertion.
- **Test-flex each barb and clip before assembly.** A barb that shears on dry test
  is a print-settings failure (interlayer adhesion), not a geometry failure. Fix
  it now, not mid-assembly.
- **Clean gear flanks.** Knock down layer ridges and seam witness marks on the
  tooth flanks. Cycle the mesh by hand; sand tight spots lightly.
- **TPU fingers:** trim any stringing, confirm grip ridges are crisp and the cells
  flex smoothly under finger pressure.
- **Seam placement in slicer:** set seam to Rear/Aligned on drive arms so it lands
  away from meshing tooth flanks. On snap pins, place the seam on the head flange
  or solid shank — not on the barb fingers (seam is a crack starter under flex).

---

## Print order checklist (full build)

1. Calibrate — XY tolerance coupon + pin-in-hole coupon in both filaments.
2. Fit-tune snap pins — one `snap_pin_finger` + scrap bore coupon; verify click.
3. Bore coupon in PA12-GF — confirm shrinkage doesn't close Ø5.2 bores.
4. Enclosure — bottom-flange down; brim + draft shield; check slicer for
   journal-bore overhangs; support if needed.
5. Drive arms ×2 — fine layers, high perimeters; both print flat (gear plate on
   bed); `drive_arm_L` crown ring faces up.
6. `input_pinion_shaft` — shaft-axis vertical, 100% infill, 6 perimeters; slow
   with minimal cooling at the collar and pinion regions.
7. Followers ×2 — flat, high perimeters.
8. Front cover ×1 — outer face down, clips up.
9. Snap pins: `snap_pin_axle` ×4 in **PA12-GF** + `snap_pin_finger` ×4 in
   **PETG-HF** — head-down, barb-up, 100% solid, slow at barb.
10. Fin Ray fingers ×2 — TPU flat on side face, slow, ≥80% infill.
11. Post-process — deburr bores (including journal bores), clear slots,
    test-flex barbs and clips.
12. (PA12-GF) anneal + condition if desired.
13. Dry-fit — snap axle pins; arms and followers pivot freely; mesh gears;
    confirm `input_pinion_shaft` drops into journals and collar seats.
14. Assemble — drop `input_pinion_shaft` into bottom journals; fingers on C/D
    pins; mechanism into housing on A/B pins; snap front cover.
15. Function check — rotate bottom D-shaft; both fingers open/close symmetrically.
16. Read `UNDERWATER.md` before it gets wet.

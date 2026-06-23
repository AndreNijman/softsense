# 3D-printing guide

How to print the geared four-bar / Fin Ray gripper (`gripper.py`, `README.md`).
This gripper is **fully 3D-printed with ZERO bought hardware** — no screws, no
bolts, no metal dowels. Every pivot is a plain printed journal pin retained by a
heat-staked (melt-riveted) cap, and the front cover clicks on with integral
cantilever clips. The one tool the build needs is a **soldering iron** to melt the
8 caps. This guide covers material profiles, per-part settings, supportless
orientations, and the fit-tuning workflow.

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
| `melt_pin_axle` (×4) | **PETG-HF** (final build) | — (already final material) |
| `melt_pin_finger_C` (×2), `melt_pin_finger_D` (×2) | **PETG-HF** (final build) | — (already final material) |
| `melt_cap` (×8) | **PETG-HF** (final build) | — (already final material) |
| `finger_L`, `finger_R` | **TPU ether-based** (~95A Shore) | TPU ether-based (no substitute) |

PA12-GF is rigid and structural throughout; TPU is the compliant jaw.
All 8 pivot pins (`melt_pin_axle` ×4, `melt_pin_finger_C` ×2, `melt_pin_finger_D`
×2) and all 8 `melt_cap` retaining caps are **PETG-HF in both test and final
builds**: PETG-HF heat-stakes cleanly under a soldering iron, forming a wide
thermal-rivet head over each pin's melt-stud. Glass-filled PA12-GF does **not**
heat-stake well — the glass fibre fights a clean melt-flow, so the pins and caps
are PETG-HF, not PA12-GF. The pin is a plain printed journal; retention is the
formed cap head, not a press fit or a snap. The rigid PA12-GF bore carries the
structural load. `input_pinion_shaft` is PA12-GF: the shaft journals benefit from
glass-filled stiffness and low creep to stay round under sustained load.

PETG-HF is **not** suitable for the seawater-structural parts (enclosure, cover,
arms, followers) — see `MATERIALS.md` when available.

---

## Drop-into-slicer plates (start here)

```bash
source /home/andre/.cad-venv/bin/activate
python export_parts.py          # parts/*.stl  (CLOSED pose, from gripper.py)
python make_print_plates.py     # print_plates/  (oriented + plated STLs)
```

Outputs (full layout in `PRINT_PLATES.md`):

- `print_plates/plate_rigid_1.stl` — the rigid PA12-GF parts (body, cover, arms,
  followers, input pinion shaft).
- `print_plates/plate_petg_1.stl` — the 8 PETG-HF pins (`melt_pin_axle` ×4,
  `melt_pin_finger_C` ×2, `melt_pin_finger_D` ×2) + 8 `melt_cap` retaining caps.
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

**Use a 0.4 mm hardened nozzle for the whole PA12-GF rigid plate** — the standard
nozzle size for the gear teeth and thin clip walls, and required because PA12-GF
glass fibre is abrasive (see above). The pins are no longer on this plate: all 8
journal pins and 8 caps are plain PETG-HF parts and print on the PETG-HF plate
with a brass 0.4 mm nozzle. There is no barb-lip wall to protect anymore — the
pins are plain stepped cylinders — so the old `SNAP_BARB_LIP_T` perimeter-count
constraint no longer applies to nozzle choice.

#### Filament drying — MANDATORY

PA12-GF is very hygroscopic. Wet filament causes:
- Stringing, bubbles, and poor layer adhesion (weakens clip roots and bore walls).
- Dimensional errors that tighten the pivot bores (a clean turning fit depends on
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
| Nozzle | 270–290°C | Start at 275°C; raise to 290°C for better layer adhesion at the clip region |
| Bed | 70–90°C | PEI textured sheet is reliable; or use Magigoo PA / glue stick on bare glass |
| Enclosure / chamber | 40–50°C | An enclosed chamber reduces warping significantly; if you have an open printer, a draft shield is required |
| Cooling fan | 10–20% max | High cooling causes layer delamination and warping; keep it minimal |

#### Warping mitigation

PA12-GF has higher shrinkage (~0.6–1.0%) than PETG (~0.3–0.5%) and warps if
the bed environment is uncontrolled.

- **Brim: 5–8 mm on all parts.** Mandatory on `enclosure` (large footprint) and
  `front_cover` (wide). (The pins are no longer PA12-GF; they print on the PETG-HF
  plate — see that section for their brim.)
- **Draft shield:** use a 2–3 layer draft shield on the enclosure; it reduces
  the in-print ambient temperature gradient around the large housing.
- **First layer:** slow (20–25 mm/s), slight over-extrusion (1.0–1.05 flow).
  A well-adhered first layer is the single most important warp-reduction step.
- **Don't open the chamber mid-print** on the large parts.

#### Shrinkage and bore calibration

Because PA12-GF shrinks ~0.6–1.0%, the pivot bores in the PA12-GF parts may print
tighter than the PETG test prints. The pins themselves are PETG-HF, but the bores
they turn in are PA12-GF, so the turning fit depends on PA12-GF shrinkage.
**Before printing the full plate, print a scrap PA12-GF bore coupon** (through-hole
at nominal AXLE_BORE_R = 2.6 mm → Ø5.2 mm, matching the real bore length) and slip
a PETG-HF pin through it. If the fit is tight, increase `PRINT_CLEAR` to 0.35–0.40
in `gripper.py` and regenerate. Do this coupon test in PA12-GF specifically —
PETG-HF coupon bores do not transfer.

#### Layer height, walls, infill

| Setting | Drive arms / followers | Enclosure / cover |
|---|---|---|
| Layer height | 0.15–0.20 mm (0.15 for gear teeth) | 0.20 mm |
| Perimeters/walls | **5–6** (shaft region: 6) | 4–5 |
| Infill | 40–60% (shaft: 100%) | 15–25% (flange area: 25%) |
| Speed | 40–50 mm/s | 40–50 mm/s |
| Cooling | 10–20% | 10–20% |

The pins are not on this plate — they are plain PETG-HF stepped cylinders (see the
PETG-HF section). For the PA12-GF parts, do not reduce wall count to speed the
print: the gear teeth and clip roots need full walls.

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
and creep resistance. Recommended for the drive arms and enclosure that will see
sustained load. Check dimensions after annealing — enclosure bore centres may
shift slightly; ream bores if needed.

#### Post-print moisture conditioning

Paradoxically, dry PA12-GF (just off the dryer) is slightly more brittle than
conditioned PA12-GF. Nylon reaches peak toughness after it has re-absorbed
~2–3% ambient moisture (equilibrium at ~50% RH). For the cover clips, where
flex-fatigue is the failure mode, leave parts to condition at room humidity for
24–48 hours before assembly or mechanical testing. Seawater
immersion will drive conditioning further; this is expected and beneficial.

---

### 2. PETG-HF — High-flow PETG (test prints + final pins & caps)

PETG-HF is used for **fit testing, bore calibration, and assembly dry-runs** for
most parts, and is also the **final production material for all 8 journal pins
(`melt_pin_axle` ×4, `melt_pin_finger_C` ×2, `melt_pin_finger_D` ×2) and all 8
`melt_cap` retaining caps**. It prints fast, requires no special nozzle, and
tolerates humidity.

**PETG-HF does NOT substitute for PA12-GF in the structural underwater parts.**
PETG creeps under sustained load, has poor UV resistance, and is not seawater-rated
for long-term submersion in a load-bearing role. The pin/cap exception is
intentional: PETG-HF heat-stakes cleanly under a soldering iron, forming a wide
thermal-rivet head; glass-filled PA12-GF does not heat-stake well (the glass fibre
fights a clean melt-flow). The pins are non-structural plain journals — the rigid
PA12-GF bore handles the load. All long-term performance data, creep margins, and
underwater life for the housing and drive parts are based on the PA12-GF parts.
See `MATERIALS.md` once it exists.

#### Temperature and bed

| Parameter | Range | Notes |
|---|---|---|
| Nozzle | 235–260°C | High-flow grades need the upper end (245–260°C) to keep up with print speed |
| Bed | 70–85°C | PEI textured or smooth glass with light hair-spray; PETG tends to over-stick to bare PEI — a release agent helps |
| Cooling | 30–60% | More than PA12-GF; PETG bridges better with cooling |
| Enclosure | Open OK | PETG does not warp badly at room temperature |

#### Nozzle for test prints

Standard brass 0.4 mm nozzle is fine — PETG is not abrasive. The pins are plain
stepped cylinders printed on the PETG-HF plate, so there is no barb-lip wall whose
perimeter count depends on nozzle size; a 0.4 mm nozzle is simply the default for
the rest of the build.

#### Speed and layer height

PETG-HF can run faster than standard PETG. Use:
- Layer height: 0.2 mm (fast test); drop to 0.15 mm for gear-teeth test prints
  where you want realistic tooth-flank geometry.
- Speed: 60–80 mm/s perimeters, 100+ mm/s infill.
- Pins: the melt-stud and head are plain solid stepped cylinders; print them at a
  moderate 30–40 mm/s with adequate cooling so the small layers set cleanly. No
  barb bridge to slow for.

#### Brim

A 3–5 mm brim is sufficient for PETG-HF (less warping than PA12-GF). Still use a
brim on the pins (tall, narrow), the tiny `melt_cap` discs, and the enclosure for
adhesion.

#### What to verify with PETG-HF test prints

1. **Pin + cap heat-stake** — print one melt pin (`melt_pin_finger_C` or
   `melt_pin_axle`), one `melt_cap`, and a scrap bore coupon. Slip the pin through
   the bore, slip the cap onto the protruding melt-stud, and fuse it with a
   soldering iron. Confirm: the pin turns freely in the bore, the melt-stud clears
   the cap bore, and the formed cap head is wider than the bore and holds the
   stack. Tune `PRINT_CLEAR` here for the turning fit. All pins and caps are
   **final-build PETG-HF**, so a passing test part is a valid final part — there is
   no separate PA12-GF axle-pin coupon (the pins are no longer PA12-GF).
2. **Cover snap engagement** — print `front_cover` in PETG-HF and snap it onto the
   PETG-HF enclosure. Check the four hooks seat positively and the cover removes
   without permanent deformation.
3. **Pivot clearance** — assemble drive arms / followers on the pins and confirm
   they pivot freely without excessive slop.
4. **Finger fit** — fit the TPU fingers onto their pin pairs (these are the final
   TPU; print them once, skip PETG-HF substitution for fingers).

---

### 3. TPU ether-based — ~95A Shore (fingers, final material)

> **Selected filament: Bambu TPU 95A HF on a Bambu Lab P1S (0.4 mm hardened nozzle).**
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
| Nozzle | 220–240°C | Bambu TPU 95A HF band; start at 230°C (Bambu's specimen temp); raise if under-extrusion in the thin ribs |
| Bed / plate | 30–35°C, **Textured PEI, NO glue** | Bambu Wiki: textured PEI grips TPU without adhesive; glue there over-adheres. Low bed temp keeps the large flat footprint removable (cool, lift corner, IPA, peel). A *smooth* Cool/Engineering plate would need glue as a release barrier instead. |
| Drying | 70°C ≥ 8 h | Bambu spec (was 55°C/4 h for eSUN); HF is humidity-sensitive — keep in a dry box |
| Cooling | fan on (this build: 50–80%) | TPU needs interlayer adhesion; the finger flexes in service, so the profile runs lower fan to protect Z-bonds (see PRINT_PROFILE §3) |

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
| `melt_pin_axle` | 4 | 180° about X | 23.0 mm | 0 | Head down on bed; melt-stud up; plain stepped cylinder, self-supporting |
| `melt_pin_finger_C` | 2 | 180° about X | ~29 mm | 0 | LONG crank-layer pin; head down on bed; melt-stud up; plain stepped cylinder |
| `melt_pin_finger_D` | 2 | 180° about X | ~24 mm | 0 | SHORT follower-layer pin; head down on bed; melt-stud up; plain stepped cylinder |
| `melt_cap` | 8 | None (head/disc on bed) | ~3 mm | 0 | Tiny PETG-HF retaining cap; disc face on bed, bore up; no supports |
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
| `melt_pin_axle` | 4 | **PETG-HF** (test + **final**) | `plate_petg_1` | Head down on bed, melt-stud up | 0.15–0.20 mm | solid | 100% |
| `melt_pin_finger_C` | 2 | **PETG-HF** (test + **final**) | `plate_petg_1` | Head down on bed, melt-stud up (LONG, crank layer) | 0.15–0.20 mm | solid | 100% |
| `melt_pin_finger_D` | 2 | **PETG-HF** (test + **final**) | `plate_petg_1` | Head down on bed, melt-stud up (SHORT, follower layer) | 0.15–0.20 mm | solid | 100% |
| `melt_cap` | 8 | **PETG-HF** (test + **final**) | `plate_petg_1` | Disc face on bed, bore up | 0.15–0.20 mm | solid | 100% |
| `finger_R` | 1 | TPU ether-based | `plate_tpu_1` | Flat on 28×96 face | 0.15–0.20 mm | 3–4 | ≥80% |
| `finger_L` | 1 | TPU ether-based | `plate_tpu_1` | Flat on 28×96 face | 0.15–0.20 mm | 3–4 | ≥80% |
| **Total** | **25** | — | **3 plates** | — | — | — | — |

**Nozzle reminder:** 0.4 mm hardened steel/ruby for PA12-GF throughout. Brass 0.4
mm for PETG-HF (pins + caps) and TPU test/production prints.

### Final-build material batches

The full build splits across three print batches:

**(a) PA12-GF batch** — `enclosure` ×1, `front_cover` ×1, `drive_arm_L` ×1,
`drive_arm_R` ×1, `input_pinion_shaft` ×1, `follower` ×2. Dry spool 80°C/8–12 h,
0.4 mm hardened nozzle, brim + draft shield on the enclosure. Print
`input_pinion_shaft` shaft-axis vertical. The pins are **not** on this plate.

**(b) PETG-HF batch** — all 8 journal pins (`melt_pin_axle` ×4,
`melt_pin_finger_C` ×2, `melt_pin_finger_D` ×2) + 8 `melt_cap` retaining caps.
These print in PETG-HF for the final build (PETG-HF heat-stakes cleanly; PA12-GF
does not — see "Pinned materials" note above). Because PETG-HF is already loaded
for the test set, the pins and caps can be added to the PETG-HF test-print run as
a small separate batch; no material change-over needed.

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

The pins are now plain journals retained by a heat-staked `melt_cap` (the formed
cap head is the retention, not a snap barb). The old `SNAP_BARB_*` and
`SNAP_CB_*` knobs no longer exist — retention is the melted cap, sized by the
melt-stud and cap geometry in `gripper.py`, not a tunable barb.

---

## Fit tuning — do this first

**Print ONE pin, ONE cap, and a scrap bore coupon before printing the full sets.**
You will need a **soldering iron** for this step (and for final assembly).

1. Print one melt pin in **PETG-HF** (brass 0.4 mm nozzle; head-down, axis-vertical,
   melt-stud up, 100% solid). A plain stepped cylinder — no barb, no `+` slot, no
   bridge. This is both a fit test and a valid final-build pin.
2. Print one `melt_cap` in PETG-HF (tiny disc, bore up). And print a scrap bore
   coupon: a small block with one through-hole at `AXLE_BORE_R = 2.6 mm` →
   **Ø5.2 mm**. Match the bore length to the real joint stack so the melt-stud
   protrudes at the correct depth on the far side.
3. Slip the pin through the bore, slip the cap onto the protruding melt-stud, and
   melt the stud with a soldering iron so it mushrooms into a head wider than the
   cap bore. You want: the pin turns freely in the bore (no bind), and the formed
   head retains the cap/stack and resists pull-back.
   - Pin binds / too tight in the bore → loosen `PRINT_CLEAR` (more clearance).
   - Pin too loose / sloppy → tighten `PRINT_CLEAR`.
   - Formed head too small to hold → leave more melt-stud proud, or melt more
     material; the retention is the cap head, not a tunable barb.
4. **For the PA12-GF bores**: run a separate scrap coupon in PA12-GF and slip a
   PETG-HF pin through it. PA12-GF shrinks 0.6–1.0% vs PETG's 0.3–0.5%; the bores
   will likely be tighter. If the fit is tight, bump `PRINT_CLEAR` to 0.35–0.40 in
   `gripper.py` and regenerate before printing the full plate. PETG-HF coupon
   bores do not transfer to PA12-GF.
5. Only once the single pin/cap heat-stakes cleanly, print the remaining pins and
   caps (and the `front_cover`, whose clips use a separate snap-flex principle).

---

## Quick start — print then assemble

### Step 1: PETG-HF test set (fit verification)

1. Generate plates:
   ```bash
   source /home/andre/.cad-venv/bin/activate
   python export_parts.py && python make_print_plates.py
   ```
2. Print `plate_rigid_1.stl` and `plate_petg_1.stl` (pins + caps) in **PETG-HF**
   (brass 0.4 mm nozzle, 0.2 mm layers, no supports, 3–5 mm brim).
3. Print `plate_tpu_1.stl` in **TPU ether-based** (direct drive, 0.15–0.20 mm, slow).
4. Run the fit-tuning checklist: pin/cap heat-stake, cover snap, pivot clearances.
5. Adjust `PRINT_CLEAR` if needed for the turning fit, then regenerate.

### Step 2: PA12-GF final build (structural parts)

1. Dry PA12-GF spools: **80°C / 8–12 h**. Load into dry box.
2. Install **0.4 mm hardened-steel or ruby nozzle**.
3. Print the PA12-GF parts from `plate_rigid_1.stl` in **PA12-GF**:
   - Nozzle 275–290°C, bed 75–85°C (Magigoo PA or PEI textured).
   - 5–8 mm brim + draft shield on enclosure.
   - 0.20 mm layers (0.15 mm option for gear teeth).
4. Print the 8 pins + 8 `melt_cap` caps from `plate_petg_1.stl` in **PETG-HF**
   (same profile as Step 1 — add them to that run or print as a small separate
   batch). These are **final build** parts; PETG-HF is correct here because it
   heat-stakes cleanly and PA12-GF does not (see "Pinned materials" and
   "Final-build material batches" above).
5. Run a PA12-GF bore coupon (see Fit tuning) before the full plate.
6. TPU fingers are already printed; reuse them.
7. Optional: anneal PA12-GF structural parts at 80°C / 4 h, then condition 24–48 h
   at room humidity before assembly (toughness peaks after re-absorbed moisture).

### Step 3: Assemble

See `ASSEMBLY.md` for the full sequence. Brief order (needs a **soldering iron**):
1. Deburr all pivot bores (countersink bit by hand).
2. Slip the finger pins (`melt_pin_finger_C` long / `melt_pin_finger_D` short)
   through each finger mounting eye; slip a `melt_cap` over each protruding
   melt-stud and fuse it with a soldering iron to lock the pin.
3. Drop drive arms and followers into the enclosure on the `melt_pin_axle` pins,
   capping and heat-staking each one the same way.
4. Push-on the `front_cover` — 4 hooks click; no tools needed.
5. Function check: rotate `input_pinion_shaft` bottom D-coupler; both fingers
   open/close symmetrically.

---

## Post-processing checklist

- **Deburr all pivot bores.** A countersink bit or a drill run by hand chamfers the
  bore mouth so the pin enters cleanly and turns freely. Burrs bind the pin.
- **Check the melt-stud and cap bore.** Confirm each pin's melt-stud is clean and
  proud, and each `melt_cap` bore slips over it. A stub too short won't form a head;
  a fused/oversize stud won't take the cap.
- **Test-flex each cover clip before assembly.** A clip that shears on dry test is a
  print-settings failure (interlayer adhesion), not a geometry failure. Fix it now,
  not mid-assembly.
- **Clean gear flanks.** Knock down layer ridges and seam witness marks on the
  tooth flanks. Cycle the mesh by hand; sand tight spots lightly.
- **TPU fingers:** trim any stringing, confirm grip ridges are crisp and the cells
  flex smoothly under finger pressure.
- **Seam placement in slicer:** set seam to Rear/Aligned on drive arms so it lands
  away from meshing tooth flanks. On the pins, place the seam on the solid shank or
  head — not on the melt-stud, so the stud melts evenly into a clean rivet head.

---

## Print order checklist (full build)

1. Calibrate — XY tolerance coupon + pin-in-hole coupon in both filaments.
2. Fit-tune pins — one melt pin + one `melt_cap` + scrap bore coupon; verify the
   turning fit and the heat-staked cap head (soldering iron).
3. Bore coupon in PA12-GF — confirm shrinkage doesn't close Ø5.2 bores.
4. Enclosure — bottom-flange down; brim + draft shield; check slicer for
   journal-bore overhangs; support if needed.
5. Drive arms ×2 — fine layers, high perimeters; both print flat (gear plate on
   bed); `drive_arm_L` crown ring faces up.
6. `input_pinion_shaft` — shaft-axis vertical, 100% infill, 6 perimeters; slow
   with minimal cooling at the collar and pinion regions.
7. Followers ×2 — flat, high perimeters.
8. Front cover ×1 — outer face down, clips up.
9. Pins + caps (PETG-HF): `melt_pin_axle` ×4 + `melt_pin_finger_C` ×2 +
   `melt_pin_finger_D` ×2 + `melt_cap` ×8 — head-down, melt-stud up, 100% solid,
   plain stepped cylinders (no supports).
10. Fin Ray fingers ×2 — TPU flat on side face, slow, ≥80% infill.
11. Post-process — deburr bores (including journal bores), check melt-studs and
    cap bores, test-flex cover clips.
12. (PA12-GF) anneal + condition if desired.
13. Dry-fit — pins drop through bores; arms and followers pivot freely; mesh gears;
    confirm `input_pinion_shaft` drops into journals and collar seats.
14. Assemble (soldering iron) — drop `input_pinion_shaft` into bottom journals;
    finger pins (C long / D short) through the finger eyes; mechanism into housing
    on the axle pins; heat-stake a `melt_cap` onto every pin's melt-stud; snap
    front cover.
15. Function check — rotate bottom D-shaft; both fingers open/close symmetrically.
16. Read `UNDERWATER.md` before it gets wet.

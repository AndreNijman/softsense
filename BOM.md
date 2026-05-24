# Bill of Materials — Underwater geared four-bar / Fin Ray gripper (FULLY 3D-PRINTED)

Production BOM for the gripper defined in `gripper.py` (geared four-bar, single
input shaft, compliant TPU Fin Ray fingers, **flooded** housing for underwater
use). This is the *what-to-print* list — and for this revision that is the
**entire** list. See `PRINTING.md` for how to orient and slice each part,
`UNDERWATER.md` for material chemistry in seawater, and `ASSEMBLY.md` for the
tool-free snap-together sequence.

> # ZERO bought hardware inside the gripper. No screws, no nuts, no bolts, no bushings.
> **Every gripper part is 3D-printed and snaps or slides together by hand — tool-free
> assembly.** The 4 axle pins are plain headed dowels captured geometrically
> between the back-wall bore step and the front-cover boss. The 4 finger pins
> are barbed push-to-snap pins with rigid counterbore capture. The front cover
> is held by 4 integral printed cantilever snap clips. The input shaft turns in
> two flooded journal bearings — no metal bushing. The **only** non-printed items
> in the whole system are the user's waterproof actuator (bottom D-shaft) and,
> at the robot-arm interface, the user's M4 mount bolts + nylon/PTFE
> galvanic-isolating washers (per `UNDERWATER.md` §5).

Headline build target: **flooded, all-polymer, fastener-free.** Nothing to seal,
nothing to buy inside the gripper, and no metal anywhere in the gripper.

---

## 1. Printed parts (the complete BOM)

Everything below is emitted by `gripper.gen_step()` (verified against the live
`gen_step()` output: 17 children, labels as listed). The enclosure floods through
its drain holes; the mechanism drops in; the axle dowels are captured between
back-wall step and cover boss; the finger snap pins latch in rigid counterbore
pockets; the cover snaps on. Done.

**Material legend:** FINAL = production print material. TEST = test-print material.
The 4 finger snap pins are the sole exception to the otherwise all-PA12-GF rigid
build — see note below the table.

| Part | Qty | **FINAL material** | Test-print | Rough filament | Role / key detail |
|---|---|---|---|---|---|
| `enclosure` | 1 | **PA12-GF (Nylon 12 glass-filled)** | PETG-HF | ~80–110 g | Flooded gearbox body. Open front, flush, full-width integrated base with chamfered bottom perimeter (4 × M4 clearance holes), top link slots, 4 back-wall axle bosses + stepped bores (wide running bore + narrow flood hole), upper + lower journal bores + collar pocket for the vertical input shaft in the bottom wall, bottom drains (4 positions × 2 Z = 8 holes) + 2 side drains, 4 snap-clip catch windows in the long side walls. Never PLA. |
| `front_cover` | 1 | **PA12-GF** | PETG-HF | ~20–30 g | Closes the open front; 4 inner-face bosses cap the axle-dowel heads (+Z dowel stop); **4 integral cantilever snap clips** (2 per long side, `SNAP_Z0=1.5` — lengthened arm, 1.85 % worst-tight strain, within PA12-GF allowable) latch into body side-wall windows; **3 × Ø1.8 mm vent holes** at (±34, +12). Push on to click; flex 4 hooks outward to release. |
| `drive_arm_R` | 1 | **PA12-GF** | PETG-HF | ~12–18 g | Right gear sector + crank arm. Clearance-bored at A_R (rides on axle dowel `pin_A_R`). Counterbored C-eye exit (−Z face) for `pin_C_R` geometric capture. Flat plate; prints face-down. |
| `drive_arm_L` | 1 | **PA12-GF** | PETG-HF | ~12–18 g | Left gear sector + crank arm + **integral CROWN gear** on its +Z face (driven by the input pinion via the right-angle stage). Clearance-bored at A_L (rides on axle dowel `pin_A_L`). Counterbored C-eye for `pin_C_L`. Flat plate; prints face-down. |
| `input_pinion_shaft` | 1 | **PA12-GF** | PETG-HF | ~8–12 g | ONE printed part: spur input pinion + vertical shaft + integral capture collar + bottom D-profile coupler (r 5.0, D-flat depth 1.4, length 12 mm). Axis vertical (exits the housing bottom). Two journal bearings in the housing (upper 2 mm, lower 7 mm); collar (OD 5.8 mm) trapped in a housing pocket between the two bore-mouth shoulders for axial capture (zero hardware). Print shaft-axis vertical for a self-supporting cylinder. |
| `follower_R` | 1 | **PA12-GF** | PETG-HF | ~6–9 g | Right B→D link bar. Counterbored D-eye exit (−Z face) for `pin_D_R` geometric capture. Flat plate; prints face-down. |
| `follower_L` | 1 | **PA12-GF** | PETG-HF | ~6–9 g | Left B→D link bar. Counterbored D-eye exit (−Z face) for `pin_D_L`. Same geometry as `follower_R` (mirrored in gen_step). |
| `finger_R` | 1 | **Ether-based TPU ~95A** — NOT ester-based | TPU | ~25–35 g | Right Fin Ray compliant jaw. Grip ridges on contact face; internal slanted-rib truss; mount holes at C_R and D_R. Must flex — print in TPU only. |
| `finger_L` | 1 | **Ether-based TPU ~95A** | TPU | ~25–35 g | Left Fin Ray compliant jaw (chiral mirror of `finger_R`). |
| `pin_A_R` | 1 | **PA12-GF** | PETG-HF | ~1–2 g | **Axle dowel** for right drive-arm pivot (A_R). Plain head + shank + narrow pilot tip. No barb — rigid geometric sandwich (head vs cover boss; shoulder vs stepped bore step). |
| `pin_A_L` | 1 | **PA12-GF** | PETG-HF | ~1–2 g | **Axle dowel** for left drive-arm pivot (A_L). Same geometry as `pin_A_R`. Added because `drive_arm_L` no longer carries an integral horizontal shaft — it now rides on this snap-pin axle like the other arms. |
| `pin_B_R` | 1 | **PA12-GF** | PETG-HF | ~1–2 g | **Axle dowel** for right follower pivot. Same geometry as `pin_A_R`. |
| `pin_B_L` | 1 | **PA12-GF** | PETG-HF | ~1–2 g | **Axle dowel** for left follower pivot. Same geometry as `pin_A_R`. |
| `pin_C_R` | 1 | **PETG-HF** ★ | PETG-HF | ~1–2 g | **Finger snap pin** for right crank-coupler joint (C_R). Barbed split tip; head above finger; lip locks in rigid PA12-GF counterbore pocket in the crank-arm C-eye. |
| `pin_D_R` | 1 | **PETG-HF** ★ | PETG-HF | ~1–2 g | **Finger snap pin** for right follower-coupler joint (D_R). Barbed; lip locks in PA12-GF follower D-eye counterbore pocket. |
| `pin_C_L` | 1 | **PETG-HF** ★ | PETG-HF | ~1–2 g | **Finger snap pin** for left crank-coupler joint (C_L). |
| `pin_D_L` | 1 | **PETG-HF** ★ | PETG-HF | ~1–2 g | **Finger snap pin** for left follower-coupler joint (D_L). |

★ **Finger snap pins (pin_C_R/L, pin_D_R/L) — PETG-HF in the final build, not PA12-GF.**
The split snap barb reaches ~2.78 % insertion strain on worst-tight tolerance.
PA12-GF's allowable is ~1.5–2.0 % (brittle glass-filled grade, no yield plateau) — it
would crack on insertion. PETG-HF's allowable is ~2.5–3.5 % — 2.78 % is inside the
band. Pull-out load is carried entirely by the **rigid PA12-GF counterbore shoulder** in
the receiving arm/follower eye, not by the pin material — so a tougher PETG-HF pin is
structurally equivalent for retention. (Verified in `MATERIALS.md` §3 / Fix 2A.)

\* Rough single-piece estimates at recommended walls/infill (`PRINTING.md`).
**Total filament: roughly ~120–175 g PA12-GF + ~50–70 g ether-TPU + ~4–8 g PETG-HF
(finger pins).** The 8 snap pins and `input_pinion_shaft` together add roughly 10–15 g.

---

### 1.1 Pin families: what makes each type work

There are **two distinct pin mechanisms** in this gripper. They are not
interchangeable.

**Axle dowels — `pin_A_R`, `pin_A_L`, `pin_B_R`, `pin_B_L` (4 pins, plain, no barb)**

Retention by rigid geometric sandwich. The flat shank shoulder (r 2.3 mm) is
wider than the back-wall flood hole (r 1.5 mm) — it **bottoms on the annular
step** and cannot pass through (−Z stop). The head flange (r 3.9 mm) is wider
than the cover-boss bore (r 2.6 mm) — once the cover is on, the head face
seats against the cover-boss face and **cannot lift past it** (+Z stop). The
dowel is trapped between two rigid shoulders with ~0 axial slop. No barb; no
click. **Must be installed before the cover is snapped on.**

**Finger snap pins — `pin_C_R`, `pin_D_R`, `pin_C_L`, `pin_D_L` (4 pins, barbed)**

Retention by **rigid counterbore capture**. A confining pocket (SNAP_CB_R
3.65 mm, depth 1.3 mm) is cut into the exit face of each receiving eye. The
locking lip (r 3.2 mm) passes the bore (r 2.6 mm) and drops into the pocket.
The **rigid annular shoulder** (1.05 mm wide, at the pocket/bore step) takes
axial pull-out load in rigid material. The pocket wall radially confines the
lip — creep drives the lip outward toward the wall (harder to escape), not
inward (easier). This is geometric capture, not elastic preload. A positive
**click** confirms the lip has seated. Inserted from above the finger, barb
exits below the link eye.

---

### 1.2 Material rationale (final build picks)

- **Structural / rigid parts → PA12-GF (Nylon 12 glass-filled), FINAL.**
  PA12 is the lowest-uptake engineering nylon (~0.7–1.2 % saturated; glass fill
  reduces it further). It does not hydrolyze and holds tight dimensions under
  sustained immersion. Glass fill gives ~3.5–5.5 GPa modulus and low creep —
  ideal for gearbox bodies, arms, link bars, and axle dowels. **PETG-HF** is
  used for test prints: same geometry fidelity, faster to iterate. **Never PLA**
  (hydrolyzes); no ester-based materials; no raw PA6/PA66 (high swell).

- **Axle dowels (pin_A_R, pin_A_L, pin_B_R, pin_B_L) → PA12-GF.** Plain rigid
  sandwich dowels — nothing flexes. PA12-GF's low creep is a bonus for sustained
  axial retention; stiffness irrelevant to the barb-free geometry.

- **Finger snap pins (pin_C_R/L, pin_D_R/L) → PETG-HF even in the final build.**
  The split barb reaches ~2.78 % insertion strain, which exceeds PA12-GF's
  ~1.5–2.0 % brittle allowable (would crack on insert). PETG-HF's 2.5–3.5 %
  allowable passes with margin. Pull-out retention is taken by the rigid PA12-GF
  counterbore shoulder in the arm/follower — the pin material carries no pull-out
  load. **Never TPU for any pin** (creeps under sustained load, wallows bores,
  loses snap retention).

- **Fingers → ether-based TPU ~95A.** The Fin Ray grip principle is material
  compliance — the fingers must flex to wrap around an object. **Ether-based**
  TPU is hydrolysis-stable in sustained/warm immersion. **Ester-based TPU
  hydrolyzes** and crumbles underwater — exclude it entirely. 95A shore
  balances conformance with grip force; softer (85A) for delicate objects,
  stiffer (98A) for more grip force.

---

## 2. Zero bought hardware inside the gripper — what this revision eliminated

**This is a fully 3D-printed, zero-hardware gripper interior.** No screws, no
nuts, no bolts, no washers, no bushings inside the gripper body. Assembly is
tool-free: drop in the printed axle dowels, install the input-pinion-shaft,
snap on the cover, push in the barbed finger pins. Disassembly reverses in kind
— flex the cover clips and lift out the pins.

| Obsolete metal item (previous version) | Count | Replaced by |
|---|---|---|
| Pivot screws / metal dowels (2 drive axles + 2 follower axles + 4 finger pins) | 8 × A4/316 SS | **8 printed pins** — 4 axle dowels (`pin_A_R/A_L/B_R/B_L`) + 4 finger snap pins (`pin_C_R/D_R/C_L/D_L`) |
| Nylon-insert locknuts (one per pivot) | 8 × SS | **Eliminated** — axle dowels trapped by cover geometry; finger pins by counterbore lock |
| M3 front-cover screws | 4 × A4/316 SS | **4 integral printed cantilever snap clips** on `front_cover` |
| Input-shaft plain bushing (PTFE/acetal) | 1 | **Eliminated** — vertical input shaft runs in two flooded printed journal bores (no metal bushing); collar trapped geometrically in housing pocket |
| **Total bought hardware** | **19 pieces** | **0 pieces** |

---

## 3. The input shaft runs in flooded printed journal bores (no bushing)

The input shaft is a **separate printed part (`input_pinion_shaft`)** that
exits through the housing **bottom wall**. In this flooded design it turns in
**two plain printed journal bores** in the housing — no metal bushing. The bore
radius (`SHAFT_R_BORE = 4.3 mm`) clears the Ø8 mm shaft (`SHAFT_R = 4.0 mm`)
with a running fit.

- **Upper journal** (alignment, near the pinion): 2.0 mm long, in a boss
  standing up from the inside of the bottom wall.
- **Lower journal** (load-bearing exit): 7.0 mm long, through the bottom wall
  and mounting flange.
- **Collar axial capture**: an integral collar (OD 5.8 mm, length 2.0 mm) on
  the shaft sits in a pocket between the two bore-mouth shoulders — wider than
  the bore, trapped with ~0.25 mm axial play each side. This is **rigid
  geometric capture** (same principle as the captured axle dowels), not elastic
  preload — no creep risk.

Flooded journal bores work for the same reason as the pivot bores: no pressure
differential, no dry cavity — the joint runs wet, water is coolant and
lubricant. A sealed bearing traps grit; an Oilite bushing leaches oil when
flooded. Printed bores flush clean with a fresh-water rinse.

---

## 4. User-supplied items (outside the gripper BOM)

| Item | Qty | Notes |
|---|---|---|
| Waterproof servo / actuator | 1 | Couples to the **bottom D-profile coupler** on `input_pinion_shaft` (exits the housing bottom). Coupler: radius 5.0 mm, D-flat depth 1.4 mm, length 12 mm. Use an IP68/submersible servo, a potted hobby servo, or a sealed/oil-filled actuator with a pressure compensator for depth. The actuator is the only real waterproofing burden in the system. Servo coupling/horn is user-supplied or printed separately. See `UNDERWATER.md` §6. |
| M4 bolts (robot-arm mount) | 4 | Attach the **bottom flange** to your robot arm or mount. The flange carries 4 × M4 clearance holes positioned around (but clear of) the shaft exit. These are **arm hardware, not gripper hardware** — choose grade and length to suit your arm. If the arm is metal, add nylon or PTFE shoulder bushings + isolating washers at each bolt (see `UNDERWATER.md` §5). The gripper itself contributes no metal to this joint. |

---

## 5. Printed-part count summary

| Group | Qty | Material (FINAL) |
|---|---|---|
| `enclosure` | 1 | PA12-GF |
| `front_cover` (4 integral clips + 3 vent holes) | 1 | PA12-GF |
| `drive_arm_R` | 1 | PA12-GF |
| `drive_arm_L` (integral crown gear; rides on `pin_A_L`) | 1 | PA12-GF |
| `input_pinion_shaft` (pinion + shaft + collar + D-coupler) | 1 | PA12-GF |
| `follower_R` | 1 | PA12-GF |
| `follower_L` | 1 | PA12-GF |
| `finger_R` | 1 | Ether-based TPU ~95A |
| `finger_L` | 1 | Ether-based TPU ~95A |
| `pin_A_R` (axle dowel) | 1 | PA12-GF |
| `pin_A_L` (axle dowel — new) | 1 | PA12-GF |
| `pin_B_R` (axle dowel) | 1 | PA12-GF |
| `pin_B_L` (axle dowel) | 1 | PA12-GF |
| `pin_C_R` (finger snap pin ★) | 1 | **PETG-HF** |
| `pin_D_R` (finger snap pin ★) | 1 | **PETG-HF** |
| `pin_C_L` (finger snap pin ★) | 1 | **PETG-HF** |
| `pin_D_L` (finger snap pin ★) | 1 | **PETG-HF** |
| **Total printed parts** | **17** | — |
| Bought hardware inside gripper (screws/nuts/bolts/bushings) | **0** | — |
| User-supplied (outside gripper) | Waterproof actuator + D-shaft coupling; M4 flange bolts + nylon/PTFE galvanic-isolating washers | — |

★ Finger snap pins in PETG-HF (final build) — see §1.2 rationale.

---

## 6. Why fully-printed is corrosion-proof underwater

A gripper made **entirely of polymer** has **no galvanic cell anywhere** —
and galvanic corrosion is the primary failure mode of mixed-metal hardware in
seawater. The previous version maintained all metal in one stainless family
(316/A4) to avoid an internal galvanic pair; this revision deletes the problem
at the root by deleting the metal.

With no screws, nuts, bolts, pins, or bushings inside the gripper:

- **No dissimilar-metal contact, no anode, no pitting, nothing to rust.**
- Structural parts in PA12-GF: low water uptake (~0.7–1.2 % saturated, further
  reduced by glass fill), no hydrolysis, holds dimension over months of immersion.
- Axle dowels and input_pinion_shaft in PA12-GF: rigid sandwich / collar-capture
  geometry, low creep — retention stays positive with zero elastic degradation.
- Finger snap pins in PETG-HF: tough enough to flex the split barb on insertion
  without cracking; pull-out load taken by the PA12-GF counterbore shoulder.
- Fingers in ether-based TPU: does not hydrolyze in sustained immersion.
- Housing flooded: internal and external pressure equalize through drain holes
  and vent holes — the thin printed wall sees no differential, nothing to crush.
- Input shaft runs in flooded journal bores: flushes clean, no sealed race to
  trap grit, no Oilite to leach oil, no seal to fail.

**Net: nothing to rust, nothing to seal, nothing to crush, and nothing to buy
inside the gripper — rinse with fresh water after each salt dive.**

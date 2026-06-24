# Bill of Materials — Underwater geared four-bar / Fin Ray gripper (FULLY 3D-PRINTED)

Production BOM for the gripper defined in `gripper.py` (geared four-bar, single
input shaft, compliant TPU Fin Ray fingers, **flooded** housing for underwater
use). This is the *what-to-print* list — and for this revision that is the
**entire** list. See `PRINTING.md` for how to orient and slice each part,
`UNDERWATER.md` for material chemistry in seawater, and `ASSEMBLY.md` for the
tool-free snap-together sequence.

> # ZERO bought hardware inside the gripper. No screws, no nuts, no bolts, no bushings.
> **Every gripper part is 3D-printed and snaps, slides, or heat-stakes together by hand —
> tool-free except for a soldering iron at the pin caps.** All 8 pivot pins are plain
> printed journal pins, each retained by a separate printed cap melted over the pin's
> protruding stud with a soldering iron (a thermal rivet head wider than the bore). The
> 4 axle pins rivet to the back wall through the existing flood holes; the 4 finger pins
> (two SKUs, C and D, at different Z depths) cap on the arm/follower-eye underside as a
> bench sub-assembly. The front cover
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
`gen_step()` output: 25 children, labels as listed). The enclosure floods through
its drain holes; the mechanism drops in; each axle pin drops through its bore and
rivets to the back wall through the existing flood hole; each finger pin is melt-capped
on the arm/follower-eye underside as a bench sub-assembly; the cover snaps on. Done.

**Material legend:** FINAL = production print material. TEST = test-print material.
The 8 pivot pins and their 8 melt caps are PETG-HF (so they melt cleanly under a
soldering iron) — the sole exception to the otherwise all-PA12-GF rigid build; see
note below the table.

| Part | Qty | **FINAL material** | Test-print | Rough filament | Role / key detail |
|---|---|---|---|---|---|
| `enclosure` | 1 | **PA12-GF (Nylon 12 glass-filled)** | PETG-HF | ~80–110 g | Flooded gearbox body. Open front, flush, full-width integrated base with chamfered bottom perimeter (4 × M4 clearance holes), top link slots, 4 back-wall axle bosses + stepped bores (wide running bore + narrow flood hole), upper + lower journal bores + collar pocket for the vertical input shaft in the bottom wall, bottom drains (4 positions × 2 Z = 8 holes) + 2 side drains, 4 snap-clip catch windows in the long side walls. Never PLA. |
| `front_cover` | 1 | **PA12-GF** | PETG-HF | ~20–30 g | Closes the open front; 4 inner-face bosses locate the axle-pin heads (the heads seat just under these bosses — but the pins are riveted to the back wall by their melt caps, so the cover is no longer their retainer); **4 integral cantilever snap clips** (2 per long side, `SNAP_Z0=1.5` — lengthened arm, now slimmed to 2.0 mm thick so each tab stands just 2.4 mm proud of the side wall with a chamfered free-tip blade; 1.36 % worst-tight strain, within PA12-GF allowable) latch into body side-wall windows; **3 × Ø1.8 mm vent holes** at (±34, +12). Push on to click (click is a touch softer with the thinner arm); flex 4 hooks outward to release. |
| `drive_arm_R` | 1 | **PA12-GF** | PETG-HF | ~12–18 g | Right gear sector + crank arm. Clearance-bored at A_R (rides on axle pin `pin_A_R`). C-eye (−Z exit face) journals the slim land of finger pin `pin_C_R`; the pin's melt-stud exits below and is melt-capped. Flat plate; prints face-down. |
| `drive_arm_L` | 1 | **PA12-GF** | PETG-HF | ~12–18 g | Left gear sector + crank arm + **integral CROWN gear** on its +Z face (driven by the input pinion via the right-angle stage). Clearance-bored at A_L (rides on axle pin `pin_A_L`). C-eye journals `pin_C_L`. Flat plate; prints face-down. |
| `input_pinion_shaft` | 1 | **PA12-GF** | PETG-HF | ~8–12 g | ONE printed part: spur input pinion + vertical shaft + integral capture collar + bottom D-profile coupler (r 5.0, D-flat depth 1.4, length 12 mm). Axis vertical (exits the housing bottom). Two journal bearings in the housing (upper 2 mm, lower 7 mm); collar (OD 5.8 mm) trapped in a housing pocket between the two bore-mouth shoulders for axial capture (zero hardware). Print shaft-axis vertical for a self-supporting cylinder. |
| `follower_R` | 1 | **PA12-GF** | PETG-HF | ~6–9 g | Right B→D link bar. D-eye (−Z exit face) journals the slim land of finger pin `pin_D_R`; the pin's melt-stud exits below and is melt-capped. Flat plate; prints face-down. |
| `follower_L` | 1 | **PA12-GF** | PETG-HF | ~6–9 g | Left B→D link bar. D-eye journals `pin_D_L`. Same geometry as `follower_R` (mirrored in gen_step). |
| `finger_R` | 1 | **Bambu TPU 95A HF** (TPU ~95A — print ether-stable only) | TPU | ~30 g (ρ 1.22) | Right Fin Ray compliant jaw. Grip ridges on contact face; internal slanted-rib truss; mount holes at C_R and D_R. Must flex — print in TPU only. Print profile: `PRINT_PROFILE_P1S_TPU.md`. |
| `finger_L` | 1 | **Bambu TPU 95A HF** (TPU ~95A) | TPU | ~30 g (ρ 1.22) | Left Fin Ray compliant jaw (chiral mirror of `finger_R`). |
| `pin_A_R` (`melt_pin_axle`) | 1 | **PETG-HF** ★ | PETG-HF | ~1–2 g | **Axle pin** (heat-stake) for right drive-arm pivot (A_R). Head seats just under the cover boss; shank journals the gear/arm and bottoms on the back-bore step; melt-stud threads the existing back-wall flood hole and protrudes past the exterior back face, where its cap is melted from outside — riveted to the back wall (a fixed pivot post). No barb, no cover sandwich. |
| `pin_A_L` (`melt_pin_axle`) | 1 | **PETG-HF** ★ | PETG-HF | ~1–2 g | **Axle pin** (heat-stake) for left drive-arm pivot (A_L). Same geometry as `pin_A_R`. Added because `drive_arm_L` no longer carries an integral horizontal shaft — it now rides on this axle pin like the other arms. |
| `pin_B_R` (`melt_pin_axle`) | 1 | **PETG-HF** ★ | PETG-HF | ~1–2 g | **Axle pin** (heat-stake) for right follower pivot. Same geometry as `pin_A_R`. |
| `pin_B_L` (`melt_pin_axle`) | 1 | **PETG-HF** ★ | PETG-HF | ~1–2 g | **Axle pin** (heat-stake) for left follower pivot. Same geometry as `pin_A_R`. |
| `pin_C_R` (`melt_pin_finger_C`) | 1 | **PETG-HF** ★ | PETG-HF | ~1–2 g | **Finger pin** (heat-stake), LONG crank-layer SKU, for right crank-coupler joint (C_R). Head seats on the finger top; fat neck is the anti-wobble running bearing in the 2.6 mm TPU finger bore; slim land journals the rigid PA12-GF crank-arm C-eye; melt-stud protrudes past the C-eye bottom, where a separate cap is melted (bench sub-assembly). |
| `pin_D_R` (`melt_pin_finger_D`) | 1 | **PETG-HF** ★ | PETG-HF | ~1–2 g | **Finger pin** (heat-stake), SHORT follower-layer SKU, for right follower-coupler joint (D_R). Same head/neck/land/melt-stud arrangement; melt-stud capped past the follower D-eye bottom. |
| `pin_C_L` (`melt_pin_finger_C`) | 1 | **PETG-HF** ★ | PETG-HF | ~1–2 g | **Finger pin** (heat-stake), LONG crank-layer SKU, for left crank-coupler joint (C_L). |
| `pin_D_L` (`melt_pin_finger_D`) | 1 | **PETG-HF** ★ | PETG-HF | ~1–2 g | **Finger pin** (heat-stake), SHORT follower-layer SKU, for left follower-coupler joint (D_L). |
| `melt_cap` | 8 | **PETG-HF** ★ | PETG-HF | <1 g ea | **Heat-stake cap** — one per pin (qty 8). Slip over the pin's protruding melt-stud and fuse with a soldering iron → a thermal-rivet head wider than the bore. Retention is geometric (formed head larger than the hole), not an elastic snap and not a press fit. Negligible mass each. |

★ **All 8 pivot pins + their 8 melt caps — PETG-HF in the final build, not PA12-GF.**
The pins and caps are heat-staked: a separate cap is melted over each pin's protruding
stud with a soldering iron to form a thermal rivet head. PETG-HF is used for all of them
because they must **melt cleanly under a soldering iron** — glass-filled PA12-GF does not
heat-stake well (the glass loading resists clean reflow). Nothing flexes (retention is the
formed head, geometric, not an elastic snap) and nothing relies on friction (not a press
fit, so nothing slides out). Pull-out load is carried by the formed melt-cap head against
the eye/wall face, not by an interference fit. (See `MATERIALS.md` §3 / Fix 2A.)

\* Rough single-piece estimates at recommended walls/infill (`PRINTING.md`).
**Total filament: roughly ~120–175 g PA12-GF + ~50–70 g ether-TPU + ~5–10 g PETG-HF
(8 pins + 8 caps).** The 8 pins, 8 caps, and `input_pinion_shaft` together add roughly
12–18 g; each melt cap is tiny (<1 g).

---

### 1.1 Pin families: what makes each type work

Every pivot is a **heat-stake (melt-rivet) pin**: a plain printed PETG-HF journal
pin retained by a separate printed PETG-HF cap (`melt_cap`) melted over the pin's
protruding stud with a soldering iron, forming a thermal rivet head wider than the
bore. Retention is **geometric** (a formed head larger than the hole) — *not* an
elastic snap (nothing flexes → nothing breaks) and *not* a press fit (nothing relies
on friction → nothing slides out). There are **two pin layouts**, distinguished by
where the cap is melted; they are not interchangeable.

**Axle pins — `pin_A_R`, `pin_A_L`, `pin_B_R`, `pin_B_L` (4 pins, `melt_pin_axle`)**

The head seats just under the cover boss. The shank (r 2.3 mm) journals the
gear/arm and **bottoms on the back-bore step** (the wide running bore narrows to
the flood hole). The melt-stud threads the **existing back-wall flood hole** and
protrudes past the **exterior back face**, where its cap is melted **from outside** —
riveting the pin to the back wall as a **fixed pivot post**. The cover is no longer
the retainer and no longer sandwiches these pins; they stand on their own once
capped. Cap the axle pins (from outside the back wall) as part of dropping the
mechanism in; the cover snaps on afterward over a finished, retained axle set.

**Finger pins — `pin_C_R`/`pin_C_L` (`melt_pin_finger_C`, LONG/crank layer),
`pin_D_R`/`pin_D_L` (`melt_pin_finger_D`, SHORT/follower layer) — 4 pins, 2 SKUs**

C and D sit at **different Z depths** (crank layer vs follower layer), so they are
**two SKUs**, not one — the old single finger pin was wrong (half didn't seat). On
each: the head seats on the **finger top**; a **fat neck** is the anti-wobble running
bearing in the fixed 2.6 mm TPU finger bore; a **slim land** journals the rigid
PA12-GF arm/follower eye; the **melt-stud** protrudes past the arm/follower-eye
**bottom**, where a separate cap is melted. The finger pins are melt-capped as a
**bench sub-assembly** (finger + pin + cap built up off the gripper, then dropped in).

---

### 1.2 Material rationale (final build picks)

- **Structural / rigid parts → PA12-GF (Nylon 12 glass-filled), FINAL.**
  PA12 is the lowest-uptake engineering nylon (~0.7–1.2 % saturated; glass fill
  reduces it further). It does not hydrolyze and holds tight dimensions under
  sustained immersion. Glass fill gives ~3.5–5.5 GPa modulus and low creep —
  ideal for gearbox bodies, arms, and link bars. **PETG-HF** is
  used for test prints: same geometry fidelity, faster to iterate. **Never PLA**
  (hydrolyzes); no ester-based materials; no raw PA6/PA66 (high swell).

- **All 8 pivot pins + 8 melt caps (`melt_pin_axle` ×4, `melt_pin_finger_C` ×2,
  `melt_pin_finger_D` ×2, `melt_cap` ×8) → PETG-HF.** These are heat-staked: a
  separate cap is melted over each pin's stud with a soldering iron to form the
  retaining rivet head. They must **melt cleanly under a soldering iron**, and
  glass-filled PA12-GF does **not** heat-stake well (the glass loading resists
  clean reflow). So all pins moved PA12-GF → PETG-HF along with the caps. Nothing
  flexes — retention is the formed head, geometric, not elastic — so the old
  barb-ductility/insertion-strain argument no longer applies. Pull-out load is the
  melt-cap head bearing against the eye/wall face. **Never TPU for any pin**
  (creeps under sustained load, wallows bores) and TPU will not form a clean
  rivet head.

- **Fingers → TPU ~95A; selected filament Bambu TPU 95A HF.** The Fin Ray
  grip principle is material compliance — the fingers must flex to wrap an object.
  **Ether-based** TPU is hydrolysis-stable in sustained/warm immersion. **Ester-based
  TPU hydrolyzes** and crumbles underwater — exclude it entirely. *Bambu's TDS lists
  the material as thermoplastic polyurethane, "insoluble in water", with low saturated
  water uptake (1.08 % at 25 °C/55 %RH) — but it does NOT state polyether vs polyester
  chemistry, so we cannot claim hydrolysis resistance from the datasheet. For sustained
  or mission-critical immersion, confirm a polyether grade with Bambu or soak-test
  first.* TDS (Bambu TDS V1.0, ISO 527 printed specimens): density 1.22 g/cm³ (ISO 1183),
  tensile strength 27.3 MPa in-plane (X-Y) / 22.3 MPa through-Z (ISO 527 printed,
  Bambu TDS), elongation >650 % (X-Y) / >480 % (Z). Melting temp 183 °C. "HF" =
  high-flow: ~3× the throughput of standard TPU 95A (max volumetric speed ~12 mm³/s,
  prints up to ~200 mm/s; external-spool only — Bambu rates 95A HF too soft for the AMS). Print profile + FEA validation:
  `PRINT_PROFILE_P1S_TPU.md`. 95A shore balances conformance with grip force; softer
  (85A) for delicate objects, stiffer (98A) for more grip force.

---

## 2. Zero bought hardware inside the gripper — what this revision eliminated

**This is a fully 3D-printed, zero-hardware gripper interior.** No screws, no
nuts, no bolts, no washers, no bushings inside the gripper body. Assembly is
tool-free apart from a soldering iron at the caps: drop in the printed axle pins
and rivet them to the back wall (melt a cap on each stud from outside), install
the input-pinion-shaft, build up the finger+pin+cap bench sub-assemblies, drop
them in, snap on the cover. Disassembly: flex the cover clips, snip or shave the
melt caps, and lift out the pins (the caps are sacrificial — reprint and re-stake).

| Obsolete metal item (previous version) | Count | Replaced by |
|---|---|---|
| Pivot screws / metal dowels (2 drive axles + 2 follower axles + 4 finger pins) | 8 × A4/316 SS | **8 printed heat-stake pins + 8 printed melt caps** — 4 axle pins (`pin_A_R/A_L/B_R/B_L` = `melt_pin_axle`) + 4 finger pins (`pin_C_R/C_L` = `melt_pin_finger_C`, `pin_D_R/D_L` = `melt_pin_finger_D`), each retained by a melted-on `melt_cap` |
| Nylon-insert locknuts (one per pivot) | 8 × SS | **Eliminated** — every pin is retained by its own melted-on cap (a thermal rivet head wider than the bore) |
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
  geometric capture** (a formed shoulder wider than the bore, same family of
  retention as the melt-capped pin heads), not elastic preload — no creep risk.

Flooded journal bores work for the same reason as the pivot bores: no pressure
differential, no dry cavity — the joint runs wet, water is coolant and
lubricant. A sealed bearing traps grit; an Oilite bushing leaches oil when
flooded. Printed bores flush clean with a fresh-water rinse.

---

## 4. User-supplied items (outside the gripper BOM)

| Item | Qty | Notes |
|---|---|---|
| Waterproof actuator (force-sensing) | 1 | Couples to the **bottom D-profile coupler** on `input_pinion_shaft` (radius 5.0 mm, D-flat 1.4 mm, length 12 mm) via a printed adapter horn. **Selected primary: a smart serial-bus servo — DYNAMIXEL XW540-T260-R** ([buy: ROBOTIS US store, USD 1,241.89 ≈ AUD 1,925](https://robotis.us/dynamixel-xw540-t260-r/), verified May 2026; `-R` = RS-485) — IP68 body, ~1.9 N·m, native `present_current` telemetry, chosen because the actuator doubles as the **grip-force sensor** (motor current → tip force; no fingertip electronics). **Value alternative — just as good for ≤ $500: DYNAMIXEL XM540-W270-R** ([buy: ROBOTIS US store, USD 494.39 ≈ AUD 766](https://robotis.us/dynamixel-xm540-w270-r/), verified May 2026) — same Dynamixel-X RS-485 bus + identical `present_current` telemetry, *more* torque (cont 2.12 / stall 10.6 N·m), drop-in; only lacks the IP68 body, which is moot at T2 (canister needed either way). **Deep-budget alternative: Feetech STS3250** ([buy: OpenELAB, €63.85 ≈ AUD 110, in stock](https://openelab.io/products/feetech-sts3250-c002-servo-12v), May 2026) — 50 kg·cm / 4.9 N·m stall @ 12V (sustained ~2.45 N·m after torque-protection, still well above the 1.2 N·m floor), TTL half-duplex serial with `load / position / voltage / temperature` feedback (load % is the torque proxy, calibrated like Dynamixel `present_current`); plastic case, no IP rating → canister required. **Rock-bottom: Feetech STS3215 (C018, 12 V)** ([buy: eckstein-shop.de, €26.45 ≈ AUD 44](https://eckstein-shop.de/feetech-st-3215-c018-servo-en), May 2026) — same SCS bus + load feedback, smaller motor at 30 kg·cm / 2.94 N·m stall and ~0.98 N·m continuous (below the 1.2 target, above the 0.6 floor — adequate for intermittent mid-face grip-and-hold, not sustained tip clamping). **Tier-3 (>30 m) fallback: a magnetic-coupling dry-pod drive** (no shaft penetration). T2 (≤30 m) still needs a thin pressure canister. The actuator's firmware **current limit must be set to the gear ceiling `T_safe`** (gear protection). Full selection + sourcing: `motor/SELECTION.md` / `motor/SURVEY.md`; sensing: `motor/SENSING.md`; see also `UNDERWATER.md` §6. |
| **Pressure canister assembly for the actuator** (T1–T3) | 1 | Houses the chosen actuator (XW540 / XM540 / STS3250 / STS3215) for any non-trivially-wet deployment — **T2 (≤ 30 m) needs a canister even for the IP68 XW540** (IP68 = 1 m freshwater only). Full architecture in `motor/ROV_INTEGRATION.md` §2c–§2d. **Itemised kit** (Blue Robotics 3" locking series + a standard 8 mm lip seal — the de-facto small-ROV recipe): <br><br>**Tube:** [3" cast-acrylic locking tube, 240 mm length, 150 m depth rating — Part `BR-102649-240`](https://bluerobotics.com/store/watertight-enclosures/locking-series/wte-locking-tube-r1-vp/) — **USD 25**. Fits the longest servo body (~117 mm XW540/XM540) + connector bend; ≥ 5× depth margin at T2. *Upgrade for sustained service:* same-series **aluminium tube** (1000 m rated, ~USD 100+) — acrylic is Blue-Robotics-rated for short-term immersion (< ~2 weeks). <br><br>**Wet-side end cap (shaft exit):** [Blue Robotics 3" aluminium end cap, "blank" SKU = no factory holes as shipped — Part `BR-100949-999`](https://bluerobotics.com/store/watertight-enclosures/locking-series/wte-end-cap-vp/) — **USD 34**, 1000 m rated. **Drilled in build to Ø14 H7 centre-bore** (light press-fit, no adhesive) for the lip seal per `motor/ROV_INTEGRATION.md` §2d Option A. <br><br>**Dry-side end cap (cable exit):** [Blue Robotics 3" aluminium end cap with 4 × M10 factory penetrator holes — Part `BR-100949-004`](https://bluerobotics.com/store/watertight-enclosures/locking-series/wte-end-cap-vp/) — **USD 34**, 1000 m rated. <br><br>**Cable penetrators (dry-side cap):** [Blue Robotics WetLink Penetrator](https://bluerobotics.com/store/cables-connectors/penetrators/wetlink-penetrator/) — **~USD 13 each, qty 2** (one for the bus + power, one spare/vent). <br><br>**Unused-hole plugs (dry-side cap):** [Blue Robotics WetLink Penetrator Blank M10](https://bluerobotics.com/store/cables-connectors/wlp-blank/) — **USD 5–8 each, qty 2** (plugs the remaining 2 M10 holes on `BR-100949-004`; 1000 m rated). <br><br>**Shaft seal (the actual shaft-exit waterproofing — Option A per §2d):** Single-lip NBR radial shaft seal, **8 × 14 × 4 mm, DIN 3760 Type A** (standard size, multiple manufacturers; SKF CR HMS5 is the premium reference). Buyable: [EAI Oil Seal 8×14×4 SC NBR with garter spring (Amazon)](https://www.amazon.com/8X14X4-Grease-EAI-Spring-8mmx14mmx4mm/dp/B07NKXB2VL) — **~USD 5**. *Upgrade for higher pressure / chemical / cold-water service:* SKF CR 8×14×6 HMSA7 V Viton dual-lip, ~USD 12–15. <br><br>**Adapter shaft (Ø 8 mm, precision-ground stainless, the part the lip seal runs on):** [goBILDA 2100 Series Stainless Steel Round Shaft, 8 mm × 50 mm](https://www.gobilda.com/2100-series-stainless-steel-round-shaft-8mm-diameter-50mm-length/) — **USD 2.79**. *In build:* the dry end clamps to the servo horn via a small printed adapter (per actuator's horn pattern — printed in PA12-GF or PETG-HF, no buy); the wet end carries a printed/machined D-socket matching the gripper's input D-coupler (Ø10 / D-flat 1.4 mm / 12 mm engagement). For best seal life, polish the lip-contact band of the goBILDA shaft to Ra ≤ 0.4 µm (5 min on a polishing wheel; goBILDA ships at Ra ~0.4–0.8 µm — usable as-is for first integration). <br><br>**Assembled total ≈ USD 130 (≈ AUD 200)** for the acrylic + standard-seal build at T2. <br><br>**For Tier 3 (>30 m), swap Option A → Option B per `motor/ROV_INTEGRATION.md` §2d Option B**: replaces the wet-side end cap + lip seal + adapter shaft with a **thin non-conductive end cap** (printed PETG/PA12-GF or machined PEEK) + **inner-rotor magnet** on the servo + **outer-rotor magnet + 608ZZ bearing** on the wet side. Same canister tube + dry-side cap + penetrators. Coupling: KTR MINEX-S SA 60/8 (~USD 600–800 quote) or DIY 80 mm N52 ring (~USD 15–50). |
| M4 bolts (robot-arm mount) | 4 | Attach the **bottom flange** to your robot arm or mount. The flange carries 4 × M4 clearance holes positioned around (but clear of) the shaft exit. These are **arm hardware, not gripper hardware** — choose grade and length to suit your arm. If the arm is metal, add nylon or PTFE shoulder bushings + isolating washers at each bolt (see `UNDERWATER.md` §5). The gripper itself contributes no metal to this joint. |
| **Mounting interface adapter** (optional, printed) | 1 | Choose an adapter that mates the gripper's 4×M4 bottom flange to your specific arm or chassis. **Printed PA12-GF, all parametric build123d** under `motor/cad/adapters/`. **Seven options** modelled (`motor/cad/output/adapter_*.step`): **P0 (ready now)** — `adapter_bravo7` (Reach Bravo 7 RB-1054, Ø71/6×M6+6×M5 CSK, ~50 g), `adapter_iso9409_50_4_M6` (UR/Franka/Doosan/Fanuc CRX cobot flange, Ø63/4×M6, **dry only**, ~40 g), `adapter_br2_bottom_newton` (BlueROV2 Newton-footprint 2×M5/100 mm/**16° tilt**, ~24 g). **P1 variants** — `adapter_iso9409_80_6_M8` (UR20-class cobots, Ø100/6×M8, **dry only**, ~80 g), `adapter_br2_roof_rack` (BR2 front-mount L-bracket, ~300 g), `adapter_br2_payload_skid` (BR2 payload skid, ~50 g). **P2 held-tool** — `adapter_iso13628_d_handle` (ISO 13628-8 / API 17H Class A D-handle for Schilling/Kraft/ECA/Hydro-Lek work-class arms — the arm's existing standard jaws clamp the handle, no bolt-on, ~107 g). Full comparison + open questions: [`motor/INTERFACES.md`](../motor/INTERFACES.md); per-interface dossiers: `motor/interfaces/*.md`. |
| **Power-supply chain** (per-interface) | 1 chain | The XW540 wants **12 V / ≤ 6 A peak**; no real-arm wrist can supply that directly, so a step-down regulator + fuses + connector chain is required between the upstream bus and the canister. **Full breakdown:** [`motor/POWER_SUPPLY.md`](../motor/POWER_SUPPLY.md) §8 (POW-1 to POW-11, each line cited to a vendor SKU). **Recommended primary chain:** Pololu D36V50F12 12 V/6.5 A buck (\#4095, USD 39.95) + 8 A ATO inline fuse + 10 A polyfuse backstop + SMBJ16A TVS (**mandatory** P2 gear-protection) + AWG 16 marine-grade twisted pair + BR WetLink penetrator + Robotis 4-pin X4P cable + Robotis U2D2 USB-RS485 master (USD 36.92). **Incremental cost by interface:** BR2 chassis ~USD 50–65 · cobot bench ~USD 95 · Reach Bravo ~USD 365–565 · Schilling/Kraft ~USD 245. **Critical safety:** **never connect the BR2 14.8 V Li-ion battery directly to the XW540** — full-charge is 16.8 V, exceeds the 14.8 V max servo rating; the buck is mandatory, not optional. |

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
| `pin_A_R` (axle pin, `melt_pin_axle` ★) | 1 | **PETG-HF** |
| `pin_A_L` (axle pin, `melt_pin_axle` — new ★) | 1 | **PETG-HF** |
| `pin_B_R` (axle pin, `melt_pin_axle` ★) | 1 | **PETG-HF** |
| `pin_B_L` (axle pin, `melt_pin_axle` ★) | 1 | **PETG-HF** |
| `pin_C_R` (finger pin, `melt_pin_finger_C` — LONG ★) | 1 | **PETG-HF** |
| `pin_D_R` (finger pin, `melt_pin_finger_D` — SHORT ★) | 1 | **PETG-HF** |
| `pin_C_L` (finger pin, `melt_pin_finger_C` — LONG ★) | 1 | **PETG-HF** |
| `pin_D_L` (finger pin, `melt_pin_finger_D` — SHORT ★) | 1 | **PETG-HF** |
| `melt_cap` (heat-stake cap, one per pin ★) | 8 | **PETG-HF** |
| **Total printed parts** | **25** (9 structural + 8 pins + 8 caps) | — |
| Bought hardware inside gripper (screws/nuts/bolts/bushings) | **0** | — |
| User-supplied (outside gripper) | Waterproof actuator + D-shaft coupling; M4 flange bolts + nylon/PTFE galvanic-isolating washers | — |

★ All 8 pins + 8 melt caps in PETG-HF (final build) so they heat-stake cleanly — see §1.2 rationale.

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
- `input_pinion_shaft` in PA12-GF: rigid collar-capture geometry, low creep —
  retention stays positive with zero elastic degradation.
- All 8 pivot pins + 8 melt caps in PETG-HF: low uptake (~0.1–0.3 %), retained by
  a melted-on rivet head (geometric, nothing flexes). PETG-HF chosen because it
  heat-stakes cleanly; glass-filled PA12-GF does not.
- Fingers in ether-based TPU: does not hydrolyze in sustained immersion.
- Housing flooded: internal and external pressure equalize through drain holes
  and vent holes — the thin printed wall sees no differential, nothing to crush.
- Input shaft runs in flooded journal bores: flushes clean, no sealed race to
  trap grit, no Oilite to leach oil, no seal to fail.

**Net: nothing to rust, nothing to seal, nothing to crush, and nothing to buy
inside the gripper — rinse with fresh water after each salt dive.**

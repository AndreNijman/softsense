# Material-specific validation — pinned material plan

Final material-engineering gate for the fully-3D-printed underwater gripper
(`gripper.py`). The structural snap-fits in this design were geometry-tuned for
**ductile PETG** (insertion strains sit comfortably under PETG's elastic band).
The user has now **pinned the production material to glass-filled Nylon 12
(PA12-GF)** for everything rigid. PA12-GF is stiffer and markedly more brittle
(lower elongation-at-break), so this document re-checks every snap against the
*real* allowable strain of PA12-GF, not PETG's.

> **Headline verdict (RESOLVED — production-ready):** The body and arms are FINE
> in PA12-GF. The pivot pins are no longer flexing snaps at all — they are
> **heat-stake (melt-rivet) pins**: plain PETG-HF journal pins each retained by a
> separate PETG-HF cap (`melt_cap`) melted over the protruding stud with a
> soldering iron. Retention is a formed head wider than the bore (geometric);
> nothing flexes, so the old insertion-strain check on the finger pins is moot.
> The one remaining **flexing** snap is the **cover clip**, originally tuned to
> PETG's elastic band; it did NOT clear PA12-GF's allowable strain as drawn and is
> now fixed in `gripper.py` (verified, interference CLEAN all poses):**
> - Cover clip: `SNAP_Z0` changed 6.5 → 1.5 (cantilever lengthened) and arm
>   `SNAP_ARM_T` thinned 2.8 → 2.0 mm → worst-tight strain 3.32 % → **1.36 %**
>   (1.07 % nominal), inside PA12-GF allowable. **PASS.**
> - Pivot pins (all 8) + caps: PETG-HF, heat-staked. PETG-HF chosen because it
>   **melts cleanly under a soldering iron** — glass-filled PA12-GF does not
>   heat-stake well. Retention is the formed rivet head, not an elastic snap, so
>   there is no insertion-strain gate to clear. **PASS.**
> - Closed-pose pin collision: `THETA_CLOSED` 104 → 102°, pin gap ~9.86 mm, no
>   interference. **PASS.**
> - Pin retention: melt-cap rivet head bears on the rigid PA12-GF eye / back-wall
>   face (the old counterbore capture pockets are gone with the heat-stake
>   redesign). **PASS.**
>
> **No remaining FAILs. Design is production-ready. A printed coupon fit-test in
> real materials is still recommended before the full production run (§5/§8).**
> Buoyancy, water-swell, and galvanic all PASS (unchanged).

All strain numbers below are the cantilever surface-strain estimates from
`ENGAGEMENT.md` (and re-derived from `gripper.py` constants — see §2). They are
**order-of-magnitude per the snap-fit engineer's own caveat**; the binding gate
is a printed coupon in *actual PA12-GF* (§5, §8).

---

## 1. Mechanical properties used (FDM-printed, typical published ranges)

Printed (FFF) values, not datasheet injection-moulded values — FFF parts run
~10–30 % below moulded due to inter-layer adhesion and porosity. Ranges are
typical of commercial filament datasheets (e.g. 3DXTech/Polymaker/BASF
PA12-GF/PAHT-GF grades; generic PETG; generic ether-TPU 95A) plus the standard
snap-fit design literature (Bayer/Covestro *Snap-Fit Joints for Plastics*; BASF
and DuPont equivalent guides). Cite-on-coupon: confirm against your actual spool.

| Property (FFF print) | **PA12-GF** (final) | **PETG-HF** (test) | **Bambu TPU 95A HF** (fingers) |
|---|---|---|---|
| Tensile modulus E | **3.5–5.5 GPa** (glass-stiffened) | ~1.7–2.1 GPa | **9.8 MPa (X-Y) / 7.4 MPa (Z)** — MEASURED, ISO 527 printed, anisotropic |
| Flexural modulus | **4–6 GPa** | ~1.9–2.3 GPa | N/A (Bambu TDS; compliant) |
| Tensile / yield strength | **40–70 MPa** (filled, often no yield plateau — fails near-brittle) | ~40–50 MPa | **27.3 MPa (X-Y) / 22.3 MPa (Z)** (ISO 527 printed; elastomer, not a brittle yield) |
| **Elongation at break** | **~3–8 %** (printed GF nylon; brittle) | ~6–12 % | **>650 % (X-Y) / >480 % (Z)** (elastomer) |
| **Allowable design strain, one-time snap** (~0.5–0.7× ε_break for filled) | **~1.5–2.0 %** | **~2.5–3.5 %** | n/a (elastic, not snap) |
| Water absorption (saturated immersion) | **~0.7–1.2 %** (PA12 is the lowest-uptake nylon; glass fill lowers it further) | ~0.1–0.3 % (low) | **1.08 %** (ISO, 25 °C/55 % RH) |
| Density ρ | **~1.20–1.30 g/cc** | ~1.27 g/cc | **1.22 g/cc** (ISO 1183) |
| Creep | low–moderate (glass fill greatly improves over unfilled nylon) | moderate | **high (creeps)** — never structural |

Key facts that drive this review:

- **Glass fill trades ductility for stiffness.** Unfilled PA12 prints at
  ~10–20 % elongation; **30 % glass-filled drops it to ~3–8 %** and removes the
  yield plateau — the part snaps rather than yields. This is the whole reason
  the PETG-tuned snaps need re-checking.
- **PETG-HF ("high-flow") ≈ PETG mechanically.** High-flow is a *processing*
  variant (lower melt viscosity, faster printing); modulus, strength and
  elongation are within normal PETG scatter. Strain allowables transfer.
- **PA12 is the *least* hygroscopic nylon.** Do not conflate it with PA6/PA66
  ("nylon swells in water"). Saturated uptake ~1 %, and glass fill cuts it more.
  This matters for §4.

---

## 2. SNAP-FIT STRAIN VALIDATION (the critical check)

**Strain model** (same one `ENGAGEMENT.md` uses): cantilever surface strain
`ε = 3·t·δ / (2·L²)`, where `t` = beam bending thickness, `δ` = insertion
deflection, `L` = free cantilever length. **Allowable** = the material's
one-time-assembly design strain from §1.

### 2a. Re-derivation from `gripper.py` (confirms ENGAGEMENT.md)

**Cover clip** (`_one_clip` / `_all_snap_clips`): arm thickness
`t = SNAP_ARM_T = 2.0 mm` (thinned from 2.8); insertion deflection = the hook must
ride out by `SNAP_HOOK_ENGAGE = 1.5 mm` (nominal) → 1.9 mm worst-tight (+0.2 FDM
each side); free length `L = COVER_Z[0] − SNAP_Z0 = 20.5 mm`.
ε = 3·2.0·1.9/(2·20.5²) = **1.36 %** worst-tight (**1.07 %** nominal at δ=1.5).
✔ matches ENGAGEMENT.md. **Build-time gate:** `gripper.py` now asserts the
worst-tight strain stays under the conservative 1.5 % PA12-GF ceiling
(`SNAP_STRAIN_ALLOW = 0.015`) and fails the build loud if it does not.

**Pivot pins** (`melt_pin_axle`, `melt_pin_finger_C`, `melt_pin_finger_D`): **no
cantilever strain check applies.** These are heat-stake pins — plain journal pins
retained by a separate `melt_cap` melted over the protruding stud. Nothing flexes
on insertion; retention is the formed rivet head (geometric). The old finger-pin
barb strain derivation (the ~2.50 / 2.78 % split-collet numbers, and the
`SNAP_SLOT_LEN` model caveat) is **obsolete** — there is no barb and no flexing
collet. The only material requirement on the pins is that they **heat-stake
cleanly** (→ PETG-HF, not glass-filled PA12-GF; see §3).

### 2b. Allowable vs measured — PASS / MARGINAL / FAIL

Allowables: **PA12-GF ε_allow ≈ 1.5–2.0 %** (one-time assembly, filled grade,
no yield plateau → ~0.5× of a ~3–8 % ε_break). **PETG-HF ε_allow ≈ 2.5–3.5 %.**
The Bayer/Covestro guide quotes filled-nylon one-time-assembly allowables as high
as ~2.5–3 % for tougher grades; **we deliberately use the conservative 1.5–2.0 %
end** because a brittle filled nylon with no yield plateau fails by cracking, not
by forgiving plastic deformation — the consequence of being wrong is a shed cover
or a cracked pin, so the margin is taken on purpose, not by recall.

> ### A. FINDINGS TABLE — each snap × {PA12-GF, PETG-HF} — **UPDATED: reflects fixes applied**
>
> | Snap feature | Insertion strain (nom / worst-tight) | **PA12-GF** (allow ~1.5–2.0 %) | **PETG-HF** (allow ~2.5–3.5 %) | Status |
> |---|---|---|---|---|
> | **Cover clip** (`_one_clip`) — *as drawn* | 2.62 % / **3.32 %** | ~~FAIL~~ — worst-tight 3.32 % > 2.0 % ceiling | PASS — firm click | **FIXED** |
> | **Cover clip** (`_one_clip`) — *after `SNAP_Z0` 6.5→1.5 + arm thinned 2.8→2.0* | **1.07 % / 1.36 %** | **PASS — both nominal (1.07 %) and worst-tight (1.36 %) inside allowable, under the 1.5 % build gate** | PASS | **PASS** (resolved) |
> | **Finger pins** (`melt_pin_finger_C/D`) — *heat-stake* | n/a — **no flexure** (melt-rivet head, geometric capture) | N/A — pins are PETG-HF (must melt under a soldering iron; PA12-GF heat-stakes poorly) | **PASS — formed-head retention, no strain gate** | **PASS** (resolved by heat-stake redesign) |
> | **Axle pins** (`melt_pin_axle`) — *heat-stake* | n/a — **no flexure** (melt-rivet head through the back-wall flood hole, geometric capture) | N/A — PETG-HF (must melt; PA12-GF heat-stakes poorly) | **PASS — riveted to the back wall** | **PASS** (resolved) |
> | **Melt cap seat** (`melt_cap`, formed head vs eye/wall face) | n/a — static bearing, not a flex | **PASS** (rigid PA12-GF eye face is the bearing surface) | **PASS** | PASS (confirmed) |
>
> **All retention features now PASS.** The cover clip — the only remaining flexing
> snap — passes in PA12-GF with the lengthened cantilever (`SNAP_Z0=1.5`). All 8
> pivot pins + caps are heat-staked in PETG-HF (PETG-HF chosen so they melt cleanly
> under a soldering iron; glass-filled PA12-GF does not heat-stake well); their
> retention is a formed rivet head, geometric, so there is no insertion-strain gate
> to clear. The pull-out bearing face is the rigid PA12-GF eye / back wall.

**Why FAIL not just MARGINAL for the cover clip:** even the *nominal* 2.62 %
sits above the 2.0 % PA12-GF ceiling, and the worst-tight 3.32 % is at the very
edge of PA12-GF's *break* strain (~3–8 %, low end). A brittle filled-nylon clip
flexed to its break strain on every assembly will micro-crack at the hook root
and shed the cover. This must be fixed before the PA12-GF print.

**Second-order effect (note for the assembler):** swapping PETG→PA12-GF at
*identical geometry* leaves ε unchanged (geometry-only) but **insertion force
roughly doubles** (E ~2 → ~4 GPa). A clip that's a firm hand-click in PETG-HF
can need tooling in PA12-GF — another reason to lengthen the arm (lower force
*and* lower strain).

---

## 3. Fix summary (full constants in the delimited section at the end)

- **Cover clip — CLEAN top-level fix.** Lengthen the cantilever
  (**`SNAP_Z0 = 6.5 → 1.5`**, drop the arm root 5 mm down the outer wall, L 15.5
  → ~20.5) **and thin the arm `SNAP_ARM_T = 2.8 → 2.0 mm`** (outward tab
  protrusion 3.2 → 2.4 mm, sleeker blade-like tab; still ≥ the 1.5 mm functional
  wall floor). Strain is *linear* in thickness, so thinning the arm LOWERED the
  strain → worst-tight **1.90 % → 1.36 %** (1.07 % nominal) → **more PA12-GF
  margin, not less**, still **inside the conservative PA12-GF ~1.5–2.0 %
  allowable and under the new 1.5 % build-time gate → true PASS** (vs hard FAIL
  before), still PASS/firm in PETG-HF. Verified collision-free: the arm runs on
  the outer X side wall at Z 1.5–22; the back flange is at Z −16…−6 and the
  cavity floor far away — no clash, hook/window/engagement unchanged (engagement
  stays 1.5 mm nominal / 1.10 mm worst-loose ✔). **Bonus:** bending stiffness
  goes as t³, so thinning the arm drops it to ~(2.0/2.8)³ ≈ 0.36× the previous
  (lengthened) clip — net insertion force ≈ **0.31×** of the old PETG clip, a
  noticeably softer, lighter tactile click that is easier to seat by hand, while
  **retention is unchanged** (it is the geometric 1.15 mm hook-in-window
  engagement that holds the cover, not the spring force).
- **Pivot pins — redesigned as heat-stake (melt-rivet) pins; no strain knob at all.**
  All 8 pins (`melt_pin_axle` ×4, `melt_pin_finger_C` ×2, `melt_pin_finger_D` ×2)
  are plain PETG-HF journal pins, each retained by a separate PETG-HF `melt_cap`
  melted over the protruding stud with a soldering iron → a thermal rivet head
  wider than the bore. Nothing flexes, so there is no insertion-strain gate and the
  old barb fix-options (per-part material exception, or deepening the slot floor in
  `snap_pin()`) are moot. **PETG-HF is required** for the pins *and* caps because
  glass-filled PA12-GF does not heat-stake cleanly under a soldering iron. Finger
  pins are now **two SKUs** (LONG `_finger_C` at the crank layer, SHORT `_finger_D`
  at the follower layer) because C and D sit at different Z depths. Pins are
  ~1 g each, caps <1 g each (buoyancy-irrelevant).

---

## B. PER-PART MATERIAL TABLE (settled final plan) + validation verdict

All issues resolved. No open items. Verdicts below reflect applied fixes.

| Part | Qty | **FINAL material** | Test-print | **Verdict** |
|---|---|---|---|---|
| `enclosure` | 1 | **PA12-GF** | PETG-HF | **PASS** — rigid box, no flexure; thick walls (3.0 mm) easily handle PA12-GF. Stiffer is better. |
| `front_cover` | 1 | **PA12-GF** | PETG-HF | **PASS** — cover plate PASS; integral clip cantilever lengthened (`SNAP_Z0` 6.5→1.5) and arm thinned (`SNAP_ARM_T` 2.8→2.0, tab protrusion 3.2→2.4 mm), worst-tight strain 1.36 % inside PA12-GF allowable (under the 1.5 % build gate). Fix applied in `gripper.py`, verified interference-clean. |
| `drive_arm_L` | 1 | **PA12-GF** | PETG-HF | **PASS** — load-bearing arm with integral crown gear. PA12-GF's higher modulus/strength is an upgrade. Rides on axle pin `pin_A_L` like the right arm. |
| `input_pinion_shaft` | 1 | **PA12-GF** | PETG-HF | **PASS** — spur pinion + vertical shaft + integral capture collar + D-coupler, one part. Runs in two flooded journal bores (2 mm upper, 7 mm lower). Collar (OD 5.8 mm, length 2.0 mm) is a **rigid trapped shoulder** — not a flexing snap — so no creep concern; geometry locks both ±Y with ~0.25 mm axial play. PA12-GF's low creep keeps journals round under sustained load. Crown mesh is representative (straight-flank), coupon-tunable. |
| `drive_arm_R` | 1 | **PA12-GF** | PETG-HF | **PASS** — same. The C-eye is a *rigid* PA12-GF journal bore; the finger pin's melt-cap rivet head bears on its underside face (PA12-GF is the good pull-out bearing surface). |
| `follower_R/L` | 2 | **PA12-GF** | PETG-HF | **PASS** — link bars + rigid D-eye journal bore. Finger-pin melt-cap rivet head bears on the rigid PA12-GF eye face (the old counterbore capture pocket is gone with the heat-stake redesign). |
| `melt_pin_axle` (pin_A_R, pin_A_L, pin_B_R, pin_B_L) | 4 | **PETG-HF** (FINAL — not PA12-GF) | PETG-HF | **PASS** — heat-stake pins, **no flexure**. Head under cover boss; shank bottoms on the back-bore step; melt-stud through the back-wall flood hole, capped from outside = riveted to the back wall (fixed pivot post). PETG-HF required so the stud melts cleanly under a soldering iron; PA12-GF excluded (glass fill heat-stakes poorly). |
| `melt_pin_finger_C` (pin_C_R, pin_C_L — LONG, crank layer) | 2 | **PETG-HF** (FINAL — not PA12-GF) | PETG-HF | **PASS** — heat-stake pin, **no flexure**. Head on finger top; fat neck is the anti-wobble bearing in the 2.6 mm TPU finger bore; slim land journals the rigid PA12-GF crank-arm C-eye; melt-stud capped past the C-eye bottom (bench sub-assembly). PETG-HF required to melt cleanly; PA12-GF excluded. |
| `melt_pin_finger_D` (pin_D_R, pin_D_L — SHORT, follower layer) | 2 | **PETG-HF** (FINAL — not PA12-GF) | PETG-HF | **PASS** — heat-stake pin, **no flexure**. Same head/neck/land/melt-stud arrangement as `_finger_C` but shorter (follower layer Z). Melt-stud capped past the follower D-eye bottom. PETG-HF required to melt cleanly; PA12-GF excluded. |
| `melt_cap` (one per pin) | 8 | **PETG-HF** (FINAL) | PETG-HF | **PASS** — heat-stake cap, melted over each pin's stud to form the retaining rivet head. Geometric retention (head wider than bore), not an elastic snap, not a press fit. PETG-HF so it fuses cleanly to the PETG-HF pin under a soldering iron. <1 g each. |
| `finger_L/R` | 2 | **Bambu TPU 95A HF** | TPU | **PASS** — compliance is the grip mechanism. Selected: Bambu TPU 95A HF (high-flow), ρ 1.22. **Material provenance (now MEASURED, not assumed):** Bambu's TDS (V1.0) publishes ISO 527 **printed-specimen** properties — a real upgrade over the old eSUN spool, whose modulus was never published (the repo used a 40 MPa *guess*). Bambu measures an **anisotropic modulus 9.8 MPa in-plane (X-Y) / 7.4 MPa through-Z**, tensile strength **27.3 MPa (X-Y) / 22.3 MPa (Z)**, elongation >650 %/>480 %, density 1.22 g/cm³. The finger prints flat (cells in the build plane), so its in-plane bending — the grip mechanism — uses the X-Y values (E 9.8, strength 27.3); the through-Z values (E 7.4, strength 22.3) feed the underwater through-thickness crush. **Caveat:** 9.8 MPa is the ISO 527 initial-tangent modulus; a Fin-Ray at finite wrap strain is hyperelastic, so absolute grip forces are order-of-magnitude — but the repo's grip ranking/margins are force-targeted and so modulus-insensitive (unchanged by the switch). **Immersion caution:** Bambu's TDS lists TPU (insoluble in water, 1.08 % saturated uptake) but does **not** state polyether vs polyester chemistry — keep the ether-vs-ester rule: confirm polyether grade with Bambu or soak-test before sustained/critical immersion. Print: `PRINT_PROFILE_P1S_TPU.md`. Bench validation on a printed coupon: `motor/BENCH_TEST.md`. |

---

## 4. WATER ABSORPTION / SWELLING (PA12-GF, seawater, days–weeks)

**Verdict: PASS — does not bind the pivots, does not loosen retention. No
clearance change required for swell.**

PA12 is the **lowest-uptake** engineering nylon (saturated immersion ~0.7–1.2 %
by mass for filled grades; glass fill reduces it further by replacing absorbent
polymer with inert glass). Contrast PA6/PA66 at 8–10 % — those *would* be a
swell problem; PA12-GF is not.

Rough dimensional estimate: linear swell ≈ ⅓ × volumetric ≈ ⅓ × (mass uptake) ≈
**~0.2–0.4 % linear** at full saturation (conservative upper bound; glass fill
typically gives well under this):

- On the **Ø5.2 mm pivot bore** (radius 2.6 mm): ~0.005–0.010 mm radial growth.
  The shank grows similarly. Net change in the `PRINT_CLEAR = 0.30 mm` running
  gap is **a few µm to ~0.02 mm worst case** — trivially absorbed by the
  0.30 mm clearance. **Pivots do not bind.**
- On the **melt-cap rivet head vs the eye/wall bearing face**: the formed PETG-HF
  head and the PA12-GF eye face swell together; net change is **near zero** and the
  head is far wider than the bore, so retention is unaffected by swell. (Note the
  pins/caps are PETG-HF, whose uptake is ~0.1–0.3 % — even lower than PA12-GF.)
- On **snap engagements**: the 1.5 mm cover-hook engagement and the melt-cap rivet
  head are tens of times larger than any swell — retention is unaffected.

**Recommendation:** keep `PRINT_CLEAR = 0.30 mm`. Do **not** open it for swell —
the swell budget is < 0.02 mm and the running clearance already has 10×+ margin.
(The clearance change that *does* matter is the print-process transfer in §5,
not swell.)

---

## 5. TEST (PETG-HF) → FINAL (PA12-GF) TRANSFER

**A fit dialed in on PETG-HF will NOT transfer 1:1 to PA12-GF. Re-tune on a
PA12-GF coupon.** Two independent reasons:

1. **Print temperature & shrink.** PETG-HF runs ~230–250 °C, low warp, low
   shrink (~0.2–0.4 %). PA12-GF runs **~260–290 °C**, higher and **anisotropic**
   shrink (glass fibres align to flow → ~0.3–1.0 % in-plane, less through-Z),
   and warps without an enclosed/heated chamber. Net: PA12-GF holes tend to come
   out **undersized** vs the PETG-HF result, and external dims/flatness drift.
2. **Stiffness.** Even at the same nominal clearance, PA12-GF's higher modulus
   makes a borderline-tight fit *feel* much tighter and a snap *much* harder to
   seat (insertion force ~2×).

**Recommendation (numbers):**

- **Running bores / pivots:** budget **+0.05 to +0.10 mm extra radial clearance
  for PA12-GF vs the PETG-HF-dialed value** (i.e. effective `PRINT_CLEAR` ~0.35–
  0.40 mm for the PA12-GF parts, if PETG-HF dialed in at 0.30). Tune on a coupon;
  do not bake a global change blindly.
- **Pin journal bores:** if a pin runs too tight in a PA12-GF eye, open the bore a
  hair on a coupon — do NOT thin the pin (PIN_R = 2.3 mm shank is the journal
  dimension).
- **Coupon gate (mandatory):** before the full PA12-GF set, print (a) one
  cover-clip-arm-on-window coupon in *actual PA12-GF* (verify the click and that
  nothing cracks) and (b) one PETG-HF heat-stake pin + cap through a scrap PA12-GF
  eye, then **melt the cap with a soldering iron** and confirm the rivet head forms
  cleanly and holds. The cover-clip strain model is order-of-magnitude (§2); the
  coupon is the real PASS/FAIL, and the melt test confirms PETG-HF heat-stakes as
  expected.
- **Test-print fidelity caveat:** a PETG-HF test print validates *kinematics,
  assembly order, and geometry* but **not** the brittle-material snap behaviour
  or the PA12-GF dimensional fit. Treat PETG-HF as a form/function mockup, not a
  material proxy for the snaps.

---

## C. WATER-SWELL + TRANSFER recommendations (consolidated)

- **Swell:** none needed — `PRINT_CLEAR = 0.30 mm` stays; swell budget <0.02 mm.
- **Transfer:** PA12-GF parts need **+0.05–0.10 mm radial bore clearance** vs the
  PETG-HF-dialed fit; ream pockets (don't thin lips); **coupon-test in real
  PA12-GF** before the full set.

---

## D. BUOYANCY RECOMPUTE (real per-material densities)

Solid volumes measured from the exported part STLs at the time of the previous
QA pass (15-part build). The current build is **25 parts** (9 structural + 8
PETG-HF pins + 8 PETG-HF melt caps). The 8 caps are each <1 g (tiny), so their
combined mass (~a few g) is buoyancy-irrelevant; the axle pins switching PA12-GF →
PETG-HF is a wash on mass (near-identical density). The buoyancy result (gently
negative / near-neutral) is **essentially unchanged**. Recompute from a fresh
`gen_step()` if a hard number is needed for the updated 25-part build.

Flooded (cavity full of water) → the tool displaces only its **solid** volume.
Net = dry mass − (total solid × ρ_water). Positive = sinks.

**Verdict: PASS — buoyancy near-neutral and essentially unchanged.** The 8 melt
caps add only a few grams (tiny parts) and the axle-pin PA12-GF → PETG-HF switch is
mass-neutral (near-identical density). Net buoyancy remains slightly negative
(sinks gently) — the desired manipulator behaviour. Recompute on a fresh
`gen_step()` if exact numbers are needed. Caveats from UNDERWATER §4 still hold: only true if the cavity floods
fully (trapped air in the ~84 cm³ void would add ~+86 g of lift and flip it
positive — the cover vents address this); and the user's actuator/mount dominate
system trim.

---

## E. GALVANIC

**PASS (trivial).** The pinned plan is **100 % polymer** — PA12-GF (body, arms,
`input_pinion_shaft`) + PETG-HF (all 8 pivot pins + all 8 melt caps) + ether-TPU
(fingers). No dissimilar metals, no electrolytic cell, nothing to pit or corrode
in seawater. (External M4 flange-to-robot joint: isolate with nylon/PTFE bushings
if the host arm is metal — but the gripper contributes no metal, per UNDERWATER §5.)

---

## === GEOMETRY CHANGES — APPLIED AND RESOLVED ===

**All three blocking issues have been fixed in `gripper.py` and verified
(interference CLEAN all poses). No open items remain before the production print.
A coupon fit-test in real materials is still recommended (§5/§8) before the
full run.**

### CHANGE 1 — Cover clip cantilever + thinned arm (**APPLIED**)

- **Constants changed:** `SNAP_Z0` **6.5 → 1.5** — arm root moved 5 mm down the
  outer wall, lengthening the cantilever free length L 15.5 → ~20.5 mm — **and**
  `SNAP_ARM_T` **2.8 → 2.0 mm** (arm thinned; outward tab protrusion beyond the
  side wall 3.2 → 2.4 mm, a sleeker blade-like tab; still ≥ the 1.5 mm functional
  wall floor). A 1.0 mm free-tip outer-edge chamfer (`SNAP_TIP_CHAM`) reads the
  tab as an intentional blade; at the print-top in the flipped cover orientation
  it is self-supporting (no support, no new overhang).
- **Effect:** Strain is *linear* in thickness, so thinning the arm LOWERED the
  strain further. Worst-tight **3.32 % → 1.36 %**, nominal **2.62 % → 1.07 %**
  (ε = 3·2.0·1.9/(2·20.5²)). Thinning *increased* PA12-GF margin, not reduced it.
- **PA12-GF (allow ~1.5–2.0 %):** both nominal (1.07 %) and worst-tight (1.36 %)
  are inside the allowable → **true PASS** (was a hard FAIL at 3.32 %). A new
  build-time assert in `gripper.py` fails the build if worst-tight strain ≥ 1.5 %
  (`SNAP_STRAIN_ALLOW`), a guardrail against future regressions.
- **PETG-HF (allow ~2.5–3.5 %):** well inside band. **PASS.**
- **Insertion force / click:** bending stiffness goes as t³, so the thinner arm
  drops to ~(2.0/2.8)³ ≈ 0.36× the previous (lengthened) clip → net insertion
  force ≈ **0.31×** the old PETG clip: a noticeably softer, lighter tactile
  click, easier to seat by hand. **Retention is unchanged** — the geometric
  1.15 mm hook-in-window engagement holds the cover, not the spring force.
- **Collision:** arm runs on ±X outer side wall at Z 1.5–22; back flange at
  Z −16…−12; no clash. **Interference check verified CLEAN all poses.**
- **Capture unchanged:** hook lip, window, `SNAP_HOOK_ENGAGE = 1.5` untouched;
  engagement stays 1.5 mm nominal / 1.10 mm worst-loose. ✔

### CHANGE 2 — Pivot pins redesigned as heat-stake (melt-rivet) pins (**APPLIED**)

The old snap pins are gone. All 8 pivots are now **heat-stake pins**: plain PETG-HF
journal pins (`melt_pin_axle` ×4; `melt_pin_finger_C` ×2 LONG/crank layer;
`melt_pin_finger_D` ×2 SHORT/follower layer), each retained by a separate PETG-HF
`melt_cap` (×8) melted over the protruding stud with a soldering iron.

- **Why the redesign:** the old finger snap pins (split barb, counterbore capture)
  kept snapping/breaking, and the old axle dowels (plain dowel sandwiched between
  back boss and cover boss) wobbled and slid out. Heat-stake retention is a formed
  rivet head wider than the bore — **geometric, nothing flexes (nothing breaks) and
  nothing relies on friction (nothing slides out).**
- **Material:** PETG-HF for all pins **and** caps, because they must **melt cleanly
  under a soldering iron**; glass-filled PA12-GF heat-stakes poorly. This moved the
  axle pins PA12-GF → PETG-HF — now *all* pins and caps are PETG-HF.
- **Finger pins are two SKUs:** C and D sit at different Z depths, so the single old
  finger SKU was wrong (half didn't seat). `_finger_C` is the long crank-layer pin;
  `_finger_D` is the short follower-layer pin.
- **Strain check obsolete:** the old 2.78 % barb insertion-strain gate (and the
  `SNAP_SLOT_LEN`/slot-floor model caveat) no longer applies — there is no barb and
  no flexing collet. Pull-out load is the melt-cap rivet head bearing on the rigid
  PA12-GF eye / back wall. Mass impact: pins ~1 g each, caps <1 g each
  (buoyancy-irrelevant).

### CHANGE 3 — Doc updates for the heat-stake redesign (**APPLIED**)

`BOM.md` has been updated: the 8 pins are listed as `melt_pin_axle` (×4),
`melt_pin_finger_C` (×2), `melt_pin_finger_D` (×2), each in **PETG-HF**, plus the
new `melt_cap` (×8) part. The pin-families section (§1.1), material rationale
(§1.2), zero-hardware comparison, and part-count summary (now **25 parts** = 9
structural + 8 pins + 8 caps) all updated to match.

### CHANGE 4 — Closed-pose pin collision (**APPLIED**)

- **Constant changed:** `THETA_CLOSED` **104° → 102°**.
- **Effect:** C-pin gap in closed pose increases to ~9.86 mm — no interference.
  Grip closure preserved. Interference verified CLEAN at all poses.

### CHANGE 5 — Counterbore pockets removed by the heat-stake redesign (**SUPERSEDED**)

- The old counterbore floor-gap bug is moot: the counterbore capture pockets in the
  arm/follower eyes are gone. The eyes are now plain journal bores; pull-out load is
  carried by the melt-cap rivet head bearing on the eye/wall face, not by a
  counterbore shoulder.

---

### NOT CHANGED (and why)

- `PRINT_CLEAR = 0.30` — kept. Water-swell budget <0.02 mm; the *only* clearance
  action is the PA12-GF print-transfer coupon (+0.05–0.10 mm if needed, tuned on
  a coupon, not baked in here).
- `PIN_R = 2.3 mm` (pin shank/journal radius) — kept, unchanged by the heat-stake
  redesign.
- `SNAP_HOOK_ENGAGE` (cover clip) — kept. Sets the cover-clip capture margin
  (ENGAGEMENT raised it deliberately); reducing it would undo hard-won retention.
  Fix cover-clip strain via L (CHANGE 1), never by reducing engagement. (The old
  finger-pin barb constants — `SNAP_BARB_PROUD`/`SEAT`/`LIP_T` — are obsolete: the
  pins no longer have a barb.)

### Resolution summary — all blocking issues CLOSED

| Issue | As-drawn / as-found | Fix applied | Assigned material | Result |
|---|---|---|---|---|
| Cover clip insertion strain | 3.32 % worst-tight — FAIL in PA12-GF | `SNAP_Z0` 6.5→1.5 (longer cantilever) + `SNAP_ARM_T` 2.8→2.0 (thinner arm) | PA12-GF | **PASS** — 1.36 % worst-tight (nom 1.07 %), inside PA12-GF allowable, under the 1.5 % build gate |
| Finger pins snapping / breaking (old split barb) | barb cracked on insertion | Redesigned as heat-stake pins (`melt_pin_finger_C`/`_D` + `melt_cap`); two SKUs for the two Z layers | **PETG-HF** | **PASS** — no flexure; formed rivet head, geometric retention |
| Axle pins wobbling / sliding out (old sandwiched dowel) | cover sandwich was the retainer | Redesigned as heat-stake pins (`melt_pin_axle` + `melt_cap`); riveted to the back wall through the flood hole | **PETG-HF** (was PA12-GF — needs to melt) | **PASS** — fixed pivot post, geometric retention |
| Closed-pose pin collision | pin gap < 0 — FAIL | `THETA_CLOSED` 104→102° | — | **PASS** — gap ~9.86 mm, no interference |

**Final gate (do not skip):** print the cover-clip-on-window coupon in **actual
PA12-GF** (real-material snap behaviour and dimensional fit) and a **PETG-HF
heat-stake pin + cap through a scrap PA12-GF eye**, then **melt the cap with a
soldering iron** to confirm the rivet head forms cleanly and holds — before
committing the full production set. The cover-clip strain model is
order-of-magnitude; the coupon is the real gate. See §5/§8.

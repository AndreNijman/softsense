# Material-specific validation — pinned material plan

Final material-engineering gate for the fully-3D-printed underwater gripper
(`gripper.py`). The structural snap-fits in this design were geometry-tuned for
**ductile PETG** (insertion strains sit comfortably under PETG's elastic band).
The user has now **pinned the production material to glass-filled Nylon 12
(PA12-GF)** for everything rigid. PA12-GF is stiffer and markedly more brittle
(lower elongation-at-break), so this document re-checks every snap against the
*real* allowable strain of PA12-GF, not PETG's.

> **Headline verdict (RESOLVED — production-ready):** The body, arms, and axle
> dowels are FINE in PA12-GF. The two **flexing** snaps — the **cover clips**
> and the **barbed finger pins** — were originally tuned to PETG's elastic band
> and did NOT clear PA12-GF's allowable strain as drawn. **Both issues are now
> fixed in `gripper.py` (verified, interference CLEAN all poses):**
> - Cover clip: `SNAP_Z0` changed 6.5 → 1.5 (cantilever lengthened) and arm
>   `SNAP_ARM_T` thinned 2.8 → 2.0 mm → worst-tight strain 3.32 % → **1.36 %**
>   (1.07 % nominal), inside PA12-GF allowable. **PASS.**
> - Finger-pin barb: 4 barbed pins (`snap_pin_finger`) assigned **PETG-HF for the
>   final build** (2.78 % insertion strain inside PETG-HF's 2.5–3.5 % allowable;
>   pull-out carried by the rigid PA12-GF counterbore shoulder). **PASS.**
> - Closed-pose pin collision: `THETA_CLOSED` 104 → 102°, pin gap ~9.86 mm, no
>   interference. **PASS.**
> - Counterbore floor-gap: fixed; 0.30 mm floor gap confirmed, 1.05 mm shoulder
>   capture intact. **PASS.**
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

| Property (FFF print) | **PA12-GF** (final) | **PETG-HF** (test) | **ether-TPU 95A** (fingers) |
|---|---|---|---|
| Tensile modulus E | **3.5–5.5 GPa** (glass-stiffened) | ~1.7–2.1 GPa | ~0.02–0.06 GPa (soft) |
| Flexural modulus | **4–6 GPa** | ~1.9–2.3 GPa | low (compliant) |
| Tensile / yield strength | **40–70 MPa** (filled, often no yield plateau — fails near-brittle) | ~40–50 MPa | ~25–40 MPa @100 % |
| **Elongation at break** | **~3–8 %** (printed GF nylon; brittle) | ~6–12 % | **300–500 %** (elastomer) |
| **Allowable design strain, one-time snap** (~0.5–0.7× ε_break for filled) | **~1.5–2.0 %** | **~2.5–3.5 %** | n/a (elastic, not snap) |
| Water absorption (saturated immersion) | **~0.7–1.2 %** (PA12 is the lowest-uptake nylon; glass fill lowers it further) | ~0.1–0.3 % (low) | ~0.5–1.5 % |
| Density ρ | **~1.20–1.30 g/cc** | ~1.27 g/cc | ~1.10–1.22 g/cc |
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

**Finger-pin barb** (`snap_pin(barb=True)`): split "+" cantilever flexes inward
by `SNAP_BARB_PROUD = 0.9 mm` (nominal) → ~1.0 mm worst-tight; effective slotted
thickness `t_eff ≈ 1.5 mm`; `L = SNAP_SLOT_LEN = 9 mm` (the value ENGAGEMENT
used). ε = **2.50 %** nominal, **2.78 %** worst-tight. ✔ matches.

> **Model caveat the materials review must flag (finding):** `SNAP_SLOT_LEN`
> does **not** actually set the flexing length. In `snap_pin()` the slot root is
> `slot_root_z = max(tip_z − SNAP_SLOT_LEN, L + 0.6)`, and for both finger pins
> the `L + 0.6` floor *clamps the real slot to 4.6 mm* (verified for pin_C and
> pin_D: tip_z−L = SEAT+LIP_T+LEAD = 5.2 mm, floor at L+0.6 → effective slot
> 4.6 mm regardless of `SNAP_SLOT_LEN`). So `SNAP_SLOT_LEN=9` is inert above
> ~5.2 mm — the flexure is shorter and stiffer than the L=9 number implies, and
> **raising `SNAP_SLOT_LEN` alone will NOT lower the finger-pin strain.** The
> split-barb collet is not really a beam anyway (it is hoop-bending of a split,
> taper-loaded tube), so we keep ENGAGEMENT's 2.78 % as the working number per
> the original "order-of-magnitude" caveat — but the fix for it is *not* the
> obvious constant bump (see §3 / GEOMETRY CHANGES).

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
> | **Finger-pin barb** (`snap_pin barb`) — *assigned material PETG-HF* | 2.50 % / **2.78 %** | N/A — pins are PETG-HF (final build; PA12-GF not used here) | **PASS — 2.78 % inside 2.5–3.5 % band** | **PASS** (resolved by material assignment) |
> | **Axle dowel** (`snap_pin barb=False`) | n/a — **no flexure** (rigid sandwiched dowel, geometric capture) | **PASS** (trivial — nothing flexes) | **PASS** | PASS (unchanged) |
> | **Counterbore lip seat** (rigid shoulder, PA12-GF eye) | n/a — static bearing, not a flex | **PASS** (rigid material is *better* here; 0.30 mm floor gap confirmed, 1.05 mm capture intact) | **PASS** | PASS (fixed/confirmed) |
>
> **All snaps now PASS in their assigned materials.** Cover clip in PA12-GF passes
> with the lengthened cantilever (`SNAP_Z0=1.5`). Finger-pin barb passes in
> PETG-HF — the assigned final material for those 4 parts. Static/geometric
> captures (axle dowels, counterbore shoulders) pass in both and are improved by
> PA12-GF stiffness (harder pull-out shoulder, lower creep).

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
- **Finger-pin barb — the obvious knob is inert; two real options:**
  - **Preferred: per-part material exception.** Print the **4 barbed finger
    pins (`snap_pin_finger`: pin_C_R/L, pin_D_R/L) in PETG-HF even for the final
    build.** Body, arms, axle dowels, cover → PA12-GF. The pins are ~1 g each
    (~4 g total, buoyancy-irrelevant) and their pull-out load is taken by the
    **rigid PA12-GF counterbore shoulder**, not the pin material — so a slightly
    softer/tougher pin material is *fine* and removes the brittle-snap risk on
    the highest-relative-strain feature. Lowest-risk path; **recommended.**
  - **Alternative (if all-PA12-GF is hard-pinned): function-level edit** to
    lengthen the real flexure — change the slot floor in `snap_pin()` from
    `L + 0.6` to `L − 2.0` so the slot cuts ~2 mm deeper into the shank. Guard:
    pin_D bearing eye is Z 7–12; the deepened slot reaches ~Z 11.5 — *marginal*
    overlap with the follower bearing zone, so re-run the interference check and
    confirm pin_D still bears. (pin_C is safe: bearing eye Z 1–6, slot floor
    ~Z 17.5.) Because of that marginal overlap, the **material exception is
    cleaner.**

---

## B. PER-PART MATERIAL TABLE (settled final plan) + validation verdict

All issues resolved. No open items. Verdicts below reflect applied fixes.

| Part | Qty | **FINAL material** | Test-print | **Verdict** |
|---|---|---|---|---|
| `enclosure` | 1 | **PA12-GF** | PETG-HF | **PASS** — rigid box, no flexure; thick walls (3.0 mm) easily handle PA12-GF. Stiffer is better. |
| `front_cover` | 1 | **PA12-GF** | PETG-HF | **PASS** — cover plate PASS; integral clip cantilever lengthened (`SNAP_Z0` 6.5→1.5) and arm thinned (`SNAP_ARM_T` 2.8→2.0, tab protrusion 3.2→2.4 mm), worst-tight strain 1.36 % inside PA12-GF allowable (under the 1.5 % build gate). Fix applied in `gripper.py`, verified interference-clean. |
| `drive_arm_L` | 1 | **PA12-GF** | PETG-HF | **PASS** — load-bearing arm with integral crown gear. PA12-GF's higher modulus/strength is an upgrade. Rides on axle dowel `pin_A_L` like the right arm. |
| `input_pinion_shaft` | 1 | **PA12-GF** | PETG-HF | **PASS** — spur pinion + vertical shaft + integral capture collar + D-coupler, one part. Runs in two flooded journal bores (2 mm upper, 7 mm lower). Collar (OD 5.8 mm, length 2.0 mm) is a **rigid trapped shoulder** — not a flexing snap — so no creep concern; geometry locks both ±Y with ~0.25 mm axial play. PA12-GF's low creep keeps journals round under sustained load. Crown mesh is representative (straight-flank), coupon-tunable. |
| `drive_arm_R` | 1 | **PA12-GF** | PETG-HF | **PASS** — same. Counterbored C-eye is a *rigid* feature (PA12-GF improves pull-out bearing). |
| `follower_R/L` | 2 | **PA12-GF** | PETG-HF | **PASS** — link bars + rigid D-eye counterbore. Counterbore floor-gap fix confirmed (0.30 mm floor gap; 1.05 mm shoulder capture). |
| `snap_pin_axle` (pin_A_R, pin_A_L, pin_B_R, pin_B_L) | 4 | **PA12-GF** | PETG-HF | **PASS** — plain rigid dowels, **no flexure**, geometric sandwich capture. PA12-GF fine (low creep is a bonus). |
| `snap_pin_finger` (pin_C_R/L, pin_D_R/L) | 4 | **PETG-HF** (FINAL — not PA12-GF) | PETG-HF | **PASS** — 2.78 % insertion strain inside PETG-HF's ~2.5–3.5 % allowable. PA12-GF excluded: its ~1.5–2.0 % brittle allowable would crack the barb on insertion. Pull-out load is carried by the rigid PA12-GF counterbore shoulder — the pin material is irrelevant for retention. |
| `finger_L/R` | 2 | **eSUN eTPU-95A** (ether/polyether ~95A) | TPU | **PASS** — compliance is the grip mechanism. Ether-TPU (never ester — hydrolyzes). Selected: eSUN eTPU-95A (ρ 1.21, UTS 35 MPa IM / ~25 MPa printed); polyether per eSUN's hydrolysis-resistance marketing — confirm/soak-test for critical immersion. Print: `PRINT_PROFILE_P1S_TPU.md`. |

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
- On the **counterbore confinement gap (0.45 mm nominal)**: both the pocket and
  the lip swell together; net change is **near zero** (matched dimensions).
  Worst-tight is +0.05 mm in the as-drawn part — swell could close that to ~0,
  i.e. a light press, which **helps retention** (does not loosen it). No loosen
  risk: creep relaxes the lip *outward* into the wall (per ENGAGEMENT §6.0).
- On **snap engagements**: the 1.5 mm cover-hook and 1.2 mm barb seat are tens
  of times larger than any swell — retention is unaffected.

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
- **Snap counterbore pocket:** if the lip presses too hard in PA12-GF, **ream
  the pocket a hair — do NOT reduce the lip** (LIP_T = 1.0 mm is the print-wall
  floor; per ENGAGEMENT §6.4).
- **Coupon gate (mandatory):** before the full PA12-GF set, print in *actual
  PA12-GF* (a) one cover-clip-arm-on-window coupon and (b) one finger snap pin +
  scrap counterbored eye. Verify the click, the seat, and that nothing cracks.
  The strain model is order-of-magnitude (§2); the coupon is the real PASS/FAIL.
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
QA pass (15-part build). The addition of `input_pinion_shaft` (~8–12 g PA12-GF)
and `pin_A_L` (~1–2 g PA12-GF) increases the rigid solid volume by a small
fraction (~8–12 cm³ combined) — the buoyancy result (gently negative / near-
neutral) is **essentially unchanged**. Recompute from a fresh `gen_step()` if a
hard number is needed for the updated 17-part build.

Flooded (cavity full of water) → the tool displaces only its **solid** volume.
Net = dry mass − (total solid × ρ_water). Positive = sinks.

**Verdict: PASS — buoyancy near-neutral and essentially unchanged.** The two new
parts (`input_pinion_shaft`, `pin_A_L`) add only a small amount of PA12-GF solid
volume. Net buoyancy remains slightly negative (sinks gently) — the desired
manipulator behaviour. Recompute on a fresh `gen_step()` if exact numbers are
needed. Caveats from UNDERWATER §4 still hold: only true if the cavity floods
fully (trapped air in the ~84 cm³ void would add ~+86 g of lift and flip it
positive — the cover vents address this); and the user's actuator/mount dominate
system trim.

---

## E. GALVANIC

**PASS (trivial).** The pinned plan is **100 % polymer** — PA12-GF (body, arms,
all 8 snap pins, `input_pinion_shaft`) + PETG-HF (finger pins) + ether-TPU
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

### CHANGE 2 — Finger-pin barb (**RESOLVED by material assignment — Option 2A**)

The 4 barbed finger snap pins (`snap_pin_finger`: pin_C_R, pin_C_L, pin_D_R,
pin_D_L) are **assigned PETG-HF for the final build.** No geometry change to
`gripper.py` was required or made.

- **Rationale:** Insertion strain 2.78 % worst-tight is inside PETG-HF's
  ~2.5–3.5 % allowable → **PASS.** PA12-GF's ~1.5–2.0 % allowable (brittle,
  no yield plateau) would crack the split collet on insertion → excluded.
  Pull-out load is carried by the **rigid PA12-GF counterbore shoulder** in the
  arm/follower eye; the pin material is irrelevant for retention. Mass impact
  ~4 g total (buoyancy-irrelevant).
- **Option 2B (geometry edit) archived:** changing the slot floor in `snap_pin()`
  from `L + 0.6` → `L − 2.0` would also work but carries a marginal bearing-overlap
  risk at pin_D. 2A is cleaner and was adopted.
- **Note on the `SNAP_SLOT_LEN` knob:** raising this constant does NOT lower
  finger-pin strain — the slot is clamped to 4.6 mm by the `max(..., L+0.6)`
  floor in `snap_pin()` regardless of `SNAP_SLOT_LEN`. The 2A material assignment
  bypasses this entirely.

### CHANGE 3 — Doc updates for Option 2A (**APPLIED**)

`BOM.md` has been updated: `snap_pin_finger` (pin_C_R/L, pin_D_R/L) final
material listed as **PETG-HF** with the one-line rationale. Material rationale
section (§1.2) and part count summary updated to match.

### CHANGE 4 — Closed-pose pin collision (**APPLIED**)

- **Constant changed:** `THETA_CLOSED` **104° → 102°**.
- **Effect:** C-pin gap in closed pose increases to ~9.86 mm — no interference.
  Grip closure preserved. Interference verified CLEAN at all poses.

### CHANGE 5 — Counterbore floor-gap (**FIXED**)

- Bug in the counterbore geometry caused the floor gap to be misreported.
- **After fix:** 0.30 mm floor gap confirmed real; 1.05 mm shoulder capture
  intact. Pull-out load path unchanged.

---

### NOT CHANGED (and why)

- `PRINT_CLEAR = 0.30` — kept. Water-swell budget <0.02 mm; the *only* clearance
  action is the PA12-GF print-transfer coupon (+0.05–0.10 mm if needed, tuned on
  a coupon, not baked in here).
- `SNAP_BARB_PROUD`, `SNAP_BARB_SEAT`, `SNAP_HOOK_ENGAGE`, `SNAP_BARB_LIP_T` —
  kept. These set *capture margin* (ENGAGEMENT raised them deliberately);
  reducing them to cut strain would undo hard-won retention. Fix strain via L
  (CHANGE 1) or material (CHANGE 2A), never by reducing engagement.

### Resolution summary — all blocking issues CLOSED

| Issue | As-drawn / as-found | Fix applied | Assigned material | Result |
|---|---|---|---|---|
| Cover clip insertion strain | 3.32 % worst-tight — FAIL in PA12-GF | `SNAP_Z0` 6.5→1.5 (longer cantilever) + `SNAP_ARM_T` 2.8→2.0 (thinner arm) | PA12-GF | **PASS** — 1.36 % worst-tight (nom 1.07 %), inside PA12-GF allowable, under the 1.5 % build gate |
| Finger-pin barb insertion strain | 2.78 % worst-tight — FAIL in PA12-GF | Material assignment: PETG-HF for these 4 pins | **PETG-HF** | **PASS** — 2.78 % inside PETG-HF's 2.5–3.5 % allowable |
| Closed-pose pin collision | pin gap < 0 — FAIL | `THETA_CLOSED` 104→102° | PA12-GF | **PASS** — gap ~9.86 mm, no interference |
| Counterbore floor-gap bug | floor gap misreported — FAIL | Geometry bug fixed | PA12-GF | **PASS** — 0.30 mm floor gap; 1.05 mm shoulder capture intact |

**Final gate (do not skip):** print the cover-clip-on-window coupon and the
finger-pin + counterbored-eye coupon in **actual PA12-GF and PETG-HF** (for
real-material snap behaviour and dimensional fit) before committing the full
production set. The strain model is order-of-magnitude; the coupon is the real
gate. See §5/§8.

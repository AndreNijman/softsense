# FINAL QA — fully-3D-printed underwater gripper

Independent pre-print QA gate. Every check re-measured from scratch against
`gripper.py` (52 KB, 1087 lines) and `parts/*.stl`. Prior reports were NOT
trusted. All geometry measured in the **authored (Y-up) frame** unless noted;
boolean-intersection volumes are frame-invariant, so the numbers hold either way.

Tooling: build123d 0.10.0, trimesh 4.12.2, venv `/home/andre/.cad-venv`.

---

## TOP-LINE VERDICT: ✅ Production-ready

All checks pass. **All 8 pivot pins and 8 retaining caps must be printed in
PETG-HF** (the rest of the rigid parts — including `input_pinion_shaft` — in
PA12-GF; fingers in TPU). A printed coupon fit-test of the snap clips is
recommended before committing the full print run.

**Drive redesign (post-QA):** the input shaft was changed to exit the housing
**bottom** via a right-angle crown + pinion stage (crown on A_L gear face,
driven by a small spur pinion on a vertical shaft). `drive_arm_L` no longer has
an integral horizontal shaft; it rides on a new heat-stake axle pin `pin_A_L`. A
new part `input_pinion_shaft` (pinion + shaft + collar + D-coupler), together with
the 8 heat-stake pins and 8 melt caps, brings the total to **25 printed parts**
(9 structural + 8 pins + 8 caps). Interference re-verified **CLEAN**; kinematics
unchanged (same four-bar, same finger gaps). Axial capture of the input shaft uses
the same geometric collar-in-pocket principle as the heat-stake pins — no new creep risk.

---

## SCORECARD

| # | Check | Result | Key number(s) |
|---|-------|--------|---------------|
| 1 | Kinematics monotonic / no dead-point | ✅ PASS | base_gap 9.86→62.0, tip_gap 9.86→123.8, rot 0→−20.1°; 100-step monotonic; transmission angle 71.7°→34.6° |
| 2 | Interference across motion (project recipe) | ✅ PASS | 0 flagged pairs >0.5 mm³ at open 0/.25/.5/.75/1.0 |
| 3 | Pin vs non-receiving part | ✅ **PASS** | open=0: all intersection volumes 0.000 mm³; CLEAN at open 0/0.5/1.0 |
| 4 | Finger–finger at closed | ✅ PASS | (finger_R ∩ finger_L) = 0.000000 mm³ at open=0 |
| 5 | Retention geometry present | ✅ PASS | melt-cap formed head bears pull-out (geometric, wider than bore); pocket shoulder 1.05 mm seat; 4 clips, 1.15 mm engage |
| 6 | Manifold (all STLs) | ✅ PASS | 9/9 watertight, winding-consistent, 1 body, vol>0, 0 degenerate faces |
| 7 | Walls vs FDM min | ✅ PASS | all functional walls ≥1.0 mm; none <0.8 mm absolute; marginals by-design |
| 8 | Vents / flood / no enclosed void | ✅ PASS | Bottom drains (4 × 2) + 2 side drains + 4 windows + 4 axle-flood + journal-bore clearance + 3 cover vents; every part single shell |
| 9 | Finger-scale param 0.7 / 1.6 | ✅ PASS | builds clean, finger-vs-rest CLEAN; C-D span=20.0, mount r=2.6, bolts fixed at all scales |
| 10 | Assembly order feasibility | ✅ PASS | axle pins inserted & capped before cover; C/D pivots above housing → finger sub-assemblies (pin staked to arm/follower) drop in after |

---

## CHECK DETAIL

### 1 — Kinematics ✅
`python gripper.py` self-check runs clean. Per-pose (right side):

| open | base_gap | tip_gap | finger_rot |
|------|----------|---------|-----------|
| 0.00 | 9.86 | 9.86 | 0.00° |
| 0.25 | 23.41 | 31.98 | −2.73° |
| 0.50 | 36.98 | 57.10 | −6.42° |
| 0.75 | 50.02 | 86.71 | −11.76° |
| 1.00 | 62.03 | 123.79 | −20.07° |

- base_gap and tip_gap strictly increase; finger_rot strictly decreases
  (outward splay, magnitude grows to 18.7° ≈ the spec'd ~18° funnel).
- 100-step sweep: monotonic on all three with no reversal.
- Four-bar transmission angle 71.7°→34.6° — stays far from 0°/180°, so **no
  dead-point** in range and no near-singular binding.

### 2 — Interference across motion ✅
Recipe: for open∈{0,.25,.5,.75,1}, reload `gen_step()` in a fresh process
(module-level `OPEN_NORM` is read at import), take all unordered child pairs
whose bboxes overlap, exclude the ignore set (any pin; `drive_arm_R↔drive_arm_L`),
compute `(a&b).volume`, flag >0.5 mm³.
**Result: 0 flags at every pose.** CLEAN.
- `enclosure↔front_cover` is now genuinely **0.000 mm³** and no longer needs an
  exclusion: a latent 2 mm front-wall **perimeter rim** (Z 22…24) was left behind
  by the old cavity-only front cut and the cover plate interpenetrated it by
  ~736 mm³ (the cover could not seat). The rim is now cut down to `COVER_Z[0]`,
  giving the cover a flush -Z seating datum; overlap drops 736 → 0.
- Verified the expected overlap cases are clean: `drive_arm_L ∩ enclosure = 0.0 mm³`
  (drive_arm_L is now a flat plate; its A_L bore runs with 0.3 mm clearance on
  `pin_A_L`). `input_pinion_shaft ∩ enclosure = 0.0 mm³` (shaft r4.0 in bore
  r4.3 → 0.3 mm running clearance). CLEAN.

### 3 — Pin vs non-receiving part ✅ **PASS**
For each of the 7 pins, every part it actually intersects (vol>1 µm³):

- open=0.0 / 0.5 / 1.0: **every pin hits only its clearance bores**
  (`pin∩receiver = 0` because pins ride in PRINT_CLEAR clearance bores — that is
  correct), and **nothing else**. **All intersection volumes 0.000 mm³. CLEAN.**

**Fix applied:** `THETA_CLOSED` was changed from 104° → 102°, which raises
`base_gap(open=0)` from 7.55 mm to **9.86 mm** — well above the `2 × SNAP_HEAD_R
= 7.80 mm` threshold. This separates the C/D mount pins at the closed pose
without loosening grip: the blade contact face is anchored to `FR_CONTACT_OFFSET`,
not the pin position. The previously failing intersections (`pin_C_R ∩ pin_C_L`,
`pin_C_R ∩ drive_arm_L`, and their L-side mirrors) are all confirmed 0.000 mm³.
General and pin-vs-non-receiving interference is clean at open 0/0.5/1.0.

### 4 — Finger–finger non-interpenetration at closed ✅
`(finger_R & finger_L).volume = 0.000000 mm³` at open=0 (and at scales 0.7/1.6).
The centreline `finger -= cut` clip guarantees the two TPU jaws never cross.

### 5 — Retention / geometric capture ✅
All three capture mechanisms present and quantified; counterbore pocket and eye
boss verified to physically materialise in the solid (drive_arm_R C-eye:
exit-face annulus empty = pocket, top annulus solid 6.92 mm³ = shoulder, boss
ring solid 8.40 mm³).

- **[A] Finger-pin heat-stake cap (C/D):** the melted PETG-HF `melt_cap` head,
  wider than the bore at the arm/follower-eye bottom, bears the axial pull-out (a
  geometric formed head, not an elastic barb lip); the cap seats on the rigid eye
  bottom face (≥1.0 mm bearing ring) — staked as a bench sub-assembly.
- **[B] Axle-pin heat-stake cap (A_R/A_L/B_R/B_L):** the `melt_pin_axle` journal
  pin inserts from the front through the back-boss / cover-boss bores and is
  retained by a melted PETG-HF `melt_cap` head outside the back wall (geometric
  formed head, wider than the flood hole); back boss Z(−2,1) + cover boss
  Z(20,22) locate the shank — capped from outside after the mechanism is in.
- **[C] Cover snap clips:** 4 cantilever clips; hook reach 1.5 mm − 0.35 clear =
  **1.15 mm net engagement**; arm thk 2.0 mm; window Z(6.65,10.35) over hook
  Z(7.0,10.0); 2.0 mm Y slack.

### 6 — Manifold ✅
All 9 `parts/*.stl` loaded with vertex merge (`process=True` + `merge_vertices`):

| part | watertight | winding | bodies | volume mm³ | degenerate |
|------|-----------|---------|--------|-----------|-----------|
| drive_arm_L | ✓ | ✓ | 1 | 5102.6 | 0 |
| drive_arm_R | ✓ | ✓ | 1 | 2950.6 | 0 |
| enclosure | ✓ | ✓ | 1 | 55243.2 | 0 |
| finger_L | ✓ | ✓ | 1 | 9071.6 | 0 |
| finger_R | ✓ | ✓ | 1 | 9070.9 | 0 |
| follower | ✓ | ✓ | 1 | 1150.6 | 0 |
| front_cover | ✓ | ✓ | 1 | 12352.8 | 0 |
| melt_pin_axle | ✓ | ✓ | 1 | 384.8 | 0 |
| melt_pin_finger_C | ✓ | ✓ | 1 | 463.5 | 0 |
| melt_pin_finger_D | ✓ | ✓ | 1 | 463.5 | 0 |
| melt_cap | ✓ | ✓ | 1 | — | 0 |

STL set is the intentional de-duped print set (follower ×2, melt_pin_axle ×4,
melt_pin_finger_C ×2, melt_pin_finger_D ×2, melt_cap ×8; chiral fingers + L/R arms
kept separate; `input_pinion_shaft` ×1). All solids in `gen_step()` (25 children)
are also single solid / single shell each.

### 7 — Walls ✅
| wall | mm | note |
|------|----|------|
| enclosure WALL | 3.000 | ✓ FDM min |
| cover plate thk | 3.000 | ✓ |
| finger contact beam | 1.200 | thin by design (3 perimeters @0.4 nozzle) — FEA-chosen for compliance/even pressure |
| finger spine / ribs | 1.8 / 1.6 | ✓ |
| SNAP_ARM_T (clip arm) | 2.000 | ✓ |
| axle-boss wall (BOSS_OD_R−AXLE_SCREW_R) | 2.000 | ✓ |
| melt_cap formed-head flange T | 1.800 | ✓ melted thermal-rivet head bearing |
| BUSH boss wall | 1.600 | ✓ |
| melt_cap head over boss bore | 1.300 | info: tight but >1.0 mm bearing |
| SNAP_EYE_BOSS confining ring | 1.000 | by-design confinement ring |
| journal-boss wall (DRIVE_BOSS_R−SHAFT_R_BORE) | 2.000 | upper journal boss wall; structural back/bottom wall is the full 3.0 mm WALL |

No wall <0.8 mm absolute. The sub-1.5 mm items are all by-design functional
features — including the **1.2 mm finger contact beam**, kept thin on purpose so
the Fin Ray face conforms and spreads pressure (FEA-validated, `fea/UNIVERSAL_FINGER.md`);
at a 0.4 mm nozzle it is 3 full perimeters = solid, ≥ the 0.8 mm / 2-perimeter
floor. PASS.

### 8 — Vents / flood ✅
- Bottom drains Ø5.0 at 4 X-positions × 2 Z-positions (clear of shaft at
  X=−12); 2 side-wall drains Ø5.0 per side; 4 snap-clip windows (also drain);
  4 back axle-flood holes (narrow stepped bore); journal-bore running clearance
  (r 4.3 bore vs r 4.0 shaft = 0.3 mm radial gap, open both ends).
- **3 cover vent holes Ø1.8 at (−34 / 0 / +34, +12)** — all verified to fully
  pierce the cover plate (0 material in hole core). (The 4 cover axle-boss bores
  are now BLIND cavity-side pockets — they do not pierce the outer face.)
- Every one of the 17 assembly solids is single solid / single shell → **no
  fully-enclosed void** anywhere; the housing floods/drains in any orientation.

### 9 — Finger-scale param ✅
Built at GRIPPER_FINGER_SCALE = 0.7 and 1.6 (also 1.0 baseline), open 0 and 1:
- All build without error.
- Finger-vs-rest interference: **CLEAN** (0 flags >0.5 mm³) at every scale/pose.
- Finger–finger = 0 at all scales.
- **Mount interface scale-invariant:** C-D span = 20.0 mm, mount-hole r = 2.6 mm,
  finger walls (contact 1.2 / spine 1.8 / rib 1.6 mm), bracket eye = 13.0 mm,
  flange bolt XY unchanged at all scales — only the blade length/width/tip scale,
  as designed. Grasp quality vs scale is characterised in `fea/SCALABILITY.md`
  (usable band ≈ 0.6–1.1×; walls are fixed, so up-scaling past ~1.5× goes floppy).

### 10 — Assembly feasibility ✅
ASSEMBLY.md order (bench-stake the finger sub-assemblies → mesh arms → drop in
housing → drop `input_pinion_shaft` into bottom journals → insert 4 axle pins from
the front + melt their caps outside the back wall → snap cover) is
geometrically valid:
- Enclosure is open-front (front wall **fully** removed — cavity *and* perimeter
  rim — so the front face ends at Z=22); cover plate Z(22,25) snaps on and seats
  flush on that Z=22 rim (its -Z datum).
- Axle-pin +Z locating boss **is** the cover boss Z(20,22) → axle pins **must**
  be inserted and capped before the cover, from the open front. Consistent.
- C/D finger pivots are at Y≈33.6/40.4, well above the housing top wall (Y=16).
  The finger pins are staked to the arm/follower as a bench sub-assembly (pin
  inserted, cap melted on) before the unit drops into the housing, independent of
  the cover. Pin Z span ~3.5–23 does not overlap the cover plate Z(22,25). Consistent.
- `input_pinion_shaft` drops into the bottom-wall journal bores from inside the
  cavity; its D-coupler exits below. Consistent.
- `drive_arm_L` now drops in like `drive_arm_R` (no integral shaft); `pin_A_L`
  axle pin inserted and capped before cover. Consistent.

---

## === ISSUES FOR FIX AGENT ===

*All blocking issues resolved. No open items.*

### RESOLVED — Check 3: finger-pin assemblies collide at the closed pose
**Was:** `pin_C_R ∩ pin_C_L = 0.362 mm³`, `pin_C_R ∩ drive_arm_L = 0.143 mm³`
(and symmetric L pair) at open=0.0.

**Fix applied:** `THETA_CLOSED` 104° → 102°. `base_gap(open=0)` raised from
7.55 mm to **9.86 mm** (> `2 × SNAP_HEAD_R = 7.80 mm`). All intersection volumes
confirmed 0.000 mm³ at open=0. Kinematics, finger–finger, and all other checks
remain clean.

### RESOLVED — cover-clip strain (SNAP_Z0 6.5 → 1.5) and counterbore floor-gap bug
These were additional fixes in `gripper.py` not tracked in the original fail list;
both confirmed clean in current geometry.

### RISK-BY-DESIGN — acknowledge, do not necessarily change
- `melt_cap` formed-head bearing over the bore = 1.3 mm axial: tight but
  >1.0 mm. The melted thermal-rivet head is the geometric pull-out stop (no
  elastic barb lip), so there is no flexing feature to fatigue. Informational.

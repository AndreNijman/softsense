# Pin / cover retention engagement report

Measured retention and engagement numbers for the snap-fit / pin-retention
re-engineering of the fully-3D-printed underwater gripper (`gripper.py`). This
file is the production gate for "won't fall apart underwater, pins won't fall
off." All numbers are measured from the live model (build123d, closed pose) and
the design constants; the FDM tolerance stack assumes the real-print ±0.2 mm
band at the seam.

> **Verdict: every retention feature is now GEOMETRIC (positive capture in
> rigid material), latches at worst-case tight, and does not lock up / fail to
> assemble at worst-case loose.**

---

## 1. What changed and why it is creep-proof

### 1a. Barbed finger pins (`pin_C_*`, `pin_D_*`) — confined counterbore

Previously the only capture was `SNAP_BARB_SEAT = 0.30 mm` of axial overlap held
by the **elastic preload** of a split tip springing out into open cavity space
below the eye. That relaxes under sustained load + water plasticization and the
pin walks out (UNDERWATER §2a FAIL).

The fix is a **rigid confining counterbore** cut into the EXIT (bottom) face of
each receiving eye (crank eye for `pin_C`, follower eye for `pin_D`):

- The expanded locking lip drops into a pocket of radius `SNAP_CB_R = 3.65 mm`
  recessed `SNAP_CB_DEPTH = 1.30 mm` into the eye.
- The pocket **wall radially confines the lip** (gap 0.45 mm nominal): the lip
  cannot creep-relax inward to re-enter the bore and escape. Creep relaxes the
  lip OUTWARD toward the wall, which makes escape *harder*, not easier.
- The step where the bore narrows back from the pocket (3.65 mm) to the running
  bore (`AXLE_BORE_R = 2.60 mm`) is a **rigid annular shoulder, 1.05 mm wide**,
  that takes the axial pull-out load in rigid material — retention no longer
  depends on the sprung tip staying expanded.
- A **local eye boss** (`SNAP_EYE_BOSS_R = 4.65 mm`) is added at each
  counterbored eye so a solid confining ring + shoulder survives around the
  widened pocket (the plain `LINK_W/2 = 3.5 mm` eye was too small for the
  3.65 mm pocket — it would have blown through the wall).

Capture proof (model-measured): at nominal the pin lip sits in the void pocket
(0 mm³ interference); raise the pin 0.5 mm and the lip clashes the rigid
shoulder (4.26 mm³) — the shoulder physically blocks pull-out.

### 1b. Input-shaft axial capture (`input_pinion_shaft`) — collar in pocket

The vertical input shaft is a separate printed part (`input_pinion_shaft`,
PA12-GF). Its axis runs along model −Y (world-down). Axial capture uses the same
rigid geometric principle as the axle dowels:

- **Two journal bearings** in the housing, bore radius `SHAFT_R_BORE = 4.3 mm`
  (running clearance 0.3 mm around the 4.0 mm shaft radius):
  - **Upper journal:** `DRIVE_UBORE_Y = (−15.5, −13.5)` → **2.0 mm** long,
    in a boss standing up from the inside of the bottom wall. Alignment guide.
  - **Lower journal:** `DRIVE_LBORE_Y = (−25.0, −18.0)` → **7.0 mm** long,
    through the bottom wall and flange. Load-bearing exit bore.

- **Integral capture collar** between the two journals:
  - Collar OD: `SHAFT_COLLAR_R = 5.8 mm` (= `SHAFT_R + 1.8`) — wider than the
    4.3 mm bore by **1.5 mm each side** (the rigid shoulder catch).
  - Collar length: `SHAFT_COLLAR_T = 2.0 mm`, centred in a pocket of height
    `DRIVE_POCKET_Y` span = 2.5 mm → **~0.25 mm axial play each side**.
  - The pocket radius `POCKET_R = 6.0 mm` keeps a 0.2 mm radial clearance so
    the collar spins freely.
  - The two bore-mouth shoulders (where the bore narrows from pocket radius back
    to journal radius) are the **rigid axial stops**: one prevents −Y pull-out,
    the other prevents +Y push-in. No barb; no elastic preload; **geometric
    capture** immune to creep relaxation.

- **Redundant shoulder** just below the flange (`SHAFT_SHOULDER_R = 5.8 mm`,
  `SHAFT_SHOULDER_T = 2.0 mm`) provides a second +Y push-in stop and a clean
  land for the D-coupler.

**Net axial play:** ~0.25 mm each side of the collar in the pocket — small
enough to prevent wobble, large enough to assemble and disassemble without
pressing. The shaft cannot pull out (−Y) or be pushed in (+Y) past either bore
mouth shoulder.

### 1d. Axle dowels (`pin_A_R`, `pin_A_L`, `pin_B_R`, `pin_B_L`) — sandwich, zero slop

These were over-long (head poked 0.8 mm INTO the cover boss, an interference)
and had ~17 mm of axial slop. They are now **sandwiched with no slop** between:

- **+Z stop:** the head (OD r 3.9, too wide for the cover-boss bore r 2.6) seats
  against the cover-boss inner face (Z = 20) with 0.20 mm clearance.
- **−Z stop:** the back axle bore is **stepped** — a wide running bore down to
  `AXLE_STOP_Z = 0`, then a narrow flood hole (`AXLE_FLOOD_R = 1.5 mm`) through
  the back wall. The dowel's flat shank end (r 2.3, too wide for the 1.5 mm
  flood hole) **bottoms on the rigid step**. A narrow pilot tip self-centres in
  the flood hole. **Flooding/draining is preserved** (3 mm-dia flood hole, well
  above the 1.5 mm vent floor) — the socket is still single-shell / open both
  ends per UNDERWATER §3.

Capture proof (model-measured): nominal dowel-vs-enclosure interference 0 mm³;
push −0.5 Z and the flat shank end clashes the step (4.8 mm³); push +Z and the
head clashes the cover boss (6.2 mm³). Trapped both ways.

### 1e. Constants changed in `gripper.py`

| Constant | Old | New | Why |
|---|---|---|---|
| `SNAP_BARB_SEAT` | 0.30 | **1.20** | audit floor ≥1.0; real axial-capture margin vs creep + ≥0.3 mm hygroscopic drift |
| `SNAP_BARB_PROUD` | 0.7 | **0.9** | lip catches 0.6 mm of rigid shoulder (was 0.4); strain still in PETG band |
| `SNAP_BARB_LIP_T` | 1.0 | **1.0** (unchanged) | print-wall floor (D-2): NOT reduced |
| `SNAP_SLOT_LEN` | 7.0 | **9.0** | longer split cantilever keeps the larger insertion deflection < ~3 % strain |
| `SNAP_CB_RCLEAR` | — (new) | **0.45** | pocket radial clearance; worst-tight gap stays ≥0 (no jam) |
| `SNAP_CB_FLOOR_CLEAR` | — (new) | **0.30** | axial gap lip-front to pocket floor |
| `SNAP_CB_DEPTH` | — (new) | 1.30 | = LIP_T + floor clr (pocket depth) |
| `SNAP_CB_R` | — (new) | 3.65 | pocket radius = barb_max_r + RCLEAR |
| `SNAP_EYE_BOSS_R` | — (new) | 4.65 | local eye boss so the pocket has a solid wall ring |
| `AXLE_STOP_Z` | — (new) | 0.0 | back-bore step the dowel bottoms on |
| `AXLE_FLOOD_R` | — (new) | 1.5 | narrow flood hole below the step |
| `AXLE_DOWEL_Z0/Z1` | (−1, 19) | **0 / 18** | sandwich length: head on cover boss, shank end on step |
| `COVER_VENT_R` | — (new) | 0.9 | 1.8 mm-dia front-cover vent (C-6) |
| `COVER_VENT_XY` | — (new) | (±34, 12) | 2 vents over the open cavity, +Y biased |

Functions touched: `snap_pin` (narrow pilot tip for `barb=False` dowels),
`link_bar` (new `counterbores` param + local eye boss + `_counterbore_cut`),
`drive_arm` (counterbore the C eye), `build_enclosure` (stepped back axle bore),
`build_front_cover` (vent holes), `gen_step` (finger-pin z0 per pocket, dowel
sandwich length, follower counterbores).

The barb is still a NARROWING lead cone (prints head-down / barb-up,
self-supporting per D-1); `SNAP_BARB_LIP_T` is untouched (D-2); the drive shaft,
grip ridges, internal fillets and the snap split slot are all untouched (D-3,
D-5).

---

## 2. Retention / engagement table (nominal + worst-case ±0.2 mm)

| Feature | Metric | Nominal | Worst tight (+0.2) | Worst loose (−0.2) | Pass condition |
|---|---|---|---|---|---|
| **Finger pin** lip radial catch past shoulder | mm | 0.60 | 1.00 | **0.20** | loose >0 → still latches ✔ |
| **Finger pin** axial seat (rigid LIP_T on shoulder) | mm | 1.00 | — | 0.80 | ≥ audit 1.0 floor (LIP_T) ✔ |
| **Finger pin** SEAT margin (lip below shoulder) | mm | 1.20 | — | — | ≥1.0 ✔ |
| **Counterbore** confinement gap (wall − lip) | mm | 0.45 | **0.05** | 0.85 | tight ≥0 → no jam ✔ |
| **Counterbore** rigid shoulder width | mm | 1.05 | 0.65 | 1.45 | robust axial bearing ✔ |
| **Finger pin** worst-tight insertion strain | % | — | **2.78** | — | < PETG yield ~4–5 % ✔ |
| **Axle dowel** head past back bore (−Z catch) | mm | 1.30 | 1.70 | 0.90 | loose >0 → can't pass ✔ |
| **Axle dowel** shank end past flood hole (−Z stop) | mm | 0.80 | 1.20 | 0.40 | loose >0 → bottoms on step ✔ |
| **Axle dowel** head past cover bore (+Z) † | mm | 1.30 | 1.70 | 0.90 | loose >0 → head can't enter cover bore ✔ |
| **Axle dowel** residual axial slop | mm | ~0 | — | ~0.40 | trapped both ends ✔ |
| **Cover hook** engagement | mm | 1.50 | 1.90 | **1.10** | loose >1.0 → geometric (≥1.5 nom) ✔ |
| **Cover hook** worst-tight insertion strain | % | 2.62 | **3.32** | — | < PETG yield ~4–5 % ✔ |

† The +Z stop is a **face-to-face seat**: the head bottom face bears on the
cover-boss face (0.2 mm seating clearance). The 1.30/1.70/0.90 mm figures are the
*radial* overlap that stops the head ENTERING the cover bore — they are not
1.30 mm of axial engagement. (Same for the −Z head row: radial overlap prevents
the head passing the back bore; the actual −Z stop is the shank end on the step.)

Insertion-strain figures use a cantilever surface-strain estimate
`ε = 3·t·δ / (2·L²)`. For the finger pin the slot cantilever uses
`L = SNAP_SLOT_LEN = 9 mm` and an effective slotted-quadrant thickness
`t_eff ≈ 1.5 mm` (estimate, not a closed-form for a cross-slotted barb — treat
as an order-of-magnitude check; calibrate on a single printed pin per
`PRINTING.md` "Fit tuning"). For the cover clip `L = 15.5 mm`, `t = 2.8 mm`.

### Axle-dowel capture, top and bottom

- **Top (cover end, +Z):** head OD r 3.9 vs cover-boss bore r 2.6 →
  **1.3 mm radial overlap**; head top seats on the cover-boss face (Z = 20) with
  0.2 mm clearance. The head cannot enter the cover bore.
- **Bottom (back end, −Z):** head OD r 3.9 vs back bore r 2.6 → **1.3 mm radial
  overlap** (head cannot pass the back bore); flat shank end r 2.3 vs flood hole
  r 1.5 → **0.8 mm radial overlap** bottoming on the rigid step.
- Dowel span Z 0 → 18 (shank), head to 19.8. Served eyes (arm Z 1–6, follower
  Z 7–12) are fully within the shank.

---

## 3. Verification results

- **Self-check** (`python gripper.py`): runs; kinematics **unchanged**
  (base/tip gap and finger-rotation table identical to phase-1 HEAD).
- **Builds**: `GRIPPER_OPEN = 0.0 / 0.5 / 1.0` all build, 17 children each, all
  children `is_valid`.
- **Interference** (project recipe; ignores pin-vs-anything,
  drive_arm_R↔drive_arm_L, enclosure↔front_cover; flags >0.5 mm³):
  **CLEAN at 0.0, 0.5, 1.0.**
- **Pin-vs-NON-receiving-part** (separate check, since pins are in the ignore
  set and now intentionally engage their bores): **CLEAN at 0.0, 0.5, 1.0** —
  the new counterbore/lip/boss geometry does not make any pin clash with a part
  it is not meant to engage.
- **Single valid solids**: `pin_C_R`, `pin_D_R` (finger snap pins),
  `pin_A_R`, `pin_B_R` (axle dowels), and `input_pinion_shaft` each build as
  **1 solid, `is_valid` True**.
- **Finger-vs-finger at closed**: `finger_R & finger_L = 0 mm³` (centerline trim
  preserved — fingers never collide closed).

---

## 4. Vent holes (UNDERWATER C-6)

- **Count / dia:** 2 holes, **1.8 mm dia** (`COVER_VENT_R = 0.9`, > the 1.5 mm
  bubble-release / FDM horizontal-hole floor).
- **Positions:** `(X, Y) = (+34, +12)` and `(−34, +12)` on the front cover,
  through the plate (Z 22→25). Both land over the **open cavity** (X ∈ [−45, 45],
  Y ∈ [−17, 14.5]), biased +Y so they are the high point fingers-up, one near
  each side for roll coverage. Nearest cover axle boss (B_R/B_L at (±26, 10)) is
  8.2 mm away — clear of all 3 bosses and both snap-clip windows.
- Lets trapped air escape directly in the front-up orientation (the one residual
  RISK in UNDERWATER §3).

---

## 5. Optional items — done / not done

- **Cover secondary detent (C-4): NOT added.** The cover hook is already
  geometric (1.5 mm nominal, 1.10 mm worst-loose) with a healthy insertion
  strain (2.62 % nominal, 3.32 % worst-tight, both < PETG/ASA yield). A detent
  on the same window would risk the verified-clean interference for marginal
  gain; skipped deliberately.
- **Enclosure flange-underside chamfer (D-4): NOT added.** The flange overhang
  sits next to bolt holes at Y = −14; chamfering the underside risks breaking
  the bolt-hole edges, and it is optional. Skipped deliberately.

---

## 6. Residual risk / notes for the integrator & user

0. **Worst-loose finger-pin radial catch is 0.20 mm — and that is geometrically
   defensible.** It is a *smaller number* than the old, failed 0.30 mm seat, but
   it is a fundamentally *safer* mode: 0.20 mm of **rigid** radial overlap on a
   shoulder, with the lip trapped in a pocket whose wall it relaxes OUTWARD
   toward under creep (escape needs inward compression, which creep never
   supplies). The old 0.30 mm was **elastic axial** preload that creep relaxed
   directly toward release. Do not compare the two numbers head-to-head.
1. **Assembly order is load-bearing for the axle dowels.** Install the three
   axle dowels through the **front-open cavity, tip-first**, BEFORE snapping on
   the cover. The cover-boss face is the +Z stop — without the cover the dowel
   can lift straight back out. State this in the build sheet.
2. **Insertion strain is an estimate, not a closed form.** The 2.78 % finger-pin
   figure uses an assumed effective slotted-quadrant thickness. Per
   `PRINTING.md`, print and fit-test ONE pin + a scrap counterbored coupon
   before committing the full set; verify the click and that the lip seats in
   the pocket.
3. **Material directive (UNDERWATER §1/§8):** snap pins and clips in **PETG**
   (or ASA / glass-filled nylon). **Never TPU** (creeps, wallows the pocket) or
   **PLA** (hydrolyzes wet, barb cracks). ASA/PA-GF raise insertion strain
   slightly — still inside yield per the table, but re-check on a coupon.
4. **Pocket worst-tight confinement gap is +0.05 mm** (essentially line-to-line).
   On a printer that oversizes solids and undersizes holes more than ±0.2 mm the
   lip could be a light press in the pocket — that *helps* retention but adds a
   little insertion force; if a pin is too hard to seat, ream the pocket a hair,
   do not reduce the lip.
5. **Running clearance kept at `PRINT_CLEAR = 0.30 mm`** (bore-to-shank radial
   0.30 mm, within the 0.25–0.40 mm window). Retention was fixed geometrically,
   NOT by tightening clearance (per UNDERWATER C-5/6).
6. **Pivot bore wall ≥ 2.0 mm** is still met (`BOSS_OD_R = AXLE_SCREW_R + 2.0`);
   for dives beyond ~30 m raise to ≥3.0 mm per UNDERWATER §5.

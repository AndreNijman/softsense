# Pin / cover retention engagement report

Measured retention and engagement numbers for the pin-retention
re-engineering of the fully-3D-printed underwater gripper (`gripper.py`). This
file is the production gate for "won't fall apart underwater, pins won't fall
off." All numbers are measured from the live model (build123d, closed pose) and
the design constants; the FDM tolerance stack assumes the real-print ±0.2 mm
band at the seam.

> **Verdict: every pivot pin is retained by a heat-staked melt cap — a formed
> thermal-rivet head wider than its bore, so retention is GEOMETRIC (positive
> capture in rigid material) and creep-immune. The cover clips remain geometric
> snap hooks that latch at worst-case tight and do not lock up at worst-case
> loose.**

---

## 1. What changed and why it is creep-proof

### 1a. Finger pins (`melt_pin_finger_C` ×2, `melt_pin_finger_D` ×2) — heat-staked melt cap

Previously the only capture was `SNAP_BARB_SEAT = 0.30 mm` of axial overlap held
by the **elastic preload** of a split barb tip springing out into open cavity
space below the eye. That relaxes under sustained load + water plasticization and
the pin walks out (the original UNDERWATER §2a FAIL).

The finger pins are now **two SKUs of plain printed journal pin**, each retained
by a separate printed **melt cap** (`melt_cap`, qty 8 total across the gripper):

- `melt_pin_finger_C` (×2, **long**, crank-layer → `pin_C_R` / `pin_C_L`) and
  `melt_pin_finger_D` (×2, **short**, follower-layer → `pin_D_R` / `pin_D_L`).
  The old single finger-pin SKU is gone; the crank and follower eyes sit at
  different layers, so the two lengths are distinct parts.
- Each pin passes through its eye and protrudes a **melt-stud** out the bottom
  (arm eye for `pin_C`, follower eye for `pin_D`). You **slip a `melt_cap` over
  the stud and fuse it with a soldering iron** — the stud and cap flow into a
  single **thermal-rivet head wider than the bore**. Capped at the arm/follower
  eye BOTTOM as a bench sub-assembly.
- Retention is purely **geometric**: a formed rivet head straddles the joint
  exactly like the pin head on the other face. **Nothing flexes** (no sprung
  barb to stress-relax) and **nothing relies on friction** (no press fit to
  slip), so the creep / pull-out mode is eliminated by mechanism — there is no
  counterbore pocket and no `SNAP_BARB_*` engagement margin involved.

Capture proof (mechanism): pull-out is blocked because the melted head (wider
than the bore) physically cannot pass the eye; there is no elastic feature whose
relaxation could release it.

### 1b. Input-shaft axial capture (`input_pinion_shaft`) — install-from-below

The vertical input shaft is a separate printed part (`input_pinion_shaft`,
PA12-GF). Its axis runs along model −Y (world-down).

> **Corrected design.** An earlier version captured a mid-shaft COLLAR (OD 5.8 mm
> > both 4.3 mm bores) in a pocket between the two journals. That was
> geometrically captured but **un-installable**: the collar could not pass either
> journal, and the housing parting plane (the front cover, at Z≈22) is ~11.5 mm
> away from the journal (Z≈10.5), so it could not clamshell it either — the
> one-piece shaft had no assembly path. The collar is **gone**. Capture is now at
> the accessible ends:

- **One continuous journal** in the housing, bore radius `SHAFT_R_BORE = 4.3 mm`
  (running clearance 0.3 mm around the 4.0 mm shaft radius), made of the boss
  upper bore + the wall/flange lower bore with no pocket between them — a longer,
  uninterrupted bearing.

- **Installable one-piece shaft.** Every feature from the pinion down is
  ≤ `SHAFT_R = 4.0 mm` < bore, so the part drops **in from below** (−Y),
  pinion-first up through the journal into the cavity (`PINION_TIP = 3.72 mm` <
  bore → the pinion passes). Sequence: assemble the internals from the open
  front and snap the cover on, then push the input shaft up from underneath.

- **+Y push-in stop:** the bottom **shoulder** (`SHAFT_SHOULDER_R = 5.8 mm` >
  bore) bottoms on the flange outer face. Rigid, geometric.

- **−Y pull-out stop:** the bottom D-coupler engages the actuator horn-adapter /
  wet D-socket bolted under the flange (`motor/cad/system_assembly.py`), which
  blocks the shaft from dropping once the servo is mounted.

The shaft cannot be pushed in (+Y) past the flange shoulder, and cannot pull out
(−Y) once the actuator is bolted on.

### 1c. Right-angle crown↔pinion mesh — genuine tooth interleave

The input pinion drives a crown (face-tooth) ring on the A_L crank gear. The
mesh is **representative** (straight-flank, coupon-tunable, like the spur gears).

> **Corrected design.** An earlier version built the crown ring at full Z-height
> with the face teeth living *inside* it — the teeth added ~0.3 mm³ (swallowed),
> so the crown was a smooth washer and the pinion just plunged into solid material.
> `_crown_gear` now builds a thin base ring + PROUD teeth with open valleys, and
> their Z-extents are computed from the pinion so the crown tips clear the spinning
> pinion ROOT cylinder (`CROWN_MESH_CLEAR = 0.4 mm`) while the valley floor sits
> below the pinion tip. Teeth now add ~270 mm³.

Verified as a real interleave, not a tip graze nor a core clash:
- **Engagement:** the pinion tip drops into the crown valley with 0.4 mm floor
  clearance; the crown tooth tips reach into the pinion tooth-gaps with 0.4 mm
  clearance to the pinion root cylinder (so the pinion spins free).
- **Interleave test (the proof):** rotating the pinion about its own axis (crown
  fixed) swings the static overlap **3.0 mm³ (mesh phase) → 6.6 mm³ (¼ tooth) →
  3.0 mm³** — phase-periodic. A graze or a core clash would stay flat; this swing
  is the signature of teeth sitting in valleys and clearing into the gaps.
Pitches match (crown 2π·8/24 = pinion 2π·3/9 = 2.09 mm), so rotation transmits.
Tune backlash with a coupon print like the other gears.

### 1d. Axle pins (`melt_pin_axle` ×4 → `pin_A_R`, `pin_A_L`, `pin_B_R`, `pin_B_L`) — riveted to the back wall

These are now plain printed PETG-HF journal pins (previously plain PA12-GF
dowels — glass-filled PA12-GF melts poorly under a soldering iron, so they too
are PETG-HF now). Each is **riveted to the back wall** by a heat-staked cap, a
fixed pivot post:

- **Head, +Z:** the pin head (OD r 3.9, too wide for the cover-boss bore r 2.6)
  seats **under the cover boss** (Z = 20) with 0.20 mm clearance. The cover is
  **no longer the retainer** — it just locates the head.
- **Shank bottoms on the back-bore step:** the back axle bore is **stepped** — a
  wide running bore down to `AXLE_STOP_Z = 0`, then a narrow flood hole
  (`AXLE_FLOOD_R = 1.5 mm`) through the back wall. The pin's shank shoulder
  (r 2.3, too wide for the 1.5 mm flood hole) **bottoms on the rigid step**.
- **Melt-stud caps from OUTSIDE the back face:** the pin's stud threads the
  back-wall flood hole and is heat-staked with a `melt_cap` on the **outside** of
  the back wall, forming a rivet head wider than the flood hole. The pin is thus
  a fixed pivot post — retention is geometric (a formed head), independent of the
  cover. **Flooding/draining is preserved** (the flood hole stays open around the
  thin stud / under the formed cap) — the socket is still single-shell / open
  both ends per UNDERWATER §3.

Capture proof (mechanism): the +Z head cannot enter the cover-boss bore and the
−Z melt-cap head cannot pass the back-wall flood hole; the pin is riveted between
the two formed/geometric heads, trapped both ways.

### 1e. Pin set in `gripper.py`

The sprung-barb / confined-counterbore approach (the whole `SNAP_BARB_*` and
`SNAP_CB_*` family of constants) is **removed**. Retention is now the heat-stake
melt cap, so the pin set is:

| Part | Qty | Role | Material |
|---|---|---|---|
| `melt_pin_axle` | 4 | axle pivot posts (A_R/A_L/B_R/B_L), riveted to back wall | PETG-HF |
| `melt_pin_finger_C` | 2 | long crank-layer finger pins (`pin_C_R/C_L`) | PETG-HF |
| `melt_pin_finger_D` | 2 | short follower-layer finger pins (`pin_D_R/D_L`) | PETG-HF |
| `melt_cap` | 8 | push-on cap heat-staked over each pin's melt-stud | PETG-HF |

Surviving retention geometry: `AXLE_STOP_Z` (back-bore step the axle pin's shank
bottoms on) and `AXLE_FLOOD_R` (narrow back-wall flood hole the melt-stud threads
and is capped through, on the outside). The three front-cover vents (C-6) are
unchanged.

Each pin is a plain stepped cylinder with a protruding melt-stud — no barb cone,
no split slot, no counterbore pocket. The drive shaft, grip ridges, internal
fillets and the cover snap split slot are all untouched (D-3, D-5).

---

## 2. Retention / engagement table (nominal + worst-case ±0.2 mm)

| Feature | Metric | Nominal | Worst tight (+0.2) | Worst loose (−0.2) | Pass condition |
|---|---|---|---|---|---|
| **Finger pin** retention | — | melt-cap head wider than bore | — | — | geometric (formed head) → no creep/pull-out path ✔ |
| **Axle pin** head past cover bore (+Z) † | mm | 1.30 | 1.70 | 0.90 | loose >0 → head can't enter cover bore ✔ |
| **Axle pin** shank shoulder past flood hole (−Z stop) | mm | 0.80 | 1.20 | 0.40 | loose >0 → bottoms on step ✔ |
| **Axle pin** melt-cap head (back face, −Z) | — | rivet head wider than flood hole | — | — | geometric → riveted to back wall ✔ |
| **Axle pin** residual axial slop | mm | ~0 | — | ~0.40 | trapped both ends ✔ |
| **Cover hook** engagement | mm | 1.50 | 1.90 | **1.10** | loose >1.0 → geometric (≥1.5 nom) ✔ |
| **Cover hook** worst-tight insertion strain | % | 1.07 | **1.36** | — | < 1.5 % PA12-GF build gate ✔ |

† The +Z head row is a **face-to-face seat**: the head bottom face bears on the
cover-boss face (0.2 mm seating clearance). The 1.30/1.70/0.90 mm figures are the
*radial* overlap that stops the head ENTERING the cover bore — they are not
1.30 mm of axial engagement.

The cover-clip insertion-strain figure uses a cantilever surface-strain estimate
`ε = 3·t·δ / (2·L²)` with `L = 20.5 mm`, `t = SNAP_ARM_T = 2.0 mm`. The pins
themselves no longer flex (no barb), so there is no pin insertion strain to
estimate — they push straight through their bores and are capped afterward.

### Axle-pin capture, top and bottom

- **Top (cover end, +Z):** head OD r 3.9 vs cover-boss bore r 2.6 →
  **1.3 mm radial overlap**; head top seats under the cover-boss face (Z = 20)
  with 0.2 mm clearance. The head cannot enter the cover bore. The cover only
  locates the head — it is no longer the retainer.
- **Bottom (back end, −Z):** flat shank shoulder r 2.3 vs flood hole r 1.5 →
  **0.8 mm radial overlap** bottoming on the rigid step; the melt-stud threads
  the flood hole and is heat-staked into a rivet head on the **outside** of the
  back wall, riveting the pin to the back wall (a fixed pivot post).
- Pin span Z 0 → 18 (shank), head to 19.8. Served eyes (arm Z 1–6, follower
  Z 7–12) are fully within the shank.

---

## 3. Verification results

- **Self-check** (`python gripper.py`): runs; kinematics **unchanged**
  (base/tip gap and finger-rotation table identical to phase-1 HEAD).
- **Builds**: `GRIPPER_OPEN = 0.0 / 0.5 / 1.0` all build, 17 children each, all
  children `is_valid`.
- **Interference** (project recipe; ignores pin-vs-anything,
  drive_arm_R↔drive_arm_L; flags >0.5 mm³): **CLEAN at 0.0, 0.5, 1.0.**
  `enclosure↔front_cover` is now genuinely **0 mm³** (the front-wall perimeter rim
  that the cover plate used to interpenetrate by ~736 mm³ is cut to `COVER_Z[0]`,
  so the cover seats flush) — no longer in the ignore set.
- **Pin-vs-NON-receiving-part** (separate check, since pins are in the ignore
  set and now intentionally engage their bores): **CLEAN at 0.0, 0.5, 1.0** —
  the journal-pin / melt-stud geometry does not make any pin clash with a part
  it is not meant to engage.
- **Single valid solids**: `melt_pin_finger_C`, `melt_pin_finger_D` (finger
  pins), `melt_pin_axle` (axle pins), `melt_cap` (retainer caps), and
  `input_pinion_shaft` each build as **1 solid, `is_valid` True**.
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
  strain (1.07 % nominal, 1.36 % worst-tight, both inside the PA12-GF allowable). A detent
  on the same window would risk the verified-clean interference for marginal
  gain; skipped deliberately.
- **Enclosure flange-underside chamfer (D-4): NOT added.** The flange overhang
  sits next to bolt holes at Y = −14; chamfering the underside risks breaking
  the bolt-hole edges, and it is optional. Skipped deliberately.

---

## 6. Residual risk / notes for the integrator & user

0. **Retention is geometric by mechanism, not by a margin number.** Each pin is
   held by a melted rivet head wider than its bore: there is **no elastic
   feature** whose worst-loose value could fall to zero and release, so there is
   no creep path to defend with a seat number. This is a fundamentally safer mode
   than the old elastic-axial barb preload (which crept directly toward release).
1. **Assembly order: cap the axle pins from OUTSIDE the back wall.** Insert each
   axle pin from the **front-open cavity, tip-first**, so the head seats under
   the cover boss and the melt-stud protrudes through the back-wall flood hole;
   slip a `melt_cap` on the stud and heat-stake it on the **outside** of the back
   face. The pin is then riveted to the back wall, so the cover is **not** the
   retainer — assemble the internals, melt the axle caps, then snap the cover on
   (the cover only locates the head). State this in the build sheet.
2. **Melt the cap on a coupon first.** Per `PRINTING.md`, print ONE pin + cap +
   a scrap bore coupon and heat-stake it before committing the full set; verify
   the formed head is wider than the bore, fully fused, and that the pin can no
   longer be pulled out.
3. **Material directive (UNDERWATER §1/§8):** ALL pins and caps in **PETG-HF**
   (heat-stakes cleanly under a soldering iron); cover clips in **PETG** (or ASA
   / glass-filled nylon). **Never TPU** for any pin (creeps, wallows the bore) or
   **PLA** (hydrolyzes wet). Glass-filled PA12-GF melts poorly and is **not** used
   for any pin or cap.
4. **Form a full melt-cap head.** Heat-stake until the cap and stud flow into a
   single head that visibly overhangs the bore all round; under-fusing (a cap
   that only tacks on) loses the geometric capture. If a pin is hard to insert
   before capping, ream the bore a hair — do not skip the cap.
5. **Running clearance kept at `PRINT_CLEAR = 0.30 mm`** (bore-to-shank radial
   0.30 mm, within the 0.25–0.40 mm window). Retention was fixed geometrically,
   NOT by tightening clearance (per UNDERWATER C-5/6).
6. **Pivot bore wall ≥ 2.0 mm** is still met (`BOSS_OD_R = AXLE_SCREW_R + 2.0`);
   for dives beyond ~30 m raise to ≥3.0 mm per UNDERWATER §5.

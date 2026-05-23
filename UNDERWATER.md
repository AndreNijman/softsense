# Running this gripper underwater

Sustained-immersion durability + material-selection audit for the **fully
3D-printed, zero-hardware** geared four-bar / Fin Ray gripper (see `gripper.py`,
`BOM.md`, `DFM.md`). This is the production-readiness material/seawater gate:
print it in the right polymers, accept the snap-fit constraints below, and dive
it **flooded** — there is nothing to seal inside the gripper itself.

> **Scope note.** The gripper is all-polymer and fastener-free: Fin Ray fingers
> in TPU; 8 printed snap pins (4 axle dowels + 4 barbed finger pins); a 4-clip
> snap-on front cover; flooded enclosure with drain holes; a separate printed
> `input_pinion_shaft` part (pinion + vertical shaft + collar + bottom D-coupler,
> exits the housing bottom) driven via a right-angle crown + pinion stage.
> **The only metal/sealing burden in the whole system is the user's own
> waterproof actuator** (see §6), which now couples to the bottom D-shaft.
> Earlier drafts of this file described a stainless-hardware build and a
> rear/side shaft exit — both obsolete and removed.

This is the **material / seawater** companion to `PRINTING.md` (orientation,
supports, slicer) and `DFM.md` (printability). Decide *how* to print there;
decide *what to print it in* and how to run it wet here.

---

## Audit summary (measured against `gripper.py`)

| # | Check | Verdict | Evidence (measured from the model) |
|---|---|---|---|
| 1 | Material selection for sustained seawater | **RISK** | PETG/ASA/glass-nylon + ether-TPU are correct; **PLA must be rejected** (hydrolysis); untreated nylon swells; ester-TPU hydrolyzes. See §1. |
| 2 | Creep at load-bearing snap interfaces | **RESOLVED** (was FAIL as drawn) | Fixed: finger-pin lips now snap into a **rigid counterbore pocket** that radially confines them (creep relaxes them *outward*) and bears load on a solid shoulder; `SNAP_BARB_SEAT` 0.30→1.2 mm. Axle dowels captured between a back-bore step and the cover boss. Capture is now **geometric**, not preload. Measured numbers in `ENGAGEMENT.md`. See §2 + CONSTRAINTS (now satisfied). |
| 3 | Flooded-correctness (no trapped air) | **PASS** (1 RISK) | **Every part is a single solid, 1 shell each → no sealed internal pocket anywhere** (cells, cross-slots, sockets, shaft bore all vent to exterior). 5 bottom drains + 4 side drains + 4 snap windows + 2 top slots + back bores. Floods/drains fingers-up, fingers-down, back-up. **RISK:** front-up (+Z up) vents only via the slot/cover corner — add a cover vent (see §3). |
| 4 | Net buoyancy | **PASS** | Solid vol **98.5 cm³**, dry mass ~**124 g** (PETG+TPU, 100% infill). Flooded → displaces solid vol only → **net ≈ +23 g in seawater (sinks gently, near-neutral)**. No ballast needed. See §4. |
| 5 | Galvanic corrosion | **PASS** | **Zero metal in the gripper.** All 8 pins and `input_pinion_shaft` are printed, snap-clip cover, no fasteners. No dissimilar-metal pair exists. See §5. |
| 6 | Drive coupler / actuator | **FLAG (user)** | Bottom D-flat coupler on `input_pinion_shaft` (`SHAFT_COUPLER_R = 5.0`, `SHAFT_DFLAT = 1.4`, length 12 mm) needs a **user-supplied waterproof actuator** (IP68/sealed/flooded servo, potted servo, or magnetically-coupled drive) coupling from below. The gripper does NOT provide this. See §6. |

---

## 1. Material selection for sustained immersion

Seawater is the hard case. The committed per-part picks (all printable on a
0.4 mm-nozzle FDM machine):

| Part (from `gripper.py`) | Seawater material | Why / what to avoid |
|---|---|---|
| `enclosure` (flooded housing) | **PETG** default; **ASA** for topside/UV; **glass-filled nylon (PA-GF) or acetal/POM** for deep/long/warm dives | Low water uptake, **no hydrolysis**. **Never PLA.** Avoid **untreated cast nylon** (PA6/PA12 absorb 1–3 %+ water, swell, soften, drift dimensionally) — only **glass-filled** nylon is dimensionally acceptable. PETG-CF is fine. |
| `front_cover` (snap-on, 4 clips) | Same as enclosure | The 4 cantilever snap clips must stay springy — see creep note §2. |
| `drive_arm_R` / `drive_arm_L` (gear+arm) | **PETG**, or **acetal/POM** / PA-GF for real torque | Self-lubricating teeth run dry flooded; water is coolant. POM is the best wet gear polymer. |
| `input_pinion_shaft` (separate printed part) | **PA12-GF** | Vertical shaft, pinion, and D-coupler in one part. Runs in two flooded journal bores in the bottom wall (upper 2 mm alignment bore, lower 7 mm load bore) — no bushing, no seal. Integral collar geometrically trapped in housing pocket (creep-proof axial capture). PA12-GF's low creep keeps journals round. |
| `follower` ×2 | PETG / ASA / PA-GF | Symmetric link, same part both sides. |
| `finger_R` / `finger_L` (Fin Ray) | **Ether-based TPU ~95A** (e.g. NinjaFlex, BASF ether grades) | **Reject ester-based TPU** — it hydrolyzes in sustained/warm immersion and crumbles. Ether-TPU is hydrolysis-stable. TPU absorbs a little water and softens slightly (re-check grip force if tuned tight). |
| 8 snap pins (4 axle dowels + 4 barbed finger pins) | **PA12-GF** (axle dowels); **PETG-HF** (finger pins) | Axle dowels are plain rigid sandwiched dowels. Finger pins must flex their barb — PETG-HF for ductility. **TPU is wrong for any pin** (creeps, wallows the bore). |

**Rejected picks (do not use underwater):**

- **PLA** — hydrolyzes; absorbs water; loses strength over days/weeks wet. Reject
  for every part, even though general FDM guides list it.
- **Ester-based TPU** — hydrolyzes; fingers eventually crumble. Use ether-TPU.
- **Untreated (unfilled) nylon** — water absorption → swelling, dimensional
  change, softening. Only **glass/CF-filled** nylon is acceptable.
- **Oil-impregnated bronze (Oilite) bushings** — N/A here (no bushings), but if
  you ever add one: the oil leaches out flooded, leaving a dry porous bush. Use
  solid PTFE/acetal instead.

**UV / biofouling:** for surface or shallow gear, **ASA** resists UV better than
PETG (which yellows/embrittles in sun over months). Biofouling (algae, barnacle
spat) settles in the open mesh and drains; rinse with fresh water after every
dive and the flush path (drains + slots) clears it.

---

## 2. Creep / stress-relaxation — the load-bearing snap interfaces (RESOLVED)

> **RESOLUTION (implemented).** This was the production-blocking finding; it is
> now fixed in `gripper.py`. Finger-pin lips snap into a **rigid counterbore
> pocket** that radially confines the lip (creep can only relax it *outward*,
> away from escape) and bears pull-out load on a solid annular shoulder;
> `SNAP_BARB_SEAT` raised 0.30→1.2 mm. Axle dowels are sandwiched with zero
> slop between a back-bore step (−Z) and the cover boss (+Z). Capture is now
> **geometric, not preload-dependent**. Measured nominal + worst-case (±0.2 mm
> FDM) numbers are in `ENGAGEMENT.md`. The analysis below is retained as the
> rationale for the fix; the CONSTRAINTS block at the end is now satisfied.

**Why it mattered.** Polymers under *constant* load do
not behave like metals: they creep, and any locking feature that depends on
**stored elastic preload** slowly relaxes. Submersion makes it worse — water
plasticizes PETG/nylon (lowers modulus and Tg), and warm shallow water adds
temperature. Over days-to-weeks submerged, a preload-held catch can relax below
its engagement and release.

### 2a. Barbed finger/axle pins — original failure mode (now fixed, see RESOLUTION above)

Measured from the *original* `snap_pin()` (pre-fix):

- Shank radius `PIN_R = 2.3`; barb lip projects to `barb_max_r = PIN_R +
  SNAP_BARB_PROUD = 3.0 mm`.
- The bore it passes through is `MOUNT_HOLE_R = 2.6 mm`, so the split tip must
  flex **0.4 mm radially** and then spring back out.
- The **entire positive-capture is `SNAP_BARB_SEAT = 0.30 mm`** of axial overlap
  of the lip past the far bore face.
- The split (`SNAP_SLOT_W = 1.0`, `SNAP_SLOT_LEN = 7.0`) makes the tip a sprung
  cantilever — its outward projection is **held by elastic preload**.

Failure path: under sustained side load on the pivot + the barb's standing
preload, the split tip stress-relaxes inward. Once the relaxed lip projection
falls below the 0.30 mm seat (plus hygroscopic dimensional drift, which can
itself be ~0.1–0.3 mm), the pin would **walk out and the joint release**. 0.30 mm
was far too little margin for a creep-prone polymer holding a constant load for
days underwater. **This drove the geometric-capture redesign** described in the
RESOLUTION box above (confined counterbore + 1.2 mm seat).

### 2b. Front-cover snap clips — geometric, but watch arm relaxation → RISK

The 4 cover clips hook behind a wall step: `SNAP_HOOK_ENGAGE = 1.5 mm` of
mechanical capture, and the wall material above each window physically blocks
the cover lifting. That is **geometric capture, not pure preload**, so it does
**not** fail the same way — the hook can only release if the arm flexes 1.5 mm
outward. **RISK** only: over long immersion the cantilever arm (`SNAP_ARM_T =
2.8 mm`) can stress-relax and reduce hold-down preload (cover rattle), but it
will not spontaneously unlatch. Acceptable; the fix (deeper engagement / stiffer
material) is in the constraints block.

> The hard, quantified requirements for fixing 2a/2b are in the
> **CONSTRAINTS FOR A (snap-fit/pin agent)** block at the end of this file.

---

## 3. Flooded-correctness — floods AND drains, no trapped air

**Geometry-level proof:** building the assembly and counting shells, **every
one of the 17 parts is a single solid with exactly 1 shell** — i.e. there is
**no fully enclosed internal void anywhere in the model.** Every feature that
could trap air is open to the exterior:

- **Snap-pin cross-slot** — the `+` slot is cut through to the barb tip (open
  end), not a blind pocket. Vents.
- **Axle dowel sockets (A_R, B_R, B_L)** — the enclosure bore runs Z −15…+1
  (through to the **back exterior**, back face at −12) and the cover bore runs
  Z 20…25 (through to the **front exterior**), with a 0.3 mm annular gap around
  the 2.3 mm dowel. Open both ends → floods/drains.
- **Input-shaft journal bores** — upper bore (r 4.3, len 2 mm in the cavity
  boss) and lower bore (r 4.3, len 7 mm through the bottom wall) around the
  Ø8 mm shaft (0.3 mm radial gap). Both bores are open both ends → floods and
  drains freely. The bearing clearance doubles as a flood path; the shaft's
  flooded running surface needs no seal.
- **Finger rib cells** — the Fin Ray cavity and ribs are 2.5-D extrusions
  through the **full 10 mm Z depth**: each cell is an **open channel** on both
  the front and back faces of the finger, not a sealed pocket. Single-shell
  confirmed. Floods/drains.

**Enclosure cavity openings** (so the housing floods/drains by orientation).
With model −Y = world-DOWN (shaft exits bottom), the model −Y wall is the
low point in the deployed orientation:

- **Bottom drains:** 4 X-positions × 2 Z-positions = 8 Ø5 mm holes through the
  bottom wall and flange, around the shaft exit.
- **Low side-wall drains** Ø5 mm (2 per side wall).
- **4 snap-clip windows** in the side walls (double as drains).
- **2 wide top slots** where the arms/fingers emerge (open to the world +Z
  exterior when fingers are up).
- **4 axle bores** through the back wall (A_R, A_L, B_R, B_L — all stepped,
  flood via the narrow pilot hole).
- **Journal bores** through the bottom wall (upper + lower — double as flood
  paths via the running clearance).

**Air-trap by orientation** (air rises to the highest point):

- **Fingers up (deployed):** highest point = the open top slots → vents.
  **PASS.**
- **Fingers down:** highest point = the bottom drains → vents. **PASS.**
- **Back up:** highest point = back wall = 4 axle bores → vents. **PASS.**
- **Front up (+Z up in model / fingers-horizontal):** the cover plate becomes
  the ceiling. The only openings reaching that plane are the top slots'
  front-top corners; a bubble must migrate along the cover/slot junction to
  escape. The path **exists** but is indirect. **RISK** — see fix below. The
  internal void is ~84 cm³; if it held air that is **+86 g of buoyancy** and an
  unequalized crush load — so guaranteeing the flood matters.

**Recommended fix for the front-up case (constraint for the cover/snap agent):**
add **2 vent holes (≥1.5 mm dia) through the front cover plate** at the +Y
(finger-side) corners, above the cavity, so air against the cover ceiling
escapes directly regardless of orientation. Cheap insurance; see CONSTRAINTS.

> Note on infill: a part printed at low infill has interconnected internal voids
> that are **not watertight** — they flood slowly through the print's micro-
> porosity. For predictable buoyancy and faster equalization, print structural
> parts at **high infill (≥40 %) or with solid walls**; do not assume low-infill
> air stays put.

---

## 4. Net buoyancy

Measured: solid material volume **98.5 cm³** (rigid 80.3 + TPU 18.1). At 100 %
infill (PETG ρ≈1.27, TPU ρ≈1.21) dry mass ≈ **124 g**. **Flooded**, the tool
displaces only its solid volume, so:

- **Seawater (ρ 1.025):** buoyant mass ≈ 100.9 g → **net ≈ +23 g (sinks
  gently / near-neutral).**
- **Freshwater (ρ 1.00):** net ≈ +25.5 g.

**Verdict: PASS — no ballast required.** It is slightly negative, which is the
desired behaviour for a manipulator (it won't float away if released). Two
caveats: **(a)** only true if the cavity is fully flooded — trapped air in the
~84 cm³ enclosure void would add up to ~+86 g of buoyancy and flip it positive
(see §3); **(b)** the user's actuator + mount dominate the system trim — account
for them separately.

---

## 5. Galvanic corrosion

**PASS — not applicable.** The gripper is **100 % polymer**: all 8 snap pins
(4 axle dowels + 4 finger pins) are printed, `input_pinion_shaft` is printed PA12-GF,
the front cover latches with 4 integral printed clips, and there are no screws, nuts,
bushings, or inserts. With no dissimilar-metal contact there is **no galvanic cell,
no anode to drive, nothing to pit or rust.**

The only galvanic consideration is **external**: the M4 flange holes pass
through to the user's robot arm. If that arm is metal, isolate the bolted joint
with **nylon/PTFE shoulder bushings + isolating washers** — but the gripper
itself contributes no metal to that joint.

---

## 6. Drive coupler & actuator — FLAG for the user

The **bottom D-flat coupler** on `input_pinion_shaft` (`SHAFT_COUPLER_R = 5.0 mm`,
`SHAFT_DFLAT = 1.4 mm`, `SHAFT_COUPLER_LEN = 12 mm`) exits below the housing
bottom flange. It transmits all drive torque and is the **only interface that
needs a waterproof actuator**. The actuator couples from below.

**FLAG (you must supply this — the gripper does not):** drive the coupler with
one of:

- a **submersible / IP68-rated servo**, or a **potted/sealed hobby servo**, or
- a **sealed or oil-filled actuator with a pressure compensator** for deeper/
  longer work, or
- a **magnetically-coupled drive** (no shaft penetration at all — cleanest for
  deep work).

The flooded gripper has **no shaft seal and no dry cavity** — the printed shaft
turns wet in flooded journal bores. **Do not** drive the coupler with a bare
unsealed servo; that servo will flood and die. Match the actuator's depth rating
to your dive — the actuator, not the gripper, sets the system depth limit.

---

## Pre-dive / post-dive checklist

**Pre-dive**

- Confirm material: no PLA, no ester-TPU, no unfilled nylon anywhere.
- Confirm snap pins meet the creep constraint (§2 / CONSTRAINTS) — geometric
  capture, adequate seat. Tug-test every pin and the cover before diving.
- Confirm all drains/slots/windows/journal bores are clear; confirm cavity floods
  (submerge, watch bubbles fully clear in your dive orientation; add the cover vent
  if you dive front-up).
- Cycle open↔close in air; check smooth mesh, full travel, cover stays latched.
- Confirm the actuator is sealed and rated for depth.
- Verify buoyancy trim with the gripper + actuator fitted.

**Post-dive**

- **Rinse thoroughly with fresh water** (flush mesh, drains, slots) — salt
  crystallizes and abrades.
- Cycle to flush grit; inspect teeth and pins for wear, the TPU for swelling.
- Inspect every snap pin and the cover clips for any loss of engagement
  (the creep failure mode) — replace pins that have loosened.

---

## What's in the CAD vs. what you choose at fabrication

**In `gripper.py` already:** flooded geometry (slots + bottom drains + windows +
back axle bores + journal bores), all-polymer zero-hardware assembly, single-shell
parts (no sealed pockets), TPU Fin Ray fingers, the bottom D-flat coupler on
`input_pinion_shaft`.

**You choose at fabrication:** the per-part polymer (§1 — never PLA/ester-TPU/
unfilled nylon), infill (≥40 % for predictable flooding/buoyancy), and the
waterproof actuator (§6). And **the snap-fit agent must apply the creep fixes
below before this is dive-ready.**

---

=== CONSTRAINTS FOR A (snap-fit/pin agent) ===

Hard, quantified requirements the snap-fit / pin design must satisfy for
sustained underwater (days–weeks) constant-load service. Rationale: polymers
creep under constant load and water plasticizes PETG/nylon, so any preload-held
catch relaxes and releases. Numbers are measured from the current `gripper.py`.

1. **Retention must be GEOMETRIC, not friction/elastic-preload.** The pin must
   be held by a positive mechanical step that exists in *rigid* material
   independent of the barb's elasticity. A split barb whose hold depends on the
   sprung tip staying expanded is **not acceptable** — it creeps and releases.

2. **Barbed-pin axial capture floor:** raise `SNAP_BARB_SEAT` from **0.30 mm**
   to **≥ 1.0 mm** (target 1.0–1.5 mm). Rationale: must survive (a) sustained-
   load stress-relaxation of the split tip and (b) ≥0.3 mm hygroscopic/thermal
   dimensional drift, with margin. 0.30 mm has zero margin against either.

3. **Preferred fix — eliminate the sprung barb entirely:** replace each barbed
   pin with a **two-piece captured pin**: a headed pin pushed in from one side +
   a separate **push-on retainer cap** snapped onto the protruding tip from the
   other side, where **both the head and the cap are wider than their bores**
   (e.g. head/cap OD ≥ bore OD + 2×0.8 mm). Capture is then purely geometric
   (two flanges straddling the joint) and creep-immune. If a one-piece pin is
   kept, the barb lip overlap must meet item 2 **and** the lip face must seat
   against a rigid counterbore shoulder, not free-spring in open space.

4. **Cover snap clips (currently OK, harden them):** keep capture geometric.
   `SNAP_HOOK_ENGAGE` is **1.5 mm** today — keep **≥ 1.5 mm**; if switching to a
   stiffer cover polymer (ASA/PA-GF) verify the arm can still flex enough to
   assemble (insertion strain < material yield). Add a small **secondary
   detent/lip** so a creep-relaxed arm cannot back out under vibration.

5. **Pivot bore wall under external pressure:** keep **≥ 2.0 mm** wall around
   every pivot bore (current `BOSS_OD_R = AXLE_SCREW_R + 2.0` = 2.0 mm wall —
   meets floor). For dives beyond ~30 m, increase to **≥ 3.0 mm** so the bore
   does not creep-ovalize under sustained hoop stress + side load.

6. **Bearing clearance vs. creep:** current pivot clearance `PRINT_CLEAR =
   0.30 mm` (bore = `PIN_R + 0.30`). Do **not** reduce it to fight wallowing —
   a tight bore + creep galls. Instead fix retention geometrically (items 1–3)
   and keep the 0.30 mm running clearance. Floor for the chosen creep-prone
   material: **bore-to-shank radial clearance ≥ 0.25 mm, ≤ 0.40 mm.**

7. **Add ≥2 vent holes through the front cover** (≥ **1.5 mm dia**) so trapped
   air against the cover ceiling escapes in the **front-up** orientation.
   **Location:** the hole must land over the *open cavity*, i.e. cover footprint
   at **Y ∈ [−17, +14.5]** and **X ∈ [−45, +45]** (not Y ∈ [14.5, 16], which is
   over the solid top wall — a hole there hits wall, not air). Bias toward the
   **+Y (finger-side) end of the cavity, around Y ≈ +12**, so it is the high
   point when fingers-up; place one near each side (e.g. X ≈ ±30) to cover roll.
   Keep clear of the 3 cover axle bosses (at A_R/B_R/B_L) and the snap-clip
   windows. Min 1.5 mm dia for bubble release and FDM horizontal-hole minimum.

8. **Material directive for all snap features:** PETG default; **do not** print
   any snap pin or clip in **TPU** (creeps, wallows the bore) or **PLA**
   (hydrolyzes wet). ASA or glass-filled nylon are acceptable stiffer
   alternatives if insertion strain is re-checked.

=== END CONSTRAINTS ===

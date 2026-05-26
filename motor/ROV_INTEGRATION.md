# ROV integration — mounting, cabling, connectors, trim

Integration plan for fitting the **all-polymer flooded gripper** (geared four-bar
+ Fin-Ray TPU fingers) to an ROV arm. Covers the six areas a competition/sponsor
judge needs to see: mounting, cable routing, connector selection, pressure
compensation scope, buoyancy trim, and the modularity interface specification
that is the campaign's core thesis.

> **Honesty.** This is an integration *plan* with stated assumptions; mass/trim
> numbers are engineering estimates (measured gripper values cited from
> `../UNDERWATER.md §4`). Connector depth ratings are vendor-catalogue figures,
> not bench-tested at this stage. The bench validation programme is `BENCH_TEST.md`.
> Cross-links: `../UNDERWATER.md`, `SELECTION.md`, `DRIVETRAIN.md`,
> `DECISION_LOG.md`. `ELECTRICAL.md` (the sibling power-bus detail doc) is a
> forward reference — it owns voltage rail, fusing, regulator, and tether ΔV
> budgets not repeated here.

---

## 1. Mounting — the bottom M4 flange

### 1a. Flange geometry

The gripper's only mechanical attachment to the ROV arm is the **bottom M4 flange**
cast into the `enclosure` below the shaft exit. The flange provides a planar mating
face around the `input_pinion_shaft` D-coupler exit (Ø10, 1.4 mm D-flat, 12 mm
engagement). The actuator bolts to the arm from below this plane; the gripper bolts
to the arm from above it. The two interfaces share the same bolt pattern.

**Recommended bolt pattern:** four M4 bolts on a ~40–50 mm bolt circle (confirm
from `gripper.py` flange geometry before drilling). Four bolts give symmetric
moment loading and allow the pattern to clear the drain holes in the bottom wall.

### 1b. Galvanic isolation (from `../UNDERWATER.md §5`)

The gripper is **100 % polymer — it contributes zero metal to the bolted joint.**
The only galvanic risk is external: M4 fasteners passing through the printed PETG
flange into the (typically aluminium or titanium) ROV arm create a stainless/
aluminium or titanium/stainless couple in seawater. Isolate per `../UNDERWATER.md §5`:

| Isolation element | Purpose | Notes |
|---|---|---|
| **Nylon or PTFE shoulder bushing** in each bolt hole | Prevents fastener shank contact with the arm's bore | Shoulder OD = M4 clearance hole dia; length = flange thickness |
| **PTFE or nylon flat washer** under bolt head / nut | Prevents fastener head bearing directly on arm metal | Must cover the counterbore, not just the shank |
| **PTFE or nylon washer** on the arm face | Isolates the gripper's flange face from the arm | Thin (0.5–1 mm) — does not affect alignment |

If the arm is polymer/composite, galvanic isolation is irrelevant but the bushings
still provide creep protection for the printed flange bores under sustained load.

### 1c. Fastener material and torque

| Scenario | Fastener choice | Torque | Rationale |
|---|---|---|---|
| Metal arm, isolated joint | **A4 / 316 stainless M4**, ≥30 mm length | **1.5–1.8 N·m** | Stainless isolated from arm metal by bushing/washers; strong enough for sustained load; seawater-compatible |
| Polymer arm, no isolation needed | **Nylon M4**, ≥30 mm | **0.8–1.0 N·m** | Low-modulus arm; nylon bolt gives matched compliance and zero corrosion |
| T3 / deep ROV (metal arm) | **A4-316 + isolation** as above + **thread-locking compound** (Loctite 243) | 1.5–1.8 N·m | Vibration from thrusters + cable pull can back off fasteners at depth over a long dive |

**Anti-vibration:** apply Loctite 243 (medium strength, serviceable) to the bolt
threads before installation. Do **not** use high-strength (Loctite 271) on a
printed polymer flange — it can attack PETG and makes removal destructive. Check
pre-dive.

### 1d. Actuator-to-flange clearance

The D-coupler exits directly below the flange face. The chosen actuator (XW540 or
adapter pod) must locate under the flange with the coupler engagement fully seated
before the bolt pattern clamps. Leave ≥ 2 mm axial clearance between the actuator
body and the flange face to accommodate print dimensional tolerance and avoid
clamp-induced shaft loads.

---

## 2. Cable routing and strain relief

### 2a. Cable from actuator to ROV

The actuator power + signal cable (RS-485, 4-conductor minimum; see §3) exits the
actuator body and runs along the ROV arm to the vehicle bulkhead. Three principles
govern routing in a flooded open-mesh assembly:

1. **Keep the cable out of the four-bar arc.** The drive arms sweep a roughly
   120°–140° cone above the flange. Route the cable along the arm's topside or
   underside (away from the sweep plane) and fix it with cable ties every ~30 mm
   before it reaches the moving region. Do not route between the arm and the
   follower links.
2. **Provide a service loop at the gripper.** Leave ≥ 1 × the gripper height
   (~60–80 mm estimate, confirm from model) of free cable as a service loop at
   the exit point, fixed with a strain-relief clip to the flange or arm bracket.
   The loop absorbs any cable-pull tension before it reaches the connector or the
   actuator's cable gland.
3. **Abrasion protection.** In the flooded mesh the cable is exposed to grit,
   coral, and arm contact. Sleeve the exposed run in **polyurethane spiral wrap
   or braided HDPE conduit**; avoid PVC in cold seawater (embrittles). For T3
   deeper work, sleeved-and-clamped (not just spiral-wrapped) is the baseline.

### 2b. Strain relief at the ROV bulkhead

The cable terminates at a bulkhead penetrator or a wet-mate connector on the ROV
body. At that point:

- **Minimum-bend-radius clamp:** the cable must not flex around its connector
  strain-relief adapter under thruster vibration or tether snagging. Use a
  commercial ROV cable clamp (e.g., Blue Robotics penetrator strain relief, or
  equivalent) rated for the cable OD.
- **Tie-off loop:** a P-clamp or cable tie 50–80 mm back from the connector takes
  the pull load; the connector itself sees zero tension.
- **Drip loop:** on the vehicle body, route the cable below the connector entry
  point so any water running down the cable drains away from the penetrator (even
  in a flooded scenario, salt deposition at the connector is a corrosion pathway).

### 2c. T2 canister routing note

For T2 (primary, ≤ 30 m), the XW540 body lives in a thin **pressure canister**
(see `SELECTION.md §"T2 sealing"`). The cable exits the canister via a rated
bulkhead penetrator. The strain-relief rules above apply at that penetrator exit
as well.

---

## 3. Connector choice — by depth tier

The RS-485 bus requires **≥ 4 conductors** (V+, GND, Data+, Data−) plus optional
shield. The XW540 at 12 V and ≤ 6 A stall dictates ≥ 0.5 mm² conductor cross-section
for a ≤ 3 m tether drop; derate for longer runs (defer to `ELECTRICAL.md`).

| Tier | Connector | Notes |
|---|---|---|
| **T1 ≤ 10 m** (bench/pool) | **DIY potted bulkhead** — JST-XH 4-pin or Molex Micro-Fit 4-pin, potted in Loctite E-30CL marine epoxy inside a small PVC bulkhead housing | Low-cost, repeatable, no specialist tooling. Depth limit ~10–15 m with good epoxy fill; adequate for T1. RS-485 twisted pair inside. |
| **T2 ≤ 30 m (PRIMARY)** | **Potted bulkhead (6-pin, ≥ M16 cable gland body)** OR **SubConn Micro Circular 6-pin** (wet-mateable, 600 m rated, ~USD 150/pair) OR **Blue Robotics WLP connector** (rated for BlueROV2 depths, ~USD 40, push-on, IP68 to ~100 m) | Potted bulkhead is the cost-effective T2 option; SubConn is the professional choice and allows underwater reconnection. Blue Robotics WLP is a pragmatic middle tier. Each provides ≥ 4 active pins + ground/shield. |
| **T3 > 30 m** (subsea/sponsor pitch) | **SubConn Micro Circular 6-pin wet-mate** (600 m) or **Macartney MCBH series** (up to 1000 m, rated wet-mateable) or **Cobalt subsea connectors** | Rated wet-mate connectors are mandatory at T3 — potted joints are not pressure-block-tested and can delaminate at sustained depth. Minimum specification: wet-mateable, ≥ 300 m rated, ≥ 4 pin, ≥ 0.5 mm² pins. |

> **Note on T2 + the canister:** the connector mates to the **canister bulkhead**,
> not the servo body directly. The XW540's own IP68 rating (= 1 m freshwater,
> per `SELECTION.md`) is the *backup* barrier; the canister and its connector
> are the primary T2 pressure boundary. Do not claim the bare IP68 servo body
> is depth-rated to 30 m.

> **RS-485 requirement:** the smart servo's RS-485 bus needs a twisted-pair
> Data+/Data− pair (preferably shielded); choose connectors with at least 4
> pins segregated for V+, GND, Data+, Data−. A 6-pin connector allows a spare
> pair or a dedicated shield return.

---

## 4. Pressure compensation — scope

**The flooded gripper itself requires no pressure compensation.** By design, the
enclosure floods completely: every internal void is vented (5+ bottom drains,
4 side drains, 4 snap windows, 2 top slots, journal bore clearances — verified
in `../UNDERWATER.md §3`). At any operating depth the cavity pressure equilibrates
to ambient; there is no enclosed air pocket under load, no differential pressure
across the walls (beyond the hydrostatic head on the ≤ 3 mm printed wall sections,
which is negligible at T2). **Pressure compensation hardware is N/A for the gripper.**

**It does apply to the actuator/pod:**

| Actuator config | Pressure compensation approach |
|---|---|
| **Primary T2 — actuator in thin canister** | Static O-ring sealed canister; no oil fill needed at ≤ 30 m if canister wall strength is adequate. **Recommended off-the-shelf assembly (Blue Robotics 3" locking series, ~USD 120 total):** [3" cast-acrylic tube, 240 mm, 150 m depth, USD 25, Part `BR-102649-240`](https://bluerobotics.com/store/watertight-enclosures/locking-series/wte-locking-tube-r1-vp/) + two [aluminium end caps, USD 34 each — blank `BR-100949-999` + 4×M10 penetrator-hole `BR-100949-004`](https://bluerobotics.com/store/watertight-enclosures/locking-series/wte-end-cap-vp/) + [WetLink cable penetrators](https://bluerobotics.com/store/cables-connectors/penetrators/wetlink-penetrator/) (~USD 13 ×2). Acrylic is rated for *short-term* submersions (< ~2 weeks per Blue Robotics) — for sustained deployment, swap to the same-series **aluminium tube** (1000 m rated, ~USD 100+). The same kit houses any servo in the ladder (XW540 / XM540 / STS3250 / STS3215); the longest body (XW540/XM540, ~117 mm) fits the 240 mm tube with room for the connector bend. |
| **T3 fallback — magnetic-coupling dry pod** | **Oil-fill + compensator required.** The pod motor is in a sealed dry cavity; at T3 depths the static-seal ΔP is prohibitive without compensation. Fill with silicone or mineral oil; add a flexible membrane/piston compensator to equalize pod pressure to ambient. Pod can then use standard motor seals (static O-rings only, no rotating shaft seal). This is the T3 fallback's depth-scaling advantage: pod re-rated by O-ring compound + oil grade, not by redesigning the rotating seal. See `SELECTION.md §"FALLBACK"` and `DECISION_LOG.md D8`. |

---

## 5. Buoyancy trim and COM/COG shift

### 5a. Gripper alone (measured from `../UNDERWATER.md §4`)

- Solid material volume: **98.5 cm³**
- Dry mass: **~124 g** (PETG + eSUN eTPU-95A, 100 % infill)
- Net buoyancy in seawater (ρ = 1.025 g/cm³): **+23 g** (sinks gently, near-neutral)

The gripper alone is correctly trimmed — no ballast required. It is slightly
negative, which is desirable for a manipulator end-effector (it sinks away from
the arm rather than floating into it on release).

### 5b. XW540 actuator contribution (estimate)

The XW540-T260 body is ~33 × 46 × 117 mm (from Robotis datasheet envelope,
including horn and cable exit). Approximate body volume estimate:
**~115–130 cm³** (treat as a rectangular block minus ~15 % for the internal
motor cavity voids that flood or stay gas-filled).

**Estimate (conservative — actuator assumed flooded at body voids):**

| Quantity | Value | Basis |
|---|---|---|
| XW540 mass in air | **~185 g** | Task-locked figure; validate by weighing |
| XW540 body volume | **~120 cm³** (estimate; assume floods partially) | Datasheet envelope; state as assumption |
| Buoyant force in seawater | 120 cm³ × 1.025 g/cm³ ≈ **123 g** | Archimedes |
| Net buoyancy, actuator | 185 − 123 = **+62 g (sinks)** | estimate |
| Gripper net buoyancy | +23 g (sinks) | `../UNDERWATER.md §4` |
| **System net (gripper + actuator)** | **+85 g (sinks)** | sum |

> **This is an estimate.** The XW540's internal void fraction (motor coil gap,
> gear cavities) is not documented; if those voids are sealed and hold gas, the
> buoyant force is smaller and the servo sinks more. If they flood (unlikely for
> a sealed IP68 body), buoyant force is larger. **Validate by displacement test
> in fresh water before dive.** The canister (T2) adds further negative buoyancy
> (aluminium shell ~100–150 g, small displaced volume); add it to the tally.

### 5c. COM shift

The actuator mounts directly below the flange, shifting the system centre of
mass **downward** (in the deployed, fingers-up orientation) relative to the
gripper-alone COM. This is beneficial for pitch stability (the heavy actuator
acts as a keel), but the ROV arm must account for the ~250–350 g end-effector
total mass in its torque budget.

### 5d. Trim method

| Correction needed | Method |
|---|---|
| Too negative (sinks too fast) | Add **syntactic foam blocks** cable-tied to the arm, upstream of the gripper. Do not add buoyancy to the gripper itself — it alters finger clearance and flood paths. |
| Too positive (floats) | Add **lead ballast disc** (M10 lead washer, ~20 g) between the flange and actuator bracket. Polymer-coat to isolate galvanically. |
| Roll bias (cable pull one side) | Adjust cable routing symmetry; add a small counterweight on the opposite side of the arm. |

Trim should be confirmed at the target depth tier with the full cable run attached
— cable mass and drag create a moment arm that changes with ROV attitude.

---

## 6. Modularity interface specification

The campaign thesis: **same gripper, same D-coupler — swapping the actuator (or arm,
or depth tier) is a connector swap and a printed adapter, not a redesign.** Every
explicit swap point is listed below with the interface spec and what a swap actually
requires.

| # | Swap point | Interface specification | What a swap requires |
|---|---|---|---|
| **A** | **D-coupler → actuator output** | Ø10 mm shaft, D-flat depth 1.4 mm, engagement 12 mm, axis vertical (exits housing bottom flange). Material: PA12-GF printed shaft. | Print a new **adapter horn** (actuator spline or round output → D-socket). Gripper geometry unchanged (`SHAFT_COUPLER_*` locked). Takes 1–2 h to design and print. Verified by `DECISION_LOG.md D9`. |
| **B** | **M4 flange → ROV arm** | Four M4 through-holes on the bottom flange (bolt circle TBD from `gripper.py`), flanged face perpendicular to shaft axis. Galvanic isolation: nylon/PTFE bushings + washers (§1b). | Print or machine a **mount adapter plate** that matches the arm's bolt pattern on one face and the gripper's M4 pattern on the other. The gripper is unchanged; the plate is arm-specific. One plate design per arm family. |
| **C** | **Power + signal → ROV** | RS-485, 4-conductor (V+, GND, Data+, Data−), 12 V nominal, ≤ 6 A peak (stall). Connector per depth tier: T1 potted JST/Molex; T2 potted bulkhead or SubConn Micro 6-pin; T3 SubConn or Macartney wet-mate (§3). | Swap connector at the canister/pod bulkhead and at the ROV penetrator. Bus protocol (RS-485) and voltage (12 V) are fixed across both primary servo variants (XW540, STS3215). Feetech STS3215 uses the same RS-485 protocol and voltage — **zero bus change on a budget↔flight swap.** |
| **D** | **Mount adapter plate → different ROV arm** | Any arm mounting pattern accommodated by printing a new adapter plate (§B above). Plate material: PETG minimum; ASA/PA-GF for structural arms. | Design and print a new plate. No change to the gripper body, flange, or actuator. Plate is the only arm-specific part. |
| **E** | **T3 magnetic-coupling fallback: barrier wall + pod interface** | The D-coupler region is replaced by a **magnetic inner-rotor** on `input_pinion_shaft` + a printed barrier wall + **outer rotor** + **dry pod** housing a smart servo or FOC BLDC. Pole-slip torque scales with coupling OD (≥ 60 mm recommended, cf. KTR MINEX-S SA 60/8 at 7 N·m). | This swap changes the coupler region of the gripper — it is a **numbered proposed option (`DECISION_LOG.md D8, D9-option 2`)**, not implemented. The gripper interior, fingers, four-bar, and M4 flange are unchanged. The dry pod re-mounts to the M4 flange via the same adapter-plate route (swap point B). |

> **Sensing continuity across swaps.** All primary-tier actuators (XW540, STS3215)
> and the T3 pod motor are smart-serial RS-485 units with native `present_current`
> telemetry. Force-sensing through the motor (`SENSING.md`) is therefore maintained
> across every swap point — no fingertip electronics, no wiring changes through the
> TPU fingers, no new underwater connectors at the gripper tip. That is the explicit
> tradeoff from `DECISION_LOG.md D5`: one aggregate force readout (no contact map),
> in exchange for zero fingertip underwater electronics.

---

## Pre-integration checklist

Before mounting the gripper to an ROV arm for a T2 dive:

- [ ] Confirm flange bolt circle geometry from `gripper.py` and drill/mill adapter plate.
- [ ] Fit nylon/PTFE shoulder bushings in every flange bolt hole; verify no metal-metal contact.
- [ ] Torque M4 fasteners to 1.5–1.8 N·m (A4-316) with Loctite 243; wait cure.
- [ ] Install actuator/canister from below; confirm D-coupler engagement ≥ 12 mm.
- [ ] Route and secure cable: service loop at gripper, sleeved run along arm, strain-relief at ROV bulkhead.
- [ ] Confirm cable clears the full four-bar + finger sweep arc by ≥ 20 mm.
- [ ] Install depth-appropriate connector (§3 table); verify RS-485 bus continuity end-to-end.
- [ ] Weigh and displacement-test full assembly (gripper + actuator + canister + partial cable); confirm net buoyancy within ±30 g of target.
- [ ] Trim as needed (foam/ballast, §5d) with cable attached and arm at operating attitude.
- [ ] Run full open↔close cycle on the surface; confirm telemetry and `present_current` readable at ≥ 50 Hz.
- [ ] Run pre-dive checklist from `../UNDERWATER.md` (snap pins, drain clear, cavity flood, cover clips).

---

Cross-links: `../UNDERWATER.md`, `SELECTION.md`, `DRIVETRAIN.md`, `SENSING.md`,
`DECISION_LOG.md`, `REQUIREMENTS.md`, `ELECTRICAL.md` (forward ref — power-bus
detail), `BENCH_TEST.md` (buoyancy + force calibration validation).

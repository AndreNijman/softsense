# ROV integration — mounting, cabling, connectors, trim

Integration plan for fitting the **all-polymer flooded gripper** (geared four-bar
+ Fin-Ray TPU fingers) to an ROV arm. Covers the six areas a competition/sponsor
judge needs to see: mounting, cable routing, connector selection, pressure
compensation scope, buoyancy trim, and the modularity interface specification
that is the campaign's core thesis.

> **Honesty.** This is an integration *plan* with stated assumptions; mass/trim
> numbers are engineering estimates (measured gripper values cited from
> `../docs/UNDERWATER.md §4`). Connector depth ratings are vendor-catalogue figures,
> not bench-tested at this stage. The bench validation programme is `BENCH_TEST.md`.
> Cross-links: `../docs/UNDERWATER.md`, `SELECTION.md`, `DRIVETRAIN.md`,
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

### 1b. Galvanic isolation (from `../docs/UNDERWATER.md §5`)

The gripper is **100 % polymer — it contributes zero metal to the bolted joint.**
The only galvanic risk is external: M4 fasteners passing through the printed PETG
flange into the (typically aluminium or titanium) ROV arm create a stainless/
aluminium or titanium/stainless couple in seawater. Isolate per `../docs/UNDERWATER.md §5`:

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

### 2d. Shaft exit from the canister — how the torque crosses the sealed wall

The actuator is **inside** the canister (§2c, BOM); its torque must reach the
gripper's input **D-coupler on the wet side**. There are exactly two architectures
for that crossing, and the campaign uses both depending on depth tier. Until now
this has been hand-waved as "in a canister" — this section closes that gap.

#### Option A — Dynamic radial shaft seal (the T1/T2 primary path)

A smooth shaft extends the servo's printed adapter horn (`SELECTION.md` D9-1) and
penetrates the canister end cap through a **radial lip seal**. The wet side of
the shaft carries the D-socket that mates the gripper's input D-coupler.

| Item | Part / spec | Source | Cost (~USD) |
|---|---|---|---|
| Radial lip seal, single-lip NBR (DIN 3760 Type A) | **SKF CR 8×14×4 HMS5** (shaft Ø8, OD 14, width 4 mm) | SKF / Trelleborg / Simrit / generic equivalents on McMaster, eBay, AliExpress | $3–6 |
| Higher-rated variant (Viton, dual-lip) | **SKF CR 8×14×6 HMSA7 V** | SKF | $8–15 |
| Sealed shaft, Ø8 mm × ~25 mm, **hard-anodised aluminium or 316 stainless** (smooth Ra ≤ 0.8 µm in the seal-contact band) | Machined locally, or print PA12-GF + polish — but PA12-GF wears under the lip over O(10³) cycles | Local fab / SendCutSend / 3D print | $2–10 |
| Seal seat in the canister end cap | Bore Ø14 H7, depth ≥ 6 mm, **centred** on the wet-side end cap. Start from the **blank** Blue Robotics end cap **`BR-100949-999`** (= no factory holes, the SKU's name — *not* blank in the finished assembly) and drill + ream a single Ø14 H7 bore for the lip seal — light press-fit, no adhesive. Avoids the "enlarge an M10 hole + plug the other three" alternative, which leaves unused penetrator holes to seal. | DIY mod on the blank cap | — |

**Parasitic torque (closed-form bound):**
`T_seal ≈ μ · F_n · d/2`, where the lip's normal force `F_n` combines garter-spring preload (~5 N circumferential) and pressure-induced loading `F_p ≈ P · π · d · b_lip`. For NBR (μ ≈ 0.15), Ø8 mm shaft, b_lip ≈ 0.5 mm:

| Tier | ΔP | F_p (N) | F_n total (N) | **T_seal (mN·m)** | % of T_safe shipped (0.034) | % of T_safe re-size (0.40) |
|---|---|---|---|---|---|---|
| T1 (1 bar) | 0.1 MPa | 1.3 | ~6 | **~3.6** | ~11 % | ~0.9 % |
| **T2 (3 bar)** | 0.3 MPa | 3.8 | ~9 | **~5.4** | **~16 %** | **~1.4 %** |
| T3 (10 bar) | 1.0 MPa | 12.6 | ~18 | **~10.8** | ~32 % | ~2.7 % |

Static breakaway is ~2–3× running, ~10–30 mN·m worst case. **Negligible vs the
gear ceiling at T1/T2; non-negligible at T3** — and it is what motivates the
switch to Option B at depth. (Bench-measure the actual seal torque against the
load cell during `BENCH_TEST.md §2 calibration` to anchor this estimate.)

**Failure modes:**
- **Lip wear** over O(10⁴–10⁵) cycles → leakage past the lip. Inspect annually
  for grit-cut grooves in the shaft and lip flattening.
- **Pressure-induced lip lift-off** at ΔP ≥ ~5–10 bar (single-lip NBR's edge of
  envelope). Mitigation at T3: dual-lip (HMSA7) or step to Option B.
- **Particulate scoring** of the shaft (sand, biofilm). Mitigation: post-dive
  fresh-water rinse (`../docs/UNDERWATER.md §"Post-dive checklist"`).
- **Soft-shaft groove-out** if the shaft surface is printed PETG/PA12-GF rather
  than hard metal — the lip eats a circumferential groove and leaks within O(10³)
  cycles. **Use anodised aluminium or 316 stainless for any sustained service.**
- **Detection in service:** pre-dive, hand-spin the shaft — it should turn with
  only the parasitic torque (~5 mN·m at T2). If gritty/stiff, replace the seal;
  if free-spinning with axial play, the seal has worn out. Telemetry catches it
  too: a sudden drop in `present_current` at the previous force setpoint, or
  servo over-temperature, indicates lost lip contact or water ingress.

#### Option B — Magnetic coupling (the T3 fallback; no shaft penetrates the wall)

An **inner rotor** (permanent-magnet disc) on the servo horn inside the canister
couples magnetically through a thin non-ferromagnetic barrier (the end cap, or a
custom printed end cap) to an **outer rotor** on the wet side, which drives the
D-coupler. No shaft pierces the seal.

| Item | Part / spec | Source | Cost (~USD) |
|---|---|---|---|
| Coaxial PM coupling, TK_max **7 N·m**, Ø80 OD | **KTR MINEX-S SA 60/8** (well above 1.5× XW540 stall 9.5 N·m? — see note below) | [KTR product page](https://www.ktr.com/us/en/products/minex-s-magnetic-couplings-with-containment-shroud/) (quote) | $600–800 |
| Smaller, TK_max **3 N·m**, Ø69 OD | KTR MINEX-S SA 46/6 (matches STS3250 stall but marginal for XW540 stall) | KTR (quote) | $300–500 |
| DIY N52 puck ring, ~6 N·m, Ø80, 6 mm gap | 10 × N52 5×10×15 mm pucks on a printed PETG/PA12-GF rotor (per the Pettersen DPV builder pattern, `SURVEY.md` Class 6 ref [21]) | AliExpress / KJ Magnetics + 3D print | $15–50 |
| Outer-rotor bearing | Stainless **608ZZ** (8 mm bore, $2) or printed PTFE bushing for short-life | McMaster / generic | $2–15 |
| Non-conductive thin barrier (replaces aluminium end cap on the coupling end) | Printed PETG or PA12-GF end cap, **2–4 mm wall**; or machined PEEK if T3 sustained | DIY print | $1–20 |

**Parasitic torque:** effectively zero in operation. Magnetic coupling itself is
near-lossless; mechanical losses come from (a) the outer-rotor bearing
(608ZZ ≈ **0.5 mN·m running**) and (b) eddy-current losses if the barrier is
conductive — aluminium end cap at ~30 rpm produces ≤ **~1 mN·m** of eddy drag
(scales with ω², so it stays small at gripper speeds). Plastic barriers
eliminate (b) entirely. **Total ≤ ~1.5 mN·m, i.e. < 5 % of T_safe shipped, < 0.5 % of T_safe re-size — and crucially does not grow with pressure.**

**Failure modes:**
- **Pole-slip** when transmitted torque exceeds the coupling's `TK_max` — the
  rotors decouple instantly and re-sync at the next pole pair. **This is a
  feature** (built-in overload clutch — protects gripper teeth AND specimen) AND
  a hazard if the coupling is undersized. *Sizing rule:* `TK_max ≥ 1.5 × servo
  stall` (XW540 stall 9.5 N·m → ≥ 14 N·m needed; STS3250 stall 4.9 N·m → ≥ 7 N·m).
  At our scale **the SA 60/8 (7 N·m) is sufficient *only* for the STS3250 + STS3215
  tier; the XW540/XM540 needs the next size up (SA 80/10 ≈ 14 N·m) or the 80 mm
  N52 DIY ring (~6 N·m) under a strict firmware current cap.** This is also why
  the magnetic fallback already pairs naturally with a **smaller motor in the dry
  pod** (`SELECTION.md` D8 — the pod motor can be a cheap non-IP unit; oversizing
  is unnecessary because the pole-slip caps it anyway).
- **Alignment:** the outer rotor must remain coaxial within ~0.2 mm of the inner.
  Misalignment widens the magnetic gap and drops `TK_max` quadratically.
  Mitigation: a printed concentric bearing housing referenced off the canister
  end-cap face.
- **Magnetic gap (= barrier thickness):** Blue Robotics' stock aluminium end cap
  is ~10–15 mm thick — too thick for small couplings at full TK_max. For Option B,
  swap to a **thinner custom end cap (3–5 mm printed PETG/PA12-GF)**; at T3 this
  is the structural design item (acrylic creeps at 10 bar — use PEEK or
  glass-filled nylon).
- **Demagnetisation** above ~80 °C for N52. Underwater is cold — non-issue.
- **Detection in service:** pole-slip is audible (a "tick") and immediately
  obvious in telemetry — the servo `present_position` advances while the
  fingertip force-derivative goes to zero. A slip during a grasp drops the
  object; safety-equivalent to the back-drivable Option A under power loss
  (`FAILURE_MODES.md` M3, M4).

#### Choice per depth tier

| Tier | Recommended | Why |
|---|---|---|
| **T1 (≤ 10 m) — bench, pool, shallow** | **Option A — lip seal** | Cheapest; parasitic ~3.6 mN·m (11 % of T_safe shipped); single-lip NBR lasts O(10⁴) dives at 1 bar. Magnetic is overkill. |
| **T2 (≤ 30 m) — PRIMARY** | **Option A — lip seal** | At 3 bar, single-lip NBR is well within rating; parasitic ~5.4 mN·m (~1.4 % of T_safe re-size); $5 replacement; integrates with the off-the-shelf BR-100949-004 end cap via one drilled bore. **This is the canonical primary architecture and now spelled out.** |
| **T3 (> 30 m) — fallback / subsea narrative** | **Option B — magnetic coupling** | At ≥ 10 bar, lip-seal cogging + lift-off risk rise (~32 % of T_safe shipped, with non-linear growth); magnetic coupling removes the wear part entirely and pressure-decouples the parasitic torque. Same drivetrain otherwise — only the end-cap region changes (`SELECTION.md` D8, `DECISION_LOG.md` D9-option 2). |

Both architectures share the **same gripper, same D-coupler, same actuator
firmware, same sensing pivot, same canister tube** (BR-102649-240). Only the
end-cap (drilled lip-seal bore for A; thin non-conductive wall + outer rotor for B)
changes. This is the explicit, judge-defensible answer to *"how does the torque
get out of the sealed canister?"* — and the parasitic-torque table shows quantitatively
why the choice flips at depth, not just qualitatively.

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
in `../docs/UNDERWATER.md §3`). At any operating depth the cavity pressure equilibrates
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

### 5a. Gripper alone (measured from `../docs/UNDERWATER.md §4`)

- Solid material volume: **98.5 cm³**
- Dry mass: **~124 g** (PETG + Bambu TPU 95A HF, 100 % infill)
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
| Gripper net buoyancy | +23 g (sinks) | `../docs/UNDERWATER.md §4` |
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
- [ ] Run pre-dive checklist from `../docs/UNDERWATER.md` (pivot pins + melt caps, drain clear, cavity flood, cover clips).

---

Cross-links: `../docs/UNDERWATER.md`, `SELECTION.md`, `DRIVETRAIN.md`, `SENSING.md`,
`DECISION_LOG.md`, `REQUIREMENTS.md`, `ELECTRICAL.md` (forward ref — power-bus
detail), `BENCH_TEST.md` (buoyancy + force calibration validation).

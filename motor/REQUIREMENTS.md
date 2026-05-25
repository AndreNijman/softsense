# Actuator requirements — derived from the gripper kinematics

What the user-supplied waterproof actuator must deliver at the bottom
**D-coupler** of `input_pinion_shaft`, derived from the *live* `gripper.py`
mechanism (not assumed). Torque / speed / stall / holding are given as a single
**band** (they barely move with depth); the **IP / seal / connector / voltage /
material** requirements are split into three depth tiers.

> **Primary design point: tier 2 — shallow seawater, ≤ 30 m.** Tiers 1 (≤ 10 m)
> and 3 (> 30 m) are carried through as sensitivity edges so the Phase-3 scoring
> visibly flips actuator class with depth. The mechanism is unchanged across
> tiers — the same D-coupler accepts a different actuator class per depth. That
> *is* the modular-product argument.

> **Honesty (carried from `grip/GRIP_MODEL.md`):** this is a **mechanics-based
> sizing**, not a calibrated absolute-newton prediction of the built tool. The
> torque↔force relation is exact kinematics from `gripper.py`; the **efficiency
> is an estimate band**, and the target clamp force is **anchored** on the
> finger-FEA report level, not measured on hardware. Numbers size and rank the
> actuator field; they are not a guarantee of grams-force at the fingertip. The
> bench-test plan (`BENCH_TEST.md`) is where absolute force gets measured.

> **Sensing pivot (campaign update).** The actuator is now also the gripper's
> **force sensor** — motor current → torque → drivetrain back-trace → tip force,
> the same principle used by force-controlled industrial/surgical grippers
> (Maxon, Robotiq, Schunk). This adds a **hard selection filter**: a candidate
> must stream torque/current telemetry fast and fine enough to resolve a
> sub-slip grip-force step (§8 below). It also removes the old conductive-foam
> fingertip sensor (zero fingertip electronics underwater — see `DECISION_LOG.md`).
> Sensed force is itself a **relative** signal unless calibrated against a load
> cell (`SENSING.md`), so the rank-only caveat carries over to the force readout.

All numbers below are reproduced by:

```bash
/home/andre/.cad-venv/bin/python motor/scripts/kinematics_chain.py
# -> prints the tables + writes motor/iterations/_requirements.json
```

---

## 1. The drive chain (read from `gripper.py`)

```
  ACTUATOR  ── D-coupler (Ø10, D-flat 1.4 mm, 12 mm engagement)
     │
     │  crown/pinion right-angle stage     i_g = CROWN_TEETH/PINION_TEETH = 24/9 = 2.667:1  (reduction)
     ▼
  LEFT sector gear  (crank A_L)
     │  spur mesh 1:1 to RIGHT sector gear (R_GEAR = 12 mm both)
     ▼            └─ so the LEFT gear carries BOTH fingers
  four-bar  (A→C crank 34, B→D follower 32, C→D coupler 20)  ×2, mirrored
     ▼
  fingertip / contact-face clamp force  F  (per finger)
```

**Quasi-static torque balance** (lossless, then de-rated by efficiency `η`):

- left-gear torque `T_L = T_motor · i_g`
- the 1:1 mesh makes the left gear drive both fingers → `T_L = 2 · T_finger`
- four-bar virtual work at a finger contact point P:
  `F · dx_P = T_finger · dθ_crank` → `MA(P) = F/T_finger = |dθ_crank/dx_P|`

$$\boxed{\,F = T_{motor}\cdot \tfrac{i_g}{2}\cdot MA(P)\cdot \eta \qquad\Rightarrow\qquad T_{motor} = \frac{F}{\tfrac{i_g}{2}\, MA(P)\, \eta}\,}$$

`MA(P)` is the four-bar Jacobian at point P, evaluated numerically on the live
solver. It is **largest near the finger base** (short moment arm) and
**smallest at the tip** — so the tip is the *sizing-conservative* point and the
contact-face centre is the *practical-use* point.

| Point on finger (clamp pose, open = 0) | MA `\|dθ/dx\|` (1/mm) |
|---|---|
| base of grip texture (0.15·L) | 0.0277 |
| **contact-face centre (0.55·L) — practical** | **0.0230** |
| tip of grip texture (0.95·L) | 0.0196 |
| blade tip, centreline (1.0·L) — **conservative** | **0.0192** |

---

## 2. Torque requirement (the binding constraint)

**Target clamp force band: 8 – 15 N per finger**, anchored on the **12 N**
"force-targeted reporting" level from the finger FEA (`fea/UNIVERSAL_FINGER.md`).
That 12 N is the *common basis chosen to compare finger designs fairly* — not a
physically-mandated load — and the FEA showed the finger carries it with ~10×
von-Mises margin, so it sits well inside structural capacity. 8 N is a soft/
slippery-object floor; 15 N is a firm-grip ceiling that still keeps the finger
and printed gears in their safe band (see `DRIVETRAIN.md` gear recheck).

**Efficiency envelope** (estimate — printed, flooded, largely unlubricated):

| Stage | η range | basis |
|---|---|---|
| crown/pinion right-angle mesh | 0.65 – 0.85 | printed straight-flank face mesh, dry/flooded |
| spur 1:1 mesh | 0.85 – 0.95 | printed spur, plastic-on-plastic |
| four-bar (2 loaded journal pivots/finger) | 0.80 – 0.90 | flooded plastic journals |
| input-shaft journals (×2) | 0.90 – 0.97 | flooded plastic plain bearings |
| **total** | **0.40 – 0.71** | product of stage bands |

**Required input-shaft torque** (mid-face/high-η best case … tip/low-η worst case):

| Clamp force / finger | Required input torque (N·m) | ideal @ tip (η=1) |
|---|---|---|
| 8 N | 0.37 … 0.78 | 0.31 |
| **12 N (FEA anchor)** | **0.56 … 1.18** | 0.47 |
| 15 N | 0.70 … 1.47 | 0.59 |

### Spec

| Quantity | Value | Rationale |
|---|---|---|
| **Continuous torque (target)** | **≥ 1.2 N·m** at the D-coupler | covers the worst case (tip, 12 N, η = 0.40) with margin; reaches 15 N at favourable contact points |
| Continuous torque (floor) | ≥ 0.6 N·m | below this, 12 N is unreachable even at the practical mid-face point |
| Continuous torque (desirable) | ≥ 1.5 N·m | headroom for 15 N at any contact point + the low-η edge |

These barely change with depth, so they are **one band across all three tiers**.

---

## 3. Speed & travel — *not* a binding constraint

A full open↔close is **only 122.7° of input rotation** (crank sweep 46° ×
i_g 2.667). So:

| Full-stroke time | Required input speed |
|---|---|
| 2.0 s (gentle) | 10.2 rpm (61°/s) |
| 1.0 s (nominal) | 20.4 rpm (123°/s) |
| 0.5 s (fast) | 40.9 rpm (245°/s) |

**Spec: ≥ ~20 rpm (≈ 123°/s) at the input, full travel ≤ ~123°.** Two
consequences that *shape the survey*:

1. The speed is trivial — any RC servo (60° in 0.1–0.2 s ⇒ 300–600°/s) clears
   it by ~3–5×, and even geared DC/stepper options reach it easily.
2. **A limited-rotation actuator is sufficient** — no continuous rotation is
   needed. This makes the **limited-arc waterproof hobby-servo class the natural
   primary** and lets *continuous-rotation drives be ruled out as overkill*
   (they'd need a position sensor + endstop logic the servo already has).

---

## 4. Stall & holding

- **Stall torque:** must exceed the continuous target (≥ 1.2 N·m) so grip can
  build without the actuator stalling short — but it must **not** be so high
  that an uncontrolled stall over-drives the fingers/printed gears. Target stall
  **1.5–3× continuous (≈ 1.8–3.6 N·m) with electronic torque/current limiting**
  to cap grip force. The compliant Fin-Ray finger and the geometric-capture
  joints tolerate modest overshoot, but force should still be *commanded*, not
  left to slam to stall (see `FAILURE_MODES.md`).
- **Holding:** the drivetrain ratio is low (2.667:1) and the four-bar has a
  healthy transmission angle, so the chain is expected to be **back-drivable** —
  the grip reaction pushes back to the input. Therefore the actuator must
  **hold position under the full grip reaction continuously** (a positional
  servo does this natively; a stepper holds with energised current; a brushed/
  BLDC needs a closed loop or a self-locking element). Holding torque ≈ working
  torque (0.6 – 1.2 N·m), continuous. *Back-drivability is confirmed numerically
  in Phase 5 (`holding_stall.py`).*
- **Duty:** grip-and-hold is intermittent in actuation but the **hold can be
  sustained for minutes** → the holding actuator's thermal duty (continuous
  stall-near current) is a real selection factor, analysed in
  `holding_stall.py` / `MOTOR_MODEL.md`.

---

## 5. Mechanical interface — the D-coupler (modularity boundary)

The actuator output must mate the existing coupler on `input_pinion_shaft`
(or be re-coupled — that re-coupling is the explicit modularity swap point):

| Coupler feature | Value (`gripper.py`) |
|---|---|
| Coupler radius `SHAFT_COUPLER_R` | 5.0 mm (Ø10) |
| D-flat depth `SHAFT_DFLAT` | 1.4 mm |
| Engagement length `SHAFT_COUPLER_LEN` | 12.0 mm |
| Axis | vertical, exits the housing bottom flange (world −Z) |
| Running env | flooded; printed PA12-GF shaft turns wet in two journal bores |

If a selected actuator's native output cannot drive this D-profile, the change
is proposed as a **numbered option in `DECISION_LOG.md`** and the gripper-side
coupler is *not* silently rewritten (per campaign rule). A printed adapter horn
that bridges actuator-spline → D-socket keeps the gripper untouched.

---

## 6. IP / seal / connector / voltage / material — by depth tier

Torque/speed/stall/holding above are constant; **these** are what move with
depth. Tier 2 is the primary design point.

| Aspect | Tier 1 — ≤ 10 m (bench / pool) | **Tier 2 — ≤ 30 m (PRIMARY)** | Tier 3 — > 30 m (subsea) |
|---|---|---|---|
| **IP / seal strategy** | IP68 hobby servo *or* epoxy-potted servo; static/grease-packed output OK | **Genuine IP68 submersible servo, or sealed body with a dynamic rotary shaft seal, or oil-filled servo** | Oil-filled / pressure-compensated actuator, or **magnetic coupling (no shaft penetration)** |
| **Shaft-seal type** | static / low-ΔP, grease | dynamic rotary lip/O-ring rated ≥ 3 bar (~30 m) | pressure-compensated (ΔP ≈ 0) or non-contact magnetic |
| **Connector class** | splash / IP67 (potted JST, Molex) | **wet-mateable or potted bulkhead ≥ 30 m** (SubConn micro / BlueTrail / DIY potted) | subsea wet-mate + pressure block (SubConn / Birns) |
| **Voltage budget** | 12 V (small-ROV 3S–4S battery) | **12 V nominal; 24 V acceptable**, tether ΔV budgeted | 24–48 V (lower current ⇒ less ΔV on a long tether) |
| **Housing / seal material** | PETG + nitrile O-ring | **ASA/PA-GF body; EPDM/nitrile seals; PTFE shaft seal** | PA-GF/POM + compensation oil (silicone/mineral); metal where ΔP demands |

---

## 7. ROV power-bus assumptions (stated, refined in `ELECTRICAL.md`)

- **Bus voltage: 12 V nominal** (BlueROV-class small-ROV convention) at the
  gripper, with **24 V** carried as a tier-3 option. The actuator must run from
  the available bus or via a dedicated regulator.
- **Peak current is the STALL current, not the run current.** Waterproof hobby
  servos stall at ~5–10× their continuous draw, so a 1.2–2 N·m-class servo at
  12 V can pull **~3–6 A on stall**. Budget the bus + fuse + tether conductor
  for the **stall**, not the average — otherwise the bus browns out the first
  time the gripper hits a hard object. Working budget: **≤ 6 A peak at 12 V** at
  the gripper, fused ~7.5–10 A, with inrush allowed for.
- **Signal:** a single PWM line (servo) is the baseline; CAN/UART/RS-485 are
  evaluated for sealed BLDC/stepper options in `ELECTRICAL.md`.

---

## 8. Force sensing through the actuator (the SoftSense pivot)

The actuator doubles as the grip-force sensor. The forward chain is the inverse
of §1: a measured motor current/torque telemetry sample is back-traced through
the same drivetrain to an estimated per-finger tip force:

$$\hat{F} = T_{sense}\cdot \tfrac{i_g}{2}\cdot MA(P)\cdot \eta \qquad\text{with}\qquad T_{sense}=K_t\,(I_{meas}-I_0)$$

(`SENSING.md` develops the forward + inverse models and the calibration; `MOTOR_MODEL.md`
carries the validation.) The selection-relevant budgets:

| # | Sensing requirement | Target | Basis |
|---|---|---|---|
| S1 | **Force resolution** (min detectable tip-force step) | **≤ 0.3 N** at the fingertip | ≈ 3 % of a 10 N working grip / 2 % of the 15 N ceiling (the FEA-anchored band). `grip_model.py` ranks textures' *relative* slip ordering — it is rank-only, so the **absolute** step target comes from the force band, not from absolute newtons it doesn't claim. |
| S2 | **Torque resolution at the input shaft** | **≈ 0.02 N·m** | S1 back-traced: 0.3 N ÷ (i_g/2 · MA_mid · η) at η≈0.5, MA_mid 0.023. Per-motor this is a current step ΔI = 0.02/K_t (evaluated per candidate in `SURVEY.md`). |
| S3 | **Telemetry rate** | **≥ 50 Hz** (desirable ≥ 100 Hz) | slip onset is detected on the force *derivative*; 50 Hz ⇒ 20 ms sampling resolves the contact/slip transient. |
| S4 | **End-to-end latency** (sense → controller → ROV topside) | **≤ ~50 ms** | usable closed-loop / operator grip control. Budget: ≤ 10 ms motor-side sense+filter, ≥ 40 ms for tether + parsing. |
| S5 | **Noise floor** | post-filter torque-sense noise < S2 (≈ 0.02 N·m RMS) | so the 0.3 N step is not buried. Brushed-DC commutation/PWM ripple (~5 %) exceeds this raw → needs filtering, which spends part of the S4 latency budget. |

**What this rules in and out** (full detail + citations in `SURVEY.md`):

- **In (native telemetry):** smart serial-bus servos expose `present_current`
  (Dynamixel X 2.69 mA/unit ⇒ ~0.005 N·m at the servo; Feetech 6.5 mA/unit) and
  FOC controllers expose `iq`/`torque` (moteus int32 ⇒ 1 mA / 1 mN·m). Both clear
  S1–S3 with margin and, crucially, **hold a clean torque estimate at stall** —
  the grip-and-hold state.
- **Out (no telemetry):** open-loop PWM servos (most IP-rated RC servos: Savox SW,
  Hitec WP, Traxxas) have **no current readback** → they cannot sense and are
  **DEAD** for this design, kept in `SURVEY.md` only with a one-line elimination.
- **Fallback-only:** sensorless BLDC back-EMF estimators go **blind below ~10–20 %
  rated speed** — i.e. at stall, exactly when grip force matters — so they are
  contact/stall *detection* only, never the primary force readout.
- **Ground truth:** a bench load cell (`SENSING.md`/`BENCH_TEST.md`) calibrates
  the current→force curve; an *in-situ* strain gauge is **not** re-introduced
  (it would put wiring back through the TPU — the very thing the foam removal
  avoided).

## 9. Requirement summary (the card the survey scores against)

| # | Requirement | Value |
|---|---|---|
| R1 | Continuous input torque | **≥ 1.2 N·m** (floor 0.6, desirable 1.5) |
| R2 | Stall torque | 1.8 – 3.6 N·m, with torque/current limiting |
| R3 | Input speed | ≥ ~20 rpm (123°/s); full stroke 0.5–2 s |
| R4 | Travel | limited rotation OK, full stroke ≤ ~123° |
| R5 | Holding | hold working torque continuously (back-drivable chain) |
| R6 | Interface | drive the Ø10 / 1.4 mm D-flat / 12 mm coupler (or adapter) |
| R7 | IP / depth | tier-2 ≤ 30 m primary; tiers 1 & 3 as edges (table §6) |
| R8 | Power | 12 V nominal; budget ~6 A peak (stall); single-PWM baseline |
| R9 | Material/seawater | hydrolysis-stable, galvanic-isolated at the M4 flange (`UNDERWATER.md`) |
| **R10** | **Force sensing via the actuator** | **stream torque/current telemetry: ≥ 0.3 N tip resolution (≈ 0.02 N·m input), ≥ 50 Hz, ≤ 50 ms latency (S1–S5)** |

`SURVEY.md` scores every candidate against R1–R10, tags which depth tiers (R7)
it satisfies, and adds the four sensing columns (modality / rate / protocol /
force-resolution); candidates that cannot sense (R10) are kept but tagged DEAD.
`SELECTION.md` weights them — **sensing fidelity is now a primary weighted axis
alongside torque, depth-tier fit and modularity** — and sweeps the weights ±50 %
(including depth tier) to pick a tier-2 primary + a fallback.

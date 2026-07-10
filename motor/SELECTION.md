# Actuator selection — primary + fallback

Weighted multi-criteria choice from the `SURVEY.md` shortlist, scored against
`REQUIREMENTS.md` R1–R10, with a **±50 % weight sensitivity sweep run across all
three depth tiers**. The full blow-by-blow is in `DECISION_LOG.md`.

> **Honesty.** The per-criterion scores (0–1) are engineering judgements read off
> `SURVEY.md`'s sourced data — not measurements. The sweep's job is not false
> precision; it is to show **which assumption flips the choice**, the same
> discipline as `grip/scripts/sensitivity.py`. Reproduce:
> `python motor/scripts/selection_score.py` → `motor/iterations/_selection.json`.

## Weights (stated)

| Criterion | Weight | What it captures |
|---|---|---|
| sensing | 0.25 | R10 force-telemetry fidelity — **the pivot → primary axis** |
| depth_fit | 0.20 | R7 fit to the active depth tier (the only tier-dependent score) |
| torque | 0.15 | R1 meets ≥ 1.2 N·m continuous + the stall band |
| modularity | 0.15 | drop-in at the D-coupler; one part/bus; same drivetrain across depths |
| integration | 0.10 | electrical/build simplicity (one wire vs FOC + CAN + a housing you design) |
| holding_thermal | 0.07 | hold-power + heat inside a sealed/flooded enclosure |
| cost | 0.08 | AUD |

## Result — the actuator class flips with depth (the modular-product thesis)

| Rank | **T1 ≤ 10 m** | **T2 ≤ 30 m (PRIMARY)** | **T3 > 30 m** |
|---|---|---|---|
| 1 | **XW540 smart serial 0.844** | **XW540 smart serial 0.795** | **magnetic pod 0.783** |
| 2 | **Feetech STS3250 0.790** | magnetic pod 0.774 | FOC BLDC 0.726 |
| 3 | Feetech STS3215 0.767 | **Feetech STS3250 0.726** | XW540 smart serial 0.725 |
| 4 | magnetic pod 0.754 | FOC BLDC 0.714 | **Feetech STS3250 0.664** |
| 5 | JMC stepper 0.713 | Feetech STS3215 0.697 | Feetech STS3215 0.637 |
| 6 | FOC BLDC 0.710 | JMC stepper 0.693 | JMC stepper 0.623 |
| 7 | worm-DC 0.657 | worm-DC 0.637 | worm-DC 0.567 |

The **STS3250 lands as the natural deep-budget peer of the rock-bottom STS3215** —
same SCS bus, same load-feedback model, but with continuous torque ~2.45 N·m
(sustained, post torque-protection) clearing the 1.2 N·m design floor that the
STS3215 doesn't. It ranks #2 at T1, #3 at T2 (top of the canister-only tier
behind XW540 and the magnetic pod), and #4 at T3. Adding it does **not flip**
any tier's winner or change the sensitivity envelope (still 14/14 → 13/14 → 13/14).

**Sensitivity:** the **smart serial servo is the robust T1 + T2 winner** — #1 in
14/14 (T1) and 13/14 (T2) of the ±50 % weight perturbations. At T2 it yields to
the magnetic pod *only* when the integration weight is halved (i.e. if you stop
valuing build simplicity). At **T3 the magnetic-coupling pod wins** (13/14),
flipping back to the smart servo only if depth_fit is de-weighted. This is the
quantified statement of the modular thesis: **same gripper, same D-coupler — the
optimal actuator class shifts from smart-serial-servo (shallow) to
magnetic-coupling (deep) as depth matters more.**

## The pick

### PRIMARY (tier 2): smart serial-bus servo — **DYNAMIXEL XW540-T260**

The only architecture that delivers **position *and* force on a single bus** with
no external sensor, no separate driver, and a **clean torque estimate held at
stall** — the literal embodiment of the motor-current force-sensing pivot (the
Robotiq principle). It is IP68 (body) and clears the ≥ 1.2 N·m continuous floor
(≈ 1.9 N·m); its 9.5 N·m stall is **far above the drivetrain's safe torque**, so it
must be current-limited (§Forward, `DRIVETRAIN.md`). `present_current` at 2.69 mA/unit
resolves ≈ 0.005 N·m at the servo (S2 with margin) at ~100–200 Hz over RS-485
(S3) — R10 satisfied outright.

- **Budget build within the same class & interface — a two-step ladder:**
  - **Deep-budget (~AUD 110): Feetech STS3250 (C002)** — 50 kg·cm / **4.9 N·m
    stall** @ 12 V (sustained ~2.45 N·m after the firmware torque-protection
    engages, still well above the 1.2 N·m design floor that the STS3215 cannot
    meet). Same SCS TTL half-duplex bus as the STS3215, same `load / position /
    voltage / temperature` feedback model; load % is the torque proxy (calibrated
    identically to Dynamixel `present_current` per `SENSING.md`). K_t ≈ 1.17 N·m/A
    (= 4.9 / 4.2 stall A), stall current 4.2 A @ 12 V — a wider bus budget than
    the STS3215 (`ELECTRICAL.md` §3). The recommended affordable build.
  - **Rock-bottom (~AUD 34–44): Feetech STS3215 (C018)** — 30 kg·cm / 2.94 N·m
    stall, ~0.98 N·m continuous (marginal vs the 1.2 N·m target but covers the
    practical mid-face grip ≈ 0.7–0.8 N·m for 12 N at η ≈ 0.5–0.55, and clears
    the 0.6 N·m floor). For pure bench/T1 dev where the STS3250 is overkill.
  - **Flight (~AUD 1,925): XW540-T260-R** for the no-compromise T2 build.

  All three share the same control model — bus daisy-chain + commanded current
  limit + load-cell-calibrated force readout. **One decision, three price
  points** (with the STS3250 as the new recommended middle), not three designs.
- **T2 sealing:** even the XW540's IP68 is only 1 m freshwater, so T2 (~3.1 bar
  seawater) still uses a thin pressure canister; the IP68 body is the backup seal
  and corrosion barrier. This is the one place the "stock-waterproof" servo still
  needs a housing — stated plainly.

### FALLBACK (tier 3): magnetic-coupling drive with a smart-servo/FOC dry pod

Chosen as the **tier-3 subsea-pitch** fallback (not a tier-1 cheap one — the
cheap path is already covered by the **STS3250 + STS3215 budget ladder** *inside*
the primary class). It wins
T3 outright and is the #2 at T2, so it is a real fallback, not a strawman. Its
case: **no rotating shaft penetrates the pressure boundary**, so depth is set by
the dry pod's *static* O-rings alone — the same drivetrain scales from pool to
real subsea with only the pod re-rated. Force sensing is **inherited from the pod
motor** (put a smart serial servo or FOC BLDC in the pod → full telemetry, and it
never gets wet so it needn't be waterproof). Pole-slip torque doubles as a
built-in **overload clutch / grip-force limiter** (protects gripper + specimen),
at the cost of capping the *senseable* force at the slip torque. It keeps the
subsea-sponsor (Fugro/Woodside) narrative intact and showcases the modular thesis.

## Why the others lost (one-line eliminations)

- **All IP-rated PWM servos (incl. Blue Trail Eng. 200–400 m):** no current
  telemetry → fail R10. The best-*sealed* option is killed by the sensing pivot.
- **Potted/oil-fill DIY (PWM base):** DEAD on sensing unless the base is a smart
  serial servo — at which point it *is* the primary class + a sealing method.
- **FOC BLDC (moteus/ODrive):** best dynamic sensing and torque, but FOC driver +
  CAN + tuning + a housing you design is heavy overhead for a small gripper;
  strong but over-specified (kept as a credible #2–3 and as the magnetic-pod
  motor option).
- **JMC closed-loop stepper:** good telemetry + torque + cheap, but
  electromagnetic **power-holding heats a sealed canister** (its low
  holding_thermal score) — a real underwater liability.
- **Brushed worm-DC:** unbeatable zero-hold-current self-locking and torque, but
  shunt+back-EMF sensing is only ±10–20 % — too coarse for the force-control pitch.

## Modularity boundary (the swap point)

The **D-coupler on `input_pinion_shaft`** (Ø10, 1.4 mm D-flat, 12 mm) is the
explicit interface. **Any actuator that mates it — directly or through a printed
adapter horn — is in scope.**

- **Primary (smart servo):** drives the D-coupler via a **printed adapter horn**
  (servo spline → D-socket). The gripper geometry is **unchanged** — no edit to
  `SHAFT_COUPLER_*` (per campaign rule). The adapter is a separate printed part.
- **Fallback (magnetic pod):** would replace the exposed D-coupler with a magnet
  inner-rotor on the input shaft + a barrier wall + outer rotor + dry pod. That
  *does* change the coupler region, so it is logged as a **numbered, proposed-only
  option in `DECISION_LOG.md`** — not implemented, not silently rewritten.

## Forward

Phase 4 (`DRIVETRAIN.md`) re-checked the crown/pinion + sector-gear ratio against
the selected servo and ran a **gear FEA**. **Finding that updates the margin claim:**
the printed crown/pinion is the gripper's binding structural limit — safe input
torque **T_safe ≈ 0.03 N·m as-shipped, ≈ 0.4 N·m at the proposed re-size** — far
below **all three** servos' stall (XW540 9.5 N·m ≈ 12–280× T_safe; STS3250 4.9 N·m
≈ 12–144× T_safe; STS3215 2.94 N·m ≈ 7–86×). So the "stall headroom" above is *not*
free headroom: **the firmware current limit is the gear-protection mechanism,
mandatory on every servo in the ladder** ("one decision, three ESC profiles" — the
same torque ceiling, a per-servo current limit). The ratio stays 2.667:1 (anchored
on the STS3215 rock-bottom torque floor). Sensing (`SENSING.md`)
builds the current→force model on this drivetrain.

### Selection holds across the self-similar scale (1.0× / 1.5× / 2.0×)

`gripper.py`'s global `GRIPPER_SCALE` re-checked the gear ceiling against the
selected servos at 1.0×, 1.5× and 2.0× (full study + power-law derivation in
`DRIVETRAIN.md §9`; per-scale JSONs in `variants/scale_<k>x/fea/`). Self-similar
scaling gives **`T_safe ~ k³`** (tooth root-bending capacity) and **deliverable
tip force `~ k²`**, with `i_g` and `η` scale-invariant (counts + angles held).

| `GRIPPER_SCALE` | `T_safe` (radial 2D) | per-finger force band | XW540 (9.5 N·m) | STS3250 (4.9 N·m) | STS3215 (2.94 N·m) |
|---|---|---|---|---|---|
| 1.0× | 0.0131 N·m | 0.14 – 0.28 N | ~725× | ~374× | ~224× |
| 1.5× | 0.0442 N·m | 0.31 – 0.64 N | ~215× | ~111× | ~67× |
| 2.0× | 0.1048 N·m | 0.55 – 1.13 N | ~91× | ~47× | ~28× |

Because `T_safe ~ k³` outruns the **fixed** servo stall torque, the stall ÷ T_safe
ratio *shrinks* with size — but that ratio is the **over-torque danger** (how hard a
servo would smash the gears on a fault), not comfort headroom, so a shrinking ratio
is *safer*, and even at 2.0× the weakest servo (STS3215) still over-torques by ~28×.
**The drivetrain stays gear-limited at every scale in [1.0, 2.0], so the
current-limit remains the mandatory protection on all three servos** — the
*selection and the sensing pivot are scale-invariant*; only the per-scale `T_safe`
current setpoint changes. The selected servos clear the load with large margin at
every scale; none is the binding element. (Caveat: the 3D crown FEA does **not**
scale self-similarly as configured — hardcoded `DISK_T` + absolute mesh — so the
radial 2D bound is the scaling basis; a self-similar 3D re-run (GPU workstation) is the
high-fidelity follow-up, per `DRIVETRAIN.md §9.3`.)

> **Rank-only caveat (carried from `grip/GRIP_MODEL.md`).** This selection ranks
> actuators on sourced specs + judged scores; it does not certify an absolute
> grip force or a depth rating for the built tool. Those come from the bench/
> pressure tests in `BENCH_TEST.md`. Cross-links: `grip/DECISION_LOG.md`,
> `fea/DECISION_LOG.md`.

# Bench test plan — actuator + drivetrain + sensing validation

> **STATUS: TEST PLAN ONLY — NOT EXECUTED.**
> All pass/fail criteria are proposed targets derived from the analytical models
> in `SENSING.md`, `DRIVETRAIN.md`, and `MOTOR_MODEL.md`. No bench data has been
> collected. Nothing in this document is a measurement.

Cross-links: `SENSING.md`, `DRIVETRAIN.md`, `MOTOR_MODEL.md`, `FAILURE_MODES.md`,
`../grip/GRIP_TEXTURE.md`.

**Actuators in scope:** PRIMARY = DYNAMIXEL XW540-T260 (IP68 body, RS-485,
`present_current` telemetry); BUDGET = Feetech STS3215 (same drivetrain,
coarser 6.5 mA/step telemetry); FALLBACK = magnetic-pod (T3, pole-slip =
passive force limiter). Unless noted, tests target the PRIMARY actuator.

**Depth tiers:** T1 ≤ 10 m, **T2 ≤ 30 m (primary design point)**, T3 > 30 m.

**Run order:** 1 → 6C → 2 → 3 → 4 → 5 → 7 → 8 → 9 (fail cheap in air first;
coupon failure test before trusting the current-limit setting).

---

## Test 1 — Dry function test (in air)

**Purpose.** Confirm full travel, smooth mesh, and current within the firmware ceiling before water exposure.

**Setup / procedure.** XW540 coupled to drivetrain; `Current Limit` set to T_safe ceiling (shipped ~18 mA; re-sized ~215 mA); `present_position` + `present_current` logged at ≥ 50 Hz. Command open → close → open (~123° input) for 10 cycles at ≈ 20 rpm. Then rotate by hand with power off.

| Criterion | Pass | Fail |
|---|---|---|
| Full travel | Commanded travel ≥ 120° without position error | Stall or mechanical stop short of travel |
| Mesh smooth | No grinding or clicking; hand rotation smooth throughout | Audible tooth skip or grind |
| Current within limit | Peak `present_current` < `Current Limit` in all 10 cycles | Any cycle trips OCP or hardware current-limit |
| Repeatability | End-position variance < ±2° over 10 cycles | Drift or creep across cycles |

> *Honesty:* shipped geometry gives ~0.5 N safe grip; this test validates mechanical integration, not functional grip. Re-size is required for useful grip (`DRIVETRAIN.md §6`).

---

## Test 2 — Force calibration vs load cell (dry)

**Purpose.** Build the `present_current` → tip-force calibration curve (`SENSING.md §3`).

**Setup / procedure.** Phidgets 10 kg load cell (0.03 % FS ≈ 0.03 N) + NAU7802 24-bit ADC ≥ 80 SPS at the finger contact face. `F_tip = m·g·d_load/d_tip` via calibrated weights + lever arm. Gripper at mid-stroke (open_norm ≈ 0.55). Apply 8–12 force levels spanning 1–20 N; 3 cycles each; fit `F = a·I² + b·I + c`. Validate on 5 blind weights.

| Criterion | Pass | Fail |
|---|---|---|
| Calibration residual | RMS < 0.15 N over 1–20 N | Any residual ≥ 0.15 N |
| Hysteresis band | < 0.30 N across 3 cycles at any load | ≥ 0.30 N at any level |
| Blind-set accuracy | All 5 estimates within ±0.30 N of load cell | Any error ≥ 0.30 N |
| Reference uncertainty | Load-cell path confirmed < 0.05 N | ≥ 0.05 N invalidates the calibration |

> *Honesty:* XW540 has ~10 current steps above I₀ at the shipped T_safe ceiling; the full 1–20 N range is only practical after the re-size (T_safe → 0.40 N·m).

---

## Test 3 — Wet-bath function test (freshwater, T1)

**Purpose.** First water exposure: telemetry survives immersion, canister dry, full travel wet.

**Setup / procedure.** Gripper fully assembled in freshwater tank ≥ 30 cm; RS-485 tether over rim; log `present_position` + `present_current` + `present_temperature` at ≥ 50 Hz; clear-sided tank for bubble inspection. Lower slowly; soak 5 min stationary; 20 open/close cycles; hold at current-limit ceiling 2 min; surface and inspect canister + shaft within 5 min; re-run 5 dry cycles.

| Criterion | Pass | Fail |
|---|---|---|
| Telemetry stability | Continuous stream; no > 2 consecutive dropped packets | RS-485 dropout or garbage frames while submerged |
| Full travel wet | All 20 cycles reach commanded travel | Any stall or position error |
| Canister dry | No visible moisture inside after drain | Standing water or soaked cloth indicates leak |
| Actuator body dry | No water at output shaft journal (IP68 rated) | Visible ingress at shaft or connector |
| Post-soak baseline | No-load `present_current` matches pre-soak ± 5 mA | > 5 mA shift suggests internal corrosion |

> *Honesty:* freshwater T1 only — not a T2 (3 bar) or seawater validation; dynamic shaft-seal behaviour under load is not covered by the static IP68 rating (Test 8).

---

## Test 4 — Slip-onset detection vs 7-class grip object set

**Purpose.** Validate `present_current` derivative detects slip onset across all object classes, and slip ranking matches `slip_margin.py` (slimy worst — `MOTOR_MODEL.md §3`). Grip surface = crosshatch micro-post texture (`../grip/GRIP_TEXTURE.md`); μ_hold from `grip/GRIP_MODEL.md`.

**Setup / procedure.** Gripper submerged (freshwater T1); object classes: `smooth_wet`, `rough_wet`, `ridged_wet`, `slimy`, `soft_wet`, `small_curved`, `dry_smooth`. Load cell on a linear-pull fixture (~2 N/s ramp); `present_current` at ≥ 100 Hz; 3 trials/class. Close to grip setpoint; ramp pull to slip; compute `dI/dt` drop; compare to load-cell slip event; rank classes by pull-at-slip force.

| Criterion | Pass | Fail |
|---|---|---|
| Slip detection latency | Derivative drop within 100 ms of load-cell slip on ≥ 6/7 classes | Detection window > 100 ms or miss on ≥ 2 classes |
| Slimy worst | `slimy` has the lowest pull-at-slip force of all 7 classes | Any other class (excluding geometry outliers) slips before slimy |
| Rank ordering | `slip_margin.py` rank matches measured rank within ±1 position for ≥ 5/7 classes | > 2 classes misranked by ≥ 2 positions |
| False positives | < 2 false slip triggers per trial during close-down | ≥ 2 false triggers/trial |

> *Honesty:* `slip_margin.py` is rank-only, no absolute force guarantee (`MOTOR_MODEL.md §3`). At shipped grip (~0.5 N) hard objects may not develop a measurable slip; test is most informative after the re-size.

---

## Test 5 — Holding / thermal-duty test

**Purpose.** Confirm the actuator sustains grip at the current-limit ceiling for ≥ 10 min without thermal shutdown, back-drive, or position drift. Validates `holding_stall.py` sub-amp holding current prediction (`MOTOR_MODEL.md §3`).

**Setup / procedure.** Gripper holding a 40 mm rigid cylinder at current-limit ceiling, in air (conservative — no water cooling). Log `present_temperature` + `present_current` + `present_position` at 1 Hz; IR thermometer on body. Hold 10 min; release; confirm temperature returns to ambient ±3 °C.

| Criterion | Pass | Fail |
|---|---|---|
| Position held | `present_position` drift < 2° over 10 min | Drift ≥ 2° (back-drive creep) |
| No back-drive | Cylinder does not visibly shift | Object moves during hold |
| Temperature within spec | `present_temperature` < 85 °C (XW540 shutdown threshold) | Thermal alarm or shutdown |
| Holding current vs model | Measured holding current within 30 % of `holding_stall.py` prediction | > 30 % discrepancy |

> *Honesty:* sub-amp holding current is an analytical prediction; 10 min in air is conservative (seawater would cool the actuator).

---

## Test 6 — Gear-survival / current-limit test

**Purpose.** (A) Printed crown/pinion survives stalls at T_safe ceiling. (B) Uncapped stall *does* cause tooth damage — validating the limit's necessity, not merely its existence. (C) Coupon torque-to-failure bounds the FEA T_safe estimate (`DRIVETRAIN.md §3`). Sub-tests B and C are destructive; use spare/coupon parts.

**A — survival.** Drive into a steel hard stop 10× at T_safe current ceiling; inspect at ×10 magnification.  
**B — damage above limit.** Same rig, limit removed or set to 2× T_safe, on a sacrificial gear set; stall once; inspect.  
**C — coupon.** PA12-GF crown/pinion coupon (identical print settings) in a torque rig; ramp in 0.005 N·m steps; record first-yield and failure torques.

| Criterion | Pass | Fail |
|---|---|---|
| A — no yield at limit | No cracks, deformation, or stress whitening at ×10 after 10 stalls | Any visible tooth yield |
| B — damage above limit | Visible tooth fracture after stall at 2× T_safe | No damage (would mean the current limit is set unnecessarily low) |
| C — coupon first yield | ≥ T_safe (confirms limit is below the structural ceiling) | First yield < T_safe (limit is non-conservative) |
| C — FEA consistency | Coupon failure torque within 3× of FEA T_safe (FEA is 2–3× conservative by design) | Failure torque < T_safe/2 |

> *Honesty:* T_safe is a conservative 2D plane-stress estimate (`DRIVETRAIN.md §3`). Sub-test C bounds the real vs. analytical margin; if the coupon fails well above T_safe, the current limit can be relaxed to unlock grip force without re-sizing.

---

## Test 7 — Endurance (500 cycles wet)

**Purpose.** Mechanical wear, telemetry drift, and calibration drift after sustained cycling (~10–25 ROV dive equivalents).

**Setup / procedure.** Gripper submerged (freshwater T1); automated cycle script (open → close → open, 1 s/half-stroke, 2 s dwell); log all telemetry; pause at cycles 0, 100, 250, 500 for a 5-point blind force check (Test 2 subset); teardown inspection at 500 cycles.

| Criterion | Pass | Fail |
|---|---|---|
| Mechanical survival | No tooth fracture, finger delamination, or connector failure in 500 cycles | Any mechanical failure before 500 cycles |
| Stall rate | Stall events in < 5 % of cycles; all self-recover | Stall rate ≥ 5 % or stuck state |
| Calibration drift | Blind-set error at 500 cycles < 0.50 N | Drift > 0.50 N |
| I₀ drift | No-load current shift < 15 mA over 500 cycles | > 15 mA shift (significant friction increase) |

> *Honesty:* 500 cycles is an arbitrary gate, not a service-life certification; no PA12-GF flooded-journal wear model exists in the literature.

---

## Test 8 — Pressure test (by depth tier)

**Purpose.** Static ingress validation at T1 (1 bar), T2 (3 bar / 30 m), T3 (> 3 bar). Requires a pressure chamber ≥ 5 bar. **If unavailable, depth rating is limited to T1 — state this explicitly in any submission.**

**Setup / procedure.** Gripper through a pressure-rated bulkhead; RS-485 telemetry live; freshwater or dry N₂. Ramp to target pressure over 30–60 s; hold 10 min; at T2 add 5 gripper cycles at pressure; ramp down; inspect for ingress.

| Criterion | Pass | Fail |
|---|---|---|
| T1 (1 bar) — no ingress | Canister dry; telemetry continuous | Any ingress or dropout |
| T2 (3 bar) — no ingress | Canister dry after cycling at pressure | Ingress, connector leak, or dropout |
| T3 (> 3 bar) — no ingress | Canister dry; no housing deformation | Ingress or visible structural deformation |
| Post-pressure baseline | Telemetry values match pre-test baseline ± noise after release | Any persistent offset |

> *Honesty:* XW540 IP68 is a static manufacturer rating; the T2 cycling sub-step probes dynamic shaft-seal behaviour. Shaft-seal failure at T2 → escalate to magnetic-pod fallback (`SELECTION.md`).

---

## Test 9 — Post-test inspection

**Purpose.** Structured teardown condition record after all water tests or any failure event.

| Item | Inspect for | Record |
|---|---|---|
| Crown / pinion teeth | Root cracks, tip deformation, stress whitening | Photo ×10; tooth height |
| TPU fingers — texture | Root cracks at crosshatch micro-post stems; delamination | Photo; pin probe |
| TPU fingers — body | Fin-ray rib cracks; creases not recovering in 30 s | Photo; flex test |
| O-rings | Compression set, cuts (consumables — replace if any damage) | Visual |
| Shaft journal bores | Wear groove; ovality > 0.1 mm → replace | Bore/pin gauge |
| Connector + tether | Pin corrosion, jacket damage | Continuity test |

No single pass/fail gate — this is a **condition record**. Failed items set service intervals or flag design changes (crown-tooth wear confirms the re-size and current limit are both load-bearing).

---

## Summary

| # | Test | Tier | Key pass criterion | Status |
|---|---|---|---|---|
| 1 | Dry function | all | Full 123° travel, no stall, current < limit (10 cycles) | NOT EXECUTED |
| 2 | Force calibration vs load cell | dry bench | Residual < 0.15 N (1–20 N); blind-set < 0.30 N | NOT EXECUTED |
| 3 | Wet-bath function | T1 | Telemetry stable submerged; canister dry; full travel wet | NOT EXECUTED |
| 4 | Slip-onset detection (7 classes) | T1 wet | ≥ 6/7 detected within 100 ms; slimy worst; rank matches model | NOT EXECUTED |
| 5 | Holding / thermal duty | T1–T2 | Position held 10 min; temp < 85 °C; no back-drive | NOT EXECUTED |
| 6 | Gear survival + current-limit validation | bench | No yield at T_safe; damage at 2×T_safe; coupon failure ≥ T_safe | NOT EXECUTED |
| 7 | Endurance (500 cycles wet) | T1 | < 0.50 N calibration drift; no mechanical failure | NOT EXECUTED |
| 8 | Pressure test | T1/T2/T3 | No ingress; telemetry stable at rated pressure | NOT EXECUTED — chamber required |
| 9 | Post-test inspection | — | Structured condition record; all wear items assessed | NOT EXECUTED |

*All criteria are proposed analytical targets. Test 6B deliberately validates the
current limit's necessity by demonstrating that damage occurs above it — the limit
is structural, not precautionary.*

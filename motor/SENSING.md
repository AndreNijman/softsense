# Force sensing through the motor — the SoftSense pivot

The gripper senses grip force **through the actuator**, not through fingertip
sensors: motor current → motor torque → drivetrain back-trace → estimated tip
force. This is the principle force-controlled industrial/surgical grippers use
(Maxon, Robotiq, Schunk). It replaces the conductive-foam fingertip pads
(`DECISION_LOG.md` D5) — **zero added fingertip electronics underwater.**

> **What this is and isn't.** Sensed force is a **relative** signal until calibrated
> against a load cell; even calibrated it is a single **aggregate** grip force with
> **no contact-location information**. The estimate inherits the rank-only honesty of
> `grip/GRIP_MODEL.md` and `MOTOR_MODEL.md`. It is good for **force control and slip
> detection**, not tactile imaging.

---

## 1. Forward (sensor) model

A measured current sample → estimated per-finger tip force, back-traced through the
*same* chain as the drive model (`MOTOR_MODEL.md` §2):

$$\hat{F} = K_t\,(I_{meas}-I_0)\cdot \tfrac{i_g}{2}\cdot MA(P)\cdot \eta$$

`K_t` torque constant, `I_0` no-load/friction current, `i_g` = 2.667, `MA(P)` the
four-bar Jacobian, `η` the (calibrated) efficiency. Because command and readout share
the chain, one drivetrain characterisation closes the loop: commanding a current
limit sets a **force limit *and* the gear-protection ceiling** (`DRIVETRAIN.md`),
while reading current back gives the force estimate.

## 2. Which telemetry, how good (from the modality swarm — `SURVEY.md`)

| Modality | At stall? | Accuracy | Role |
|---|---|---|---|
| **Smart-servo current/load telemetry** (XW540 `present_current` 2.69 mA ≈ 0.005 N·m/step; **STS3250 `present_load` % — proxy for torque on the same SCS bus, K_t ≈ 1.17 N·m/A, load-cell-calibrated identically**; STS3215 `present_current` 6.5 mA, K_t ≈ 1.08) | yes | ±3–5 % calibrated | **primary** |
| **FOC `iq`/torque** (moteus int32 = 1 mA/1 mN·m) | yes | ±2–5 % calibrated | primary (BLDC fallback) |
| Brushed DC + current shunt (INA226/240) | partial | ±10–20 % raw, ±5–10 % cal | secondary |
| Sensorless hall/back-EMF | **NO — blind < 10–20 % rated speed** | contact-detect only | never primary |
| Strain-gauge / load cell | yes | reference-grade | **bench calibration GT only** |

**Resolution check.** Force resolution `ΔF = K_t·ΔI·i_g·MA·η/2`. The drivetrain is
current-limited to the gear ceiling (`T_safe` ≈ 0.034–0.40 N·m), so the *useful*
setpoint range is small: at a 0.05 N·m motor setpoint the XW540 has only ~10
`present_current` LSBs of headroom (fine but tight); the Feetech (6.5 mA/step) is
tighter. Above the gear ceiling there is plenty of resolution — the constraint is the
small commandable range, not the LSB.

## 3. Calibration — current→force curve against a bench load cell

Per the strain-gauge modality (`SURVEY.md`): a dry bench load cell is the ground
truth that turns the *relative* current signal into newtons.

1. **Rig:** mount a load cell (e.g. Phidgets 10 kg, 0.03 % FS = 3 g) + a 24-bit ADC
   (NAU7802, ≥ 80 SPS) at the finger contact face. Reference uncertainty < 0.05 N —
   well under the 0.3 N target.
2. **Apply known tip forces** via calibrated weights + a lever arm
   (`F_tip = m·g·d_load/d_tip`), or load the pad directly through the cell.
3. **Log `(I_motor, F_cell)` pairs** at 8–12 force levels (1…20 N), 3 cycles each
   (captures hysteresis + the `I_0` offset + drivetrain friction).
4. **Regress** `F = a·I² + b·I + c` (quadratic absorbs the motor R/back-EMF
   nonlinearity) or a lookup table; require residuals < 0.15 N (½ the target).
5. **Validate** on 5 blind weights; require < 0.3 N error. This is the
   `BENCH_TEST.md` calibration test.

Re-calibrate after thermal excursions (`K_t` drifts ~−0.1 %/°C; cold seawater is
favourable but shunt self-heating is not — `FAILURE_MODES.md`).

## 4. Noise floor & filtering

- **Brushed DC** carries commutation + PWM ripple (~5 % of mean); an RC/oversample
  filter (≈ 10 ms) recovers a 5–20 mA RMS floor — well under the ΔI target, but the
  filter spends part of the ≤ 50 ms latency budget (S4).
- **FOC / smart-servo** report a clean torque-axis current (no brush noise); the ADC
  noise floor is far below target — `K_t` tolerance + friction dominate, not noise.
- **Slip detection** watches the **force derivative** (a sudden `dF/dt` drop as the
  object starts to move), so the ≥ 50 Hz rate (S3) matters more than absolute
  accuracy for catching slip onset.

## 5. Validation plan (→ `BENCH_TEST.md`)

| Test | Pass criterion |
|---|---|
| Static calibration vs load cell | residual < 0.15 N over 1–20 N; blind-set error < 0.3 N |
| Repeatability (3 cycles) | hysteresis band < 0.3 N |
| Slip-onset detection vs the grip object set | detect slip within 100 ms on ≥ 6/7 object classes |
| Thermal re-check (cold bath) | error < 0.5 N after a 15 °C step |

## 6. Honest limits

- **Force-only, no contact location.** Motor current is one aggregate number — it
  cannot tell *where* on the finger the contact is, nor map pressure. (The foam could
  not really do this underwater either, but it is the explicit trade for removing
  fingertip wiring — `DECISION_LOG.md` D5.)
- **Relative until calibrated**, and per-unit (`K_t` ±5–10 % unit-to-unit).
- **Gear-ceiling-bounded.** The sensed/commandable force is capped by `T_safe`
  (`DRIVETRAIN.md`) — the sensor is most useful precisely as the limiter that keeps
  the printed gears alive.
- **Rank-only inheritance.** `grip_model.py` ranks object slip risk; it does not give
  the absolute hold force, so neither does a slip-margin readout built on it.

Cross-links: `MOTOR_MODEL.md`, `DRIVETRAIN.md`, `REQUIREMENTS.md` §8, `SURVEY.md`,
`BENCH_TEST.md`, `FAILURE_MODES.md`, `grip/GRIP_MODEL.md`.

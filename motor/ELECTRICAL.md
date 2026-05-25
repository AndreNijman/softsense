# Electrical architecture — wiring, power budget, and telemetry

This document is the **wiring and control plan** for the smart-serial-servo
actuator system. Numbers (voltage drop, wire resistance, current) are
**computed estimates with stated assumptions**, not bench-measured values.
Cross-links: `SENSING.md`, `DRIVETRAIN.md`, `SELECTION.md`, `../UNDERWATER.md`.

> **Scope.** Covers the primary actuator (DYNAMIXEL XW540-T260), the same-class
> budget build (Feetech STS3215), and the tier-3 fallback (magnetic-coupling pod
> with a FOC BLDC motor running moteus/ODrive). The connector sealing strategy
> is in `../UNDERWATER.md §6`; the material/depth-tier split is in `SELECTION.md`.
> Ground-truth force calibration is in `SENSING.md §3`.

---

## 1. Controller / driver

### 1a. Primary path — smart serial-bus servo (XW540 or STS3215)

The servo is its own ESC (motor + driver + encoder + current-sense ADC in one body).
The host needs only a **bus master** on the RS-485 or TTL half-duplex line:

| Option | Role | Notes |
|---|---|---|
| **ROBOTIS U2D2** | USB ↔ RS-485 & TTL | Plug-and-play with DYNAMIXEL SDK; 12 V via U2D2 Power Hub. Lives in **dry ROV electronics canister**. |
| **MCU + MAX3485 / 75176** | Embedded RS-485 master | STM32/ESP32 + RS-485 transceiver; removes USB round-trip latency. |
| **MCU + UART** | STS3215 TTL path | SCS TTL half-duplex (not RS-485); single-wire buffer, ≤ 1 Mbaud. |

Bus master is always **topside / dry housing** — never in the flooded gripper. Only
the 4-conductor servo bus + power cable runs wet (servo body is IP68 per `SELECTION.md`).

### 1b. Fallback path — FOC BLDC in a magnetic-coupling pod (tier 3)

For T3 (`SELECTION.md`): moteus r4.11 or ODrive 3.6 inside a sealed dry pod, coupled
magnetically (no rotating shaft seal). Driver sits **inside the pod**, communicates
via **CAN-FD** to a topside CAN-USB bridge (PEAK PCAN-USB). Reports `q_current`
(`iq`) at ≥ 1 kHz natively. The rest of this document covers the **smart-serial path
(T1/T2 primary)**.

---

## 2. Signal protocol — why RS-485 half-duplex, not PWM/CAN/I²C

| Protocol | Conductors | Telemetry at stall? | Multi-drop? | Verdict |
|---|---|---|---|---|
| **PWM** | 3 (V+, GND, signal) | No — command-only | No (one wire per servo) | Eliminated by the sensing pivot (R10): no current readback |
| **RS-485 UART (DYNAMIXEL Protocol 2.0)** | 4 (V+, GND, D+, D−) | **Yes** — position, current, temperature on the same bus | **Yes** — daisy-chain up to ~32 nodes per segment | **PRIMARY** |
| **TTL UART (SCS/STS)** | 3 (V+, GND, data) | **Yes** — same telemetry model | Yes (single wire half-duplex) | Budget STS3215 path; needs ≤ 3 m run or a signal repeater |
| **CAN-FD** | 4 (V+, GND, CAN-H, CAN-L) | Yes (moteus `iq`) | Yes (up to 64 nodes) | FOC fallback only; overhead is excessive for a 2-servo gripper |
| **I²C / SPI** | N/A | — | Short-range only | Not suitable for tether lengths |

**RS-485 wins because one 4-conductor cable carries V+, GND, D+, D−** from the dry
canister to both servos daisy-chained — and those same 4 wires carry back
`present_position`, `present_current`, and `present_temperature` in every reply packet.
Zero extra sense wires, zero extra wet connectors. DYNAMIXEL Protocol 2.0 is
half-duplex; the U2D2 handles TX-enable toggling automatically.

---

## 3. Tether power budget

### 3a. Conductor sizing — voltage drop vs tether length

Peak current budget is the **stall current**, not the run current
(`../UNDERWATER.md §7`). Stall values:

| Servo | Stall current (datasheet) | Run current (typ.) |
|---|---|---|
| XW540-T260 | **~5.1 A** | ~0.5–1.5 A |
| STS3215 | **~2.7 A** | ~0.3–0.8 A |

Formula: `V_drop = I × 2L × R_per_m` (round-trip). Cu at 20 °C: AWG 18 = 0.021 Ω/m, AWG 20 = 0.033, AWG 22 = 0.053.

**XW540 stall case (5.1 A) — V_drop (V) over round-trip tether:**

| AWG | 10 m tether | 20 m tether | 30 m tether |
|---|---|---|---|
| AWG 18 | **2.1 V** | 4.3 V | **6.4 V** |
| AWG 20 | 3.4 V | **6.7 V** | 10.1 V |
| AWG 22 | 5.4 V | 10.8 V | 16.2 V |

**STS3215 stall case (2.7 A) — V_drop (V) over round-trip tether:**

| AWG | 10 m tether | 20 m tether | 30 m tether |
|---|---|---|---|
| AWG 18 | 1.1 V | 2.3 V | **3.4 V** |
| AWG 20 | 1.8 V | **3.6 V** | 5.3 V |
| AWG 22 | 2.9 V | 5.7 V | 8.6 V |

*Assumed: one gripper axis, stall current, 20 °C copper; add ~5–10 % for stranded flex cable.*

### 3b. When does 12 V sag and when is 24 V needed?

XW540 operating range: 10–14.8 V. Gripper end must see ≥ 10 V at stall.

| Scenario | V_supply | V_drop (worst) | V_at_servo | OK? |
|---|---|---|---|---|
| XW540, AWG 18, 10 m | 12 V | 2.1 V | 9.9 V | **Marginal** — borderline at stall |
| XW540, AWG 18, 10 m | 12 V | 2.1 V | 9.9 V | Raise V_supply to 13–14 V or use AWG 16 |
| XW540, AWG 18, 20 m | 12 V | 4.3 V | 7.7 V | **Fail** — needs 24 V rail |
| XW540, AWG 18, 20 m | **24 V** | 4.3 V | 19.7 V | Pass (24 V tier-2 option, `SELECTION.md §6`) |
| STS3215, AWG 20, 20 m | 12 V | 3.6 V | 8.4 V | **Fail** — Feetech min 6 V, technically alive but weak |
| STS3215, AWG 20, 20 m | **12 V** | 3.6 V | 8.4 V | Borderline; consider AWG 18 |

**Take-away:** AWG 18 at 12 V fails the XW540 beyond ~8 m at stall. Beyond ~10 m, use
24 V + a DC-DC step-down at the gripper (e.g. Pololu S18V20F12 → 12 V). The STS3215's
lower stall current makes AWG 18 viable to ~20 m at 12 V.

> **Honesty:** computed estimates only. Stranded cable, coiling, and shared loads
> (thrusters, cameras) all add resistance. Measure V at the servo connector under load.

### 3c. Fusing and inrush

**Fuse: slow-blow at ~1.5× stall** — XW540 → 7.5 A; STS3215 → 4 A. Slow-blow is
required because inrush at power-on spikes 2–3× run current without constituting a
stall. Place the fuse **topside, at the supply output**. Do not fuse at the stall
value exactly — the servo must reach stall on a normal hard-grip without tripping;
the firmware current limit (§6) is the force ceiling, not the fuse.

**Inrush / soft-start:** at power-on the servo bulk capacitor charges rapidly.
Stagger both servos ≥ 200 ms apart, or add an **NTC inrush limiter** (e.g. Ametherm
SL22 5R025) in the tether supply line.

---

## 4. Telemetry channel — the sensing pivot

This is the core of the motor-current-as-force-sensor architecture
(`SENSING.md §1`). The same 4 wires that carry commands carry force back.

### 4a. What each controller exposes

| Actuator | Register / field | LSB | Torque resolution | Rate (max) |
|---|---|---|---|---|
| **XW540-T260** | `present_current` (reg 126, 2-byte int16) | **2.69 mA** | ~0.005 N·m/step at the servo shaft | ~100–200 Hz via Sync Read |
| **STS3215** | `present_current` (SCS reg 56, 2-byte) | **6.5 mA** | ~0.012 N·m/step | ~50–100 Hz |
| **moteus r4.11 (FOC fallback)** | `q_current` (int32) | **1 mA** | ~0.001–0.002 N·m/step (K_t dependent) | ≥ 1 kHz |

The XW540 resolves ≈ 0.005 N·m per step, giving ~0.07 N tip-force resolution
at mid-face contact — comfortably below the 0.3 N target (`SENSING.md §2`).
**Caveat:** at the shipped gear ceiling (T_safe ≈ 0.034 N·m) the XW540 has only
~10–13 present_current LSBs of commandable headroom. This is adequate but tight;
the proposed re-sized drivetrain (T_safe ≈ 0.40 N·m, `DRIVETRAIN.md §3`)
gives ~80–100 LSBs — much more comfortable for closed-loop force control.

### 4b. How telemetry pipes through the tether

**Smart serial path (primary):** DYNAMIXEL Sync Read broadcasts to both servo IDs
in one packet; each servo appends its reply in turn — 2 axes, 1 round-trip,
no extra wires. **FOC fallback:** CAN-FD over CAN-H/CAN-L twisted pair; 4 conductors
total (same count as RS-485).

### 4c. Sample rate vs tether bandwidth — the tradeoff

RS-485 at 4 Mbaud (XW540 max) supports ~200 Hz Sync Read for 2 servos
(packet sizes ~20–30 bytes per servo, plus inter-frame gap). At full baud and
short tether, 100–200 Hz is achievable, satisfying S3 (`REQUIREMENTS.md §8`).

**Long tethers limit baud:** high-frequency RS-485 over 20–30 m unshielded
cable suffers from reflections, capacitive loading, and common-mode noise from
thrusters. Practical safe baud over 30 m is ~1 Mbaud (the STS3215's max), which
still supports ~50–100 Hz Sync Read for 2 axes. This meets the S3 floor (≥ 50 Hz)
but with no headroom. Mitigations:

- Use **shielded twisted-pair** (STP) for the RS-485 pair in the tether.
- Add **120 Ω termination resistors** at each end of the RS-485 segment.
- If baud must drop below 1 Mbaud, reduce the telemetry set to `present_current`
  only (drop temperature, velocity) to recover packet bandwidth.

**Latency budget (S4 ≤ 50 ms):**

| Stage | Budget |
|---|---|
| Servo ADC sample + reply | ~1–2 ms |
| Bus transit (20 m, 1 Mbaud) | ~0.2 ms (propagation negligible) |
| USB round-trip (U2D2 → host) | ~5–10 ms (USB 2.0 latency) |
| Host parsing + filter (10-tap MA) | ~2–5 ms |
| **Total** | **~8–17 ms** |

Headroom remains for the 40 ms tether-to-ROV-pilot link budget. The latency
budget is satisfied.

### 4d. Topside parsing

Polling loop (Python + `dynamixel_sdk`, or a ROS2 driver node):

1. Send Sync Read for IDs [1, 2], register `present_current` (address 126, 2 bytes).
2. Convert raw int16 → amperes: `I_A = raw × 2.69e-3` (XW540) or `× 6.5e-3` (STS3215).
3. Pass through `SENSING.md §1` forward model to get `F_tip_estimate`.
4. Compare against grip-force setpoint; adjust `goal_current` register if needed.
5. Log slip detection: watch `dF/dt` via finite difference at ≥ 50 Hz.

---

## 5. Ground scheme

### 5a. Single-point ground

All returns (servo, MCU, sensors) share **one GND node at the ROV battery negative**.
No parallel return paths through tether shield or ROV frame — each parallel path is
a ground loop that seawater and thruster switching can excite. Tether shield: connect
**topside end only**; leave subsea end floating to avoid shield-driven loop currents.

### 5b. Isolation at the M4 arm joint

The 4 × M4 flange holes mate the gripper to the ROV arm (`../UNDERWATER.md §5`).
If the arm is metal, the joint is an electrical coupling point.

**Mitigation (mandatory for metal arms):** nylon shoulder bushings (Ø4.5 mm, M4
clearance) in each flange hole + PTFE/polyester isolating washers under bolt heads.
This breaks the galvanic path between ROV-frame GND and servo power return, preventing
stray return current routing through the joint into seawater.

### 5c. Seawater as a conductor

Seawater (resistivity ~0.2–0.3 Ω·m) forms a galvanic cell between any two metals
at different potentials. The gripper is **all-polymer** (`../UNDERWATER.md §5`) — no
exposed metal in the printed assembly. The concern is the servo body (XW540:
aluminium) and tether connector shells. Keep servo body at GND potential; float
or isolate connector shells from signal ground.

---

## 6. Current-limit configuration — the gear-protection ceiling

### 6a. Why it is mandatory (`DRIVETRAIN.md §7`)

| Servo | Stall torque | vs T_safe shipped (0.034 N·m) | vs T_safe re-size (0.40 N·m) |
|---|---|---|---|
| XW540-T260 | 9.5 N·m | ~280× | ~24× |
| STS3215 | 2.94 N·m | ~86× | ~7× |

A fault or hard-stop stall **will strip the crown/pinion teeth** without a firmware
ceiling. The current limit is **not a performance preference — it is gear protection.**

### 6b. How to set it — "one decision, two ESC profiles"

Same torque ceiling for both servos, different raw LSB threshold because K_t and
mA/LSB differ. Target: **T_cmd ≤ T_safe**; for a useful grip on the proposed
re-sized drivetrain: T_cmd ~ 0.3–0.4 N·m.

K_t is the torque constant (= stall torque ÷ stall current = telemetry N·m per A;
XW540 9.5 N·m ÷ 5.1 A ≈ STS3215 2.94 ÷ 2.7 ≈ the per-step torque ÷ per-step current):

| Servo | K_t (N·m/A) | T_cmd = 0.35 N·m → I_limit | raw LSB | DYNAMIXEL/SCS register |
|---|---|---|---|---|
| **XW540-T260** | **1.86** | **~0.19 A** | ≈ 70 LSB (× 2.69 mA) | `current_limit` (reg 38) AND `goal_current` (reg 102) |
| **STS3215** | **1.08** | **~0.32 A** | ≈ 50 LSB (× 6.5 mA) | `goal_torque` / max-torque reg (model-specific) |

Set **both** `current_limit` (hardware ceiling, survives power-cycle) and
`goal_current` (operating setpoint). `current_limit` is the backstop; `goal_current`
is the control input.

> **XW540 low-setpoint caveat (`SENSING.md §2`):** at the shipped T_safe
> (~0.034 N·m), the useful current setpoint is only ~10 LSBs of headroom above
> the no-load current — fine for bench integration but tight for closed-loop force
> control. The proposed re-sized drivetrain (T_safe ~0.40 N·m) gives ~80–100 LSBs
> of headroom and is the recommended configuration for production use.

### 6c. Implementation checklist

- [ ] On startup, write `current_limit` to the per-servo value above **before**
      enabling torque (`torque_enable = 1`).
- [ ] Set operating mode to **Current Control Mode** (XW540 operating_mode = 0)
      or **Current-Based Position Mode** (operating_mode = 5) — not plain position
      mode, which ignores `goal_current`.
- [ ] Log `present_current` continuously; alarm if it saturates at `current_limit`
      for > 500 ms (indicates a jam or a stall against a rigid object — close-loop
      response should back off, not hold).
- [ ] After any firmware update, re-verify `current_limit` is written (the register
      can revert to factory default on flash).
- [ ] **Both servos** get their own profile — do not assume the same raw LSB value
      applies to both (different mA/LSB).

---

## Summary — one cable, complete control + sensing

| Function | Wire(s) | Where |
|---|---|---|
| Power | V+ (12 V or 24 V), GND | Tether, topside-to-servo |
| RS-485 command | D+, D− | Tether, same 4-conductor cable |
| Position telemetry | D+, D− | Same RS-485 bus |
| **Force telemetry** (`present_current`) | D+, D− | Same RS-485 bus — no extra wire |
| Temperature telemetry | D+, D− | Same RS-485 bus |
| Ground isolation | Nylon bushings at M4 flange | Mechanical joint to ROV arm |

The full gripper electrical interface is **one 4-conductor cable** to each servo
(or a daisy-chained 4-conductor run). No separate sense wires, no fingertip
electronics, no wet connectors beyond the servo body and the tether bulkhead.

> **Honesty.** This is a wiring and control **plan** derived from datasheets and
> computed estimates. The voltage-drop table assumes ideal copper, 20 °C, no
> contact resistance. The current-limit LSB values assume the published K_t and
> linear torque-current. Actual commissioning should measure V at the servo
> connector under load and confirm the force–current calibration per `SENSING.md §3`
> against a bench load cell before relying on the telemetry for force control.

Cross-links: `SENSING.md`, `DRIVETRAIN.md`, `SELECTION.md`, `REQUIREMENTS.md`,
`../UNDERWATER.md`.

# Failure Modes and Effects Analysis — motor / drivetrain / sensing

Underwater soft gripper — fully 3D-printed flooded design on an ROV.
Primary actuator: DYNAMIXEL XW540-T260 (IP68 body, RS-485, native
`present_current` + `present_position` + `present_temperature`).
Budget build: Feetech STS3215 (same telemetry model, TTL bus).
Tier-3 fallback: magnetic-coupling dry-pod (FOC BLDC, CAN-FD).

> **Honesty statement.** This is a pre-deployment design analysis — not a
> record of observed failures on a built article. Likelihood and severity are
> qualitative engineering judgements (L/M/H; 1 = nuisance → 5 = loss of
> gripper or specimen damage). Hardware validation is the job of
> `BENCH_TEST.md`. Cross-links throughout: `DRIVETRAIN.md`, `SENSING.md`,
> `ELECTRICAL.md`, `BENCH_TEST.md`, `../docs/UNDERWATER.md`.

---

## Mechanical and power failure modes

### M1 — Motor stall / over-torque: gear tooth yield

| Field | Detail |
|---|---|
| **Cause** | Hard-stop stall against a rigid object, fully-closed position, or jam. Servo stall torque far exceeds printed-gear T_safe: XW540 9.5 N·m; STS3215 2.94 N·m; T_safe shipped ~0.034 N·m, proposed re-size ~0.40 N·m. Without a ceiling, a single fault strips the crown/pinion. |
| **Detection** | `present_current` spikes to the firmware current-limit and holds there. `present_position` stops advancing while motor continues to run — position error accumulates, distinguishing a jam from a normal grip. |
| **Mitigation** | **Firmware current-limit is mandatory on both servos** — this is gear protection, not a performance preference. Write `current_limit` register (XW540 reg 38) AND `goal_current` (reg 102) before enabling torque on every power-on. Both servos need their own LSB-correct profile: same torque ceiling, different raw value because mA/LSB differs (XW540 2.69 mA/step; STS3215 6.5 mA/step). Re-verify after every firmware flash — register reverts to factory default. See `ELECTRICAL.md §6`. |
| **Graceful degradation** | Current cap holds torque at T_safe; gripper stops closing with force bounded. No tooth yield. If the object is harder than the cap permits, the gripper stalls at the limit with no mechanical damage. |

### M2 — Water ingress into the actuator or sealed canister

| Field | Detail |
|---|---|
| **Cause** | O-ring blow-out or pinch on the servo body (XW540 IP68 rated; STS3215 IP54 — requires canister for T2/T3); connector flood; housing cracked under pressure cycling; inadequate pre-dive seal check. |
| **Detection** | Erratic or elevated `present_current` at rest (electrolysis current); unexpected temperature anomaly; RS-485 comms loss or CRC errors; servo hardware-error register flag; bus isolation resistance drop detectable with a topside megohm check before dive. |
| **Mitigation** | IP68 body on primary servo. Sealed canister for budget build and all T2/T3 deployments. Wet-mate or potted connector per tier (`../docs/UNDERWATER.md §6`). Pre-dive seal and continuity check protocol. Pressure-cycle test per `BENCH_TEST.md`. Do not exceed rated depth tier. |
| **Graceful degradation** | Loss of that actuator axis. Both axes on the same bus — one can be isolated in firmware. The magnetic-pod fallback (T3) removes the shaft-seal failure path entirely: no rotating shaft penetrates the housing. |

### M3 — Tether power loss / brown-out under stall current

| Field | Detail |
|---|---|
| **Cause** | Stall current (XW540 ~5.1 A; STS3215 ~2.7 A) causes voltage sag on an undersized tether; fuse blow; ROV supply interruption; inrush at power-on during a degraded supply. |
| **Detection** | Bus voltage drop visible on servo `present_voltage` register; servo reboots (resets to power-on defaults); RS-485 heartbeat absent; topside watchdog timer fires. |
| **Mitigation** | Size tether conductors for stall, not run current. AWG 18 minimum for XW540 at ≤ 10 m; 24 V supply + DC-DC step-down beyond ~10–20 m (see `ELECTRICAL.md §3`). Slow-blow fuse at ~1.5× stall current. Stagger servo power-on ≥ 200 ms; NTC inrush limiter in the supply line. Soft-start ramp in firmware. |
| **Graceful degradation** | **Back-drivable drivetrain: grip releases on power loss.** No worm gear — the chain is back-drivable. A powered positional servo holds actively; an unpowered chain is free to back-drive to open. Safety consequence: **held object will be dropped** on any power loss event. For most sampling operations this is acceptable (drops the object, no hardware damage). If hold-through-power-loss is mission-critical (e.g. emergency ascent with sample), a self-locking stage or mechanical brake must be added — accepting that it gives up the back-drive overload escape (M4). That is a mission-design trade, not a default. |

### M4 — Back-drive overload: external load exceeds active holding torque

| Field | Detail |
|---|---|
| **Cause** | ROV manoeuvre imparts reaction force through the gripper; thruster surge; specimen snagged on the environment; unexpected collision; grip object denser or heavier than expected. |
| **Detection** | `present_position` error grows while `goal_current` stays at the setpoint; position registers drift from commanded value under sustained load. |
| **Mitigation** | Servo holds actively (powered). Firmware current-limit prevents gear damage during back-drive events. For the T3 magnetic-coupling fallback, the pole-slip torque is the mechanical overload clutch — it caps back-drive torque at the coupling's slip threshold (scales with coupling diameter, not housing radius), then releases smoothly. |
| **Graceful degradation** | Controlled slip or release rather than tooth fracture. Back-drivable chain means fingers open and yield to the overload, protecting specimen and mechanism. The magnetic fallback's pole-slip is a designed-in safety valve (`DRIVETRAIN.md §8`). |

### M5 — Connector flood or short

| Field | Detail |
|---|---|
| **Cause** | Wet-side connector not rated for depth; improper mate or damaged seal; conductor corrosion after repeated salt-water cycles; pinhole crack in potting compound. |
| **Detection** | RS-485 comms loss or corrupted packets; `present_current` elevated or erratic at no command; topside ground-fault detector trips; ROV bus current anomaly. |
| **Mitigation** | Wet-mate or fully potted connector for every depth tier (`../docs/UNDERWATER.md §6`). Inspect and pressure-test connector pre-dive. Nylon shoulder bushings at the M4 flange mount isolate servo power-return from the ROV frame, preventing stray return current through seawater (`ELECTRICAL.md §5`). |
| **Graceful degradation** | Lose that actuator axis. Connector-level short isolated from ROV bus by in-line fuse and frame isolation — other gripper axis and ROV subsystems unaffected if isolation is intact. Abort dive for connector inspection. |

### M6 — Gear tooth wear and fatigue over cycles

| Field | Detail |
|---|---|
| **Cause** | Cyclic bending at the crown/pinion interface; PA12-GF accumulates fatigue damage under current-limited load; micro-abrasion in seawater-lubricated contact (seawater is a poor tribological fluid); any overload event accelerates crack initiation at the tooth root. |
| **Detection** | Growing backlash measured as position hysteresis on a close/open cycle; `present_position` drift under constant `goal_current`; visible tooth deformation on post-dive inspection. |
| **Mitigation** | PA12-GF material for higher fatigue life vs plain PA12 (`DRIVETRAIN.md §2`). Current-limit held strictly at or below T_safe — operating margin preserved over the teeth. Post-dive visual and functional inspection (backlash check). Log cycle count; replace printed gear set at an interval established empirically by `BENCH_TEST.md`. |
| **Graceful degradation** | Increasing backlash degrades position repeatability before catastrophic tooth loss — progressive failure, not sudden. Early warning is available from telemetry drift before complete failure. Printed gear set is a low-cost replaceable part: by design, a consumable. |

---

## Sensing failure modes — the pivot's new failure surface

The sensing pivot — motor current as grip-force sensor — is the design's
key capability and its primary new failure surface. Removing fingertip
electronics eliminates one underwater failure surface (wet wiring, connectors,
electrolysis) but concentrates force-sensing reliability in the RS-485
telemetry chain and the calibration model. The modes below cover that chain
specifically. These are the failure modes that did **not** exist in a
conventional position-only gripper.

### S1 — Telemetry dropout: RS-485 packet loss or bus noise

| Field | Detail |
|---|---|
| **Cause** | Thruster PWM and switching regulators couple common-mode noise into an unshielded RS-485 run; long tether (> 20 m) with reflections at baud > 1 Mbaud; missing or mismatched 120 Ω termination resistors; bus collision from servo addressing error. |
| **Detection** | CRC-fail or absent reply packets at the topside parser (`COMM_RX_TIMEOUT`, `COMM_RX_CORRUPT` in the DYNAMIXEL SDK); packet loss rate > 1 %; watchdog timer fires on reply absence > 100 ms. |
| **Mitigation** | Shielded twisted-pair (STP) for D+/D− in the tether. 120 Ω termination resistors at both ends of the RS-485 segment. Baud rate reduced to ≤ 1 Mbaud for tethers > 20 m (`ELECTRICAL.md §4c`). Retry logic in the topside parser (≥ 3 retries before fault declaration). Watchdog with escalating response: retry → fallback → abort. |
| **Graceful degradation** | **Fall back to open-loop position control** — no force feedback. Gripper closes to a pre-defined position target with a conservative fixed current limit. Grip is safe (the current ceiling still protects the gears and the specimen) but not adaptive. Operator is alerted; re-establish comms before resuming force-controlled operation. |

### S2 — Current-sense offset / gain drift

| Field | Detail |
|---|---|
| **Cause** | Servo internal current-sense ADC offset shifts with temperature or age; `K_t` varies ±5–10 % unit-to-unit per datasheet; friction model (`I_0` no-load current) changes with wear or lubrication state; shunt resistance drift in the servo's internal circuit. |
| **Detection** | Non-zero `present_current` at known no-load (motor enabled, no grip load applied); calibration check against a bench load cell returns error outside the ±0.3 N acceptance band (`SENSING.md §3`); two successive session-start calibration checks diverge by > 5 mA. |
| **Mitigation** | Periodic tare: zero `I_0` at no-load at the start of each dive session. Re-run the full current→force calibration curve (`SENSING.md §3`) after any servo replacement or significant thermal excursion. Log the `I_0` baseline; flag deviation > 5 mA session-to-session as a re-calibration trigger. |
| **Graceful degradation** | Force readout is biased by a fixed offset — reads systematically high or low. The force cap (current-limit register) is still hardware-enforced and unaffected by ADC drift. Widen the grip-force safety margin in the control setpoint until re-calibrated. |

### S3 — Calibration drift after thermal cycling

| Field | Detail |
|---|---|
| **Cause** | Motor winding `K_t` drifts ~−0.1 %/°C. Cold seawater (5–15 °C) shifts a bench calibration done at 20–25 °C by several percent. Servo self-heating during operation partially offsets cold immersion — the net is a non-stationary baseline. |
| **Detection** | Known-weight calibration check (`BENCH_TEST.md`) returns force error that grows with the temperature delta between calibration environment and deployment water temperature. Error grows approximately a few percent per 10 °C step. |
| **Mitigation** | Temperature-compensated calibration: record water temperature at calibration time and apply a `K_t(T)` correction factor. Re-run calibration after any > 10 °C environmental step. Use `present_temperature` from the servo's own internal thermistor as the real-time winding temperature proxy for a live correction term. |
| **Graceful degradation** | Force error grows with temperature delta. At 15 °C delta: ~1.5 % `K_t` error — a small fraction of a newton at the operating range. The current-limit gear ceiling is temperature-independent (it is a raw current count, not a force number) — mechanical protection is unaffected by thermal drift in `K_t`. |

### S4 — Sense saturation at stall: current pinned at the firmware limit

| Field | Detail |
|---|---|
| **Cause** | Object harder than expected; gripper hits a hard stop; current-limit fires and holds. `present_current` is pinned at `current_limit` — the ADC is at its commanded ceiling, not at a hardware rail. |
| **Detection** | `present_current` reads constant at or near `current_limit` for > 200 ms; `present_position` stops advancing; force estimate is stuck at the ceiling value with no dynamic information. |
| **Mitigation** | Design the normal working range to operate **below** the current-limit ceiling. The commanded grip force setpoint should run at 70–80 % of the limit so the force estimate retains headroom before saturation. The limit is a protective cap — it is not meant to be the operating point. |
| **Graceful degradation** | Above the ceiling, grip force is **"at least X N"** — a lower bound, not a precise number. This is the intended behaviour: the limit IS the mechanical protection ceiling. Safe recovery: back off the position command to reduce current; re-engage with a lower setpoint. Do not treat saturation as a sensor fault — it is the gear-protection mechanism functioning correctly. |

### S5 — Loss of force feedback in servo fault or overtemperature state

| Field | Detail |
|---|---|
| **Cause** | Sustained high-current operation without duty cycling; sealed canister blocking convection; ambient water temperature higher than expected; repeated stall events without cooling intervals. The servo's own protection trips an overtemperature shutdown (XW540 hardware error register, overheating bit). |
| **Detection** | `present_temperature` approaches or exceeds the servo protection threshold (~80 °C internal for XW540); servo error register (reg 70) sets the overheating bit; torque is disabled by the servo's own protection firmware; RS-485 comms remain active while torque is off — the fault is readable. |
| **Mitigation** | Monitor `present_temperature` continuously at every telemetry poll. Alarm and reduce duty cycle at a conservative threshold (e.g. 65 °C — 15 °C headroom before servo self-trip). Design the grip-and-hold duty cycle with the thermal budget in mind. Flooded gripper body conducts heat from the servo body into seawater — a real thermal management advantage of the flooded design vs. a sealed-air enclosure. |
| **Graceful degradation** | Servo disables its own torque. **Force feedback is lost** — current is no longer a valid force proxy when torque is off. Fall back to position-only control with conservative open-loop targets. Abort the current grasp; allow cooling before re-engaging. Log overtemperature events — repeated occurrence indicates a duty-cycle or thermal design violation. |

---

## Prioritisation

**Highest likelihood × highest severity (address first):**

1. **M1 — Gear tooth yield under stall.** Likelihood: High (both servos exceed
   T_safe by 10–280× without a limit). Severity: 5 (loss of gripper mechanism,
   no field repair). Mitigation is a firmware register write — it costs nothing,
   but must be re-verified after every flash.

2. **S1 — Telemetry dropout.** Likelihood: Medium-High (thruster noise + long
   tether is a realistic ROV environment). Severity: 4 (loss of force feedback;
   fall to open-loop). Termination resistors and shielded cable are cheap
   insurance; the open-loop fallback keeps the system safe but uncontrolled.

3. **M2 / M5 — Water ingress (servo body or connector).** Likelihood: Medium
   (IP68 servo body is robust; connectors and canisters are the weak points in a
   flooded-body design). Severity: 4–5 (loss of actuator axis; possible ROV bus
   fault if isolation fails). Pre-dive protocol and connector tier selection are
   the primary controls.

4. **S3 / S2 — Calibration drift (thermal or offset).** Likelihood: Medium
   (unavoidable in the field). Severity: 2–3 (force readout error; mechanical
   protection is intact). The current-limit ceiling is a raw current count — it
   is immune to `K_t` drift. Force accuracy degrades, gear protection does not.
   Manageable with a session-start tare and temperature-compensated calibration.

5. **M3 — Brown-out / power loss.** Likelihood: Low-Medium (proper sizing
   prevents it; shared ROV supply is unpredictable). Severity: 3 (dropped
   object; no hardware damage). See key safety statement below.

6. **S4 — Saturation at the current limit.** Likelihood: Low (operating point
   is designed below the ceiling). Severity: 1 (expected, designed behaviour —
   not a fault). Clearly document so operators do not misread the saturated
   readout as a sensor failure.

**Lower priority** (by design, already bounded):

- **M4** back-drive overload: chain back-driveability is a feature; magnetic-pod
  pole-slip is a built-in clutch that caps the overload torque.
- **M6** wear/fatigue: printed gear set is a consumable; replace on a cycle
  schedule once `BENCH_TEST.md` establishes the empirical interval.
- **S5** overtemperature: seawater cooling is a design advantage; duty-cycle
  discipline prevents the condition.

---

## Key safety statement

> **The drivetrain is back-drivable.** There is no worm gear, brake, or
> self-locking stage. A powered positional servo holds actively; an unpowered
> chain is mechanically free to back-drive to the open position. **On any power
> loss — brown-out, fuse blow, tether fault, servo reboot — the gripper opens
> and the held object is released.** This is the intended safe state: it
> prevents a stuck-closed failure during a loss-of-power event and protects
> specimen and mechanism from a dead-stick grip. If mission requirements demand
> hold-through-power-loss (e.g. sample retention during an emergency ROV ascent),
> a self-locking stage or mechanical brake must be explicitly added — accepting
> that it removes the back-drive overload escape (M4) and changes the M3
> brown-out behaviour from "releases" to "holds until manually opened." That
> trade is a mission-design decision, not a default of the current architecture.

---

> **Analysis status.** All failure modes, mitigations, and degradation paths
> are pre-deployment analytical assessments derived from datasheets, computed
> FEA estimates, and design documents. No failure modes have been exercised on
> built hardware. `BENCH_TEST.md` is the empirical validation plan. Numbers in
> this document (T_safe, current limits, temperature thresholds, force errors)
> inherit the honesty caveats of `DRIVETRAIN.md §7`, `SENSING.md §6`, and
> `ELECTRICAL.md §6c`.

Cross-links: `DRIVETRAIN.md` · `SENSING.md` · `ELECTRICAL.md` · `BENCH_TEST.md` · `../docs/UNDERWATER.md`

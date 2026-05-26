# Motor campaign — decision log

Blow-by-blow of the actuator-system campaign (branch `feat/actuator-system`),
in the spirit of `grip/DECISION_LOG.md` and `fea/DECISION_LOG.md`. Numbered
decisions; options that were considered and rejected are kept, not erased.

---

> ⚠️ **What "12 N" means throughout this log.** 12 N is the finger-FEA
> **stress-probe load** used to fairly rank finger designs in software, not
> a force the shipped drivetrain delivers. Per the gear-tooth FEA the
> per-finger force band is **0.14–0.73 N** (radial 2D crown FEA) or
> 4.2–8.7 N (proposed re-size). See `OVERNIGHT_FIXES.md #1` for the full
> propagation, `motor/DRIVETRAIN.md` for the radial crown FEA result, and
> `motor/scripts/drivetrain_force_envelope.py` for the live force band.

## D1 — Scope & locked geometry
Campaign = motor selection + actuator integration + ROV mounting in `motor/`.
**Locked, untouched:** finger geometry (`fea/UNIVERSAL_FINGER.md`), grip texture
(`grip/GRIP_TEXTURE.md`, the `FR_GRIP_*` crosshatch), print profile
(`PRINT_PROFILE_P1S_TPU.md`). **Unlocked:** gear/crown/pinion ratios, D-coupler
dims, housing/mount. The blocky representative drivetrain in `gripper.py` is to
be replaced/retuned.

## D2 — Requirements derived from the live kinematics, not assumed
`motor/scripts/kinematics_chain.py` imports `gripper.py` and computes the
input-torque ↔ tip-force chain: i_g = CROWN_TEETH/PINION_TEETH = 24/9 = 2.667:1;
the 1:1 sector mesh makes the left gear carry both fingers (T_motor·i_g = 2·T_finger);
the four-bar Jacobian gives MA(P). Result: input torque **0.56–1.18 N·m for 12 N/
finger** across the efficiency envelope (η 0.40–0.71), input travel only **122.7°**
(→ limited-rotation OK), speed trivial. Target band → `REQUIREMENTS.md` R1–R9.
12 N is the finger-FEA *report level* (a fair comparison basis), cited as such,
not a physical mandate.

## D3 — Survey by a 12-agent concurrent swarm
7 actuator classes + 5 sensing modalities, each agent datasheet-sourced. Roster +
findings: `iterations/_survey_provenance.md`; merged data: `SURVEY.md`.

## D4 — **The sensing pivot: the actuator IS the force sensor**
**Decision:** grip-force sensing moves from fingertip sensors to **motor-current /
torque telemetry** back-traced through the drivetrain (the Maxon/Robotiq/Schunk
principle). Adopted as a **hard selection filter** (R10 / `REQUIREMENTS.md` §8,
S1–S5): a candidate must stream torque/current at ≥ 50 Hz fine enough to resolve
a ≈ 0.3 N tip step (≈ 0.02 N·m at the input shaft), ≤ 50 ms end-to-end.
**Why:** it makes the actuator do double duty (force control + sensing) with
**zero added fingertip electronics underwater** — a stronger, more defensible
innovation than the foam, and the literal industry approach. **Consequence:**
open-loop PWM servos (most "waterproof" RC servos, incl. the best-sealed Blue
Trail Eng. units) are eliminated; smart-serial servos and FOC/closed-loop drives
rise. Sensed force is *relative* until load-cell-calibrated (`SENSING.md`).

## D5 — Conductive-foam fingertip sensor: **REMOVED** (numbered options)
The pre-pivot SoftSense plan used conductive-foam fingertip pressure pads.
With D4, that role is taken by motor-current sensing. Options considered:

- **(a) Remove the foam entirely — CHOSEN.** Simpler finger; **no wires routed
  through the flexing TPU**; no underwater connector/ingress failure point at the
  fingertip; aligns with the "zero added fingertip electronics" pitch. The finger
  reverts to the settled `fea/UNIVERSAL_FINGER.md` geometry untouched.
- (b) Keep the foam as a **redundant secondary** signal fused with motor current.
  *Rejected:* re-introduces exactly the TPU wiring-penetration + waterproofing
  failure class that motivated dropping it (confirmed by the strain-gauge/in-situ
  modality agent), for marginal benefit over a load-cell-*calibrated* current
  signal.

**Tradeoff accepted (stated plainly):** motor-current sensing gives a single
**aggregate grip force** — it has **no contact-location / pressure-map** info,
and slip detection must use the **force derivative**, not a distributed signal.
The gripper's value proposition is grip-force *control*, not tactile imaging, so
this is an acceptable loss. Redundancy, if ever needed, comes from dual
current-sense paths or a slip-detecting position encoder — not finger wiring.
(Cascade: drop foam references from `ASSEMBLY.md`, `BOM.md`, `UNDERWATER.md`,
`README.md` in the Phase-7 wiring pass.)

## D6 — Selection: weighted multi-criteria + ±50 % sweep across depth tiers
`motor/scripts/selection_score.py`. Weights (stated): sensing 0.25, depth_fit
0.20, torque 0.15, modularity 0.15, integration 0.10, holding_thermal 0.07,
cost 0.08. **Sensing fidelity is a primary axis** (per D4). Result
(`iterations/_selection.json`): smart serial servo wins T1 (14/14 stable) and
**T2 (13/14)**; magnetic-coupling pod wins **T3 (13/14)** — the actuator class
flips with depth, demonstrating modularity quantitatively.

## D7 — PRIMARY = smart serial-bus servo (DYNAMIXEL XW540-T260) — with a budget ladder
Robust T1/T2 winner; native `present_current` + position on one RS-485 bus, holds
a clean torque estimate at stall, IP68 body, ≥ 1.2 N·m cont. (1.9) with stall
headroom (9.5). **Cost honesty:** at ~AUD 1,925 it is the no-compromise flight
part — and the same class has same-bus, same-protocol, same-sensing budget peers:
- **DYNAMIXEL XM540-W270-R (~AUD 766 / USD 494)** — exact Dynamixel-X RS-485
  twin, *more* torque (cont 2.12 N·m, stall 10.6); only loses the IP68 body
  (moot at T2 since the XW540 still needs a canister there). The < $500 "just
  as good" option.
- **Feetech STS3250 (C002, ~AUD 110)** — *deep-budget*; same **SCS TTL
  half-duplex bus** as the STS3215 (it's the larger-motor sibling), same
  `load / position / voltage / temperature` feedback model (load % is the
  torque proxy — calibrated identically per `SENSING.md`), but **50 kg·cm /
  4.9 N·m stall** at 12 V and **~2.45 N·m sustained** post torque-protection,
  which clears the 1.2 N·m design floor that the STS3215 doesn't. K_t ≈
  1.17 N·m/A (= 4.9/4.2 stall A); stall current 4.2 A @ 12 V — adds a wider
  bus/fuse line item than the STS3215 (`ELECTRICAL.md` §3, §6).
- **Feetech STS3215 (C018, ~AUD 34–44)** — rock-bottom; same bus + literal
  `present_current` (SCS reg, 6.5 mA/unit), but a smaller motor: 30 kg·cm /
  2.94 N·m stall, ~0.98 N·m continuous (below the 1.2 target, above the 0.6
  floor — adequate for intermittent mid-face grip-and-hold, not sustained tip
  clamping). The "cheap as chips" T1 dev part.

**One decision, four price points** (XW540-T260 → XM540-W270 → STS3250 → STS3215),
not four designs. T2 still needs a thin pressure canister even for the IP68
XW540 (1 m FW only).

## D8 — FALLBACK = magnetic-coupling drive with a smart-servo/FOC dry pod (T3)
Chosen as the **tier-3 subsea-pitch** fallback (cheap-bench path is already
covered inside D7 by the **STS3250 + STS3215 budget ladder**). No dynamic shaft
seal → depth set only by the dry pod's static seals → same drivetrain from pool
to subsea. Sensing inherited from the pod motor; pole-slip = built-in force
limiter (also caps senseable force). Keeps the subsea-sponsor narrative; is the
genuine #2 at T2.

## D9 — Coupler interface: options (no silent rewrite of `SHAFT_COUPLER_*`)
- **(1) Keep the D-coupler + a printed adapter horn (servo spline → D-socket) —
  CHOSEN for the primary.** Gripper geometry **unchanged**; the adapter is a
  separate printed part. Smart serial servos multi-turn, so the 122.7° travel is
  trivially within range.
- **(2) Magnetic inner-rotor on the input shaft + barrier + outer rotor + pod —
  PROPOSED ONLY (for the D8 fallback).** Changes the coupler region; **not
  implemented**, logged here so the fallback is buildable later without surprise.
- **(3) Re-cut `SHAFT_COUPLER_*` to a different profile —** not adopted; no
  selected actuator requires it.

## D10 — Gear FEA: the crown/pinion is the gripper's structural limit
`DRIVETRAIN.md` / `gear_fea.py`. **Ratio KEPT at 2.667:1** (the STS3215 budget
servo is the floor; dropping it loses 12 N at the tip). The FEA finding dominates
Phase 4: the printed crown/pinion is grossly under-sized for the torque a 12 N grip
needs (working ≈ 0.94 N·m at η 0.5; F_contact ≈ 313 N). Safe input torque
**T_safe ≈ 0.02 N·m as-was**.

- **D10-a — implemented + build-verified:** face-width strengthening
  `PINION_T 4→8`, `CROWN_TOOTH_H 1.6→3.0` (pitch radii / four-bar untouched).
  `check_drivetrain.py` → no new collisions; self-check unchanged. **T_safe → 0.034 N·m**
  (helps ~1.7×, still ≪ working — face width alone is insufficient).
- **D10-b — proposed, NOT implemented (needs CAD-render clearance validation):**
  full module/radius re-size CROWN_RC 8→11, module 0.67→1.83, teeth 24/9→12/6, face 8
  (i_g→2.0 as a by-product). **T_safe ≈ 0.40 N·m (realistic ~0.80)** → ~5–9 N safe
  grip. Specified, not silently written (same rule as D9).
- **Consequence:** T_safe is the **firmware current-limit ceiling** (the sensing
  pivot is the gear protection); both servos' stall ≫ T_safe → current limit
  mandatory on both. The compact right-angle stage caps grip below the finger's
  12 N — a key campaign finding, and the structural argument for the magnetic-
  coupling fallback (pole-slip torque scales with coupling diameter, not housing
  radius). Deliverables re-exported (`export_parts.py`).

---

*Cross-links:* `SELECTION.md`, `SURVEY.md`, `REQUIREMENTS.md`,
`grip/DECISION_LOG.md`, `fea/DECISION_LOG.md`.

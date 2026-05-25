# Motor model — sim physics, assumptions, validation, sensitivity

The analytical model behind the Phase-5 sims, in the spirit of `grip/GRIP_MODEL.md`.

> **RANK / SIZE ONLY — NOT A CALIBRATED ABSOLUTE-NEWTON PREDICTOR.** Every torque↔
> force relation here is exact kinematics from `gripper.py`, but the **efficiency
> band, the PA12-GF allowable, and the contact compliance are estimates, not
> hardware measurements.** The model sizes the actuator, sets the gear current-limit
> ceiling, and ranks object classes by slip risk. It does **not** certify a grip
> force in newtons or a depth rating — those come from `BENCH_TEST.md`. The
> force *readout* (inverse model) is likewise a **relative** signal until calibrated
> against a load cell (`SENSING.md`). This caveat governs the whole campaign.

Reproduce everything:
```bash
python motor/scripts/kinematics_chain.py    # the exact chain (i_g, MA, eta, travel)
python motor/scripts/gear_fea.py            # gear ceiling T_safe
python motor/scripts/torque_chain.py        # motor -> tip force across travel
python motor/scripts/slip_margin.py         # slip margin vs object class (rank-only)
python motor/scripts/holding_stall.py       # holding/stall current + back-drive
python motor/scripts/motor_sensitivity.py   # +/-50% envelope
```

---

## 1. Forward model — command → tip force

The drive chain (derivation in `REQUIREMENTS.md` §1). With input-shaft torque
`T_in`, per-finger tip force at a contact point P:

$$F = T_{in}\cdot \tfrac{i_g}{2}\cdot MA(P)\cdot \eta$$

- `i_g = CROWN_TEETH/PINION_TEETH = 2.667` (crown/pinion reduction). The 1:1 sector
  mesh makes the left gear carry both fingers (the `/2`).
- `MA(P) = |dθ_crank/dx_P|` — the four-bar Jacobian at P, computed numerically on the
  live solver (`kinematics_chain.contact_MA`). 0.0277 (base) → 0.0192 (tip)·mm⁻¹.
- `η` — drivetrain efficiency **band 0.40–0.71** (product of stage estimates, §4).
- **Gear ceiling:** the deliverable force is `min(servo torque, T_safe)` through the
  chain — and Phase 4 found **T_safe binds** (`DRIVETRAIN.md`).

## 2. Inverse model — current → tip force (the sensing pivot)

The forward model run backwards is the force *sensor*. A measured motor current
`I_meas` gives shaft torque `T_sense = K_t·(I_meas − I_0)` (motor torque constant
`K_t`, no-load/friction current `I_0`), back-traced to an estimated tip force:

$$\hat{F} = K_t(I_{meas}-I_0)\cdot \tfrac{i_g}{2}\cdot MA(P)\cdot \eta$$

The forward and inverse models **share the same chain**, so a single drivetrain
characterisation closes the control loop: command a current limit (= a force limit,
and the gear-protection ceiling); read current back (= a force estimate). The
applied details — calibration, noise floor, filtering, limits — are in `SENSING.md`.
Force *resolution*: `ΔF = K_t·ΔI·i_g·MA·η/2`; for the XW540 (`ΔI` = 2.69 mA,
`K_t` ≈ 1.86 N·m/A) this is ≈ 0.005 N·m/step at the shaft → well inside the 0.3 N
tip target (`REQUIREMENTS.md` S1–S2).

## 3. The three sims

| Sim | What it computes | Key output |
|---|---|---|
| `torque_chain.py` | `F(open_norm)` for each servo × geometry, capped by `T_safe`, η-banded | **gear ceiling binds, not the servo**: shipped ≈ 0.5 N, re-size ≈ 4.6 N mid-face |
| `slip_margin.py` | `F_available × μ_hold(object class)` from `grip_model.py` (crosshatch) | **slimy is the worst class** (μ_hold 0.45); rough/ridged best (1.75); rank-only |
| `holding_stall.py` | holding/stall current (`T/K_t`), thermal duty, back-drive check | **back-drivable** → active hold, but holding current **sub-amp**; stall sets the bus budget (XW540 5.1 A, STS3215 2.7 A) |

## 4. Coefficients & provenance

| Symbol | Value | Source |
|---|---|---|
| `i_g` | 2.667 (= 24/9) | `gripper.py` CROWN_TEETH/PINION_TEETH |
| `MA(P)` | 0.0192–0.0277 mm⁻¹ | numeric four-bar Jacobian, `gripper.py` solver |
| `η` | 0.40–0.71 | per-stage estimate band (crown/pinion 0.65–0.85, spur 0.85–0.95, four-bar 0.80–0.90, journals 0.90–0.97) — printed/flooded, `REQUIREMENTS.md` §2 |
| `T_safe` | 0.034 N·m (shipped) / 0.40 (re-size) | gear FEA `gear_fea.py`, allowable 30 MPa PA12-GF |
| `K_t` | 1.86 (XW540) / 1.08 (STS3215) N·m/A | from `present_current` resolution ÷ torque/step, `SURVEY.md` |
| `I_0` | per-unit (calibrated) | no-load/friction current — `SENSING.md` calibration |
| σ_allow | 30 MPa | PA12-GF FDM root-bending, conservative (Polymaker PA6-GF25 84.5 MPa, knockdowns) |

## 5. Validation gates (must pass, like the grip literature gate)

1. **Gear FEA ↔ Lewis cross-check:** pinion at 10 N tip → FEA 40 MPa vs hand
   `6Fh/(bs²)` = 38 MPa → no model bug. ✓ (`gear_fea.py`)
2. **Kinematics ↔ live model:** the chain imports `gripper.py`; the four-bar
   self-check is unchanged by the Phase-4 face-width edits → chain still matches
   the as-built mechanism. ✓
3. **Back-drivability is structural:** spur + four-bar, no worm/self-lock → the
   chain back-drives (the sims assume active hold, consistent). ✓
4. **Force resolution clears the target:** every telemetry-capable candidate
   resolves ≤ 0.02 N·m at the shaft (S2). ✓ (`SURVEY.md`)
5. **Slip ordering is physical:** `grip_model.py` (already literature-gated in the
   grip campaign) ranks slimy/soft worst, rough/ridged best — inherited here. ✓

## 6. ±50% sensitivity envelope (`motor_sensitivity.py`)

Perturbing η, T_safe, MA, K_t each ±50%:

| Conclusion | Result |
|---|---|
| C1 "the gear ceiling binds, not the servo" | **invariant** (no flips) — T_safe ≤ 0.6 still ≪ servo cont. 0.98 |
| C2 "achievable grip stays below the 12 N FEA level" | **invariant** (no flips) — F_mid spans 2.3–6.8 N |
| C3 "holding current stays sub-amp" | **invariant** — 0.11–0.43 A across all perturbations |

The model's headline conclusions do not depend on the soft coefficients; they are
set by structure (the small-radius right-angle stage, the no-worm chain). The
*absolute* grip number does move with η/T_safe — which is exactly why it is reported
as a band and gated on the bench test, not asserted.

Cross-links: `REQUIREMENTS.md`, `DRIVETRAIN.md`, `SENSING.md`, `SELECTION.md`,
`grip/GRIP_MODEL.md`.

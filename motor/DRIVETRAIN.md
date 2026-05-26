# Drivetrain — ratio rationale + gear-tooth FEA under motor stall

Phase 4 revisited the crown/pinion + sector-gear stage against the selected
actuator (`SELECTION.md`) and ran a structural FEA of the printed teeth. The
brief's instinct was right: *the drivetrain in `gripper.py` was a blocky
representative prototype.* This phase replaces representative-by-eye with
analysis — and the headline finding is significant.

> **Headline.** The compact **right-angle crown/pinion stage is the binding
> structural limit of the entire gripper.** At the small radii the housing allows,
> the printed teeth carry far less torque than a 12 N tip grip demands. The fix is
> (a) the **face-width strengthening implemented + build-verified here**, plus (b) a
> **module/radius re-size specified as a proposed engineered target** (needs CAD
> clearance validation), with (c) the **motor current-limit (the sensing pivot)
> enforcing the safe ceiling in firmware**. This is *why* the magnetic-coupling
> fallback (whose pole-slip torque scales with coupling diameter, not housing
> radius) looks strong in retrospect.

Reproduce: `python motor/scripts/gear_fea.py` (→ `motor/iterations/_gear_fea.json`),
`python motor/scripts/check_drivetrain.py` (interference), `python gripper.py`
(four-bar self-check).

---

## 1. Method

- **Headline = 2D plane-stress FEA** of the actual straight-flank tooth (`gear_fea.py`,
  porting the grip Tier-2 Q4 machinery, `grip/scripts/texture_fea.py`). A worst-case
  **tip tangential load** bends a cantilever tooth (root thickness `s_root`, height
  `h`, loaded face width `b_eff` = min of the two mating faces); peak von-Mises is
  sampled in the root band (sharp shoulder → conservative; a real fillet lowers it).
- **Lewis = sanity check only.** The gears are *representative straight-flank, not
  20° involute* (`gripper.py` notes), so the standard Lewis form factor `Y` is
  misleading. Cross-check: pinion at 10 N tip → FEA 40 MPa vs Lewis
  `6·F·h/(b·s²)` = 38 MPa → model consistent, no bug.
- **Allowable σ = 30 MPa** (PA12-GF, the drive-arm + pinion material per `BOM.md`).
  Basis: Polymaker Fiberon **PA6-GF25 = 84.5 MPa** tensile (ISO 527); PA12 base is
  weaker than PA6, FDM 100 %-infill knocks bulk down ~30–40 % (layer adhesion) →
  ~50–65 MPa, and a wet/creep/cyclic safety factor brings the **root-bending
  allowable to a conservative 30 MPa** (cf. the grip campaign's `STRENGTH = 25` for
  eTPU-95A).

## 2. The torque the teeth must carry

From the kinematics (`REQUIREMENTS.md`): a 12 N tip grip needs left-gear torque
`T_left = 2·T_finger ≈ 1247 N·mm`. The crown/pinion **contact force depends only on
the crown pitch radius** (the i_g split is irrelevant to the tooth force):

`F_contact = T_left / CROWN_RC`.

| | ideal (η=1) | realistic (η≈0.5) |
|---|---|---|
| input torque T_motor for 12 N tip | 0.47 N·m | **0.94 N·m** |
| F_contact at the crown/pinion (CROWN_RC = 8) | 156 N | **≈ 313 N** |

(The losses sit *downstream* of the gears, so the crown/pinion sees the full
η-adjusted motor torque — the realistic column is the honest one.)

## 3. Result — T_safe (input-shaft torque at which the weakest tooth reaches 30 MPa)

| geometry | pinion | crown | sector | **binding T_safe** |
|---|---|---|---|---|
| **as-was** (PINION_T 4, CROWN_TOOTH_H 1.6, b_eff 3.2) | 0.02 | 0.02 | 0.21 | **0.02 N·m** |
| **shipped** (PINION_T 8, CROWN_TOOTH_H 3.0, b_eff 6.0) ✓ | 0.04 | 0.034 | 0.21 | **0.034 N·m** |
| **proposed re-size** (CROWN_RC 11, m 1.83, 12/6 teeth, face 8) ⚠ | — | — | — | **0.40 N·m** (realistic ~0.80) |

The sector gear (chunky m≈1.5) is robust; the **crown then pinion** are the weak
links, exactly as expected for a 9-tooth, 0.67-module pinion below the involute
interference limit. **Face-width doubling roughly halves root stress but the tiny
module dominates** — T_safe only rises 0.02 → 0.034 N·m, still ≪ the 0.94 N·m
working torque. **Strengthening alone is insufficient; the module/radius re-size is
required**, and even it (T_safe ≈ 0.4–0.8 N·m) only *approaches* the working torque,
because `CROWN_RC` is capped at ~11 by the sector teeth (which reach R_GEAR + 0.45·H
= 13.35).

## 4. Ratio decision — KEEP 24/9 = 2.667:1

The **rock-bottom budget servo in the ladder** — Feetech STS3215, cont. 0.98 N·m —
is the binding floor: at 2.667:1 it reaches 12 N at the **tip** continuous; dropping
to 2.2:1 it falls to ~11.4 N and the budget option no longer hits 12 N. So the
ratio is **revisited and deliberately kept** — the real Phase-4 change is
*engineered teeth* and a *derived current ceiling*, not a ratio tweak. (The
proposed re-size's geometry happens to land at i_g 2.0 as a by-product of the
bigger module + fewer teeth — a ~5 % grip-at-tip reduction for the STS3215,
accepted as the structural price; the **deep-budget STS3250 (cont ~2.45 N·m)**
and **value-tier XM540-W270 (cont 2.12 N·m)** and **flight XW540-T260 (cont
1.9 N·m)** all have ample torque headroom over the ratio and are not constrained
by it.)

## 5. What was implemented vs proposed

- **Implemented + build-verified (`gripper.py`):** `PINION_T 4.0 → 8.0`,
  `CROWN_TOOTH_H 1.6 → 3.0`. Pitch radii, mesh depth and the four-bar are untouched.
  - `check_drivetrain.py`: **no new collisions** at open = 0/0.5/1 — all moving
    pairs 0 mm³; pinion∩enclosure = 0.476 mm³ is the pre-existing shaft-in-journal
    running fit (the widened pinion at Y −12..−4 sits above the bores at −13.5, so it
    adds nothing; constant across poses ⇒ static).
  - `gripper.py` four-bar self-check **identical** to before (gaps/rotations
    unchanged) — confirms the kinematics are untouched.
- **Proposed / not implemented (numbered option `DECISION_LOG.md` D10-a):** the full
  re-size (CROWN_RC 8→11, module 0.67→1.83, teeth 24/9→12/6, face 8). It ripples
  through ~15 coupled mesh constants (DRIVE_Z, MESH_DEPTH, PINION_TIP, CROWN_Z, the
  crown band radii…) with crown-ring-vs-sector-teeth clearance that **must be
  validated by CAD render** before shipping — so it is specified, not silently
  written, per the campaign rule.

## 6. The current-limit ceiling (the sensing-pivot connection)

T_safe **is** the firmware current-limit ceiling: the actuator is current-controlled
(the sensing pivot), so commanded torque must stay below T_safe. Achievable safe grip
`F_tip ≈ T_safe · i_g · MA · η / 2`:

| geometry | T_safe | safe grip (mid-face, η 0.5) | realistic (×2) |
|---|---|---|---|
| shipped (face-width) | 0.034 N·m | ~0.5 N | ~1 N |
| proposed re-size | 0.40 N·m | ~4.6 N | ~9 N |

So the **shipped representative geometry is a bench/integration article** (grip < ~1 N
before tooth yield); a **functional grip needs the re-size** (~5–9 N), and even then
the right-angle stage caps grip below the finger's 12 N capability. *That is the
campaign finding*, not a number to bury.

## 7. Margin vs the selected servos — current limit is MANDATORY on both

The selected servos can *mechanically* exceed T_safe and destroy the gears on a
fault, so an ESC/firmware current limit is **required for both** (not just the strong
one):

| servo | stall torque | × shipped T_safe | × proposed T_safe |
|---|---|---|---|
| DYNAMIXEL XW540-T260 | 9.5 N·m | ~280× | ~12–24× |
| Feetech STS3250 | **4.9 N·m** | ~144× | ~12× |
| Feetech STS3215 | 2.94 N·m | ~86× | ~4–7× |

All three ≫ T_safe → **"one decision, three *ESC profiles*"**: same torque setpoint
(~0.5 N·m-class motor for a useful grip on the re-sized train), but each servo needs
its own current-limit configured to the same torque ceiling. (Resolution check for
`SENSING.md`: XW540 `present_current` 2.69 mA/step ≈ 0.005 N·m/step — a 0.05 N·m
ceiling is ~10 LSB of headroom: fine but tight; **STS3250 K_t ≈ 1.17 N·m/A** so a
0.05 N·m ceiling = ~43 mA, well inside the load-feedback proxy's resolution; the
STS3215's 6.5 mA/step is the tightest of the three.)

## 8. Why the fallback wins where this can't

The magnetic-coupling fallback (`SELECTION.md` D8) removes this bottleneck: its
**pole-slip torque scales with coupling diameter, not housing radius**, so a
60–80 mm coupling clears the stall band (KTR MINEX-S SA 60/8 = 7 N·m; an 80 mm N52
ring ≈ 6 N·m) with margin the cramped right-angle stage can never reach — and the
pole-slip *is* a mechanical force limiter (it protects the gripper and the specimen).
The gear FEA is the quantitative reason the fallback is a genuine #2, not a courtesy.

> **Honesty.** T_safe is a conservative analytical/2D-FEA estimate (tip-load +
> sharp-shoulder + 30 MPa + no load-sharing ≈ 2–3× conservative); the *realistic*
> column reflects ~2× of that. It is a **ranking/sizing** number that sets the
> current ceiling — not a certified breaking torque. Bench torque-to-failure on a
> printed coupon is the validation (`BENCH_TEST.md`). Cross-links: `SELECTION.md`,
> `DECISION_LOG.md`, `SENSING.md`, `fea/DECISION_LOG.md`.

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
- **Lewis "cross-check" disclosure.** The earlier framing presented "Lewis 40 vs FEA
  38 MPa → no bug" as cross-validation. It isn't: Lewis assumes a 14.5° / 20°
  **involute spur tooth** form factor, and our teeth are *representative straight-
  flank, not involute* (`gripper.py` notes). Two wrong models that agree are not
  the same as one right model being confirmed. The Lewis cross-check is at best a
  same-formulation consistency check (both are 2D Bernoulli cantilevers at the
  pitch radius), not independent validation.
- **Crown gear is a 3D problem, not a 2D plane-stress tooth.** A real crown / face
  gear has a tangential tooth thickness `s_root(r)` that varies with radial
  station, a contact line that sweeps radially under rotation, and a load that
  decomposes into tangential + radial + axial components — none of which the
  shipped 2D plane-stress single-station FEA captures. `gear_fea_radial.py`
  (added on this branch) runs the same 2D FEA at five radial stations across the
  crown's `2·CROWN_TOOTH_H` extent and reports the worst (inner-radius) station.
  Result: the inner-edge slice carries the binding stress and `T_safe(crown)`
  drops from **0.034 N·m → 0.013 N·m** — a **2.6× tighter upper bound** on what
  the printed teeth can carry. This is still not a real 3D solve (the base disk's
  bending compliance and the moving contact line are still missing). The only
  bench-grade ceiling is the printed-coupon torque-to-failure test in
  `motor/BENCH_TEST.md`.
- **Allowable σ = 30 MPa** (PA12-GF, the drive-arm + pinion material per `BOM.md`).
  Basis: Polymaker Fiberon **PA6-GF25 = 84.5 MPa** tensile (ISO 527); PA12 base is
  weaker than PA6, FDM 100 %-infill knocks bulk down ~30–40 % (layer adhesion) →
  ~50–65 MPa, and a wet/creep/cyclic safety factor brings the **root-bending
  allowable to a conservative 30 MPa** (cf. the grip campaign's `STRENGTH = 25` for
  Bambu TPU 95A HF).

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

| geometry | pinion | crown (single-station 2D) | crown (radial 2D, inner edge) | sector | **binding T_safe** |
|---|---|---|---|---|---|
| **as-was** (PINION_T 4, CROWN_TOOTH_H 1.6, b_eff 3.2) | 0.02 | 0.02 | — | 0.21 | **0.02 N·m** |
| **shipped** (PINION_T 8, CROWN_TOOTH_H 3.0, b_eff 6.0) ✓ | 0.04 | 0.034 | **0.013** | 0.21 | **0.013 N·m** (radial) / **0.034 N·m** (single-station) |
| **proposed re-size** (CROWN_RC 11, m 1.83, 12/6 teeth, face 8) ⚠ | — | — | — | — | **0.40 N·m** (single-station conservative) |

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
  through ~15 coupled mesh constants (DRIVE_Z, PINION_TIP, CROWN_Z, the
  crown band radii…) with crown-ring-vs-sector-teeth clearance that **must be
  validated by CAD render** before shipping — so it is specified, not silently
  written, per the campaign rule.

### 2026-06 tooth-FORM upgrade (branch `feat/gearbox-linkage-redesign`)

The gearbox-polish pass replaced the **representative straight-flank** teeth with
**true involutes** where it matters, *without* re-sizing — so this whole FEA chain
stays valid as-is:

- **Spur sector pair (A_L↔A_R)** and the **input pinion** are now sampled-involute
  (25° pressure angle, 0.15 mm designed circular backlash, the 9-tooth pinion
  profile-shifted x=+0.25 + tip-truncated to clear undercut). Conjugate flanks roll
  instead of tip-gouging → the visible mesh ripple/backlash is gone.
- **CROWN_RC (8), PINION_RP (3), CROWN_TEETH (24), PINION_TEETH (9) are HELD**, so
  `CROWN_RC/PINION_RP = 24/9 = 8/3` is unchanged and **T_safe, the torque chain,
  slip margin and selection scores are untouched** (no campaign re-run). The pinion
  tip stays < the journal bore, so the one-piece input shaft still installs
  pinion-first — the reason the bigger D10-a re-module was *not* taken here.
- The **crown stays representative proud radial blocks** (now phase-locked to the
  involute pinion with `PINION_PHASE_DEG`, and pitch-plane-tangent via the new
  `DRIVE_Z`), deliberately kept block-form so the conservative straight-cantilever
  `gear_fea*.py` model still bounds it — the crown remains the binding link at
  **T_safe ≈ 0.013 N·m (radial)**. A fully conjugate face-gear crown is the open
  follow-on. Re-running `gear_fea*.py` on the involute pinion only *raises*
  `T_safe(pinion)` (stronger root), it does not move the binding crown bound.

## 6. The current-limit ceiling (the sensing-pivot connection)

T_safe **is** the firmware current-limit ceiling: the actuator is current-controlled
(the sensing pivot), so commanded torque must stay below T_safe. Achievable safe grip
`F_tip ≈ T_safe · i_g · MA · η / 2`:

| geometry | T_safe (2D, by which model) | safe grip per finger (band over η, MA) |
|---|---|---|
| shipped (single-station 2D)   | 0.034 N·m | **0.35 – 0.73 N** |
| shipped (radial 2D inner edge)| **0.013 N·m** | **0.13 – 0.28 N** |
| proposed re-size (single-station) | 0.40 N·m | **4.2 – 8.7 N** |

So the **shipped representative geometry is a bench/integration article** (grip
≪ 1 N before crown-tooth yield); a **functional grip needs the re-size**
(~4–9 N), and even then the right-angle stage caps grip below the finger's 12 N
*stress-probe* capability (which is itself the FEA-comparison load, not an
operating force — see `docs/TESTING_AND_SIMULATION.md` A.8). The live force band
is regenerated by `motor/scripts/drivetrain_force_envelope.py`. *That is the
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

## 9. Self-similar scaling — T_safe ~ k³, tip force ~ k² (the gear is *still* the limit)

`gripper.py` now carries a global self-similar scale (`GRIPPER_SCALE`, default 1.0).
At `GRIPPER_SCALE = k` every linear gear dimension scales by `k` while the tooth
**counts are held**, so the module scales `k` and the mesh ratio `i_g = 24/9 =
2.667:1` is preserved (true mechanical similitude). All four chain scripts
(`gear_fea.py`, `gear_fea_radial.py`, `drivetrain_force_envelope.py`,
`kinematics_chain.py`) read `gripper.py` for their dims, so `GRIPPER_SCALE=k`
propagates automatically — no per-script parameter editing.

The power laws fall out of dimensional analysis and are confirmed numerically:

- **Tooth root-bending capacity `T_safe ~ k³`.** Allowable tooth force `F_allow ∝
  σ_allow · b · s_root² / h ∝ k²` (face width `b ~ k`, root thickness `s_root ~ k`,
  height `h ~ k`), and the lever (`PINION_RP ~ k`) adds one more `k` →
  `T_safe = F_allow · lever ~ k³`. σ_allow (material) is held.
- **Mechanical advantage `MA ~ 1/k`.** `MA = |dθ_crank/dx_P|`: the crank angle is
  similitude-invariant, the contact displacement `dx_P ~ k`, so `MA ~ 1/k`.
- **Deliverable tip force `F ~ k²`.** `F = T_safe · i_g · MA / 2 · η`, with `i_g`
  and `η` scale-invariant (counts + angles held) → `F ~ k³ · k⁻¹ = k²`.

Reproduce: `GRIPPER_SCALE=k PYTHONPATH=. python motor/scripts/gear_fea_radial.py`
(and `gear_fea.py`, `drivetrain_force_envelope.py`). Result JSONs per scale live in
`variants/scale_<k>x/fea/`; the combined summary is
`variants/scale_scaling_summary.json`.

### 9.1 Headline table (radial 2D inner-edge bound — the self-similar basis)

The **radial 2D crown FEA** (`gear_fea_radial.py`, the binding inner-edge slice) is
the scaling headline: it is fully geometry-driven from `gripper.py`, so it reads the
power law cleanly. The single-station 2D (`gear_fea.py`) independently confirms `k³`.

| `GRIPPER_SCALE` | `T_safe` (radial 2D) | `T_safe` (single-station 2D) | per-finger force band | T_safe ratio vs 1× | force-hi ratio vs 1× |
|---|---|---|---|---|---|
| **1.0×** | 0.0131 N·m | 0.034 N·m | **0.14 – 0.28 N** | 1.00 (k³ = 1.00) | 1.00 (k² = 1.00) |
| **1.5×** | 0.0442 N·m | 0.113 N·m | **0.31 – 0.64 N** | 3.37 (k³ = 3.375) | 2.25 (k² = 2.25) |
| **2.0×** | 0.1048 N·m | 0.268 N·m | **0.55 – 1.13 N** | 8.00 (k³ = 8.00) | 4.00 (k² = 4.00) |

The fits land on `k³` / `k²` to three significant figures. **`T_safe` and the force
band are quoted on the *same* radial 2D basis** — they are not mixed across models.

### 9.2 Servo headroom — the ratio SHRINKS with scale, but the gear is still the limit

`T_safe` grows as `k³` while servo stall torque is fixed (a bigger gripper does not
get a bigger motor for free), so the **stall ÷ T_safe ratio shrinks with scale**.
That ratio is *not* comfort headroom — it is the **over-torque danger**: how badly a
servo would smash the printed crown on a firmware/limit fault. Smaller is *safer* in
that sense, but it is still enormous:

| servo | stall | × T_safe @ 1.0× | × T_safe @ 1.5× | × T_safe @ 2.0× |
|---|---|---|---|---|
| DYNAMIXEL XW540-T260 | 9.5 N·m | ~725× | ~215× | ~91× |
| Feetech STS3250 | 4.9 N·m | ~374× | ~111× | ~47× |
| Feetech STS3215 | 2.94 N·m | ~224× | ~67× | ~28× |

Even at 2.0× the weakest servo in the ladder (STS3215) still over-torques the gear by
~28×; the crossover where a servo could *no longer* exceed `T_safe` is around `k ≈ 6`
(`T_safe ∝ k³` reaches ~2.94 N·m near `k = 0.0131·6³·...`, i.e. far beyond any
printable size). **Conclusion: the gripper is gear-limited at every scale in
[1.0, 2.0], and the firmware current-limit remains the mandatory gear-protection
mechanism at all scales** — the same "one decision, N ESC profiles" posture, just
with the per-scale `T_safe` setpoint from the table above. The force *grows* with
size (good — a 2× gripper delivers ~4× the per-finger clamp force, 0.55–1.13 N vs
0.14–0.28 N), but it is **still capped far below the finger's 12 N stress-probe
capability**, so the qualitative finding of §6 is scale-invariant: a *functional*
absolute grip still needs the module/radius re-size, not just a bigger envelope.

### 9.3 Honesty: what does NOT scale cleanly, and the high-fidelity follow-up

- **`gear_fea_3d.py` is NOT self-similar as configured.** It hardcodes `DISK_T =
  4.0 mm` (absolute, not `×SCALE`) and meshes at **absolute** gmsh sizes
  (`mesh_max=0.6, mesh_min=0.25`), so its mesh density (988 → 1567 → 2658 nodes) and
  its disk-to-tooth proportion both change with `k`. Its `T_safe` therefore reads
  0.0161 → 0.140 → 0.326 N·m, a ratio of ~8.7× / ~20× vs `k`, far above `k³`. This is
  a **tooling artifact, not physics** — the 3D model simply cannot read the power law
  while its disk and mesh are pinned to absolute sizes. The shipped 1× repo posture
  (per `docs/OVERNIGHT_FIXES.md`) treats 3D as the better *physics* at 1×; that judgement
  stands for the 1× point, but for the **scaling study the radial 2D bound is the
  honest basis** because it is the one that is actually self-similar. The 3D
  per-scale JSONs are retained in `variants/scale_<k>x/fea/_gear_fea_3d.json` flagged
  as non-scaling.
- **High-fidelity re-run warranted (follow-up):** make `gear_fea_3d.py`
  self-similar (`DISK_T = 4.0 * g.SCALE`; gmsh `MeshSizeMax/Min` scaled by `SCALE`)
  and re-run at `k ∈ {1.0, 1.5, 2.0}` on a GPU workstation (RTX 3070)
  to confirm the 3D solve also recovers `k³` once disk + mesh scale with the part.
  This is the clean way to cross-check the radial 2D headline at higher fidelity; it
  is left for the GPU workstation because the 3D mesh + build123d STEP step is the heavy part.
- **`torque_chain.py` does NOT scale.** Its `T_SAFE` and `SERVOS` are **hardcoded 1×
  literals** (lines 33–37); it only imports `kinematics_chain` for `MA`/`i_g`. Run at
  `GRIPPER_SCALE=k` it therefore pairs `k`-scaled `MA` (which falls as `1/k`) against
  *fixed* 1× `T_safe`, producing tip-force curves that **shrink** with scale — the
  exact opposite of the real `k²` law. It is a **1× illustration plotter only**; its
  scaled output must not be quoted. To make it scale you would replace the `T_SAFE`
  literals with the per-scale radial values from §9.1 (a one-line-per-scale edit, left
  optional since the force-envelope script already delivers the correct per-scale
  band).
- **All bounds remain 2D/linear upper-bound estimates.** Scaling does not change the
  §-Honesty caveats: straight-flank-vs-involute edge-loading, no base-disk compliance
  in 2D, no moving contact line. The bench torque-to-failure on a printed coupon
  (`BENCH_TEST.md`) is the only validated ceiling, at every scale.

> **Honesty.** T_safe is a 2D-FEA upper-bound estimate. The crown is a 3D face
> gear (a 2D plane-stress single-station tooth model is partial; the
> radial-station integration on this branch is tighter but still 2D), the
> teeth are "representative straight-flank" not involute (so they will
> edge-load and gall in PA12-GF rather than roll cleanly), and the
> base-disk bending compliance + moving contact line are not modelled. The
> shipped value reads "0.013 N·m (radial 2D) / 0.034 N·m (single-station 2D)"
> — both are conservative upper bounds, and the true ceiling is even lower.
> Bench torque-to-failure on a printed coupon is the validation
> (`BENCH_TEST.md`). Cross-links: `SELECTION.md`, `DECISION_LOG.md`,
> `SENSING.md`, `fea/DECISION_LOG.md`.

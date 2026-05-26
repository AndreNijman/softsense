# Overnight branch — `fix/honest-headlines-overnight`

Andre asked for an overnight fix-up of the critical-review issues in the
gripper-cad project. This file is the punch-list mapping each issue to the
commit(s) that addressed it.

Read this top-down to audit the changes; each commit is small and focused.

## Critical — the headlines the prior docs couldn't survive

### #1. The 12 N grip force is unreachable by the shipped drivetrain
**Status: fixed (re-anchored, not removed).**

- New `motor/scripts/drivetrain_force_envelope.py` propagates the gear-tooth
  `T_safe` through the kinematics chain (efficiency band 0.40–0.71, MA
  0.020–0.023/mm) to compute the per-finger force band the drivetrain can
  *safely* deliver: **0.14 – 0.28 N (radial 2D crown bound)** /
  0.35 – 0.73 N (single-station 2D bound) / 4.2 – 8.7 N (proposed re-size).
  Output lives in `motor/iterations/_drivetrain_force_envelope.json`.
- 12 N is now framed everywhere as a **stress-probe load** used to rank
  finger designs in software at a closure the FEA can reach, *not* an
  operating force the drivetrain delivers. The published 5.7 – 8.6× margins
  are *worst-case-load* margins; the implied margins at the operating force
  are **~100 – 700×**.
- Propagated through: `README.md`, `docs/TESTING_AND_SIMULATION.md` (A.8,
  A.12, C.4, D), `fea/FEA.md`, `fea/UNIVERSAL_FINGER.md` (§2 callout, §5, §6),
  `motor/DRIVETRAIN.md`, `motor/MOTOR_STUDY.md` §5, and the docstring +
  inline comments in `fea/scripts/iter_harness.py`. The "12 N" number is
  kept because re-running ~90 finger-FEA solves at the corrected load is
  costly and the design ranking is preserved at any sub-`T_safe` load (small-
  strain elastic regime) — but it is no longer presented as an operating
  force or a structural mandate.

Commits: `79bc061`, `8ad12ec`, `c84faf3`, `76ecc7a`.

### #2. Crown gear analysed as 2D plane-stress spur tooth
**Status: tightened (still 2D, but with explicit honesty about the gap to a real 3D solve).**

- New `motor/scripts/gear_fea_radial.py` runs the same 2D plane-stress FEA
  used in `gear_fea.py` at five radial stations across the crown's
  `2·CROWN_TOOTH_H` extent (r = 5 .. 11 mm for the shipped CROWN_RC=8). The
  inner-edge station has s_root = 0.65 mm (vs 1.05 mm at the pitch radius)
  and is the binding station. Re-derived crown T_safe **drops from 0.034
  N·m to 0.013 N·m** — a 2.6× tighter upper bound.
- `motor/DRIVETRAIN.md` §1 now explicitly says the crown is a 3D problem,
  what's still missing (base-disk compliance, moving contact line,
  tangential+radial+axial decomposition, straight-flank gall-vs-roll in
  PA12-GF), and that the "Lewis 40 vs 38 MPa → no bug" cross-check is a
  same-formulation consistency check (both are 2D Bernoulli cantilevers),
  not independent validation. The only bench-grade ceiling is
  `motor/BENCH_TEST.md`.

Commit: `8ad12ec`.

### #3. "Two independent FEA cross-validate at 2.7 MPa" is misleading
**Status: demoted to "order-of-magnitude consistency check".**

- `docs/TESTING_AND_SIMULATION.md` §A.11 now contains an apples-to-apples
  comparison table: 3D uses ν=0.42, displacement-controlled, rigid contact,
  hits 12 N; 2D uses ν=0.45, force-controlled patch, *no contact*, hits a
  load-control limit point at 5.4 N (≈5.7 N snap-instability threshold).
  The doc says explicitly: the two solves *don't solve the same problem*,
  so this is a consistency check rather than a true cross-validation.
- `fea/FEA.md` §1 tabulates the same differences and removes "cross-
  validate each other" from the headline.
- `docs/TESTING_AND_SIMULATION.md §D Established` calls it a "cross-
  formulation consistency check, not an independent re-derivation".

Commit: `79bc061`.

### #4. Linear tets + nearly-incompressible TPU + ν=0.42 — volumetric locking
**Status: locking-diagnostic ν-sweep launched, results pending.**

- `fea/scripts/param_sweep.py` and `fea/scripts/iter_harness.py` env-var
  overrides (GRIPPER_NU, GRIPPER_NLAYERS, GRIPPER_NSTEPS_OVERRIDE,
  GRIPPER_E_TPU, GRIPPER_REPORT_MODE, …) make it possible to re-run the
  shipped finger at ν ∈ {0.40, 0.42, 0.45, 0.48} without touching the
  validated production solver. Four runs were launched at NSTEPS=12 (to
  fit overnight); the results live under
  `fea/iterations/_locking_nu{40,42,45,48}/metrics.json` and
  `fea/iterations/_sweeps_log/locking_nu*.log` once they complete.
- `fea/FEA.md` "Locking diagnostic" section was added; it currently
  describes the expected pattern (force shifts monotonically with ν, peak
  vM shifts < 15 %, the truss-vs-flexure margin narrows from ~12 % to ~7 %
  across ν = 0.42 → 0.48 — see the *Final-sweep results* commit below for
  the actual numbers). The fix is partial mitigation only; a real cure
  (B-bar / mean-dilatation / mixed u-p / P2 tets) is out of scope for
  one overnight branch.

Commits: `c84faf3` (sweep enablers); the data + final write-up commit will land when the runs finish.

## Major

### #5. Literature-gate is self-referential
**Status: robustness diagnostic added; honest framing in docs.**

- New `grip/scripts/baseline_gate_robustness.py`: each
  [PLACEHOLDER]/[ESTIMATE] coefficient is perturbed ±50% from default, the
  gate is re-run, and the pass rate reported. Result: **89/90 (99 %) of
  perturbed settings still pass** — the gate isn't tightly tuned to specific
  coefficients in a ±50% neighborhood. A harsher "zero the placeholders"
  test FAILS: removing EDGE_PIERCE, C_EDGE, C_HYS, SUCT_GAIN and tiny-ing
  CAP0 (i.e. letting only cited Briscoe–Tabor / tyre-wet-skid terms drive
  the model) breaks "tread beats ridges", confirming the placeholder terms
  *are* doing real work.
- `grip/GRIP_MODEL.md` Validation § now frames the gate as a
  sufficient-condition test (the model can be fit) not a necessary one
  (the model generalises), notes that a true out-of-sample test (a new
  reference pattern the model has never seen) has not been done, and
  disputes the published μ values the gate reproduces (smooth-wet μ ≈ 0.07
  is the *dynamic aquaplaning floor*, not static; sucker μ ≈ 1.11
  conflates suction with sliding friction).
- `grip/GRIP_TEXTURE.md` §2 has a matching callout.

Commit: `92af096`.

### #6. Tier-2 texture FEA validates only what doesn't drive the ranking
**Status: demoted explicitly in docs.**

- `grip/GRIP_MODEL.md` Validation §2 now says:
  - The φ_eff "validation" under rigid-platen / flat-top-post / plane-strain
    is essentially **tautological** — a post that can't bulge sideways into
    the gap is *expected* to show load-independent φ_eff. A different test
    (laterally-confined platen, hyperelastic post, higher pressure) might
    give a different answer; we didn't run that test.
  - The durability `6·τ·AR` check is useful for design margins, not for
    ranking.
  - The **friction physics** and **Reynolds drainage** — the ranking-driving
    terms — are NOT touched by Tier-2.
  - "Tier-2 validates structural sub-models, NOT ranking physics."
- `grip/GRIP_TEXTURE.md` §6 mirrors this.

Commit: `92af096`.

### #7. The "31/31 invariant winner" claim hides a swap
**Status: documented in README + GRIP_TEXTURE (already done in §5; README added).**

- `README.md` (top-of-file Fin-Ray paragraph) now says the model's raw
  winner is the octopus-sucker (31/31 invariant), the shipped crosshatch
  wins 23/31 only among tileable families, and the override (sucker can't
  tile a 10 mm blade) was a geometric / engineering-judgement call applied
  externally — *not* a coefficient that demotes the sucker.
- `grip/GRIP_TEXTURE.md` §5 already had this honestly framed.

Commit: `cd58e02`.

### #8. fea3d_finger.py is a duplicate "production" 3D solver
**Status: collapsed to a deprecation stub.**

- `fea/scripts/fea3d_finger.py` is now a stub that prints a pointer to
  `iter_harness.py` and exits 64. The full parameter mapping (the
  ν/K_PEN/press_max/steps drift) is in the new docstring.
- `iter_harness.py` is now portable: `GRIPPER_REPO` env var with a
  file-relative fallback, plus the env-var overrides for ν / NLAYERS /
  E_TPU / REPORT_MODE / TARGET_GRIP / PRESS_AT_REPORT /
  NSTEPS_OVERRIDE.

Commit: `c84faf3`.

### #9. Doc claims FᵀF eigendecomp; code uses SVD
**Status: doc corrected.**

- `docs/TESTING_AND_SIMULATION.md` §A.3 now correctly says the polar
  decomposition is done via SVD (F = UₛΣVᵀ → R = UₛVᵀ), with the last
  Uₛ-column flip if det(R) < 0. SVD is more robust than FᵀF eigen for
  near-rank-deficient F.

Commit: `cd58e02`.

### #10. Force-targeted reporting is "THE methodology"; default is closure-based
**Status: doc/code disclosure added.**

- `iter_harness.py` REPORT_MODE comment block now explicitly discloses the
  doc/code split: the doc presents force-targeted as the fairness
  methodology, but the production code default is `REPORT_MODE="closure"`
  at `PRESS_AT_REPORT = 8.0` mm. Most per-family universal-score numbers in
  this repo were generated with closure mode; force-targeted was used
  selectively in the swarm. Toggleable via `GRIPPER_REPORT_MODE` env var.
- `docs/TESTING_AND_SIMULATION.md` §A.8 has the same disclosure.
- `fea/UNIVERSAL_FINGER.md` §2 has the same disclosure.

Commits: `c84faf3`, `79bc061`.

### #11. "Gecko / Cattaneo–Mindlin" partial-slip overreach
**Status: rewritten as "monotone partial-slip surrogate [ESTIMATE]".**

- `grip/scripts/grip_model.py` `eta_edge()` docstring and the §5 comment
  now say: this is a monotone surrogate; gecko adhesion is vdW on
  hierarchical fibrils; Cattaneo–Mindlin is `1−(T/μN)^(2/3)` for a
  Hertzian sphere; the *direction* of the effect is supported by tyre-
  tread / tree-frog literature but the *functional form* is engineering
  convenience.
- `docs/TESTING_AND_SIMULATION.md` §B.3 point 5 rewritten the same way.

Commits: `cd58e02`, `92af096`.

## Minor

### #12. TPU 35 → 25 MPa derate provenance
**Status: provenance documented honestly.**

- `docs/MATERIALS.md` and `docs/PRINT_PROFILE_P1S_TPU.md` §5 now say
  eSUN's published TDS quotes ~30 MPa (likely printed, not IM); the
  "35 MPa IM → 25 MPa printed via FDM derate" derivation may double-count;
  25 MPa is retained as a *conservative lower-bound estimate*, not a
  measured ceiling. Bench validation on a printed coupon is in
  `motor/BENCH_TEST.md`.

Commit: `c84faf3`.

### #13. E_TPU = 40 MPa as a single linear modulus
**Status: secant-modulus assumption documented; rank-only claim retained.**

- `docs/TESTING_AND_SIMULATION.md` §A.3 + §A.12 acknowledge TPU is strongly
  nonlinear (1 %-strain secant 2–4× different from 10 %-strain secant) and
  that the rib bending strains span 3–8 % so a single linear modulus is a
  working approximation.
- `docs/PRINT_PROFILE_P1S_TPU.md` §5 makes the same point and adds an
  honest caveat that the "modulus-insensitive at fixed grip force" claim
  holds in `REPORT_MODE="grip"` (force-targeted) but the production default
  is `REPORT_MODE="closure"`; under closure the absolute stress shifts
  with E. The design ranking survives either way.

Commits: `79bc061`, `c84faf3`.

### #14. Newton convergence flag not persisted
**Status: persisted.**

- `iter_harness.py` now persists per-step `newton_iters_per_step`,
  `did_converge_per_step`, `residual_final_per_step`, plus the overall
  `did_converge_all_steps`, `n_steps_not_converged`,
  `newton_iters_max_used`, `newton_iters_mean`, `newton_max_iters`, and
  `newton_tol_rel` in `metrics.json`. Also persists the run conditions
  (`report_mode`, `target_grip_stress_probe_N`, `press_at_report_mm`,
  `nu_used`, `e_tpu_used`, `nlayers_used`).

Commit: `c84faf3`.

### #15. "Frictionless = conservative" framed as one-sided
**Status: reframed.**

- `docs/TESTING_AND_SIMULATION.md` §A.4 + `fea/FEA.md` Honesty §:
  frictionless lower-bounds the *holding force* (true) but its effect on
  the *wrap claim* is sign-indeterminate — a frictionless surface lets the
  finger slide tangentially during wrap, generally helping no-peel
  coverage.

Commit: `cd58e02`.

### #16. NLAYERS = 3 mesh-convergence sweep
**Status: sweep launched (NLAYERS ∈ {3, 5, 8}), results pending.**

- `fea/scripts/param_sweep.py` + the env-var overrides in
  `iter_harness.py` enabled the sweep. Three runs were launched at
  NSTEPS=12; results live under `fea/iterations/_mesh_nl{3,5,8}/metrics.json`
  and `_sweeps_log/mesh_nl*.log` once they complete. The data + final
  write-up commit will land when the runs finish.

Commit: `c84faf3` (enabler); final data commit pending.

---

## What is NOT addressed in this branch (deliberately)

- **A real 3D crown FEA.** The radial-station 2D check (`gear_fea_radial.py`)
  is a tighter upper bound but still doesn't model the moving contact line,
  base-disk compliance, or load decomposition. The doc says so explicitly.
  The only real ceiling is the printed-coupon bench test in
  `motor/BENCH_TEST.md`.
- **A B-bar / mixed-u-p / P2 finger FEA.** The locking-diagnostic sweep
  quantifies the impact of ν on the existing linear-tet model; it doesn't
  fix the model. A proper element-formulation change is out of scope for
  one overnight branch.
- **Out-of-sample literature gate.** The robustness diagnostic shows the
  current gate is robust ±50%; a true out-of-sample test requires sourcing
  a new bio-inspired wet-grip reference pattern with parameters in our
  printable envelope. Out of scope overnight.
- **Re-running the 90-solve universal-finger swarm at the corrected
  operating force.** The rank ordering is preserved in the small-strain
  elastic regime; re-running the swarm at sub-Newton forces would cost
  hours of MSI compute and produce numerically identical rank orderings.
  The doc now flags this explicitly.

These are all candidates for a future pass.

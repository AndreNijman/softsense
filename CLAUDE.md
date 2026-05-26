# gripper-cad — working notes for agents & people

## ⚙️ COMPUTE POLICY (read this first)

**Heavy / high-quality runs → the MSI. Everything else → local.**

- **Run on the MSI** (`ssh andremsi`, an RTX-3070 laptop set up as a remote FEA/render
  node — see `docs/MSI_REMOTE.md`) for: high-resolution / high-quality FEA, full
  multi-object batteries, big sweeps, long render jobs — anything intensive, so the
  main machine isn't tied up.
- **Stay local** for: quick iteration, single screens, edits, doc work, light renders.
- The MSI has the full stack in `C:\Users\andre\cad-venv` (build123d, gmsh, scipy,
  numpy, matplotlib, cupy) and a repo clone at `C:\Users\andre\gripper-cad`. Exact
  commands + the gotchas (cmd.exe `set "VAR=1"` quoting; nvrtc DLL on PATH) are in
  `docs/MSI_REMOTE.md`.
- **GPU note:** the solver has a CuPy GPU backend (`GRIPPER_FEA_GPU=1`) but at the
  gripper's mesh sizes (≤25k DOF) **CPU is faster** (GPU is overhead-bound; crossover
  is ~100k+ DOF). Keep CPU default; GPU is only worth it for future very-high-res work.

## Orientation

- `gripper.py` — the parametric model (source of truth): geared four-bar + Fin Ray
  fingers + flooded enclosure. Env: `GRIPPER_OPEN` 0–1, `GRIPPER_FINGER_SCALE` 0.6–2.5.
- `fea/` — FEA tooling + studies. `scripts/eval_finger.py` (universal multi-shape
  scorer), `scripts/iter_harness.py` (3D corotational contact solver, CPU+GPU),
  `scripts/render_wrap.py` (renders). Studies: `UNIVERSAL_FINGER.md` (finger design),
  `SCALABILITY.md`, `DECISION_LOG.md` (full history).
- `grip/` — grip-texture study + tooling. `scripts/grip_model.py` (Tier-1 wet-grip
  surrogate + coefficients), `scripts/sweep.py`/`sensitivity.py` (search +
  ±50% robustness), `scripts/texture_fea.py` (Tier-2 2D contact FEA),
  `scripts/baseline_validate.py` (literature gate). Study: `GRIP_TEXTURE.md`,
  `DECISION_LOG.md`, `GRIP_MODEL.md`. Shipped texture = crosshatch micro-posts
  (`FR_GRIP_*` in `gripper.py`).
- `motor/` — actuator selection + sensing + ROV integration. `scripts/kinematics_chain.py`
  (input-torque↔tip-force chain), `gear_fea.py` (gear-tooth FEA → `T_safe`),
  `torque_chain.py`/`slip_margin.py`/`holding_stall.py` (sims), `selection_score.py`
  + `motor_sensitivity.py` (weighted pick + ±50%). Study: `MOTOR_STUDY.md`; also
  `REQUIREMENTS.md`, `SURVEY.md`, `SELECTION.md`, `DRIVETRAIN.md`, `MOTOR_MODEL.md`,
  `SENSING.md`, `ELECTRICAL.md`, `ROV_INTEGRATION.md`, `BENCH_TEST.md`,
  `FAILURE_MODES.md`, `DECISION_LOG.md`, `INTERFACES.md`. **Sensing pivot:** the actuator is the
  grip-force sensor (motor current → torque → tip force); the printed crown/pinion
  is the structural limit (`T_safe`) and the motor current-limit is its protection.
  Selected: smart serial servo (DYNAMIXEL XW540-T260) primary, magnetic-coupling
  dry-pod fallback. The drivetrain (gear teeth) in `gripper.py` is **unlocked**;
  finger/texture/print-profile are locked.
- `motor/interfaces/` — mounting-interface dossiers (research only, no CAD yet):
  Reach Bravo 7 / Alpha 5, ISO 9409-1 cobot flange, Schilling/Kraft work-class
  wrist, fixed BlueROV2-chassis mount. Top-level comparison in `motor/INTERFACES.md`.
  Three adapters P0-ready; Alpha 5 + Schilling-bolt-on blocked on NDA dims.
- `docs/PRINT_PROFILE_P1S_TPU.md` + `profiles/` — print the fingers in **eSUN eTPU-95A on a
  Bambu P1S, 0.4 mm hardened nozzle** (importable Bambu Studio filament+process).
- `regen.sh` — rebuild all derived artifacts (poses, parts, plates, heroes, GIF).

## Conventions
- Conventional Commits; no AI attribution in commit messages.
- The finger FEA assumes **100 %-dense walls** (the print spec); material is
  eSUN eTPU-95A (~25 MPa printed strength, E≈40 MPa estimate, ν=0.42).

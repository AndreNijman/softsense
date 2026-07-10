# softsense — working notes for agents & people

## 📌 STATUS: PROJECT COMPLETE (July 2026)

The competition is over — **the SoftSense project won a prize.** This repo is
the finished, consolidated record (renamed from `gripper-cad`; the Orange Pi
controller worktree/branches are merged in under `opi/`). Treat the design as
**frozen**: finger, texture, print profile, bevel drivetrain and controllers
are all final. Future work here is archival/maintenance — docs, renders,
reproductions — not design iteration.

## ⚙️ COMPUTE POLICY (if heavy work ever comes back)

**Heavy / high-quality runs → the MSI. Everything else → local.**

- **Run on the MSI** (`ssh andremsi`, an RTX-3070 laptop set up as a remote FEA/render
  node — see `docs/MSI_REMOTE.md`) for: high-resolution / high-quality FEA, full
  multi-object batteries, big sweeps, long render jobs. Full stack in
  `C:\Users\andre\cad-venv`; repo clone at `C:\Users\andre\gripper-cad` (pre-rename
  name until re-cloned). Exact commands + gotchas in `docs/MSI_REMOTE.md`.
- **Stay local** for: quick iteration, single screens, edits, doc work, light renders.
- **GPU note:** the solver has a CuPy GPU backend (`GRIPPER_FEA_GPU=1`) but at the
  gripper's mesh sizes (≤25k DOF) **CPU is faster**; crossover is ~100k+ DOF.

## Orientation

- `gripper.py` — the parametric model (source of truth): geared four-bar + Fin Ray
  fingers + flooded enclosure + **true 90° bevel drive** (12/6, module 1.8) + the
  **Feetech STS3250 25T spline socket** in the Ø15 input shaft. Env: `GRIPPER_OPEN`
  0–1, `GRIPPER_FINGER_SCALE` 0.6–2.5, `GRIPPER_SCALE` (self-similar scale-up).
- `fea/` — FEA tooling + studies. `scripts/eval_finger.py` (universal multi-shape
  scorer), `scripts/iter_harness.py` (3D corotational contact solver, CPU+GPU),
  `scripts/render_wrap.py` (renders). Studies: `UNIVERSAL_FINGER.md`,
  `SCALABILITY.md`, `DECISION_LOG.md` (full history).
- `grip/` — grip-texture study + tooling. Tier-1 wet-grip surrogate
  (`scripts/grip_model.py`), sweep + ±50% sensitivity, Tier-2 2D contact FEA,
  literature gate. Study: `GRIP_TEXTURE.md`, `DECISION_LOG.md`, `GRIP_MODEL.md`.
  Shipped texture = crosshatch micro-posts (`FR_GRIP_*` in `gripper.py`).
- `motor/` — actuator selection + sensing + ROV integration. **Sensing pivot:** the
  actuator is the grip-force sensor (motor current → torque → tip force); the
  printed drivetrain is the structural limit (`T_safe`), the motor current-limit its
  protection. Study selection: XW540-T260 (depth-rated primary); the built
  demonstrator runs the STS3250 direct-spline mount. Docs: `MOTOR_STUDY.md`,
  `REQUIREMENTS.md`, `SURVEY.md`, `SELECTION.md`, `DRIVETRAIN.md`, `MOTOR_MODEL.md`,
  `SENSING.md`, `ELECTRICAL.md`, `ROV_INTEGRATION.md`, `BENCH_TEST.md`,
  `FAILURE_MODES.md`, `DECISION_LOG.md`, `INTERFACES.md`, `POWER_SUPPLY.md`
  (⚠️ BR2 4S full-charge 16.8 V > XW540's 14.8 V max — buck is MANDATORY on BR2).
- `motor/interfaces/` + `motor/cad/adapters/` — mounting-interface dossiers and all
  7 parametric adapters (shared gripper-side mating in `_base.py`: 4×M4 at
  (±38, ±8, 0), shaft clearance Ø16 at X=-12).
- `firmware/` — the **shipped controller**: ESP32 (Waveshare General Driver) Wi-Fi-AP
  web UI + stop-on-load + NVS calibration; `firmware/gamepad/` DualSense jog bridge.
- `opi/` — Orange Pi controllers (3 LTS AP appliance + Ethernet-only H3 variant),
  the ESP32's predecessor; complete and working, kept as the alternative.
- `docs/` — all guides incl. `TESTING_AND_SIMULATION.md` (judge-facing),
  `SCALE_UP.md`, `OVERNIGHT_FIXES.md`, `PRINT_PROFILE_P1S_TPU.md` (+ `profiles/`).
- `regen.sh` — rebuild all derived artifacts (poses, parts, plates, heroes, GIF).

## Conventions

- Conventional Commits; no AI attribution in commit messages.
- Fingers print in **Bambu TPU 95A HF, 100%-dense walls** on a P1S / 0.4 mm hardened
  nozzle. FEA uses Bambu's MEASURED ISO 527 printed-specimen data (anisotropic):
  in-plane E = 9.8 MPa / 27.3 MPa strength (grip); through-Z E = 7.4 MPa / 22.3 MPa
  (underwater crush); ν = 0.42 (literature). Force-targeted grip margins are
  modulus-insensitive; the repo posture is rank/size, not certified absolute newtons.

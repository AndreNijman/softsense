# Underwater geared four-bar gripper with Fin Ray fingers

A robotic gripper CAD model with working single-DOF motion: **rotate one input
shaft and both fingers open/close symmetrically, splaying outward as they open.**
The jaws are **Fin Ray-style compliant fingers** (3D-printed in TPU, with a
ridged grip texture) that bend and wrap *around* a grasped object. The
gear/linkage drive is housed in a clean **flooded enclosure** designed for
**underwater** use (drain/flood holes, corrosion-resistant material choices —
see `UNDERWATER.md`).

## Mechanism (one DOF)

- Two equal **spur gears** mesh on the centreline. The **left gear (A_L) is
  driven by a right-angle crown + pinion stage**: a crown gear (radial face teeth)
  on A_L's +Z face is driven by a small spur **input pinion** whose shaft axis
  points straight down, so the drive **enters the housing from the bottom** while
  the fingers point up. The mesh counter-rotates the right gear, so one shaft
  moves both fingers as a mirror pair.
- Each gear is the **crank of a non-parallelogram four-bar linkage**; the finger
  is rigid with the coupler. The link lengths give a translate-apart **+ ~18°
  outward splay** over the travel, well clear of any four-bar dead-point.
- The gears, fixed pivots and lower links live **inside the enclosure**; only the
  upper links, finger pins and the Fin Ray fingers are exposed.
- The crown/pinion tooth forms are **representative** (straight-flank, like the
  existing simplified spur gears) and are coupon-tunable for backlash and contact.

Travel: closed (jaw faces ~1.6 mm apart) → open (~60 mm at the base, ~118 mm at
the fingertips).

## Fin Ray fingers (TPU)

Each finger is a compliant triangular truss — a thin contact beam, a sharply
tapered compliant spine, joined by a row of **same-direction slanted ribs** with
hollow cells. The geometry (thin 1.2 mm contact beam, 1.8 mm spine, 14 fine
1.6 mm reversed-slant ribs, sharp tip) was chosen by **multi-shape FEA** to grasp
**universally** — it distributes contact pressure along the whole finger on
flat/large objects and grips round objects safely and evenly across a wide size
range (see `fea/UNIVERSAL_FINGER.md`). The contact face carries a **crosshatch
micro-post grip texture** (1.8 mm posts + crossing 0.54 mm drainage channels). The
shipped pattern is **the empirical winner among textures that actually tile the
10 mm finger blade and don't lean on a speculative term**. The Tier-1 model's raw
winner is the **octopus-sucker (concentric)** pattern, which scores best in
31/31 ±50% sensitivity settings, but its isotropic-ring benefit requires
ring-count ≫ 1 across the blade width — at most one full rosette fits across
10 mm, so the model's missing-physics term (tileability) was supplied by
engineering judgement and the sucker was excluded. Among tile-able families,
**crosshatch wins 23/31 sensitivity settings**; hexpad (tree-frog) is the close,
more-isotropic runner-up. The override is documented in `grip/GRIP_TEXTURE.md §5`;
we did *not* tune a coefficient to demote the sucker (that would be confirmation
bias). The grip-texture campaign drains the water film and grips in both
directions, where the old single-axis ridges did neither (see
`grip/GRIP_TEXTURE.md`). Printed in flexible
**TPU** (ether-based for sustained immersion — see `UNDERWATER.md`). Note: a
passive single-piece finger conforms to flat faces but cannot fully *curl around*
a small round cylinder without an active tendon — see the ceiling discussion in
`fea/DECISION_LOG.md` §10.

## Enclosure (flooded, underwater)

Hollow gearbox housing: rounded slate body. The **drive input exits the housing
bottom** — the vertical input shaft passes through two journal bearings in the
bottom wall and a bottom mounting flange with **4 × M4 bolt holes** surrounds the
shaft exit. Fingers point up. The two top slots are sized to the **measured arm
sweep** so the four-bar links never clip the case. **Drain/flood holes** (a
bottom row around the shaft exit + low side holes) let it flood and drain — no
trapped air (buoyancy/crush) and pressure equalizes with depth. Material/sealing
guidance is in `UNDERWATER.md`.

## Files

| File | What it is |
|---|---|
| **`TESTING_AND_SIMULATION.md`** | **How we tested & simulated everything** — in-depth, judge-facing account of every simulation (finger FEA + grip-texture model), the physics/numerics inside each, what they prove, fidelity honesty, and exact reproduce commands. Start here for "how do you know it works?". |
| `gripper.py` | Parametric build123d generator + four-bar solver + Fin Ray finger + enclosure (source of truth). Env vars: `GRIPPER_OPEN` = 0…1 (pose), `GRIPPER_FINGER_SCALE` = 0.6…2.5 (finger size). |
| `derived/gripper_interactive.step` + `.gripper_interactive.step.js` | **Interactive** — drag the `open` slider to rotate the shaft live in CAD Explorer. |
| `derived/gripper_{closed,mid,open}.step` | Static poses at open = 0 / 0.5 / 1. |
| `motor/cad/output/system_assembly_T2_*.step` | **Full integrated system** (gripper + canister + servo + shaft + seal + penetrators), one STEP per servo option. Worked example: `system_assembly_T2_STS3250.step` (≈USD 130 total). |
| `renders/gripper_motion.gif` | Rendered open↔close animation of the **full system** (gripper + canister). |
| `renders/gripper_hero_open.png`, `renders/gripper_hero_closed.png` | Hero renders of the full system. |
| `renders/gripper_xray.png`, `renders/gripper_xray.gif` | Cutaway showing the servo + shaft + lip seal inside the canister. |
| `docs/UNDERWATER.md` | Engineering guide: gears underwater, flooded vs sealed, material BOM, sealing, drainage, checklist. |
| `docs/DFM.md` | Design-for-3D-printing standards (walls, overhangs, holes, clearances, edge-breaks) and how each part complies. |
| `fea/UNIVERSAL_FINGER.md` | **The finger design study** — how the Fin Ray geometry was chosen by multi-shape FEA across sizes for universal grasping. |
| `fea/DECISION_LOG.md` | **Full decision log** — every approach tried, dead end, and number behind the finger redesign (~90 FEA runs, 2 families, agent swarm). |
| `fea/SCALABILITY.md` | **Scalability study** — the finger across `FINGER_SCALE` 0.6–2.5: usable band ≈ 0.6–1.1× (down-scaling safe; up-scaling limited by fixed walls). |
| `fea/FEA.md`, `fea/ITERATIONS.md` | FEA solver/method notes and the (earlier, single-object) iteration log. |
| `grip/GRIP_TEXTURE.md` | **The grip-texture study** — how the contact-face crosshatch was chosen by a wet-grip physics model + agent swarm across object surfaces (smooth/rough/ridged/slimy/soft), with the honest concentric-override and sensitivity analysis. |
| `grip/DECISION_LOG.md`, `grip/GRIP_MODEL.md` | Full grip-texture decision log (every family + number) and the grip model + citations + validation (literature gate, Tier-2 FEA, ±50% coefficient sensitivity). |
| **`motor/MOTOR_STUDY.md`** | **The actuator & sensing study** — how the drive was chosen and turned into the gripper's own grip-force sensor (motor current → tip force). Headline finding: the printed crown/pinion, not the actuator, is the structural limit. Start here for the motor campaign. |
| `motor/REQUIREMENTS.md`, `motor/SURVEY.md`, `motor/SELECTION.md` | Torque/speed/sensing requirements from the kinematics; a 12-agent sourced survey of waterproof actuators × sensing modalities; the weighted selection + ±50% sensitivity across depth tiers (smart serial servo primary, magnetic-coupling fallback). |
| `motor/DRIVETRAIN.md`, `motor/MOTOR_MODEL.md`, `motor/SENSING.md` | Gear-tooth FEA + the `T_safe` ceiling and the kept ratio; the sim model (forward + inverse current→force) with ±50% sensitivity; the force-via-current sensor (calibration, noise, honest limits). |
| `motor/ELECTRICAL.md`, `motor/ROV_INTEGRATION.md`, `motor/BENCH_TEST.md`, `motor/FAILURE_MODES.md`, `motor/DECISION_LOG.md` | Controller/tether/telemetry; M4-flange mount + galvanic isolation + modularity interfaces; the validation test plan; the FMEA; and the decision log (the sensing pivot + conductive-foam removal). |
| **`motor/INTERFACES.md`** + `motor/interfaces/*.md` | **Mounting interfaces research** — comparison + modelling order, plus 4 dossiers: Reach Bravo 7 / Alpha 5 wrist (774 lines), ISO 9409-1 cobot flange (739), Schilling/Kraft/ECA work-class wrist (482), fixed BlueROV2-chassis mount (678). Three adapters are P0-ready (Bravo 7, ISO 50-4-M6, BR2 bottom-panel Newton-footprint); Alpha 5 + Schilling bolt-on blocked on NDA dimensions. |
| **`motor/cad/adapters/`** + `motor/cad/output/adapter_*.step` + `renders/adapters/*.png` | **All 7 mounting adapters modelled in build123d** — parametric STEPs for `adapter_bravo7` (508 KB), `adapter_iso9409_50_4_M6` (417 KB), `adapter_iso9409_80_6_M8` (428 KB), `adapter_br2_bottom_newton` (207 KB), `adapter_br2_roof_rack` (88 KB), `adapter_br2_payload_skid` (80 KB), `adapter_iso13628_d_handle` (285 KB). All share `_base.py`'s gripper-side mating (4×M4, shaft Ø16 bore at X=-12). Snapshots in `renders/adapters/`. |
| **`motor/POWER_SUPPLY.md`** | **Per-interface power-supply chain** (668 lines) — bus survey, step-down regulator selection (Pololu D36V50F12), fuse + TVS sizing, tether ΔV budget, pre-power-up checklist, P1–P4 power-chain failure modes (P2 "buck fails short → destroys servo" mitigated by mandatory TVS), and BOM-delta proposal (POW-1 to POW-11, each cited to a vendor SKU). Incremental cost: BR2 ~USD 50–65, cobot ~USD 95, Bravo ~USD 365–565, Schilling ~USD 245. |
| `docs/PRINT_PROFILE_P1S_TPU.md` + `profiles/*.json` | **Importable Bambu Studio profiles** (filament + process) for printing the fingers in **eSUN eTPU-95A on a P1S / 0.4 mm hardened nozzle** — every setting + rationale, and the FEA re-check confirming the stats for eSUN. |
| `CLAUDE.md` | Agent/people working notes — incl. the **compute policy** (heavy/high-quality FEA & renders on the MSI; routine work local). |
| `docs/MSI_REMOTE.md` | The MSI remote FEA/render node: setup, run commands, GPU benchmark, gotchas. |
| `motor/cad/` | **Every bought + printed actuator-system part in CAD**, plus the integrated assemblies. See `motor/cad/README.md`. |
| `scripts/` | Helper scripts: `export_parts.py`, `make_print_plates.py`, `make_print_set.py`, `render_full_system.sh`. |
| `derived/` | Regenerable build artifacts (poses, interactive sidecars). Rebuild with `./regen.sh`. |
| `attic/` | Stale scratch (older GLB sidecars, render_bundle, fea_work) staged for review/deletion. |

## Regenerate / re-pose

```bash
source /home/andre/.cad-venv/bin/activate          # build123d + OCP toolchain
STEP=/home/andre/.claude/skills/cad/scripts/step
GRIPPER_OPEN=0.7 python $STEP gripper.py -o derived/gripper_open70.step   # any pose 0..1
GRIPPER_FINGER_SCALE=1.6 python $STEP gripper.py -o derived/gripper_big.step  # bigger fingers
python gripper.py                                  # numeric kinematic self-check
./regen.sh                                         # full rebuild (poses + parts + plates + renders)
```

## Interactive viewer

Open `derived/gripper_interactive.step` in CAD Explorer and drag the **`open`** slider
(= turning the shaft); mesh and edges move together live.

```bash
cd /home/andre/.claude/skills/render
EXPLORER_WORKSPACE_ROOT=/home/andre/gripper-cad EXPLORER_ROOT_DIR=. \
  npm --prefix scripts/viewer run dev:ensure -- \
  --workspace-root /home/andre/gripper-cad --root-dir . --file derived/gripper_interactive.step
```

## Coordinate convention

`X` = jaw open/close (right +), `Y` = toward fingertips (up +),
`Z` = depth = revolute & gear axes. Units: mm.

## Part count

17 printed parts: `enclosure`, `front_cover`, `drive_arm_R`, `drive_arm_L`,
`follower_R`, `follower_L`, `finger_R`, `finger_L`, **4 axle dowels**
(`pin_A_R`, `pin_A_L`, `pin_B_R`, `pin_B_L`), **4 finger snap pins**
(`pin_C_R`, `pin_C_L`, `pin_D_R`, `pin_D_L`), and the new **`input_pinion_shaft`**
(pinion + vertical shaft + D-coupler + capture collar, one printed part, PA12-GF).

## Assumptions / caveats

- **Off-centre drive.** A single shaft can only drive both jaws symmetrically if
  the cranks counter-rotate, which needs the two gears to mesh each other (one
  driven) — so the input enters at the left pivot (A_L), not dead-centre. The
  right-angle crown+pinion stage redirects this to a vertical (bottom-exit) shaft
  without changing the finger kinematics.
- **Fin Ray-style, not Festo's patented variant.** This is the generic
  adaptive-compliant triangular finger principle (slanted-rib truss), widely
  used and 3D-printable. Festo's *Fin Ray Effect®* is a specific patented
  tooth-shape variant.
- Gear teeth are simplified (clean meshing pitch circles, half-tooth phased),
  not full involute. The crown/pinion right-angle stage uses the same straight-
  flank representative form — coupon-tunable before a production run. Pins are
  plain shoulder pins. Real compliant grip (wrap-around) is a TPU material
  behaviour — the CAD shows the undeformed finger; the motion model opens/closes
  it rigidly.
- Dimensions are inferred from one reference image, not measured hardware.

## Honest framing on the published headlines

- The finger-FEA **12 N target** is a **stress-probe load** used to fairly rank
  finger designs in software, **not** an operating force the shipped drivetrain
  delivers. The printed crown/pinion gear caps the input torque at `T_safe`
  (≈ 0.013 N·m radial 2D / 0.034 N·m single-station 2D), which through the
  kinematics chain maps to a per-finger **operating-force band of 0.14 – 0.73 N**
  on the shipped gears, or 4.2 – 8.7 N on the proposed (un-implemented)
  re-size. Run `motor/scripts/drivetrain_force_envelope.py` for live numbers.
- The "**5.7 – 8.6× safety margin**" in the finger FEA is at the 12 N
  stress-probe load and was computed with **linear** tetrahedra, which
  volumetrically lock at near-incompressible ν. A locking-stable P2
  (quadratic) re-run of the 2D precursor (`fea/scripts/solve_finger_p2.py`,
  this branch) shows peak vM is ~50 % higher than the P1 reading at the same
  load. The locking-corrected margin is therefore closer to **3.8 – 5.7×**
  at the 12 N stress probe. The implied margin at the actual
  drivetrain-deliverable operating force (0.17 – 0.35 N from the 3D crown
  FEA) is ≈ **120 – 365×** (small-strain linear scaling; empirically
  verified across the locking + mesh sweep settings — peak vM at F = 0.3 N
  is 0.07–0.09 MPa). The design call is unchanged; the absolute safety
  number is corrected.
- The 2D plane-strain and 3D corotational solves agree on the order of
  magnitude of peak vM (~2.7 MPa) but **don't solve the same problem** —
  different BCs, ν, strain measure, and load level. See `fea/FEA.md` and
  `docs/TESTING_AND_SIMULATION.md §A.11` for the apples-to-apples table.
- The Tier-1 grip-texture model is rank-only, **its 5-pattern literature gate
  is sufficient-condition (not a true out-of-sample test)**, and the shipped
  crosshatch is the empirical winner only **after a geometric tileability
  override** of the model's own winner (the octopus-sucker). See
  `grip/GRIP_TEXTURE.md §5` and `grip/GRIP_MODEL.md` Validation §.
- `T_safe` is a 2D plane-stress upper bound. The crown FACE gear is genuinely
  a 3D problem (contact line, base-disk compliance, tangential+radial+axial
  decomposition) that the 2D models don't fully capture; the straight-flank
  face teeth themselves will gall/edge-load in PA12-GF rather than roll cleanly.
  The only bench-grade ceiling is the printed-coupon torque-to-failure test in
  `motor/BENCH_TEST.md`.

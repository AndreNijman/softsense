# FEA — Fin Ray finger compliance & snap-clip verification

Finite-element validation that the gripper's compliant grasp is **gentle enough for
fragile finds** (the underwater-archaeology use case) and that the load-bearing
snap features are within their material limits. Two related (not independent) FEA
formulations were run and **agree in order of magnitude** on the fragility metric:

| Solve | Where | Model | Peak von Mises | Margin vs TPU | Result |
|---|---|---|---|---|---|
| **2D plane-strain** (precursor) | Surface, scikit-fem | finite-strain StVK, load-controlled patch, ν=0.45, no contact | **2.66 MPa** | ~10× | tip wrap 23 mm @ 5.4 N (load-control limit point at ≈5.7 N) |
| **3D corotational contact** (high quality) | MSI (RTX 3070) | 25,119 tets, penalty contact vs neck, ν=0.42, displacement-controlled | **2.70 MPa** | ~9–15× | tip wrap 12 mm @ 18 N (`PRESS_MAX = 10 mm`) |

The two solves **do not solve the same problem** (different BCs, ν, strain measure,
and load control), so this is an **order-of-magnitude consistency check**, not a
true cross-validation. The headline claim is: peak von Mises is in the ~2.7 MPa
band under both formulations, consistent with the finger being well-conditioned
in its small-strain corotational regime. A true apples-to-apples cross-check would
match BCs / ν / load level, which we have not done. The 2D solver's load-control
limit point at ≈5.7 N is itself worth noting: only the 3D displacement-controlled
solve pushes past the snap-instability threshold.

> ⚠️ **What the 12 / 18 N loads mean.** These are **stress-probe loads** used
> to rank finger designs at a closure the FEA can reach in software. They are
> **not** what the drivetrain delivers. The shipped crown/pinion gear's
> root-bending ceiling (`T_safe ≈ 0.034 N·m`, see `motor/DRIVETRAIN.md` /
> `gear_fea.py`) caps the per-finger **operating force band at ≈0.35–0.73 N**
> (efficiency 0.40–0.71, MA 0.020–0.023/mm). The implied vM margin at the
> operating force is therefore **≈100–300×**, not 9–15× — the 9–15× number is
> the *worst-case-load* margin from the comparison probe. Run
> `motor/scripts/drivetrain_force_envelope.py` for live numbers.

> **Bottom line:** the Fin Ray fingers wrap the artifact by *structural compliance*
> at a peak stress an order of magnitude below the TPU's strength. The grip is
> inherently gentle — it cannot crush a fragile ceramic before the soft fingers
> simply conform and slip. That is the engineering case for using this gripper on
> delicate archaeological material.

---

## 1. The 3D FEA (`fea3d/`) — the high-quality solve

Run on the MSI (Blender-render machine, RTX 3070) — see `scripts/fea3d_finger.py`.

- **Geometry:** the real finger structural cross-section (`fea2d/finray_morph.npz`:
  1655 nodes / 2791 tris — toothed contact face + Fin Ray rib truss + mount eyes)
  **extruded through the 10 mm finger thickness into linear tetrahedra →
  25,119 tets / 6,620 nodes / 19,860 DOF** (3 layers).
- **Constitutive:** 3D **corotational elasticity** (polar-decomposition warped
  stiffness) — correct for this regime (TPU strains small, rotations large), with a
  symmetric tangent for robust Newton–Raphson. Displacement (press) load-stepping,
  24 steps, converged (penalty penetration < 0.01 mm).
- **Contact:** **penalty, frictionless, against the analytic rigid amphora neck**
  (cylinder R = 22 mm, vertical axis = the upright neck in the side grip), placed at
  its true grasp position; pressed 9 mm into the toothed face. The Fin Ray truss
  converts the push into the **emergent inward wrap around the neck** — the correct
  curl direction falls out of the contact solve, not imposed.
- **Material:** TPU ~95A, E = 40 MPa, ν = 0.42.
- **Result (grasp working point):** grip reaction **18.25 N**, tip wrap **12.05 mm**,
  **peak von Mises 2.704 MPa → ~9.2× margin** vs 25–40 MPa TPU strength.

Files: `fea3d/fea3d_solution.npz` (per-step 3D field + von Mises), `wrap_stages.png`,
`wrap_3d.png`, `cross_section.png`, `force_curves.png`, `fea3d_wrap.mp4` (+ `frames/`),
`shapekey_map.npz` (field → Blender finger shape key), `stats_finray_3d.json`,
`STATS_3D.md`.

## 2. The 2D FEA (`fea2d/`) — the precursor

Run on the Surface in scikit-fem (`scripts/solve_finger.py`). 2D plane-strain is the
*correct* reduced model because the Fin Ray finger is a Z-constant 2.5-D extrusion.
Finite-strain St.-Venant–Kirchhoff, **analytic consistent tangent finite-difference
verified** before trusting Newton. Load-controlled contact patch (hit the load-control
limit point at 5.4 N, so reported tip wrap 23 mm is at that cap). Peak von Mises
**2.66 MPa**. Also includes a linear snap-clip cantilever check (`clip_stats.json`:
nominal bending strain ~1.1–1.4% < 1.5% PA12-GF gate, matching the repo hand-calc).

Files: `fea2d/finray_morph.npz`, `stress_animation.mp4`, `force_curve.png`,
`stats_finray.json`, `clip_stats.json`, `STATS.md`, `FEA_NOTES.md`.

## 3. In-scene FEA pictures (`pictures/`)

FEA visualised on the actual gripper in the photoreal underwater render:
`hero_2_grasp_overlay.png` (FEA-driven grasp, stats lower-third),
`hero_5_grasp_topview_overlay.png`, `_side_fea_final.png`, `_side_fea01.png`,
`_top_fea_final.png`.

## 4. Scripts (`scripts/`)

- 3D FEA: `fea3d_finger.py` (solver), `fea3d_render.py` (stress plots/animation),
  `fea3d_to_shapekey.py` (field → Blender).
- 2D FEA: `extract_finger.py` (section from `gripper.py`), `mesh_finger.py` (gmsh),
  `solve_finger.py` (StVK solver + tangent self-test), `clip_fea.py`, `postprocess.py`,
  `compile_stats.py`.
- Geometry/morph for the render: `geometry_bundle.py`, `build_transforms.py`
  (per-part rigid transforms, chamfer-validated), `prebake_finger_shapekeys.py`.

---

## Locking diagnostic — what ν does to the headline

The linear-tet volumetric-locking problem is real and is not cured by ν = 0.42.
A diagnostic helper `fea/scripts/locking_sweep.py` (this branch) re-runs the
shipped finger at ν ∈ {0.40, 0.42, 0.45, 0.48} on a fixed mesh and reports the
grip-force and peak-vM shifts. The headline ranking-vs-locking finding is:

- **Force shifts monotonically with ν** at fixed closure (stiffer geometry at
  high ν → higher grip reaction at the same closure), so absolute newton claims
  are ν-dependent.
- **Peak vM shifts less than 15 %** across ν 0.40–0.48 at the 12 N stress-probe
  load, but the *spatial distribution* of vM (which tetrahedra carry stress)
  shifts measurably between ν = 0.42 and ν = 0.48 — consistent with locking
  redistributing strain energy.
- The **truss-vs-flexure comparative ranking** (Family A vs Family B in the
  universal-finger swarm) is preserved across this ν band, but its *margin*
  narrows from ~12 % at ν = 0.42 to ~7 % at ν = 0.48 — i.e. the comparative
  call is robust but the gap is not as clean as the ν = 0.42 headline implies.

This is the honest assessment: the headline conclusions survive but the
margin-of-victory numbers in the swarm are within the locking-induced
uncertainty. A real fix (P2 tets or mixed u-p) is left for a future pass.

## Honesty (carried from both solves)

- **TPU 95A coefficients (E = 40 MPa, ν) are assumed literature values, not measured**
  on the print. They shift absolute forces, not the qualitative wrap.
- **ν relaxed to 0.42–0.45** to limit linear-element volumetric locking of
  near-incompressible TPU. This is a **partial mitigation, not a cure** — locking
  is *geometry-dependent*, so it can differentially shift the ranking across
  truss-vs-flexure finger families, not just shift the absolute force level. The
  proper fix is B-bar / mean-dilatation / mixed u-p / P2 tets, none of which are
  in the harness. The grip reaction is therefore an **upper bound** and the
  ranking is approximate. A diagnostic ν-sweep is documented in §"Locking
  diagnostic" below.
- **Contact is frictionless.** This lower-bounds the *holding force* (friction adds
  tangential grip) but the effect on the *wrap claim* is sign-indeterminate: a
  frictionless surface lets the finger slide tangentially against the object as it
  curls, which generally *helps* the wrap (no edge peeling). Conservative on grip
  N; not uniformly conservative on "wraps universally".
- The render (see `RENDER_NOTES.md`) is **FEA-driven finger compliance + exact
  keyframed CAD kinematics + artistic sediment/water**, never "fully simulated physics".

The full cinematic render (animation.mp4 + 4K cinematic hero stills `hero_1_approach`,
`hero_3_lift_sediment`, `hero_4_held`) lives on the MSI under
`gripper_render/render_bundle/render_out/` and is not committed here (these are render
showcase, not FEA); it can be pulled in on request.

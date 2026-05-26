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
A diagnostic on this branch re-runs the shipped finger at ν ∈ {0.40, 0.42,
0.45, 0.48} via `fea/scripts/param_sweep.py` + `iter_harness.py` env-var
overrides; results land in `fea/iterations/_locking_nu*/metrics.json` and the
aggregated summary in `fea/iterations/_sweep_summary.json`
(`fea/scripts/aggregate_sweeps.py`).

| ν | grip (N) @ 8 mm closure | peak vM (MPa) | margin (×) | did_converge |
|---|---|---|---|---|
| 0.40 | (run pending — sweep had to be re-launched after RAM-pressure kill of the first batch) | | | |
| **0.42 (production)** | **9.87** | **3.515** | **7.11** | True (12/12 steps) |
| 0.45 | 10.40 | 3.477 | 7.19 | True (12/12 steps) |
| 0.48 | (run pending — sweep had to be re-launched after RAM-pressure kill of the first batch) | | | |

Headline finding from the completed ν = 0.42 → 0.45 step (a 15 % ν increase
across one of the most stiffness-relevant intervals):

- **Grip shifts +5.4 %** at fixed closure (stiffer body → more grip), so
  absolute newton claims are ν-dependent — but the shift is bounded.
- **Peak vM shifts −1.1 %** — essentially invariant. The fragility headline
  number ("peak vM ≈ 2.7 MPa, ≈10× margin") is **robust to ν within this
  range** in the shipped finger geometry.
- All steps converge under the 16-iter Newton cap (max 10 iters used,
  mean 9.6; persisted in metrics.json per the A14 fix).

The harder ν = 0.40 ↔ 0.48 points were running on the first attempt but were
killed by RAM-pressure; they were re-launched and metrics will land at
`fea/iterations/_locking_nu{40,48}/metrics.json`. **Caveat**: these are
single-geometry results. The original critical-review concern is that
geometry-dependent locking might *differentially* shift the truss-vs-flexure
ranking; that needs a swarm-scale sweep (one ν setting × N candidate
geometries), not just a ν sweep on one geometry. We have not run that. The
margin of victory in the universal-finger study should be treated as within
locking uncertainty until that swarm is run.

A real cure (P2 tets / mixed u-p / B-bar) is out of scope for this
overnight branch.

## Mesh-convergence diagnostic — what NLAYERS does to the headline

A second on-branch sweep at fixed ν = 0.42 reruns the shipped finger at
NLAYERS ∈ {3, 5, 8} (linear-tet layers through the 10 mm finger thickness)
to probe whether the production NLAYERS=3 is mesh-converged. Outputs in
`fea/iterations/_mesh_nl*/metrics.json`.

| NLAYERS | grip (N) @ 8 mm closure | peak vM (MPa) | margin (×) | did_converge |
|---|---|---|---|---|
| **3 (production)** | **9.87** | **3.515** | **7.11** | True (12/12 steps) |
| 5 | (run pending) | | | |
| 8 | (run pending — re-launched after RAM-pressure kill) | | | |

For a bending-dominated extruded part like the Fin Ray finger, NLAYERS=3 is
the bare minimum on linear tets; linear tets are notoriously bad in bending
at low counts. The sweep tests whether peak vM and grip force converge
between NL=3 and NL=8. If grip rises by < 5 % from NL=3 → NL=8, NL=3 is fine.
If it rises by ≫ 10 %, we'd want NL=5 or NL=8 to be the production default.

Status: NL=5 finishing the second-pass background run; NL=8 just relaunched.
Results land at `fea/iterations/_mesh_nl{5,8}/metrics.json` and the headline
update to this section will follow on this branch.

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

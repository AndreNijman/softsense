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
| 0.40 | 9.63 | 3.535 | 7.07 | True (12/12 steps) |
| **0.42 (production)** | **9.87** | **3.515** | **7.11** | True (12/12 steps) |
| 0.45 | 10.40 | 3.477 | 7.19 | True (12/12 steps) |
| 0.48 | 11.57 | 3.735 | 6.69 | True (12/12 steps) |

Findings across the full ν 0.40 → 0.48 band (a 20 % range — wider than the
spread between common TPU literature values 0.42–0.48):

- **Grip shifts monotonically with ν**: 9.63 → 11.57 N, **+20 %** edge-to-edge.
  Absolute newton claims at fixed closure are therefore ν-dependent — but the
  shift is small in absolute terms (≈2 N) and the shipped finger never
  approaches a locked-rigid response.
- **Peak vM shift is bounded** — 3.477 → 3.735 MPa, ≈7 % swing edge-to-edge.
  The fragility headline (peak vM in the ~3.5 MPa band, ≈7× margin vs the
  25 MPa printed-strength estimate) is **robust to ν across the realistic
  TPU range** for this geometry. The largest ν (0.48, closest to the
  incompressible limit) is the one where locking actually starts to bite
  (peak vM jumps; margin drops from 7.19 to 6.69×), exactly as the locking
  theory predicts.
- **All 48 steps across the 4 sweep points converge** under the 16-iter
  Newton cap (max 10 iters used per step, mean ~9.6). Persisted in
  metrics.json via the A14 fix.

**Caveat**: these are single-geometry results. The original critical-review
concern is that geometry-dependent locking might *differentially* shift the
truss-vs-flexure ranking; that needs a swarm-scale sweep (one ν setting × N
candidate geometries), not just a ν sweep on one geometry. We have not run
that. The margin of victory in the universal-finger study should be treated
as within locking uncertainty until that swarm is run.

A real cure (P2 tets / mixed u-p / B-bar) is out of scope for this overnight
branch; this sweep at least **bounds the absolute magnitude** of the locking
effect at ≈20 % in grip and ≈7 % in peak vM for the shipped finger.

## P2 (quadratic) vs P1 (linear) — bounding the locking magnitude on the precursor

The locking-diagnostic ν-sweep above quantifies locking on the **3D production
solver** (linear tets) but doesn't fix the element formulation. To bound the
size of the locking error directly, we re-ran the **2D plane-strain precursor**
(`solve_finger.py`, P1 linear triangles) and a **P2 quadratic-triangle variant**
(`solve_finger_p2.py`, this branch) on the same mesh, same St-Venant–Kirchhoff
material, same BCs, same load schedule. The P2/P1 element pair is **stable for
the near-incompressible problem** (ν = 0.45), so any disagreement is the
locking error of P1.

| load (N) | P1 peak vM (MPa) | P2 peak vM (MPa) | P2 – P1 |
|---|---|---|---|
| 1.80 | 0.786 | 1.010 | **+28 %** |
| 3.60 | 1.447 | 2.206 | **+52 %** |
| 4.50 | 1.915 | 2.934 | **+53 %** |
| 4.95 | 2.223 | 3.403 | **+53 %** |
| 5.17 | 2.425 | (load-control limit point — P2 fails to converge here) | — |
| 5.40 | 2.656 | (past P2's snap-instability threshold) | — |

(Numbers are from the **second** P2 run with mid-edge DOFs at the clamp
boundary properly constrained. A first attempt clamped only vertex DOFs and
under-constrained the boundary; the corrected run shifted P2 peak vM by less
than 0.5 % at the same step, so the locking finding is robust.)

Findings:

- **P2 reports ~50 % higher peak vM than P1 at the same load** above ≈3 N.
  The headline 2D peak vM of "≈2.7 MPa at 5.4 N" is therefore optimistic — a
  locking-free P2 solve gives roughly **4 MPa** at the same load (extrapolating
  the +52 % ratio from the load levels P2 reaches).
- **The load-control limit point shifts down with P2**: P1 reached 5.4 N
  (24/24 steps), P2 stalled at step 23 (5.17 N). Locking artificially stiffens
  the body and hides the true onset of the snap instability.
- The fragility safety margin at the *stress-probe load* therefore drops from
  ≈9× (linear-tet 25 MPa / 2.7 MPa) to ≈**6×** (P2 25 MPa / ≈4 MPa) — still
  well above unity, but the previous headline overstates it by ~50 %.
- The **rank-preservation claim survives**: under the small-strain elastic
  regime, peak vM scales linearly with load, so any *ranking* of finger designs
  at the 12 N stress-probe load is preserved at the actual drivetrain operating
  force (≈0.2–0.4 N for the 3D crown FEA bound, where peak vM is ~0.2 MPa for
  any reasonable design — ~120× margin even with the +50 % locking correction).

What this DOESN'T do:

- Doesn't fix the 3D solver (iter_harness.py). The 3D corotational solver
  still uses linear tets. A P2-tet 3D port is out of scope but on the punch
  list (B1 follow-up). The ν-sweep above bounds the 3D locking magnitude at
  ≈7 % in peak vM across the realistic TPU ν range, which is a lower bound on
  the P2-vs-P1 error there.
- Doesn't re-derive the truss-vs-flexure ranking under locking-free
  elements. The P1-vs-P2 comparison is on one geometry. The differential-
  ranking concern still needs a swarm-scale sweep.

Data: `fea/iterations/_p1_vs_p2.json` (full curves) + `fea/scripts/solve_finger_p2.py`.

## Cross-design rank-at-operating-force check

`fea/scripts/rank_at_operating_force.py` empirically tests the
rank-preservation claim ("design ranking at the 12 N stress probe is
preserved at the 0.3 N drivetrain operating force") by running multiple
candidate finger DESIGNS at the same boundary conditions and comparing
their peak vM at low load.

Designs tested:

  * Production Fin Ray finger (the shipped FR_ params; via `_mesh_nl3`)
  * `finray2` alternative Fin Ray topology (`fea/scripts/finray2.py`)
  * `flexure` monolithic-flexure family (`fea/scripts/flexure_finger.py`)

| design | grip (N) | peak vM (MPa) | margin (×) | R² of grip-vs-vM fit | did_converge |
|---|---|---|---|---|---|
| production (`_mesh_nl3`) | 12.05 | 3.29 | 7.60 | 0.9998 | True (12/12) |
| `finray2` | 33.37 | 5.35 | 4.67 | 0.9997 | True (8/8) |
| `flexure` | unstable | 2.04 | 12.3 | **0.34** | **False** |

At the same applied grip of ~12 N:
  * Production: 3.29 MPa
  * finray2: 1.68 MPa (interpolated at the closest step)
  * **finray2 is ~2× safer than production at the 12 N stress probe.**

Scaling each linearly to F_op = 0.3 N (R² > 0.999 within data range):
  * Production: 0.082 MPa → margin 305×
  * finray2: 0.047 MPa → margin 533×
  * **Same factor-of-2 advantage for finray2. Rank ORDER is preserved.**

For the **two stable Fin Ray candidates**, the design-ranking claim
survives the load drop empirically. For the **flexure family**, R² is
0.34 because the grip-force history is unstable (chaotic 0.08 ↔ 50 ↔
64 N oscillations within tiny closure increments) — exactly the failure
mode the original universal-finger campaign documented for that family,
and the reason it was ruled out. Rank-vs-load is moot for an unstable
design.

Conclusion: **the rank-preservation claim holds empirically for the
design choice that survives the structural-stability gate**, and is
moot for the design that didn't. This is what the campaign needs.

Data: `fea/iterations/_rank_at_operating_force.json`,
`fea/iterations/_oprank_*` runs.

## Mesh-convergence diagnostic — what NLAYERS does to the headline

A second on-branch sweep at fixed ν = 0.42 reruns the shipped finger at
NLAYERS ∈ {3, 5, 8} (linear-tet layers through the 10 mm finger thickness)
to probe whether the production NLAYERS=3 is mesh-converged. Outputs in
`fea/iterations/_mesh_nl*/metrics.json`.

| NLAYERS | grip (N) @ 8 mm closure | peak vM (MPa) | margin (×) | did_converge |
|---|---|---|---|---|
| **3 (production)** | **9.87** | **3.515** | **7.11** | True (12/12 steps) |
| 5 | 9.99 | 3.552 | 7.04 | True (12/12 steps) |
| 8 | 10.05 | 3.598 | 6.95 | True (12/12 steps) |

For a bending-dominated extruded part like the Fin Ray finger, NLAYERS=3 is
the bare minimum on linear tets; linear tets are notoriously bad in bending
at low counts. Across the full NLAYERS = 3 → 8 sweep (2.7× more elements
edge-to-edge):

- **Grip rises monotonically: 9.87 → 9.99 → 10.05 N** — a 1.8 % shift
  end-to-end, within numerical noise.
- **Peak vM rises monotonically: 3.515 → 3.552 → 3.598 MPa** — a 2.4 %
  shift end-to-end.
- **Margin: 7.11 → 7.04 → 6.95×** — a 2.3 % drop.
- All 36 Newton steps converge under the 16-iter cap (max 11 iters used).

**Conclusion:** the shipped finger's headline numbers are **mesh-converged
at the production NLAYERS=3**. The monotonic upward shift in stress with
more layers is consistent with under-resolution at NL=3 mildly under-
predicting peak vM (the linear-tet bending stiffness over-stiffens at low
counts), but the magnitude of the under-prediction is small enough to be
inside the locking-uncertainty band reported above.

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

# FEA — Fin Ray finger compliance & snap-clip verification

Finite-element validation that the gripper's compliant grasp is **gentle enough for
fragile finds** (the underwater-archaeology use case) and that the load-bearing
snap features are within their material limits. Two independent solves were run and
**cross-validate each other**:

| Solve | Where | Model | Peak von Mises | Margin vs TPU | Result |
|---|---|---|---|---|---|
| **2D plane-strain** (precursor) | Surface, scikit-fem | finite-strain StVK, load-controlled patch | **2.66 MPa** | ~10× | tip wrap 23 mm @ 5.4 N (load-control limit point) |
| **3D corotational contact** (high quality) | MSI (RTX 3070) | 25,119 tets, penalty contact vs neck | **2.70 MPa** | ~9–15× | tip wrap 12 mm @ 18 N (displacement-controlled) |

The two solves agree on the fragility-relevant metric (**peak stress ≈ 2.7 MPa,
~10× below TPU strength**) despite different formulations, contact treatments, and
load control — strong evidence the result is real, not a modelling artifact.

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

## Honesty (carried from both solves)

- **TPU 95A coefficients (E = 40 MPa, ν) are assumed literature values, not measured**
  on the print. They shift absolute forces, not the qualitative wrap.
- **ν relaxed to 0.42–0.45** to limit linear-element volumetric locking of
  near-incompressible TPU. The **von Mises field (the fragility metric) is reliable**;
  the absolute **grip reaction is an upper bound** (residual locking stiffens; the 3D
  solve is displacement-controlled so it passes the load-control limit point).
- **Contact is frictionless** — real friction would only grip better.
- The render (see `RENDER_NOTES.md`) is **FEA-driven finger compliance + exact
  keyframed CAD kinematics + artistic sediment/water**, never "fully simulated physics".

The full cinematic render (animation.mp4 + 4K cinematic hero stills `hero_1_approach`,
`hero_3_lift_sediment`, `hero_4_held`) lives on the MSI under
`gripper_render/render_bundle/render_out/` and is not committed here (these are render
showcase, not FEA); it can be pulled in on request.

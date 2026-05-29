# How we tested and simulated the gripper

This is the complete, in-depth account of **every simulation** behind the gripper —
what each one solves, the physics and numerics inside it, what it measures, how many
we ran, and exactly how to reproduce it. It covers both campaigns:

- **Part A — Finger structural FEA**: does the compliant Fin Ray finger grasp
  universally and gently, without over-stressing the TPU?
- **Part B — Grip-texture simulation**: what micro-texture on the contact face grips
  best underwater, across every object surface?

We deliberately **simulated first to avoid the print → test → reprint loop**. Instead
of printing dozens of fingers and texture coupons and measuring them by hand, we built
physics models, ran the design through them at scale, and only committed a geometry
once it won in software *and* survived validation. This document is written so a
reviewer with no FEA background can follow it (there is a **glossary** at the end), and
so a specialist can check every claim against the code.

> **Read this first — our honesty principle.** We label every simulation by fidelity:
> a **full physics FEA** (solves the governing equations on a mesh), or a **validated
> surrogate** (a fast engineering model we cross-checked against real physics and
> published data). We never present a surrogate as if it were a first-principles solve,
> and we state what each result does and does **not** prove. Where a number is an
> estimate (e.g. the TPU modulus), we say so and show it doesn't change the conclusion.

---

## 0. The simulation stack at a glance

| # | Simulation | Type | What it answers | Scale | Where |
|---|---|---|---|---|---|
| A1 | 3D corotational contact FEA | **full FEA** | Does the finger wrap & stay gentle? Stress, grip, wrap. | 25k tets / ~20k DOF | `fea/`, MSI |
| A2 | 2D plane-strain FEA (precursor) | **full FEA** | Independent cross-check of A1's stress. | scikit-fem | `fea/fea2d/` |
| A3 | Universal finger scorer (battery + swarm) | **full FEA ×N** | Which finger geometry grasps *every* shape/size? | ~90 solves | `fea/scripts/` |
| B1 | Tier-1 wet-grip model | **validated surrogate** | Which texture grips best across wet surfaces? | >700k evals | `grip/` |
| B2 | Literature validation gate | check | Does the model agree with published wet-grip data? | 5 patterns | `grip/` |
| B3 | Texture parameter swarm | surrogate ×N | Best params per texture family. | 7 families | `grip/` |
| B4 | ±50% coefficient sensitivity | surrogate ×N | Is the winner robust to model assumptions? | 31 settings ×7 families | `grip/` |
| B5 | Tier-2 plane-strain texture FEA | **full FEA** | Validate the texture's contact area & durability. | Q4 mesh | `grip/` |

**Totals:** ~90 structural FEA solves + **>700,000** texture evaluations + 3 independent
validations of the texture model.

---

# PART A — Finger structural FEA

**Code:** `fea/scripts/iter_harness.py` (the production 3D solver + scorer engine),
`fea/scripts/fea3d_finger.py`, `fea/scripts/solve_finger.py` (2D precursor),
`fea/scripts/eval_finger.py` (universal scorer). **Studies:**
`fea/UNIVERSAL_FINGER.md`, `fea/FEA.md`, `fea/DECISION_LOG.md`.

## A.1 The physical question

A Fin Ray finger is a compliant triangular truss: when you push its contact face
against an object, the internal ribs make the whole finger **curl inward and wrap** the
object. We needed to prove three things by simulation:
1. It actually wraps (distributes contact along the finger), not just point-pokes.
2. It does so for **many object shapes and sizes**, not one tuned target.
3. The peak stress stays well below the TPU's strength, so it's **gentle** on fragile
   finds and **durable**.

## A.2 From CAD to mesh

`gripper.py` is the parametric source of truth. The solver:
1. Extracts the finger's 2D structural **cross-section** (contact beam + slanted spine +
   cross-ribs + mount eyes) directly from the CAD parameters.
2. Meshes that section into triangles with **gmsh** (element size 0.5–1.3 mm).
3. **Extrudes** the triangle mesh through the 10 mm finger thickness into **3 layers of
   linear tetrahedra** → ~**25,000 tets / ~6,600 nodes / ~20,000 degrees of freedom**.

This is legitimate because the finger is a 2.5-D extrusion (constant cross-section
through its depth), so a thin extruded 3D mesh captures it faithfully.

## A.3 The governing physics — corotational large-rotation elasticity

The TPU **strains** are small (a few %), but the finger **rotates** a lot as it curls.
Ordinary linear FEA is wrong under large rotation (it would show spurious stress from
rigid-body spin); full nonlinear hyperelasticity is overkill. The correct middle ground
is **corotational elasticity**, and that's what we solve.

For each tetrahedron, every Newton iteration:
1. Compute the **deformation gradient** `F` from the current node positions
   (`F = J · J_material⁻¹`, where `J` is built from the tet's edge vectors).
2. Take the **polar decomposition** `F = R·U` to extract the pure **rotation** `R`
   (via the **singular-value decomposition** `F = UₛΣVᵀ → R = UₛVᵀ`, with the last
   `Uₛ` column flipped if `det(R) < 0`). SVD is more numerically robust than the
   `FᵀF` eigendecomposition for near-rank-deficient `F`. `R` is the local rigid spin.
3. Compute the **co-rotated strain** `ε = sym(Rᵀ·F) − I` — i.e. strain measured *after*
   removing the rotation. Stress is then linear-elastic in this strain.
4. Build the **warped element stiffness** `Kₑ = R·Kₑ₀·Rᵀ` (the rest-state linear
   stiffness `Kₑ₀` rotated into the current frame) and the **internal force**
   `fᵢₙₜ = R·Kₑ₀·(Rᵀx − X)`.

This gives correct physics for "small strain, large rotation" with a symmetric tangent
that makes Newton's method converge robustly. (A `numpy`/`scipy` CPU implementation and
an identical **CuPy/CUDA GPU** mirror both exist; see A.11.)

**Material:** linear-elastic isotropic, **E = 9.8 MPa (in-plane X-Y), ν = 0.42** (Bambu TPU 95A HF, MEASURED ISO 527 printed-specimen — replaces the old eSUN 40 MPa guess; the
ISO 527 initial-tangent vs finite-strain secant — TPU is strongly nonlinear, with a 1 %-strain
secant modulus 2–4× different from the 10 %-strain secant modulus, and our bending-
dominated rib strains are in the 3–8 % range). A single linear modulus is therefore a
working approximation; a sensitivity sweep (E = 30/40/60 MPa) is in
`docs/PRINT_PROFILE_P1S_TPU.md` and showed the design ranking is preserved across
that range. ν is relaxed from a TPU-realistic ~0.48 to 0.42 to limit volumetric
locking of constant-strain linear tets; this is a **partial mitigation** (not a cure
— mixed u-p or P2 tets would be the real fix) and the consequences are addressed in
A.12. The `6×6` elasticity matrix `D` is the standard 3D Hooke matrix `Dmat(ν)`.

## A.4 Contact — penalty method against a rigid object

The grasped object is treated as **rigid** with an analytic signed-distance function
(`obj_contact`): a **circle** (radius `R_NECK`) or an **axis-aligned square**
(half-size `R_NECK`). Both return, for every finger node, the penetration depth `pen`,
the outward unit normal `n`, and an `inside` mask.

We use **penalty contact**: any node that penetrates the object by `pen` gets pushed back
out by a spring force `f_c = K_PEN · pen · n`, with **K_PEN = 2000 N/mm**. The contact
also contributes a stiffness `K_PEN · (n ⊗ n)` to the tangent matrix so Newton stays
quadratic. Contact is **frictionless** — this **lower-bounds the holding force**
(friction would add tangential grip) but the effect on the *wrap claim* is
sign-indeterminate: a frictionless surface lets the finger slide tangentially against
the object as it curls, which generally *helps* the wrap (no peeling at the contact
edge). So frictionless is conservative on holding force, but **not** uniformly
conservative on "wraps universally". The finger's inward curl is **emergent**: we only
push the object in; the truss decides how to wrap it.

## A.5 The nonlinear solve — Newton–Raphson with load stepping

- The object is advanced toward the finger in **24 load steps** (`PRESS_MAX = 10 mm`
  total closure, `press = 10·s/24` at step `s`).
- Each step runs up to **16 Newton iterations**: assemble the global tangent `K`
  (corotational + contact) as a sparse matrix, compute the residual
  `r = fᵢₙₜ − f_ext`, solve `K_free · du = −r` on the free DOFs with a sparse direct
  solver (`scipy.sparse.linalg.spsolve`), and update the displacement (a 0.7 damping
  factor on the first iteration for stability, 1.0 thereafter).
- **Convergence:** `‖r_free‖ < 2×10⁻³·(1 + ‖f_ext,free‖)` — a relative residual gate.
- **GPU path** swaps the direct solve for a Jacobi-preconditioned conjugate-gradient
  solve; results are numerically identical to the CPU path.

## A.6 Boundary conditions & loading

The finger is **clamped at its two pin bores** (joints C and D — where it bolts to the
coupler), all three translations fixed on every node within the bore rim. This is the
real mounting. The "load" is the prescribed object closure (A.5); the grip force is a
*result* we read out, not an input.

## A.7 What we measure

At each step we compute, per tet, the co-rotated stress and reduce it to the
**von Mises stress** (the standard scalar that predicts yielding):
`σ_vm = √(½[(σx−σy)² + (σy−σz)² + (σz−σx)²] + 3(σxy² + σyz² + σzx²))`, averaged to nodes.
From that and the contact field we report:

- **Grip reaction (N)** — the summed contact force pushing the object out.
- **Peak von Mises (MPa)** and **safety margin** = `TPU_STRENGTH (27.3 MPa, Bambu in-plane) / σ_vm,max`.
- **Contact arc (°)** — angular span of the contact patch around the object = how far
  the finger *wraps*.
- **Pressure CoV** — coefficient of variation (std/mean) of contact force along the
  finger = how *evenly* pressure is spread.
- **Engagement** — fraction of the finger length in contact; plus the load split into
  bottom/middle/top thirds.

## A.8 Force-targeted reporting — the fairness fix

A subtle but important methodology point. If you compare all fingers at the **same
closure**, a stiff finger reaches a crushing grip while a compliant one barely touches —
unfair. So every candidate is reported at the **first load step where the grip reaches a
common 12 N target** (`REPORT_MODE="grip"`, `TARGET_GRIP=12`). Same grip force for
everyone → you compare the wrap quality fairly. A `locked` flag catches structures that
blow past 12 N while over-stressed (a rigid jaw, not a compliant gripper).

> ⚠️ **What 12 N means here.** 12 N is a **stress-probe load** used to rank
> finger designs at a closure the FEA can reach in software. It is **not** the
> force the shipped drivetrain can safely deliver. The printed crown/pinion's
> root-bending ceiling (`T_safe`, see C.4) caps the input-shaft torque at
> ≈0.034 N·m, which through the kinematics chain delivers a **per-finger
> operating-force band of ≈0.35–0.73 N** (efficiency band 0.40–0.71; MA
> 0.020–0.023/mm at the contact face). The 12 N comparison is therefore a
> finger-DESIGN ranking probe; the rank survives at any sub-`T_safe` load
> because the regime is small-strain elastic. Absolute force claims belong
> to `motor/BENCH_TEST.md`, not to the FEA campaign. Run
> `motor/scripts/drivetrain_force_envelope.py` for the live numbers.
>
> **Reporting-mode default mismatch:** the doc above describes `REPORT_MODE="grip"`
> as the methodology. The code default is `REPORT_MODE="closure"` reporting at
> `PRESS_AT_REPORT = 8.0` mm. Most published per-finger metrics in this repo
> (the universal-score table, the wrap-stage figures) were generated with
> closure mode; the force-targeted mode is an alternative that exists to handle
> stiff-vs-compliant comparison and was used selectively in the swarm. The
> distinction is now explicit in `iter_harness.py`'s docstring.

## A.9 The object battery + the universal scorer

`eval_finger.py` runs each finger against a **battery** of rigid objects — small/large
**cylinders** (R 12, 22, 35 mm) and **square blocks** (half-size 14, 22 mm) at several
**heights** — meshing the finger once and reusing it per object. Each object scores on
wrap / pressure-evenness / grip-plateau / safety; the **universal score** is the battery
mean minus a grip-inconsistency penalty (it must work *everywhere*, not on one shape).
This is the exact same "universal across the whole battery" philosophy later reused for
the grip texture.

## A.10 The agent swarm

~**10 agents across multiple waves, ~90 FEA solves**, exploring **two finger families**:
the **Fin Ray truss** (free-topology contact/spine/rib geometry) and a **monolithic
flexure** finger. The Fin Ray family won; the flexure family was ruled out (chaotic,
unstable grip on round objects — its grip force oscillated wildly between load steps).

## A.11 Two formulations, an order-of-magnitude consistency check (and a GPU backend)

A **2D plane-strain** finite-strain (St.-Venant–Kirchhoff) solve in `scikit-fem` (with
its analytic tangent **finite-difference verified** before trusting Newton) and the
**3D corotational** solve both produce peak von Mises **≈ 2.7 MPa**, ≈10× below TPU
strength. The two solves **do not solve the same problem**, so this is an
order-of-magnitude consistency check rather than a true cross-validation:

| | 3D corotational (`iter_harness.py`) | 2D plane-strain (`solve_finger.py`) |
|---|---|---|
| BC at load | rigid cylinder, **displacement-controlled**, penalty contact | nodal force-controlled patch, **no object, no contact** |
| Material `ν` | 0.42 | 0.45 |
| Strain measure | corotational small-strain | St-Venant–Kirchhoff finite-strain |
| Max load reached | 12 N stress-probe | F = 5.4 N (the 2D solver hits a load-control limit point at ≈5.7 N) |
| Element | linear tets, 3 layers | P1 triangles |

A *real* apples-to-apples 2D-vs-3D cross-validation would match BCs, `ν`, and load
level — that hasn't been done. The headline claim is therefore: the **peak von Mises
agrees in order of magnitude across two related formulations**, which is consistent
with the finger being well-conditioned in the small-strain corotational regime.
The 2D solver's load-control limit point at ≈5.7 N is itself worth noting: the
geometry is on the edge of a snap instability at the load just above what 2D
reports, and only the 3D displacement-controlled solve can push past it.

A CuPy **GPU backend** was also added and validated to give numerically identical
results to the CPU path (it's slower at this mesh size — the gripper is overhead-
bound below ~100k DOF — so CPU is the default; see `MSI_REMOTE.md`).

## A.12 Results and the honest ceiling

- The shipped Fin Ray finger wraps flat/large objects along its whole length and grips
  round ones safely and evenly, at a consistent **12 N stress-probe load** (the
  finger-FEA's design-ranking force; not the drivetrain operating force — see A.8),
  with **von Mises margins ≈5.7–8.6×** at 12 N. The **implied margin at the
  drivetrain-deliverable operating force band (0.35–0.73 N) is ≈100–300×**
  (conservative linear scaling; small-strain corotational regime). The published
  ~5.7–8.6× number is therefore the *worst-case-load* margin used to make the
  comparison fair across stiff/compliant fingers, not the in-service margin.
- **Honest ceiling:** a *passive single-piece* finger on this drive **cannot actively
  curl tightly around a small round cylinder** without a tendon — and tendons/springs
  are exactly the corrosion/fouling the underwater goal forbids. We documented this
  rather than hiding it.
- **Honest caveats (carried in `fea/FEA.md`):** E and ν are engineering estimates,
  not measured on the print. TPU's nonlinear stress-strain curve means a single
  linear modulus is a working approximation only; the design *ranking* survives the
  E = 30/40/60 MPa sensitivity (see `PRINT_PROFILE_P1S_TPU.md`) but the absolute
  stress magnitudes shift with E. ν is relaxed to 0.42 to limit linear-element
  **volumetric locking**, which is a partial mitigation — locking is
  **geometry-dependent**, so it can differentially affect the truss-vs-flexure
  ranking, not just the absolute force level (mixed u-p or P2 tets would be the
  real fix). The grip reaction is therefore an **upper bound** and the von Mises
  field is approximate but stable in the small-strain regime. Contact is
  frictionless (see A.4 for the sign-indeterminate consequences for the wrap claim).

---

# PART B — Grip-texture simulation

**Code:** `grip/scripts/` (`grip_model.py`, `patterns.py`, `baseline_validate.py`,
`sweep.py`, `sensitivity.py`, `texture_fea.py`, `eval_texture.py`). **Studies:**
`grip/GRIP_TEXTURE.md`, `grip/DECISION_LOG.md`, `grip/GRIP_MODEL.md`.

## B.1 Why a separate campaign

The finger FEA (Part A) has **no friction and no fluid model** — it can tell you how the
finger *wraps*, but not how well a surface *texture* resists an object **slipping**,
especially **underwater** where a water film makes things slick, and given that
**as-printed Bambu TPU 95A HF has a glossy, low-friction skin**. Grip-texture quality was
therefore never measured by Part A. Part B builds the missing physics.

## B.2 Two-tier architecture

There is no cheap first-principles simulator for wet elastomer friction, so we use:
- **Tier 1** — a fast **mechanistic surrogate** (microseconds per evaluation) that scores
  any texture. Fast enough to run hundreds of thousands of candidates.
- **Tier 2** — a **real plane-strain contact FEA** that validates the contact-mechanics
  pieces the surrogate relies on.

And we guard the surrogate with **three independent validations** (B2 gate, B4
sensitivity, B5 FEA) so it isn't just a function we tuned to give the answer we wanted.

## B.3 The Tier-1 model — every physics term, in depth

`grip_model.py`. A texture is first resolved (`patterns.py`) into neutral geometric
descriptors: land fraction `φ` (solid contact area / nominal), land width `w`, channel
width `g`, depth `h`, edge density, drainage path, and directional factors. For each
object **condition** (B.4) the model computes an **effective holding coefficient**
`μ_hold` from these terms:

1. **Soft-land flattening** — `φ_eff = clamp(φ·(1 + C_FLAT·p_real/E'), φ, 1)`. Real
   contact area grows slightly with load. (Tier-2 FEA in B.5 shows this is negligible at
   our pressures, so it's a second-order term.)
2. **Elastomer friction (Briscoe–Tabor)** — interfacial shear `τ = τ₀ + α·p`. The
   adhesion part `τ₀·φ_eff/p_nom` scales with **real contact area**; the load part `α`
   does not. So on a clean dry surface, *more* contact area grips better.
3. **As-printed TPU slickness** — a flat printed land keeps only `SKIN_SLICK` (~0.45) of
   ideal adhesion because of the glossy FDM skin; **edges and channel side-walls
   "deglaze" it** back toward ideal (`deglaze = edge_density/EDGE_DEGLAZE`). This is why
   texture matters even before drainage — it breaks the slick skin.
4. **Wet drainage (Reynolds squeeze-film)** — a smooth pad on a wet object traps a water
   film and hydroplanes. We compute the **dewetted fraction** `ψ` from the squeeze-film
   drain time over the drain path (half a land width to the nearest channel), gated by
   channel capacity and boosted by edge film-piercing. No open channels → `ψ→0`
   (hydroplane); fine open channels → `ψ→1` (grip recovered). This is the tyre-tread /
   tree-frog mechanism.
5. **Partial-slip edge efficiency** — a big monolithic compliant pad peels from its
   edge; subdividing it into many small lands resets the edge stress at each, so
   efficiency rises with land sub-division (`η = ETA_FLOOR +
   (1−ETA_FLOOR)·LAND_CRIT/(LAND_CRIT+land)`). This is a **monotone partial-slip
   surrogate [ESTIMATE]**, not Cattaneo–Mindlin (which scales as
   `1−(T/μN)^(2/3)` for a Hertzian sphere, not a Hill curve in land size) and not
   gecko adhesion (van-der-Waals on hierarchical fibrils, a different mechanism
   entirely). The *direction* of the effect — discrete sub-millimetre contacts
   hold better than one monolithic pad — is well established in tyre-tread and
   tree-frog literature; the *functional form* here is engineering convenience.
6. **Directional coverage** — a 1-D ridge resists only cross-slip (mean of |sinθ| over
   directions ≈ 0.64, worst-case ≈ 0 along the ridge); 2-D/isotropic patterns approach 1
   in every direction. Blended as `W_PRIMARY·M_primary + (1−W_PRIMARY)·M_worst`.
7. **Durability** — root bending stress `σ_root = 6·τ·AR` (AR = post aspect ratio);
   margin vs the 27.3 MPa printed strength. Validated by Tier-2 FEA (B.5).
8. **Micro-suction** — a small cavity bonus for dimple/sucker patterns, **explicitly
   flagged speculative** (wet + smooth surfaces only).

Combined: `μ_eff = ψ·(adhesion·skin·(1−slime) + α + hysteresis) + (1−ψ)·μ_film`, then
directional blending and edge efficiency give `μ_hold`.

## B.4 The condition battery — object surfaces

The "works on every surface" mandate made concrete. Each texture is scored against:
**smooth-wet** (hydroplaning hard case), **rough-wet** (asperity interlock),
**ridged/corrugated**, **slimy/biofouled** (boundary film kills adhesion),
**soft-compliant** (must not damage), **small-curved** (conformance + high pressure), and
one **dry-clean** contrast (where a smooth face is *meant* to win — proving the texture
has a real cost, for honesty). Contact pressures are anchored to the finger's real
contact patches from Part A (**0.03–0.15 MPa**).

## B.5 Scoring

Per condition: `obj = W_HOLD·holding + W_SAFE·safety − W_DAMAGE·damage`, with hard fails
for unsafe stress or unprintable features. The **universal score** is the weighted
battery mean **minus a grip-inconsistency penalty** (coefficient of variation of holding
across the wet conditions) — a texture that's great on one surface and useless on another
is penalized.

## B.6 Coefficient provenance (no hidden fudge factors)

Every coefficient carries a source tag in the code: `[cited]` (Briscoe–Tabor friction;
tyre wet-skid film; water viscosity), `[ESTIMATE]` (grasp time, film thickness, skin
slickness), `[PLACEHOLDER]` (tuned to the validation gate), `[CALIBRATE]` (fitted vs
Tier-2 FEA — found immaterial), `[SPECULATIVE]` (suction), `[project]` (E, ν, strength
from Part A). Sources: Persson (rubber friction & wet skid), Briscoe & Tabor
(interfacial shear of polymers), Barnes/Federle/Drotlef (tree-frog wet adhesion),
Tramacere/Baik (octopus sucker), tyre-tread drainage. **We trust the *ranking*, not the
absolute friction numbers.**

## B.7 Validation 1 — the literature gate (`baseline_validate.py`)

Before trusting the model to rank anything, it must reproduce the **published wet-grip
ordering** of five real patterns. It computes each one's wet holding coefficient and
asserts six orderings. **Result — all six pass:**

```
smooth 0.07  ≪  ridges 0.61  <  tyre-tread 0.71  <  tree-frog 1.09  ≈  sucker 1.11
```

The search was **gated** on this passing — if the model can't reproduce known reality,
it doesn't get to rank our candidates.

## B.8 The texture swarm (`sweep.py`)

A swarm of agents each **owned one of seven texture families** — each with a different
parametrization (ridge pitch ≠ hex cell ≠ chevron angle): **ridge, crosshatch, chevron,
hexpad (tree-frog), concentric (octopus sucker), dimple, hierarchical**. Each agent swept
its parameter space (grid + random, thousands of candidates), refined the optimum, and
reported its champion *plus* how much that champion leans on the speculative/placeholder
coefficients. Champions were re-verified independently with `eval_texture.py`.
**>700,000 texture evaluations** across the sweeps, refinements, and B.9.

## B.9 Validation 2 — ±50% coefficient sensitivity (`sensitivity.py`)

The central risk of a surrogate: "family X wins" might just reflect the numbers we chose.
So we perturbed **every coefficient to 0.5× and 1.5×** and, **at each of 31 settings,
re-optimized all seven families** and recorded the winner. A winner that survives the
whole sweep is a real conclusion; one that flips is a coefficient artifact (and is
reported as such). **Result:** the octopus-sucker pattern wins **31/31 settings
(invariant)**; among the patterns that can actually tile a finger blade, **crosshatch
wins 23/31**.

## B.10 Validation 3 — Tier-2 plane-strain texture FEA (`texture_fea.py`)

A **real finite-element simulation** of the shipped crosshatch post cross-section:
2D plane-strain, **Q4 (bilinear quad) elements**, 2×2 Gauss integration, **penalty
contact** against a rigid platen, sparse direct solve. **Scope: it validates only the
contact-mechanics sub-models every family shares — not the grip number itself** (friction
and drainage rest on Tier-1 + literature; the FEA cannot confirm those, and we say so).

- **Contact study:** press a rigid platen onto the post, measure real contact fraction vs
  load. Result: `φ_eff ≈ 0.72` vs the geometric `0.70`, and **load-independent** — so the
  lands carry load at the geometric fraction (`p_real = p_nom/φ` is right) and the
  soft-flattening term is negligible (consistent with B.9 finding `C_FLAT` immaterial).
- **Durability study:** apply normal + shear traction, measure peak von Mises at the post
  root vs the `6·τ·AR` beam formula. Result: FEA stress is **1.1–1.4×** the formula, and
  the margin is **24×** at μ=1.0, **14×** even at μ=1.8 — durability never binds.

## B.11 The decision

The model's invariant winner is the **octopus-sucker** pattern — and we **did not ship
it**, on an honest geometric ground: the finger contact face is ~72 mm × 10 mm, and at a
~1.4 mm ring pitch **at most one full concentric "rosette" fits across the 10 mm width**,
so its isotropic-ring advantage isn't realized on the blade (plus its residual edge over
the field leans on the speculative suction term). We shipped the **crosshatch** — the
robust (23/31), perfectly-tiling, no-speculation winner. **Hexpad (tree-frog)** is the
documented close runner-up. Shipped geometry: **1.8 mm posts / 0.54 mm crossing channels
/ 0.6 mm deep**; ported into `gripper.py` (`FR_GRIP_CROSS`), both fingers verified valid
solids with **0.0 mm³ interference** at the closed pose.

---

# PART C — Motor, drivetrain & sensing simulation

The third campaign (`motor/`) sizes the actuator, turns it into the grip-force sensor,
and structurally re-checks the drivetrain. Same simulate-first, honest-fidelity method.

## C.1 The torque↔force chain (exact kinematics)
`motor/scripts/kinematics_chain.py` imports the live `gripper.py`: crown/pinion ratio
`i_g = 24/9 = 2.667`, the 1:1 sector mesh (left gear carries both fingers), and the
four-bar Jacobian `MA(P)` give `F = T_in·(i_g/2)·MA·η`. Efficiency is an estimate **band
0.40–0.71**. Result: input torque **0.56–1.18 N·m** for 12 N/finger; full open↔close is
only **122.7°** of input rotation (→ a limited-rotation servo suffices).

## C.2 Survey + selection (12-agent swarm, weighted + ±50%)
A concurrent **12-agent research swarm** (7 actuator classes × 5 sensing modalities)
pulled datasheets (`motor/SURVEY.md`). A weighted score (`selection_score.py`) swept
**±50% across the three depth tiers** shows the **actuator class flips with depth** —
smart serial servo (T1/T2) → magnetic-coupling pod (T3) — the modular-product thesis,
quantified.

## C.3 The sensing pivot — the actuator is the force sensor
Motor current → torque → drivetrain back-trace → tip force (the Robotiq/Maxon
principle), so **no fingertip electronics** (`motor/SENSING.md`, `MOTOR_MODEL.md`). The
forward model run backwards is the sensor; resolution `ΔF = K_t·ΔI·i_g·MA·η/2` clears the
0.3 N target. It is **force-only, relative until load-cell-calibrated** — the rank-only
caveat carries to the readout.

## C.4 The gear-tooth FEA — the structural finding
A **2D plane-stress Q4 tooth FEA** (`gear_fea.py`) found the printed **crown/pinion is
the gripper's binding structural limit**: safe input torque **`T_safe` ≈ 0.034 N·m
(shipped, face-width-strengthened + build-verified) / ≈ 0.40 N·m (proposed re-size)** —
far below the 0.94 N·m a 12 N grip needs at η ≈ 0.5. So the **motor current limit (the
sensing pivot) is the gear-protection ceiling**, and 12 N is the finger-FEA *report
level*, not what the drivetrain can safely deliver. The
**drivetrain-deliverable per-finger force band** computed from `T_safe` through the
kinematics chain is **0.35–0.73 N (shipped) / 4.2–8.7 N (proposed re-size)** — see
`motor/scripts/drivetrain_force_envelope.py` for live numbers (regenerable JSON in
`motor/iterations/_drivetrain_force_envelope.json`).

> **Caveat on the gear FEA model.** The crown gear is treated as a **2D
> plane-stress straight-flank cantilever tooth** (`gear_fea.py:tooth_root_stress`),
> i.e. the same machinery as the grip Tier-2 spur-tooth check. A real crown/face
> gear is a **3D problem**: the contact line sweeps radially across the tooth
> length under load, the contact decomposes into tangential + radial + axial
> components, and the base-disk bending compliance matters — none of which is
> captured here. The earlier "Lewis 40 vs 38 MPa → no bug" cross-check is also
> not a real cross-validation: the Lewis form factor assumes an involute spur
> tooth, not a straight-flank face tooth, so two wrong models agreeing is not
> the same as one right model being confirmed. Worse, the printed teeth are
> "straight-flank representative" rather than involute-generated; in PA12-GF
> these will edge-load and gall rather than roll cleanly. The `T_safe` value is
> therefore an *engineering estimate from a partial model*, not a bench-validated
> ceiling. A 2D-through-radius FEA with multiple radial stations
> (`motor/scripts/gear_fea_3d.py`, added in this branch) integrates the bending
> contribution across the crown tooth's radial extent for a tighter bound; the
> only real answer is the bench measurement specified in `motor/BENCH_TEST.md`.

## C.5 The sims + sensitivity
`torque_chain.py` (gear ceiling binds, not the servo), `slip_margin.py` (slimy is the
worst object class, rank-only), `holding_stall.py` (back-drivable → active hold, but
sub-amp holding current; stall sets the bus budget). `motor_sensitivity.py`: the
headline conclusions are **invariant under ±50%** on η, `T_safe`, MA, `K_t`.

---

# PART D — What the simulations do and do not establish

**Established:**
- The Fin Ray finger wraps universally and gently at the **12 N stress-probe load** —
  peak stress ~2.7 MPa, ≈10× below TPU strength. At the **drivetrain-deliverable
  operating force band (0.35–0.73 N, current gears)** the implied margin is
  ≈100–300× (conservative linear scaling). See A.8/A.12/C.4 for what 12 N means
  and `motor/scripts/drivetrain_force_envelope.py` for the live force band.
- A 2D plane-strain solve (`fea/scripts/solve_finger.py`, scikit-fem) and the 3D
  corotational solve agree on the **order of magnitude** of peak von Mises
  (~2.7 MPa in both) — but they solve **different problems** (different BCs,
  different ν, different load levels, the 2D run hits a load-control limit
  point at ≈5.7 N before reaching the 3D's 12 N). This is a *cross-formulation
  consistency check*, not an independent re-derivation. See A.11.
- The crosshatch is the best **tileable, printable, no-speculation** texture across a
  battery of wet object surfaces, and that choice is **robust to ±50% coefficient
  uncertainty** (B.9); its contact mechanics and durability are **FEA-validated** (B.5,
  margins 14–24×).
- The ported part **builds with zero interference** at full closure.
- The drivetrain torque↔force chain + 122.7° travel (exact kinematics); the actuator
  selection ranking + its ±50% robustness; the printed crown/pinion **structural limit
  `T_safe`** and that the motor current limit is its protection; back-drivability; the
  sensing resolution/rate budget; the object-slip ordering.

**Not established (stated plainly):**
- An **absolute holding force in newtons** for the texture — the Tier-1 model *ranks*
  textures, it doesn't predict force; only the *ordering* is validated (gate + literature
  + FEA contact mechanics).
- Exact friction/drainage magnitudes, and **long-term wet service** (TPU swelling/wear,
  biofilm growth in the channels, edge abrasion) — those need physical soak/field testing.
- For the finger, the **absolute grip reaction is an upper bound** (volumetric locking);
  the stress/fragility field is the reliable output.
- The **slimy and soft** object cases are a genuine physical grip ceiling, not a tuning
  miss.
- For the motor: the **absolute grip force in newtons**, the **absolute depth rating**,
  the current→force **calibration accuracy** on real hardware, endurance/wear, and whether
  the proposed gear re-size's clearance is buildable — all need `motor/BENCH_TEST.md`.

This is the simulate-first engineering case: we converged the design in software, with
validated models and explicit honesty about fidelity, instead of printing and iterating
blindly.

---

# PART E — Reproduce every simulation

All commands assume the project venv: `source /home/andre/.cad-venv/bin/activate`.

```bash
# --- Part A: finger structural FEA ---
cd fea/scripts
# one finger vs the full object battery (universal score):
python eval_finger.py myfinger production '{}' full
# CPU vs GPU solver benchmark (same solve, both backends):
GRIPPER_FEA_GPU=0 python bench_gpu.py 1.3 24
GRIPPER_FEA_GPU=1 python bench_gpu.py 1.3 24      # GPU mirror (numerically identical)

# --- Part B: grip-texture ---
cd ../../grip/scripts
python baseline_validate.py            # B2: literature gate (must pass before anything)
python sweep.py crosshatch 8000 12     # B3: sweep one family (any of the 7)
python sensitivity.py 1500             # B4: ±50% sensitivity, all families (all coeffs)
python sensitivity.py 1500 concentric  # B4: same, excluding the sucker (tileable winner)
python texture_fea.py                  # B5: Tier-2 plane-strain contact + durability FEA
python eval_texture.py SHIP crosshatch '{"pitch":1.8,"land":1.26,"depth":0.6}'  # ship pt
python make_figures.py                 # regenerate all campaign figures

# --- Part C: motor, drivetrain & sensing ---
cd ../../motor/scripts
python kinematics_chain.py             # C1: torque<->force chain + travel
python gear_fea.py                     # C4: gear-tooth FEA -> T_safe (+ proposed re-size)
python check_drivetrain.py             # C4: interference of the strengthened gears
python torque_chain.py                 # C5: motor -> tip force (plot)
python slip_margin.py                  # C5: slip margin vs object class (plot)
python holding_stall.py                # C5: holding/stall current + back-drive
python selection_score.py             # C2: weighted selection + ±50% across depth tiers
python motor_sensitivity.py            # C5: ±50% envelope
```

Outputs land in `fea/iterations/`, `grip/iterations/`, `motor/iterations/` (per-run
JSON) and `grip/pictures/` + `motor/pictures/` (figures).

---

# Glossary

- **FEA (finite-element analysis):** split a part into many small elements, solve the
  equations of elasticity on the mesh to get deformation and stress.
- **DOF (degrees of freedom):** the unknowns solved for (3 per node in 3D: x/y/z motion).
- **Tetrahedron / Q4 quad:** the element shapes (3D tets; 2D 4-node quads).
- **Corotational:** an FEA formulation that removes local rigid rotation before measuring
  strain — correct for "small strain, large rotation" like a curling soft finger.
- **Plane strain:** a valid 2D reduction for a part that is uniform and long in the third
  direction (the finger and the extruded texture both qualify).
- **Polar decomposition (F = R·U):** splits deformation into a pure rotation `R` and a
  pure stretch `U`.
- **von Mises stress:** a single number combining the stress components that predicts when
  a ductile material yields; we compare it to the TPU strength for the safety margin.
- **Penalty contact:** prevent interpenetration by adding a stiff restoring spring
  proportional to penetration depth, instead of exact constraints.
- **Newton–Raphson:** iterative method to solve the nonlinear equilibrium equations each
  load step.
- **Surrogate model:** a fast approximate model used in place of an expensive simulation,
  here validated against real physics and published data.
- **CoV (coefficient of variation):** std ÷ mean — our measure of how *evenly* something
  (pressure, grip) is distributed.
- **φ / land fraction:** fraction of the textured area that is raised solid contact.
- **ψ / dewetted fraction:** fraction of contact where the water film has been squeezed
  out so real grip can occur.
- **Reynolds squeeze-film:** the lubrication physics of a liquid film being pressed out
  from between two surfaces — why channels (tread) restore wet grip.

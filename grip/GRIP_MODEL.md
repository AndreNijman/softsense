# The grip model — physics, coefficients, validation

The grip score is a **Tier-1 mechanistic surrogate**
([`scripts/grip_model.py`](scripts/grip_model.py)): a composition of textbook
relations, fast enough (~µs) to run hundreds of thousands of sims. It is a
*hypothesis about what matters* for underwater grip — its job is to **rank**
textures, not to predict an absolute holding force. Read this with that scope.

## Terms

A texture is resolved ([`patterns.py`](scripts/patterns.py)) to neutral descriptors
(land fraction φ, land/channel widths, depth, edge density, drain path, directional
factors M, …). For each object **condition** the model computes an effective holding
coefficient:

1. **Soft-land flattening** — `φ_eff = clamp(φ·(1+C_FLAT·p_real/E'), φ, 1)`. Real
   contact grows with load. *Tier-2 FEA shows this is negligible at our pressures
   (§Validation), so C_FLAT is immaterial.*
2. **Elastomer friction** — Briscoe & Tabor: interfacial `τ = τ₀ + α·p`. The adhesion
   part `τ₀·φ_eff/p_nom` scales with **real contact area**; the load part `α` does not.
3. **As-printed TPU slickness** — eSUN eTPU-95A prints a glossy, low-friction skin. A
   flat land keeps only `SKIN_SLICK` of ideal adhesion; **edges/channel walls deglaze
   it** back toward ideal (`deglaze = edge_density / EDGE_DEGLAZE`). This is why
   texture is needed even before drainage.
4. **Wet drainage** — Reynolds squeeze-film over the drain path (half-land to the
   nearest channel), gated by channel capacity, boosted by edge film-piercing →
   dewetted fraction ψ. Smooth/closed-pocket patterns → ψ→0 (hydroplane); fine open
   channels → ψ→1 (grip recovered). The tyre-tread / tree-frog mechanism.
5. **Partial-slip edge efficiency** — a big monolithic compliant pad peels from its
   edge; subdividing into small lands resets the edge stress at each so partial-slip
   efficiency rises toward 1. `η = ETA_FLOOR + (1-ETA_FLOOR)·LAND_CRIT/(LAND_CRIT+land)`.
   **This is a monotone partial-slip surrogate [ESTIMATE], not the gecko
   mechanism.** Gecko adhesion is van-der-Waals on hierarchical fibrils, a
   different physics entirely; Cattaneo–Mindlin partial slip scales as
   `1−(T/μN)^(2/3)` for a Hertzian sphere, not as a Hill curve in land size.
   The *direction* of the effect (small discrete contacts hold better than one
   big monolithic pad) is supported by tyre-tread and tree-frog wet-grip
   literature; the *functional form* here is engineering convenience.
6. **Directional coverage** — 1-D ridges resist only cross-slip (mean |sinθ|≈0.64,
   worst≈0); 2-D/iso patterns approach 1 in every direction. Blended
   `W_PRIMARY·M_primary + (1-W_PRIMARY)·M_worst`.
7. **Durability** — root bending `σ_root = 6·τ·AR`; margin vs 25 MPa printed strength.
8. **Micro-suction** — dimple/sucker cavity bonus, **flagged speculative**, wet+smooth
   only.

`μ_eff = ψ·(adhesion·skin·(1-slime) + α + hysteresis) + (1-ψ)·μ_film`, directional
and edge-efficiency applied, capped. Per-condition object score weights holding +
durability − damage; the universal score is the weighted battery mean minus a
grip-inconsistency (coefficient-of-variation) penalty.

## Coefficients and their provenance

Every coefficient in `COEFFS` carries a source tag. Summary:

| tag | meaning | examples |
|---|---|---|
| `[cited]` | from literature | `TAU0`, `ALPHA` (Briscoe&Tabor); `MU_FILM` (tyre wet-skid); `ETA_WATER` |
| `[ESTIMATE]` | physically-bounded guess | `T_GRASP`, `H0_FILM`, `LAND_CRIT`, `SKIN_SLICK`, `MU_GOOD` |
| `[PLACEHOLDER]` | tuned to the baseline gate | `CAP0`, `EDGE_PIERCE`, `C_EDGE`, `EDGE_DEGLAZE` |
| `[CALIBRATE]` | fitted vs Tier-2 FEA | `C_FLAT` (→ found immaterial) |
| `[SPECULATIVE]` | low-confidence effect | `SUCT_GAIN` |
| `[project]` | from the finger study | `E_TPU`=40, `NU`=0.42, `STRENGTH`=25 |

Sources for the ordering and mechanisms: Persson (rubber friction & wet skid, 2001);
Briscoe & Tabor (interfacial shear of polymers, 1978); Barnes / Federle / Drotlef
(tree-frog hexagonal wet adhesion, 2006–2013); Tramacere / Baik (octopus sucker wet
attachment, 2013–2017); pneumatic-tyre tread drainage. Absolute μ values are
estimates; the **relative ranking** is what the optimization trusts.

## Validation

**1. Literature gate** ([`baseline_validate.py`](scripts/baseline_validate.py)) — the
model reproduces the published wet-grip ordering of 5 real patterns
(smooth ≪ ridges < tread < tree-frog ≈ sucker), all six checks pass. The swarm was
gated on this.

> ⚠️ **Honest framing.** The [PLACEHOLDER]/[ESTIMATE] coefficients in
> `grip_model.COEFFS` were *chosen* so the gate passes. "Gate passes" is therefore
> a **sufficient condition** test (the model *can be fit* to reproduce the
> published ordering on these 5 patterns), **not a necessary one** (the model
> generalises to textures it wasn't tuned on). Two robustness diagnostics in
> lieu of true out-of-sample data:
>
> - **Coefficient-perturbation robustness** (`baseline_gate_robustness.py`):
>   sweeping each placeholder ±50% from default, one at a time, the gate
>   passes in **89/90 settings (99 %)**. So the gate's pass is **not** tightly
>   tuned to specific coefficient values in a narrow neighbourhood — small
>   perturbations don't break the ordering. This is a real result, but it is
>   still self-referential (the 5 reference patterns are the same patterns the
>   model was tuned on).
> - **Harsher zero-placeholder check**: if we zero out `EDGE_PIERCE`, `C_EDGE`,
>   `C_HYS`, `SUCT_GAIN` and tiny-out `CAP0` (i.e. let only the [cited]
>   Briscoe–Tabor / tyre-wet-skid terms drive the model), **the gate FAILS** —
>   "tread beats ridges" no longer holds. So the placeholder terms (drainage,
>   edge piercing, hysteresis) *are* doing real work; cited physics alone isn't
>   enough to reproduce the ordering.
>
> A true out-of-sample test would add reference patterns the model has never
> seen (a recent bio-inspired wet-grip study not used to tune the model) and
> check whether the model places them correctly. We have not done that — the
> reference patterns in `baseline_validate.PATTERNS` *are* the patterns whose
> ordering was used to tune the placeholder coefficients.
>
> **Dispute on the published μ values reproduced by the gate.** The
> "smooth_wet μ_hold ≈ 0.07" the gate emits is the **dynamic aquaplaning floor**
> (tyre wet-skid at speed), **not** the static smooth-wet TPU coefficient
> (closer to **0.2–0.4** from elastomer-friction literature). The
> "sucker μ_hold ≈ 1.11" mixes the **suction normal-pressure differential**
> mechanism with a **sliding friction** coefficient — they have different
> physical meaning. So even the numbers the gate matches should be read as
> **rank-only**, not calibrated absolute friction.

**2. Tier-2 FEA** ([`texture_fea.py`](scripts/texture_fea.py)) — 2D plane-strain
contact FEA of the shipped crosshatch post. **Scope:** this validates only the
**structural contact-mechanics sub-models** (real-contact-area φ_eff;
root-bending stress against the `6·τ·AR` formula). It does **NOT** validate the
friction or Reynolds-drainage physics — and those are what actually drive the
texture ranking. Specifically:

- The **φ_eff under rigid-platen / flat-top-post / plane-strain** is essentially
  *tautological*: a post pressed straight down on its flat top cannot bulge
  sideways into the gap, so φ_eff comes out at the geometric value and `C_FLAT`
  reads as immaterial. A different test (laterally-confined platen, hyperelastic
  post, higher pressure) might give a different answer; we did not run it.
- The **root durability** check confirms `σ_root = 6·τ·AR` to within 1.1–1.4×
  — useful for design margins, not for ranking.
- The **friction model** (Briscoe–Tabor + skin slickness + edge deglaze) and
  the **Reynolds drainage / channel capacity** physics — the ranking-driving
  terms — are NOT touched by Tier-2.

So the honest claim is: Tier-2 validates that the **structural** sub-models
won't surprise the design, **not** that the ranking is right. The gate (point 1)
and the literature citations are the only checks on the ranking physics.

**3. Coefficient sensitivity** ([`sensitivity.py`](scripts/sensitivity.py)) — ±50% on
every coefficient, re-optimizing all families per setting. Concentric wins 31/31
(invariant); among tileable families crosshatch wins 23/31. **Important framing:**
this proves the **winner-selection** is robust to coefficient uncertainty, not
that the model is right. The same 31/31 result would obtain if the model were a
neural network whose weights all moved together — it's a robustness-of-output
test, not a robustness-of-physics test. Combined with the gate's self-referential
nature (above), the honest summary is: *the ranking that comes out is what this
hypothesis says, and ±50 % wiggling doesn't break it; whether the hypothesis is
right needs bench data.*

## What this model does NOT establish

- An absolute holding force in newtons. It ranks; it does not predict.
- The friction/drainage **magnitudes** — only their *ordering* is validated, and
  even that validation is partially self-referential (gate + literature; the
  Tier-2 FEA only touches the structural sub-models, not the ranking physics).
- Long-term effects (TPU swelling/wear, biofilm growth in the channels, abrasion of
  the post edges). Those are service-life questions for soak/field testing.
- That the model **generalises** to textures it wasn't tuned on. The 5
  reference patterns in the gate *are* the patterns whose ordering was used
  to fit the [PLACEHOLDER] coefficients; a true out-of-sample test (a new
  reference texture the model has never seen) has not been done.
- That the published μ values reproduced by the gate (smooth_wet ≈ 0.07,
  sucker ≈ 1.11) are correct measurements of static friction on TPU; they're
  not — see the dispute box in §Validation.

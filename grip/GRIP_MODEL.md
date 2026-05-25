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
   edge; subdividing into small lands resets the edge stress at each → efficiency →1
   (the fibrillar/gecko benefit). `η = ETA_FLOOR + (1-ETA_FLOOR)·LAND_CRIT/(LAND_CRIT+land)`.
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

**2. Tier-2 FEA** ([`texture_fea.py`](scripts/texture_fea.py)) — 2D plane-strain
contact FEA of the shipped crosshatch post. Validates the **shared contact-mechanics**
sub-models (not the grip number): φ_eff ≈ geometric φ and load-independent (so C_FLAT
is immaterial); root stress = 1.1–1.4× the beam estimate, durability margin 14–24×.

**3. Coefficient sensitivity** ([`sensitivity.py`](scripts/sensitivity.py)) — ±50% on
every coefficient, re-optimizing all families per setting. Concentric wins 31/31
(invariant); among tileable families crosshatch wins 23/31. The conclusions are robust
to the coefficient uncertainty, which is the point of a surrogate-model study.

## What this model does NOT establish

- An absolute holding force in newtons. It ranks; it does not predict.
- The friction/drainage **magnitudes** — only their *ordering* is validated (gate +
  literature). The FEA validates contact mechanics only.
- Long-term effects (TPU swelling/wear, biofilm growth in the channels, abrasion of
  the post edges). Those are service-life questions for soak/field testing.

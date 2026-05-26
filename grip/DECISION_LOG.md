# Grip-texture campaign — full decision log

The blow-by-blow: every approach, dead end, correction and number behind
[`GRIP_TEXTURE.md`](GRIP_TEXTURE.md). Chronological.

> ⚠️ **Updated honest framing (see `OVERNIGHT_FIXES.md` #5–#7, #11).** The
> grip-model "literature gate" is a **sufficient-condition** test (the
> Tier-1 model *can be fit* to reproduce the published wet-grip ordering on
> the 5 reference patterns; the [PLACEHOLDER] coefficients were chosen so
> it does). It is **not** a true out-of-sample test, and the μ values it
> reproduces are **not** calibrated absolute friction
> (smooth-wet μ ≈ 0.07 is the dynamic aquaplaning floor, sucker μ ≈ 1.11
> conflates suction with sliding friction). The shipped crosshatch is the
> **engineering-judgement geometric override** of the model's invariant
> winner (octopus-sucker); the override was applied externally and is
> documented openly in `GRIP_TEXTURE.md §5`. See `GRIP_MODEL.md`
> Validation § for the full honest framing and `baseline_gate_robustness.py`
> for the perturbation diagnostic (89/90 = 99 % robustness on ±50 %
> coefficient sweep). These callouts apply to every "the model says…"
> claim in this log.

## 0. Brief and constraints

Optimize the contact-face grip texture (the finger geometry is already locked).
Method: physics model + agent swarm + lots of sims, fully documented, ending in a
shipped texture and a summary like the finger study. Hard constraints, all of which
shaped the model:

- **Underwater.** Wet grip, not dry grip, is the target. A water film between pad and
  object is the enemy.
- **Every object surface** — smooth, rough, ridged, slimy, soft — not one. (Same
  universality mandate the user enforced on the finger: "works on every shape/size".)
- **eSUN eTPU-95A, as-printed, is slick.** FDM TPU comes out with a glossy
  low-friction skin; the texture has to overcome the material's own slipperiness.
  (User-added requirement mid-campaign.)
- Printable on a Bambu P1S, 0.4 mm hardened nozzle, 0.16 mm layer.

## 1. The gap: the existing texture was never measured

The shipped finger used single-axis ridges (`FR_GRIP_PITCH 2.2`, depth 0.6). The
finger FEA (`fea/scripts/iter_harness.py`) has **no friction and no fluid model** — it
only penalised the teeth for adding pressure unevenness and never scored their grip.
So texture quality was unknown. Two a-priori weaknesses of ridges: directional (no
grip along the ridge axis) and poor wet drainage on a smooth object. → build the
missing physics.

## 2. The model (Tier-1 surrogate)

No tractable first-principles wet-elastomer-friction simulator exists, so a
microsecond **mechanistic surrogate** was built (`grip_model.py`), composing: elastomer
friction (Briscoe-Tabor `τ=τ₀+αp`), wet squeeze-film drainage (Reynolds + channel
capacity), partial-slip edge efficiency (gecko/fibrillar), directional coverage,
root-stress durability, printability, and a flagged-speculative micro-suction term.
Pattern geometry is resolved per family in `patterns.py`. Pressure floor anchored to
the finger's real contact patches: 0.03–0.15 MPa (8–44 mm span × 10 mm depth at the
12 N grip target). Full term list + citations in [`GRIP_MODEL.md`](GRIP_MODEL.md).

Design decision (advisor-driven): the absolute friction numbers are estimates; the
study trusts only the **relative ranking**, and defends it with a literature gate +
sensitivity sweep (below). Tier-2 FEA validates only the shared contact mechanics.

## 3. User-added requirements, folded in

Mid-build the user added two requirements, both incorporated as first-class:

- **Object surface span** — added a **ridged/corrugated** object condition (Ra 80 µm)
  alongside smooth/rough/slimy/soft/curved, so the battery spans "smooth, rough,
  ridgy" surfaces explicitly.
- **As-printed eTPU slickness** — added a `SKIN_SLICK` factor: a flat printed land
  keeps only ~45% of ideal adhesion; edges and channel side-walls deglaze it back.
  This made the smooth control appropriately terrible and made texture's value partly
  about breaking the slick skin, not only drainage.

## 4. Calibration fixes (before trusting the model)

- **Inconsistency metric.** First used `(max−min)/mean`, which let a uniformly-mediocre
  smooth face dodge the penalty that crushed a strong-but-variable texture (smooth
  0.225 > ridge 0.197 — wrong). Switched to **coefficient of variation** (std/mean)
  over the *wet* conditions, threshold 0.35, weight 0.8. Result sane: smooth 0.251 ≪
  ridge 0.512.
- **Dimple drainage.** Closed dimple pockets were getting full drainage credit (and
  thus winning). Fixed: drainage requires an **open** channel network (`n_drain>0`);
  closed pockets drain poorly. Dimple correctly dropped to last.

## 5. The literature gate (go/no-go for the swarm)

`baseline_validate.py` requires the model to reproduce the published wet-grip ordering
of five real patterns before any search. Result:

```
smooth 0.073  <  ridges 0.614  <  tread 0.709  <  treefrog 1.089  ≈  sucker 1.107
```

All six checks pass (smooth worst; ridges>smooth; tread>ridges; both bio patterns
beat tread; bio pair on top). Gate PASSED → swarm released.

## 6. The agent swarm (seven families)

Each family owned by an agent that swept its parameter space, refined, and reported
its champion **plus** its dependence on the speculative/placeholder coefficients. All
numbers below were produced by the agents running the scripts and re-verified.

- **ridge** — champion 0.754 (pitch 1.01/land 0.58/depth 0.5). Depth inert above
  ~0.03 mm (drainage saturates). Rank **not robust to W_PRIMARY** (falls to 0.66 at
  W_PRIMARY 0.4): the `M_worst=0.18` dead-zone along the ridge axis is unfixable.
- **crosshatch** — champion 0.808 (pitch 1.97/land 1.55/depth 1.6). Conservative
  (gap ≥0.5 mm) 0.746. Wins on `M_worst=0.72` and edges that fully deglaze the skin;
  immune to SKIN_SLICK and CAP0 at the optimum. Cost: `φ=(w/λ)²` lowers adhesion area.
- **chevron** — champion 0.797 (angle 85°). The angle optimum is **degenerate** — it
  just maximises transverse-ness toward a ridge with a better worst-direction. Beats
  ridge (+0.05) but loses to crosshatch in every robustness test. Doesn't earn its
  complexity.
- **hexpad** (tree-frog) — champion 0.798 (cell 1.3/channel 0.42). **Robust
  no-speculation winner**: zero suction dependence, immune to SKIN_SLICK/CAP0; only
  EDGE_DEGLAZE moves it. Channel pins to the 0.42 mm print floor → conservative
  variant (0.55 mm channel) 0.734.
- **concentric** (octopus sucker) — champion **0.872**, the highest. Critically, the
  agent isolated the suction: **0.851 with cavity=0 / SUCT_GAIN=0**, still beating
  every other family by ≥0.04. So concentric is a *genuine* winner, not a speculative
  one — but the agent also judged a printed FDM TPU cavity can't actually hold suction
  on real surfaces (stepped rims break the seal).
- **dimple** — champion 0.632, last. Closed pockets → ψ=0.62 on smooth-wet vs 0.997
  for an open network. Never competitive under any perturbation.
- **hierarchical** — champion 0.801 (printable), but the +0.002 edge over crosshatch
  collapses at the safe print floor (0.789) and carries two-scale print risk; the
  micro scale just stacks edge terms. Doesn't clearly beat a single scale.

## 7. Sensitivity (the honesty deliverable)

`sensitivity.py`: ±50% on every coefficient, **re-optimizing all families** at each of
31 settings.

- **All families:** concentric wins **31/31 — fully invariant**, including suction
  halved. The model's raw winner is not a coefficient artifact.
- **Tileable families (concentric excluded):** crosshatch wins **23/31**; hierarchical
  4, chevron 3, hexpad 1. The four are a tie (~0.80±0.01); flips occur only at
  coefficient extremes (hexpad takes #1 only at W_PRIMARY=0.3).

## 8. The ship decision (and an advisor reconciliation)

Concentric is the invariant model winner but is **overridden, geometrically**: the
contact face is ~72×10 mm; concentric rings at ~1.4 mm pitch fit **≤1 rosette across
the 10 mm width**, so the isotropic-ring benefit the `M=0.95/0.80` constants assume is
never realized on the blade. Plus its residual lead leans on the speculative cavity
suction. (No tileability coefficient was added to the model — that would be
confirmation bias; the geometric filter is applied externally and disclosed.)

Initial lean was hexpad (tree-frog: robust, bio-proven, isotropic). But the
exclude-concentric sensitivity data showed **crosshatch is the robust plurality
winner (23/31)**, not hexpad (1/31) — hexpad only wins under the extreme W_PRIMARY=0.3
"slip is uniform in all directions" regime, which a finger with a defined pull-out axis
doesn't face. The reviewer's earlier hexpad lean (from runner-up positions before the
head-to-head) was reconciled to: **ship crosshatch**, document hexpad/concentric as
runners-up with their exact defeat conditions.

## 9. Tier-2 FEA

`texture_fea.py`, 2D plane-strain, shipped crosshatch post. Validates the shared
contact-mechanics sub-models only (explicitly *not* the grip number):

- φ_eff = 0.72 ≈ geometric 0.70, **load-independent** over p_real 0.04–0.74 MPa →
  lands carry load at the geometric fraction; soft-flatten `C_FLAT` immaterial (matches
  sensitivity). No re-run of sensitivity needed.
- Root von-Mises = 1.1–1.4× the `6·τ·AR` beam estimate; durability margin 24× (μ=1.0),
  14× (μ=1.8). Never binding.

(Debugged en route: orphan-node singularity in the masked mesh; contact-force sign;
penalty-contaminated pressures → switched to base-reaction load extraction.)

## 10. Port + verification

Shipped crosshatch: **pitch 1.8 / land 1.26 / channel 0.54 / depth 0.6 mm**, score
0.746. Ported into `gripper.py` (`FR_GRIP_CROSS=True`, `FR_GRIP_PITCH 1.8`,
`FR_GRIP_FLAT 0.54`, `FR_GRIP_DEPTH 0.6`, `FR_GRIP_CROSS_PITCH/GAP 1.8/0.54`) by
keeping the proven ridge-builder and adding a cross-cut that chops the ridges into a
post grid.

**Depth decision:** the sweep champion used 0.9 mm but the model proved depth is
grip-neutral above ~0.3 mm (`chan_cap` saturates), so depth was kept at **0.6 mm** — it
gives the same grip, a safe closed-pose finger-finger gap (0.6 mm to centreline; a
0.9 mm post would close to 0.2 mm), and a lower post aspect (0.48 → safer durability).

Build verified: both fingers are valid solids, **finger-finger interference = 0.0 mm³**
at the closed pose. Conservative ≥0.5 mm channels for reliable TPU printing.

## 11. What is and isn't established (honest scope)

**Established:** crosshatch is the best *tileable, printable, no-speculation* texture
for this finger across a battery of wet object surfaces; the choice is robust to ±50%
coefficient uncertainty (23/31); contact mechanics and durability are FEA-validated
(margins 14–24×); the part builds with zero interference.

**Not established:** an absolute holding force (the model ranks, it doesn't predict);
the friction/drainage *magnitudes* (only their ordering is validated); long-term wet
service (TPU swelling/wear, biofilm in the channels, edge abrasion). Those need
soak/field testing. The slimy and soft cases are the genuine grip ceiling — physics,
not a tuning miss.

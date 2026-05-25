# Chevron family — grip texture analysis

## Champion (fine-grid refined)

| param | value |
|-------|-------|
| pitch | 1.24 mm |
| land  | 0.82 mm |
| depth | 0.41 mm (insensitive — see below) |
| angle | 85 deg |

**Score: 0.7966** (base=0.8900, incon=0.467) — beats ridge champ (0.752), below crosshatch champ (0.807).

Initial sweep (8000 random + grid, 8625 total candidates) peaked at the published
baseline of pitch=1.271/land=0.85/depth=0.41/angle=68.7 → 0.7907. Fine-grid
refinement reveals +0.006 is available by pushing angle from 68→85 and tightening
pitch/land slightly.

## Conservative printable variant

| param | value |
|-------|-------|
| pitch | 1.60 mm |
| land  | 1.00 mm |
| depth | 0.40 mm |
| angle | 70 deg |

**Score: 0.7287** (gap=0.60 mm, min_feat=0.60 mm — well above the 0.42 mm floor).

## Physics: what the angle actually does

The chevron model has only one angle-dependent term:

```
iso = sin(angle)
M_primary = 0.90 + 0.10 * iso     # 0.934 at 20 deg -> 1.000 at 90 deg
M_worst   = 0.35 + 0.30 * iso     # 0.453 at 20 deg -> 0.650 at 90 deg
```

At 85 deg, iso≈0.996 so M_primary=1.000 and M_worst=0.649. This is fully saturated —
pushing to 89 deg gives score=0.7967, a gain of 0.0001. The "optimal" is just
"as close to transverse as possible."

Compared to a plain ridge at the same pitch/land geometry:
- Ridge M_worst = 0.18 (hardcoded; slides along its axis)
- Chevron M_worst = 0.649 (V deflects lateral slip into the arms)

Everything else — phi, edge_dens, chan_cap, drain_path — is identical. (n_drain
differs: ridge=1, chevron=2, but both are > 0 so both enter the open-channel branch
of psi_dewet. The psi outcome is the same.) The V-geometry adds nothing except a
better M_worst.

A ridge scored at the exact same pitch=1.24/land=0.82/depth=0.41 gives **score=0.7459**
vs chevron's **0.7966**: the V-geometry lift is +0.051, entirely from M_worst (0.180→0.649).

## Does chevron beat a plain ridge?

Ridge champion: pitch=1.065/land=0.636/depth=1.44 → **score=0.752**. Chevron at
pitch=1.24/land=0.82/angle=85 → **0.797**. Delta = +0.045. That gap is entirely
attributable to M_worst (0.649 vs 0.18). At W_PRIMARY=0.80 the gap narrows but
chevron still leads (0.806 vs 0.798). At W_PRIMARY=0.40 (multi-directional equal
weighting), chevron wins more strongly (0.778 vs 0.658) because M_worst matters more.

## Does chevron beat crosshatch?

Crosshatch champion: pitch=2.04/land=1.62/depth=1.46 → **score=0.807**. Crosshatch
uses two orthogonal ridge sets giving M_worst=0.72 vs chevron's 0.649. Across all
tested perturbations, crosshatch leads chevron by 0.007–0.016 score units:

| Perturbation    | chevron | xhatch | delta |
|-----------------|---------|--------|-------|
| W_PRIMARY=0.40  | 0.7776  | 0.7930 | −0.016 |
| W_PRIMARY=0.60  | 0.7966  | 0.8072 | −0.011 |
| W_PRIMARY=0.80  | 0.8061  | 0.8191 | −0.013 |
| SKIN_SLICK=0.30 | 0.7851  | 0.8062 | −0.021 |
| SKIN_SLICK=0.60 | 0.8062  | 0.8083 | −0.002 |
| CAP0=0.25       | 0.7966  | 0.8072 | −0.011 |
| CAP0=1.00       | 0.7966  | 0.8072 | −0.011 |

Chevron never beats crosshatch under any tested coefficient variation.

## Depth insensitivity

Depth has zero effect on score from 0.35 to 1.40 mm. The model's drainage and grip
terms are driven by edge_dens, phi, M factors, and land_char — none of which depend
on depth. Depth only appears in chan_cap and aspect. Because psi_dewet=1.00 at this
pitch (the fine-pitch channel drains instantly), chan_cap is irrelevant. The aspect
penalty only kicks in above ASPECT_MAX=3.0 (which requires depth/land > 3.0 = 2.46 mm
at land=0.82). Use the minimum structurally safe depth: **0.40 mm** (2–3 layer lines).

## Manufacturability

Champion gap = 0.420 mm, just at the 0.42 mm floor. This is marginal:
- Gap is nominally printable but any elephant-foot or first-layer squish on a live
  print will close the channel.
- Chevron tips are pointed V-apexes. At angle=85 the tip half-angle is 5 degrees —
  essentially a needle tip. Actual printed tip radius will be ~0.2 mm (one bead width),
  not a sharp point. This is a real geometry, not a model-computed, flaw.
- The conservative variant (gap=0.60 mm) has 43 % more margin and prints reliably.
  Score cost: 0.797 → 0.729 (−0.068). That is a large penalty for safety.
- A middle path: pitch=1.40, land=0.88, depth=0.40, angle=75 → gap=0.52 mm,
  score=0.7517, tip half-angle 15 deg — more robustly printable.

## Verdict

Chevron earns its complexity over plain ridge (+0.051 vs ridge-at-same-geometry, robust to all coefficient
perturbations), but does **not** beat crosshatch (−0.011 gap, consistent across all
sensitivities). The angle optimum is degenerate: higher is always better, converging
to a barely-angled transverse ridge. There is no true chevron-specific optimum —
the model is rewarding M_worst improvement, and crosshatch delivers more of that
(M_worst=0.72) with two full drainage axes vs chevron's one. Additionally, the
champion's 0.420 mm gap is at the minimum printable limit with pointed V-tips that
will not print as modelled. Recommend the conservative variant (0.60 mm gap,
score=0.729) if chevron is selected for fabrication, or crosshatch as the stronger
alternative. Do not carry the fine-grid champion (angle=85, gap=0.420) to print.

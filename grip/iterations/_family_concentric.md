# Concentric family — analysis (2026-05-25)

## Champion

```
pitch=1.375  land=0.932  depth=1.106  cavity=0.593
```

| Variant | Score |
|---|---|
| Full model (SUCT_GAIN=0.25) | **0.8719** |
| SUCT_GAIN=0 (suction disabled) | 0.8505 |
| cavity=0 (no suction geometry, full gain) | 0.8505 |
| cavity=0 + SUCT_GAIN=0 | 0.8505 |
| Best optimised no-cavity concentric | **0.8573** |

Suction (cavity × SUCT_GAIN) accounts for **0.0214 of the 0.8719 score**,
or ~2.5 percentage points. The optimised no-cavity champion scores 0.8573
(+0.0068 over the suction-disabled original champion), because relaxing
the cavity constraint lets the optimiser shift pitch/land.

## Geometry notes

At the champion params: edge_dens = 2.18 /mm, EDGE_DEGLAZE = 2.0 /mm →
deglaze saturates at 1.0, so **SKIN_SLICK is insensitive** (the ring edges
fully restore adhesion regardless of the printed-skin slickness value).
Channel capacity (0.490 mm²/mm) vastly exceeds the trapped film volume
(w × H0_FILM × 1e3 = 0.047), so **CAP0 is also insensitive** — the rings
drain faster than the film can resist. Both saturations are genuine physical
wins for the ring geometry, not model pathologies.

## Suction-dependence analysis

- With SUCT_GAIN=0.25 (default): 0.8719
- With SUCT_GAIN=0.125 (half): 0.8618
- With SUCT_GAIN=0.0 (zero): 0.8505
- Best no-cavity optimum (SUCT_GAIN irrelevant): 0.8573

The ring/edge/drainage contribution alone yields ~0.857. The speculative
suction term adds at most +0.015 on top of the optimised no-cavity result.

## Head-to-head vs other families (no suction, SUCT_GAIN=0)

| Family | Score (default) | Score (SUCT_GAIN=0) |
|---|---|---|
| concentric (cavity=0.593) | 0.8719 | 0.8505 |
| concentric (cavity=0, optimised) | 0.8573 | 0.8573 |
| hierarchical | 0.8108 | 0.8108 |
| crosshatch | 0.8072 | 0.8072 |
| hexpad | 0.7977 | 0.7977 |

Even with suction completely off, the best no-cavity concentric (0.8573)
beats every other family by ≥0.046 points. **The ring geometry wins on
its own merits.**

## Physics

**What rings do well:**
- Four-direction drainage (n_drain=4) removes trapped film isotropically;
  the concentric-plus-radial layout means there is always a channel within
  ~0.47 mm of any land point.
- High edge density (2.18 /mm) from the ring perimeters deglazes the
  printed TPU skin completely and provides high hysteresis-friction under
  rough and ridged objects.
- Near-isotropic directional factors (M_primary=0.95, M_worst=0.80)
  ensure grip is good regardless of pull direction — critical for a gripper
  that may close at any angle.

**Can the printed cavity actually produce suction underwater?**

Almost certainly not on the objects that matter. Micro-suction requires:
(a) a compliant sealing lip that conforms to the object surface,
(b) a smooth, clean, hard surface on the object,
(c) a sealed cavity volume that sustains negative pressure.

A 0.4 mm nozzle / 0.16 mm layer FDM print in eTPU-95A gives a cavity
rim with ~0.16 mm layer steps, not a smooth lip. On any surface rougher
than Ra ~1 µm (smooth acrylic, glass) the steps break the seal. The model
restricts the suction bonus to wet + Ra < 2 µm, which already limits it
to smooth_wet only — but even there, a printed TPU sucker with a stepped
rim is unlikely to maintain the pressure differential needed. Real octopus
suckers have a muscular infundibulum that actively seals; FDM cannot
replicate this.

Verdict on the suction term: treat it as zero. The SUCT_GAIN tag
[SPECULATIVE] is appropriate. Do not use the suction bonus for ranking
decisions.

## Robustness

SKIN_SLICK {0.30, 0.45, 0.60}: score unchanging at 0.8719 (deglaze
saturated; rings fully restore grip regardless of printed-skin quality).
CAP0 {0.25, 0.5, 1.0}: score unchanging at 0.8719 (channel capacity >>
film volume; drainage is not the bottleneck).
SUCT_GAIN {0.0, 0.125, 0.25, 0.5}: scores 0.8505 / 0.8618 / 0.8719 /
0.8890. Only this coefficient moves the number.

## Verdict

Concentric is a **genuine winner, not a speculative one**. The ring
geometry (drainage, edge density, isotropy) scores 0.857 with zero suction
— a clear margin over all other families. The cavity/suction term adds
at most +0.015 on the no-cavity-optimised baseline and should be treated
as zero pending Tier-2 FEA or physical testing. The recommended print
configuration is cavity=0 (eliminates the unverifiable term and simplifies
the geometry) with pitch ~1.48, land ~1.06, depth ~1.02 for a suction-free
score of 0.8573.

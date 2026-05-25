# Dimple family — grip texture analysis

## Champion

| param | value |
|-------|-------|
| pitch | 1.213 mm |
| dia   | 0.785 mm |
| depth | 1.041 mm |

**Score: 0.6315** (base=0.7334, incon=0.477) — lowest of all optimised families.

## Why dimple loses: the drainage diagnosis

Dimple pockets are **closed** (`n_drain=0`). On `smooth_wet` the trapped water film
cannot escape laterally, so `psi_dewet` falls into the closed-pocket branch
(`base = 0.05 + 0.10 * chan_cap = 0.060`). Edge piercing recovers some of this
(pierce=0.60, saturated), but the final dewetted fraction is only **psi=0.624**
versus **psi=0.997** for hexpad's open three-direction channel network on the same
condition. That 0.37-unit psi gap directly suppresses mu_hold on the most
demanding condition and drives the large inconsistency penalty (incon=0.477).

**One sentence:** Dimple loses because closed pockets cannot drain the water film —
psi on smooth_wet is 0.62 vs 1.00 for hexpad, cutting effective friction nearly in
half on the hardest wet condition.

## Suction reliance

With `SUCT_GAIN=0` (no speculative micro-suction):
- Score drops from **0.6315 → 0.5541** (−0.077, a 12 % collapse)
- The champion is adding 0.166 mu units of suction bonus on smooth_wet alone

Dimple is carrying the SPECULATIVE suction term to be competitive at all; its
mechanical (drainage) physics is poor.

## Interconnected dimples — would they fix it?

Connecting dimples with micro-channels would open a drainage network
(`n_drain > 0`). However:

- Drainage requires channel width ≥ 0.42 mm (nozzle limit); connecting dimples
  on a ~1.2 mm pitch leaves almost no land between them.
- Once channels are added, the geometry converges to a **crosshatch or hexpad** —
  the dimple becomes a post/pad pattern with a circular top rather than square.
- Circular pads on a close pitch have *lower* land fraction and worse directional
  grip (M_primary=0.72 vs hexpad's 0.97) than purpose-designed hex cells.
- Conclusion: interconnected dimples do not fix dimple — they become an inferior
  version of hexpad/crosshatch with worse directional factors and no benefit that
  offsets the geometric penalty.

## Robustness under coefficient perturbations

| Perturbation     | dimple | hexpad | winner  |
|------------------|--------|--------|---------|
| baseline         | 0.6315 | 0.7560 | hexpad +0.12 |
| SKIN_SLICK=0.30  | 0.6244 | 0.7560 | hexpad +0.13 |
| SKIN_SLICK=0.60  | 0.6386 | 0.7560 | hexpad +0.12 |
| CAP0=0.25        | 0.6315 | 0.7560 | hexpad +0.12 |
| CAP0=1.0         | 0.6315 | 0.7560 | hexpad +0.12 |
| SUCT_GAIN=0      | 0.5541 | 0.7560 | hexpad +0.20 |
| SUCT_GAIN=0.5    | 0.6987 | 0.7560 | hexpad +0.06 |

Dimple never beats hexpad under any tested perturbation. Its closest approach is at
SUCT_GAIN=0.5 (gap narrows to 0.057), but that requires the speculative suction
coefficient to be twice its baseline value — not a conservative assumption.

## Verdict

Dimple is **not competitive** for this application. Its closed-pocket geometry is
structurally penalised by the drainage model on smooth wet surfaces (the highest-
weight condition). Any redesign that adds drainage converts it into a different
family. Recommend: do not carry dimple to fabrication; invest in hexpad or
concentric for the suction+drainage combination.

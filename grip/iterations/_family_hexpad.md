# hexpad family — tree-frog hex-pad texture

## Champion

**cell=1.3 mm, channel=0.42 mm, depth=0.5 mm** (any depth 0.3–1.2 mm scores identically)
score=0.7977 · base=0.8917 · incon=0.467 · printable=True

Confirmed by `python sweep.py hexpad 8000 12` (8232 candidates) and `eval_texture.py`.

## Conservative printable variant

**cell=1.2 mm, channel=0.55 mm, depth=0.5 mm**
score=0.7337 · base=0.8729 · incon=0.524 · printable=True
Score cost vs champion: −0.064 (−8%). Minimum printed feature = 0.55 mm — safe margin
above the 0.42 mm absolute print floor. Recommend depth ≥ 0.5 mm so the 0.55 mm
channel is a real groove (AR=0.45), not a cosmetic scratch.

## Tree-frog mechanism in this model

1. **Short drain path** (cell/3 = 0.43 mm): psi_dewet reaches ~1.0 on every condition
   because the squeeze-film drains completely in t_drain << T_GRASP=2 s. No residual
   hydroplaning — solid contact is established.
2. **High edge density** (2.01 /mm, hex lattice): edge_dens >= EDGE_DEGLAZE=2.0, so
   deglaze=1.0 and skin=1.0. The printed TPU gloss layer is fully broken by the six-sided
   pad perimeter; the slick-skin penalty (SKIN_SLICK=0.45) is entirely overcome by edge
   geometry, not material choice.
3. **Near-isotropic grip** (M_primary=0.97, M_worst=0.85): the three-direction channel
   network means no weak pull-out axis; the hexpad resists rotation and skew without a
   dedicated anisotropic feature.
4. **Edge efficiency** (eta_edge): cell=1.3 mm < LAND_CRIT=2.0 mm, so partial-slip
   efficiency is high (~0.88), recovering most of the gecko-style benefit.

## Depth insensitivity — finding and interpretation

Score is identical from h=0.3 to h=1.2 mm. Root cause: chan_cap = channel × depth =
0.42 × h. The cap_ratio = chan_cap / (w × H0_FILM_mm) = (0.42h)/(1.3 × 0.05) = 6.46h.
At h=0.3, cap_ratio=1.94 >> CAP0=0.5, so the drainage gate is already clamped to 1.0.
No additional depth opens any new drainage path — the model only integrates one channel
cross-section per unit width, not a length-varying Reynolds problem.

**Is this physical or a model gap?** Partly a model simplification. Real channels would
gain slightly from deeper grooves at very high flow rates or faster grasps, but for slow
(2 s) wet contact at sub-mm drain paths, shallow channels genuinely do saturate. The
near-zero aspect ratios (AR=0.23 at h=0.3) are structurally fine. Recommend h=0.5 mm as
the print-safe practical minimum (yields a visible, mechanically robust groove).

## Robustness / coefficient sensitivities

| Coefficient         | Range tested  | Score range   | Rank stable? |
|---------------------|---------------|---------------|--------------|
| SKIN_SLICK          | 0.30–0.60     | 0.7977–0.7977 | Yes (deglaze=1.0 saturated) |
| CAP0                | 0.25–1.0      | 0.7977–0.7977 | Yes (cap_ratio >> CAP0 at h≥0.3) |
| EDGE_DEGLAZE        | 1.0–3.0       | 0.7319–0.7977 | Sensitive at 3.0 (−0.066) |
| W_PRIMARY           | 0.4–0.8       | 0.7916–0.8038 | Robust (±0.006) |
| SUCT_GAIN           | 0.01–1.0      | 0.7977–0.7977 | Immune (hexpad suction=0) |

EDGE_DEGLAZE is the one real vulnerability: if the true threshold is 3.0 /mm (edges
deglaze more weakly), edge_dens=2.01 /mm only partially deglazes (deglaze=0.67, skin=0.82)
and the score drops to 0.732. This is a model-parameter uncertainty, not a design flaw;
the conservative variant (cell=1.2, channel=0.55, edge_dens higher) slightly improves
resilience to this scenario.

hexpad does NOT use suction (geom["suction"]=0.0). Its performance is entirely drainage
+ edge-deglaze driven, which is solid literature-backed physics. Rank is robust.

## Manufacturability notes

- **Channel=0.42 mm is the absolute Bambu P1S print floor.** Reliable TPU channel
  printing requires ≥2 nozzle widths clearance; at 0.42 mm a single-extrusion channel
  may under-fill or fuse on TPU. **Use the conservative variant (0.55 mm) for
  first hardware print.**
- Channel depth: h≥0.5 mm recommended so channels are positively engraved and survive
  TPU over-squish. h=0.3 mm may print as a shallow groove that closes on contact.
- Cell=1.3 mm is 3.25 nozzle widths — well printable, likely 2–3 perimeter lines across.
- aspect ratio max across the range = 0.92 (at h=1.2 mm) — far below ASPECT_MAX=3.0.
  No structural concern.

# Crosshatch family — iteration report

**Pattern:** Two orthogonal ridge sets crossing to form square posts (tire-tread geometry).
Channels run in both X and Y axes. Multidirectional by design.

## Champion

| param  | value |
|--------|-------|
| pitch  | 1.971 mm |
| land   | 1.549 mm |
| depth  | 1.596 mm |

**Score: 0.8083** | base=0.8853 | incon=0.446 | printable=True  
Geometry: phi=0.618, gap=0.422 mm, edge_dens=2.03/mm, aspect=1.03, M_worst=0.72

*Confirmed by `eval_texture.py xhatch_champ` above.*

## Alternates

| label | pitch | land | depth | score | notes |
|-------|-------|------|-------|-------|-------|
| Alt-A | 2.042 | 1.621 | 1.456 | 0.8072 | prior baseline champion; 0.001 lower |
| Alt-B | 1.916 | 1.495 | 1.555 | 0.8067 | slightly finer pitch, equivalent result |

Score plateau is flat: top ~15 candidates span only 0.001 score units. Any of these three
prints identically well and performs indistinguishably in the model.

## Conservative variant (min feature >= 0.5 mm)

pitch=1.8, land=1.26, depth=0.9 → **score=0.7462** (cost: -0.062, -7.7%)  
phi=0.490, gap=0.540 mm, edge_dens=2.22/mm, aspect=0.71. Safe margin for 0.4 mm nozzle.

## Physics: why this pitch/land/depth wins

Crosshatch accumulates from three distinct mechanisms:

1. **phi penalty is real but bounded.** phi=(w/lam)^2 for square posts, so phi=0.618
   vs a ridge's w/lam≈0.80 — a ~23% area reduction. That directly cuts mu_adh. The
   optimizer converges to high land/pitch ratios (land/pitch≈0.79) to partially
   recover phi; the narrowest printable gap (0.42 mm) is the active constraint.

2. **Edge deglazing is the dominant term.** eSUN eTPU-95A prints with a glossy skin
   (SKIN_SLICK=0.45). Edge density 4/lam resets this skin to unity once edge_dens
   reaches EDGE_DEGLAZE=2.0/mm — which the champion achieves. At the optimum,
   skin=1.0 and SKIN_SLICK becomes irrelevant; the channel edges do the work.

3. **Drainage saturates quickly.** cap_ratio=chan_cap/(w*H0_FILM)≈8.7 >> CAP0=0.5,
   so gate=1.0 regardless of CAP0. t_drain=0.062s << T_GRASP=2.0s at p_real≈0.16 MPa;
   psi(smooth_wet)=0.988. Both drainage mechanisms are saturated — depth only matters
   enough to provide the cap_ratio >> 1 condition (any h > 0.5 mm suffices).

4. **M_worst=0.72 is the family's key selling point.** Ridges score M_worst=0.18 (nearly
   zero crosswise grip); crosshatch holds 72% of peak grip at 45 deg slip, which matters
   greatly when the score weights worst-direction as (1-W_PRIMARY)=0.40.

## Sensitivities

| perturbation | champion score | delta |
|---|---|---|
| baseline | 0.8083 | — |
| SKIN_SLICK=0.30 | 0.8083 | 0.000 (edge-saturated, immune) |
| SKIN_SLICK=0.60 | 0.8083 | 0.000 (edge-saturated, immune) |
| CAP0=0.25 | 0.8083 | 0.000 (channel hugely oversized) |
| CAP0=1.0 | 0.8083 | 0.000 (channel hugely oversized) |
| W_PRIMARY=0.40 | 0.7940 | −0.014 (more weight on M_worst=0.72 — still good) |
| W_PRIMARY=0.80 | 0.8199 | +0.012 (less weight on worst dir — score rises) |

SKIN_SLICK and CAP0 have zero effect because the champion is in a saturated regime for
both. Rank among families is robust to W_PRIMARY changes — crosshatch at 0.808 sits
above ridge (~0.76) and below hexpad (~0.83) regardless.

## Print caveats

- Gap = 0.422 mm is 1.005× the 0.42 mm floor. A worn nozzle or slight over-extrusion
  can close the channel. Use the conservative variant (gap=0.540 mm) for first prints.
- Aspect ratio = 1.03 is safe (ASPECT_MAX=3.0). No tip-over risk.
- Depth=1.596 mm requires 10 layers at 0.16 mm layer height. Verify seam alignment
  does not merge posts across channels.
- Square post tips (~1.55×1.55 mm) print cleanly on the P1S; no bridging required.

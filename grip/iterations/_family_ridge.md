# Ridge family — optimisation report

## Champion

| param | value |
|-------|-------|
| pitch | 1.010 mm |
| land  | 0.580 mm |
| depth | 0.500 mm (any >= 0.30 is equal; see depth note) |

**Score: 0.7536** (base 0.848, incon 0.468)
phi=0.574  gap=0.430 mm  edge_dens=1.98 /mm  aspect=0.86

Per-condition mu_hold: smooth_wet 0.742, rough_wet 1.472, ridged_wet 1.472,
slimy 0.382, soft_wet 0.822, small_curved 0.547, dry_smooth 0.753.
All safety margins > 16 (well clear of the 1.2 hard-fail threshold).

## Conservative variant (min feature >= 0.5 mm)

pitch=1.120 mm, land=0.620 mm, depth=0.500 mm
**Score: 0.7160** — cost: -0.038 vs champion.
Gap=0.500 mm satisfies the conservative 0.5 mm floor, removing the
risk of the 0.43 mm gap bridging on a 0.4 mm nozzle.

## Alternates

- **Alt-1 (stiffer):** pitch=1.010, land=0.580, depth=1.000 — score=0.7536 (equal),
  aspect=1.72; taller ridges are stiffer in-plane but score is identical (depth-flat).
- **Alt-2 (relaxed pitch):** pitch=1.200, land=0.700, depth=0.500 — score=0.7148,
  minfeat=0.500 mm; score penalty -0.039 for generous print margins.

## Physics — why this pitch/land wins

Short pitch (~1 mm) maximises edge density (~2.0 /mm), which drives both the
deglaze term (overcoming eTPU's slick FDM skin) and hysteresis friction. Land
fraction phi~0.57 is the sweet spot: enough real contact area for adhesion while
keeping the drain path (= land/2 = 0.29 mm) short enough that even the thin
50 µm water film drains in << 2 s at nominal pressure — psi_dewet > 0.998 across
all conditions. The low aspect ratio (0.86) keeps bending-stress margins high
(worst condition margin=16.6).

**Depth insensitivity:** The channel-capacity gate saturates at a depth of
only ~0.034 mm (chan_cap >> CAP0 * w * H0_FILM for any printable depth). This
means depth contributes nothing to drainage once you are above the print floor;
the controlling variables are pitch and land ratio exclusively. Choose depth 0.5 mm
for adequate stiffness without unnecessary material.

## Key sensitivities

| perturbation | score | delta |
|---|---|---|
| SKIN_SLICK=0.30 (slicker skin) | 0.7531 | -0.0005 |
| SKIN_SLICK=0.60 (better skin) | 0.7541 | +0.0005 |
| CAP0=0.25 | 0.7536 | 0.0000 |
| CAP0=1.00 | 0.7536 | 0.0000 |
| W_PRIMARY=0.4 (slip direction matters more) | 0.6605 | **-0.093** |
| W_PRIMARY=0.8 (pull-out dominates) | 0.8002 | +0.047 |

SKIN_SLICK and CAP0 are essentially irrelevant. W_PRIMARY is the only coefficient
that materially shifts the score: when cross-axis slip is weighted equally with
pull-out (W_PRIMARY=0.4), ridge drops to 0.66 while hexpad stays at 0.75 —
ridge loses its rank against isotropic families under that assumption.

## Print caveats (Bambu P1S, 0.4 mm nozzle, eTPU-95A)

- Champion gap = 0.430 mm = 1.07x the 0.42 mm printability floor — this is
  tight. Any over-extrusion or elephant-foot at layer 1 may bridge the channel.
  Strongly recommend first-layer live-adjust and a 0.05 mm gap-compensation
  offset in the slicer, or use the conservative variant (gap=0.500 mm).
- Depth >= 0.30 mm (aspect <= 0.52) is easy; no aspect-ratio penalty applies
  below depth=1.74 mm (ASPECT_MAX=3.0 threshold).
- Ridge is single-axis drainage (n_drain=1): orient ridges transverse to the
  primary pull-out direction. Axial slip (along ridges) is barely resisted
  (M_worst=0.18); do not rely on this texture where lateral roll is a concern.

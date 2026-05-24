# Fin Ray finger — design-iteration log (FEA-driven)

Goal: make the grasp load **distribute across the whole finger** and make the
**top of the finger morph over the object** (wrap), instead of all the load sitting
in the lower-mid ribs while the tip stays straight and unloaded (the problem in the
first 3D FEA, `fea/fea3d/wrap_stages.png`).

Each iteration changes **one geometry lever** on the real `gripper.py` Fin Ray
finger, re-runs a high-quality 3D FEA, and is committed + pushed with its data,
pictures, and notes. Harness: `fea/scripts/iter_harness.py`.

## Method (frozen across all iterations for fair comparison)
- **FEA:** full 3D corotational finite-element (linear tets, 3 z-layers,
  ~25k tets / ~20k DOF), penalty contact, Newton–Raphson, displacement-stepped.
- **Boundary condition (corrected):** the finger is **clamped at the two pin-bore
  rims (C and D)** — the real coupler-mounted pivots — *not* a bottom slab. Both
  bore-rim node rings are fixed in all 3 translations.
- **Grasp scenario (frozen):** rigid amphora-neck cylinder R=22 mm, centre y=80 mm,
  pressed 10 mm into the contact face over 24 steps, kpen=2000.
- **Material:** TPU ~95A, E=40 MPa, ν=0.42 (assumed; ν relaxed for linear-tet
  locking, per the bundle).
- **Mesh density frozen** (gmsh 0.5–1.3 mm); only the geometry changes.

## Metrics (defined up front)
| Metric | Meaning | Target |
|---|---|---|
| `engage_y_frac` | contacted height / finger length | ≥ 0.70 |
| `top_third_force_frac` | share of contact force in the upper third | ≥ 0.20 |
| `tip_inward_mm` | apex displacement toward the object (the wrap) | > baseline, clearly |
| `stress_spread_frac` | fraction of elements above 0.3×peak vM (load shared) | higher = better |
| `margin_x` | TPU strength (25 MPa) / peak vM (stay fragile-safe) | ≥ 5 |

**Stop condition:** all of `engage_y_frac ≥ 0.70`, `top_third_force_frac ≥ 0.20`,
`tip_inward_mm` clearly above baseline, `margin_x ≥ 5` — or 6 iterations, whichever
first. Then land the winning FR_* values into `gripper.py` and regenerate.

## Results
| iter | change | engage | top‑⅓ | tip‑in (mm) | spread | max vM | margin | verdict |
|---|---|---|---|---|---|---|---|---|
| iter00 | baseline, corrected 2‑bore clamp | 0.073 | 0.00 | **−11.8** | 0.031 | 8.86 | 2.82 | reference — problem confirmed |

## Log

### iter00 — baseline (corrected 2-bore clamp)
The first realistic-BC run. Pinning only the two pin bores (C, D), as the real
coupler does, makes the failure **worse and clearer** than the render: contact is a
6 mm band at mid-finger (`engage=0.073`, all force in the middle third, **top third
gets zero**), and the apex actually moves **−11.8 mm = AWAY from the object** — the
upper finger rotates rigidly about the pins instead of the lattice shearing into a
wrap. Stress piles into the contact band (`spread=0.031`, peak 8.86 MPa, **margin
2.82× — below the 5× gentle-grip floor**). Diagnosis: the finger acts as a stiff
lever about the base pins, not a compliant Fin Ray. The fix must make the rib
lattice shear (more compliance / more ribs) and stop the upper finger behaving as a
rigid wedge (less taper). Distributing contact will also raise the margin.
**Decision:** sweep compliance (FR_WALL), rib density (FR_N_RIBS), taper
(FR_TIP_WIDTH), tip cap (FR_INSET_TIP) and rib slant (FR_RIB_SLANT_DEG) in parallel.

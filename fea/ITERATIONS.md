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
| r1_wall20 | FR_WALL 2.8→2.0 | 0.053 | 0.00 | −8.8 | 0.028 | 7.46 | 3.35 | no top engage |
| r1_wall15 | FR_WALL 2.8→1.5 | 0.053 | 0.00 | −7.0 | 0.071 | 4.47 | 5.59 | margin↑ but grip→8N (confounded) |
| r1_ribs16 | FR_N_RIBS 10→16 | 0.053 | 0.00 | −14.3 | 0.020 | 11.40 | 2.19 | worse (stiffer lever) |
| r1_ribs22 | FR_N_RIBS 10→22 | — | — | — | — | — | — | incomplete (agent didn't wait) |
| r1_tip10 | FR_TIP_WIDTH 5→10 | 0.073 | 0.00 | −11.5 | 0.069 | 6.37 | 3.93 | no top engage |
| r1_tip16 | FR_TIP_WIDTH 5→16 | 0.073 | 0.00 | −11.8 | 0.074 | 5.65 | 4.42 | no top engage |
| r1_tipcap05 | FR_INSET_TIP 3→0.5 | 0.073 | 0.00 | −11.5 | 0.041 | 8.02 | 3.12 | no top engage |
| r1_slant22 | FR_RIB_SLANT 38→22 | 0.053 | 0.00 | −10.9 | 0.031 | 8.17 | 3.06 | worse engage |
| — | *rows above at full press=10mm; rows below at the corrected 8mm closure (grip in parens)* | | | | | | | |
| iter00b | baseline @8mm closure (grip 24.5N) | 0.053 | 0.00 | −9.4 | 0.198 | 3.87 | 6.46 | reference (contact=22 nodes) |
| r2_spinetip10 | spine 2.8→1.0 @tip (grip 21.5N) | 0.053 | 0.00 | −9.1 | 0.219 | 3.46 | 7.22 | DEAD — contact still 22, no wrap |

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

### Round 1 — uniform single-lever sweep (8 variants, 4 parallel agents): NEGATIVE
Every uniform parameter change **failed to move the core problem.** Across all 8
variants `top_third_force_frac` stayed exactly **0.00**, the contact band stayed
pinned at **y≈72–79 mm** (invariant), and `tip_inward_mm` stayed **negative** (tip
away). Trends: thinner walls → marginally less-negative tip and higher margin, but
only by collapsing grip force (8 N at WALL=1.5 — confounded, not real conformance);
MORE ribs → *worse* (stiffer lever, margin 2.19). The **invariance of the contact
band under every stiffness lever** is the diagnosis: a straight contact face only
tangent-touches the cylinder, and the finger rotates about the pins rather than the
rib lattice shearing into a conforming wrap. **Uniform parameters cannot fix this —
the change must be structural.** **Decision:** (1) discriminating experiment — does
*reversing the rib slant* flip the tip from away→toward? then (2) structural levers
in `gripper.py` (rib-slant sign, wall stiffness gradient base→tip). NOT a concave
face (that would kill adaptivity to other object shapes — the opposite of the goal).

### Discriminator — reversed rib slant (FR_RIB_SLANT_DEG=−38): NEGATIVE
Reversing the slant did NOT flip the tip toward the object (tip −12.5, slightly
worse; contact band still y 72–79, 26 nodes). So the slant *sign* is not the cause
— it is the **contact-area problem**: a straight contact face only tangent-touches
the cylinder, and the finger bends like a tapered cantilever (tip away from a mid
push) rather than the lattice conforming.

### Methodology change — closure-controlled reporting (important)
Metrics are now read at a **fixed closure (press = 8 mm**, the user's grasp
scenario from the image), not at a fixed grip force. Reason: grip-controlled
reporting at 5 N washed out all discrimination — at 5 N the finger has closed only
~2.5 mm and is barely touching, so every variant looked identical (7 contact nodes).
Closure is the actuator input (fair across variants); grip force is now a reported
result. Added `gripper.py` graded/directional wall params (`FR_CONTACT_WALL`,
`FR_SPINE_WALL`, `FR_RIB_WALL` + `_TIP`, None→uniform, byte-identical when unused)
and a `reeval_npz.py` to re-score saved solutions at any closure without re-solving.

### Round 2a — spine stiffness gradient (FR_SPINE_WALL_TIP=1.0): DEAD
Hypothesis: thin the spine toward the tip so the back yields and the contact face
wraps. Result at 8 mm closure: **contact_nodes 22→22 (no growth)**, top-third still
0.00, tip still −9 mm (away); only softened the finger (grip 24.5→21.5 N, margin
6.5→7.2). The spine-yields hypothesis does not grow the contact patch. **Decision:**
the away-bending (simple cantilever) mode dominates the Fin Ray curl. Next test the
opposite stiffness distribution — **stiff beams + thin ribs** — to suppress the
cantilever mode and free the rib-shear/curl mode.

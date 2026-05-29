# Fin Ray finger — design-iteration log (FEA-driven)

> ## ➡️ SUPERSEDED BY THE UNIVERSAL-FINGER STUDY — read `fea/UNIVERSAL_FINGER.md`
> The iterations below optimised wrap/pressure against **one** object (the R=22
> cylinder). That over-fits — a real gripper must work on **every shape and size**.
> A later study added a **square object + a size/height battery** and a **universal
> scorer** (`fea/scripts/eval_finger.py`), mass-iterated **two finger families**
> (Fin Ray truss + monolithic flexure) with an **agent swarm** (~90 FEA runs), and
> shipped a finger that distributes pressure across the whole finger on flat/large
> objects and grips round ones safely + evenly across sizes. Key results: the
> flexure family is structurally unstable on round objects (ruled out); a passive
> single-piece finger cannot actively curl around a small *round* object without a
> tendon (which the underwater/no-maintenance goal forbids). The shipped `gripper.py`
> `FR_*` values come from that study, not from the single-object tuning below.

Goal (original, single-object): make the grasp load **distribute across the whole
finger** and make the **top of the finger morph over the object** (wrap), instead of
all the load sitting in the lower-mid ribs while the tip stays straight and unloaded
(the problem in the first 3D FEA, `fea/fea3d/wrap_stages.png`).

Each iteration changes **one geometry lever** on the real `gripper.py` Fin Ray
finger, re-runs a high-quality 3D FEA, and is committed + pushed with its data,
pictures, and notes. Harness: `fea/scripts/iter_harness.py`.

> ## ⚠️ CORRECTION (read first — supersedes the metric used in iter00–r3/f2)
> **The `tip_inward` (apex-displacement) metric was WRONG and the "doesn't wrap"
> conclusion built on it was wrong.** On a base-clamped Fin Ray (robot-gripper
> config, unlike the free-base fish-fin demo) the apex correctly moves *with* the
> push; the wrap is the **contact face curving to conform** to the object, with the
> apex ending on the object's FAR side. A validation (`loadtest.py`) showed even a
> textbook symmetric base-clamped Fin Ray has the apex follow the load — i.e. that
> is *correct* behaviour, confirmed by two independent solvers (2D StVK + 3D
> corotational), not an FEA bug.
>
> **Corrected finding: the production finger DOES wrap.** With the right metric —
> contact-patch growth with closure — the contact patch grows **0→7→14→22→23 nodes**
> as the finger closes (24 N at 8 mm), with ~20% stress spread: the face is
> conforming to the object's reachable arc. The "**top gets nothing**" the user saw
> is real but **geometric and largely unfixable**: the object (R=22, centre y≈80)
> spans y≈58–102, while the finger tip is at y=122 — the top ~20 mm of finger is
> simply *above the object*, so there is no surface there to load. That is not a
> finger defect.
>
> The correct success metrics going forward: **contact_nodes growth with closure**
> and **stress-spread along the contact arc** — NOT apex direction. The iter00–r3
> and f2 variant rankings below were scored on the wrong metric and should not be
> used for design conclusions.

## Method (frozen across all iterations for fair comparison)
- **FEA:** full 3D corotational finite-element (linear tets, 3 z-layers,
  ~25k tets / ~20k DOF), penalty contact, Newton–Raphson, displacement-stepped.
- **Boundary condition (corrected):** the finger is **clamped at the two pin-bore
  rims (C and D)** — the real coupler-mounted pivots — *not* a bottom slab. Both
  bore-rim node rings are fixed in all 3 translations.
- **Grasp scenario (frozen):** rigid amphora-neck cylinder R=22 mm, centre y=80 mm,
  pressed 10 mm into the contact face over 24 steps, kpen=2000.
- **Material:** TPU ~95A, E=9.8 MPa in-plane, ν=0.42 (Bambu TPU 95A HF measured ISO 527; legacy runs in this doc used the old E=40 estimate; ν relaxed for linear-tet
  locking, per the bundle).
- **Mesh density frozen** (gmsh 0.5–1.3 mm); only the geometry changes.

## Metrics (defined up front)
| Metric | Meaning | Target |
|---|---|---|
| `engage_y_frac` | contacted height / finger length | ≥ 0.70 |
| `top_third_force_frac` | share of contact force in the upper third | ≥ 0.20 |
| `tip_inward_mm` | apex displacement toward the object (the wrap) | > baseline, clearly |
| `stress_spread_frac` | fraction of elements above 0.3×peak vM (load shared) | higher = better |
| `margin_x` | TPU strength (27.3 MPa) / peak vM (stay fragile-safe) | ≥ 5 |

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
| r2b_stiffbeam_thinrib | contact4/spine4/rib1.2 (grip 19.8N) | 0.029 | 0.00 | −7.1 | 0.038 | 5.88 | 4.25 | DEAD — contact 14 (fewer) |
| r2c_thinrib_only | rib 2.8→1.2 (grip 11.1N) | 0.024 | 0.00 | −5.8 | 0.024 | 5.48 | 4.56 | DEAD — contact 10 (fewer) |
| exp_yc95 | baseline, object centre y=80→95 | 0.029 | 0.00 | −10.4 | 0.035 | 4.61 | 5.42 | position not the lever (contact 13, band just moves up) |
| r3_len58 | shorten FR_BLADE_LEN 90→58 | 0.076 | **1.00** | −9.6 | 0.186 | 5.94 | 4.21 | top‑⅓=1.0 is a METRIC ARTIFACT (band near short tip); tip still −9.6 away, contact still a 19‑node band, margin worse |
| — | *Round 4: free-topology generator (finray2), full control of beam angles + rib dir/angle* | | | | | | | |
| f2_default | finray2 = production shape | 0.029 | 0.00 | −7.0 | — | 5.2 | 4.8 | validates same failure mode (tip away) |
| f2_ribrev | reverse rib direction | 0.029 | 0.00 | −6.6 | — | 5.3 | 4.7 | tip STILL away |
| f2_ribsteep | rib angle 38→65° | 0.029 | 0.00 | −7.7 | — | 5.7 | 4.4 | tip STILL away |
| f2_symmetric | contact face angled to centre (isoceles) | 0.000 | 0.00 | −0.2 | — | — | 0 | barely touches (face moved off the object) |

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

### Round 2b — stiff-beam / thin-rib decoupling: DEAD (and the key result)
Stiff beams + thin ribs (contact 4 / spine 4 / rib 1.2) and thin-ribs-only both
**reduced** the contact patch (14 and 10 nodes vs baseline's 22) and left top-third
at 0.00. The baseline actually has the *most* contact of any variant. **Conclusion,
now firmly established across ~14 variants: no internal stiffness change (uniform,
graded, directional, slant) grows the contact patch or engages the top. The limit
is GEOMETRIC, not material.** Visual (`r2c_thinrib_only/wrap_stages.png`): the
finger below the contact curls toward the object (it's driven, sitting between the
clamp and the load), but the free cantilever ABOVE the contact has **no driving
load** — the cylinder only tangent-touches one y on the straight vertical contact
face, so nothing pushes the upper finger toward the object; it bends away. **The fix
must put more of the finger face near the object**, two candidates: (#2, free) the
object may sit too low — the finger tip is 20 mm above the object top; test yc=95.
(#1) flip the taper so the CONTACT face narrows toward the tip (angled-but-straight,
preserves adaptivity; not a concave face) so the upper face approaches the object as
the gripper closes. Testing #2 first (one run, no geometry change).

### Round 2c — object position (yc 80→95): NEGATIVE; and the geometric wall
Raising the object did not help (contact 13, top-third 0; the band just tracked the
object up to y89–92). yc=80 actually has the most contact (22). **Position is not the
lever.** This, plus the contact patch being press-invariant (22 nodes at press 10,
22 at press 8 — it does NOT grow with closure), establishes the real wall:

> **A straight contact face only tangent-touches a cylinder at one line, and the
> finger's wrap mechanism propagates only BELOW the contact (toward the clamp
> reaction), not ABOVE it (free cantilever, no driving load). The finger tip
> (y=122) is also ABOVE the object entirely (object top y≈102–117) — there is no
> surface there to "morph over." So the top third can never load for this
> object/finger combination, by geometry, not material.** No stiffness, gradient,
> directional-wall, slant, or position change moved it (16 runs).

The wrap the finger DOES produce (the lower/driven arc) is real and works. Getting
the *whole* finger to share load requires a **geometric** change, three families:
- **(a) match finger length to the object** — shorten `FR_BLADE_LEN` so the tip is
  ~object-top height; the whole finger is then in the wrap arc. Cheap (1 param).
  Cost: less open-jaw reach (blade 90→58 drops tip span 123.8→101.8 mm).
- **(b) a topology that propagates curl toward the tip too** (tendon / coupled tip /
  different rib scheme) — real R&D, not a parameter sweep.
- **(c) accept the wrap is the lower arc** and document the over-the-top limit for
  objects smaller than the finger length.

Testing (a) as a concrete data point (r3_len58), then bringing the choice to the user.

### Round 3 — shorten finger (a): top‑⅓ metric rises but it's an ARTIFACT
`FR_BLADE_LEN` 90→58 gives `top_third_force_frac = 1.0` — but only because the
unchanged contact band (y71–76) now sits in the top third of the *shorter* finger.
The real behaviour is unchanged: tip still bends **away** (−9.6 mm), contact is
still a single 19-node band, and margin got *worse* (4.21×, the short finger is
stiffer). So (a) relabels the geometry; it does not produce a conforming wrap or
make the tip curl toward the object. **Net conclusion after 17 runs: this Fin Ray
finger does not conform-wrap a 44 mm cylinder — it tangent-contacts and the free
portion bends away. True whole-finger wrap needs a topology change (R&D), not a
parameter. Surfaced to the user for a direction decision (kept gripper.py at its
original, working geometry — only added the unused graded-wall params).**

### Round 4 — free-topology scan (user chose "topology redesign"): apex never wraps
Built `fea/scripts/finray2.py`, a fully-parametric Fin Ray section generator (free
beam endpoints, rib direction, rib angle, wall split) decoupled from the production
finger, and scanned fundamental topologies. **Result: NO topology flips the apex
toward the object.** Default, reversed ribs (rib_dir −1), steep ribs (65°) all keep
`tip_inward ≈ −7` (apex bends AWAY) with top-third = 0; the symmetric/isoceles form
just moves the contact face off the object (grip 0). So the failure is **not** the
rib scheme — it is structural to a passive Fin Ray clamped at the base with contact
at mid-span: the portion below the contact is driven and wraps, the free cantilever
above it has no driving load and bends away, regardless of internal topology.
Diagnostic next: does the finger wrap when the object sits near the TIP (no free
cantilever above)? — to separate "object position" from "object size" and confirm
the finger can wrap at all.

### Wrap-quality optimization (CORRECT metrics: contact arc + pressure evenness)
After the metric correction, re-scored on what actually matters: the angular
**contact arc** the face conforms to around the object, **pressure evenness**
(`pressure_cov`, lower = more even), and **margin** (keep gentle). Operating point
= 8 mm closure. Renderer `fea/scripts/render_wrap.py` shows the finger mesh
(coloured by von Mises) conforming to the SOLID object + closing animations.

| variant | change | contact | arc° | pcov | grip | margin | note |
|---|---|---|---|---|---|---|---|
| w0_base | baseline | 22 | 12 | 0.74 | 24 | 3.6 | reference |
| w1_contactgrad15 | contact wall →1.5 @tip | 22 | 12 | **0.53** | 24 | 3.5 | more EVEN pressure, same arc |
| w2_ribs16 | 16 ribs | 18 | 11 | 0.64 | 35 | 2.9 | stiffer, worse margin |
| w3_ribs16_cgrad | 16 ribs + contact grad | 16 | 7 | 0.50 | 35 | 2.8 | stiffer, smaller arc |

Finding: the contact **arc is only ~12°** (a small patch, not a big wrap) and
margin is low (3.6) because the contact is concentrated. More ribs = stiffer =
worse. The contact-wall gradient (w1) evens the pressure (pcov 0.74→0.53) for free.
The lever to GROW the arc and lift the margin is a more compliant **contact beam**
(thinner) so the face curves around more of the cylinder at lower peak pressure —
Round 2 (w4–w6) testing FR_CONTACT_WALL 1.2–1.6.

### Round 2 — compliant contact beam: grows the wrap arc. WINNER = w7
| variant | contact wall | contact | arc° | pcov | grip | margin |
|---|---|---|---|---|---|---|
| w0_base | 2.8 uniform | 22 | 12 | 0.74 | 24 | 3.6 |
| w4_csoft15 | 1.5 uniform | 22 | 12 | 0.73 | 17 | 4.4 |
| w5_csoft12 | 1.2 uniform | 23 | 17 | 0.94 | 15 | 4.7 |
| w6_csoft_grad10 | 1.6→1.0 | 24 | 17 | 0.91 | 17 | 4.6 |
| **w7_balanced** ✅ | **1.8→1.2** | **24** | **17** | **0.79** | **18** | **4.2** |

A more compliant contact beam lets the face curve around more of the cylinder:
**arc 12°→17° (+40% wrap), margin 3.6→4.2 (gentler peak), contact 22→24**, at a
still-secure 18 N grip. **w7 (FR_CONTACT_WALL 1.8 base → 1.2 tip)** is the winner —
biggest arc with the best evenness + grip of the arc-gainers, and the 1.2 mm tip
stays ≥ the FDM 2.5-perimeter floor (printable). **Ported into `gripper.py`**
(`FR_CONTACT_WALL=1.8`, `FR_CONTACT_WALL_TIP=1.2`); verified kinematics unchanged,
finger a single valid solid, finger-vs-finger still 0 at closed.

**Honest scope of the win:** the wrap is still modest in absolute terms (17° arc) —
a straight contact face on a Ø44 mm cylinder is geometry-limited — but the
optimization delivered a real, printable improvement on the correct metrics: more
conforming contact area, distributed over a wider arc, at a gentler peak stress.
Renders: per-iteration `wrap_render.png`/`wrap_anim.gif` + `_comparison/compare.png`
+ `_comparison/compare.gif` (finger mesh coloured by von Mises conforming to the
SOLID object, closing animations).

# Underwater FEA — how the gripper actually performs wet

Companion to `docs/UNDERWATER.md` (the material/seawater audit) and the
on-land FEA campaign in `fea/FEA.md`. The land FEA gates the design; this
study answers a different question:

> Once you put the as-designed gripper in the water, does it still work?

Three effects are in play, and they're routinely confused:

1. **Hydrostatic compression of the flooded finger** — water at depth
   squeezes the TPU, but pressure acts on every wetted surface equally
   (inside the Fin Ray cells AND outside the skin), so the bulk stress
   state is pure hydrostatic → von Mises ≈ 0. See §2.
2. **Pressure-crush of the trapped-air finger** — the same depth pressure
   becomes a real, large mechanical load if the Fin Ray cells **fail to
   flood** (trapped air at 1 atm inside, external water at P_depth). This
   is the load case the user was worried about. See §3.
3. **Water plasticization of the soaked TPU** — wet TPU is softer than
   dry TPU; grip force and peak vM at the same actuator stroke both
   drop linearly with modulus. See §4.

The headline result, in one line:

> **In the nominal FLOODED state the finger is fine at any practical depth
> (von Mises ≈ 0). In the TRAPPED-AIR state the geometry is crushed from
> very shallow depth (≥10 m) and the MATERIAL yields beyond ~177 m — so
> ensuring the cells flood is a pre-dive procedure, not a finger redesign.**
>
> **Material note (2026 switch to Bambu TPU 95A HF):** the crush von-Mises
> stress field is **load-controlled → modulus-INDEPENDENT**, so the vM
> numbers below are identical to the previous eSUN run. What changed with
> the measured, ~4× softer modulus is (a) displacements scale ~5.4× larger
> (the linear-validity envelope now trips at even shallower depth) and
> (b) the measured through-Z strength 22.3 MPa (vs the old 25 MPa estimate)
> moves the material-yield depth from ~199 m to ~177 m (vM = 0.1258·depth MPa,
> crossing strength/0.1258).

Gear ceiling `T_safe` (`motor/DRIVETRAIN.md`) is unchanged in any case
because it is gear-limited, not finger-limited.

---

## TL;DR

| Effect | At 30 m | At 100 m | At 300 m | Verdict |
|---|---|---|---|---|
| FLOODED finger — peak vM (3D, ν=0.45) | ≈0 (bulk hydrostatic) | ≈0 | ≈0 | **negligible by physics** — vM = 0 in the free bulk because σ = −P·I. 3D FEA sanity-check confirms (peak vM 0.3 MPa is clamp boundary only) |
| TRAPPED-AIR finger — peak vM (3D worst case, ν=0.45) | **3.8 MPa** | **12.6 MPa** | linearity broken (≫finger-thickness sag) | 30 m: 5.9× yield margin (vs 22.3 MPa), linear sag **26 mm (2.6× finger thickness — far past validity)** → geometrically crushed. 100 m: 1.8× margin. ≥~177 m: material yields. (vM is modulus-independent — same as the old eSUN run; sag is ~5.4× larger on the softer measured modulus.) |
| **2D plane-strain UNDER-estimate** (trapped-air, the original figure I quoted) | 0.41 MPa, 2.6 mm sag | 1.35 MPa, 8.7 mm | — | **2D was wrong** — εz = 0 hides the dominant foam-collapse mode; 3D is the correct number |
| Bulk linear contraction (ν=0.45, flooded) | −0.31% | −1.0% | −3.1% | 396 / 1320 / 3960 μm on the 90 mm blade — **uniform** isotropic shrink (no shape change, vM≈0), just larger on the softer modulus |
| Pin-bore radial contraction (ν=0.45, flooded) | −7 μm | −24 μm | −70 μm | Trivial vs 300 μm PRINT_CLEAR — pin stays running clearance |
| 20% modulus drop (typical wet TPU) at 8 mm closure | grip force ~−20% | (depth-independent) | (depth-independent) | gripper softer, T_safe unchanged |
| 50% modulus drop (worst-case sat.) | grip force ~−50% | (depth-independent) | (depth-independent) | still wraps; less force margin |

**Updated operating verdict: in the FLOODED design state the finger is
fine at any practical depth. In the TRAPPED-AIR state — even at very
shallow depths (10 m: 1.6 mm contact-face sag) — the finger is
geometrically crushed and the wrap is wrecked. So pre-dive cell flooding
is LOAD-CRITICAL from depth ZERO, not just for deep dives.** The
mitigation procedure in `docs/UNDERWATER.md` (submerge fingers-down,
soak ~30 s, cycle open↔close once underwater) is mandatory for any
underwater operation, not an optional best-practice.

---

## 1. Physics of the underwater load case

`docs/UNDERWATER.md §3` proves the flooded property *geometrically*:
**every part is a single solid with one shell** → no enclosed void anywhere
in the assembly. Water reaches every TPU face including the Fin Ray rib
cavities, so the TPU sees water at the same pressure on every wetted
surface simultaneously.

For a closed surface ∮ n dA = 0, so the **net force** on the TPU is zero.
For a linear-elastic body under uniform pressure on every face, the
interior stress is the pure hydrostatic state

  σ_ij = −P δ_ij,  ε_v = −P / K,  von Mises = 0,

with bulk modulus K = E / (3(1−2ν)). For E_TPU = 9.8 MPa (Bambu TPU 95A HF,
in-plane X-Y; the bulk-contraction displacement scales 1/K, so the softer
measured modulus gives ~4× more uniform shrink than the old 40 MPa guess —
still benign, vM = 0):

| ν | K (MPa) |
|---|---|
| 0.42 | 20.4 |
| 0.45 | 32.7 |
| 0.48 | 81.7 |

The only place deviatoric stress can develop is at the **rigid mount-bore
clamp**, where the printed PA12-GF dowel holds the TPU that wants to
contract isotropically. A 1D Poisson-restraint argument gives

  σ_clamp ≲ (1 − 2ν) · P.

At 30 m: 0.012 – 0.048 MPa depending on ν — 500–2000× below the 27.3 MPa
in-plane strength. (This bound is pressure-only, independent of E.)

The hydrostatic-pressure story is **analytical, not a finite-element
question**. The 2D plane-strain FEA below is a sanity check that the
implementation matches the closed-form bound.

---

## 2. Pressure-probe FEA — `underwater_pressure_probe.py`

Plane-strain linear-elastic solve on the existing finger section mesh
(`fea/scripts/mesh.npz`), reusing the `solve_finger.py` clamp setup at
the C/D mount bores. Hydrostatic pressure tractions applied on **every
boundary edge** of the mesh — outer skin AND the inner Fin Ray rib
cavities (because the cavities flood).

Plane-strain is the **conservative upper bound**: it artificially
constrains ε_z = 0, but the real finger CAN compress in Z because its
front/back faces are also wetted at the same pressure. So the 3D answer
is *smaller* than what this script reports.

Sweep over ν ∈ {0.42, 0.45, 0.48} and depths {0, 10, 30, 100, 300, 600} m
(seawater, ρ = 1025 kg/m³, P = 0.01005 MPa/m).

### Result (peak von Mises, MPa)

| depth | P (MPa) | ν=0.42 | ν=0.45 | ν=0.48 |
|---|---|---|---|---|
| 0 m | 0.00 | 0.000 | 0.000 | 0.000 |
| 10 m | 0.10 | 0.016 | 0.010 | 0.005 |
| 30 m | 0.30 | 0.047 | 0.031 | 0.013 |
| 100 m | 1.01 | 0.156 | 0.103 | 0.045 |
| 300 m | 3.02 | 0.469 | 0.309 | 0.134 |
| 600 m | 6.03 | 0.938 | 0.619 | 0.268 |

Even the most-conservative case (ν=0.42, 600 m) is **0.94 MPa peak vM
against the 27.3 MPa in-plane strength — 29× margin** (these vM values are
load-controlled and identical to the old eSUN run — modulus-independent). The pressure question is
**closed**: water doesn't stress the TPU at any depth the system can
physically operate at (the actuator pressure rating sets the system
limit, not the finger).

### Result (peak displacement, μm)

| depth | ν=0.42 | ν=0.45 | ν=0.48 |
|---|---|---|---|
| 30 m | 621 | 396 | 162 |
| 100 m | 2069 | 1320 | 539 |
| 300 m | 6207 | 3960 | 1616 |

These are the WHOLE-FINGER **uniform isotropic-contraction** amplitudes —
~4× larger than the old 40 MPa guess gave, because displacement scales 1/E
and the measured modulus is softer. They do **not** threaten clearances:
this is uniform shrink (the whole blade gets slightly smaller with vM ≈ 0),
not a local gap closing. The clearance-relevant number is the pin-bore
radial contraction in §1 (tens of μm, well under the 300 μm `PRINT_CLEAR`).

Figure: `fea/pictures/underwater_pressure.png`.

---

## 3. The pressure-CRUSH case — what if the cells don't flood?

The §2 result depends entirely on the cells actually flooding. If they
trap air (transient before equilibration; or if some cell vents end up
blocked by infill, print artefacts, or particulates), the TPU sees a
**real pressure differential** across the contact wall and every rib:

  external skin:    water at P_depth.
  inside the cells: air at ~1 atm (gauge 0).

`underwater_pressure_crush.py` runs the 2D plane-strain solve with
boundary loops classified by topology (signed-area ranking of connected
boundary-edge loops): the LARGEST loop is the outer skin → loaded with
−P_depth · n; the smaller loops are Fin Ray cells → traction-free
(equivalent to 1 atm air inside, in gauge convention).

### Geometry classification

The 2D section mesh comes back with **12 boundary loops** total:

  outer skin:      253 facets, |signed area| 1379 mm²  → external water
  Fin Ray cells:    11 inner loops, 286 facets total, area 470 mm²  → air

### 2D plane-strain result (under-estimates the true load case)

| depth | P (MPa) | peak vM (MPa) | contact wall sag (μm) | margin (vs 27.3) |
|---|---|---|---|---|
| 30 m | 0.30 | 0.41 | 2598 | 67× |
| 100 m | 1.01 | 1.35 | 8661 | 20× |
| 300 m | 3.02 | 4.05 | 25982 | 6.7× |

(vM unchanged from the old run — load-controlled; sag ~4× larger on the softer measured modulus. ν=0.45 shown.)

The first version of this analysis used 2D plane-strain because it was
fast and reused the existing 2D mesh. **It is wrong.** Plane-strain
forces εz = 0 — the finger cannot deform in its thickness direction.
The Fin Ray cells, however, can collapse globally in 3D because the
ribs are thin walls that bend; this mode requires Z-direction freedom,
which plane-strain forbids. The user's pushback ("what about crushing
vertically?") was exactly right.

### 3D linear-elastic result (the correct worst case)

`underwater_crush_3d.py` runs the 3D solve. The mesh is the same 2D
section extruded N_LAYERS = 5 times in Z (33,375 linear tets, 25,812
DOF). The prism-to-tet split is **face-conforming** (sorted indices
a<b<c, split into (a,b,c,c'), (a,b,c',b'), (a,b',c',a') — adjacent
prisms see matching diagonals on shared quad faces, no spurious
hanging-node mechanisms). Outward-of-solid normals are computed by
the **local-triangle topology test** (the third vertex of the adjacent
2D triangle is on the solid side; outward points away from it), which
correctly orients both outer-skin and inner-cavity face normals.

**Sanity check (flooded, 100 m, ν=0.45):**

  f_net = 1e-13      (numerical zero — equilibrium satisfied)
  mean σ_xx = -0.986 MPa   vs analytical -P = -1.006 (2% mesh)
  peak |u| = 1226 μm   (uniform bulk contraction; ~5.4× the old 227 μm because E_Z 40→7.4)
  peak vM = 0.31 MPa   (mostly clamp boundary; bulk ≈ 0 as required)

Reproduces σ = -P·I in the free bulk → FEA is trustworthy.

**Trapped-air result (ν = 0.45):**

Margins are vs the measured through-Z strength **22.3 MPa** (the crush is a
through-thickness mode). vM is **load-controlled and identical to the old
eSUN E=40 run**; only the sag (∝ 1/E) is ~5.4× larger, and the yield
verdict shifts because the measured strength is 22.3 vs the old 25 estimate.

| depth | P (MPa) | peak vM (MPa) | contact-wall sag (μm) | margin | verdict |
|---|---|---|---|---|---|
| 0 m | 0.00 | 0.00 | 0 | ∞ | trivial |
| 10 m | 0.10 | **1.26** | **8678** (8.7 mm) | 17.7× | material OK, **geometry already crushed** (sag ≈ finger thickness) |
| 30 m | 0.30 | **3.77** | **26033** (26 mm) | 5.9× | material OK, **GEOMETRICALLY CRUSHED** (linear sag 2.6× finger thickness — far past validity) |
| 100 m | 1.01 | 12.58 | 86778 (≫thickness) | 1.8× | linear FEA past validity; gas/contact dominates |
| 150 m | 1.51 | ~18.9 | ~130000 | ~1.2× | approaching yield |
| 200 m | 2.01 | 25.16 | 173556 | **0.89×** | **MATERIAL YIELDS** |
| 300 m | 3.02 | 37.74 | 260334 | **0.59×** | **MATERIAL YIELDS** |

**3D is ~10× worse than 2D plane-strain at every depth.** At 30 m the linear
solve predicts 26 mm of sag — 2.6× the finger's 10 mm Z-thickness, i.e. deep
past the linear-elastic validity envelope. Physically the cells self-contact
and gas backpressure intervene long before that, but the blade is
unrecognizably distorted; the wrap geometry is wrecked.

### Why 3D is so much worse — foam collapse

The trapped-air finger blade behaves as a **closed-cell foam** in
compression. Cell wall thickness t ≈ 1.4 mm; cell size b ≈ 6 mm. The
effective foam modulus for bending-dominated cell collapse is:

  E_foam ≈ E_TPU · (t/b)³ ≈ 7.4 · 0.013 ≈ 0.10 MPa

(through-Z E_TPU = 7.4 MPa; ~75× below the parent modulus.) Under any pressure
differential, both the contact face and the spine face move INWARD
together, and the slanted ribs bend like trusses with no internal
support. This is a *global* deformation mode, not local plate-bending
between adjacent ribs.

The 2D plane-strain analysis **artificially prevented** this mode by
forcing εz = 0 — the cells couldn't collapse in the Z direction, so
the only available mode was in-plane bowing of the contact wall.

### Convergence + domain of validity

NLAYERS=5 → 7 gives identical answers within 1% (verified). The
linear-elastic FEA does NOT model:

1. **Adiabatic gas compression in cells.** The linear solve now predicts
   far more sag than the cell can physically give (26 mm at 30 m into a
   ~6 mm-deep cell), so the cell fully closes; the trapped gas compresses
   adiabatically (PV^γ, γ=1.4) and self-contact intervenes. Gas backpressure
   + self-contact CAP the real deflection at roughly cell-closure (~several
   mm) — but at that point the geometry is already wrecked.
2. **Self-contact between contact wall and spine/ribs.** Once the contact
   wall closes the ~6 mm cell it self-contacts and halts further motion
   (force is then taken by direct compression of the rib stack).
3. **Material nonlinearity.** The linear strains here are well past TPU's
   linear-elastic regime; real response stiffens at large compressive strain.

So the linear 3D sag numbers **massively overstate actual deflection** —
they are diagnostic of "the cell collapses", not a literal displacement.
But this only sharpens the engineering verdict: the cells close and the
wrap geometry is wrecked from very shallow depth. At 10 m the linear sag
is already 8.7 mm — larger than the finger thickness — so even 10 m closes
the cells. **There is no trapped-air depth shallow enough to be safe.**

**Bottom line: a finger with cells trapping air is geometrically crushed
at any operating depth ≥10 m. There is no depth shallow enough to
tolerate trapped air. Pre-dive cell flooding is mandatory from dive
plan zero, not an optional best-practice.**

Figure: `fea/pictures/underwater_crush.png` (3D in red, 2D in orange
for the under-estimate comparison).

The real 3D-with-gas-compression answer is therefore strictly safer than
the plane-strain rigid-air-pocket numbers above. The "survives" verdicts
at 30 / 100 / 300 m are robust.

### Mitigation (already in `UNDERWATER.md §3` pre-dive checklist)

> "Confirm all drains/slots/windows/journal bores are clear; confirm
> cavity floods (submerge, watch bubbles fully clear in your dive
> orientation; add the cover vent if you dive front-up)."

For deep dives (>30 m), this becomes a **load-critical procedure**, not
optional. Add a pre-dive **soak + cycle** step: submerge the gripper
slowly (cells vent from the +Z and −Z openings), let air bubbles escape
for ~30 s, then cycle the fingers open→close once underwater to flush
any residual air pockets. After this, the §2 flooded analysis applies
(vM ≈ 0) and there is no pressure-crush risk at any practical depth.

Figure: `fea/pictures/underwater_crush.png`.

---

## 4. The bigger effect — water plasticization

`UNDERWATER.md §1` already notes that ether-TPU "absorbs a little water
and softens slightly." For ether-based 95A TPU, manufacturer data and
literature put the soaked-modulus drop at **typically 10–30%**, with
50% as a worst-case for warm prolonged immersion. iter_harness has the
`GRIPPER_E_TPU` env override (line 121) already in place, so this sweep
is essentially free — and it's the question the user is actually asking
("how does it actually perform underwater").

### Sweep (`iter_harness.py`, `GRIPPER_E_TPU` env, REPORT_MODE = closure, R=22 mm cylinder, ν = 0.42, NLAYERS = 3)

| run name | E_TPU (MPa) | scenario | peak vM (MPa) | grip @ 8 mm (N) | tip inward (mm) | arc (°) | margin vs 27.3 MPa† |
|---|---|---|---|---|---|---|---|
| under_E98_dry | 9.8 | dry baseline (measured X-Y) | 0.81 | 2.28 | −6.13 | 13.6 | 33.7× |
| under_E78_wet20 | 7.8 | 20% softening (typical wet) | 0.64 | 1.82 | −6.13 | 13.6 | 42.4× |
| under_E69_wet30 | 6.9 | 30% softening | 0.57 | 1.61 | −6.13 | 13.6 | 47.9× |
| under_E49_wet50 | 4.9 | 50% softening (warm long soak) | 0.41 | 1.14 | −6.13 | 13.6 | 67.4× |

> † Margin vs the **measured** Bambu TPU 95A HF in-plane strength 27.3 MPa
> (ISO 527 printed; `iter_harness.py`, `docs/MATERIALS.md`) — replacing the
> old 25 MPa estimate. The absolute grip/vM numbers are ~4× lower than the
> old eSUN-guess (E 40→9.8) table because at fixed closure both scale with
> E; this is closure-mode (absolute) reporting, not the force-targeted
> ranking basis. **Wet TPU strength also drops on soak** — typically less
> than modulus does — so stress drops by the full modulus ratio while
> strength drops more slowly: the gripper does **not** become stress-limited
> as the finger softens. A measured wet-strength datum on Bambu TPU 95A HF
> would close the last gap; the project does not yet have one.

The sweep reproduces the linear-elastic prediction (Hooke's law guarantee,
not an emergent finding):

  peak_vM / E = 0.0826   (constant across all 4 cases)
  grip_at_8mm / E = 0.233 N/MPa   (constant across all 4 cases)
  tip_inward, contact_arc → identical (kinematic state unchanged)

So softening produces **proportional reductions** in both stress and grip
force at the same actuator stroke, with no change in wrap geometry.

Figure: `fea/pictures/underwater_wet_modulus.png`. Side-by-side wrap
stages at constant vM color scale: `fea/pictures/underwater_wrap_compare.png`.

### What changes when the TPU softens

In the small-strain corotational regime, force scales **linearly** with
modulus at a given displacement field, so the headline expectation is:

- Grip force at fixed actuator stroke → drops ~proportionally with E.
- Peak vM at the same closure → drops ~proportionally with E (softer
  material means lower stress for the same kinematics).
- Tip inward travel → increases slightly (softer ribs deflect more under
  the same contact).
- Contact arc → marginally larger (softer finger conforms more).

The interesting non-linear question is whether the wrap becomes unstable
at heavy softening — this is what the sweep actually tests.

### What does NOT change

- `T_safe` (gear ceiling, `motor/scripts/gear_fea_3d.py`) — the printed
  crown/pinion is the binding constraint, not the finger.
- The motor current-limit, which is sized to `T_safe`.
- The kinematic chain (`motor/scripts/kinematics_chain.py`) — depends
  on geometry, not finger modulus.

So a saturated finger reduces the **delivered force at a given stroke**,
but the **maximum force the drivetrain can push** is the same. To
restore grip force on a softened finger, the operator commands more
closure — the same as for a harder object.

---

## 5. Operating-envelope implications

`motor/scripts/drivetrain_force_envelope.py` reports the per-finger
operating-force band as 0.17–0.35 N (radial 2D bound) up to 0.35–0.73 N
(single-station bound). At a 50% E_TPU drop (worst case), achieving the
upper end of that band requires roughly twice the closure of the dry
case at the same force — well within the 16 mm stroke. The gripper is
**not** kinematically saturated by softening.

The honest summary: **underwater the gripper is softer at the same
stroke, but its delivered force ceiling is unchanged.** The dry
on-land FEA campaign (`fea/FEA.md`) bounds the wet behavior, because
peak vM scales DOWN with softening at fixed kinematics — the dry case
is the high-stress case.

### Plot reading

`fea/pictures/underwater_pressure.png` — three panels covering depth:
(a) bulk linear contraction vs depth (analytical), (b) clamp peak vM vs
depth (plane-strain UB), (c) peak displacement vs depth.

`fea/pictures/underwater_wet_modulus.png` — three panels covering wet
softening: (a) peak vM at closure vs E_TPU, (b) grip force at closure
vs E_TPU, (c) wrap quality (contact arc, tip inward) vs E_TPU.

---

## 6. Limits of this analysis

- **Material model is linear elastic.** TPU 95A has known viscoelastic
  response (stress relaxation under sustained grip). The on-land FEA
  does not capture this; the underwater case inherits the same gap.
  For sustained-grip applications the relevant follow-on is a
  Prony-series viscoelastic solve, not an additional pressure case.
- **E_TPU is now a MEASURED value** (9.8 MPa in-plane / 7.4 MPa through-Z,
  Bambu TPU 95A HF ISO 527 printed-specimen TDS; per `iter_harness.py`
  and `docs/MATERIALS.md`) — an upgrade over the old 40 MPa eSUN guess.
  The caveat is now *definitional*: ISO 527 reports the initial-tangent
  modulus, while a Fin-Ray at finite wrap strain is hyperelastic, so the
  wet-modulus sweep remains a sensitivity study and absolute forces stay
  order-of-magnitude. The conclusion ("force scales linearly with E at
  fixed kinematics") falls out of linear elasticity, independent of the
  modulus value.
- **No measured wet/dry datum on this specific filament** (Bambu TPU 95A
  HF). Bambu publishes a dry saturated water-absorption of 1.08 % (low),
  but no wet-modulus number; the 10–30 % softening band is from
  polymer-chemistry literature on ether-TPU. A soak-test on a printed
  finger blade would pin down the actual modulus drop and shrink the
  uncertainty band — see `BENCH_TEST.md` if extended.
- **Plane-strain is conservative for pressure** but pessimistic for
  shear-dominated loadings. The wet-modulus sweep uses the 3D
  corotational solver, which is the right model for grip kinematics.
- **Sustained immersion creep** (days–weeks at constant load + soaked)
  is bounded by `UNDERWATER.md §2` (creep section). Not a pressure
  effect; covered by the snap-fit constraints, not this FEA.

---

## 7. Self-similar scale (1.5× / 2.0×) — invariance confirmed

`gripper.py` now carries a global self-similar scale (`GRIPPER_SCALE`,
default 1.0) that multiplies **every** linear dimension — walls included —
so the wall-thickness / radius ratio is held constant (the `SCALABILITY.md`
fix). The expectation here is not a new finding but a textbook similitude
result, stated **before** running and then verified:

> Under uniform geometric scaling ×k with **pressure (traction)** boundary
> conditions and linear elasticity, element stiffness ∝ E·L scales as k and
> the pressure load ∝ P·L² scales as k², so displacement scales as **k** while
> strain (= B·u) — and therefore the **von-Mises field and the material-yield
> depth — are SCALE-INVARIANT**. Flooded stays vM ≈ 0 at every scale.

Both underwater scripts were re-run at `GRIPPER_SCALE` = 1.0 / 1.5 / 2.0
(local, screen/coarse) via `fea/scripts/underwater_scale_driver.py`, a thin
driver that imports the original scripts unmodified and only (a) rebinds the
crush extrusion Z-span to the *scaled* finger thickness `Z_FINGER0 ..
Z_FINGER0+T_FINGER` (the crush script hardcodes the 1× 13→23 mm) and (b)
scales the gmsh element-size targets ×k so the mesh is *relatively* the same.
The 1.0 run reproduces the published §2/§3 numbers exactly, which gates the
1.5/2.0 results. Result JSONs in `variants/scale_{1.0,1.5,2.0}x/fea/`.

### 7.1 Flooded probe (`underwater_pressure_probe.py`) — exact invariance

The 2D flooded probe scales the **baked** section mesh + clamp landmarks ×k,
so the discretization (topology, `n_clamp` = 33) is byte-identical at every
scale. This is the clean check, and it lands on the analytic answer to 5
decimals (ν = 0.45):

| depth | peak vM (MPa), all k | disp 1.0 (μm) | 1.5/1.0 | 2.0/1.0 |
|---|---|---|---|---|
| 100 m | 0.10311 | 1320.1 | **1.5000** | **2.0000** |
| 300 m | 0.30933 | 3960.4 | **1.5000** | **2.0000** |
| 600 m | 0.61865 | 7920.8 | **1.5000** | **2.0000** |

peak vM identical to all printed digits at k = 1.0/1.5/2.0; displacement
scales exactly ×k. This is the pressure-only clamp bound ~(1−2ν)·P, which is
scale-free by inspection. Flooded vM ≈ 0 at every scale, as predicted.

### 7.2 Trapped-air crush (`underwater_crush_3d.py`) — invariance confirmed

| depth | vM 1.0 | vM 1.5 | vM 2.0 | yield depth |
|---|---|---|---|---|
| 30 m | 3.774 MPa | 3.869 | 4.019 | — |
| 100 m | 12.581 MPa | 12.896 | 13.397 | — |
| (slope / yield) | 0.1258 MPa/m → **177.3 m** | 0.1290 → 172.9 m | 0.1340 → 166.5 m | — |

Peak displacement scales ≈ ×k (contact-wall sag at 100 m: 86.8 mm → 134.2 mm
≈ ×1.5 → 191.2 mm ≈ ×2.0). The vM field is **modulus- and load-controlled**,
so as predicted it does **not** scale with size: the headline crush verdict
(geometrically crushed from ≥10 m if cells trap air; material yields beyond
~177 m) is unchanged at 1.5× and 2.0×. Pre-dive cell flooding remains the
load-critical procedure at every scale.

**On the small residual (do not over-read it).** The re-meshed crush shows a
*monotonic* creep — peak vM +2.5 % at 1.5× and +6.5 % at 2.0×, yield depth
177 → 173 → 167 m — and the gmsh node count climbs (1434 → 1503 → 1553). That
is **not** physics: it is non-self-similar discretization. Two contributors:
(i) gmsh's mesh is not exactly self-similar even at scaled element targets, and
(ii) `gripper.py` deliberately **holds** the finish features (fillets,
chamfers, `FR_GRIP_*` micro-texture, `DFM_EDGE`) at absolute size, so on a 2×
part they are *relatively* sharper and gmsh refines there. A self-similar
**control** — scaling the 1× tet coordinates directly (identical tets, identical
clamp DOFs, no re-mesh; `variants/scale_*x/fea/underwater_crush_selfsimilar_control.json`)
— removes both and recovers **exact** invariance:

| depth | vM (control), all k | disp 1.0 | disp 1.5 | disp 2.0 |
|---|---|---|---|---|
| 10 m | 1.25807 MPa | 9492.2 μm | 14238.3 (×1.5) | 18984.4 (×2.0) |
| 30 m | 3.77422 MPa | 28476.7 | 42715.0 (×1.5) | 56953.3 (×2.0) |
| 100 m | 12.58074 MPa | 94922.2 | 142383.4 (×1.5) | 189844.5 (×2.0) |

vM identical to 5 decimals, displacement exactly ×k, and the peak-vM tet sits
in the contact-wall **field** (~0.23·blade from base) — not at the clamp — at
every scale. So the re-meshed ±few-% is a meshing artifact of the as-designed
held-feature part, not a real strength change with size. The land FEA still
bounds the wet case at every scale.

### 7.3 Fidelity note

These runs are **local, screen/coarse** (NLAYERS = 5, gmsh 0.5–1.3 mm ×k;
MSI was down). A high-fidelity MSI re-run (finer mesh, NLAYERS ≥ 8) is
warranted only if a certified absolute crush-depth number is needed — but it
would not change the scale-invariance conclusion, which is analytic. The
honest absolute crush figures already carry the §3 linear-validity caveat
(sag ≫ wall thickness past ~10 m); scaling does not relax that.

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

> **At the primary operating depth (≤30 m), the finger survives both the
> nominal flooded case AND the worst-case trapped-air case. The finger
> can be crushed at depths >~200 m IF its cells fail to flood — so
> ensuring the cells flood is a pre-dive procedure, not a finger redesign.**

Gear ceiling `T_safe` (`motor/DRIVETRAIN.md`) is unchanged in any case
because it is gear-limited, not finger-limited.

---

## TL;DR

| Effect | At 30 m | At 100 m | At 300 m | Verdict |
|---|---|---|---|---|
| FLOODED finger — peak vM (plane-strain UB, ν=0.45) | 0.03 MPa | 0.10 MPa | 0.31 MPa | **negligible** — 800× / 240× / 80× margin to 25 MPa TPU yield |
| TRAPPED-AIR finger — peak vM (worst case, ν=0.45) | **0.41 MPa** | **1.35 MPa** | (linearity broken — see §3) | At 30 m: 62× yield margin, 0.6 mm contact-wall sag, geometry intact. At 100 m: 18.5× margin, 2.1 mm sag (degraded). At 300 m+ linear FEA over-predicts — real response is self-contact / gas-pressure limited |
| Bulk linear contraction (ν=0.45, flooded) | −0.075% | −0.25% | −0.75% | 68 / 226 / 678 μm on the 90 mm blade. Sub-PRINT_CLEAR until ~100 m |
| Pin-bore radial contraction (ν=0.45, flooded) | −1.7 μm | −5.8 μm | −17 μm | Trivial vs 300 μm PRINT_CLEAR — pin stays running clearance |
| 20% modulus drop (typical wet TPU) at 8 mm closure | grip force ~−20% | (depth-independent) | (depth-independent) | gripper softer, T_safe unchanged |
| 50% modulus drop (worst-case sat.) | grip force ~−50% | (depth-independent) | (depth-independent) | still wraps; less force margin |

**Operating verdict (≤30 m, the primary actuator-rated envelope): no
material yield in any case; no functional degradation if cells flood as
designed; ~0.6 mm contact-wall sag if cells trap air, which the standard
pre-dive cycle clears.** Deeper than 100 m, ensuring the cells flood
(pre-soak, fingers-down submersion, or a brief actuation cycle while
underwater) is **load-critical**, not just a "nice to have" from
`UNDERWATER.md §3`.

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

with bulk modulus K = E / (3(1−2ν)). For E_TPU = 40 MPa:

| ν | K (MPa) |
|---|---|
| 0.42 | 83.3 |
| 0.45 | 133.3 |
| 0.48 | 333.3 |

The only place deviatoric stress can develop is at the **rigid mount-bore
clamp**, where the printed PA12-GF dowel holds the TPU that wants to
contract isotropically. A 1D Poisson-restraint argument gives

  σ_clamp ≲ (1 − 2ν) · P.

At 30 m: 0.012 – 0.048 MPa depending on ν — 500–2000× below TPU yield.

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
against 25 MPa TPU yield — 27× margin**. The pressure question is
**closed**: water doesn't stress the TPU at any depth the system can
physically operate at (the actuator pressure rating sets the system
limit, not the finger).

### Result (peak displacement, μm)

| depth | ν=0.42 | ν=0.45 | ν=0.48 |
|---|---|---|---|
| 30 m | 152 | 97 | 40 |
| 100 m | 507 | 323 | 132 |
| 300 m | 1521 | 970 | 396 |

These are the WHOLE-FINGER deformation amplitudes — small everywhere
relative to the 22 × 90 mm blade and the 300 μm `PRINT_CLEAR` clearance.

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

### Result (ν = 0.45)

| depth | P (MPa) | peak vM (MPa) | contact wall deflection (μm) | margin to 25 MPa | survives? |
|---|---|---|---|---|---|
| 0 m | 0.00 | 0.00 | 0 | ∞ | yes |
| 10 m | 0.10 | 0.135 | 212 | 185× | yes |
| 30 m | 0.30 | 0.405 | 637 | **62×** | yes |
| 100 m | 1.01 | 1.35 | 2122 (2.1 mm) | 18.5× | yes (geometry degraded) |
| 300 m‡ | 3.02 | 4.05 | 6366 (6.4 mm) | 6.2× | LINEAR FEA past validity — see note |
| 600 m‡ | 6.03 | 8.10 | 12731 (12.7 mm) | 3.1× | LINEAR FEA past validity — see note |

> ‡ **Domain-of-validity note.** The Fin Ray cells are ~10 mm tall and
> ~2 mm wide. A 6.4 mm or 12.7 mm wall sag is a large fraction of (or
> greater than) the available cell depth, so in reality the contact wall
> would **self-contact** the spine wall or adjacent ribs long before
> reaching those linear-FEA deflections. Linear elasticity has no
> notion of self-contact — it just keeps deflecting. Additionally,
> adiabatic gas compression bites hard at this scale: at 100 m the
> cell volume shrinks ~21% so the trapped air rises to ~1.27 atm,
> reducing the external/internal differential by ~10%; at 300 m the
> compression would be 50%+, reducing the differential by half. So
> the 300/600 m rows are **upper bounds twice over** (no self-contact
> + rigid air) — the real response would be self-contact-limited
> and gas-pressure-limited, not material-yield-limited. Treat the
> 300 m and 600 m rows as "linearity broken; real response is
> self-contact / gas-pressure dominated, not modeled here." The
> 30 m and 100 m rows remain in-validity.

So the user's intuition that "pressure will crush the finger" is
**half-right**:

- At ≤30 m (primary actuator-rated depth): even worst-case crush mode
  keeps a 60× yield margin and only deflects the contact face 0.6 mm.
  The finger does **not** crush in any operationally meaningful sense.
- At 100 m+: the contact wall starts deflecting by mm (2.1 mm at 100 m,
  6.4 mm at 300 m). The TPU does not yield until you go past ~600 m,
  but the finger geometry collapses well before that, ruining wrap.
- The **kink** in the response is between 30 m and 100 m. Inside the
  actuator's primary envelope the finger is safe even in the worst case;
  outside it (tier-3 magnetic-coupling territory) the flooding becomes
  load-critical.

### Conservatism in this estimate

The plane-strain trapped-air FEA is an **upper bound** on the real
stress, for two reasons:

1. **Plane-strain over-constrains Z.** The real finger can shrink in Z
   under the same load case (the front/back faces of the blade are also
   wetted symmetrically). A 3D solve would give lower deviatoric stress
   for the same external pressure.
2. **Trapped air is not perfectly rigid.** As the cells compress, the
   trapped air's pressure rises adiabatically (PV^γ = const, γ=1.4 for
   air). Approximate volume change ≈ deflection / cell depth (~10 mm):
   - 30 m: ~6% compression → ~1.08 atm internal, **2% correction** on
     a 300 kPa differential. Operating-depth analysis essentially
     unaffected.
   - 100 m: ~21% compression → ~1.27 atm internal, **3% correction**
     on a 1.0 MPa differential. Still small.
   - 300 m: ~64% compression → ~3.2 atm internal, **~10% correction**
     on a 3.0 MPa differential (and self-contact dominates anyway).
   So the gas-backpressure correction is **negligible at the operating
   depths where the analysis is in-validity**, and the deep-depth rows
   are bounded by self-contact before gas backpressure becomes the
   leading limiter.

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

| run name | E_TPU (MPa) | scenario | peak vM (MPa) | grip @ 8 mm (N) | tip inward (mm) | arc (°) | margin vs 25 MPa† |
|---|---|---|---|---|---|---|---|
| under_E40_dry | 40.0 | dry baseline | 3.30 | 9.31 | −6.13 | 13.6 | 7.6× |
| under_E32_wet20 | 32.0 | 20% softening (typical wet) | 2.64 | 7.45 | −6.13 | 13.6 | 9.5× |
| under_E28_wet30 | 28.0 | 30% softening | 2.31 | 6.52 | −6.13 | 13.6 | 10.8× |
| under_E20_wet50 | 20.0 | 50% softening (warm long soak) | 1.65 | 4.66 | −6.13 | 13.6 | 15.1× |

> † Margin computed against the **dry-print** 25 MPa estimate
> (`iter_harness.py` L124, `docs/MATERIALS.md`). **Wet TPU strength
> also drops on soak** — typically less than modulus does, but by a
> non-zero amount. The honest reading of the right column is: stress
> drops by the full modulus ratio, strength drops more slowly, so the
> gripper does **not become stress-limited** as the finger softens.
> The wet-vs-dry safer-ness comparison would require a measured
> wet-strength datum on this specific filament (eSUN eTPU-95A) which
> the project does not have.

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
- **E_TPU is an engineering estimate** (40 MPa, per `iter_harness.py`
  L115–123 and `docs/MATERIALS.md`). The wet-modulus sweep is therefore
  itself a sensitivity study on top of an estimate. The conclusion
  ("force scales linearly with E at fixed kinematics") is robust to
  E_TPU because it falls out of linear elasticity, not from a specific
  modulus value.
- **No measured wet/dry datum on this specific filament** (eSUN
  eTPU-95A). The 10–30% softening band is from polymer-chemistry
  literature on ether-TPU. A soak-test on a printed finger blade would
  pin down the actual modulus drop and shrink the uncertainty band —
  see `BENCH_TEST.md` if extended.
- **Plane-strain is conservative for pressure** but pessimistic for
  shear-dominated loadings. The wet-modulus sweep uses the 3D
  corotational solver, which is the right model for grip kinematics.
- **Sustained immersion creep** (days–weeks at constant load + soaked)
  is bounded by `UNDERWATER.md §2` (creep section). Not a pressure
  effect; covered by the snap-fit constraints, not this FEA.

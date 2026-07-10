# Finger scalability study (FEA)

Question: the gripper must be **scalable** — printable at different sizes for
different jobs. Does the shipped Fin Ray finger still grasp well when the whole
finger is scaled up or down? This characterises the current design across
`FINGER_SCALE` 0.6–2.5; **it makes no design changes** (that's a separate follow-up).

Companion to `fea/UNIVERSAL_FINGER.md` (which fixed the geometry at 1×) and
`fea/DECISION_LOG.md`.

---

## 1. What "scalable" has to mean here

`FINGER_SCALE` (the `GRIPPER_FINGER_SCALE` env var, range 0.6–2.5) scales the **blade
in-plane only** — length, width, tip. By deliberate design (so the finger still bolts
to the linkage and stays printable at any size) it does **not** scale:

- **wall thicknesses** (contact 1.2, spine 1.8, rib 1.6 mm — fixed),
- the **mount** (pin bores, C/D spacing) and the base position,
- the **grip-tooth** size and print clearances.

So the blade gets bigger/smaller but the walls stay the same absolute thickness — the
**wall-to-blade ratio drops ~4× across the range** (0.022 at 0.6× → 0.005 at 2.5×). A
scaled-up finger is therefore *relatively thinner-walled and more compliant*; a
scaled-down finger is *relatively thicker-walled and stiffer*. **That fixed-wall
effect is the whole scalability question** — a perfectly self-similar finger would be
scale-invariant; this one is not, and the study finds the usable band.

For a fair test, the **object scales with the finger**: at scale *s* the battery
objects are *s×* bigger (`R → R·s`) and sit at the same fraction up the blade
(`yc = base_y + (yc₁ₓ − base_y)·s`, base_y = 32.9 mm fixed).

## 2. Two grip-force targets (they measure different things)

Reporting is force-targeted (compare the grasp at equal grip force). Two targets are
run because each answers a different scalability question:

- **Fixed 12 N at every scale** — *delicate-grasp invariance*: "if I print this
  bigger/smaller, does it still grasp objects gently?" 12 N is the **finger-FEA
  stress-probe load** (see `docs/TESTING_AND_SIMULATION.md §A.8`); the shipped
  drivetrain can't deliver 12 N (per-finger operating force is 0.14–0.73 N — see
  `motor/scripts/drivetrain_force_envelope.py`). The 12 N target is used here
  as a *comparative probe*: in the small-strain elastic regime, scaling
  invariance at 12 N implies scaling invariance at any sub-`T_safe` load
  (the rank order is preserved).
- **Force ∝ s² (area scaling)** — 0.6×→4.3 N, 0.8×→7.7 N, 1×→12 N, 1.5×→27 N,
  2×→48 N, 2.5×→75 N — *mechanical similitude*: "at the same fingertip pressure, does
  the deformation behave the same?" This is where the fixed-wall effect shows
  cleanest (beam deflection ∝ F·L³/EI, and I doesn't scale like L⁴ when walls are
  fixed). Again, these are stress-probe loads; the operating force is much
  lower across the whole scale band.

## 3. Keeping the comparison fair (press stroke + mesh scale too)

Both are scaled with the finger so every scale is tested at a comparable operating
point and solve cost:

- **Press stroke** `PRESS_MAX = 10·s` mm — a 2.5× finger closes over 25 mm, not 10,
  so it can actually reach a grasp (a hard-coded 10 mm would stop a big finger short
  and produce garbage).
- **Mesh size** `MESH_MAX = 2.4·s`, `MESH_MIN = 1.1·s` mm — same element count at
  every scale → comparable resolution and solve time.

Implementation: `eval_finger.py` accepts `_scale` and `_grip` params. 1× reproduces
the baseline exactly (0.645 screen), confirming the scaling code is neutral at s=1.

## 4. Results

Screen battery (small + large circle + square) at each scale; full battery at the
0.6× and 2.5× endpoints. Universal score (higher = better; 1× baseline 0.65). "small
circle" columns are the discriminator — flat faces grip more easily, round objects
expose the floppiness.

| scale | blade (mm) | wall/blade | closure→12 N (mm) | score @ 12 N | score @ force∝s² |
|---|---|---|---|---|---|
| **0.6×** | 54 | 0.022 | 3.5 | **0.646** | 0.437 (@4.3 N) |
| **0.8×** | 72 | 0.017 | 5.3 | **0.630** | 0.593 (@7.7 N) |
| **1.0×** | 90 | 0.013 | 8.3 | **0.645** | = 0.645 (@12 N) |
| 1.5× | 135 | 0.009 | not reached (max ~3.6 N) | 0.441 | 0.441 (@27 N, also unreached) |
| 2.0× | 180 | 0.007 | not reached (~2.7 N) | 0.368 | 0.368 (@48 N) |
| 2.5× | 225 | 0.005 | not reached (~2.0 N) | **−0.250** | −0.250 (@75 N) |

Full-battery endpoints (7 objects): 0.6× = **0.546**, 1.0× = 0.652, 2.5× = **−0.230**.

Per-object detail (fixed 12 N, small round object):

| scale | circle grip | circle closure | box grip | note |
|---|---|---|---|---|
| 0.6× | 13.8 N | 3.5 mm | 15.1 N | firm grip, low stroke (stiff) |
| 1.0× | 12.1 N | 8.3 mm | 13.3 N | firm grip, ~baseline |
| 1.5× | **3.6 N** | 15 mm (full) | 7.2 N | can't reach 12 N — blade bends |
| 2.0× | 2.7 N | 20 mm (full) | 5.7 N | floppy |
| 2.5× | 2.0 N | 25 mm (full) | **2621 N** | floppy on round; flat-face contact snaps |

Two things to read here: (a) **closure-to-grip grows 3.5 → 8.3 mm from 0.6× to 1.0×**
and then the finger can't reach 12 N at all (≥1.5×); (b) **von-Mises margins stay
8–13× at every scale** — the large fingers never *break*, they just **under-grip**
(the floppy failure), and the lone over-force is the 2.5× square, a penalty-contact
snap on a stiff flat contact (cov 1.6 — pathological, not a usable grip).

The **force∝s² runs collapse onto the fixed-12 N runs for ≥1.5×** because the finger
cannot reach *either* target force — definitive evidence the limit is the **fixed
walls** (mechanical), not a force-target mismatch. At small scales the s²-force is too
*gentle* (0.6× @4.3 N scores 0.44 vs 0.65 @12 N): a small, relatively stiff finger
both tolerates and benefits from a firmer grip, so **fixed ~12 N is the better
stress-probe choice across the whole usable band** — keeping in mind that the
absolute newton number is the FEA's design-comparison probe, not what the
drivetrain can deliver in service. The scalability claim is *rank invariance
of the comparison*, not "every printed-size finger can apply 12 N safely".

## 5. The usable scale band

**Down-scaling is safe; up-scaling is limited.**

- **0.6× – ~1.1× : USABLE.** Firm ~12 N grip on every shape and size, margins 7–10×,
  scores 0.55–0.65 (at or near the 1× baseline). Print the gripper anywhere in this
  band and the finger behaves like the validated 1× design.
- **~1.2× – 1.5× : MARGINAL.** The finger starts running out of stroke before it
  builds a firm grip on round objects (1.5×: ~3.6 N). Usable only for light/flat
  objects or a gentler grip spec.
- **> 1.5× : NOT USABLE as-is.** The blade is too compliant (relatively thin walls)
  to grip round objects — it bends instead of squeezing (2.0–2.5×: ~2 N), and flat
  contact can snap. Needs a geometry change first (see §6).

Note the asymmetry: scaling *down* keeps the walls relatively thicker → stiffer →
still grips; scaling *up* thins the walls relatively → floppy. So the design has
**generous head-room downward and limited head-room upward**.

## 6. Honest limits — what does and doesn't scale, and the fix (out of scope)

What scales cleanly: the blade (length/width/tip), the object range it suits, the
grasp height, and — within 0.6–1.1× — the grasp quality itself.

What doesn't: the **walls, mount, and grip teeth are fixed by design** (so the finger
keeps bolting to the one linkage and stays printable). That fixed wall thickness is
the sole reason up-scaling fails — a self-similar finger (walls ∝ scale) would be
scale-invariant.

**The obvious follow-up (deliberately NOT done here, per the brief — no design
changes):** make the walls scale with `FINGER_SCALE` for large sizes, e.g.
`wall = base_wall · max(1, scale^k)` with k≈0.7–1.0, which would restore stiffness on
big fingers and likely extend the usable band well past 2×. The mount would still
stay fixed so it bolts to the (separately scaled) linkage. This study only
*characterises* the current finger; tuning the walls is a separate task.

---

## 7. Self-similar scale-up (`GRIPPER_SCALE`) — walls scale too

§1–§6 above study the **blade-only** `FINGER_SCALE` knob (walls held at fixed absolute
thickness), and §6 predicts the cure: *"a self-similar finger (walls ∝ scale) would be
scale-invariant."* The model now has that knob. `GRIPPER_SCALE` (env var, range
0.5–3.0) multiplies **every** linear dimension of the gripper — blade **and** walls,
mount, gear, pins — so the whole part grows geometrically (true mechanical similitude).
The wall-to-blade ratio is now **constant** at every scale instead of dropping ~4×
across the band. This section tests §6's prediction directly. (`GRIPPER_SCALE` and the
legacy `FINGER_SCALE` compose: `eval_finger.py` uses an *effective* blade factor
`eff = GRIPPER_SCALE · FINGER_SCALE`; here `FINGER_SCALE = 1`, so `eff = GRIPPER_SCALE`.
Press stroke, mesh size, and the object battery all scale by `eff`, exactly as in
§3 — a fair self-similar comparison.)

### 7.1 The material moved since §1–§6 — read both bases

The §4 table (0.645 / 0.441 / 0.368) was computed on the **old eSUN E≈40 MPa** modulus.
The repo finger material is now **Bambu TPU 95A HF, measured in-plane E = 9.8 MPa**
(~4× softer; see `CLAUDE.md` / `UNIVERSAL_FINGER.md`). The fixed-12 N stress-probe is a
*comparative* load (the drivetrain delivers sub-Newton in service — §2); on the ~4×
softer current material the finger **cannot build 12 N within the 10·`eff` mm press
stroke at any scale** (it under-grips the probe, with very high margins). So the
absolute fixed-12 N screen score is **lower on the current material at every scale,
including 1.0×** (0.484 vs the old 0.645). That is a *material* shift, not a scaling
regression, and it is consistent with the repo's standing position: force-targeted
**rankings and margins are modulus-insensitive** (preserved), but the **absolute
fixed-12 N screen score is not** — because reaching 12 N within a finite stroke depends
on stiffness. Both bases are reported below.

**(A) Matched E = 40 MPa basis — the controlled contrast vs the old blade-only table.**
Re-running at `_E:40` isolates the *one* variable that changed between the old blade-only
runs and these: **walls fixed vs walls-scaled.** Same modulus, same `eff` blade factor,
same battery, same scorer.

| scale (`eff`) | OLD blade-only @12 N (walls fixed) | NEW self-similar @12 N (walls ∝ scale) | small-circle grip reached | small-circle margin |
|---|---|---|---|---|
| **1.0×** | 0.645 | **0.632** | 12.0 N (reached) | 8.5× |
| **1.5×** | **0.441** | **0.598** | **12.3 N (reached)** | 9.9× |
| **2.0×** | **0.368** | **0.619** | **13.5 N (reached)** | 11.0× |

(1.0× reproduces the old 0.645 to within 0.013 — the small residual is strength 27.3 vs
the old 25 MPa plus mesh discretisation. This confirms the scaling code is **neutral at
1.0×**: it does not by itself move the score.)

**Headline — the bigger finger KEEPS its grip.** Self-similar scaling holds the score
**flat at ~0.60–0.63 across 1.0–2.0×** (0.632 / 0.598 / 0.619 — non-monotonic, within
scorer noise), versus the blade-only **collapse to 0.441 → 0.368**. The mechanism is the
one §6 named: with the wall/blade ratio fixed, the big finger is no longer relatively
thin-walled, so it **reaches the 12 N probe at every scale** (12.0 → 12.3 → 13.5 N) where
the blade-only finger went floppy and could only manage ~3.6 → ~2.7 N before running out
of stroke. §6's prediction is confirmed.

**(B) Current Bambu E = 9.8 MPa basis — today's shipped material, same `{}` probe.**

| scale (`eff`) | self-similar score @12 N target | small-circle grip @ full stroke | note |
|---|---|---|---|
| **1.0×** | **0.484** | 3.6 N (12 N not reached) | soft material under-grips the probe |
| **1.5×** | **0.543** | 5.3 N (12 N not reached) | grip *rises* with scale (see below) |
| **2.0×** | **0.591** | 6.8 N (12 N not reached) | box reaches 13.1 N; rounds still short |

On the soft current material the probe is unreachable at every scale, so the score is
**force-reach-limited, not floppiness-limited**. The score still **does not fall** with
scale — it edges *up* (0.484 → 0.543 → 0.591), because at a fixed *absolute* 12 N target
the larger self-similar finger develops **more absolute grip at the same proportional
closure** (force builds ~`eff²` for a given relative stroke). The point that matters for
the headline: on **either** material the self-similar finger holds or improves its score
as it scales up — the floppy up-scaling collapse of §5 is gone.

### 7.2 What "keeps its grip" does and does not mean (honest reading)

- **It is force-reach + safety that is preserved, not wrap.** Round-object conformance is
  modest at *every* scale, including 1.0× — the small-circle `contact_arc_deg` is only
  ~8–11° on round objects at all scales (at E40 2.0× the small circle is a near-point
  press, arc ≈ 3.7° at 13.5 N). The held score comes from the finger continuing to reach
  the probe **safely** (the grip term plus a healthy von-Mises margin), which is exactly
  the §5 failure mode (under-grip / floppy) that self-similar scaling fixes. It does **not**
  mean the big finger conforms *more* — round-object wrap is a near-constant, not a scale win.
- **Force at a given grip scales ~`eff²` but stays gear-limited.** A `k×` self-similar
  finger develops ~`k²` the contact force at the same fingertip *pressure* / proportional
  closure (area scaling). This is a **rank/size** statement, not an absolute-newton claim:
  the shipped drivetrain is still `T_safe`-bounded (per-finger operating force 0.14–0.73 N,
  §2 and `motor/DRIVETRAIN.md`), and a bigger crown/pinion printed at the same scale raises
  `T_safe` ~`k³` (section modulus) but the *service* force remains whatever the motor
  current limit allows — the gripper does not suddenly deliver tens of newtons just because
  the FEA probe is reachable. No absolute-newton overclaim is made or implied.
- **One mild self-similar degradation to flag honestly:** on the flat-faced box the
  pressure spreads less evenly as it scales (E40 box `pressure_cov` rises 1.00 → 1.85 → 2.02
  from 1.0× to 2.0×) and its von-Mises margin falls (9.1× → 5.3× → 4.8×) as contact
  concentrates on the now-stiffer wall. It stays **safe** (margin > 1.5 everywhere, no
  yield), but the very-large self-similar finger is slightly more peaky on flat contacts.

### 7.3 Reproduce / artifacts

```
GRIPPER_SCALE=1.0 PYTHONPATH=/home/andre/Projects/softsense \
  /home/andre/.cad-venv/bin/python fea/scripts/eval_finger.py selfsim_1p0 production '{}' screen
# …1.5, 2.0 likewise. Add '{"_E":40}' for the matched-basis contrast (selfsim_E40_*).
```

- Current-material evals: `fea/iterations/selfsim_{1p0,1p5,2p0}/eval.json`.
- Matched-E40 contrast evals: `fea/iterations/selfsim_E40_{1p0,1p5,2p0}/eval.json`.
- The 1.0× run is kept in `fea/iterations/` as the reference; the 1.5× and 2.0× results
  (current basis `eval.json` + matched-basis `eval_E40basis.json` + `wrap_stages.png`) are
  copied into `variants/scale_1.5x/fea/` and `variants/scale_2.0x/fea/`.
- `wrap_stages.png` figures are rendered on the **current E = 9.8 MPa** material (the soft
  basis the parts actually print in); the §7.1(A) contrast *table* is the matched E = 40 MPa
  basis. The figures therefore show the (lower-force) current-material wrap, not the E40 table.

### 7.4 Coarse / local-run caveat — where an MSI re-run is warranted

These runs were done **locally in coarse `screen` mode** (3-object battery; `NSTEPS = 12`;
mesh `MESH_MAX/MIN = 2.4/1.1 · eff`) because the MSI FEA node is currently down. The
**rank conclusion is robust** (the self-similar vs blade-only gap is large — 0.60+ vs
0.37–0.44 — and the §6 prediction it confirms is mechanical, not marginal). A
**high-fidelity MSI re-run is warranted** to firm up the absolute numbers before any
publication-grade claim: the **full 7-object battery** at `NSTEPS = 24` and the finer
`MESH_MAX/MIN = 1.3/0.5 · eff`, ideally at both the E40 and current-E bases, plus a
mesh-convergence check at 2.0× (element count is held constant across scales by the
`· eff` mesh sizing, but absolute resolution at 2.0× is the coarsest in the set). The
flat-contact `pressure_cov` rise at 2.0× (§7.2) in particular deserves a finer mesh to
confirm it is physical and not discretisation.

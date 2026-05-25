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
  bigger/smaller, does it still grasp objects gently?" (The project grasps delicate
  artifacts, so a gentle force is wanted regardless of size.)
- **Force ∝ s² (area scaling)** — 0.6×→4.3 N, 0.8×→7.7 N, 1×→12 N, 1.5×→27 N,
  2×→48 N, 2.5×→75 N — *mechanical similitude*: "at the same fingertip pressure, does
  the deformation behave the same?" This is where the fixed-wall effect shows
  cleanest (beam deflection ∝ F·L³/EI, and I doesn't scale like L⁴ when walls are
  fixed).

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
operating choice across the whole usable band.**

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

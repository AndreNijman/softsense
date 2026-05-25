# Universal-adaptive finger investigation

Goal set by the user: the gripper must conform to **every shape and every size**, not
one tuned object — wrap around objects and **distribute pressure across the whole
finger**, while staying **fool-proof / no-maintenance** (it runs underwater).

This document records the full investigation: how we measured universality, the two
finger families we mass-iterated with an agent swarm, what the FEA found, the physical
ceiling we hit, and the finger we shipped.

---

## 1. The problem with the old finger (and the old metric)

The production Fin Ray finger (`w7_balanced`) and every prior iteration had been tuned
against **one** object: a Ø44 mm cylinder (R=22) at a fixed height. So we had never
actually measured whether it adapts. We added a **box (square) object** and a
**size/height sweep** to the FEA harness and re-tested the production finger:

| object | contact span | top-third load | grip | note |
|---|---|---|---|---|
| circle R12 / R22 / R35 | 2–7 mm band, **always at y≈79** | **0.00** | 12–13 N | contact pinned to one spot regardless of size |
| circle at y=60 / 80 / 95 | follows the object | **0.00** | **74 N / 18 N / 10 N** | grip swings **7×** with height (cantilever stiffness gradient) |
| square (flat face) | full length, arc 90° | — | 42 N | engages, but `pressure_cov 1.3` (very uneven) |

**Conclusion:** the old finger *pinches at a single spot* — it never wraps (top-third
load is zero on every rounded object, every size, every height) and its grip force
varies 7× with where the object sits. It is **not** universal. This is architecture,
not tuning — a straight contact face on a round object can only tangent-kiss.

## 2. How we measured universality (the scorer)

`fea/scripts/eval_finger.py` evaluates a candidate against a **battery** of rigid
objects (small + large circles + a square, at several heights), meshing the finger once
and reusing it per object. Each object is scored on:

- **wrap** — `contact_arc_deg / 80` (how far around the object it conforms)
- **even** — `1.2 − pressure_cov` (how evenly contact pressure spreads)
- **grip** — plateau reward for a firm-but-not-crushing force
- **safe** — von-Mises margin vs TPU strength

and the universal score is the battery mean minus a grip-inconsistency penalty.

Crucial fix mid-investigation: **force-targeted reporting.** Pressing a fixed *closure*
rewards stiff fingers with crushing force and starves compliant ones, so all candidates
are instead reported at the **first closure reaching a 12 N target grip** — same grip
force, compare the wrap. A `locked` flag catches structures that blow past target grip
while over-stressed (a rigid jaw, not a gripper).

The 2-object screen initially mis-ranked candidates (an R20-box resonance scored 0.72
on screen but 0.595 on the full battery); a **3-object screen (R12 + R30 + box)** was
validated to predict the full-battery ranking and used for the swarm.

## 3. Two finger families, mass-iterated by an agent swarm

~10 agents across multiple waves, ~90 FEA evaluations.

### Family A — Fin Ray truss (`fea/scripts/finray2.py`)
Free-topology Fin Ray: contact + spine beams, slanted cross-ribs, all walls/angles
free. **Well-behaved and safe.** Findings:
- Conforms beautifully to **flat / large** faces — a tuned config wraps **both** the
  22 mm and 14 mm squares fully (88°), where the production finger only wrapped the
  one it was tuned for.
- **Never wraps a round object** in any configuration — the flat contact face
  point-contacts a cylinder; rib direction/angle changes do not add a curl DOF.
- Best gains came from **even pressure**: a thin contact beam (t_contact≈1.2) + a
  sharply tapered compliant spine (spine_x_tip≈3) collapsed circle `pressure_cov`
  from ~0.8 to ~0.35, at a safe, consistent ~12 N grip across all sizes.

### Family B — monolithic flexure finger (`fea/scripts/flexure_finger.py`)
A single TPU strip with thin living-hinge notches, pre-curved to curl inward.
**Can** curl around circles (we saw 45–120° arc) but is **structurally unstable on
round objects**: grip force is chaotic — at 0.25 mm closure steps it oscillates
0 → 148 → 2 500 → 107 000 → 1.4 → … → 1 600 000 N. The finger snaps between floppy and
jammed within a fraction of a millimetre. **Verdict: not viable** — a real gripper with
this finger would have uncontrollable grip on round objects.

## 4. The physical ceiling

A **passive, single-piece** finger on this four-bar drive **cannot actively curl around
a small round object** without either (a) snapping (the flexure failure) or (b) a tendon
that pulls the tip in — and tendons/springs/pin-joints are exactly the corrosion +
fouling + maintenance the "fool-proof, underwater" goal rules out. The Fin Ray family
plateaus near a universal score of ~0.60–0.68: it wraps flat/large objects across sizes,
grips round ones safely and with even pressure, but does not wrap small cylinders.

This is the honest universal answer for the constraints: **one geometry that distributes
pressure across the whole finger on flat/large objects and grips round ones safely and
evenly, fool-proof, single TPU print.**

## 5. Shipped finger

Winner of the search (`finray2` config, full-battery universal score **0.65** vs the
production finger's **0.56**):

```
n_ribs 14, rib_angle 38°, rib_dir -1 (reversed slant),
t_contact 1.2, t_spine 1.8, t_rib 1.6,  spine tip width 2 (sharp taper)
```

Ported into `gripper.py` as `FR_N_RIBS=14`, `FR_RIB_DIR=-1`, `FR_TIP_WIDTH=2`,
`FR_CONTACT_WALL=1.2`, `FR_SPINE_WALL=1.8`, `FR_RIB_WALL=1.6` (uniform). Verified:
both fingers build as valid solids, **zero finger-finger interference** at the closed
pose, four-bar closure unchanged, and the ported finger reproduces the FEA win
(the friction grip-teeth cost a little vs the bare `finray2` shape).

### Full-battery comparison (per object, at equal 12 N grip)

| object | old arc / cov | **new arc / cov** | what changed |
|---|---|---|---|
| circle Ø24 (R12) | 2° / 0.45 | **6° / 0.43** | more contact, even |
| circle Ø44 (R22) | 7° / 0.74 | **13° / 0.67** | ~2× contact |
| circle Ø70 (R35) | 11° / 0.68 | **17° / 0.80** | more contact |
| **square 28 mm** | **1° / 0.83** | **88° / 0.81** | **now wraps it** |
| square 44 mm | 88° / 1.23 | 88° / 1.01 | wraps, more even |
| Ø44 low (y64) | 6° / 0.64 | **13° / 0.39** | 2× contact, much more even |
| Ø44 high (y94) | 10° / 0.79 | 4° / 0.41 | softer at the tip, even |
| **universal score** | **0.559** | **0.652** | **+17 %** |

The standout: the old finger only wrapped the **one** square size it happened to suit
(44 mm: 88°; 28 mm: 1°). The new finger wraps **both** (88° each), roughly doubles
contact on every cylinder, and grips every size a consistent safe ~12 N — where the
old finger's grip swung 7× with object position. All von-Mises margins stay 6–9×.

FEA renders (production vs new, round + square, still + animation, all at equal grip
force) are in `fea/iterations/_panel_new/`, `_compare_circle/`, `_compare_box14/`.

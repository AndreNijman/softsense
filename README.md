# Geared four-bar parallel-splay gripper

A full CAD reproduction of the robotic claw in the reference image, with a
working single-DOF motion model: **rotate one input shaft and both fingers
open/close symmetrically, splaying outward as they open so larger objects
drop into the mouth.**

## Mechanism

- Two equal **sector/spur gears** mesh on the centreline. The **left gear is
  driven by the input shaft** (coaxial with the left crank pivot); the mesh
  forces the right gear to counter-rotate, so one shaft moves both fingers as a
  mirror pair. *(The drive is therefore off-centre at the left pivot, not in
  the middle of the plate — see "Assumptions".)*
- Each gear is the **crank of a non-parallelogram four-bar linkage**
  (`A`=crank pivot, `B`=follower pivot, `C`/`D`=coupler pins). The finger is
  rigid with the coupler `C–D`.
- Link lengths were chosen by a design search so the finger both **translates
  apart and rotates ~18° outward** over the travel (funnel mouth), while
  staying well clear of any four-bar dead-point.

Travel: jaws closed (faces ~1.6 mm apart) → open (~60 mm at the base,
~116 mm at the serrated tips).

## Files

| File | What it is |
|---|---|
| `gripper.py` | Parametric build123d generator + the four-bar solver (source of truth). `GRIPPER_OPEN` env var = 0…1. |
| `gripper_interactive.step` | Geometry baked at the **closed** pose, paired with a live motion sidecar. |
| `.gripper_interactive.step.js` | CAD Explorer sidecar: one **`open`** slider drives the whole linkage live (same solver as the Python). |
| `gripper_closed/mid/open.step` | Static STEP poses at open = 0 / 0.5 / 1. |
| `gripper_motion.gif` | Rendered open↔close animation. |
| `gripper_hero_open.png`, `gripper_hero_closed.png` | Iso renders. |

## Regenerate / re-pose

```bash
source /home/andre/.cad-venv/bin/activate          # build123d + OCP toolchain
STEP=/home/andre/.claude/skills/cad/scripts/step

# any pose, 0 (closed) .. 1 (open)
GRIPPER_OPEN=0.7 python $STEP gripper.py -o gripper_open70.step

# numeric kinematic self-check (gaps, splay, branch continuity)
python gripper.py
```

## Interactive viewer

Open `gripper_interactive.step` in CAD Explorer and drag the **`open`** slider
(= turning the shaft). Mesh and edges move together live.

```bash
cd /home/andre/.claude/skills/render
EXPLORER_WORKSPACE_ROOT=/home/andre/gripper-cad EXPLORER_ROOT_DIR=. \
  npm --prefix scripts/viewer run dev:ensure -- \
  --workspace-root /home/andre/gripper-cad --root-dir . --file gripper_interactive.step
```

## Coordinate convention

`X` = jaw open/close (right +), `Y` = toward fingertips (up +),
`Z` = depth = all revolute & gear axes. Units: mm.

## Assumptions / caveats

- **Off-centre drive.** A single shaft can only drive both jaws symmetrically
  if the cranks counter-rotate, which needs the two gears to mesh each other
  (one driven). The image looks centre-driven; if a literal central input is
  required, add an idler gear between an input pinion and one crank gear — a
  mechanical add-on, no change to the finger kinematics.
- Gear teeth are simplified (clean meshing pitch circles, half-tooth phased),
  not full involute profiles. Pins are plain shoulder pins with cap heads, no
  threads. Both are visual/representative at this scale.
- Dimensions are inferred from one image, not measured from the original part.

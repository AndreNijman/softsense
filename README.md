# Underwater geared four-bar gripper with Fin Ray fingers

A robotic gripper CAD model with working single-DOF motion: **rotate one input
shaft and both fingers open/close symmetrically, splaying outward as they open.**
The jaws are **Fin Ray-style compliant fingers** (3D-printed in TPU, with a
ridged grip texture) that bend and wrap *around* a grasped object. The
gear/linkage drive is housed in a clean **flooded enclosure** designed for
**underwater** use (drain/flood holes, corrosion-resistant material choices —
see `UNDERWATER.md`).

## Mechanism (one DOF)

- Two equal **spur gears** mesh on the centreline. The **left gear is driven by
  the input shaft** (coaxial with the left crank pivot); the mesh counter-rotates
  the right gear, so one shaft moves both fingers as a mirror pair.
- Each gear is the **crank of a non-parallelogram four-bar linkage**; the finger
  is rigid with the coupler. The link lengths give a translate-apart **+ ~18°
  outward splay** over the travel, well clear of any four-bar dead-point.
- The gears, fixed pivots and lower links live **inside the enclosure**; only the
  upper links, finger pins and the Fin Ray fingers are exposed.

Travel: closed (jaw faces ~1.6 mm apart) → open (~60 mm at the base, ~118 mm at
the fingertips).

## Fin Ray fingers (TPU)

Each finger is a compliant triangular truss — a near-straight contact beam, a
slanting spine, joined by a row of **same-direction slanted ribs** with hollow
cells. That asymmetric rib geometry is what makes the tip curl toward and
conform around an object when the contact face is loaded. The contact face has
**fine friction ridges** (≈2.2 mm pitch) so grasped objects don't slip. Printed
in flexible **TPU** (ether-based for sustained immersion — see `UNDERWATER.md`).

## Enclosure (flooded, underwater)

Hollow gearbox housing: rounded slate body, a back-wall bore where the drive
shaft exits, and a back **mounting flange with 4× M4 holes**. The two top slots
are sized to the **measured arm sweep** so the four-bar links never clip the
case. **Drain/flood holes** (a bottom row + low side holes) let it flood and
drain in any orientation — no trapped air (buoyancy/crush) and pressure
equalizes with depth. Material/sealing guidance is in `UNDERWATER.md`.

## Files

| File | What it is |
|---|---|
| `gripper.py` | Parametric build123d generator + four-bar solver + Fin Ray finger + enclosure (source of truth). Env vars: `GRIPPER_OPEN` = 0…1 (pose), `GRIPPER_FINGER_SCALE` = 0.6…2.5 (finger size). |
| `gripper_interactive.step` + `.gripper_interactive.step.js` | **Interactive** — drag the `open` slider to rotate the shaft live in CAD Explorer. |
| `gripper_closed/mid/open.step` | Static poses at open = 0 / 0.5 / 1. |
| `gripper_motion.gif` | Rendered open↔close animation. |
| `gripper_hero_open.png`, `gripper_hero_closed.png` | 3D hero renders. |
| `UNDERWATER.md` | Engineering guide: gears underwater, flooded vs sealed, material BOM, sealing, drainage, checklist. |
| `DFM.md` | Design-for-3D-printing standards (walls, overhangs, holes, clearances, edge-breaks) and how each part complies. |

## Regenerate / re-pose

```bash
source /home/andre/.cad-venv/bin/activate          # build123d + OCP toolchain
STEP=/home/andre/.claude/skills/cad/scripts/step
GRIPPER_OPEN=0.7 python $STEP gripper.py -o gripper_open70.step   # any pose 0..1
GRIPPER_FINGER_SCALE=1.6 python $STEP gripper.py -o gripper_big.step  # bigger fingers
python gripper.py                                  # numeric kinematic self-check
```

## Interactive viewer

Open `gripper_interactive.step` in CAD Explorer and drag the **`open`** slider
(= turning the shaft); mesh and edges move together live.

```bash
cd /home/andre/.claude/skills/render
EXPLORER_WORKSPACE_ROOT=/home/andre/gripper-cad EXPLORER_ROOT_DIR=. \
  npm --prefix scripts/viewer run dev:ensure -- \
  --workspace-root /home/andre/gripper-cad --root-dir . --file gripper_interactive.step
```

## Coordinate convention

`X` = jaw open/close (right +), `Y` = toward fingertips (up +),
`Z` = depth = revolute & gear axes. Units: mm.

## Assumptions / caveats

- **Off-centre drive.** A single shaft can only drive both jaws symmetrically if
  the cranks counter-rotate, which needs the two gears to mesh each other (one
  driven) — so the input sits at the left pivot, not dead-centre. For a literal
  central input, add an idler between a centre pinion and one crank gear; the
  finger kinematics don't change.
- **Fin Ray-style, not Festo's patented variant.** This is the generic
  adaptive-compliant triangular finger principle (slanted-rib truss), widely
  used and 3D-printable. Festo's *Fin Ray Effect®* is a specific patented
  tooth-shape variant.
- Gear teeth are simplified (clean meshing pitch circles, half-tooth phased),
  not full involute. Pins are plain shoulder pins. Both are representative at
  this scale. Real compliant grip (wrap-around) is a TPU material behaviour —
  the CAD shows the undeformed finger; the motion model opens/closes it rigidly.
- Dimensions are inferred from one reference image, not measured hardware.

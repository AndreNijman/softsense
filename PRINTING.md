# 3D-printing guide

How to print the geared four-bar / Fin Ray gripper (`gripper.py`, `README.md`).
This gripper is now **fully 3D-printed with ZERO hardware** — no screws, no
bolts, no metal dowels. Every pivot is a printed snap pin and the front cover
clicks on with integral cantilever clips. Covers per-part orientation,
supports, material, and the print settings that matter, plus how the built-in
clearances behave and how to tune them.

This is the **fabrication** companion to `UNDERWATER.md` (which covers material
*chemistry* for seawater). Pick orientation and settings here; pick the exact
filament grade there.

## Parts list (what comes out of `gripper.py`)

`gen_step()` emits, in world coords, one `enclosure`, two drive arms
(`drive_arm_R`, `drive_arm_L`), two followers (`follower_R/L`), two Fin Ray
fingers (`finger_R/L`), one `front_cover`, and **seven 3D-printed snap pins**
(`pin_A_R`, `pin_B_R`, `pin_C_R`, `pin_D_R`, `pin_B_L`, `pin_C_L`, `pin_D_L`).
The **input shaft is integral to `drive_arm_L`** (it *is* the left axle, hence
no `pin_A_L`) — there is no separate shaft part to print.

**Everything in the queue is printed. There is no hardware to buy.** The print
queue is: enclosure, 2 drive arms, 2 followers, 2 fingers, front cover, and the
7 snap pins (3 hidden axle pins + 4 visible finger pins).

## Drop-into-slicer plates (start here)

The fastest path to a print is the **pre-oriented, pre-packed plates** produced
by `make_print_plates.py`. They rotate every part to its supportless orientation
and arrange them on a common bed for you:

```bash
source /home/andre/.cad-venv/bin/activate
python export_parts.py          # parts/*.stl  (CLOSED pose, from gripper.py)
python make_print_plates.py     # print_plates/  (oriented + plated STLs)
```

Outputs (see `PRINT_PLATES.md` for the full layout):

- `print_plates/plate_rigid_1.stl` — all 13 rigid parts (PETG/ASA/Nylon).
- `print_plates/plate_tpu_1.stl` — the 2 TPU Fin Ray fingers (separate material).
- `print_plates/oriented/<part>.stl` — each part alone, already oriented.

> The plates are a **derived artifact**: re-run `export_parts.py` *then*
> `make_print_plates.py` after ANY change to `gripper.py` geometry. The script
> wipes and rebuilds `print_plates/` each run.

## Supportless orientation table (audited)

Every part below was mesh-audited for supportless printing (down-facing surface
steeper than 45° from horizontal). The "support" column is the residual
overhang area in the chosen orientation. **The whole set prints supportless**
with two caveats called out below.

| Part | Qty | Print orientation (from `gen_step()` export pose) | Support? |
|---|---|---|---|
| `enclosure` | 1 | **No rotation.** Open slot/cavity face **+Z up**, solid floor (drain bores) on bed. Drains print as vertical bores; clip-catch windows print as vertical wall slots. | ~1272 mm² — interior floor ceilings mostly bridge; **back flange (+Y) may want a few support pillars / a small skirt** |
| `front_cover` | 1 | **Rotate 180° about X.** Flat outer face on bed, 4 snap clips point **+Z up** (self-supporting beams). | 184 mm² — hook underlips bridge; no support |
| `drive_arm_L` | 1 | **Rotate 180° about X.** Gear/arm plate anchored flat on the bed, integral input shaft pointing **+Z up** (vertical cylinder = self-supporting rings). | 23 mm² — only the Ø8→Ø10 coupler shoulder at the shaft tip bridges; **see torsion note below** |
| `drive_arm_R` | 1 | **No rotation.** Flat 5 mm plate face-down, pivot axis vertical. | 0 |
| `follower` | 2 | **No rotation.** Flat 5 mm bar face-down. | 0 |
| `snap_pin_axle` | 3 | **Rotate 180° about X.** Head flange on bed, barb tip **up** (lead-in cone narrows going up). | 0 |
| `snap_pin_finger` | 4 | **Rotate 180° about X.** Head flange on bed, barb tip **up**. | 12 mm² — 0.7 mm locking-lip bridge; no support |
| `finger_R` | 1 | **No rotation.** Lying flat on a 28×96 Z-face, build height 10 mm; Fin Ray cells in the build plane. | ~0 |
| `finger_L` | 1 | **No rotation.** Same as `finger_R` (chiral mirror). | ~0 |

**Two orientation facts the older prose got slightly wrong, now corrected:**

1. **The snap pins and the front cover must be FLIPPED 180° about X** relative to
   the `gen_step()` export pose. In the *exported* STL the pin head (Ø7.8 flange)
   sits at **+Z (top)** and the barb at the bottom; the front-cover clips hang
   **downward**. `make_print_plates.py` applies the 180° flip so the head/outer
   face lands on the bed and the barb/clips point up — the supportless direction.
   If you orient the raw `parts/*.stl` by hand, do the flip yourself.
2. **The finger grip ridges are on the −X *contact* face, which is vertical** when
   the finger lies flat (it is not a top/bottom face). The ridge grooves run up
   the 10 mm build height as in-plane perimeters — so "ridge side down" from the
   old notes is moot for the flat-on-Z-face orientation; either Z face on the bed
   works. What matters is keeping the 28×96 cell plane horizontal so the truss
   self-supports.

### drive_arm_L — supportless vs. torsion (the one real trade-off)

The audited supportless orientation flips the part **180° about X** so the
**gear plate anchors on the bed and the shaft stands vertical** (no support under
the shaft; only the Ø8→Ø10 coupler shoulder at the shaft tip bridges, ~23 mm²).
Printing it the *other* way — shaft tip on the bed, gear plate at the top —
cantilevers the whole 26×50 plate in mid-air (529 mm² of support); don't. The
cost of the correct orientation is that the shaft's layers run **transverse to
the drive-torque axis**, the weak direction for interlayer shear. To keep it
supportless *and* strong:

- **100 % infill + 5–6 perimeters in the shaft region.**
- Print PETG hot for max interlayer fusion; slow on the shaft.
- If you will drive the gripper hard, the optional metal-shaft upgrade in
  "Integral shaft on `drive_arm_L`" below trades zero-hardware for strength.

(The older "lay the shaft horizontal" hint from `export_parts.py` is
geometrically impossible — the shaft is perpendicular to the plate; you choose
plate-flat/shaft-up *or* shaft-down, not both flat at once.)

### Clearance constant note (read before tuning)

The live value in `gripper.py` is **`PRINT_CLEAR = 0.3 mm`** (confirmed in
`DFM.md`), giving pivot bores of **Ø5.2 mm** (`AXLE_BORE_R = PIN_R + 0.3 = 2.6`,
shank Ø4.6). Some prose further down still says "0.25 mm / Ø4.9–5.1" — that is
**stale**; trust 0.3 mm / Ø5.2. `SNAP_CLEAR = 0.35`, `SNAP_BARB_PROUD = 0.7`,
`SNAP_BARB_SEAT = 0.3` are current.

## Per-part print recommendations

Orientations are described in the **printed/Z-up** frame (`gen_step()` rotates
the model so fingers point +Z and the shaft exits horizontally). "On the bed"
means that face is the first layer.

| Part | Material | Orientation on bed | Supports | Layer height | Walls / perimeters | Infill |
|---|---|---|---|---|---|---|
| `finger_R` / `finger_L` (Fin Ray) | **TPU 95A** | **Flat on a Z side face** (finger lying on its side, ribs/cells in the build plane) | **No** | 0.15–0.20 mm | 3–4 perimeters (spars print as solid wall) | 100% (or ≥80%) |
| `drive_arm_R` | PETG / ASA / Nylon | **Flat** (gear+arm pad-down, axis vertical) | No | **0.12–0.16 mm** (fine, for the teeth) | **5–6 perimeters** (solid eyes + teeth) | 40–60% |
| `drive_arm_L` (integral shaft) | PETG / ASA / Nylon | **Shaft vertical** (see Integral shaft) | Yes (gear/arm fan above shaft) | 0.12–0.16 mm | 5–6 perimeters | 60–80% |
| `follower_R` / `follower_L` | PETG / ASA / Nylon | **Flat** | No | 0.16–0.20 mm | **5–6 perimeters** (load goes through the pivot eyes) | 30–50% |
| `enclosure` | PETG / ASA / Nylon | **Bottom (drain-hole face) on bed, open slot face up** | Mostly no (see notes) | 0.20–0.24 mm | 3–4 perimeters | 15–25% |
| `front_cover` (snap-clip) | PETG / ASA / Nylon | **Outer face on bed, clips pointing up** | **No** | 0.16–0.20 mm | 4–5 perimeters (clips need solid walls) | 30–50% |
| `pin_A_R` / `pin_B_R` / `pin_B_L` (hidden axle pins) | **PETG** | **Head-down, axis vertical, barb up** | **No** | 0.12–0.16 mm | 100% / solid | 100% |
| `pin_C_R` / `pin_D_R` / `pin_C_L` / `pin_D_L` (finger snap pins) | **PETG** | **Head-down, axis vertical, barb up** | **No** | 0.12–0.16 mm | 100% / solid | 100% |

### Fin Ray fingers — `finger_R` / `finger_L` (TPU)

These are the part that makes the gripper grip, so they get the most care.

- **Material: flexible TPU, ~95A shore.** The whole Fin Ray principle is
  *material compliance* — the slanted-rib triangular truss lets the tip curl and
  wrap around an object when the contact face is loaded. A rigid print of this
  finger doesn't grip adaptively; it has to flex. 95A is a good default: soft
  enough to conform, stiff enough to hold force. Go softer (85A) for delicate /
  light objects, stiffer (98A) for more grip force.
- **Orientation: lay the finger flat on one of its Z side faces** so the layers
  run *across* the finger thickness and the ribs/cells lie in the build plane.
  Printed this way the triangular cells, ribs and the hollow interior are all
  self-supporting — **no supports needed inside the cells**, which you could
  never cleanly remove from a flexible part anyway. (Printing it "standing up"
  tip-toward-the-sky would put the rib overhangs in mid-air and bury supports in
  the compliant truss — avoid.)
- **Layer adhesion is the failure mode for flexible parts under repeated flex.**
  Laying the finger flat on its side puts the bending stress *along* the layers
  (in-plane), which is the strong direction — flex cycles don't peel layers
  apart. Print slow (20–30 mm/s), high-ish temp for good fusion, and turn part
  cooling down for TPU.
- **Walls: print the spars solid.** With 3–4 perimeters at the wall thickness in
  the model (`FR_WALL = 2.8 mm`), the contact spar, spine and ribs come out as
  solid extruded walls. Use **100% (or ≥80%) infill** so the floor/cap insets
  and any thicker sections are dense — a hollow spar is squishy in the wrong way.
- Keep the grip ridges on the contact face (≈2.2 mm pitch) — printed flat-on-side
  they reproduce cleanly as little teeth running across the finger depth.

#### Why the fingers now have fillets & chamfers (new — print-friendly TPU)

The finger geometry now bakes in rounded corners specifically so TPU prints
cleaner and doesn't crack in service. These are applied last, after all the
booleans, so they round real edges of the finished truss:

- **`FR_CELL_FILLET = 0.8 mm` — fillet on every internal rib-cell / spar-junction
  corner.** TPU fatigue cracks *start* at sharp interior re-entrant corners,
  where each flex cycle concentrates stress. Rounding those corners removes the
  stress riser, so the truss survives many times more open/close cycles before a
  rib tears. It also gives the nozzle a smooth interior path instead of a hard
  inside corner that leaves a void.
- **`FR_BASE_CHAMFER = 0.5 mm` — chamfer on the bottom (bed-face) edges.**
  Because the finger prints flat on its Z side face, that bottom face is where
  **elephant's foot** (first-layer squish bulge) appears. A 0.5 mm chamfer gives
  the squish somewhere to go, so the bottom edge stays dimensionally true and the
  finger doesn't rock or bind on its bulged base.
- **`FR_TIP_FILLET = 1.5 mm` (blade apex) + `FR_GRIP_TIP_FLAT = 0.2 mm` (grip
  tooth tips).** A knife-edge in TPU prints as a single fragile bead that
  delaminates; rounding the apex and putting a tiny flat on each grip-tooth tip
  makes those features print as multi-perimeter geometry that holds together and
  doesn't peel.

Net: the fingers print with cleaner walls, no elephant-foot, and far better
flex-fatigue life. Don't "simplify" them back to sharp corners.

### Drive arms & followers — `drive_arm_R/L`, `follower_R/L`

- **Material: PETG, ASA, or nylon** (or PETG-CF / nylon-CF for stiffness). These
  are the rigid load path from the shaft to the fingers. PLA is fine for a dry
  bench prototype but **not for underwater** (see `UNDERWATER.md`).
- **Print flat** (the main face on the bed, pivot axis vertical). Flat keeps the
  pivot **eyes** strong: the bore walls are then concentric rings of perimeter,
  and the pin load is carried in-plane rather than trying to split layers.
- **High perimeter count (5–6) at the eyes.** The eyes and the meshing teeth are
  the stressed features; perimeters carry that load far better than infill, so
  bias walls up and infill down. Followers see pin-to-pin tension/compression —
  perimeters along the bar handle it.
- **Gear teeth want fine layers (0.12–0.16 mm).** The drive-arm teeth mesh on the
  centreline; coarse layers leave a stair-stepped flank that meshes roughly and
  loses backlash control. Finer layers + a clean seam (below) give a smoother
  mesh. A small chamfer/deburr on the tooth tips after printing helps.

### Snap pins — `pin_A_R/B_R/B_L` (axle) & `pin_C_R/D_R/C_L/D_L` (finger)

**All seven pivots are now 3D-printed push-to-snap pins — no metal dowels, no
fasteners.** Each pin has a HEAD flange at one end (a stop that can't pull
through) and a SPLIT, BARBED compliant tip at the other: a `+` cross-slot lets
the tip squeeze inward as it's pushed through the bore, then a locking lip
springs back out *past* the far bore face to lock the pin in place. A tapered
lead-in cone at the very tip starts the insertion.

- **Material: PETG** (or nylon). The snap tip must flex without snapping — PETG
  has the toughness/elongation for a living-hinge-style barb. **Avoid PLA**: it's
  too brittle, the barb fingers crack off on the first insertion.
- **Orientation: print HEAD-DOWN, axis VERTICAL, barb pointing UP — no supports.**
  This is correct for the geometry and it prints supportlessly:
  - The **lead-in cone** tapers from wide (`barb_max_r ≈ 3.0 mm`) at its base up
    to a small flat tip (`SNAP_TIP_R = 1.0`). Printed point-up, a cone narrows as
    Z rises — that's the printable direction, every layer sits on a slightly
    larger one below. No support under the cone.
  - The **locking lip** is only `SNAP_BARB_PROUD = 0.7 mm` proud of the shank; the
    step out to the lip is a tiny ~0.7 mm horizontal overhang the printer bridges
    in a layer or two. No support needed.
  - The **`+` split slot runs vertically** (parallel to the print axis), so it's
    just two empty channels the nozzle walks around — it never traps support.
  - The **head flange** is the first thing on the bed: a flat, well-adhered disc
    that anchors the print.
- **Layer adhesion is the load-bearing caution for snap pins.** When you push the
  pin through a bore, the split tip fingers **flex outward/inward**, and that
  bending puts tension *across* the layer boundaries on the outer fibre of each
  finger. Printed axis-vertical, the layers stack across the flex direction — so:
  print **PETG at the high end of its temperature range** for maximum interlayer
  fusion, **slow down** through the barb region, and **reduce/turn off part
  cooling at the barb** so the thin split fingers fuse fully. A poorly-fused barb
  shears off on first insertion. (The plain bearing shank below the slot stays
  solid and just needs to be round — that's the part the link actually pivots on.)
- **Print 100% solid.** These are small structural pins; there's no room for
  infill and you want maximum strength. Fine layers (0.12–0.16 mm) keep the shank
  round so the joint turns smoothly.
- **Two kinds, same print orientation, different assembly:**
  - **3 hidden axle pins** — `pin_A_R`, `pin_B_R`, `pin_B_L` (head at the back
    wall, barb snapping into the front cover boss). These are the fixed pivots
    buried inside the housing.
  - **4 visible finger pins** — `pin_C_R`, `pin_D_R`, `pin_C_L`, `pin_D_L` (head
    as a small cap above the finger top, barb at the bottom). These carry the
    Fin Ray fingers on the coupler.
  Both kinds print the same way (head-down, barb-up, no supports); only where they
  go in the assembly differs.
- **Tuning fit** — see the [Fit tuning](#fit-tuning-do-this-first) section. In
  short: too tight to push in → loosen the bore (`PRINT_CLEAR`) or ream it; barb
  won't lock / pin pulls back out → the lip isn't clearing the far face, raise
  `SNAP_BARB_PROUD` and/or `SNAP_BARB_SEAT`; pin too hard to ever remove → lower
  `SNAP_BARB_PROUD`.

### Front cover — `front_cover` (snap-clip, tool-free)

**The front cover now snaps on with 4 integral cantilever clips (2 per long side
wall) — no screws.** It also closes the open front of the housing and carries
the bosses that support the far end of the three internal axle pins. Push it on
(the hooks cam in over the lead-in and click into the side-wall windows); to
remove, flex the four hooks outward.

- **Orientation: print the OUTER face on the bed, so the clips point UP — no
  supports.** The four cantilever snap clips stand up off the cover's inner face
  as ~15 mm-tall vertical beams. With the cover's flat outer face down, those
  clips grow straight up in the build direction and print as self-supporting
  walls. (Print it the other way — inner face down — and the clips would
  cantilever sideways in mid-air and demand support that's a nightmare to clean
  out of the hooks.)
- **The hook lead-in chamfer (`SNAP_LEADIN = 2.0 mm`) prints as part of the
  upward clip** and is what cams the hook over the housing's catch edge during
  push-on. Don't sand it flat — it's the ramp that makes the snap work.
- **Same layer-adhesion caution as the snap pins.** The clips flex outward every
  time you snap the cover on/off, putting tension across the layers at the clip
  root. Print PETG hot, solid walls (4–5 perimeters so the clip beam is mostly
  perimeter), and slow at the clip roots.

### Enclosure body — `enclosure`

- **Print open-slot-face up, drain-hole face on the bed.** After the Z-up
  rotation the two wide arm slots are on top; printing that face upward means the
  housing is essentially open at the top and needs **no internal supports** for
  the cavity. The only solid spanning the top is the narrow central bridge
  between the slots, which is short enough to bridge.
- **Drains print as clean vertical bores.** With the bottom (drain-row) face on
  the bed, the bottom-row flood/drain holes run straight up as vertical
  cylinders — they print round and dimensionally true with no support.
- **The snap-clip catch windows** are through-windows in each long side wall (they
  double as side drains). They're vertical slots in the walls, so they print
  cleanly with the housing on its base; just deburr the top edge of each window —
  that's the lip the cover hook latches behind, so it needs to be crisp.
- **The back mounting flange overhangs sideways.** It sticks out at the rear and
  may need a **small support skirt / a few support pillars** under its outer edge,
  or print it bridge-able by keeping the overhang modest. Check the slice — it's
  the one feature on this part that might want support.
- Walls 3–4 perimeters, infill 15–25% — it's a housing, not a load member; the
  flange bolt area benefits from the higher end.

## Integral shaft on `drive_arm_L` — orientation trade-off

`drive_arm_L` carries the **input shaft** as one rigid piece with the gear and
crank arm; that shaft transmits **all the drive torque**, so its print
orientation is a real strength decision. Both options below are **fully printed**
(this gripper has zero hardware):

- **Recommended: print the arm with the shaft vertical** (shaft pointing up off
  the bed, the gear/arm at the top). The shaft is then a stack of full-perimeter
  rings, so torsion and bending load it *along* the layers — the strong
  direction. The cost is that the gear/arm fans out above the shaft and needs
  **support** under that overhang; use easy-to-remove support and clean up the
  tooth flanks afterward.
- **The alternative — arm flat, shaft lying down — is support-free but weak:** the
  shaft's layers then run *across* its axis, so drive torque tries to shear one
  layer off the next. For anything but a light bench test this is the wrong way.
- **Optional non-default upgrade (departs from zero-hardware):** if you'll drive
  the gripper hard, you *can* print the arm flat (support-free, strong eyes/teeth)
  and bond/pin a Ø8 mm metal shaft into a relieved hub instead of the printed
  shaft — a metal-strength input shaft with an easy print. This adds hardware, so
  it's outside the all-printed default; mentioned only as an option for high-load
  use, and it pairs with the marine-grade hardware in `UNDERWATER.md`.

## General settings

### Clearances: joints (0.25 mm) and snaps (0.35 mm)

The model bakes in **four independent clearance/fit knobs**. Know which one drives
which feature — they are *not* interchangeable:

| Constant | Value | Controls | Symptom it fixes |
|---|---|---|---|
| `PRINT_CLEAR` | 0.25 mm/side | pin-in-bore turning fit (link/arm/gear rides on its pin) | pivots too tight or too sloppy |
| `SNAP_CLEAR` | 0.35 mm | front-cover **clip** hook vs side-wall window engagement | cover won't click / cover rattles |
| `SNAP_BARB_PROUD` | 0.7 mm | snap-**pin** locking-lip protrusion (retention force) | pin pulls back out / pin won't ever come out |
| `SNAP_BARB_SEAT` | 0.30 mm | how far the snap-pin lip seats past the far bore face | weak/no "click", pin loose along its axis |

- **Bores ride on `PRINT_CLEAR`.** Links/gears ride on their pins via
  `AXLE_BORE_R = PIN_R + 0.25`; the finger mount holes and link-bar eyes use a
  slightly tighter `+0.15`. Net effect: pin shanks are ~Ø4.6 mm, bores are
  ~Ø4.9–5.1 mm, giving a free-but-not-sloppy pivot.
- **`SNAP_CLEAR` (0.35 mm) is the cover clip's engagement gap**, set by the window
  cut `SNAP_WIN_Z`. It's a *different feature* from the pins — adjust it only for
  cover-click feel, not for pivot fit.
- **`SNAP_BARB_PROUD` and `SNAP_BARB_SEAT` are the snap-pin retention knobs.** The
  lip stands 0.7 mm proud and seats 0.30 mm past the far face — that overhang is
  what locks the pin and gives the click. More PROUD = harder to remove; more
  SEAT = more positive click but needs the bore length to match.
- **First, calibrate your printer.** Print an XY tolerance test and a small
  pin-in-hole coupon in your actual filament before committing; PETG and TPU each
  oversize holes differently. The 0.25 mm value assumes a typical FDM machine
  holding ±0.1–0.15 mm.

#### Adjusting the fit

- **Pivot too tight (link won't turn on its pin):** don't reprint first — **ream
  the bore one drill size up**, or run the pin in once to wear it free. Permanent
  fix: raise `PRINT_CLEAR` (and the `+0.15` bores) and regenerate.
- **Pivot too loose / sloppy:** lower `PRINT_CLEAR` (e.g. 0.15–0.20), regenerate
  and reprint the link/arm/gear.
- **Snap pin too tight to push through:** that's a *bore* problem — loosen
  `PRINT_CLEAR` or ream the bore; don't touch the barb.
- **Snap pin won't lock / springs back out:** the lip isn't clearing the far face.
  Raise `SNAP_BARB_PROUD` (more lip) and/or `SNAP_BARB_SEAT` (seat further past
  the face). Check the bore depth actually lets the lip emerge.
- **Snap pin impossible to remove (or barb shears installing it):** lower
  `SNAP_BARB_PROUD` so the lip flexes in more easily; also check the layer-adhesion
  print settings above — a brittle barb shears instead of flexing.
- **Cover won't click / pops off:** adjust `SNAP_CLEAR` (smaller = tighter latch)
  and/or check the side-wall window's top edge is crisply deburred.
- **To regenerate after changing any clearance:**
  ```bash
  source /home/andre/.cad-venv/bin/activate
  STEP=/home/andre/.claude/skills/cad/scripts/step
  python $STEP gripper.py -o gripper_closed.step          # default pose
  # (gripper.py is read-only here — edit a copy if you need to change clearances)
  ```

### First layer

- Use a deliberate first layer: slightly squished, slower speed. **TPU
  especially** benefits from a clean, well-adhered first layer (it's the
  flat-on-side face of the finger). A textured/PEI bed and no extra adhesion is
  usually enough; avoid over-squish that closes up the bottom grip ridges.
- The `FR_BASE_CHAMFER = 0.5 mm` on the finger already gives the first layer room,
  but still mind elephant's foot on the **bore eyes** and on the **snap-pin head**
  — squish there can pinch a bore or fatten the head so the cover won't seat. A
  small chamfer or -0.1 mm first-layer horizontal expansion keeps them true.

### Seam placement

- **Move the Z-seam off the gear tooth flanks.** A seam blob on a meshing flank
  adds backlash and roughness. In the slicer set seam to **Rear/Aligned** (or
  paint the seam onto a non-meshing back edge of the gear) so the visible seam
  lands away from the engaged teeth. Keep the same setting on both arms so they
  mesh symmetrically.
- **On the snap pins, put the seam on the head, not the barb fingers.** A seam
  witness on a split-tip finger is a crack starter; align the seam to the head
  flange or the solid shank.

### Post-processing

- **Deburr the pivot bores** so the snap pins seat. Lightly chamfer/ream every pin
  bore (a countersink bit spun by hand is enough) and break the edge — a burr or
  elephant-foot lip at the bore mouth stops the snap-pin lead-in cone from
  starting, or shaves the barb on the way through.
- **Clean the gear flanks.** Knock down layer ridges and any seam witness on the
  teeth; cycle the mesh by hand and sand any tight spots.
- **Snap pins & clips:** trim any stringing in the `+` slot, make sure the slot is
  fully open (a fused-shut slot won't flex), and test-flex each barb/clip gently
  before final assembly.
- **TPU fingers:** trim stringing, check the grip ridges are crisp, flex the
  finger a few times to confirm the cells move and the layers hold.

## Fit tuning — do this first

**Before printing the whole set of 7 snap pins, print ONE and verify the click.**
Snap fit is the highest-risk feature of an all-printed assembly; calibrate it on
a single pin and a scrap coupon before you commit filament to six more.

1. **Print one snap pin** (any of the 7 — they print identically: head-down,
   axis-vertical, barb-up, no supports, PETG, solid, slow at the barb).
2. **Print a scrap bore coupon** — a small block with one through-hole at the
   real bore size (`AXLE_BORE_R = PIN_R + 0.25`, so ~Ø4.9 mm). Match the bore
   *length* to the real joint stack so the lip emerges where it should.
3. **Push the pin through and feel for the click.** You want: it pushes in with
   moderate force, the barb flexes, then **clicks** as the lip springs out past
   the far face, and it won't pull straight back out.
   - No click / pulls out → raise `SNAP_BARB_PROUD` / `SNAP_BARB_SEAT`.
   - Too tight to push / barb shears → loosen the bore (`PRINT_CLEAR`) or fix
     barb layer adhesion (hotter, slower, less cooling).
   - Locks but impossible to remove → lower `SNAP_BARB_PROUD`.
4. **Only once the single pin clicks cleanly**, print the remaining 6 (and the
   front cover, whose clips use the same flex principle — dry-snap it once to
   confirm before final assembly).

## Quick start — print then assemble

**Print (2 plates, no supports):**

```bash
source /home/andre/.cad-venv/bin/activate
python export_parts.py && python make_print_plates.py
```

1. **Calibrate once** — XY tolerance + a pin-in-hole coupon in BOTH filaments
   (rigid + TPU). Confirm a printed Ø5.2 bore accepts the snap-pin Ø4.6 shank and
   turns freely.
2. **Fit-tune ONE snap pin** + a scrap bore coupon; verify the click before
   committing the other six (see Fit tuning below).
3. **Slice `plate_rigid_1.stl`** — PETG/ASA, 0.2 mm (0.12–0.16 mm for the gear
   teeth if your slicer lets you vary by object), no supports, brim on the tall
   skinny pins and the enclosure. Add a few **support pillars under the enclosure
   back flange** if the preview shows it drooping.
4. **Slice `plate_tpu_1.stl`** — TPU 95A, 0.15–0.20 mm, ≥80 % infill, slow
   (20–30 mm/s), part cooling down, no supports.
5. **Assemble** (tool-free, see `ASSEMBLY.md`): fit each Fin Ray finger on its 2
   finger pins → drop the arms/followers into the housing on the 3 axle pins →
   **snap on the front cover** (it clicks; flex the 4 hooks outward to remove).
6. **Function check** — turn the shaft on `drive_arm_L`; both fingers must
   open/close symmetrically.

**Per-group settings at a glance:**

| Group | Material | Layer | Walls | Infill | Supports |
|---|---|---|---|---|---|
| Fingers (`plate_tpu_1`) | TPU 95A ether-based | 0.15–0.20 mm | 3–4 | ≥80 % | none |
| Pins (on `plate_rigid_1`) | PETG | 0.12–0.16 mm | solid | 100 % | none |
| Structure (rest of `plate_rigid_1`) | PETG / ASA / Nylon | 0.16–0.20 mm (0.12–0.16 for gear teeth) | 4–6 | 30–60 % (15–25 % enclosure) | none (flange may want a few pillars) |

## Print order / checklist

1. **Calibrate** — XY tolerance + pin-in-hole coupon in each filament (rigid +
   TPU). Confirm a printed bore accepts your snap-pin shank and turns freely.
2. **Fit-tune the snap pins** — print **one** snap pin + a scrap bore coupon and
   verify the **click** (see [Fit tuning](#fit-tuning-do-this-first)) BEFORE
   committing to the full set. Tune `PRINT_CLEAR` / `SNAP_BARB_PROUD` /
   `SNAP_BARB_SEAT` here, not after you've printed seven.
3. **Enclosure** — slot-face up, drains on bed; add a support skirt under the
   flange if the slice shows overhang. Longest print; start it early.
4. **Drive arms** ×2 — fine layers, high perimeters. `drive_arm_R` flat;
   `drive_arm_L` shaft-vertical.
5. **Followers** ×2 — flat, high perimeters.
6. **Front cover** ×1 — outer face down so the snap clips print upward, no
   supports.
7. **Snap pins** ×7 — PETG, head-down/axis-vertical/barb-up, no supports, slow +
   low cooling at the barb (3 axle pins + 4 finger pins).
8. **Fin Ray fingers** ×2 — TPU, flat on side face, slow, ≥80% infill. (The
   fillets/chamfers are in the model; don't remove them.)
9. **Post-process** — deburr all bores so the snap pins seat, clean gear flanks,
   clear the snap-pin slots, test-flex every barb and clip.
10. **Dry-fit** — snap the axle pins through the eyes; arms and followers must
    pivot freely. Mesh the two gear sectors and check for smooth, low-backlash
    engagement.
11. **Assemble** — fit the fingers on the C/D snap pins, drop the mechanism into
    the housing on the A/B axle pins, then **snap on the front cover** (no
    screws — it clicks).
12. **Function check** — turn the input shaft on `drive_arm_L`; both fingers must
    open/close symmetrically and splay outward. Then read `UNDERWATER.md` for
    material/seawater prep before it gets wet.

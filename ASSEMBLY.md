# Assembly instructions — Underwater geared four-bar / Fin Ray gripper

How to assemble the gripper from printed parts (`gripper.py`) and stainless
hardware (`BOM.md`) into a working, single-DOF, flooded underwater gripper.
Turn one input shaft and **both jaws open/close symmetrically, splaying
outward** as they open.

Read `BOM.md` for the parts/hardware list and `PRINTING.md` for printing and
post-processing first. This document assumes you have printed and deburred all
parts and bought the 316/A4 hardware.

Part names used here match `gripper.py`: `enclosure`, `front_cover`,
`drive_arm_R`, `drive_arm_L`, `follower_R`, `follower_L`, `finger_R`,
`finger_L`. Pivots: **A_R** (right drive axle), **B_R / B_L** (follower axles),
**C_R, D_R, C_L, D_L** (finger pins). The **left drive arm's axle is its own
integral shaft** in a back-wall bushing — there is no A_L pin.

---

## Tools needed

- Hex/Allen keys for the M3 and M4 socket-head screws
- Small spanner / nut driver for M4 nylon-insert locknuts
- Reamer or drill bits (≈Ø5.0 mm) to free any tight pivot bores
- Deburring tool / countersink bit (hand-spun) for bores and dowel ends
- Fine file or sandpaper for gear-flank cleanup
- Soft-jaw pliers or an arbor press for seating the bushing
- Calipers (verify the 0.25 mm joint clearance / pin-in-hole fit)
- Marine grease (optional — break-in only; not required for the flooded mesh)
- A tub of water for the flood check

---

## Assembly steps

### 1. Print prep & test-fit

1. Confirm all parts are printed in the chosen seawater materials (see `BOM.md`):
   rigid parts in acetal/glass-nylon, fingers in **ether-based TPU 95A**.
2. **Deburr every pivot bore** (A_R, B_R, B_L, C/D, and the finger mount holes)
   with a hand-spun countersink, and **break the edges on all dowels/screws** so
   joints turn without shaving plastic.
3. **Clean the gear flanks** on both `drive_arm_R` and `drive_arm_L`: knock down
   layer ridges and any seam witness on the teeth.
4. **Test-fit the pivots to the designed 0.25 mm clearance.** A printed bore
   (~Ø4.9–5.1 mm) should accept your Ø4.6 mm pin/screw **free but not sloppy**.
   - Too tight (won't turn): ream/drill one size up (~Ø5.0 mm) or run the pin in
     once to wear it free.
   - Too loose (rattles): take up slack with a thin shim washer or a slightly
     larger pin (or lower `PRINT_CLEAR` and reprint — `gripper.py` is read-only,
     so edit a copy).
5. Tap/clear the 4× M4 flange holes and 4× M3 cover holes to size.

### 2. Seat the input-shaft bushing

1. Press the **PTFE/acetal plain bushing** into the back-wall shaft bore of the
   `enclosure` (the bore at A_L, `SHAFT_BORE_R = 5.0`). It should be a light
   press fit, square to the wall.
2. Confirm the bore is clear — **no sealed bearing, no lip seal, no O-ring**
   (flooded design; the shaft turns wet). Do **not** fit Oilite bronze.

### 3. Mesh the two drive arms with correct gear timing

This is the one delicate step. The two 16-tooth sector gears mesh on the
centreline (X = 0); their teeth must **interleave with a half-tooth offset** so
the jaws come out symmetric.

1. Hold the gripper at the **closed pose** as your reference. At closed,
   `drive_arm_L`'s crank points **up and slightly inboard** (~104° from +X) and
   `drive_arm_R` is its **mirror**.
2. Bring the two gear sectors together so their pitch circles touch on the
   centreline. **Before engaging the mesh, rotate one arm by half a tooth pitch**
   — that's **360° / 16 / 2 = 11.25°** — so a tooth of one gear sits in the gap
   of the other (the teeth interleave, not tip-to-tip).
3. With the half-tooth offset set, the cranks are a true mirror pair and the two
   fingers will be symmetric. **Sanity check:** at closure the C-pin base gap
   should be small (~1.6 mm; jaw faces nearly touching). If the jaws come out
   lopsided, you meshed off by a tooth — separate, re-offset by half a tooth,
   re-engage.

### 4. Seat the drive-arm axles in the back-wall bosses

1. Seat **`drive_arm_R`** on its **A_R** axle: pass an M4 screw (or Ø4.6 mm
   dowel) through the arm's clearance bore into the **back-wall boss** at A_R,
   from inside the cavity. Fit the M4 **nylon-insert locknut** on the back side.
2. Seat **`drive_arm_L`**: thread its **integral input shaft** out through the
   back-wall bushing (from inside the cavity, shaft pointing out the back), so
   the gear/arm sits in the cavity and the **rear D-coupler** projects behind the
   flange. Keep the half-tooth mesh from Step 3 engaged as you seat it.
3. Recheck the mesh is still interleaved and both arms swing freely.

### 5. Add the followers

1. Seat **`follower_R`** on its **B_R** axle (back-wall boss), and connect its
   far eye to the right crank at the **D_R** location. Repeat for **`follower_L`**
   on **B_L** to **D_L**.
2. Use M4 screws into the B bosses with nylon-insert locknuts. The followers are
   identical parts; orientation is by which side they bolt to.
3. The four-bar on each side is now A→C (crank), B→D (follower), C→D (coupler).

### 6. Fit the Fin Ray fingers to the C/D pins

1. Place **`finger_R`** so its bracket eyes line up with **C_R** and **D_R**;
   place **`finger_L`** on **C_L / D_L**. The fingers are chiral — the contact
   face (with grip ridges) must face **inboard**, toward the centreline.
2. Pass the long **finger pins** (M4 / Ø4.6 mm, ~24 mm) through C and D, capping
   the finger to the coupler so each finger is rigid with its coupler CD.
3. Fit the M4 **nylon-insert locknuts**. The finger pins are the visible ones
   above the housing.

### 7. Tighten the pivots — snug but free

For **every** pivot (A_R, B_R, B_L, C/D ×4), the locknut is a **positional stop,
not a torque setting**:

1. Run the nyloc up until the joint just stops being sloppy in the Z (axial)
   direction.
2. Then **back the nut off** until the arm/finger **pivots freely under its own
   weight**. The nylon insert holds that position — **no threadlocker needed**
   (and threadlocker would gum a flooded joint anyway).
3. Confirm by hand: every link, follower and finger must move freely with no
   binding and no rattle.

### 8. Bolt on the front cover (4× M3)

1. If using the optional `front_cover`, set it over the enclosure opening and
   fasten with the **4× M3 socket-head screws** into the housing-wall holes.
2. Ensure the cover has **at least one vent/drain hole** so it doesn't trap air
   behind it (the cover keeps debris out but must still flood).

### 9. Mount to the robot via the flange (4× M4)

1. Bolt the back **flange** to the robot arm interface with the **4× M4 bolts**.
2. **If the arm is a dissimilar metal** (aluminium / anodized / other stainless),
   fit the **nylon/PTFE isolation washers + shoulder bushings** at the 4 flange
   bolts so the all-316 gripper isn't galvanically tied to the frame.

### 10. Couple the servo to the D-shaft

1. Mate your **waterproof servo / actuator coupling** to the rear **D-profile
   coupler** on `drive_arm_L`'s shaft (`SHAFT_DFLAT = 1.4` flat — the D keys the
   coupling so it can't slip).
2. Use an IP68/submersible or potted servo, or a sealed/oil-filled actuator with
   a pressure compensator for deeper work. The actuator carries the only real
   waterproofing burden — the gripper itself is passive and flooded.

---

## 11. Test the motion (in air)

1. Rotate the input shaft (turn the actuator, or the shaft directly).
2. **Both jaws must open and close symmetrically**, splaying ~18° outward as they
   open (funnel mouth) and coming nearly together at closed.
3. Watch the mesh: smooth, low-backlash engagement through the full travel, no
   tight spots or skipped teeth. If one jaw leads the other, the gears are meshed
   off by a tooth — go back to Step 3 and re-time with the half-tooth offset.
4. Confirm everything moves freely: arms, followers and both compliant fingers.
   Press a finger's contact face and confirm the Fin Ray tip curls toward /
   around the load.

## 12. Flood check (before it gets wet)

1. **Drain/flood holes clear:** confirm the bottom-row holes and low side-wall
   holes are open and unobstructed (not bridged shut by print artefacts or
   debris).
2. **No trapped air:** the front cover (if fitted) has a vent hole; no blind bolt
   pockets or dead-end cavities retain bubbles.
3. **Submerge and watch the bubbles:** lower the gripper into water **mouth-down**
   first, then **mouth-up** — bubbles must escape both ways and the cavity must
   fully flood. Cycle the jaws open↔close underwater to flush any last trapped
   air through the mesh and slots.
4. Once it floods and drains freely in any orientation with no retained air, the
   flooded build is sealed-free and ready. After every salt dive, **rinse with
   fresh water**, cycle the jaws to flush grit, dry, and inspect (see the
   pre-/post-dive checklist in `UNDERWATER.md`).

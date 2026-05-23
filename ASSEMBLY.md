# Assembly instructions — fully 3D-printed underwater gripper

> ## NO TOOLS. NO HARDWARE. ZERO FASTENERS.
> Every part of this gripper — including all pivot pins and the front cover —
> is **3D-printed and snaps together by hand**. No screws, no nuts, no dowels,
> no bearings, no bushings, no glue, no Allen keys. If you are reaching for a
> tool, stop: this build does not need one.

How to assemble the gripper entirely from printed parts (`gripper.py`) into a
working, single-DOF, **flooded underwater** gripper. Turn one input shaft and
**both jaws open/close symmetrically, splaying outward** as they open.

Read `README.md` for the mechanism overview, `parts/MANIFEST.md` for the part
list and print orientations, and `PRINTING.md` for material/post-processing
first. This document assumes every part is printed and deburred.

Part names match `gripper.py`: `enclosure`, `front_cover`, `drive_arm_R`,
`drive_arm_L`, `follower_R`, `follower_L`, `finger_R`, `finger_L`. Pivots:
**A_R** (right drive-arm axle), **B_R / B_L** (follower axles), **C_R, D_R,
C_L, D_L** (finger pins). The **left drive arm's axle is its own integral
shaft** seated in the back-wall bore — there is no A_L pin.

Printed pins, two roles, one component family (all ~24 mm; they differ in which
end the head is on, not in length):
- **3 axle dowels** (`snap_pin_axle`) — plain headed dowels for A_R, B_R, B_L;
  dropped in **from the front** before the cover, then **trapped by the cover
  bosses** (no barb needed — the cover captures them).
- **4 finger snap pins** (`snap_pin_finger`) — barbed, head-on-top, for C_R, D_R,
  C_L, D_L; pushed **down from above** the finger, barb springing out below the
  coupler to self-lock.

---

## How the snap pins work (read this first)

Each pin is a printed peg with two ends:

- a **head flange** at one end — the stop that can't pass through the bore, and
- a **split, barbed compliant tip** at the other — sawn by a printed cross-slot
  into four springy jaws with a tapered lead-in and a locking lip.

To install: line up the bores it has to pass through, then **push the barb end
straight in**. The tapered tip cams the four jaws inward as it traverses the
bore stack; the moment the locking lip clears the far face, the jaws **spring
back out and click**, catching the lip against that far face. The head flange
stops it on the near side. The pin is now captured axially — it **cannot back
out** on its own.

To remove (tool-free): **pinch the four split barb jaws together** with your
fingernails (squeeze the cross collapses to under bore size) and **push/pull the
pin straight out**. Do not pry — flex the jaws inward and it slides free
undamaged.

Clearances are built in: **0.25 mm** print clearance on every moving bore/slot,
**~0.35 mm** snap-engagement clearance on the clips and barbs. You should feel a
positive click, then a small amount of axial play — that's correct, it's a
flooded pivot, not a press fit.

---

## Assembly steps

### 1. Print prep & snap test

1. Confirm all parts are printed in the chosen materials (see
   `parts/MANIFEST.md`): rigid parts in PETG/Nylon, fingers in **TPU ~95A**.
2. **Deburr every bore** — A_R, B_R, B_L, the four C/D finger holes, the
   back-wall axle holes, the cover boss bores, and the back-wall shaft bore —
   with a hand-spun countersink or a twist of a deburring blade. Knock the
   first-layer "elephant-foot" lip off the bore mouths so pins enter square.
3. **Clean the gear flanks** on `drive_arm_R` and `drive_arm_L`: knock down
   layer ridges and any seam witness so the teeth mesh without shaving.
4. **Test each snap pin in a spare bore before assembly.** Push a pin through
   any matching bore: it must **cam in, click past the far face, and hold** when
   you tug the head. Then pinch the barb jaws and confirm it **comes back out**.
   - Won't click / barb shears: the bore is too tight or the jaws are fused by
     stringing — clean the cross-slot, deburr the bore, retry.
   - Clicks but rattles loose: that's fine for a flooded pivot; the lip still
     catches. Only worry if the head pulls through (then reprint at lower
     clearance — `gripper.py` is read-only, so edit a copy).
5. **Test the cover clips on the body once, dry:** push the cover straight on
   until the 4 hooks click into the side-wall windows, then flex the hooks out
   and remove. This proves the clip geometry before you trap the mechanism.

### 2. Mesh the two drive arms with correct gear timing

This is the one delicate step. The two 16-tooth sector gears mesh on the
centreline (X = 0); their teeth must **interleave with a half-tooth offset** so
the jaws move symmetrically.

1. Hold the pair at the **closed pose** as reference. At closed, `drive_arm_L`'s
   crank points up and slightly inboard (~104° from +X); `drive_arm_R` is its
   mirror.
2. Bring the two gear sectors together so their pitch circles touch on the
   centreline. **Before the teeth engage, rotate one arm by half a tooth** —
   that's **360° / 16 / 2 = 11.25°** — so a tooth of one gear drops into the gap
   of the other (teeth interleave, not tip-to-tip).
3. With the half-tooth offset set, the cranks are a true mirror pair.
   **Sanity check at closed:** the C-pin base gap should be small (~1.6 mm; jaw
   faces nearly touching). If the jaws come out lopsided later, you meshed off by
   a tooth — separate, re-offset by half a tooth, re-engage.

### 3. Drop the arms and followers into the open-front housing

The enclosure prints **open-front** so the mechanism drops straight in onto the
back-wall axle bosses. Keep the half-tooth mesh from Step 2 engaged throughout.

1. **Seat `drive_arm_R`:** lower it into the cavity so its axle bore sits over the
   **A_R** back-wall boss. It is only *located* by the boss now (not yet captured
   in Z — that's Step 5).
2. **Seat `drive_arm_L` (integral shaft) — one motion:** thread its **integral
   input shaft tip-first** through the back-wall shaft bore from inside the
   cavity as you lower the arm, so the gear/arm seats in the cavity and the
   **rear D-coupler** projects behind the flange. There is no separate axle and
   **no bushing to press** — the printed shaft rides directly in its printed bore
   (flooded, runs wet). Confirm the shaft turns freely in the bore.
3. **Add the followers:** seat **`follower_R`** so one eye sits over the **B_R**
   back-wall boss and the other eye lines up with the right crank's **D_R** end;
   repeat **`follower_L`** on **B_L** to **D_L**. The followers are identical
   parts — orientation is by which side they fall on.
4. Each side now reads A→C (crank) and B→D (follower), with C→D the coupler.
   Recheck the mesh is still interleaved and both arms swing freely by hand.

### 4. Drop in the 3 axle dowels (from the front, before the cover)

The 3 axle pins (`snap_pin_axle`, for **A_R**, **B_R**, **B_L**) are **plain
headed dowels** — no barb. They are captured between the back-wall socket and the
front-cover boss, so they go in **before** the cover.

1. With an arm/follower seated, drop an **axle dowel** straight **down from the
   open front** through its bore: through the drive arm (A_R) or follower
   (B_R/B_L) and into the **back-wall socket**. The dowel's **head flange sits up
   top** (toward the cover); the lead-in tip seats in the back-wall socket.
2. Repeat for all three (A_R through drive_arm_R; B_R through follower_R; B_L
   through follower_L). Each arm/follower must still **pivot freely** on its dowel.
   - (There is no A_L pin — the left arm's integral shaft is its own axle.)

### 5. Snap the front cover on (traps the axle dowels)

1. Set **`front_cover`** over the open front, the 4 hooks aligned to the four
   side-wall windows (2 per long side).
2. **Push it straight on** until all **4 cantilever clips click** into their
   windows. The cover's inner-face **bosses now cap the 3 axle-dowel heads** —
   the dowels are trapped between back-wall socket and cover boss and **cannot
   fall out**. No tools, no fasteners.
3. To remove later, flex the 4 hooks **outward** through the windows and lift the
   cover straight off; the axle dowels can then lift out.

### 6. Snap the fingers onto the C/D ends (4 finger snap pins)

1. Place **`finger_R`** so its bracket eyes line up with **C_R** and **D_R**, and
   **`finger_L`** on **C_L / D_L**. The fingers are chiral — the ridged contact
   face must face **inboard**, toward the centreline.
2. For each of C_R, D_R, C_L, D_L: push a **finger snap pin straight down from
   above the finger**, head-flange-on-top. The barb traverses the finger eye and
   the coupler/crank end beneath it and **springs out below** with a click; the
   head caps flush on top of the finger.
3. The finger is now rigid with its coupler CD. Tug each pin head — it must hold.
   These 4 pins are the visible ones standing proud above the housing.

### 7. Couple a waterproof servo to the rear D-shaft

1. Mate your **waterproof servo / actuator coupling** onto the rear **D-profile
   coupler** on `drive_arm_L`'s integral shaft (the milled flat keys the coupling
   so it can't slip).
2. Use an IP68/submersible or potted servo, or a sealed/oil-filled actuator with
   a pressure compensator for depth. The actuator carries the **only**
   waterproofing burden — the gripper itself is passive and fully flooded.

### 8. Mount via the flange holes (no bolts)

1. The back **flange** has 4 through-holes. Because this build is **hardware-free**,
   mount it **without bolts**: pass **zip-ties** through the 4 holes and cinch the
   flange to the robot interface, **or** print a set of snap-pegs (the same
   barbed-pin family) and push them through the holes into matching holes on the
   mount.
2. No metal fasteners are required anywhere on the gripper. If your mount
   *demands* bolts, that interface is outside this tool-free build.

---

## Test the motion (in air)

1. Rotate the input shaft (turn the actuator, or the rear D-coupler directly).
2. **Both jaws must open and close symmetrically**, splaying ~18° outward as they
   open (funnel mouth) and coming nearly together (~1.6 mm) at closed.
3. Watch the mesh: smooth, low-backlash engagement through the full travel, no
   tight spots or skipped teeth. If one jaw leads the other, the gears are off by
   a tooth — go back to **Step 2** (mesh timing) and re-time with the half-tooth
   (11.25°) offset.
4. Confirm everything moves freely: both arms, both followers, both compliant
   fingers. Press a finger's contact face and confirm the Fin Ray tip curls
   toward / around the load.

## Flood check (before it gets wet)

1. **Drain/flood holes clear:** confirm the bottom-face row and the low
   side-wall holes are open and unobstructed (not bridged shut by print artefacts
   or debris). The 4 cover-clip windows also vent.
2. **No trapped air:** there are no blind pockets or sealed cavities — the snap
   pins replace bolt counterbores, so nothing holds a bubble. Confirm the cavity
   is open through the slots and holes.
3. **Submerge and watch the bubbles:** lower the gripper into water
   **mouth-down** first, then **mouth-up** — bubbles must escape both ways and the
   cavity must fully flood. Cycle the jaws open↔close underwater to flush any last
   trapped air through the mesh and slots.
4. Once it floods and drains freely in any orientation with no retained air, the
   flooded build is ready. After every salt dive, **rinse with fresh water**,
   cycle the jaws to flush grit, dry, and inspect.

---

## Tool-free disassembly

Reverse the build with bare hands — no tools:

1. **Finger pins (C/D ×4):** pinch the four split barb jaws under the
   coupler/crank, push each pin up and out, lift the fingers off.
2. **Axle pins (A_R, B_R, B_L):** pinch each barb where it protrudes past the
   front cover and pull the pin out the back; the arm/follower releases.
3. **Front cover:** flex all 4 cantilever hooks **outward** through the side-wall
   windows simultaneously and lift the cover straight off.
4. **Left drive arm:** withdraw its integral shaft back through the bore; lift the
   arms and followers out of the open-front cavity.

Every pin is reusable — pinch, don't pry, and the barbs survive many cycles.

# Assembly instructions — fully 3D-printed underwater gripper

> ## NO TOOLS. NO HARDWARE. ZERO FASTENERS.
> Every part of this gripper — including all pivot pins and the front cover —
> is **3D-printed and snaps or slides together by hand**. No screws, no nuts,
> no dowels, no bearings, no bushings, no glue, no Allen keys. If you are
> reaching for a tool, stop: this build does not need one.

How to assemble the gripper entirely from printed parts (`gripper.py`) into a
working, single-DOF, **flooded underwater** gripper. Turn one input shaft and
**both jaws open/close symmetrically, splaying outward** as they open.

Read `PRINTING.md` for material, orientation, and post-processing first. Read
`UNDERWATER.md` for seawater material chemistry. This document assumes every
part is printed, deburred, and fit-tested.

Part names match `gripper.py` `gen_step()`: `enclosure`, `front_cover`,
`drive_arm_R`, `drive_arm_L`, `input_pinion_shaft`, `follower_R`, `follower_L`,
`finger_R`, `finger_L`. Pivots: **A_R, A_L** (drive-arm axles), **B_R / B_L**
(follower axles), **C_R, D_R, C_L, D_L** (finger pins). The drive input enters
via a right-angle crown + pinion stage and exits the **housing bottom** — there
is no shaft exiting the back or side.

---

## Part inventory (17 printed parts, 0 hardware)

| Part label | Qty | Role |
|---|---|---|
| `enclosure` | 1 | Flooded gearbox housing, open front, bottom mounting flange |
| `front_cover` | 1 | Snap-on cover with 4 integral cantilever clips |
| `drive_arm_R` | 1 | Right gear sector + crank arm (rides on axle dowel `pin_A_R`) |
| `drive_arm_L` | 1 | Left gear sector + crank arm + **integral crown gear** (rides on axle dowel `pin_A_L`) |
| `input_pinion_shaft` | 1 | Vertical input shaft: pinion + shaft + collar + bottom D-coupler |
| `follower_R` | 1 | Right B→D link bar |
| `follower_L` | 1 | Left B→D link bar |
| `finger_R` | 1 | Right Fin Ray compliant jaw (TPU) |
| `finger_L` | 1 | Left Fin Ray compliant jaw (TPU) |
| `pin_A_R` | 1 | Axle dowel — right drive-arm pivot |
| `pin_A_L` | 1 | Axle dowel — left drive-arm pivot |
| `pin_B_R` | 1 | Axle dowel — right follower pivot |
| `pin_B_L` | 1 | Axle dowel — left follower pivot |
| `pin_C_R` | 1 | Finger snap pin — right crank-coupler joint |
| `pin_D_R` | 1 | Finger snap pin — right follower-coupler joint |
| `pin_C_L` | 1 | Finger snap pin — left crank-coupler joint |
| `pin_D_L` | 1 | Finger snap pin — left follower-coupler joint |
| **Total** | **17** | **Zero purchased hardware** |

---

## How the two pin families work (read this before assembling)

The 8 printed pins divide into two families with different retention
mechanisms. Do not confuse them.

### Axle dowels — `pin_A_R`, `pin_A_L`, `pin_B_R`, `pin_B_L` (4 pins)

Plain headed cylinders with a **narrow pilot tip** at the far end. No split
barb. Retention is purely **geometric sandwich**:

- **−Z stop:** the flat shank shoulder (r 2.3 mm) is wider than the
  stepped-bore flood hole (r 1.5 mm) in the back wall. The pilot tip centres
  in the flood hole; the shank shoulder **bottoms on the rigid bore step** and
  cannot pass through.
- **+Z stop:** the head flange (r 3.9 mm) is wider than the cover-boss bore
  (r 2.6 mm). Once the cover is snapped on, the head seats against the
  cover-boss inner face and **cannot lift past the boss**.

The dowel is **sandwiched with essentially no axial slop** between two rigid
stops. There is no click on installation — you simply drop the dowel in from
the front (head toward the cover end) and it seats when the pilot enters the
back-wall bore. The cover snapping on completes the capture.

**Assembly order is load-bearing: the axle dowels must be installed BEFORE
the cover is snapped on.** Without the cover, the head is uncapped and the
dowel can lift straight back out.

### Finger snap pins — `pin_C_R`, `pin_D_R`, `pin_C_L`, `pin_D_L` (4 pins)

Barbed split-tip pins. Head flange is at the +Z (top, above-finger) end;
the far end is a **split barbed tip** sawn by a printed `+` cross-slot into
four springy jaws with a tapered lead-in and a locking lip.

**Retention is geometric counterbore capture.** A rigid confining pocket
(counterbore) is cut into the exit (bottom) face of each receiving eye:
the crank eye for C_R/C_L, the follower eye for D_R/D_L. When the locking
lip clears the bore and enters the pocket, the **rigid pocket shoulder takes
the axial pull-out load**; the pocket wall radially confines the lip so it
cannot creep-relax inward and escape. The lip catches the shoulder even at
worst-case FDM tolerance — this is a **positive, geometric lock**, not just
elastic preload.

To install: push the barb end straight down through the finger eye and the
link eye beneath it. The tapered cone cams the four jaws inward; when the
lip drops into the counterbore pocket you feel the **click**. The head flange
caps on top of the finger and cannot pull through.

To remove (tool-free): **pinch the four split barb jaws inward** with
fingernails — compress the cross to below bore diameter — and push/pull the
pin straight out. Pinch, do not pry; the jaws survive many cycles undamaged.

---

## Assembly sequence

### Step 1 — Print prep and snap test

1. Confirm all parts are in the correct material: enclosure, cover, arms,
   followers, and `input_pinion_shaft` in **PA12-GF** (or PETG-HF for test);
   **finger snap pins (C/D ×4) in PETG-HF**; axle dowels (A_R/A_L/B_R/B_L ×4)
   in PA12-GF; fingers in **ether-based TPU ~95A**. Never PLA; never TPU for
   pins (see `UNDERWATER.md`).
2. **Deburr every pivot bore** — A_R, A_L, B_R, B_L back-wall sockets, the
   four C/D finger mount holes, the cover boss bores, and the two journal bores
   in the bottom wall — with a hand-spun countersink or deburring blade. Knock
   the first-layer elephant-foot lip off each bore mouth so pins enter square.
3. **Clean the gear flanks** on `drive_arm_R` and `drive_arm_L`: knock down
   layer ridges and seam witness on the teeth.
4. **Fit-test one finger snap pin** against a scrap counterbored bore coupon
   (per `PRINTING.md` "Fit tuning"). Push it through; you must hear/feel the
   **click** as the lip drops into the counterbore pocket, and the head should
   be captive. Pinch and remove. Tune before printing all seven.
5. **Dry-snap the front cover once:** push it straight onto the bare enclosure
   until all **4 cantilever clips click** into their side-wall windows, then
   flex the four hooks outward and lift the cover off. Confirms clip geometry
   before you trap the mechanism.

---

### Step 2 — Mesh the two drive arms with correct gear timing

This is the one step requiring care. The two 16-tooth sector gears must
**interleave with a half-tooth offset** so both jaws move symmetrically.

1. Hold the pair at the **closed pose**: `drive_arm_L` crank points up and
   slightly inboard (~102° from +X); `drive_arm_R` is its mirror.
2. Bring the sectors together so their pitch circles touch on the centreline.
   **Before teeth engage, rotate one arm by half a tooth:** 360° ÷ 16 ÷ 2 =
   **11.25°** — so a tooth of one gear drops into the valley of the other
   (teeth interleave, not tip-to-tip).
3. The cranks should now be a true mirror pair. **Check:** at closed, the
   C-pin base gap is ~9.86 mm. If jaws come out lopsided after
   assembly, the mesh is off by one tooth — separate, re-offset 11.25°, re-engage.

---

### Step 3 — Drop the arms and followers into the housing

The enclosure prints **open-front**. The mechanism drops straight in.

1. **Seat `drive_arm_R`:** lower it into the cavity so its A_R axle bore
   rests over the back-wall A_R boss. It is only located, not yet Z-captured.
2. **Seat `drive_arm_L`:** lower it into the cavity so its A_L axle bore
   rests over the back-wall A_L boss. The crown gear face on `drive_arm_L`
   must face the bottom (−Y) toward the input-pinion position. It is only
   located, not yet Z-captured.
3. **Add `follower_R`:** seat one eye over the B_R back-wall boss, the other
   eye aligned with the D_R end of the right crank.
4. **Add `follower_L`:** same on the left — one eye on B_L boss, one on D_L.
5. Recheck that the gear mesh is still correctly interleaved and both arms
   swing freely by hand.

### Step 3a — Install the input drive shaft

1. **Drop `input_pinion_shaft` into the bottom-wall journal bores:** lower the
   shaft down through the upper journal boss bore (2 mm bearing, in the cavity)
   and into the lower journal bore in the bottom wall (7 mm bearing). The
   pinion end enters the cavity first and meshes the crown gear on `drive_arm_L`
   at the −Y (bottom) azimuth.
2. **Confirm collar seating:** the integral collar (OD 5.8 mm) is larger than
   the bore and will seat in the housing pocket between the two bore mouths —
   this is the axial capture. It should drop in freely and sit in the pocket
   with a small amount of axial play (~0.25 mm each side). No click; no barb.
   The collar cannot pull out (−Y) or push in (+Y) past either bore shoulder.
3. The D-profile coupler end exits below the housing bottom, below the mounting
   flange. The shaft runs in flooded journal bores (no bushing needed); confirm
   it turns freely.
4. **Verify the crown/pinion mesh:** rotate the shaft slightly by hand. Both
   drive arms should move, confirming the crown/pinion stage is engaged.

---

### Step 4 — Install the 4 axle dowels (BEFORE the cover)

> **Critical order:** axle dowels must go in now, before the cover is snapped
> on. The cover-boss face is their +Z stop — without the cover they are
> uncaptured and can lift out.

For each of **A_R**, **A_L**, **B_R**, **B_L**:

1. Orient the dowel head-up (head flange toward the open front / cover side).
2. Drop it **tip-first down through the front-open cavity** through the
   arm/follower bore and into the back-wall socket. The pilot tip self-centres
   in the narrow flood hole; the flat shank shoulder seats on the rigid bore
   step (−Z stop).
3. The head flange sits near the cavity top, waiting for the cover boss.
4. The arm/follower must still **pivot freely** on its dowel.

Repeat all four. **`pin_A_L`** is the axle dowel for `drive_arm_L` — install it
the same way as `pin_A_R`. The left arm no longer has an integral shaft; it rides
on its axle dowel like the right arm.

---

### Step 5 — Snap the front cover on (captures the axle dowels)

1. Align `front_cover` over the open front, the 4 hook clips facing the four
   side-wall windows (2 per long side).
2. **Push it straight on** until all **4 cantilever clips click** into their
   windows. The cover's inner-face bosses now **cap all 4 axle-dowel heads** —
   each dowel is sandwiched between the back-wall bore step and the cover boss
   and **cannot fall out in either direction**. No tools, no fasteners.
3. Verify: tug each axle-dowel head — it should have essentially no axial slop
   and refuse to pull out.

To remove later: flex all 4 hooks **outward** through the windows and lift the
cover straight off; the axle dowels can then lift out the front.

---

### Step 6 — Mount the Fin Ray fingers

1. Place **`finger_R`** so its bracket eyes align with **C_R** (crank eye)
   and **D_R** (follower eye). Place **`finger_L`** on **C_L / D_L**. The
   fingers are a chiral pair — the ridged contact face must face **inboard**,
   toward the centreline.
2. For each of C_R, D_R, C_L, D_L: push a **finger snap pin straight down
   from above the finger**, head flange on top. The barb traverses the finger
   eye and the link eye beneath it, then the locking lip drops into the
   **counterbore pocket** cut into the exit face of that eye with a **click**.
   The head caps flush on top of the finger; the lip is now held by a rigid
   annular shoulder — geometric capture.
3. Tug each pin head — it must hold. These 4 pins are the visible ones
   standing proud above the housing.

---

### Step 7 — Snap the front cover on (if not already done at Step 5)

The cover can be installed either at Step 5 (before fingers) or after Step 6
(after fingers), since the C/D pivot points are on the arms/followers above
the enclosure top, not through the cover plate. The task-standard order is:
**cover at Step 5, fingers at Step 6.** Either order is geometrically valid.

---

### Step 8 — Couple a waterproof actuator to the bottom D-shaft

1. Mate your **waterproof servo / actuator coupling** onto the **bottom
   D-profile coupler** on `input_pinion_shaft` (the D exits below the housing
   bottom flange — actuator couples from below). Coupler dimensions: radius
   5.0 mm, D-flat depth 1.4 mm, length 12 mm. The milled flat keys the
   coupling so it cannot slip.
2. Use an IP68/submersible servo, a potted hobby servo, or a sealed/oil-filled
   actuator with a pressure compensator for deeper work. See `UNDERWATER.md`
   §6. The actuator carries the **only** waterproofing burden in the system —
   the gripper itself is passive and fully flooded.

---

### Step 9 — Mount via the bottom flange

1. The **bottom flange** carries **5 × M4 clearance holes** positioned around
   the shaft exit. Attach the gripper to your robot arm or mount with M4 bolts
   through these holes. The actuator couples below the flange to the D-shaft.
2. **Galvanic isolation:** if your robot arm is metal, use **nylon or PTFE
   shoulder bushings + isolating washers** on every flange bolt so no
   metal-to-metal contact path exists between the gripper body and the arm
   (see `UNDERWATER.md` §5). The gripper itself contributes no metal — the
   isolation lives at this interface.

---

## Function test (in air)

1. Rotate the input shaft — turn the actuator or the bottom D-coupler directly.
2. **Both jaws must open and close symmetrically**, splaying ~18° outward as
   they open (funnel mouth) and coming nearly together at closed.
3. Check the mesh: smooth, low-backlash engagement through the full travel,
   no tight spots or skipped teeth. If one jaw leads the other, the gears are
   off by one tooth — return to Step 2 and re-time with the 11.25° half-tooth
   offset.
4. Confirm all pivots move freely. Press a finger's contact face and confirm
   the Fin Ray tip curls toward/around the load.

---

## Flood check (before it gets wet)

The gripper is designed to **flood completely** — there are no sealed air
pockets inside. Trapped air would add buoyancy and create pressure differential
on the walls, so verifying full flooding matters.

1. **Drain/flood holes clear:** confirm the 5 bottom-face holes, the 4 low
   side-wall holes, the 4 snap-clip windows, and the 2 front-cover vent holes
   are all open and unobstructed (not bridged shut by print artefacts).
2. **Cover vent holes:** the front cover carries **2 × Ø1.8 mm vent holes**
   at (±34, +12) mm, positioned over the open cavity toward the finger side.
   These let trapped air escape when the gripper is oriented front-up. Confirm
   both holes are clear through the cover plate.
3. **Submerge and watch bubbles:** lower the gripper **mouth-down** first,
   then **mouth-up** — bubbles must escape both ways and the cavity must fully
   flood. Cycle the jaws open↔closed underwater to flush any last trapped air.
4. Once it floods and drains freely in any orientation with no retained air
   bubble, the flooded build is ready for use.

After every salt dive: **rinse with fresh water**, cycle the jaws to flush
grit, dry, and inspect.

---

## Tool-free disassembly (full reverse of assembly)

Reverse in order — no tools:

1. **Finger snap pins (C/D ×4):** pinch the four split barb jaws **below the
   link eye** (inward toward the pin axis), push each pin up and out, lift the
   fingers off. Pinch, do not pry — the jaws survive many cycles.
2. **Front cover:** flex all **4 cantilever hooks outward** through the
   side-wall windows simultaneously and lift the cover straight off.
3. **Axle dowels (A_R, B_R, B_L ×3):** with the cover off, the head is
   uncapped. Lift each dowel straight up out of the front-open cavity. There
   is no barb to compress — it slides free.
4. **Input drive:** pull the `input_pinion_shaft` straight up out of the bottom
   journal bores.
5. **Arms and followers:** lift `follower_R`, `follower_L`, `drive_arm_R`, and
   `drive_arm_L` out of the cavity. All four arms ride on axle dowels; none
   have integral shafts.

Every pin is reusable. The axle dowels lift out freely; the finger snap pins
are pinched and pulled — neither requires force after releasing its retainer.

---

## Print → assemble quick-start

1. **Print:** `plate_rigid_1.stl` (PETG/ASA, 0.12–0.20 mm, no supports) and
   `plate_tpu_1.stl` (TPU 95A, 0.15–0.20 mm, slow, no supports). See
   `PRINTING.md` and `PRINT_PLATES.md` for full settings.
2. **Post-process:** deburr all pivot bores; clean gear flanks; clear the
   `+` slot on each finger snap pin; test-flex each barb and clip.
3. **Fit-test one finger pin** + a scrap counterbored coupon; verify the click
   and that the lip seats in the pocket before committing the remaining 6 pins.
4. **Assemble in order:** mesh arms → drop into housing → drop `input_pinion_shaft`
   into bottom journals → install 4 axle dowels → snap on front cover → place
   fingers → snap in 4 finger pins.
5. **Function check:** rotate the bottom D-shaft; both jaws must open/close symmetrically.
6. **Flood check:** submerge, watch bubbles clear, cycle jaws wet.
7. **Read `UNDERWATER.md`** for material prep and seawater guidance before the
   first dive.

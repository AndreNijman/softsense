# Assembly instructions — fully 3D-printed underwater gripper

> ## NO PURCHASED HARDWARE. ZERO FASTENERS. ONE TOOL: a soldering iron.
> Every part of this gripper — including all 8 pivot pins, their 8 retaining
> caps, and the front cover — is **3D-printed**. No screws, no nuts, no metal
> dowels, no bearings, no bushings, no glue, no Allen keys. The **only** tool
> the build needs is a **soldering iron**: each pivot pin is retained by
> melting a separate printed cap onto its protruding stud (a heat-stake /
> melt-rivet). Everything else slides or snaps together by hand.

How to assemble the gripper entirely from printed parts (`gripper.py`) into a
working, single-DOF, **flooded underwater** gripper. Turn one input shaft and
**both jaws open/close symmetrically, splaying outward** as they open.

Read `PRINTING.md` for material, orientation, and post-processing first. Read
`UNDERWATER.md` for seawater material chemistry. This document assumes every
part is printed, deburred, and fit-tested.

Part names match `gripper.py` `gen_step()`: `enclosure`, `front_cover`,
`drive_arm_R`, `drive_arm_L`, `input_pinion_shaft`, `follower_R`, `follower_L`,
`finger_R`, `finger_L`. Pin SKUs: `melt_pin_axle` (×4), `melt_pin_finger_C`
(×2, the LONG crank-layer pin), `melt_pin_finger_D` (×2, the SHORT
follower-layer pin), and `melt_cap` (×8, one per pin). Pivots: **A_R, A_L**
(drive-arm axles), **B_R / B_L** (follower axles), **C_R, D_R, C_L, D_L**
(finger pins). The drive input enters via a right-angle crown + pinion stage
and exits the **housing bottom** — that bottom shaft-exit flange is the
mounting face, so the **back wall stays free and accessible** for melting the
axle caps from outside.

---

## Part inventory (25 printed parts, 0 hardware)

| Part label | Qty | Role |
|---|---|---|
| `enclosure` | 1 | Flooded gearbox housing, open front, bottom mounting flange |
| `front_cover` | 1 | Snap-on cover with 4 integral cantilever clips |
| `drive_arm_R` | 1 | Right gear sector + crank arm (rides on axle pin A_R) |
| `drive_arm_L` | 1 | Left gear sector + crank arm + **integral crown gear** (rides on axle pin A_L) |
| `input_pinion_shaft` | 1 | Vertical input shaft: pinion + continuous journal + bottom shoulder + D-coupler |
| `follower_R` | 1 | Right B→D link bar |
| `follower_L` | 1 | Left B→D link bar |
| `finger_R` | 1 | Right Fin Ray compliant jaw (TPU) |
| `finger_L` | 1 | Left Fin Ray compliant jaw (TPU) |
| `melt_pin_axle` (A_R, A_L, B_R, B_L) | 4 | **Heat-stake axle pin** — journals an arm/follower; melt-stud threads the back-wall flood hole and is capped outside the back wall |
| `melt_pin_finger_C` (C_R, C_L) | 2 | **Heat-stake finger pin, LONG** — reaches the crank layer; capped at the crank-eye bottom on the bench |
| `melt_pin_finger_D` (D_R, D_L) | 2 | **Heat-stake finger pin, SHORT** — reaches the follower layer; capped at the follower-eye bottom on the bench |
| `melt_cap` | 8 | Separate retaining cap, one per pin — slips over the pin's melt-stud and is fused with a soldering iron into a thermal-rivet head wider than the bore |
| **Total** | **25** | **Zero purchased hardware** |

The finger pins are **two SKUs** because C and D sit at different Z depths: C
reaches the crank layer (the longer `melt_pin_finger_C`), D only reaches the
follower layer (the shorter `melt_pin_finger_D`). A single length would leave
half the finger pins unseated.

---

## How the pins work (read this before assembling)

All 8 pivot pins are **plain printed PETG-HF journal pins**, each retained by
a **separate printed PETG-HF cap** (`melt_cap`, ×8): you slip the cap over the
pin's protruding **melt-stud** and fuse it with a **soldering iron** into a
thermal-rivet head wider than the bore. Retention is **geometric** — a formed
head larger than the hole — **not** an elastic snap (nothing flexes, so
nothing breaks) and **not** a press fit (nothing relies on friction, so
nothing slides out). The 8 pins split into two families by *where* the cap is
melted, which drives the assembly order. Do not confuse them.

### Axle pins — `melt_pin_axle`: A_R, A_L, B_R, B_L (4 pins)

Plain headed journal pins. The **head seats just under the cover boss** (its
+Z stop); the **shank journals** the gear or follower eye and **bottoms on the
back-bore step** (its −Z stop); a **melt-stud** threads the existing back-wall
flood hole and **protrudes past the EXTERIOR back face**.

Retention: insert each axle pin from the open front (mechanism already in),
then flip the housing and **melt a `melt_cap` onto each stud from OUTSIDE the
back wall**. The cap fuses into a rivet head wider than the flood hole, so the
pin is **riveted to the back wall = a fixed pivot post**. There is no sandwich
relying on the cover; the formed head is the +Z-side capture against the back
wall. (The back wall is reachable because the mount is the bottom shaft-exit
flange, not the back face.)

**Axial capture of each rotating element** (so an arm cannot slide along the pin):
every element is trapped between a back-boss **down thrust shoulder** and the pin's
**locating collar** above it (0.12 mm running gap each way). The crank/gear sits in
the low Z layer and lands on the plain back-boss; the **follower sits a layer higher**,
so its pivots (B_R, B_L) carry a **taller D-shaped boss** — full thrust shoulder on the
**outboard** half, cut away on the inboard half where the crank arm sweeps past the
follower pivot at full open. This trapped the old ~5.6 mm follower axial float down to
0.24 mm without fouling the crank.

### Finger pins — `melt_pin_finger_C` (C_R, C_L) + `melt_pin_finger_D` (D_R, D_L) (4 pins, 2 SKUs)

Plain stepped journal pins. From the top down: the **head seats on the finger
TOP**; a **fat neck** is the anti-wobble running bearing in the **fixed 2.6 mm
TPU finger bore**; a **slim land** journals the rigid arm or follower eye; and
the **melt-stud protrudes past the arm/follower-eye BOTTOM (exit) face**, where
the cap is melted. C reaches the crank layer (long `melt_pin_finger_C`); D
reaches the follower layer (short `melt_pin_finger_D`).

**Anti-wobble journal boss (2026-06 redesign):** each rigid C/D eye now grows a
**journal boss upward** to just under the finger, so the slim land runs
**continuously from the cap-recess floor up to the finger bottom** (L/D ≈ 3.6 at
C) instead of journaling a short eye then flag-poling across an empty gap — this
kills the finger's out-of-plane wobble. The **boss top is the under-finger thrust
shoulder**: the finger seats on it with a 0.12 mm running gap (head above + shoulder
below), so the old ~1 mm finger axial float collapses to a running fit and the finger
sits square on **both** bosses (they end at the same Z). The neck→land step floats
just above the shoulder, so there is no rotating thrust face to drag.

Because the cap face is **buried mid-cavity** once the mechanism is in the
housing, the finger pins are staked as a **bench sub-assembly**: build
{finger + crank arm + follower + the two C/D pins + 2 caps}, melt the 2 caps at
the arm/follower-eye bottoms while both pin ends are still reachable on the
bench, **then** drop that finished sub-assembly into the open-front housing.

**Assembly order is load-bearing:** the finger sub-assemblies must be staked on
the bench *before* they go into the housing, and the axle pins are capped from
outside the back wall *after* the mechanism is in. There is no tool-free pinch
release — a melted cap is permanent; to service a joint you slice the cap off
and melt on a fresh one.

---

## Assembly sequence

### Step 1 — Print prep and fit test

1. Confirm all parts are in the correct material: enclosure, cover, arms,
   followers, and `input_pinion_shaft` in **PA12-GF** (or PETG-HF for test);
   **all 8 pivot pins (`melt_pin_axle` ×4, `melt_pin_finger_C` ×2,
   `melt_pin_finger_D` ×2) and the 8 `melt_cap` retainers in PETG-HF**; fingers
   in **ether-based TPU ~95A**. Never PLA; never TPU for pins (see
   `UNDERWATER.md`). Have a **soldering iron** ready — it is the only tool the
   build needs (for melting the 8 caps).
2. **Deburr every pivot bore** — the 4 back-wall axle sockets / flood holes,
   the four C/D finger mount holes, the cover boss bores, and the two journal
   bores in the bottom wall — with a hand-spun countersink or deburring blade.
   Knock the first-layer elephant-foot lip off each bore mouth so pins enter
   square.
3. **Clean the gear flanks** on `drive_arm_R` and `drive_arm_L`: knock down
   layer ridges and seam witness on the teeth.
4. **Fit-test one melt pin + cap** against a scrap bore coupon (per
   `PRINTING.md` "Fit tuning"). Slip the pin through, slip a `melt_cap` over the
   protruding stud, and touch the soldering iron to the stud until it mushrooms
   the cap into a head **wider than the bore**. Confirm the formed head holds
   and the pin runs free in the bore. Tune the stud/cap fit before staking the
   real pins.
5. **Dry-snap the front cover once:** push it straight onto the bare enclosure
   until all **4 cantilever clips click** into their side-wall windows, then
   flex the four hooks outward and lift the cover off. Confirms clip geometry
   before you trap the mechanism.

---

### Step 2 — Bench-stake the two finger sub-assemblies

The finger pins are capped at the arm/follower-eye **bottom**, which is buried
mid-cavity once the mechanism is in the housing — so you cannot reach them
later. **Stake each finger as a bench sub-assembly first**, while both pin ends
are still reachable. Build **two** of these (one per side, a chiral pair).

For each side {`finger` + crank `drive_arm` + `follower`}:

1. Lay the crank arm and follower so the finger's two bracket eyes line up over
   the **C eye** (crank) and **D eye** (follower). The finger's ridged contact
   face must face **inboard** (toward the centreline) in the finished gripper —
   build the chiral pair accordingly (`finger_R` on the right arm/follower,
   `finger_L` on the left).
2. Drop a `melt_pin_finger_C` (the **LONG** pin) down through the finger eye at
   **C** and a `melt_pin_finger_D` (the **SHORT** pin) at **D**, head on the
   finger top. The fat neck runs in the fixed 2.6 mm TPU finger bore; the slim
   land journals the arm/follower eye; the melt-stud pokes past the eye
   **bottom**.
3. Slip a `melt_cap` over each protruding stud and **melt it with the soldering
   iron** into a head wider than the bore. Two caps per side, **4 caps total
   across both sub-assemblies**.
4. Check both pivots run free — the finger should pivot on each pin without
   wobble, and neither pin can pull out (the formed head holds).

You now have two finished {finger + arm + follower} sub-assemblies ready to
drop into the housing.

---

### Step 3 — Mesh and drop the two sub-assemblies into the housing

The enclosure prints **open-front**. The two drive arms must **interleave with
a half-tooth offset** so both jaws move symmetrically — get the timing right as
they go in.

1. Hold the two sub-assemblies at the **closed pose**: `drive_arm_L` crank
   points up and slightly inboard (~102° from +X); `drive_arm_R` is its mirror.
2. Bring the two sector gears together so their pitch circles touch on the
   centreline. **Before teeth engage, rotate one arm by half a tooth:**
   360° ÷ 16 ÷ 2 = **11.25°** — so a tooth of one gear drops into the valley of
   the other (teeth interleave, not tip-to-tip).
3. **Seat the right sub-assembly:** lower it so the `drive_arm_R` A_R bore and
   the `follower_R` B_R bore rest over their back-wall bosses. **Seat the left
   sub-assembly:** the `drive_arm_L` A_L bore and `follower_L` B_L bore over
   their bosses; the crown gear face on `drive_arm_L` must face the bottom (−Y)
   toward the input-pinion position. The arms are only located, not yet
   Z-captured (the axle pins do that in Step 4).
4. The cranks should now be a true mirror pair. **Check:** at closed, the
   C-pin base gap is ~9.86 mm. If jaws come out lopsided, the mesh is off by one
   tooth — lift out, re-offset 11.25°, re-seat.
5. Recheck both arms swing freely by hand and the gear mesh stays interleaved.

### Step 3a — Install the input drive shaft

1. **Push `input_pinion_shaft` UP into the journal from below:** the shaft is a
   plain cylinder (≤4.0 mm) below the pinion, so it feeds
   pinion-first up through the lower journal bore and the upper boss bore (one
   continuous 4.3 mm bearing). The pinion (Ø7.44 mm < the bore) passes through
   and enters the cavity, meshing the crown gear on `drive_arm_L` at the −Y
   azimuth. Push until the bottom shoulder lands on the flange.
2. **Confirm the +Y stop:** the bottom shoulder (OD 5.8 mm > bore) bottoms on the
   flange outer face — that is the push-in stop. (There is no mid-shaft collar;
   the older collar-in-pocket design was un-installable and was removed.) The
   shaft runs in flooded journal bores (no bushing) — confirm it turns freely.
3. The D-profile coupler end exits below the housing bottom, below the mounting
   flange. The shaft runs in flooded journal bores (no bushing needed); confirm
   it turns freely.
4. **Verify the crown/pinion mesh:** rotate the shaft slightly by hand. Both
   drive arms should move, confirming the crown/pinion stage is engaged. (Note:
   the crown/pinion faces were widened in the Phase-4 strengthening —
   `PINION_T 8 mm`, `CROWN_TOOTH_H 3 mm` — but the mesh and assembly are unchanged;
   `motor/DRIVETRAIN.md`.)
5. **Couple the actuator:** fit the printed adapter horn from the selected
   actuator (primary: DYNAMIXEL XW540-T260 smart serial servo; or the magnetic-
   coupling dry-pod for >30 m) onto the D-coupler. **Set the actuator's firmware
   current limit to the gear ceiling `T_safe`** before driving — the printed
   crown/pinion is the structural limit and the current limit is its protection.
   The same current telemetry is the gripper's grip-force sensor. See
   `motor/SELECTION.md`, `motor/SENSING.md`, `motor/ELECTRICAL.md`.

---

### Step 4 — Insert the 4 axle pins from the front

For each of **A_R**, **A_L**, **B_R**, **B_L**:

1. Orient the `melt_pin_axle` head-up (head toward the open front / cover side,
   melt-stud toward the back wall).
2. Drop it **straight down through the front-open cavity**, through the
   arm/follower bore and into the back-wall socket. The shank journals the eye
   and **bottoms on the back-bore step** (−Z stop); the **melt-stud threads the
   back-wall flood hole and pokes out past the exterior back face**.
3. The head sits just under where the cover boss will land; the arm/follower
   must **pivot freely** on the pin.

Repeat all four. **`pin_A_L`** is the axle pin for `drive_arm_L` — install it
the same way as `pin_A_R`. The left arm no longer has an integral shaft; it
rides on its axle pin like the right arm. After all four are in, the four
melt-studs protrude from the **outside of the back wall**.

---

### Step 5 — Flip the housing and melt the 4 back caps

> **The back wall must be accessible for this step.** It is *not* the mounting
> face — the mount is the bottom shaft-exit flange (Step 9) — so the back face
> is free. Keep it clear of any fixture while you stake the caps.

1. **Flip the housing** so the exterior back wall faces up and the four axle
   melt-studs point at you.
2. Slip a `melt_cap` over each stud and **touch the soldering iron to it** until
   it fuses into a **thermal-rivet head wider than the flood hole**. Four caps,
   one per stud. Each axle pin is now **riveted to the back wall = a fixed pivot
   post** — captured geometrically, not by the cover and not by friction.
3. Verify: tug each axle pin from the front — it must have essentially no axial
   slop and refuse to pull out. The arm/follower must still pivot freely on it.

This is the **fourth through eighth caps**: 4 finger caps were melted on the
bench (Step 2), 4 axle caps here — **8 caps melted in total**.

---

### Step 6 — Snap the front cover on

The axle pins are already captured by their melted back caps (Step 5), so the
cover is now purely a closure, not a pin retainer.

1. Align `front_cover` over the open front, the 4 hook clips facing the four
   side-wall windows (2 per long side).
2. **Push it straight on** until all **4 cantilever clips click** into their
   windows (the click is a little softer now that the tabs are slimmer, but the
   geometric hook capture — not the spring force — holds the cover). No tools,
   no fasteners.
3. Verify the cover sits flush and the mechanism still turns freely.

To remove later: flex all 4 hooks **outward** through the windows and lift the
cover straight off. The pins stay riveted in place — removing the cover does
not free them (slice a cap off only if you need to service that joint).

---

### Step 7 — Couple a waterproof actuator to the bottom D-shaft

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

### Step 8 — Mount via the bottom flange

1. The **bottom flange** carries **4 × M4 clearance holes** positioned around
   the shaft exit. Attach the gripper to your robot arm or mount with M4 bolts
   through these holes. The actuator couples below the flange to the D-shaft.
   (This bottom flange is the mounting face — which is why the back wall stayed
   free for the axle-cap melt in Step 5.)
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
   off by one tooth — return to Step 3 and re-time with the 11.25° half-tooth
   offset.
4. Confirm all pivots move freely. Press a finger's contact face and confirm
   the Fin Ray tip curls toward/around the load.

---

## Flood check (before it gets wet)

The gripper is designed to **flood completely** — there are no sealed air
pockets inside. Trapped air would add buoyancy and create pressure differential
on the walls, so verifying full flooding matters.

1. **Drain/flood holes clear:** confirm the 8 bottom-face drain holes, the 4 low
   side-wall holes, the 4 snap-clip windows, and the 3 front-cover vent holes
   are all open and unobstructed (not bridged shut by print artefacts).
2. **Cover vent holes:** the front cover carries **3 × Ø1.8 mm vent holes**
   in a symmetric row at (−34 / 0 / +34, +12) mm, positioned over the open cavity
   toward the finger side. These let trapped air escape when the gripper is
   oriented front-up. Confirm all three holes are clear through the cover plate.
3. **Submerge and watch bubbles:** lower the gripper **mouth-down** first,
   then **mouth-up** — bubbles must escape both ways and the cavity must fully
   flood. Cycle the jaws open↔closed underwater to flush any last trapped air.
4. Once it floods and drains freely in any orientation with no retained air
   bubble, the flooded build is ready for use.

After every salt dive: **rinse with fresh water**, cycle the jaws to flush
grit, dry, and inspect.

---

## Disassembly (the melt caps are permanent)

A heat-staked cap is a formed rivet head — there is no pinch release. To open a
joint you **slice its `melt_cap` off** (flush cutter or knife at the cap root),
then melt a **fresh** cap on at reassembly. Caps are cheap to reprint; the pins
themselves are reusable. Reverse in order:

1. **Front cover:** flex all **4 cantilever hooks outward** through the
   side-wall windows simultaneously and lift the cover straight off. (The pins
   are *not* held by the cover, so this alone frees nothing.)
2. **Axle pins (A_R, A_L, B_R, B_L ×4):** slice the **4 back caps** off the
   melt-studs at the exterior back wall, then lift each pin straight up out of
   the front-open cavity.
3. **Input drive:** with the actuator detached, pull the `input_pinion_shaft`
   straight DOWN and out the bottom of the journal (the bottom shoulder won't
   pass the bore upward, so it leaves the way it went in — downward).
4. **Arms and finger sub-assemblies:** lift the two {finger + arm + follower}
   sub-assemblies out of the cavity. All four arms ride on axle pins; none have
   integral shafts.
5. **Finger pins (C/D ×4), only if servicing a finger:** slice the cap off the
   arm/follower-eye bottom of each finger pin and push the pin out to separate
   the finger from its arm/follower. Otherwise leave each finger sub-assembly
   intact and reuse it whole.

Each pin is reusable; every cap is single-use (slice off, reprint, re-melt).

---

## Print → assemble quick-start

1. **Print:** `plate_rigid_1.stl` (PETG/ASA, 0.12–0.20 mm, no supports) and
   `plate_tpu_1.stl` (TPU 95A, 0.15–0.20 mm, slow, no supports). See
   `PRINTING.md` and `PRINT_PLATES.md` for full settings.
2. **Post-process:** deburr all pivot bores; clean gear flanks; test-flex each
   cover clip. Have a **soldering iron** ready for the 8 melt caps.
3. **Fit-test one melt pin + cap** on a scrap bore coupon; melt the cap and
   confirm the formed head clears the bore and holds before staking the real
   pins.
4. **Assemble in order:** bench-stake the 2 finger sub-assemblies (finger + arm
   + follower + 2 pins, melt 2 caps each) → mesh + drop both sub-assemblies into
   the housing → push `input_pinion_shaft` UP into the journal from below
   (pinion-first) → insert the 4 axle pins from the front → flip and melt a cap
   onto each of the 4 back studs → snap on the front cover → bolt on the
   actuator. (8 caps melted in total.)
5. **Function check:** rotate the bottom D-shaft; both jaws must open/close symmetrically.
6. **Flood check:** submerge, watch bubbles clear, cycle jaws wet.
7. **Read `UNDERWATER.md`** for material prep and seawater guidance before the
   first dive.

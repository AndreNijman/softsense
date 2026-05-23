# Bill of Materials — Underwater geared four-bar / Fin Ray gripper (FULLY 3D-PRINTED)

Production BOM for the gripper defined in `gripper.py` (geared four-bar, single
input shaft, compliant TPU Fin Ray fingers, **flooded** housing for underwater
use). This is the *what-to-print* list — and for this revision that is the
**entire** list. See `PRINTING.md` for how to orient and slice each part,
`UNDERWATER.md` for material chemistry in seawater, and `ASSEMBLY.md` for the
tool-free snap-together sequence.

> # ⚓ ZERO bought hardware. No screws, no nuts, no bolts, no bushings.
> **Every part is 3D-printed and snaps together by hand — tool-free assembly.**
> The pivot pins are printed push-to-snap pins (flange head + split barbed tip).
> The front cover is held by 4 integral printed cantilever snap clips. The input
> shaft turns in a bare printed bore — no bushing. The **only** non-printed item
> in the whole system is the user's own waterproof servo/actuator, and that is
> the user's choice, outside this BOM (it just plugs onto the integral D-shaft).

Headline build target: **flooded, all-polymer, fastener-free.** There is nothing
to seal, nothing to buy, and nothing metal anywhere in the gripper.

---

## 1. Printed parts (the complete BOM)

Everything below is emitted by `gripper.gen_step()`. The enclosure floods through
its drain holes; the mechanism drops in; the printed snap pins push through the
pivots; the cover snaps on. Done.

| Part | Qty | Material (seawater pick) | Rough filament* | Suggested colour | Notes |
|---|---|---|---|---|---|
| `enclosure` (flooded housing) | 1 | **PETG** (default) — or **ASA / glass-filled nylon** for deep/long dives | ~80–110 g | Dark slate / graphite | Hollow gearbox body, back flange (4 mounting holes), top link slots, A_L shaft bore + integral bushing-less seat, captured-axle bosses, drain/flood holes, and the **snap-clip catch windows** in the long side walls. **Never PLA** (hydrolyzes underwater). |
| `front_cover` (snap-on, **4 integral snap clips**) | 1 | Same as enclosure (PETG / ASA / nylon) | ~20–30 g | Slate (slightly lighter than body) | Closes the open front and supports the far axle ends. **Carries 4 integral cantilever snap clips** (2 per long side) that hook into the body's side-wall windows — **no screws**. Push on to click home; flex the 4 hooks outward to release. The clips are part of this print, not separate items. |
| `drive_arm_R` (gear sector + crank arm, clearance-bored) | 1 | **PETG** (or ASA / glass-filled nylon) | ~12–18 g | Steel grey | Rides on the right axle snap-pin at A_R. Flat gear+arm plate, prints face-down. |
| `drive_arm_L` (gear sector + crank arm + **integral input shaft + rear D-coupler**) | 1 | **PETG** (or ASA / glass-filled nylon) | ~14–20 g | Steel grey | Carries all drive torque through its integral printed shaft; its shaft **is** the left axle (no A_L pin). Rear D-profile coupler accepts the user's servo. Reorient for printing (shaft sticks out along Z). |
| `follower` (B→D link bar) | 2 | **PETG** (or ASA / glass-filled nylon) | ~6–9 g each | Steel grey | Symmetric link bar; left and right are the **same part**. Flat plate, prints face-down. |
| `finger_R` / `finger_L` (Fin Ray compliant jaws) | 2 (chiral pair) | **Ether-based TPU ~95A** (e.g. NinjaFlex / suitable BASF grade) — **not** ester-based | ~25–35 g each | Matte black | Mirror images (ribs all slant one way per finger), so both are printed. Compliance is the working principle — these must flex. |
| `snap_pin_axle` (internal pivot pin, head-at-back) | 3 | **PETG** | ~1–2 g each | Steel grey / bright | Push-to-snap pins for the 3 captured pivots **A_R, B_R, B_L**. Flange head seats at the back wall; split barbed tip springs out past the cover boss to lock. |
| `snap_pin_finger` (finger pivot pin, head-at-front) | 4 | **PETG** | ~1–2 g each | Steel grey / bright | Push-to-snap pins for the 4 finger pivots **C_R, D_R, C_L, D_L** that couple each finger to its coupler CD. Flange head caps above the finger; barbed tip locks below. |

\* Rough single-piece estimates at the recommended walls/infill in `PRINTING.md`;
calibrate against your slicer and material. **Total filament: roughly ~140–200 g
rigid (PETG/ASA/nylon) + ~50–70 g ether-TPU.** The 7 snap pins together add only
a few grams.

### 1.1 Material rationale (why each polymer, for seawater)

- **Structural parts — enclosure, front_cover, drive_arm_R, drive_arm_L,
  follower → PETG (default), or ASA / glass-filled nylon for the harder cases.**
  PETG has **very low water uptake, does not hydrolyze** (unlike PLA, which
  absorbs water and crumbles), and holds dimension and creeps little under the
  modest sustained loads of a flooded passive gripper. **ASA** adds UV/heat
  stability for surface/topside work; **glass-filled nylon** is the pick for deep
  or long dives where creep under prolonged hydrostatic load and higher torque
  matter — it is tougher and stiffer with still-low water sensitivity. All three
  are inert in seawater and free of any galvanic concern because they are
  polymers. **Never PLA underwater.**

- **Snap pins → PETG (not TPU).** The pins are *pivots* and *snap-retainers*:
  they take repeated side load from the four-bar links and must hold the barb's
  retention preload indefinitely. PETG is semi-flexible enough that the split,
  barbed tip can squeeze going in and spring back to lock, yet **stiff enough not
  to creep**. **TPU is deliberately wrong here:** under sustained side load and
  the barb's standing preload, TPU would slowly creep and **wallow out the bore**,
  the joint going sloppy, and the barb would relax and **lose its snap-lock**.
  PETG keeps the pivot tight and the snap positive over time. (A stiffer ASA or
  nylon pin also works; PETG is the easy default with the right springiness.)

- **Fingers → ether-based TPU ~95A.** The Fin Ray wrap-around grip *is* material
  compliance — the fingers have to flex to conform around an object, so a rigid
  polymer cannot do this job. **Ether-based** TPU resists hydrolysis in sustained
  or warm immersion; **ester-based** TPU hydrolyzes and eventually crumbles
  underwater, so it is excluded. 95A shore balances conformance against grip force.

---

## 2. NO bought hardware — what this revision deleted

**This is a fully 3D-printed, zero-hardware gripper.** There are no screws, no
nuts, no bolts, no washers, and no bushings anywhere in it. Assembly is
**tool-free**: push the printed snap pins through the pivots and snap the cover
on. Disassembly is the same in reverse — flex the cover clips and pull the pins.

This **replaces the obsolete stainless-hardware version**, whose entire metal
hardware list is now gone:

| Obsolete metal item (PREVIOUS version) | Was | Now replaced by |
|---|---|---|
| Pivot screws / dowels (1 drive axle + 2 follower axles + 4 finger pins) | 7 × A4/316 SS | **7 printed push-to-snap pins** (`snap_pin_axle` ×3 + `snap_pin_finger` ×4) |
| Nylon-insert locknuts (one per pivot) | 7 × A4/316 SS | **Eliminated** — the printed pins' barbed split tips self-retain |
| M4 robot-flange bolts | 4 × A4/316 SS | **Out of scope** — flange holes pass through to the user's robot arm (see §4) |
| M3 front-cover screws | 4 × A4/316 SS | **4 integral printed cantilever snap clips** on `front_cover` |
| Input-shaft plain bushing (PTFE/acetal) | 1 | **Eliminated** — the shaft now runs in a bare printed bore (see §3) |
| **Total fixed bought hardware** | **23 pieces** | **0 pieces** |

> Net change: **−23 bought parts → 0.** Everything that used to be stainless is
> now printed and snaps together.

---

## 3. The input shaft runs in a bare printed bore (no bushing)

The input shaft is **integral to `drive_arm_L`** and exits through the back-wall
bore. In this flooded design it turns directly in a **plain printed bore** in the
housing — **there is no separate bushing part.** The bore (`BUSH_BORE_R = 4.4`)
is sized to clear the Ø8 mm printed shaft (`SHAFT_R = 4.0`) with running fit.

**Why a bare printed bore is fine flooded:** there is no pressure differential
and no dry cavity to protect, so nothing needs sealing; the joint runs **wet**,
with water as the coolant and lubricating film. Polymer-on-polymer at this size,
speed, and torque has ample margin for a passive gripper. A sealed bearing would
be **worse** here — it traps grit and seawater in the race where it can't flush,
then corrodes and seizes — and an Oilite bronze bushing would **leach its oil out
when flooded**. A bare printed bore needs no grease and **flushes clean** with a
freshwater rinse. (For high-duty use you may still ream/print the bore slightly
oversize or burnish it; no purchased part is required.)

---

## 4. The only user-supplied item: a waterproof servo / actuator

| Item | Material | Qty | Notes |
|---|---|---|---|
| Waterproof servo / actuator | per your system | 1 (user-supplied) | Drives the rear **D-profile coupler** integral to `drive_arm_L` (`SHAFT_COUPLER_R = 5.0`, `SHAFT_DFLAT = 1.4`). Couples **directly** to the integral D-shaft; the servo horn / coupling is **user-supplied or printed separately** to match the D-flat. Use an **IP68/submersible servo, a potted hobby servo, or a sealed/oil-filled actuator with a pressure compensator** for deeper/longer work. The actuator carries the *only* real waterproofing burden — the gripper itself is passive and flooded. |

**Robot-mount flange (also outside the gripper's hardware scope):** the back
flange keeps its **4 mounting holes** (`BOLT_R = 2.25`, `BOLT_XY`). Whatever
fasteners attach the gripper to your robot arm are the **arm's** hardware, chosen
to suit your arm — they are not part of the gripper. If your arm is metal and you
want galvanic isolation, use nylon/PTFE isolating washers there; the gripper
itself contributes no metal to that joint. This preserves the **zero-hardware**
claim for the gripper proper.

---

## 5. Printed-part count summary

| Group | Count |
|---|---|
| `enclosure` | 1 |
| `front_cover` (with 4 integral snap clips) | 1 |
| `drive_arm_R` | 1 |
| `drive_arm_L` (integral shaft + D-coupler) | 1 |
| `follower` | 2 |
| `finger_R` / `finger_L` (TPU) | 2 |
| `snap_pin_axle` | 3 |
| `snap_pin_finger` | 4 |
| **Total printed parts** | **15** |
| Bought hardware (screws/nuts/bolts/bushings) | **0** |
| User-supplied | waterproof servo + coupling (out of BOM) |

---

## 6. Why fully-printed is corrosion-proof underwater

A gripper made **entirely of polymer** has **no galvanic cell anywhere** — and
galvanic corrosion is the thing that kills mixed-metal hardware in seawater. The
previous version went to great lengths to keep every metal part in one stainless
family (all 316/A4) precisely to avoid an internal galvanic pair; this revision
deletes the problem at the root by deleting the metal. With no screws, nuts,
bolts, pins, or bushings, there is **no dissimilar-metal contact, no less-noble
anode to drive, no pitting, and nothing to rust** — printed structure in PETG /
ASA / nylon (low water uptake, no hydrolysis), printed pivot pins in PETG (stiff
enough not to creep or lose their snap), and printed Fin Ray fingers in
ether-based TPU (does not hydrolyze in sustained immersion). The housing is
**flooded**, so internal and external pressure equalize through the drain holes
and the thin printed wall never sees a differential — nothing to crush. The shaft
turns in a **bare printed bore** that runs wet and flushes clean — no sealed
bearing to trap grit, no Oilite to leach oil, no seal to fail. Net: **nothing to
rust, nothing to seal, nothing to crush, and nothing to buy** — rinse with fresh
water after each salt dive and it stays reliable.

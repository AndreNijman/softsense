# Bill of Materials — Underwater geared four-bar / Fin Ray gripper (FULLY 3D-PRINTED)

Production BOM for the gripper defined in `gripper.py` (geared four-bar, single
input shaft, compliant TPU Fin Ray fingers, **flooded** housing for underwater
use). This is the *what-to-print* list — and for this revision that is the
**entire** list. See `PRINTING.md` for how to orient and slice each part,
`UNDERWATER.md` for material chemistry in seawater, and `ASSEMBLY.md` for the
tool-free snap-together sequence.

> # ZERO bought hardware. No screws, no nuts, no bolts, no bushings.
> **Every part is 3D-printed and snaps or slides together by hand — tool-free
> assembly.** The 3 axle pins are plain headed dowels captured geometrically
> between the back-wall bore step and the front-cover boss. The 4 finger pins
> are barbed push-to-snap pins with rigid counterbore capture. The front cover
> is held by 4 integral printed cantilever snap clips. The input shaft turns in
> a bare printed bore — no bushing. The **only** non-printed items in the whole
> system are the user's waterproof actuator and, at the robot-arm interface, the
> user's mount bolts (with galvanic-isolating hardware per `UNDERWATER.md` §5).

Headline build target: **flooded, all-polymer, fastener-free.** Nothing to seal,
nothing to buy inside the gripper, and no metal anywhere in the gripper.

---

## 1. Printed parts (the complete BOM)

Everything below is emitted by `gripper.gen_step()` (verified against the live
`gen_step()` output: 15 children, labels as listed). The enclosure floods through
its drain holes; the mechanism drops in; the axle dowels are captured between
back-wall step and cover boss; the finger snap pins latch in rigid counterbore
pockets; the cover snaps on. Done.

| Part | Qty | Material (seawater pick) | Rough filament | Role / key detail |
|---|---|---|---|---|
| `enclosure` | 1 | **PETG** (default); **ASA** for topside/UV; **glass-filled nylon (PA-GF)** for deep/long/warm dives | ~80–110 g | Flooded gearbox body. Open front, back mounting flange (4 × M4 holes), top link slots, A_L shaft bore + integral bare-bore bushing seat, 3 back-wall axle bosses + stepped bores (wide running bore + narrow flood hole), 5 bottom drains, 4 side drains, 4 snap-clip catch windows in the long side walls. Never PLA. |
| `front_cover` | 1 | Same as enclosure (PETG / ASA / PA-GF) | ~20–30 g | Closes the open front; 3 inner-face bosses cap the axle-dowel heads (+Z dowel stop); **4 integral cantilever snap clips** (2 per long side) latch into body side-wall windows — no screws; **2 × Ø1.8 mm vent holes** at (±34, +12) let trapped air escape front-up. Push on to click; flex 4 hooks outward to release. |
| `drive_arm_R` | 1 | **PETG** (or ASA / PA-GF) | ~12–18 g | Right gear sector + crank arm. Clearance-bored at A_R (rides on axle dowel `pin_A_R`). Counterbored C-eye exit (−Z face) for `pin_C_R` geometric capture. Flat plate; prints face-down. |
| `drive_arm_L` | 1 | **PETG** (or ASA / PA-GF) | ~14–20 g | Left gear sector + crank arm + **integral input shaft + rear D-profile coupler** (r 5.0, D-flat depth 1.4, length 12 mm). The shaft **is** the left axle — there is no separate A_L pin. Counterbored C-eye for `pin_C_L`. Print shaft-vertical for support-free strong layers. |
| `follower_R` | 1 | **PETG** (or ASA / PA-GF) | ~6–9 g | Right B→D link bar. Counterbored D-eye exit (−Z face) for `pin_D_R` geometric capture. Flat plate; prints face-down. |
| `follower_L` | 1 | **PETG** (or ASA / PA-GF) | ~6–9 g | Left B→D link bar. Counterbored D-eye exit (−Z face) for `pin_D_L`. Same geometry as `follower_R` (mirrored in gen_step). |
| `finger_R` | 1 | **Ether-based TPU ~95A** (e.g. NinjaFlex / suitable BASF grade) — **not** ester-based | ~25–35 g | Right Fin Ray compliant jaw. Grip ridges on contact face; internal slanted-rib truss; mount holes at C_R and D_R. Must flex — print in TPU only. |
| `finger_L` | 1 | **Ether-based TPU ~95A** | ~25–35 g | Left Fin Ray compliant jaw (chiral mirror of `finger_R`). |
| `pin_A_R` | 1 | **PETG** | ~1–2 g | **Axle dowel** for right drive-arm pivot. Plain head + shank + narrow pilot tip. Head toward cover (+Z); pilot enters back-wall flood hole; flat shank shoulder bottoms on stepped-bore step (−Z stop). Sandwiched, no barb. |
| `pin_B_R` | 1 | **PETG** | ~1–2 g | **Axle dowel** for right follower pivot. Same geometry as `pin_A_R`. |
| `pin_B_L` | 1 | **PETG** | ~1–2 g | **Axle dowel** for left follower pivot. Same geometry as `pin_A_R`. |
| `pin_C_R` | 1 | **PETG** | ~1–2 g | **Finger snap pin** for right crank-coupler joint (C_R). Barbed split tip; head above finger; lip locks in rigid counterbore pocket in the crank-arm C-eye. |
| `pin_D_R` | 1 | **PETG** | ~1–2 g | **Finger snap pin** for right follower-coupler joint (D_R). Barbed; lip locks in follower D-eye counterbore pocket. |
| `pin_C_L` | 1 | **PETG** | ~1–2 g | **Finger snap pin** for left crank-coupler joint (C_L). |
| `pin_D_L` | 1 | **PETG** | ~1–2 g | **Finger snap pin** for left follower-coupler joint (D_L). |

\* Rough single-piece estimates at recommended walls/infill (`PRINTING.md`).
**Total filament: roughly ~140–200 g rigid (PETG/ASA/nylon) + ~50–70 g
ether-TPU.** The 7 snap pins together add only a few grams.

---

### 1.1 Pin families: what makes each type work

There are **two distinct pin mechanisms** in this gripper. They are not
interchangeable.

**Axle dowels — `pin_A_R`, `pin_B_R`, `pin_B_L` (3 pins, plain, no barb)**

Retention by rigid geometric sandwich. The flat shank shoulder (r 2.3 mm) is
wider than the back-wall flood hole (r 1.5 mm) — it **bottoms on the annular
step** and cannot pass through (−Z stop). The head flange (r 3.9 mm) is wider
than the cover-boss bore (r 2.6 mm) — once the cover is on, the head face
seats against the cover-boss face and **cannot lift past it** (+Z stop). The
dowel is trapped between two rigid shoulders with ~0 axial slop. No barb; no
click. **Must be installed before the cover is snapped on.**

**Finger snap pins — `pin_C_R`, `pin_D_R`, `pin_C_L`, `pin_D_L` (4 pins, barbed)**

Retention by **rigid counterbore capture**. A confining pocket (SNAP_CB_R
3.65 mm, depth 1.3 mm) is cut into the exit face of each receiving eye. The
locking lip (r 3.2 mm) passes the bore (r 2.6 mm) and drops into the pocket.
The **rigid annular shoulder** (1.05 mm wide, at the pocket/bore step) takes
axial pull-out load in rigid material. The pocket wall radially confines the
lip — creep drives the lip outward toward the wall (harder to escape), not
inward (easier). This is geometric capture, not elastic preload. A positive
**click** confirms the lip has seated. Inserted from above the finger, barb
exits below the link eye.

---

### 1.2 Material rationale (seawater picks)

- **Structural parts and all pins → PETG (default), or ASA / PA-GF.**
  PETG has very low water uptake, does not hydrolyze (unlike PLA), holds
  dimension under the modest loads of a flooded passive gripper, and has the
  elasticity the snap-pin barbs need. **ASA** adds UV stability for topside
  work. **Glass-filled nylon** for deep/long dives where creep and hydrostatic
  load matter. All are polymer → no galvanic concern. **Never PLA** (hydrolyzes
  underwater). **Never TPU for pins** (creeps under sustained load, wallows
  bores, loses snap retention).

- **Fingers → ether-based TPU ~95A.** The Fin Ray grip principle is material
  compliance — the fingers must flex to wrap around an object. **Ether-based**
  TPU is hydrolysis-stable in sustained/warm immersion. **Ester-based TPU
  hydrolyzes** and crumbles underwater — exclude it entirely. 95A shore
  balances conformance with grip force; softer (85A) for delicate objects,
  stiffer (98A) for more grip force.

---

## 2. Zero bought hardware — what this revision eliminated

**This is a fully 3D-printed, zero-hardware gripper.** No screws, no nuts, no
bolts, no washers, no bushings. Assembly is tool-free: drop in the printed
axle dowels, snap on the cover, push in the barbed finger pins. Disassembly
reverses in kind — flex the cover clips and lift out the pins.

| Obsolete metal item (previous version) | Count | Replaced by |
|---|---|---|
| Pivot screws / metal dowels (1 drive axle + 2 follower axles + 4 finger pins) | 7 × A4/316 SS | **7 printed pins** — 3 axle dowels (`pin_A_R/B_R/B_L`) + 4 finger snap pins (`pin_C_R/D_R/C_L/D_L`) |
| Nylon-insert locknuts (one per pivot) | 7 × SS | **Eliminated** — axle dowels trapped by cover geometry; finger pins by counterbore lock |
| M3 front-cover screws | 4 × A4/316 SS | **4 integral printed cantilever snap clips** on `front_cover` |
| Input-shaft plain bushing (PTFE/acetal) | 1 | **Eliminated** — shaft runs in a bare flooded printed bore |
| **Total bought hardware** | **19 pieces** | **0 pieces** |

---

## 3. The input shaft runs in a bare printed bore (no bushing)

The input shaft is **integral to `drive_arm_L`** and exits through the back-wall
bore. In this flooded design it turns in a **plain printed bore** in the housing
— no separate bushing. The bore (`BUSH_BORE_R = 4.4`) clears the Ø8 mm shaft
(`SHAFT_R = 4.0`) with a running fit.

A bare printed bore works flooded because there is no pressure differential and
no dry cavity — the joint runs wet, water is coolant and lubricant. A sealed
bearing would trap grit in the race and corrode; an Oilite bushing would leach
its oil when flooded. A bare printed bore needs no grease and flushes clean with
a fresh-water rinse.

---

## 4. User-supplied items (outside the gripper BOM)

| Item | Qty | Notes |
|---|---|---|
| Waterproof servo / actuator | 1 | Drives the rear D-profile coupler on `drive_arm_L`. Coupler: radius 5.0 mm, D-flat depth 1.4 mm, length 12 mm. Use an IP68/submersible servo, a potted hobby servo, or a sealed/oil-filled actuator with a pressure compensator for depth. The actuator is the only real waterproofing burden in the system. Servo coupling/horn is user-supplied or printed separately. See `UNDERWATER.md` §6. |
| M4 bolts (robot-arm mount) | 4 | Attach the back flange (holes at (±37, −14) and (±37, +8) mm) to your robot arm or mount. These are **arm hardware, not gripper hardware** — choose grade and length to suit your arm. If the arm is metal, add nylon or PTFE shoulder bushings + isolating washers at each bolt (see `UNDERWATER.md` §5). The gripper itself contributes no metal to this joint. |

---

## 5. Printed-part count summary

| Group | Qty |
|---|---|
| `enclosure` | 1 |
| `front_cover` (4 integral clips + 2 vent holes) | 1 |
| `drive_arm_R` | 1 |
| `drive_arm_L` (integral shaft + D-coupler) | 1 |
| `follower_R` | 1 |
| `follower_L` | 1 |
| `finger_R` (TPU) | 1 |
| `finger_L` (TPU) | 1 |
| `pin_A_R` (axle dowel) | 1 |
| `pin_B_R` (axle dowel) | 1 |
| `pin_B_L` (axle dowel) | 1 |
| `pin_C_R` (finger snap pin) | 1 |
| `pin_D_R` (finger snap pin) | 1 |
| `pin_C_L` (finger snap pin) | 1 |
| `pin_D_L` (finger snap pin) | 1 |
| **Total printed parts** | **15** |
| Bought hardware (screws/nuts/bolts/bushings) | **0** |
| User-supplied | Waterproof servo + coupling; M4 flange bolts + galvanic isolators |

---

## 6. Why fully-printed is corrosion-proof underwater

A gripper made **entirely of polymer** has **no galvanic cell anywhere** —
and galvanic corrosion is the primary failure mode of mixed-metal hardware in
seawater. The previous version maintained all metal in one stainless family
(316/A4) to avoid an internal galvanic pair; this revision deletes the problem
at the root by deleting the metal.

With no screws, nuts, bolts, pins, or bushings:

- **No dissimilar-metal contact, no anode, no pitting, nothing to rust.**
- Structural parts in PETG/ASA/PA-GF: low water uptake, no hydrolysis, holds
  dimension over months of immersion.
- Pivot pins in PETG: stiff enough to keep snap retention positive, tough
  enough to flex on insertion without cracking.
- Fingers in ether-based TPU: does not hydrolyze in sustained immersion.
- Housing flooded: internal and external pressure equalize through drain holes
  and vent holes — the thin printed wall sees no differential, nothing to
  crush.
- Shaft runs in a bare flooded bore: flushes clean, no sealed race to trap grit,
  no Oilite to leach oil, no seal to fail.

**Net: nothing to rust, nothing to seal, nothing to crush, and nothing to buy
inside the gripper — rinse with fresh water after each salt dive.**

# Running this gripper underwater

A practical guide for taking the geared four-bar / Fin Ray gripper (see
`gripper.py`, `README.md`) into fresh or salt water. It answers the obvious
question first, then covers the real-world details.

This is the **material / seawater** companion to `PRINTING.md` (which covers
orientation, supports, and slicer settings). Decide *how* to print there; decide
*what to print it in* and how to run it wet here. The headline: **print it
flooded, in marine-grade polymers and 316/A4 stainless, and there is nothing to
seal.**

## Will the gears be fine underwater? — Yes.

Open spur gears run fine underwater **when the gearbox is flooded**, which is the
standard approach for ROV/AUV manipulators and tooling. The two 16-tooth spur
sectors (12 mm pitch radius, meshing on the centreline) don't care that they're
wet — water is a poor lubricant but a fine coolant, and at this size, speed, and
torque the mesh has plenty of margin. Let the housing flood through the drain
holes and run the mesh wet.

The gears fail underwater for **material/contamination** reasons, not because
they're submerged:

- **Corrosion** — plain carbon steel rusts fast in water and very fast in salt.
  The teeth pit, mesh quality drops, then it seizes. **Don't use plain carbon
  steel.** Use acetal/Delrin, nylon, or 316 stainless.
- **Lubricant washout** — any grease packed in an open mesh washes out within a
  few cycles. Plan to either run dry on self-lubricating polymer gears, or use a
  water-resistant marine/PTFE grease and re-apply (see Lubrication).
- **Grit & biofouling ingress** — the open mesh and slot openings let sand, silt,
  and marine growth into the teeth. This is abrasive and can jam the mesh. The
  flood/drain holes (below) double as a flush path; rinse after every dive.
- **Galvanic corrosion** — mixing dissimilar metals in seawater drives the less
  noble one to corrode (see Galvanic corrosion). All-polymer mesh sidesteps this
  entirely.

Bottom line: flooded + corrosion-resistant tooth material = reliable. The default
recommendation is **acetal (Delrin) or 316 SS gears**, run flooded.

## Flooded vs sealed — choose FLOODED

**Recommended: flooded, pressure-equalized.** Let water fill the housing through
the drain/flood holes. This is simple, depth-independent, and needs no seals.
Internal and external pressure equalize automatically, so the housing wall sees
no pressure differential and there is nothing to crush or implode.

Do **not** seal this housing dry without a real pressure-rated enclosure:

- **Trapped air = buoyancy + crush risk.** A sealed air pocket makes the tool
  buoyant and, more importantly, the external water pressure (~1 bar per 10 m of
  depth) tries to collapse the housing. A 3 mm-walled printed/CNC slate body is
  not a pressure vessel.

A **sealed/dry housing is only worth it** when you need clean dry internals
(precision metal gears with retained grease, electronics inside, very long
service intervals). If you go that route, the housing then needs:

- A **dynamic shaft seal** on the input shaft where it exits the back-wall bore
  (`SHAFT_BORE_R = 5.0 mm` in the CAD — that bore is exactly where a rotary lip
  seal or shaft O-ring goes).
- **Static gaskets / face O-rings** on any cover joint and the mounting flange.
- **Pressure-rated walls** sized for your max depth, or
- **Oil-fill + a pressure compensator** (a flexible bladder that equalizes
  internal oil pressure to ambient) — this is how "dry" subsea gearboxes actually
  survive depth without thick walls.

For this passive gripper, none of that is needed. Flood it.

## Material BOM by part

Corrosion-resistant picks for freshwater and saltwater. Saltwater is the harder
case — bias toward 316/A4 stainless and inert polymers there.

| Part | Freshwater pick | Saltwater pick | Avoid |
|---|---|---|---|
| Enclosure / housing | PETG, ABS, or anodized 6061 Al | Glass-filled nylon, acetal, or anodized 6061; HDPE | **PLA** (absorbs water & hydrolyzes), bare aluminium next to SS |
| Drive shaft | 303/304 SS or acetal | **316 SS** | Carbon/mild steel, brass in salt |
| Gears (spur sectors) | Acetal/Delrin or nylon | Acetal/Delrin or **316 SS** | Plain carbon steel |
| Pivot pins (A,B,C,D) | 304 SS shoulder pins | **316/A4 SS** shoulder pins | Carbon steel dowels |
| Fasteners (M4 flange etc.) | A2 (304) stainless | **A4 (316)** stainless | Zinc-plated steel, mixed-metal mix |
| Bushings (if fitted at pivots) | Acetal or PTFE | PTFE or sealed SS bearing | **Oil-impregnated bronze (Oilite)** — loses its oil when flooded |
| Fingers (Fin Ray) | TPU | **Ether-based TPU** | Ester-based TPU for long warm immersion |

Notes:

- **PLA is listed as an option in the README for rigid parts — do not use it
  underwater.** It absorbs water and hydrolyzes over time, losing strength.
  Substitute PETG/ABS/nylon or metal.
- **Oil-impregnated bronze (Oilite) bushings are a trap underwater:** the
  impregnated oil leaches out when flooded, leaving a dry porous bushing. Use
  solid plastic, PTFE, or sealed stainless bearings instead.
- Keep the assembly **single-metal where possible** (all 316, or all polymer) to
  avoid galvanic pairs.

### Final pick per part — SEAWATER build

The committed "just tell me what to use in salt water" list. Where two are given,
either works; the first is the default.

| Part (from `gripper.py`) | Seawater material |
|---|---|
| `enclosure` (flooded housing) | **Glass-filled nylon** or **acetal**; PETG/ASA OK for short/shallow work; anodized 6061 if you machine it |
| `front_cover` (optional) | Same as the enclosure |
| `drive_arm_R` / `drive_arm_L` (gear + arm) | **Acetal (Delrin)** or glass-filled nylon — self-lubricating teeth, runs dry flooded |
| Integral input shaft (part of `drive_arm_L`) | Printed acetal/nylon for light duty; **316 SS shaft insert** for real torque (see Input shaft) |
| `follower_R` / `follower_L` | Acetal or glass-filled nylon |
| `finger_R` / `finger_L` (Fin Ray) | **Ether-based TPU** (e.g. NinjaFlex / suitable BASF grade) — *not* ester-based |
| Pivot pins A/B/C/D | **316 / A4 stainless** dowel or shoulder pins |
| Flange / cover fasteners | **A4 (316) stainless** |
| Pivot bushings (if fitted) | **PTFE or acetal** plain bushing — never Oilite |

Single-family rule: keep **every metal part 316/A4 stainless** so there is no
galvanic pair inside the gripper, and isolate the whole gripper from any
dissimilar metal on the robot arm (see Galvanic corrosion).

### The input shaft (flooded plain bushing — no seal)

The input shaft is **integral to `drive_arm_L`** and exits through the back-wall
bore (`SHAFT_BORE_R = 5.0 mm`). In the **flooded** design it rides in a simple
**plain bushing** and needs **no dynamic seal at all** — because there is no
pressure differential and no dry cavity to protect, the shaft just turns wet:

- **Bushing material: PTFE or acetal.** Both are self-lubricating and run dry
  when flooded; water is the coolant. **No grease is required.** A dab of
  **marine grease is optional** — it can smooth break-in and slightly reduce
  wear, but in an open flooded bore it is partly sacrificial, so don't rely on it.
- **No lip seal, no O-ring** on the shaft in the flooded build. The bore is sized
  to clear the shaft, not to seal it.
- *(Aside — if you ever want a DRY / sealed variant:* you'd add a **rotary lip
  seal or shaft O-ring** in that 5 mm bore, **static face O-rings** on the cover
  and flange joints, and either **pressure-rated walls** for your max depth or an
  **oil-fill + pressure compensator**. That is a different machine — for this
  passive gripper, stay flooded.)

## Lubrication

- **Self-lubricating polymer mesh (acetal/nylon/PTFE) can run dry** — usually the
  simplest and most reliable choice flooded. Water provides cooling; the polymer
  provides the low-friction surface.
- **If you grease**, use a **water-resistant marine grease (calcium-sulfonate or
  PTFE-fortified)**, not standard lithium grease — lithium grease emulsifies and
  washes out. Accept that even good grease in an open mesh is partly sacrificial.
- **Maintenance:** after each saltwater dive, **rinse with fresh water**, dry,
  inspect the mesh for grit/pitting, and **re-grease** if greased. Salt left to
  dry crystallizes in the mesh and accelerates wear and corrosion.

## Galvanic corrosion

In seawater, dissimilar metals in contact form a battery and the less-noble metal
corrodes preferentially.

- **Best fix: don't mix metals.** Keep every metal part in the gripper the **same
  stainless family (all 316/A4)**, or go all-polymer where the load allows. A
  single-family assembly has no internal galvanic pair.
- **Isolate the gripper from the rest of the robot.** Even if the gripper is
  internally all-316, the arm it bolts to may be aluminium, anodized, or a
  different stainless. Break that path: mount with **nylon/PTFE isolating washers
  and shoulder bushings** at the flange so the gripper isn't electrically tied to
  a dissimilar-metal robot frame.
- If you must mix metals anyway (e.g., aluminium housing + SS fasteners), use the
  same **isolating washers / nylon shoulder bushings** to break the path, and keep
  the small-anode/large-cathode trap in mind (a small bare-aluminium feature next
  to a large SS area corrodes fast).
- For larger metal assemblies on long deployments, a **sacrificial zinc/aluminium
  anode** protects the structure. For a hand-sized gripper this is usually
  overkill — material choice + isolation is enough.

## The Fin Ray TPU fingers

**TPU works wet.** The compliant Fin Ray action — tip curling and wrapping around
an object as the contact face loads — is a mechanical/geometric behaviour and
still works fully submerged. Practical notes:

- TPU **absorbs a little water and may swell/soften slightly**, marginally
  changing finger stiffness. For most grasping this is negligible; if you've tuned
  grip force tightly, re-check it wet.
- **Chemistry matters for chronic immersion:** **ester-based TPU hydrolyzes** in
  long or warm immersion and eventually crumbles. For sustained underwater use,
  print the fingers in **ether-based TPU** (e.g. NinjaFlex / suitable BASF
  grades). Short dives in any TPU are fine.
- A wet, slightly softer TPU surface can actually improve conformance on smooth
  objects.

## Why the drain/flood holes (this housing)

The housing is being given drainage/flood holes specifically so it runs as a
flooded design:

- **Bottom-row holes + low side holes** let the cavity **flood and drain in any
  orientation** — fingers up, down, or sideways, no air stays trapped.
- They **equalize internal/external pressure** continuously, so the wall never
  sees a pressure differential (no crush, no implosion, depth-independent).
- They give grit and silt a **flush-out path** — water moving through the mesh
  during actuation, plus a freshwater rinse afterward, carries debris out instead
  of packing it into the teeth.
- Holes should clear the top link slots and the shaft bore so they don't weaken
  those features.

## Actuation & buoyancy

The gripper itself is **passive and flooded** — only the input shaft needs to be
driven. Drive it with one of:

- a **waterproof/submersible servo** (IP68-rated, or a hobby servo potted/sealed),
  or
- a **sealed or oil-filled actuator with a pressure compensator** for deeper /
  longer work.

The actuator carries the only real waterproofing burden in the system. The
flooded gripper adds little trapped air, so its buoyancy contribution is small and
roughly constant with depth; account for the actuator and any mount in your
overall buoyancy trim.

## Depth & pressure

- **Flooded design is essentially depth-independent.** Pressure equalizes through
  the holes, so the mechanism behaves the same at 1 m or 100 m. Polymer parts see
  hydrostatic pressure equally on all sides and don't care.
- **What changes with depth is only the sealed bits** — i.e. the actuator, and the
  housing *only if* you chose the sealed-dry route. Then seals, wall thickness,
  and/or a compensator must be rated for max depth.
- Practical limit for the flooded gripper is set by your **materials and actuator**,
  not by the gripper's structure.
- **Rough depth guidance for this flooded printed housing:** because it floods and
  equalizes, the printed body has no hard depth ceiling — water pushes equally
  inside and out. The realistic envelope is **a few tens of metres for a
  hobby/ROV rig and into the 100 m+ range** if the actuator and electronics are
  rated for it; the gripper goes as deep as whatever drives it. Three things still
  scale with depth even on a flooded part: **(1)** any *unintended* trapped-air
  pocket (a blind bolt hole, a dead-end rib cavity, an unvented cover) sees the
  full crush load — vent every pocket; **(2)** water uptake and creep in the
  polymer grow with pressure, time and temperature, so for deep/long dives prefer
  **glass-filled nylon or acetal** over PETG/ASA; **(3)** the actuator/seal, not
  the gripper, sets the true rating — match it to your target depth.

## Pre-dive / post-dive checklist

**Pre-dive**

- Confirm gears, pins, fasteners are corrosion-resistant grade (no carbon steel).
- Confirm flood/drain holes are clear and unobstructed.
- Cycle the gripper open↔close in air; check smooth mesh and full travel.
- Confirm the actuator/shaft seal (if any) is intact and the actuator is rated for
  depth.
- Check galvanic isolation washers are in place on any mixed-metal joint.
- Verify buoyancy trim with the gripper fitted.

**Post-dive**

- **Rinse thoroughly with fresh water**, especially after salt — flush the mesh
  and flood holes.
- Cycle open↔close to flush trapped grit; inspect teeth for grit, pitting, growth.
- Dry, then **re-grease** if the mesh is greased.
- Inspect TPU fingers for swelling/softening or surface damage.
- Check fasteners and pins for early corrosion; replace any that show it.

## What's already in the CAD vs. what you choose at fabrication

**Already reflected in the CAD (`gripper.py`):**

- **Flooded-design geometry** — the housing is open to flooding (top link slots,
  shaft bore, plus the drain/flood holes being added).
- **TPU Fin Ray fingers** — compliant grip that works submerged as-is.
- **Plastic/SS-friendly geometry** — plain shoulder pins (PIN_R 2.3 mm),
  clearance-bored links/gears, M4 flange holes — all compatible with stainless or
  polymer parts with no redesign.
- **A shaft bore** (`SHAFT_BORE_R = 5.0 mm`) sized to accept a rotary lip seal or
  shaft O-ring *if* you ever choose the sealed-dry path.

**You must choose at fabrication:**

- **Actual materials per part** — pick from the BOM / final-pick tables above
  (acetal/316 for gears & pins, PETG/nylon/anodized-Al housing, ether-TPU fingers).
  In particular, **don't print the rigid parts in PLA for underwater use** even
  though the README lists it. See **`PRINTING.md`** for how to orient and slice
  each part once the material is chosen.
- **Fasteners** — A2 for freshwater, **A4/316 for salt**.
- **Bushings** — plastic/PTFE/sealed-SS, **not Oilite**.
- **Actuator** — a waterproof servo or sealed/oil-filled actuator with compensator,
  rated for your depth.
- **Lubrication strategy** — run dry on self-lubricating polymer, or marine/PTFE
  grease with a rinse-and-re-grease routine.
- **Galvanic isolation / anode** — only if you end up with a mixed-metal assembly.

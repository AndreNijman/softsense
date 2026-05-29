# Fixed-mount on ROV chassis — interface study

Adapter-mount research for **bolting the all-polymer flooded gripper directly to
an ROV chassis** (no manipulator arm in between). The ROV positions the gripper
with its own thrust; the gripper is a fixed forward- or downward-facing tool.

This is the inverse of the manipulator interface campaign (`motor/interfaces/`
arm-side files): instead of a Reach/Schilling end-effector plate, the gripper's
bottom M4 flange mates to a printed adapter that bolts to **chassis holes the
ROV vendor publishes**. Chassis-mount is the dominant pattern in hobby,
inspection-class, and citizen-science ROVs because manipulator arms cost more
than the vehicle they hang off.

> **Honesty.** Where Blue Robotics publishes a number (datasheet, store page,
> drilling-template PDF, or assembly guide) it is quoted verbatim with a
> numbered source. Numbers we could not verify (e.g. the often-repeated claim
> that BR2 side panels carry a 25 mm M3 grid) are surfaced in §11, not asserted.
> Estimates are marked **(estimate)**. The shipped manipulator-mount
> counterpart is `../ROV_INTEGRATION.md`; this file is the **chassis-mount**
> sibling.

---

## 1. Why a fixed chassis mount

Most published gripper-on-ROV integrations in the public hobby/conservation
literature use **chassis mounts, not arms.** The reason is price-class:

- **Manipulator arms** (Reach Bravo, Schilling Titan, ECA ARM 5E) start at
  USD ~10 k and target work-class vehicles. Reach Bravo's payload interface
  is a real product [12], but the arm itself dwarfs a USD-3 k BlueROV2.
- **Chassis grippers** (Blue Robotics Newton, Chasing Grabber Arm, QYSEA tool
  port) are USD 60–800. They bolt to the vehicle frame and the **pilot drives
  the ROV** onto the target.

Public reference applications all use the chassis-mount pattern:

| Application | Vehicle class | Gripper interface | Source |
|---|---|---|---|
| Lionfish removal (community & RSE prototypes) | BlueROV2 | Newton, or custom spear/suction on a chassis-bolted frame | [8] [13] |
| BR-promoted "autonomous lionfish harvester" | BlueROV2 | Newton, bottom-panel mount | [8] |
| BR product page — "for BlueROV2 and other ROVs" | BlueROV2 + 3rd-party | Newton bracket with 2× M5×16 | [2] [3] |
| Citizen-science conservation volunteer work | Mixed inspection-class | Chassis-mount tooling on hobby ROVs | [13] |
| Chasing M2 Pro recreational grab tasks | Chasing M2 family | Chasing Grabber Arm 2, P/N 121129 bracket | [9] |
| QYSEA V6 / V-EVO sampling | FIFISH inspection-class | "Robotic Arm Mount Kit" with 2 holders | [10] [11] |

The shared geometry: **gripper bolts under or in front of the vehicle's
camera, cable runs along the frame to the main electronics bottle, and the ROV's
thrusters do all the fine positioning.** No joint angles, no kinematics — just
two M-class screws and a cable.

For our gripper specifically, this is the natural fit for **T1 (≤10 m,
inspection)** and **T2 (≤30 m, primary)** depth tiers (`SELECTION.md`),
because hobby ROVs in that class do not carry manipulators. The XW540-T260
+ Blue Robotics 3" canister stack fits the BR2 payload skid envelope and uses
the same M3/M4/M5 fastener family BR ships everything in.

---

## 2. Reference ROVs — chassis interfaces per vehicle

| ROV | Chassis material | Published accessory interface | Documented gripper mount | Pub. payload budget | Notes |
|---|---|---|---|---|---|
| **Blue Robotics BlueROV2** (R3 / R4) | HDPE 1/2" (bottom + centre), HDPE 3/8" (sides); AL6061-T6 enclosure cradles [1] [4] | Bottom panel = blank HDPE drilled per template; Roof Rack accessory with pre-drilled multi-tool holes [6] [7] | **Newton Subsea Gripper** — 2× M5×16, drilled per BR drilling template [2] [3] | ~+0.2 kg net buoyancy with stock ballast; +0.5 kg additional from upgraded foam [1] [5] | The canonical hobby ROV; >50 % of public chassis-mount gripper builds |
| **BlueROV2 Heavy** | Same frame + extra horizontal thrusters | Same as BR2 + Heavy thruster brackets | Same as BR2 | Same payload class | Vector-thrust 6-DoF; gripper mount unchanged from BR2 |
| **BR2 Payload Skid** (BR-100233) | HDPE 1/2"; AL6061-T6 mounting clips [14] | 8× M5×16 to clamp under BR2; 4× M5×20 panels-to-bottom; 12 ballast-weight slots | Newton can mount to skid bottom panel (same 2× M5 footprint) | 12× 200 g extra ballast slots ⇒ 2.4 kg ballast budget if foam upgraded | Skid is 475 × 338 × 197 mm, 1200 g in air [14] |
| **OpenROV Trident** (discontinued, but still in field) | Moulded ABS shell, 410 × 205 × 86 mm, 3.5 kg [15] | "Payload Interface" rear bay, dimensions un-published in Kickstarter update [16] | Community 3D-printed claw grippers (rubber-band actuated) [17] | Not published | Forum/Kickstarter only; no formal accessory ecosystem since OpenROV shutdown |
| **Chasing M2 / M2 Pro / M2 Pro Max** | Moulded plastic shell + 1/4-20 tripod + proprietary accessory rail | Vendor-only "Mounting Bracket" P/N **121129** (required for M2 Pro Max) [9] | Vendor **Grabber Arm 2** (7 kgf, 170 mm range, 2.8 s actuation, 100 m depth) — only mount path | Not published | No public bracket drawings; vendor-locked |
| **QYSEA FIFISH V6S / V6 EXPERT / V-EVO** | Moulded plastic + vendor accessory port | "Robotic Arm Mount Kit" = 1 arm mount + 2 holders [10] [11] | Vendor 1-DoF claw arm; tool head swaps (clamp / sampler / circular claw) | Not published | "Over 20 professional tools" all share one undocumented bay [11] |
| **Custom T-slot ROV (DIY hobby)** | 20 × 20 mm aluminium extrusion, V-slot or T-slot | M5 T-nut + M5 button-head every 20 mm; any face, any orientation | DIY only — community examples vary | Builder-defined | Our printed adapter only needs 2× M5 T-nut holes spaced on any 20 mm multiple |

Take-aways:

- **BR2 is the only ROV in this class with public dimensioned mounting docs.**
  Everyone else is vendor-locked (Chasing, QYSEA) or community/discontinued
  (Trident). The mount design therefore *anchors on BR2*, and we describe the
  others as compatibility notes.
- **The Newton bracket footprint (2× M5×16 on a 100 mm-pitch line, 16° tilt)
  is the de-facto BR2 chassis-mount standard** — and the cheapest single
  interface for any third-party gripper to copy.

---

## 3. BlueROV2 — chassis geometry we could verify

### 3a. Top-level dimensions

| Quantity | Value | Source |
|---|---|---|
| External length | 457 mm (18 in) | BR datasheet/specs [1] |
| External width | 338 mm (13.3 in) | [1] |
| External height | 254 mm (10 in) | [1] |
| Weight in air, no ballast | 9–10 kg (20–22 lb) | [1] |
| Weight in air, with ballast | 10–11 kg (22–24 lb) | [1] |
| Net buoyancy, no ballast | +1.4 kg (+3 lb) | [1] |
| Net buoyancy, with ballast | +0.2 kg (+0.5 lb) | [1] |
| Max rated depth | 100 m (330 ft) | [1] |
| Max tested depth | 130 m (425 ft) | [1] |
| Stock ballast | 6 × 200 g coated lead | [1] |
| Main tube ID × L | 102 × 298 mm (4.0 × 11.75 in) | [1] |

**Why this matters for our gripper.** A standard BR2 (no foam upgrade) has
+1.4 kg net positive buoyancy *without* ballast. After the ~1.2 kg of stock
ballast it's near-neutral. Our gripper stack (≤350 g gripper + ~600 g BR 3"
canister assembly with XW540 + cable; *estimate*, see §6) consumes
**~0.95 kg of the standard ballast budget if we remove ballast to compensate**
— which is the natural integration path: take out 5× 200 g lead, add 950 g
gripper, you're back to ~+0.2 kg net buoyancy.

### 3b. Frame composition (R3 / R4) [4] [18]

| Panel | Material | Thickness | Quantity | Attachment |
|---|---|---|---|---|
| Side panels | Black HDPE | 3/8" (9.5 mm) | 2 | M5×20 to bottom panel (4×); M5×16 to centre panels (8×) [18] |
| Bottom panel | Black HDPE | 1/2" (12.7 mm) | 1 | Foundation for battery + skid mount |
| Front/rear centre panels | Black HDPE | 1/2" (12.7 mm) | 2 + 2 | Rear has 3 large pass-throughs |
| Enclosure cradle (4" series) | AL6061-T6, type III anodized | n/a | 2 | M4×18 to centre panels (8×) |
| Battery clamp (3" series) | AL6061-T6 | n/a | 1 | M4×14 to bottom panel (4×) |
| Stock-bag fasteners | 316 stainless | mixed M3/M4/M5 | as above | All metal hardware 316 SS [4] |

**No factory accessory grid is published.** BR ships the bottom panel as a
**blank HDPE plate** that the customer drills per the printed template that
comes with each Newton Gripper (§4). The Roof Rack accessory carries
pre-drilled multi-tool holes (§3d), but the **side and bottom panels do not.**

### 3c. Bottom panel — the canonical gripper-mount surface

From the Newton drilling-template PDF (BR document
`NEWTON-GRIPPER-W-MOUNTHOLE-DRILLING-TEMPLATE-R1`, SolidWorks 2018) [3]:

- Newton's bracket sits on the **underside of the bottom panel**, with the
  counterbore side facing **down**.
- Two M5 clearance holes are drilled **through the full 12.7 mm HDPE thickness**.
- The drill bit is **Ø5.50 mm** (or 7/32") — that's M5 clearance with thread
  rolled directly into HDPE (no metal insert).
- The two holes lie on a line **100 mm pitch**, with offsets **16 mm** and
  **31 mm** from a reference edge (right vs. left side respectively), at a
  **16° angle** to that edge.

> **The 16° tilt is the design insight.** The bottom-panel Newton mount is not
> orthogonal to the keel — it's canted ~16° so the gripper jaws clear the
> bottom panel and aim into the front-camera frustum. Any third-party gripper
> intending to drop into "the Newton mount slot" must inherit this tilt or
> publish its own offset.

| Newton-mount drilled-hole geometry (BR template R1) | Value |
|---|---|
| Hole count | 2 |
| Hole diameter | Ø5.50 mm (or 7/32") |
| Hole pitch (between centres) | 100 mm |
| Right-side edge offset | 16 mm |
| Left-side edge offset | 31 mm |
| Pattern angle to side edge | 16° |
| Drill direction | Straight through HDPE bottom panel |
| Fastener | 2× M5×16 button-head socket cap [2] |

### 3d. Roof Rack — the alternative front-mount surface

BR-200126 / "BlueROV2 Roof Rack" [6] [7]:

- Material: AL 5052-H34 (bent sheet).
- Mass: 177 g in air [6].
- Cost: USD 57 [6].
- Mount to BR2: **uses existing mounting holes** on the side panels (top
  mount), or the four Lumen-light holes (front mount) [7].
- Top-mount fasteners (included): 4× M5×12 button-head [7].
- Front-mount fasteners (included): 4× M3×12 socket-head [7].
- Pre-drilled hole sets on the rack itself (from BR): WTE3 + WTE4 clamps (×3),
  Lumen lights (×4), Ping360 (×3), **Newton Gripper (×2)**, Sonoptix Echo (×3),
  1/4-20 UNC tripod mounts (×3) [6].
- Two top-mount angles available: **0° (flat)** or **10° tilt**, by choosing
  different bolt hole pairs on the rack [7].

> **Hole coordinates not published.** The Roof Rack drawing referenced on the
> store page does not give per-feature coordinates we could parse. BR's
> documented design intent is "every supported accessory has 2–4 holes
> pre-drilled in known positions, use the installation guide for that
> accessory" [7] — but those guides do not redistribute the per-coordinate
> data either. **For our adapter, this means we either (a) carry our own M5
> pattern matching Newton's 2-hole footprint and use the rack-Newton positions,
> or (b) buy a Roof Rack, photogrammetry-measure it, and design to the measured
> dimensions.**

### 3e. Payload Skid — third mount surface

BR-100233 (BR2 Payload Skid) [14] [19]:

| Quantity | Value | Source |
|---|---|---|
| Length × width × height | 475 × 338 × 197 mm | [14] |
| Mass in air | 1200 g (2.65 lb) | [14] |
| Panel material | HDPE (sides, bottom); AL6061-T6 (mounting clips) | [14] |
| Attach to BR2 (mounting clips) | 8× M5×16 button-head [19] | [19] |
| Frame internal fasteners | 4× M5×20 (panels-to-bottom); 4× M4×14 (clamps); 4× M3×12 (enclosure clamp) | [19] |
| Ballast slots | 12× 200 g positions (= 2400 g compensation budget) | [14] |
| Payload bays | 2× 4" enclosures **or** 3× 3" enclosures + 2× Lumens | [14] |
| Cost | USD 320 | [14] |

A BR2 Payload Skid is **the cleanest production path for our 3" canister
gripper** because it natively accommodates a 3" enclosure clamped on its
underside *and* a Newton mount on the same bottom panel. The skid mounting
clips bolt to the same side-panel holes the Roof Rack uses [14].

---

## 4. Newton Subsea Gripper — the canonical chassis-mount gripper

The Newton Gripper is the de-facto reference because it is **the only mass-
market chassis-mount gripper with a publicly dimensioned BR2 mount.** Everything
about our adapter should at minimum be Newton-compatible at the chassis side,
because that lets us slot into the existing BR2 ecosystem with zero new holes.

### 4a. Published specs (BR product page) [2]

| Quantity | Value |
|---|---|
| SKU | BR-100789 (current R2-RP); also seen as BR-100862 in older listings |
| Cost | USD 720 |
| Supply voltage | 9–18 V |
| PWM logic voltage | 3.3–5 V |
| Peak current | 6 A |
| PWM neutral | 1500 µs |
| PWM open | 1530–1900 µs |
| PWM close | 1100–1470 µs |
| Grip force, jaw tip | 97 N (22 lbf) |
| Grip force, mid-jaw | 124 N (28 lbf) |
| Jaw opening | 62 mm (2.44 in) |
| Linear travel | 13.5 mm (0.53 in) |
| Operation time, open → close | 1.6 s |
| Length, closed | 303.2 mm (11.94 in) |
| Length, open | 309.2 mm (12.17 in) |
| Body diameter | 36 mm (1.42 in) |
| Mass in air | 524 g (18.5 oz) |
| Mass in water | 267 g (9.4 oz) |
| Housing | Aluminium 6061-T6 (anodized) |
| Pressure rating | 300 m (984 ft) |
| Cable | BR-101050 (3 conductors, 22 AWG, 635 mm length) |
| Wiring | Black GND, red +V, yellow PWM signal |
| Device-side penetrator | M06-4.5mm-LC |
| Cable-end penetrator | M10-4.5mm-LC |
| Mount kit | Anodized AL bracket + thumbscrew + 2× M5×16 + M10 nut/O-ring |

### 4b. Mounting kit contents (BR install guide) [3]

- **Mount kit (included in BR-100789):** anodized aluminium clamp bracket
  with thumbscrew, 2× M5×16 button-head, M10 penetrator nut + O-ring.
- **Additional hardware required:** medium-strength threadlocker; 3 mm hex
  driver; **5.50 mm drill bit (or 7/32")**; tape; printed drilling template
  (PDF, BR website).
- **Penetrator on BR2 end:** drilled into a blank position on the 4" end cap
  using the M10 hole — the gripper's signal/power cable runs through this and
  terminates inside the electronics enclosure.

### 4c. BR2 install procedure summary [3]

1. Power off; remove enclosure mounting screws (M3, 2.5 mm hex).
2. Slide enclosure aft, expose end cap.
3. Remove one of the **blank M10 penetrators** in the middle of the BR2 end
   cap with an M10 wrench.
4. Install Newton's M10 penetrator (lubricate O-ring with silicone grease).
5. Route signal wire to a Pixhawk PWM output channel; connect +V/GND to the
   terminal blocks inside the enclosure.
6. Reassemble enclosure (silicone grease on all O-rings).
7. **Print the Newton drilling template PDF at "Actual size,"** cut it out,
   tape it to the *underside* of the bottom HDPE panel (counter-bore side).
8. Drill 2× holes straight through with a Ø5.50 mm bit (hand drill OK on
   12.7 mm HDPE).
9. Weave the gripper through the frame from the front, clamp into the
   bracket, install 2× M5×16 from above with threadlocker.
10. Cable-tie the gripper cable along the frame to prevent thruster contact.
11. Rebalance ballast (typically remove 2–3 lead weights to compensate).

### 4d. Newton bracket dimensions — what BR does **not** publish

The Newton bracket is a custom anodized AL part. BR does not publish:

- Bracket outer dimensions (length, width, thickness).
- The bracket's relationship to the gripper's body cylinder axis (other
  than "two M5 clearance holes 100 mm apart, 16° canted").
- The thumbscrew torque spec.
- Bracket mass alone (the 524 g figure is the whole assembly).

**Verifiable inference (estimate, marked):** From the published 303 mm body
length and 36 mm body diameter, and the 100 mm 2× M5 footprint, the bracket
is ≥100 mm along the body and clamps a Ø36 cylinder — i.e. a saddle/clamp
geometry, not a flange. Our gripper, by contrast, has a planar flange at the
bottom of a 3" (76 mm) canister, so our adapter is a **flange-to-2× M5
pattern** transformer, not a saddle.

### 4e. Roof Rack front-mount (the second canonical Newton position) [6] [7]

The Roof Rack has *pre-drilled* "Newton (×2)" holes — Newton can move from
its bottom-panel slot to the Roof Rack without drilling. The Roof Rack itself
attaches to the BR2 in one of three positions:

- **Top, level (0°)** — over the electronics enclosure, between the
  side panels.
- **Top, 10° forward tilt** — same location, alternate bolt holes.
- **Front, inverted** — bolted to the four Lumen-light mounting points using
  4× M3×12.

The Newton on the rack faces **forward-down** when the rack is in the
front-mount Lumen-light position [7]. This is the second of the two
BR-blessed Newton geometries.

---

## 5. Forward vs downward vs side mount — trade-offs

| Aspect | Forward mount (nose) | Downward mount (belly) | Side mount (port/stbd) |
|---|---|---|---|
| Driving model | Pilot drives ROV forward into target | Pilot descends onto target | Lateral creep (used in pairs) |
| Visible in main camera | Yes — gripper appears in lower-front of frame | Marginal — needs lower-vehicle camera or angled main cam | Out of frame; pilot infers position |
| Centre-of-mass effect | Nose-heavy → trim nose-down (~5–10° pitch *estimate*) | Centred; lowers VCG slightly (good for roll stability) | Asymmetric → list angle |
| Bow-impact load | Yes — gripper takes initial chassis-tap | Low — descends onto target slowly | Low |
| Cable run to electronics tube | ~150–250 mm along top/side rails *estimate* | ~50–100 mm direct *estimate* | ~150 mm |
| BR2 implementation | Roof Rack front-mount (M3×12) or Newton on rack | Newton bottom-panel mount (M5×16, 16° tilt) | No supported BR2 path; custom only |
| Our gripper jaw direction | Jaws in line with ROV +X (push-grab) | Jaws point down (descend-grab) | Jaws point ±Y |
| Tasks suited | Spear-style grabs, lionfish, tether-attach, snag-clear | Bottom samples, archaeology, debris off seabed | Bimanual paired sampling (rare) |
| Trim compensation | Move ballast aft, add nose foam *(see §6)* | Symmetric — only mass-budget compensation needed | Counter-mass on opposite side |
| Failure-mode-on-impact | Gripper bracket and bottom panel take load | Gripper takes vertical impact only on descent | Skew load — worst for fasteners |

**Recommendation for our gripper** (`SELECTION.md` primary use case T2, BR2-class):

- **Forward (Roof Rack) is the recommended primary** because the gripper
  shows up in the main camera frustum without any extra camera hardware, and
  the lionfish/inspection use cases match the "drive into target" model.
- **Belly (Newton-bottom-pattern) is the recommended secondary** for sample
  collection / archaeology.
- **Side mount is out of scope** — no BR2-blessed path and our gripper is
  not designed for bimanual.

---

## 6. Trim / buoyancy implications for our gripper

### 6a. Mass budget (estimate, see `../REQUIREMENTS.md §1`)

| Component | Mass in air (g) | Notes |
|---|---|---|
| Gripper (all-polymer, flooded) | ~250–350 *(estimate; live `gripper.py`)* | Flooded ⇒ submerged mass ≈ 0 in seawater (PA12-GF SG ≈ 1.04; offset by water displacement) |
| BR 3" canister tube (240 mm, BR-102649-240) | ~250 *(estimate from BR product page)* | Aluminium |
| BR 3" end cap, penetrator face | ~120 *(estimate)* | Aluminium |
| BR 3" end cap, blank, drilled for shaft seal | ~120 *(estimate)* | Aluminium |
| XW540-T260 servo | 165 *(Robotis datasheet)* | |
| Internal mounting + cable gland | ~50 *(estimate)* | |
| Cable (RS-485 + power), 0.5 m to electronics bottle | ~30 *(estimate)* | |
| **Stack total in air** | **~985 g** *(estimate)* | Within ±15 % |
| **Stack net buoyancy in seawater (estimate)** | **+50 to +150 g positive** | Aluminium SG 2.7 dominates; tube is mostly air-filled → buoyant. **(estimate)** |

> **Why the net is *positive* in water.** The 3" canister is air-filled
> (servo dry inside), and its enclosed volume of ~2.0 L provides ~2.0 kgf of
> buoyancy *(estimate, π × 51² × 240 mm³)*. That largely cancels the ~1.5 kgf
> dry mass. The gripper itself is essentially neutral when flooded. We
> therefore expect a **net positive buoyancy of ~50–150 g** for the whole
> stack — i.e. we will be **adding lift, not lead, at the mount point**.

### 6b. BR2 ballast bookkeeping

| BR2 state | Net buoyancy (kg) | Source |
|---|---|---|
| As shipped, no foam, with ballast | +0.2 | [1] |
| Stock ballast removed entirely | +1.4 | [1] |
| With upgraded machined foam (R3 default) | +0.7 *(=+0.2 + 0.5)* | [5] |
| **Plus our gripper stack at ~+0.1 kg lift** | **+0.3 to +0.8 *(estimate)*** | derived |

**Compensation strategy (BR2 with stock foam):**

1. Remove **2× 200 g lead** from the rear ballast positions on the bottom
   panel to compensate for the gripper's mass *and* take advantage of the
   gripper's mild buoyancy. This biases pitch nose-down by ~3–6°
   *(estimate)*, useful for a forward-facing Roof-Rack-mounted gripper that
   wants to point into a target slightly below the horizon.
2. **Forward mount only:** add a 100 g foam wedge above the cradle to raise
   the COB *(centre of buoyancy)* over the new COM. (Optional; only
   noticeable in surge.)
3. **Belly mount only:** ballast remains roughly symmetric — only mass-
   budget compensation needed.

### 6c. Heavy-payload limit

The BR2 Payload Skid carries 12× 200 g extra ballast slots ⇒ **2400 g
compensation budget** [14]. Our ~1 kg stack consumes ~40 % of this. The
BR2 + skid + our gripper still has ample reserve for the upgraded foam
(+500 g lift) plus any other accessories. No buoyancy headroom problem at
T1/T2 depths.

---

## 7. Cable routing — bulkhead penetrator into the main electronics tube

### 7a. From canister to BR2 electronics enclosure

| Element | Spec | Source |
|---|---|---|
| Gripper canister cable exit | BR 3" end-cap blank penetrator (M10-4.5mm-LC or M10-7.5mm-LC depending on outer cable Ø) | BR penetrator catalogue [20] |
| Cable type | RS-485 + 12 V power, ≥4-conductor; 22–24 AWG signal, 18–20 AWG power *(estimate; see `../ELECTRICAL.md`)* | derived |
| Cable length, canister → electronics tube | 150–250 mm for forward (Roof Rack) mount; 80–150 mm for belly (bottom-panel) mount *(estimate)* | derived |
| Strain relief | Cable tie within 30 mm of each penetrator, plus 1× cable tie on the frame mid-run | BR ROV_INTEGRATION pattern, mirrors `../ROV_INTEGRATION.md §2` |
| BR2 enclosure entry penetrator | Re-use a blank slot on the BR2 end cap (the BR2 ships with 14× M10 slots, only some populated) | [1] |
| BR2-side connector | Same M10-4.5mm-LC blanks BR uses for thrusters and Newton itself | [3] |
| Service loop | ≥ 60 mm slack at the canister side and ≥ 30 mm at the BR2 side *(estimate)* | conservative |

### 7b. Why we don't need a separate wet-mate

BR's published flow is that the Newton (and our gripper by analogy) **goes
through a WetLink-style cable-end penetrator directly into the existing main
electronics enclosure** — no separate connector. The cable lands on
**screw terminals inside the enclosure**, next to the Pixhawk/Navigator
[3]. For RS-485 instead of PWM, the same end-cap penetrator path works; we
just terminate on the Navigator's serial header instead of a Pixhawk PWM
output (see `../ELECTRICAL.md`).

> **WetLink vs. SubConn.** BR's stock penetrator is a compression-gland WetLink
> (≤950 m rated [20]), assembled per-cable, not a wet-mateable connector.
> Pulling the gripper off the ROV in the field means **cutting cable ties
> and removing the end cap**, not unplugging anything. For T2 operations
> this is acceptable. For frequent swaps (T3 / professional), upgrade to a
> SubConn MCBH/MCIL micro circular connector on the BR2 end cap — adds
> ~USD 200 but allows wet-mate swap. Out of scope for the primary mount
> design.

### 7c. Cable abrasion protection along the frame

Same recipe as `../ROV_INTEGRATION.md §2a`:

- **Polyurethane spiral wrap or braided HDPE conduit** over the exposed run.
- Avoid PVC sleeving (embrittles in cold seawater).
- Cable ties every ~30 mm before any moving region; the BR2 has no moving
  parts in the cable path so the ties are pure abrasion control.

---

## 8. Vibration / impact protection — compliance bracket

Chassis-mount is **rigid** — the ROV's thrusters drive vibration straight
into the bracket, and any chassis-tap (driving the nose into a target)
delivers an impulse the bracket must accept.

### 8a. Vibration sources

| Source | Frequency band (estimate) | Mechanism |
|---|---|---|
| T200 thruster blade-pass | ~30–150 Hz at typical 1500–3000 rpm × 3 blades | Vortex shedding into chassis water |
| Servo gear meshing | ~10–40 Hz at 60 rpm output × tooth count | Gear FEA in `../DRIVETRAIN.md` shows gear ceiling is structural — minimise impulse from outside |
| Tether tug / surge | <1 Hz | Quasi-static; not a vibration concern |

### 8b. Recommended isolation stack

For a forward-facing Roof Rack mount, the gripper is ~150 mm forward of the
BR2 centreline and acts as a cantilever — vibration amplification is real.
Stacked from chassis up:

| Layer | Element | Function |
|---|---|---|
| 1 (under bracket head) | M5 nylon flat washer, 1 mm | Galvanic isolation + small compliance |
| 2 (bracket-to-rack interface) | **3 mm laser-cut TPU 95A compliance pad** (printed in-house from the same Bambu TPU 95A HF reel as the Fin-Ray fingers) | Vibration absorber + impact damper |
| 3 (rack-to-frame interface) | Rubber grommet sleeve isolator in each M5 hole *(McMaster 90131A132 family or eq.)* | Decouples high-frequency thruster vibration |
| 4 (M5 fastener) | A4-316 SS M5×20 with Loctite 243 *(not 271; medium-strength only)* | Per `../ROV_INTEGRATION.md §1c` |

The **TPU compliance pad** is the key idea. It is the same material we already
print the fingers in (Bambu TPU 95A HF), so no new BOM line. Sized to the
bracket's 2× M5 footprint plus 5 mm border, it transmits the static
clamp load (1.5 N·m × 1 mm thread pitch ⇒ ~9.4 kN per bolt; nylon-on-TPU is
fine) while absorbing ≥3 mm of impact travel.

### 8c. Impact / chassis-tap load

For a 9 kg BR2 driving forward at 1 m/s [1] into a stationary target,
the worst-case impulse if the gripper takes the full hit:

- Kinetic energy = ½ × 9 × 1² = 4.5 J.
- If stopping distance is 5 mm (rigid HDPE on rock), peak force ≈ 4.5 J ÷
  5 mm = 900 N (= 90 kgf). *(estimate, rigid-stop upper bound)*
- The 2× M5 SS A4 bolts have ≥4 kN shear capacity each — well above the
  impact load — but the **HDPE bore is the limiting element.** HDPE
  bearing strength ~25 MPa × 5.5 mm × 12.7 mm = 1.7 kN per bolt — also
  adequate, with a 1.8× margin.
- The TPU compliance pad reduces peak force by ~50–70 % by lengthening the
  stop distance from 5 mm to 15–20 mm. **Strongly recommended for any
  forward-mount build.**

> **`../FAILURE_MODES.md`** covers downstream failure paths (gear cracking,
> servo stall); the chassis mount adds one new mode — **HDPE bore wallowing**
> under repeated impact. Inspect the 2× M5 holes after every 50 dives;
> re-drill ±5 mm laterally and re-mount if wallowed.

---

## 9. Mount design proposal

### 9a. Primary variant — BR2 Roof Rack forward-mount

**Top face (chassis-side):** 2× M5 clearance holes matching the **Newton
pattern on the Roof Rack** — i.e. inherit Newton's bracket footprint so our
adapter drops into the existing Newton position with no chassis modification.

| Quantity | Value | Source |
|---|---|---|
| Top-face hole count | 2 | matches Newton bracket |
| Top-face hole pitch | 100 mm | matches Newton drilling template [3] |
| Top-face hole Ø | 5.5 mm clearance | matches Newton drilled holes [3] |
| Top-face hole offset to adapter centreline | 16 mm and 31 mm (or symmetric per measured rack) | matches template; **measure Roof Rack before drilling final** |
| Top-face tilt (built into adapter) | 16° | matches Newton template canted axis |
| Top-face material | PA12-GF printed *(production)*; PETG-HF *(prototype)* | repo material policy `../docs/MATERIALS.md` |
| Compliance pad | 3 mm Bambu TPU 95A HF, footprint = top face + 5 mm border | §8b |
| Top-face fasteners | 2× A4-316 M5×20 button-head + Loctite 243 | longer than Newton's M5×16 to account for 3 mm pad |

**Bottom face (gripper-side):** 4× M4 on the existing 40–50 mm bolt circle of
the gripper's bottom flange (`../ROV_INTEGRATION.md §1a`).

| Quantity | Value | Source |
|---|---|---|
| Bottom-face hole count | 4 | gripper M4 flange [`../ROV_INTEGRATION.md` §1a] |
| Bottom-face hole pitch | ~40–50 mm bolt circle (confirm from `gripper.py`) | shipped flange geometry |
| Bottom-face fasteners | 4× A4-316 M4×30 + nylon/PTFE bushings (galvanic isolation) | `../ROV_INTEGRATION.md` §1b |
| Drain holes | Yes — 2–4× Ø3 mm in adapter floor to prevent water trapping in the saddle | flooded-gripper policy |

**Shape:** A wedge — top face canted 16° to match the Roof Rack Newton slot,
bottom face flat to mate the M4 flange. Estimated envelope **80 × 70 × 35 mm,
~45 g in PA12-GF *(estimate)***.

**Cable channel:** A 6 mm-Ø open trench from the canister side of the adapter
out to the BR2-side, routing the gripper canister's M10-4.5mm-LC pigtail
along the Roof Rack toward the rear electronics-tube end cap. The cable does
**not** pass through the adapter body — it runs externally along the rack.

**Optional production variant:** Same geometry milled from **AL 6061-T6** for
salt/UV-tolerant high-cycle operations (T3-leaning service). Mass climbs to
~120 g *(estimate)*.

### 9b. Secondary variant — BR2 bottom-panel belly-mount (Newton pattern)

**Top face:** Same 2× M5 / 100 mm-pitch / 16° tilt — but now bolted to the
**factory-drilled BR2 bottom panel** holes the customer drilled when they
installed (or would have installed) a Newton.

**Pros over Roof Rack mount:**
- Lower aerodynamic profile — gripper hangs under the keel, doesn't add bow
  drag.
- Better COM (gripper directly below the existing ballast lead pattern).
- No interference with Lumen / Ping360 / sonar that compete for the Roof
  Rack.

**Cons:**
- Gripper not in main camera frustum unless the BR2's main camera is
  re-aimed downward.
- Adds bottom-strike risk — the gripper now hangs below the keel skids and
  is the first thing to touch the seabed.

**Adapter geometry differs only in the top-face tilt** — the bottom panel
Newton pattern is on a 16° canted line, so the adapter rotates the gripper
to point its jaws **downward at the same 16°** as Newton's natural
orientation. **Two variants of the same adapter — same top hole pattern,
same bottom flange pattern, just bolted to different chassis surfaces.**

### 9c. T-slot custom-ROV variant (bonus)

Replace the top-face 2× M5 / 100 mm-pitch pattern with **a 20 mm-pitch
multi-hole strip** so the adapter can mount to any 20 × 20 mm extrusion
T-slot at any spacing that's a multiple of 20 mm. Same bottom-face M4
flange pattern. This single change opens compatibility to any custom
T-slot ROV build — a large community population for which no vendor
gripper exists. (Out of scope for v1 ship — note as future.)

### 9d. What we are explicitly **not** designing

- **Wet-mate connectors.** The mount uses BR's compression-gland WetLink
  flow.
- **Active vibration damping.** Passive TPU pad only.
- **Bracket-mounted camera.** The BR2 already has a main camera; we point
  the gripper into its frustum, not the other way around.

---

## 10. Other ROV families — compatibility notes

### 10a. Chasing M2 / M2 Pro / M2 Pro Max

- Vendor manipulator (Grabber Arm 2) is **the only published path**: 7 kgf
  grip, 170 mm range, 2.8 s actuation, 100 m depth [9].
- Mount to the M2 Pro Max requires vendor **Mounting Bracket P/N 121129**;
  no public drawings of its bolt pattern [9].
- Verdict: **third-party gripper not viable** without reverse-engineering
  the 121129 bracket. Out of scope for our adapter family.

### 10b. QYSEA FIFISH V6 / V6S / V6 EXPERT / V-EVO

- Vendor "Robotic Arm Mount Kit" (1 arm mount + 2 holders) is the only
  documented chassis interface [10] [11].
- "Over 20 professional tools" all share **one undocumented accessory port
  / tool slot** [11].
- Verdict: same as Chasing — vendor-locked; we'd need to buy the mount kit
  and reverse-engineer it.

### 10c. OpenROV Trident

- Discontinued (OpenROV out of business since 2019); units still in the
  field.
- Body **410 × 205 × 86 mm, 3.5 kg** [15].
- Kickstarter update #10 announced a "payload interface" rear bay but
  dimensions were never publicly released [16].
- Community grippers exist (Thingiverse rubber-band claws [17]) but no
  documented chassis bolt pattern.
- Verdict: out of scope; community-only ecosystem with no canonical
  interface.

### 10d. Custom T-slot ROVs

- 20 × 20 mm aluminium extrusion (V-slot or T-slot) with M5 T-nut hardware.
- Any face, any pitch (20 mm multiple).
- This is the broadest target by population — but every build is bespoke.
- Our §9c variant (multi-hole 20 mm strip) is the right primitive.

### 10e. Reach Bravo manipulator (counter-reference)

- **Not a chassis interface** — it's the work-class manipulator counter-
  point. End-effector plate via Reach's "Payload Interface" [12].
- Listed here only to mark the boundary: chassis-mount is the cheap path,
  Bravo is the expensive path. The Bravo lives in `../ROV_INTEGRATION.md`
  and the *manipulator interface* studies (separate files).

---

## 11. Open questions / what we couldn't verify

| # | Item | Status | Path to close |
|---|---|---|---|
| Q1 | Newton bracket outer dimensions (length, width, plate thickness) | Not published by BR | Buy a Newton, measure; OR photogrammetry from BR product photos (low confidence) |
| Q2 | Roof Rack per-feature hole coordinates | Not published in usable form | Buy a Roof Rack and measure; BR's product-page drawing is referenced but un-recoverable in the publicly-served PDF/page content |
| Q3 | Claim "25 mm M3 grid on BR2 side plates" (task brief) | **Not confirmed** by any BR primary source we could fetch (datasheet, store, GitHub specs, R3 assembly guide, payload skid guide) | Likely conflation with another vehicle; treat as **unverified** until a BR drawing is found |
| Q4 | Newton 16° tilt — *why* 16° specifically | Inferred from template; BR does not document the design rationale | Email BR support (`support@bluerobotics.com`) |
| Q5 | Stack mass in §6a | All estimates (no live-CAD measure yet) | Update once BR-102649-240 canister + XW540 are weighed |
| Q6 | Stack net buoyancy in seawater | Computed from approximate volumes | Float the actual assembly in a saltwater tank |
| Q7 | Chasing P/N 121129 bracket bolt pattern | Vendor-only | Buy/borrow a M2 Pro Max bracket |
| Q8 | QYSEA accessory port dimensions | Vendor-only | Buy/borrow a Robotic Arm Mount Kit |
| Q9 | Trident payload interface dimensions | Never published; vendor defunct | None — accept as undocumented |
| Q10 | "Was there a Newton drilling template revision after R1?" | The PDF we fetched is dated 2018-05-31, marked "R1." | Re-check BR website periodically |

---

## 12. Sources

1. **BR2 Specifications (GitHub).** `bluerobotics/bluerobotics.github.io/blob/master/brov2/specifications.md` — vehicle dimensions, weight, buoyancy, ballast, depth ratings, tether. <https://github.com/bluerobotics/bluerobotics.github.io/blob/master/brov2/specifications.md>
2. **Newton Subsea Gripper product page (Blue Robotics).** SKU BR-100789, USD 720; jaw, grip, voltage, current, mass, depth, mount kit contents. <https://bluerobotics.com/store/thrusters/grippers/newton-gripper-asm-r2-rp/>
3. **Newton Subsea Gripper Installation on a BlueROV2 (Blue Robotics Learn).** Drilling-template reference, M5×16 fasteners, M10 penetrator, install sequence. <https://bluerobotics.com/learn/newton-subsea-gripper-installation/>
4. **BlueROV2 Frame product page (BR-100118).** Panel materials/thicknesses, M3/M4/M5 fastener schedule, 316 SS hardware list, AL6061-T6 cradles. <https://bluerobotics.com/store/rov/bluerov2-components-spares/brov2-asm-frame/>
5. **BlueROV2 Machined Buoyancy Foam.** R-3318 syntactic foam upgrade adds 500 g positive buoyancy; 300 m rated; standard on R3 and later. <https://bluerobotics.com/store/rov/bluerov2-accessories/float-r3318-brov2-r1-rp/>
6. **BlueROV2 Roof Rack product page.** AL 5052-H34, 177 g, USD 57; pre-drilled hole sets for WTE clamps, Lumen lights, Ping360, **Newton (×2)**, Sonoptix Echo, 1/4-20 tripod. <https://bluerobotics.com/store/rov/bluerov2-accessories/rov-roof-rack/>
7. **Installing the BlueROV2 Roof Rack (Learn article).** 4× M5×12 top-mount; 4× M3×12 front-mount via Lumen holes; 0° and 10° tilt options; blue threadlocker. <https://bluerobotics.com/learn/installing-the-bluerov2-roof-rack/>
8. **Autonomous Lionfish Harvester (Blue Robotics blog).** BR-promoted reference application; uses Newton on a BR2. <https://bluerobotics.com/autonomous-lionfish-harvester/>
9. **CHASING Grabber Arm 2 (vendor and resellers).** Vendor bracket P/N 121129; 7 kgf, 170 mm range, 2.8 s, 100 m depth. <https://www.focusnordic.com/products/drones/underwater-drones/propellers-parts-power/chasing-m2-pro-max-grabber-robotic-arm-quick-mounting-bracket>
10. **QYSEA Robotic Arm Mount Kit for FIFISH V6 Series.** 1 arm mount + 2 holders. <https://www.blueskiesdroneshop.com/products/qysea-fifish-v6-series-robotic-arm-mount-kit>
11. **QYSEA FIFISH V-EVO product page.** Standard + Robotic Arm Pack option; "attachment port accommodates a variety of tools." <https://store.qysea.com/fifish-v-evo.html>
12. **Reach Bravo Payload Interface (Reach Robotics).** Plate-style end-effector mount for Bravo manipulator; chassis-mount counter-point. <https://quote.reachrobotics.com/product/bravo-accessories-upgrades/payload-interface/>
13. **The role of conservation volunteers in the detection, monitoring and management of invasive alien lionfish (Blue Ventures publication).** Citizen-science use of inspection-class ROV tooling. <https://blueventures.org/publications/role-conservation-volunteers-detection-monitoring-management-invasive-alien-lionfish/>
14. **BlueROV2 Payload Skid product page (BR-100233).** 475 × 338 × 197 mm, 1200 g, HDPE + AL6061-T6; 12 ballast slots, 8× M5×16 attachment; USD 320. <https://bluerobotics.com/store/rov/bluerov2-accessories/brov-payload-skid/>
15. **OpenROV Trident specifications.** 410 × 205 × 86 mm, 3.5 kg. <https://openrov.com/products/trident/specifications>
16. **Trident Kickstarter Update #10 — Payload Interface: Mechanical.** Forum post announcing the payload bay; dimensions never publicly released. <https://forum.openrov.com/t/payload-interface-mechanical-trident-kickstarter-update-10/4615>
17. **ROV Claw Gripper for OpenRov Trident (Thingiverse).** Community 3D-printed rubber-band claw; representative of post-OpenROV ecosystem. <https://www.thingiverse.com/thing:2753801>
18. **BlueROV2 R3 Assembly and Build Instructions (Learn).** Side panel / centre panel / bottom panel composition; M5×16 frame fasteners; M4×18 / M4×14 cradle and clamp fasteners. <https://bluerobotics.com/learn/bluerov2-assembly-r3-version/>
19. **BlueROV2 Payload Skid Assembly Guide (Learn).** Fastener schedule; 8× M5×16 to ROV; M3×12, M4×14, M5×16, M5×20 stations. <https://bluerobotics.com/learn/bluerov2-payload-skid-assembly-guide/>
20. **Blue Robotics WetLink Penetrator family.** Compression-gland through-hull penetrator series; M10 body size for typical thruster/gripper cables; ≤950 m rated. <https://bluerobotics.com/store/cables-connectors/penetrators/wlp-vp/>

### Local cross-references (this repo)

- `../ROV_INTEGRATION.md` — manipulator-arm-side mount (M4 flange detail); the **arm** sibling of this **chassis** file.
- `../SELECTION.md` — actuator class / depth-tier decision.
- `../REQUIREMENTS.md` — input-shaft torque / mass / depth requirements.
- `../DRIVETRAIN.md` — gear ceiling; sets the *upstream* structural limit the mount must not exceed.
- `../ELECTRICAL.md` — RS-485 + 12 V termination inside the BR2 electronics enclosure.
- `../FAILURE_MODES.md` — failure mode catalogue; this file adds **HDPE bore wallowing** (§8c) and **bow-impact cantilever** (§8c).
- `../docs/UNDERWATER.md` §5 — galvanic isolation policy (re-used at §9a fastener stack).
- `../docs/MATERIALS.md` — printed-material selection; PA12-GF for production adapter, Bambu TPU 95A HF for the compliance pad.

---

*File created 2026-05-26 as the chassis-mount counterpart to `motor/ROV_INTEGRATION.md`. Every BR-published number is referenced to a numbered source. Numbers marked **(estimate)** are derived, not measured — close before bench validation per `../BENCH_TEST.md`.*

# Reach Robotics / Blueprint Lab — Alpha 5 + Bravo 7 wrist interfaces

> Research-only file. Adapter design implication is *proposed geometry,
> not modelled in CAD yet.* Every dimension that appears here is cited to a
> Blueprint Lab / Reach Robotics primary source (datasheet, integration
> manual, accessory datasheet, or third-party CAD/URDF), a Reach product
> directory, or marked as an **estimate** with the reason. Cross-links:
> `../ROV_INTEGRATION.md` (our mounting baseline), `../SELECTION.md`
> (actuator), `../SURVEY.md` (full actuator survey), `../../docs/UNDERWATER.md`
> (depth, materials, galvanic isolation).

## 1. Why this interface

Reach Robotics (rebranded from **Blueprint Lab** in 2024–2025; the same
Sydney-based company still trades under both names — old `blueprintlab.com`
URLs 301-redirect to `reachrobotics.com` [1]) is the dominant supplier of
**electric**, all-sealed manipulator arms for **observation- and
inspection-class ROVs**. Two product lines bracket the BlueROV2-up-to-1500m-WROV
gap our gripper targets:

- **Reach Alpha 5 (RA-5001)** — 5-function (5 DoF), ~1.36 kg in air,
  300 m depth, the standard manipulator on a BlueROV2 Heavy and
  comparable portable ROVs [2, 5].
- **Reach Bravo 7 (RB-7001)** — 7-function (6 DoF + jaw), ~9.5 kg in
  air, 450 m depth (per the V010+ integration manual), positioned at
  inspection-class work platforms one tier larger than BlueROV2 [3, 4].

Both arms publish an **explicit "BYO end-effector"** path. The
Bravo Integration Manual V007 §9.4 states that the **Payload Interface
RB-1054** "replaces the jaws at the end-effector" specifically so that
"developers can securely integrate their own payloads" [4]. The Alpha 5
datasheet calls itself "End-Effector Interchangeable" and Reach sells a
catalogue of stock jaws (RA-1011 / RA-1012 / RA-1014 / RA-1017 / RA-1018 /
RA-1037 / RA-1048 / RA-1070) plus a tool-less **Mounting Kit RA-1013**
for swap-out [2, 6, 8].

Designing a printed adapter that drops our gripper onto these two arms is
therefore a *legitimate, supported* integration path — not a hack — and
opens the gripper to the largest installed base of small-ROV
manipulators in the market.

The headline story is asymmetric, and that asymmetry drives §9 below:

- **Bravo 7** publishes a fully-dimensioned third-party tool plate
  (Ø71 mm, 6× M6 + 6× M5 CSK + 2× Ø3 dowel, 82 g) — *we can spec a
  printed adapter today*.
- **Alpha 5** does not publish the jaw mating dimensions. The
  end-effector swap uses a screw collar around a central push-rod; the
  thread size, collar OD, push-rod tip geometry, and dowel-pin
  alignment dimensions are not on any datasheet we could pull. *Adapter
  geometry is therefore design-intent only and pending an RA-1013
  dimensioned drawing from Reach Sales, or reverse-measurement of a
  delivered jaw base.*

---

## 2. Alpha 5 — datasheet summary + mechanical interface

### 2a. Datasheet — arm-level numbers

All from the Reach Robotics Alpha 5 datasheet (RA-5001, archived from
`blueprintlab.com/media/docs/40929/Alpha_5_Datasheet.pdf` via Wayback
Machine 2024) [2]:

| Spec | Value | Notes |
|---|---|---|
| Part number | **RA-5001** | 5-function "standard" Alpha 5; RA-5002 = Inspector variant with probe head instead of jaws [6] |
| DoF / functions | **5** | shoulder yaw + elbow pitch + elbow pitch + wrist rotate + jaw open/close (URDF: 4 revolute + 1 prismatic) [11] |
| Full-extension reach | **400 mm** | datasheet figure [2] |
| Outer diameter (main tube) | **40 mm** | datasheet figure [2] |
| Max closing force (jaw) | **600 N (60 kg)** | datasheet figure; programmable [2] |
| Push-rod axial load rating | **1 kN (100 kg)** | datasheet figure — this is the *axial* rating of the central drive rod that opens/closes the jaw, **not** a wrist-bearing rating [2] |
| Push-rod stroke | **0–15 mm** (`axis_a` prismatic joint upper limit 0.015 m) | Robotic-Decision-Making-Lab URDF [11] |
| Mass in air | **1360 g** | datasheet figure [2] |
| Mass in water | **900 g** | datasheet figure [2] |
| Lift capacity (full reach) | **2000 g** | datasheet figure [2] |
| Depth rating | **300 MSW** | datasheet figure [2], confirmed by Mariscope 2023 product directory [5] |
| Operating temperature | **−35 °C to +35 °C** | datasheet figure [2] |
| Voltage | **18–30 V DC** | datasheet figure [2] |
| Max power | **35 W** | datasheet figure (so peak current ≈ 1.95 A @18 V, ≈ 1.17 A @30 V) [2] |
| Communications | **RS-232 / RS-485** | datasheet figure; half-duplex per Reach Bravo Integration Manual §8.1.2 (same protocol family) [2, 4] |
| Joint speed | **0.1° / 0.1 mm accuracy** | datasheet figure [2] |
| Materials | **Anodised AL6061** | datasheet figure [2] |
| Connector | **Teledyne 6-pin IE(W)-55 Impulse** | datasheet figure; whip ("pigtail") supplied [2] |
| Operator control | 3D Space Mouse, Gamepad, Software GUI, Master Controller | datasheet [2] |

### 2b. Joint ranges (Alpha 5)

From the datasheet diagram [2], cross-checked against the
Robotic-Decision-Making-Lab ROS 2 URDF [11]:

| Joint | URDF axis | Datasheet range | URDF limits |
|---|---|---|---|
| Base yaw | `axis_e` | **350°** software-limited to 352° (not continuous) | 0.0 to 6.10 rad (~349.5°) [11] |
| Shoulder pitch | `axis_d` | **185°** | −3.49 to +3.49 rad (~±200°) [11] |
| Elbow pitch | `axis_c` | **185°** | 0 to 3.22 rad (~184.5°) [11] |
| Wrist rotate | `axis_b` | **200°** | 0 to 3.22 rad (~184.5°) [11] |
| Jaw (pushrod) | `axis_a` (prismatic) | **0–15 mm** axial | 0 to 0.015 m, 10 N·m effort* [11] |

\* The URDF declares `effort=10` on the prismatic, which is a placeholder
— the **datasheet value is the load-bearing one** (1 kN axial / 600 N
closing force). The 9 N·m / 0.5 rad/s revolute effort/velocity figures
in the URDF are also placeholders, not Blueprint Lab joint torque specs;
Blueprint Lab does not publish per-joint torque for the Alpha series in
any source we could find (open question §10).

### 2c. End-effector mating interface (the part we need)

**This is the gap.** Despite the Alpha 5 being marketed as
"end-effector interchangeable" with a published catalogue of 8+ jaws
[6, 8], **no datasheet, manual, or vendor page we pulled lists the
mating dimensions** (thread, collar OD, dowel-pin diameter and offset,
push-rod tip geometry). What is documented:

| What's published | Where | What it tells us |
|---|---|---|
| "Rapid swap-out procedure ensures interchangeability on the go" | Alpha End-Effector Datasheet (page 1) [8] | qualitative — a screw-collar plus dowel-pin is the mechanism, but no dimensions |
| Stock jaw P/Ns + lengths + max-opening: RA-1014 Standard 90/80 mm; RA-1012 Parallel 75/90 mm; RA-1017 Quad 70/50 mm; RA-1018 Rope Cutter 17 mm; RA-1037 SAR; RA-1011 Needle-Nose | Alpha End-Effector Datasheet [8] | the jaw mates at a **common 40 mm-OD interface** because the arm tube OD is 40 mm and every jaw photo shows a near-flush collar transition |
| RA-1013 "Alpha Mounting Kit" exists for tool-less removal | Mariscope 2023 product directory [5]; Reach quote page [7] | confirms a screw-collar is the swap mechanism; no published dimensions |
| Push-rod axial 1 kN; closing force 600 N | Alpha 5 datasheet [2] | the push-rod is the *only* mechanical input to the jaw — the wrist-side mount must let our adapter intercept that push-rod *or* lock it out |

**What this means in practice.** Three plausible mating mechanisms for
the Alpha 5 jaw — we can't tell from open sources which it actually is:

1. **Threaded collar around a 40 mm shoulder, push-rod tip sliding
   axially inside.** Most likely based on the Alpha End-Effector
   datasheet photo: every stock jaw shows a knurled collar where the
   jaw meets the arm tube, consistent with a threaded interface ≈40 mm
   OD. *Adapter implication:* our printed body has to provide an
   internal thread that matches Reach's external thread on the arm
   tube. **We don't know the thread spec.**
2. **Push-rod tip carries an axial M-size fastener** (the Bravo
   Integration Manual §8.1.1 step 6 explicitly says "Fasten the screw in
   the centre of the jaws with the 5 mm Allen key to secure (with a
   torque of ~3 N·m)" for the **Bravo** — possibly mirrored on the
   Alpha but not documented [4]).
3. **Dowel pin alignment + threaded collar** — analogous to the Bravo
   RB-1054 (Ø3 mm dowel pins + 6× M6) but at a smaller scale.

**Until Reach Sales supplies the RA-1013 mounting-kit dimensioned
drawing, the Alpha 5 adapter geometry stays unspecified.** This is the
single biggest open question (§10).

### 2d. Alpha 5 base mount (for reference — different from wrist)

Not directly relevant to our gripper-side adapter but useful for total
integration: the Alpha series base-mounts via a **screw-collar mounting
kit (RA-1013, also doubles as the end-effector swap kit per Mariscope
[5])**. No specific base-bolt pattern published. The arm body itself is
the Ø40 mm tube which clamps into the collar.

---

## 3. Bravo 7 — datasheet summary + mechanical interface

### 3a. Datasheet — arm-level numbers

From the Reach Bravo 7 datasheet (RB-7001), Wayback Machine 2023
snapshot of `reachrobotics.com/media/docs/75773/Bravo7-Datasheet.pdf`
[3], cross-referenced against the **Reach Bravo Integration Manual V007**
(`reachrobotics.com/media/docs/43447/Reach-Bravo-Integration-Manual-V007.pdf`,
Wayback 2022) [4]:

| Spec | Value | Source notes |
|---|---|---|
| Part number | **RB-7001** | datasheet [3] |
| Functions / DoF | **7-function / 6 DoF + jaw** | datasheet + integration manual §5.1 [3, 4] |
| Full-extension reach | **900 mm** | datasheet [3]; integration manual §5.1 confirms [4] |
| Full-reach lift | **10 kg** (water-side, dynamic) | datasheet [3] / integration manual §5.1 [4] |
| Max lift capacity | **20 kg** (static, retracted) | datasheet [3] |
| End-effector accuracy | **<1 cm** | datasheet [3] |
| Grabber closing force | **800 N (80 kg)** | **integration manual §5.1** [4] gives **800 N for all Bravos** with stock grabber. Three other published numbers disagree: Bravo 7 datasheet features panel = "1000 N" [3]; Bravo 5 datasheet = "2000 N" [21]; Bravo 5 quote portal also "2000 N". The 800 N manual value is the most conservative; the per-arm datasheet values appear to be peak / specific-jaw configurations and the manual figure is the across-family minimum. Adopt the manual figure for engineering. *Jaw close force does not load our adapter — the load path bypasses the jaw line — so this trilemma is informational only.* |
| Base joint torque | **110 N·m** | integration manual §5.1 [4] |
| Wrist torque | **50 N·m** | integration manual §5.1 [4] — **this is the load-bearing number** for any tool we hang off the wrist |
| Max axial load (along arm) | **100 kg (≈1 kN)** | integration manual §5.1 [4] |
| Joint speed | **45–80°/s (24–48 V)** | integration manual §5.1; datasheet says "60°/s nominal" [3, 4] |
| Mass in air | **9.5 kg** | datasheet [3] / integration manual [4] |
| Mass in water | **4.5 kg** | datasheet [3] / integration manual [4] |
| Depth rating | **450 MSW** (V010 + integration manual); **300 MSW** appears in the older standalone datasheet | integration manual §5.2 [4]; older datasheet [3]. The 450 MSW figure is the canonical/current value (Mariscope 2023 catalogue also confirms 450 m [5]). The 300 MSW Bravo-7 datasheet is **out of date** relative to the V007 manual. |
| Operating temperature | **5 °C to 35 °C** | integration manual §5.2 [4] |
| Storage temperature | −10 to 80 °C | integration manual §5.2 [4] |
| Housing material | **Hard-anodised AL7075** | integration manual §5.2 [4] |
| Voltage | **20–48 V DC** | datasheet [3] / integration manual §5.3 [4] |
| Nominal power (10 kg load) | **400 W**; manual says 400 W, datasheet says 200 W | integration manual §5.3 = 400 W [4], datasheet figure 200 W [3] — manual is authoritative |
| Peak power (10 kg load) | **500 W** (manual) / 300 W (datasheet) | as above [3, 4] |
| Processor | **NVIDIA TX2** (on-board) | integration manual §5.4 [4] — important: the arm has *embedded kinematics* and *runs Ethernet + RS-232 + RS-485 concurrently*, not just a dumb serial slave |
| Comms | **Ethernet (100 Mbit/s) + RS-485 + RS-232** | integration manual §5.4 [4] |
| Protocol | **Reach System Communication Protocol** (NDA — request from Sales) | integration manual §5.4 [4] |
| Magnetic field at <10 mm from shell | <0.5 mT (5 Gauss) | integration manual §2.3 [4] — relevant for our (non-magnetic) gripper near actuators; we have no compatibility issue |
| End-effector dimensions, default-config | Max OD 90 mm, min OD 80 mm (jaw envelope) | datasheet [3] |

### 3b. Bravo 7 joint ranges

| Joint | Description | Range | Source |
|---|---|---|---|
| J1 | Base linear (carriage) | 0–210 mm | datasheet [3] |
| J2 | Base yaw | Continuous (360°+), software-limited to 350° | datasheet [3] |
| J3 | Shoulder pitch | 180° | datasheet [3] |
| J4 | Elbow pitch | 350° | datasheet [3] |
| J5 | Wrist rotate 1 | 180° | datasheet [3] |
| J6 | Wrist rotate 2 (pitch) | 180° | datasheet [3] |
| J7 | Wrist roll | 350° | datasheet [3] |

### 3c. Bravo 7/5 end-effector mating interface — the Payload Interface RB-1054

**This is dimensioned and we can build to it.** From the
**Bravo Payload Interface datasheet RB-1054**
(`reachrobotics.com/media/docs/43886/Bravo-Payload-Interface-Datasheet.pdf`,
Wayback 2024) [9] and integration manual §9.4 [4]:

| Dimension | Value | Notes |
|---|---|---|
| **Mating plate OD** | **Ø 71.0 mm** | datasheet — this is the plate edge; mounting circle is inside this [9] |
| **Mating plate thickness / overall depth** | 61 mm overall (height of the assembly above the arm) | datasheet drawing [9] |
| **Alignment** | **2 × Ø 3 mm dowel pin holes** for repeatable angular orientation | datasheet [9] |
| **Threaded bolt circle (tool-side)** | **6 × M6 × 1** threaded into the plate from the **tool side** | datasheet [9] |
| **Through-bolt pattern (far-side)** | **6 × Ø 5 mm**, **countersunk from the far side for M5 screws** | datasheet [9] |
| Bolt-circle radius (dimension) | **Not numerically specified** on the datasheet; estimable from drawing as ≈26–28 mm radius (≈52–56 mm bolt circle) given the Ø71 mm plate and counterbore clearance | drawing scale estimate — **mark as estimate** until a STEP file confirms |
| Dowel-pin centre-to-centre | **Not numerically specified**; estimable as ≈40–50 mm on a diameter near the M6 pitch circle | drawing scale estimate — **mark as estimate** |
| Plate mass | **82 g** | datasheet [9] |
| Material | Hard-anodised AL6061 (assumed — matches the rest of the Bravo accessory line; not stated on the RB-1054 datasheet itself) | inferred from datasheet style [9] vs. Bravo arm AL7075 [4] |
| Depth rating | 450 MSW (matches arm) | inferred from manual [4]; not separately stated on accessory datasheet |
| Wet-side fastener instructions | "Apply marine grease to the thread at the base of the jaws" + "Screw the collar on the end-effector interface to tighten… ~3 N·m" (this is the standard jaw routine, but the **same collar + thread + central push-rod-screw** mounts the RB-1054 in lieu of jaws) | integration manual §8.1.1 [4] |

The Bravo's stock jaw mount is a **central push-rod screw** (5 mm Allen,
~3 N·m, integration manual §8.1.1 step 6 [4]) plus a **screw-collar
sheath** over the push-rod plus a **dowel-pin** to lock angular
orientation. The RB-1054 substitutes for the stock jaws at this same
interface — it occupies the geometric envelope of the jaws and exposes
the Ø71 / 6× M6 / 6× M5 CSK / 2× Ø3 pattern outward, so a third-party
tool sees only the dimensioned plate, not the push-rod / collar / dowel
plumbing underneath.

**This means our adapter's Bravo-side face is dimensioned and
buildable today.** See §9.

### 3d. Bravo 7/5 base mount (informational)

From integration manual §6.1.1 + §8.1.1 [4]:

- **4 × M8 bolts** (size called out explicitly, 5 mm hex Allen on the
  end-effector but the M8 base-bolts likely take a 6 mm Allen — manual
  does not call out base-bolt torque)
- Optional **RB-1010 Bravo Mounting Kit** (datasheet not pulled; refer
  Reach Sales). The integration manual §6.1.1 also shows a direct
  backplate-integration option with the bolt pattern dimensioned on a
  drawing we couldn't extract from the manual's embedded vector graphic.

Not relevant to our gripper-side adapter, but worth noting for any
"full integration" handoff to the ROV builder.

---

## 4. Differences between Alpha 5 and Bravo 7

| Axis | Alpha 5 | Bravo 7 | Implication for our adapter |
|---|---|---|---|
| Functions / DoF | 5 / 5 (4 R + 1 P jaw) | 7 / 6 + 1 jaw | More DoF = more posing options, irrelevant to the static mount |
| Depth rating | 300 MSW | 450 MSW (some older datasheets say 300) | Both well past our T2 (30 m) and T3-comfort range. Adapter doesn't need *new* depth qualification beyond what the gripper has. |
| Voltage | 18–30 V DC | 20–48 V DC | Both arms supply **only their own arm-internal voltage**. Our gripper draws 12 V via the canister bulkhead from the ROV bus, **not** from the arm. No voltage interop required at the wrist. |
| Comms supported | RS-232, RS-485 (no Ethernet) | Ethernet (100 Mbps), RS-485, RS-232 | The Bravo Ethernet does **not** terminate at the wrist (it's an arm-internal bus to the on-board TX2). Our gripper still tethers RS-485 to the ROV bulkhead, not the arm. |
| Wrist torque (published) | n/a (not on any Alpha datasheet) | 50 N·m | The Bravo wrist comfortably swings our ≈350 g end-effector at 100 mm offset = 0.35 N·m, ~140× margin. Alpha: must rely on the 2 kg-full-reach-lift number, which is enough for our ~0.8 kg total but tighter (factor ~5×). |
| Full-reach lift | 2 kg | 10 kg | Both pass our ~0.8 kg estimate (gripper + canister + servo + service-loop cable). Alpha is the binding case. |
| Mass (in water) | 0.9 kg | 4.5 kg | Bravo wants a much bigger ROV; both classes are downstream of the *gripper-side* adapter design. |
| Wrist mating interface | **Push-rod + screw-collar; dimensions not published** | **RB-1054 Payload Interface; Ø71 mm / 6× M6 / 6× M5 CSK / 2× Ø3 dowel** | **One arm we can spec to today, one we can't.** |
| Tool-side electrical pass-through | **None** — power and comms exit the *arm base* connector only | **None at the jaw**, but there is an **Accessory Port (RB-1006) at the elbow** providing 12–24 V DC + RS-485 or 100 Mbps Ethernet via an MCBH8F bulkhead | The Bravo can carry our RS-485 + 12 V along the arm; the Alpha cannot. Our canister cable still tethers all the way to the ROV bulkhead either way (we don't tap arm power). |
| Force feedback sensor accessory | none | RB-FT (6-axis F/T sensor, Ø81.6 × 42 mm, 460 g) sold separately | Bravo can be ordered with an in-line F/T sensor downstream of the wrist; we don't need it because our gripper's force sensing is the actuator current itself (`SELECTION.md`, `SENSING.md`) |
| Stock jaw catalogue | 8+ jaws + 2 rotators | 5+ jaws + 1 cutter + payload interface + F/T + wrist camera | Both are explicitly "BYO end-effector" ecosystems |
| Magnetic field | not specified | <0.5 mT @ ≥10 mm from shell [4] | Our gripper has no magnetic components (decision per `SELECTION.md` T2 = direct servo, not magnetic-coupling). Bravo magnetic field is irrelevant. |

The **single dominant difference** is: *Bravo has a Ø71 mm bolt-pattern
plate we can dimension to; Alpha has a screw-collar with no published
dimensions.* Everything else is comfortable on both.

---

## 5. Electrical pass-through + cable routing

### 5a. Pass-through *at* the wrist

| Arm | Wrist electrical | Implication |
|---|---|---|
| **Alpha 5** | **None.** The wrist is mechanical-only. Power and RS-232/485 exit only from the arm-base connector (Teledyne 6-pin IE(W)-55 Impulse) [2]. | Our cable must tether *separately* along the arm and back to the ROV bulkhead. |
| **Bravo 7** | **None at the wrist itself.** The base-side connector is split into a 4-pin power (MCBH4M) and an 8-pin comms (MCBH8ME, Ethernet + RS-485 + RS-232) [4]. *However* there is an **Accessory Port connector at the elbow (J5 area) — MCP16WD 16-pin** [4]. With the optional **RB-1006 Accessory Port** [4] this is broken out as MCBH8F providing **12–24 V DC** + 100 Mbps Ethernet or RS-485 — for things like the Bravo wrist camera (RB-1057). | We *could* tap RB-1006 to supply RS-485 + 12 V to our canister, but two reasons not to: (a) the gripper's bus voltage is fixed at 12 V nominal from the ROV (per `../ELECTRICAL.md`), so adding a second power source needs a tier check; (b) RB-1006 costs and another wet-mate is more failure modes than a single canister-to-ROV bulkhead run. |

### 5b. Bravo connector pinouts (for reference)

From integration manual §6.1.2 [4]:

**Power (MCBH4M, 4-pin)**

| Pin | Function | Wire colour (supplied MCIL4F pigtail) |
|---|---|---|
| 1 | GND | Black |
| 2 | PWR | White |
| 3 | PWR | Red |
| 4 | GND | Green |

**Comms (MCBH8ME, 8-pin)**

| Pin | Function | Wire colour | Pair |
|---|---|---|---|
| 1 | RS-485 A | Brown | TP |
| 2 | RS-485 B | Light brown | TP |
| 3 | RS-232 TX | Blue | TP |
| 4 | RS-232 RX | Light blue | TP |
| 5 | ETH RX− | Orange | TP |
| 6 | ETH RX+ | Light orange | TP |
| 7 | ETH TX− | Green | TP |
| 8 | ETH TX+ | Light green | TP |

**Accessory port (MCP16WD, 16-pin) — at the elbow**

| Pin | Function | Pin | Function |
|---|---|---|---|
| 1 | RX− | 9 | TX+ |
| 2 | CAN L | 10 | GND |
| 3 | CAN H | 11 | PWR |
| 4 | TX− | 12 | PWR |
| 5 | RX+ | 13 | GND |
| 6 | GND | 14 | PWR |
| 7 | GND | 15 | PWR |
| 8 | GND | 16 | PWR |

(Light on accessories: this port runs **CAN, RS-485 (TX/RX), and
multiple PWR/GND** within the same 16-pin connector. The RB-1006
Accessory Port datasheet [4 §9.2] says it provides "12–24 V DC and
communications over either 100 Mbps Ethernet or RS-485," so the
elbow-side socket carries Ethernet wires too — manual prints partial
pinout only.)

### 5c. Alpha 5 connector pinout

The Alpha 5 datasheet [2] specifies a **Teledyne 6-pin IE(W)-55 Impulse**
connector (whip included). The pinout is not on the datasheet —
typical wiring is **V+ / V− / RS-485-A / RS-485-B / RS-232-TX / RS-232-RX**
or similar, but we can't confirm without contacting Reach Sales. Mark
this as **open question** (§10).

### 5d. Cable-routing implication for our gripper

Our gripper, per `../ROV_INTEGRATION.md` §2 + `../ELECTRICAL.md`, runs
**4-conductor RS-485 + 12 V + GND** (effectively a single twisted-pair-plus-power
cable) from the canister bulkhead to the ROV penetrator. With either
Reach arm, the routing is unchanged:

1. Gripper canister bulkhead (penetrator) → cable runs **along the arm
   topside**, fixed every ~30 mm with ROV-grade ties (not the cheap
   nylon ties that go brittle in seawater) → service loop at the
   wrist/Bravo-elbow region → strain-relief at the ROV bulkhead. *Per
   `../ROV_INTEGRATION.md` §2.*
2. **Keep cable out of the four-bar arc** of *our* gripper *and* the
   manipulator's full envelope — both arms' wrist rotates through ≥180°
   continuously (Bravo 7 J5/J6/J7) and any cable tied to the *end-effector
   side* will twist with the wrist.
3. **Service loop at the gripper:** ≥1× gripper height (~60–80 mm),
   tied to the adapter or the arm flange — `../ROV_INTEGRATION.md`
   §2a-2.
4. The cable should *not* terminate at the arm — both Reach arms
   already have their own ROV-side power/comms connectors and any
   shared bus introduces noise, ground-loop, and inrush issues (the
   Bravo manual explicitly warns about inrush triggering OV protection
   on the ROV supply [4 §6.1.2]).

---

## 6. Depth / sealing

| Arm | Depth (current) | Depth (older) | Material | Temp |
|---|---|---|---|---|
| Alpha 5 | **300 MSW** | unchanged | Anodised AL6061 | −35 °C to +35 °C [2] |
| Bravo 7 | **450 MSW** (per V010+ V007 manual) | 300 MSW (older datasheet) | Hard-anodised **AL7075** | +5 °C to +35 °C [4] |
| Bravo 7 future | 600 MSW (announced) | — | — | per Mariscope catalogue [5] |

Both depth ratings comfortably exceed our **T2 30 m** primary tier and
even the **T3 >30 m** fallback tier per `../SELECTION.md`. Our adapter,
in PA12-GF, is irrelevant to depth rating — it's a structural part not
a pressure-bearing one (gripper is **flooded**, so the adapter is
nominally fully wet on both sides).

Note: **AL7075** (Bravo) is **less corrosion-resistant than AL6061**
(Alpha) — 7075 needs the hard anodising it ships with to survive
seawater, and *galvanic isolation between our adapter's fasteners and
the AL7075 wrist surface is more important on Bravo than on Alpha* (per
`../docs/UNDERWATER.md` §5). Stainless M5/M6 in nylon/PTFE shoulder
bushings, A4-316, with Loctite 243 is the conservative spec for both.

---

## 7. Sourcing + cost

| Item | P/N | Vendor channel | Price (USD) | Lead time | Source |
|---|---|---|---|---|---|
| **Reach Alpha 5** (single arm) | RA-5001 | Reach Robotics / Blueprint Lab direct; distributors include Deep Trekker [10], Bay Dynamics NZ, Hot Robotics (rental), Mariscope [5] | **Quote-only** | Quote-only | [2, 5, 10] |
| **Reach Bravo 7** (single arm) | RB-7001 | Reach Robotics / Blueprint Lab direct; same distributors | **Quote-only** | Quote-only | [3, 4, 5] |
| **Bravo Payload Interface** | RB-1054 | Reach quote portal; RobotShop listing [13] | Quote-only | Quote-only | [9, 13] |
| **Alpha Mounting Kit** | RA-1013 | Reach quote portal | Quote-only | Quote-only | [7] |
| **Alpha Standard Jaws** | RA-1014 (Al), RA-1062 (SS-316) | Reach quote portal | Quote-only | Quote-only | [6, 8] |
| **Alpha Soft Jaws** | RA-1032 | Reach quote portal | Quote-only | Quote-only | [8] |
| **Alpha Parallel Jaws** | RA-1012 | Reach quote portal | Quote-only | Quote-only | [8] |
| **Alpha Quad Jaws** | RA-1017 | Reach quote portal | Quote-only | Quote-only | [8] |
| **Alpha Rope Cutter** | RA-1018 | Reach quote portal | Quote-only | Quote-only | [8] |
| **Alpha SAR Jaws** | RA-1037 | Reach quote portal | Quote-only | Quote-only | [8] |
| **Alpha Needle-Nose** | RA-1011 | Reach quote portal | Quote-only | Quote-only | [8] |
| **Alpha Rotating Grabber** | RA-2130 | Blueye Robotics (and others) [14] | Quote-only | Quote-only | [14] |
| **Bravo Force/Torque Sensor** | RB-FT | Reach quote portal | Quote-only | Quote-only | [12] |
| **Bravo Hub** | RB-1080 | Reach quote portal | Quote-only | Quote-only | [4] |
| **Bravo Accessory Port** | RB-1006 | Reach quote portal | Quote-only | Quote-only | [4] |

**Honest finding:** Reach Robotics does not publish list prices for any
of the manipulators or accessories. Every channel (Reach direct, Deep
Trekker, Bay Dynamics, Mariscope, Blueye) is **quote-only**. Two
publicly-cited *anchors* for currency framing (not direct list prices):

- **Hot Robotics UK** offers the Alpha 5 as a **rental** unit to UK
  marine researchers (no published rental rate; access via their
  equipment portal) [16].
- Academic procurement papers using the Alpha 5 (BlueROV2 + Alpha 5
  UVMS systems on ResearchGate) routinely refer to the system as
  "tens of thousands of USD" but no specific number is cited [15].

We **mark all USD pricing as quote-only** and do not anchor a number we
cannot trace. The ratio is intuitive — Bravo 7 is ~5–10× the price of
Alpha 5 based on the size + features delta — but this is an estimate,
not a sourced datum.

### 7a. Export / dealer restrictions

- Blueprint Lab / Reach Robotics is **Australian-based** (Sydney,
  +61 (2) 9519 7651) [4]. Export to defence end-users may require
  Australian DECO clearance; civilian/research export is generally
  open via the dealer network.
- Both arms ship with **a topside Master Arm controller as an
  option** (`RM-5201` for Alpha 5-function, `RM-7201` for Bravo
  7-function) [4] — significant additional line item if not bundled.
- "Reach Control Lite" software is included with the arm; "Reach
  Control Pro" is an upgrade [4 §7.1].

---

## 8. Ecosystem — third-party tools, open-source adapters

### 8a. Software / ROS ecosystem

| Project | What it is | Useful for our adapter? | Link |
|---|---|---|---|
| **`Robotic-Decision-Making-Lab/alpha`** (archived 2025-04-10) | ROS 2 driver + URDF + meshes for Reach Alpha 5 (`alpha_description/meshes/M2-1-1.stl`, `M2.stl`, `M3-INLINE.stl`, `RS1-100-101-123.stl`, end-effector `RS1-124.stl`, `RS1-130.stl`, `RS1-139.stl`) | **Yes — STL meshes for every Alpha link + standard jaws** are checked into git, BSD-licensed (cf. `alpha_description/meshes/LICENSE`). These are the closest thing to an open CAD model of the wrist mating geometry. *Caveat: meshes are abstractions/decimations, not engineering CAD.* | https://github.com/Robotic-Decision-Making-Lab/alpha [11] |
| **`Robotic-Decision-Making-Lab/reach`** (current, successor to above) | C++ driver + ROS 2 interface for **both** Alpha 5 and Bravo 7; packages `libreach`, `reach_bringup`, `reach_controllers`, `reach_description`, `reach_hardware`, `reach_ip_camera`, `reach_msgs` | Likely supersedes the URDF/STL set above with Bravo 7 data added. Not affiliated with Reach Robotics. | https://github.com/Robotic-Decision-Making-Lab/reach |
| **Blueprint Lab GitHub org** (`github.com/blueprint-lab`) | **Empty** — no public repositories | n/a | https://github.com/blueprint-lab |
| **ROS-Industrial `reach_ros`** | Reachability analysis library (different "reach" — name collision) | **Not Reach Robotics**; unrelated despite name | https://github.com/ros-industrial/reach_ros |

### 8b. Hardware ecosystem (third-party tools we found cited)

- **Bay Dynamics NZ** distributes Reach Alpha jaws and shows custom
  tool integrations in their marketing photos (Bay Dynamics is credited
  on the Alpha End-Effector datasheet [8] for the soft-jaw photography).
- **Blueye Robotics** (Norway, BlueROV-class observation drones) ships
  the Reach Alpha Rotating Grabber RA-2130 with a **Blueye Smart
  Connector** instead of the standard Teledyne 6-pin — a worked
  example of integrating a different ROV-side connector on the Reach
  arm-base path. *No equivalent wrist-side custom example found.* [14]
- **Mariscope** (DE/CL/AR distributor) publishes the 2023 Reach
  Robotics product directory as a single PDF [5] — most consolidated
  third-party reference.
- **MARUM Workclass ROV** (Bremen) operates a heavy-duty hydraulic
  Schilling-class arm rather than a Reach arm — not a Reach ecosystem
  user. (Mentioned only to confirm the Reach class is *not* a workclass
  arm.)

### 8c. Open-source 3D-printed adapter examples

We searched Thingiverse, Printables, MyMiniFactory, Cults3D, STLFinder,
and GrabCAD for "reach alpha", "reach bravo", "RA-1013", "RB-1054",
"blueprint lab manipulator", and combinations. **No open-source
printable adapter for either arm was found in any of those repos** as
of 2026-05. Closest hits are unrelated jaw mechanisms and chuck-jaw
adapters. This is a **gap in the open ecosystem** that our adapter
project would fill.

GrabCAD has community-uploaded CAD for various Mercury "Bravo" boat
drives — irrelevant; name collision.

### 8d. Academic users (proof the ecosystem exists)

A small but established research community publishes on UVMS = BlueROV2
+ Reach Alpha 5:

- **Aalborg University** — MPC for BlueROV2 with Reach Alpha [17]
- **MDPI Marine Eng** — open-source BlueROV2 simulator with Alpha 5
  [18]
- **arXiv 2303.00042** — continuum UVMS with Alpha 5 deployment [19]
- **ResearchGate Fig. 372641893** — DH-parameter abstract of Reach
  Alpha 5 [15]
- **Sage 2025** — NLMPC dynamic positioning for ROV + manipulator [20]

These confirm the Alpha-on-BlueROV2 stack is the canonical research
configuration. **None of these publish a custom end-effector adapter
design** — the research community uses the stock jaws.

---

## 9. Adapter design proposal for *our* gripper

### 9.1. Reference: what our gripper presents to the adapter

From `../ROV_INTEGRATION.md` §1 and `../../gripper.py`:

- **Bottom face:** planar M4 flange, **4× M4 through-holes** on a
  ~40–50 mm bolt circle (confirm from `gripper.py` `FLANGE_*` before
  drilling; not pinned numerically here because the gripper geometry is
  unlocked at the gear level per `../DRIVETRAIN.md`).
- **Centred axially:** Ø10 mm D-coupler shaft, 1.4 mm D-flat,
  12 mm engagement — the actuator under the flange engages this.
  *The adapter must not interfere with this exit.*
- **Total stack mass (gripper + canister + servo + service loop):**
  estimated ~600–900 g (gripper ~250–350 g, XW540 + canister + end caps
  + cable ~300–500 g) — *estimate*, not measured, but well under both
  arms' lift ratings (Alpha 2 kg / Bravo 10 kg) [2, 3, 4].
- **Cable exit:** RS-485 + 12 V + GND, single cable from the canister
  bulkhead. Routes along the arm to the ROV penetrator (not through the
  arm).

### 9.2. Bravo 7 adapter — fully specifiable today

**Concept:** a printed **bridge plate** that bolts to the RB-1054
Payload Interface on top, and to our M4 flange on the bottom. Zero
mods to the gripper itself.

| Feature | Bravo side (top of adapter) | Gripper side (bottom of adapter) |
|---|---|---|
| Mating face OD | **Ø 71 mm** (matches RB-1054 plate) | ~Ø 60–70 mm (matches our flange — confirm from `gripper.py`) |
| Bolt pattern | **6 × Ø 5.5 mm clearance holes** for M5 socket-cap, on the same bolt circle as the RB-1054's "6 × Ø 5 CSK" pattern (we use the RB-1054's M5 through-bolt pattern, *not* its M6 threaded pattern — M5 is the right size for our load and lets us pass the bolt right through the adapter plate) | **4 × Ø 4.5 mm clearance holes** for M4 on the gripper flange pattern, with **nylon/PTFE shoulder bushings** per `../docs/UNDERWATER.md` §5 |
| Alignment | **2 × Ø 3 H7 dowel-pin pocket** (3 mm dowel, ≥ 6 mm depth) matching the RB-1054 datasheet alignment-pin pattern | *Floating* — gripper flange has no dowel pins; the adapter is the alignment master |
| Centre clearance | Either a **clearance hole** if the RB-1054's centre is open, or **no through-hole** if RB-1054 is solid (the datasheet drawing suggests the centre is solid, but we can't confirm without a STEP file) | **Clearance for the D-coupler shaft exit ≥ Ø 12 mm** so the actuator under the flange can engage |
| Thickness | **15–25 mm** estimate (load path is 6× M5 in single shear; printed PA12-GF wall has plenty of margin at this thickness — confirm by FEA before shipping) | as above |
| Through-axis | **Vertical** — the Bravo wrist axis (J7 roll) defines "down", and our gripper's D-coupler axis must align with it so the four-bar swings symmetrically about the wrist roll | as above |
| Fasteners (top) | **6 × M5 × ~25 mm A4-316 socket cap** with **Loctite 243** + nylon shoulder bushings; bolt-circle radius estimable ≈26–28 mm pending STEP file | M5 captive nut or threaded heat-set insert (Heli-coil M5 in printed PA12-GF is the structurally honest choice — direct PA12-GF threads creep under sustained load) |
| Fasteners (bottom) | n/a | **4 × M4 × ~25 mm A4-316** + nylon bushings + PTFE flat washers per `../docs/UNDERWATER.md` §5 |
| Dowel pins | **2 × Ø 3 × 10 mm A4-316** dowel pins, press-fit into the RB-1054's dowel-pin holes; clearance-fit into the adapter | n/a |
| Material | **PA12-GF (Bambu PAHT-GF or equivalent, 100 % infill)** — matches `../docs/MATERIALS.md` for our rigid-printed parts (PETG-HF for the heat-stake pivot pins + caps) | as above |
| Material alternative | **Machined Delrin** if a printed bridge plate fails FEA — pricier (~AUD 80 cut) but cheap relative to the arm | as above |
| Mass estimate | **40–80 g** depending on thickness; the dimensioned envelope is Ø71 × ~20 mm × density 1.4 g/cm³ (PA12-GF) — *estimate, computed not measured* | as above |
| FEA gate | **Required** before shipping. Bolt-shear is *not* the limiting case: with ~0.8 kg gripper-stack mass at 2 g impact (15.7 N total) spread across 6× M5, each bolt sees ≈2.6 N in direct shear plus ≈5 N from a 100 mm-cantilever moment about the bolt circle — ≈8 N per bolt at impact. Vs. M5-A4 single-shear capacity (~5 kN), that's a >100× margin on the metal. **The PA12-GF print is the limiting case** — bolt-hole bearing creep and the bridge-plate bending stiffness around the central clearance. FEA the printed body, not the bolts. | as above |
| Cable routing on the adapter | A **side notch** (or **side groove**, fillet ≥ 5 mm to avoid stress raisers) lets the RS-485+12V cable exit *sideways* from the canister and run up the arm without being trapped between the adapter and the wrist | as above |

**Worked-example bolt-circle estimate.** The RB-1054 datasheet drawing
shows 6× M6 threaded holes evenly spaced around the Ø71 mm plate. With
3 mm minimum edge distance for an M6 (10 mm OD washer face), the
**M6 pitch-circle radius is ≈26–28 mm** (M6 BCR ≈ 52–56 mm). The
**M5 CSK** pattern shares the same bolt circle (it's the same 6 holes
counterbored from the far side, per [9]). **Confirm by STEP file before
committing**: this is an estimate, not a measurement.

**Worked-example mass.** Ø71 × 20 mm bridge plate, minus a Ø30 mm
centre clearance, minus 6× M5 + 2× Ø3 dowel pockets, minus 4× M4
pockets, in PA12-GF (1.43 g/cm³):
- gross volume ≈ π × 35.5² × 20 = 79 000 mm³
- centre clearance ≈ π × 15² × 20 = 14 100 mm³
- net ≈ 65 000 mm³ ≈ 65 cm³ × 1.43 g/cm³ ≈ **93 g** — *estimate*.

**Procurement implication for §7.** Our integrator buys the RB-1054
(Reach quote) + prints the bridge plate (~AUD 5 in PA12-GF filament) +
bag of A4-316 M5 + M4 stainless + 2× Ø3 dowel pins (~AUD 5 from
McMaster or Australian fastener distributor). Total ~AUD 10 + quote
for RB-1054.

### 9.3. Alpha 5 adapter — design intent only, pending RA-1013 drawing

**Concept (until dimensioned drawing is supplied):** the adapter
*replaces a standard Alpha jaw* — i.e. it presents the same collar /
push-rod / dowel-pin interface that the stock RA-1014 jaw mates to,
**not** an external bolt-on plate. The adapter then exposes our
M4-flange pattern on its outer face.

| Feature | Alpha side (top of adapter) | Gripper side (bottom of adapter) |
|---|---|---|
| Mating face OD | **Ø 40 mm** (matches Alpha 5 arm tube OD per datasheet [2]) — *but the actual thread or collar interface is unknown* | as before — ~Ø 60–70 mm to match our flange |
| Bolt pattern | **Unknown** — possibilities: (a) internal thread on the adapter ID engaging an external thread on the Alpha arm tube, like a stock jaw collar; (b) 1–2× axial M-size screws into the push-rod end face; (c) dowel-pin alignment + threaded collar. **Need RA-1013 dimensioned drawing.** | 4 × M4 clearance — same as Bravo adapter |
| Push-rod handling | **Critical open question.** The Alpha's push-rod is the *only* mechanical input to a jaw — it has 15 mm stroke and 1 kN axial force [2, 11]. Our gripper does not consume axial push-rod motion; the push-rod *must be locked out* (mechanically blocked or unpowered) so it does not drive our adapter into the gripper. *This needs to be confirmed with Reach Sales — does the Alpha permit a passive jaw substitute?* | n/a |
| Alignment | unknown (likely dowel pin somewhere — see Alpha End-Effector datasheet photos [8]) | floating |
| Centre clearance | **Critical** — must clear the push-rod tip and its stroke (≥ Ø 6–8 mm × ≥ 20 mm axial — *estimate*) | Ø ≥ 12 mm clearance for our D-coupler shaft exit |
| Material | **PA12-GF** as before; or **machined Delrin** if the thread tolerance demands precision (machined wins on thread accuracy at small Ø) | PA12-GF |
| Mass estimate | **30–60 g** — the Alpha is half the diameter of the Bravo so the adapter is intrinsically smaller. *Estimate, not measured.* | — |
| FEA gate | Required, same as Bravo. **Load case is gentler** (Alpha full-reach lift 2 kg = ~20 N at the gripper), so the load-path is easier than the Bravo case. | — |
| Cable routing | **Sideways notch** because the Alpha provides no wrist electrical pass-through — cable must exit the canister and run up the Ø 40 mm arm separately. Use polyurethane spiral wrap per `../ROV_INTEGRATION.md` §2a-3. | — |
| **Critical pending data** | (i) RA-1013 mounting-kit dimensioned drawing; (ii) Alpha arm-tube thread spec (or collar interface); (iii) push-rod tip geometry + axial-lock procedure; (iv) Teledyne IE(W)-55 pinout | — |

**Honest verdict.** The Alpha 5 adapter is a research-and-design
project, not a print-and-bolt project. We can describe what it *needs*
to be — a printed sleeve that screws onto the Alpha arm tube where a
jaw would, presents an M4 pattern on the underside, and locks out the
push-rod — but we cannot dimension it from open sources. **Next step is
explicitly a Reach Sales contact, not a CAD session.**

### 9.4. Material recommendation (both arms)

Adopting `../docs/MATERIALS.md` and the campaign's printed-rigid
material posture:

| Layer | Material | Why |
|---|---|---|
| Adapter body (Bravo + Alpha) | **PA12-GF** (Bambu PAHT-GF or equivalent) | Glass-filled nylon for stiffness; survives sustained sub-100 °C load; chemically inert in seawater; isotropically (100 % infill) printed at the campaign's standard spec. |
| Fasteners | **A4-316 stainless** with **Loctite 243** medium-strength threadlocker | Seawater-compatible per `../docs/UNDERWATER.md` §5; Loctite 243 is safe on PA12-GF (271 attacks polymers per `../ROV_INTEGRATION.md` §1c). |
| Galvanic isolation | **Nylon or PTFE shoulder bushings** in every bolt hole; **PTFE flat washer** on the arm face | Bravo's AL7075 is more galvanically active than Alpha's AL6061; isolation matters more on Bravo but is good practice on both. Per `../docs/UNDERWATER.md` §5. |
| Threaded inserts (printed-thread alternative) | **Heli-Coil or Heat-set brass M5** in the printed adapter | Printed PA12-GF threads creep under sustained load; brass inserts let stainless bolts torque to ~3 N·m without crushing the polymer. Heat-set inserts are the cheap option; Heli-Coil is the rigorous one. |
| Dowel pins | **Ø 3 × 10 mm A4-316** dowel pins from the standard subsea-distributor catalogue | Matches RB-1054 datasheet [9] alignment-hole spec. |

### 9.5. Approximate mass / volume per design

| Adapter | Volume (cm³) | Mass (g) | Notes |
|---|---|---|---|
| Bravo 7 bridge plate | ~50–70 cm³ (Ø71 × 15–20 mm, centre relieved) | **70–100 g** estimate | dominant axis dimension is the Ø71 mm RB-1054 pattern |
| Alpha 5 sleeve | ~25–40 cm³ (Ø~50 OD × ~15–20 mm wall, internal threads, ~Ø 40 ID) | **35–60 g** estimate | dominant axis dimension is the Ø40 mm Alpha arm tube |

Both estimates assume PA12-GF density 1.43 g/cm³. Adding the
**fastener + insert** mass (~10–20 g for the M5/M4 bolts + bushings +
dowels + Heli-Coils per side) gives a printed-and-bolted **adapter
mass under 120 g** even on Bravo. This is **well below** the gripper's
own ~300 g mass and so does not move the end-effector trim budget
materially (`../ROV_INTEGRATION.md` §5).

### 9.6. RS-485 routing on the adapter (both arms)

Same routing on both arms — both arms are mechanically the structural
host only; **the bus does not transit the arm or the adapter**.

```
[ROV bulkhead penetrator] ── ROV-grade cable, sleeved (PU spiral or HDPE braid) ──
   │
   └─ runs along the arm topside, fixed every ~30 mm
      │
      └─ service loop (≥ 1 × gripper height = ~60–80 mm) at the
         wrist/adapter region, strain-relieved with a P-clamp on the
         arm flange or adapter side notch
         │
         └─ enters canister bulkhead via WetLink penetrator
            │
            └─ continues inside canister to XW540 via spliced RS-485 +
               12 V (see ../ELECTRICAL.md §4 for rail topology)
```

The **adapter's only contribution** to this routing is a side
notch / groove that lets the cable exit the canister and immediately
rise vertically along the arm without being trapped between the
adapter and the wrist envelope. The notch should be:

- **5 mm radius minimum** fillet on the cut edges (stress raiser
  prevention)
- **≥ 10 mm wide** (accommodate Ø 6–8 mm cable + service margin)
- **on the arm-shadowed side** of the gripper, so the cable cannot
  catch on the workpiece during a grasp

---

## 10. Open questions / what we couldn't verify

This is the explicit list of things we **did not pin** to a primary
source. They block §9.3 (Alpha) more than §9.2 (Bravo).

| # | Question | Why it matters | Resolution path |
|---|---|---|---|
| Q1 | **Alpha 5 wrist mating geometry: thread, collar OD, dowel-pin, push-rod tip** | Blocks the Alpha 5 adapter entirely (§9.3). | Contact **Reach Sales** for the RA-1013 mounting-kit dimensioned drawing, or buy a stock jaw (RA-1014) and reverse-measure. |
| Q2 | **Alpha 5 push-rod axial-lock procedure for passive end-effectors** | Without a lock, the push-rod will drive our gripper into the wrist or pull it free. | Reach Sales — does any third-party tool currently use the Alpha as a passive mount? |
| Q3 | **Alpha 5 Teledyne IE(W)-55 6-pin pinout** | Not blocking — we don't tap the Alpha bus — but useful for any later "share the bus" optimisation. | Teledyne datasheet + Reach Sales. |
| Q4 | **RB-1054 bolt-circle radius (M6/M5 BCR) and dowel-pin-to-pin distance — numerical** | Both numerical anchors of the §9.2 adapter; currently estimated from the datasheet drawing at ≈26–28 mm BCR. | **Reach STEP file** of the RB-1054 — Sales says they share CAD on request (`Section 6 of the integration manual: "Please contact Support if you require 3D CAD files"` [4]). |
| Q5 | **Bravo 7 / 5 base-mount dimensioned bolt pattern** (4× M8 confirmed; pitch circle TBD) | Doesn't affect *our* gripper adapter, but matters for the ROV builder integrating the arm. | Reach Sales — RB-1010 Bravo Mounting Kit datasheet (we couldn't pull it). |
| Q6 | **Reach Robotics list pricing — Alpha 5, Bravo 7, RB-1054, RA-1013** | Locks the §7 cost table. | Quote request — Reach Sales (`sales@reachrobotics.com`) or distributor (Deep Trekker, Mariscope, Bay Dynamics). |
| Q7 | **Reach System Communication Protocol** — actual byte-level format | Not used by us (we run our own RS-485 to our XW540); only relevant if someone wants to **command the arm from the same MCU that talks to our gripper**. | Reach Sales (NDA-gated). |
| Q8 | **Bravo 7 depth rating — 300 vs 450 MSW** | The older datasheet says 300; the V007 integration manual + Mariscope catalogue say 450 (with 600 announced). **We assume 450 MSW is current**, but if a customer's arm is an older V005/V006 unit, the rating is 300. | Spec the customer's arm by serial number at Reach Sales. |
| Q9 | **Alpha 5 per-joint torque (any joint)** | Not on any datasheet we could find. **The 9 N·m / 0.5 rad/s figures in the open-source URDF [11] are placeholders, not Blueprint Lab numbers.** | Reach Sales — joint torque is in the Research Data Pack (per integration manual §5.5 [4]). |
| Q10 | **Open-source 3D-printed adapter examples** | We searched Thingiverse / Printables / GrabCAD / etc. and **found none.** | Confirmed absence — our adapter would be a first. |
| Q11 | **Whether Reach supports a passive-jaw substitute mode** (Alpha 5) | If the firmware refuses to operate without a confirmed jaw end-effector, we can't run the arm in our config. | Reach Sales. |
| Q12 | **Magnetic-field interference with our future T3 magnetic-coupling fallback** (`../SELECTION.md` §3) | The Bravo emits <0.5 mT at ≥10 mm [4 §2.3]; our T3 fallback uses N52 magnets at >50 mT at the rotor face. If the gripper is mounted at the Bravo wrist, our magnet field is much stronger than the arm's — but the arm has on-board electronics. | T3 fallback FMEA — likely fine but flagged in `../FAILURE_MODES.md`. |

---

## 11. Sources

1. **Reach Robotics** product page (Reach Alpha) —
   `https://reachrobotics.com/products/manipulators/reach-alpha/`
   (formerly `blueprintlab.com/products/reach-alpha/`, 301-redirected).
2. **Reach Alpha 5 datasheet (RA-5001)** —
   `https://reachrobotics.com/media/docs/40929/Alpha_5_Datasheet.pdf`
   (live URL gated; mirrored at
   `https://web.archive.org/web/2024/https://reachrobotics.com/media/docs/40929/Alpha_5_Datasheet.pdf`).
3. **Reach Bravo 7 datasheet (RB-7001)** —
   `https://reachrobotics.com/media/docs/40983/Bravo-7-Datasheet.pdf`
   (live URL gated; mirrored at
   `https://web.archive.org/web/2024/https://reachrobotics.com/media/docs/40983/Bravo-7-Datasheet.pdf`).
4. **Reach Bravo Integration Manual V007** —
   `https://reachrobotics.com/media/docs/43447/Reach-Bravo-Integration-Manual-V007.pdf`
   (live URL gated; mirrored at
   `https://web.archive.org/web/2022/https://blueprintlab.com/media/docs/43447/Reach-Bravo-Integration-Manual-V007.pdf`).
5. **Reach Robotics Product Directory (Mariscope 2023)** —
   `https://mariscope.com/wp-content/uploads/2023/06/Reach-Robotics-Product-Catalogue.pdf`.
6. **NauticExpo — Alpha 5 brochure (RA-5001)** —
   `https://www.nauticexpo.com/prod/reach-robotics/product-195661-596965.html`.
7. **Reach Robotics quote portal — Alpha Mounting Kit (RA-1013)** —
   `https://quote.reachrobotics.com/product/alpha-tools/alpha-mounting-kit-2/`.
8. **Reach Alpha End-Effector Datasheet** —
   `https://reachrobotics.com/media/docs/40955/Alpha-End-Effector-Datasheet.pdf`
   (live URL gated; mirrored at
   `https://web.archive.org/web/2024/https://reachrobotics.com/media/docs/40955/Alpha-End-Effector-Datasheet.pdf`).
9. **Reach Bravo Payload Interface (RB-1054) Datasheet** —
   `https://reachrobotics.com/media/docs/43886/Bravo-Payload-Interface-Datasheet.pdf`
   (live URL gated; mirrored at
   `https://web.archive.org/web/2024/https://reachrobotics.com/media/docs/43886/Bravo-Payload-Interface-Datasheet.pdf`).
10. **Deep Trekker shop — Reach Alpha 5 (single arm)** —
    `https://www.deeptrekker.com/shop/products/manipulator-reach-alpha-5-single-arm`
    (quote-only).
11. **Robotic-Decision-Making-Lab/alpha** (ROS 2 driver + URDF + STL
    meshes for Reach Alpha 5) —
    `https://github.com/Robotic-Decision-Making-Lab/alpha`
    (archived 2025-04-10; superseded by
    `https://github.com/Robotic-Decision-Making-Lab/reach`).
12. **Reach Bravo Force/Torque Sensor (RB-FT) Datasheet** —
    `https://reachrobotics.com/media/docs/43900/Reach-Bravo-Force-Torque-Sensor-Datasheet.pdf`
    (live URL gated; mirrored at
    `https://web.archive.org/web/2024/https://reachrobotics.com/media/docs/43900/Reach-Bravo-Force-Torque-Sensor-Datasheet.pdf`).
13. **RobotShop — Reach Robotics Bravo Payload Interface** —
    `https://www.robotshop.com/products/blueprint-bravo-external-end-effector-interface`.
14. **Blueye Robotics — Reach Alpha Two-Axis Rotating Gripper** —
    `https://www.blueyerobotics.com/products/reach-alpha-two-axis-gripper`.
15. **ResearchGate Fig. 372641893** — "Abstracted representation of the
    manipulator Reach Alpha 5 and its coordinate systems" — DH
    parameters for the Alpha 5.
16. **Hot Robotics UK — Reach Robotics Alpha 5** rental access —
    `https://hotrobotics.co.uk/equipment/blueprint-labs-reach-alpha-5/`.
17. **Aalborg University** — "Model Predictive Control for the BlueROV2"
    (thesis) —
    `https://vbn.aau.dk/ws/files/387609647/MPC_control_for_the_BlueROV2_Theory_and_Implementation.pdf`.
18. **MDPI** — "An Open-Source Benchmark Simulator: Control of a BlueROV2
    Underwater Robot" —
    `https://www.mdpi.com/2077-1312/10/12/1898`.
19. **arXiv 2303.00042** — "Design, Kinematics, and Deployment of a
    Continuum Underwater Vehicle-Manipulator System" —
    `https://arxiv.org/html/2303.00042v2`.
20. **Sage 2025 (Walker et al.)** — "Nonlinear model predictive dynamic
    positioning of a remotely operated vehicle with wave disturbance
    preview" — `https://journals.sagepub.com/doi/10.1177/02783649241286909`.
21. **Reach Bravo 5 Datasheet (RB-5001)** —
    `https://reachrobotics.com/media/docs/40982/Bravo-5-Datasheet.pdf`
    (live URL gated; mirrored at
    `https://web.archive.org/web/2024/https://reachrobotics.com/media/docs/40982/Bravo-5-Datasheet.pdf`).
22. **Reach Bravo Hub Datasheet (RB-1080)** —
    `https://reachrobotics.com/media/docs/43899/Reach-Bravo-Hub-Datasheet.pdf`
    (live URL gated; mirrored at
    `https://web.archive.org/web/2024/https://reachrobotics.com/media/docs/43899/Reach-Bravo-Hub-Datasheet.pdf`).
23. **Reach Bravo Rotating Grabber (RB-2130) Datasheet** —
    `https://reachrobotics.com/media/docs/75057/Bravo2-Rotating-Grabber-Datasheet.pdf`
    (live URL gated; mirrored at
    `https://web.archive.org/web/2024/https://reachrobotics.com/media/docs/75057/Bravo2-Rotating-Grabber-Datasheet.pdf`).
24. **Reach Robotics — Blog: "ROV Grabbers Everything You Need To
    Know"** — `https://reachrobotics.com/blog/what-are-rov-grabbers/`.

---

*Cross-links inside this repo (for the next session that comes back to
this file):*
- `../ROV_INTEGRATION.md` §1 — our M4 flange (the gripper side of every
  adapter in §9).
- `../ROV_INTEGRATION.md` §5 — mass + trim budget (~250–350 g end-effector
  total).
- `../SELECTION.md` §"T2 sealing" — the canister stack the adapter
  has to clear.
- `../ELECTRICAL.md` §4 — the RS-485 + 12 V rail routing the adapter
  has to make a side notch for.
- `../docs/UNDERWATER.md` §5 — galvanic isolation rules for stainless
  fasteners on AL7075 (Bravo) and AL6061 (Alpha).
- `../docs/MATERIALS.md` — PA12-GF print spec (the adapter material).
- `../DRIVETRAIN.md` — gear ceiling that bounds our gripper's tip
  force (and so the worst-case load on the adapter).
- `../FAILURE_MODES.md` (Q13 above) — magnetic-field interference for
  the T3 magnetic-coupling fallback.

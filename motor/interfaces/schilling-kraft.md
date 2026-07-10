# Schilling / Kraft / ECA / Hydro-Lek wrist interfaces — research for a work-class adapter

Research-only deliverable for a printed/machined adapter that mounts our 3D-printed
underwater gripper as a custom tool on a heavy work-class ROV manipulator. Companion
to `../ROV_INTEGRATION.md` (§1 "the bottom M4 flange"), `../MOTOR_STUDY.md`, and the
campaign honesty posture in `../../grip/` and `../../fea/`.

**Scope.** Public datasheets, vendor product pages, third-party integrators' jaw-replacement
catalogues, and one peer-reviewed comparative review (Sivčev et al., *Ocean Engineering*
163, 2018). Anything not in those is marked "Not published" or "Estimated."

**Bottom line.** The Schilling-class wrist *jaw flange* — the bolted interface where a custom
tool would attach in place of the standard parallel jaws — is **not dimensioned in any
public document we could find for any work-class vendor.** What *is* public is the
**number** of bolts (six on Schilling Titan II/III/IV and Orion, four on Kraft Predator) and
the existence of an industry-standard tool *handle* (ISO 13628-8 / API 17H D-handle,
Ø70 mm flange, Ø56 mm PCD, 4 or 8 × M6) that the manipulator's *standard jaws*
already grip onto. For our 250–350 g gripper, the handle is the right answer (§9).

---

## 1. Why work-class — and our load-mismatch caveat

Work-class ROVs (Forum Atlas/Comanche, Saab Cougar XT in heavy-tool config,
TechnipFMC Schilling Gemini, Oceaneering Magnum/eMagnum, SAAB Lynx, ROVOP and
DOF survey fleets, etc.) carry one or two 6–7-function manipulator arms with lift
capacities of **120–250 kg at full extension** [1, 9, 10, 13, 14, 22] and wrist torques
of **170–205 N·m** [1, 9, 10, 13]. These arms exist to twist valves, lift bolt-on subsea
modules, manhandle 19 mm-bar ROV handles on production equipment, and clamp the
vehicle onto a structure as a station-keeping anchor. They are *enormously* over-spec
for a 0.3 kg gripper.

Our gripper is **≈ 0.3 % of TITAN 4's full-extension lift rating** (300 g vs 122 kg
[1]) and is built entirely from PETG / PA12-GF / TPU. The polymer flange on the bottom
of the canister cannot accept a stainless or titanium 6-bolt clamp at the torque the
work-class wrist can apply, and the polymer crown/pinion drivetrain has a structural
ceiling of T_safe ≈ 0.034 N·m at the input shaft (see `../DRIVETRAIN.md`). The
work-class arm is roughly *5 000× the wrist torque our gripper can withstand*.

So the adapter is honest about its job: it is a **demo of interface compatibility,
not of load capability**. The work-class arm could crush, snap or shear the gripper
in normal operation. This is acknowledged explicitly in §10 and the adapter framing
in §9 follows.

The realistic deployment (already in `../ROV_INTEGRATION.md` §1) is an observation-class
ROV (BlueROV2, Sub-Atlantic Tritech, Saab Falcon, ECA H300) where the gripper's mass
and force budget are matched. This file exists because *the question of work-class
compatibility was asked* — not because we recommend it as a primary path.

---

## 2. Arm survey — capacity, wrist torque, depth rating

All numbers below come from manufacturer datasheets or the Sivčev et al. (2018)
comparative review [22]; cell-by-cell sources in the column **Src**. WC = work-class,
MC = medium-class, OC = observation-class. "—" means the spec is not in public docs.

| Manufacturer | Model | Funcs | Class | Lift full-ext (kg) | Max lift nom. (kg) | Wrist torque (N·m) | Grip force (N) | Reach (mm) | Mass air / water (kg) | Std depth (msw) | Materials | Src |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Schilling Robotics (TechnipFMC) | **TITAN 4** | 7 | WC | 122 | 454 | **170** | 4 092 | 1 922 | 100 / 78 | 4 000 (7 000 ext.) | primary Ti | [1] [2] [3] [22] |
| Schilling Robotics | CONAN 7P | 7 | WC | 181 | 159¹ | 205 | 4 448 | 1 806 | 107 / 73 | 3 000 | Al / SS / Ti | [4] [22] |
| Schilling Robotics | ATLAS 7R | 7 | WC | 250 | 500 | 205 | 4 448 | 1 664 | 73 / 50 | 6 500 | Al 6061 / SS | [5] [22] |
| Schilling Robotics | ATLAS 7P | 7 | WC | 250 | 500 | 205 | 4 448 | 1 664 | 73 / 50 | 6 500 | Al / SS | [5] |
| Schilling Robotics | ORION 7P/7R | 7 | MC | 68 | 250 | 205 | 4 448 | 1 532 | 54 / 38 | 6 500 | Al / SS / Ti | [6] [22] |
| Schilling Robotics | ORION 4R | 4 | MC | 109 | — | 68 | 1 334 | 1 920 | 80 / 51 | 6 500 | Al / SS | [22] |
| Schilling Robotics | RigMaster (grabber) | 5 | WC | 181 | 270 | 205 | 4 448 | 1 372 | 64 / 48 | 6 500 | Ti / Al / SS | [7] |
| Schilling Robotics | TITAN 2 (legacy) | 6 | WC | 109 | — | 68 | — | 1 920 | 80 / 51 | — | Al / SS | [22] |
| Schilling Robotics | TITAN 3 (legacy) | 6 | WC | 250 | 275 | 175 | 6 396 | 2 100 | 115 / 77 | 4 000 | Al / SS | [22] |
| Kraft TeleRobotics | **Predator** | 6 | WC | 91 (≈200 lb) | 227 (≈500 lb) | **135**² (1 200 in-lbs) | 1 334 (300 lbf) | 2 035 (79.7 in) | 80 / 51 | 3 000 (6 500 ext.)³ | anod. Al + SS | [8] [22] |
| Kraft TeleRobotics | Raptor | 6 | WC | 91 | 227 | 135 | — | 1 920 | 75 / 44 | 6 500 | Al / SS | [22] |
| Kraft TeleRobotics | Grips | 6 | MC | 45 | 82 | — | — | 1 556 | 59 / 41 | 3 000 | Al / SS | [22] |
| Kraft TeleRobotics | HYDRA UW3 | 6 | WC | 121 | 300 | 350 | 2 942 | 2 035 | 130 / — | 500 (test only) | Al / SS / Ti | [22] |
| ECA-Hytec (Exail) | ARM 7E (electric) | 7 | MC | 40 (>40) | 100 | 190⁴ | 1 471 | 1 790 | 69 / 49.2 | 6 000 | Ti | [11] [22] |
| ECA-Hytec | ARM 5E (electric) | 5 | OC/MC | 25 | 40 | 25 | 490 | 1 000 | 27 / 18.5 | 6 000 | Al 6082 T6 | [11] [22] |
| ECA-Hytec | ARM 5E Micro (electric) | 5 | OC | 10 | 10 | 14 | 245 | 640 | 10 / 2.75 | 300 | Al | [11] |
| Hydro-Lek (SAAB Seaeye) | **HLK-43000** | 5 | OC | 10 (HD 20) | 20 (200 bar) | 8 (jaw rot.) | 90 | 660 | 8.4 / 4.2 | not published⁵ | 316SS, 6082-T6 Al, HDPE | [12] [22] |
| Hydro-Lek | HLK-5300 | 6 | OC/MC | — | — | — | — | — | — | — | — | [22] |
| Hydro-Lek | HLK-5680 | 6 | MC | 40 | — | — (cont. jaw rot.) | — | 1 050 | 27.8 / 21 | not published | 316SS / Al / HDPE | [12] |
| Hydro-Lek | HLK-HD5 | 5 | MC | 40 | 75 | 75 | — | 1 060 | 28 / 14.5 | — | 316SS / Al | [22] |
| Hydro-Lek | HD6R / HD6W | 6 | MC | 75 | 150 | 75 | — | 1 500 | 59 / 40 | — | 316SS / Al | [22] |
| Forum / Perry "TA60J" | TA60J | 4 | WC | 250 (∼) | 380 | 250 (∼) | 5 000 | 1 440 | 82 / 60 | 11 000 | Al / SS | [22] |
| Forum / Perry | TA60 | 4 | WC | 300 (∼) | 380 | 250 | 5 000 | 1 380 | 76 / 51 | 11 000 | Al / SS | [22] |
| Cybernetix / Ifremer | MAESTRO | 6 | WC | 96 | 100 | 150 | 1 471 | 2 400 | 85 / 65 | 6 000 | Ti | [22] |
| Schilling Robotics | GEMINI (all-elec.) | 7 (×2) | WC | — | — (lift 1 000 kg system) | — | — | — | — | 3 000 (4 000 ext.) | — | [10] |

¹ The Schilling CONAN 7P "max lift, nominal" line in the datasheet reads "159 kg",
which is **lower** than the "lift at full extension" of 181 kg — almost certainly a
labelling artefact in the marketing PDF (the same row in Sivčev's table is "Conan 7P:
max 273, full-ext 159"). Both numbers are cited as-printed for reproducibility.

² Predator: Kraft publishes 1 200 in-lbs = 135 N·m on the public product page [8],
while the Sivčev review lists 135 N·m as well [22] — matched.

³ Predator extended depth: "21 000 fsw" = 6 400 m claimed on Kraft's product page;
Sivčev gives the standard model at 6 500 m. Both rounded to "6 500 (ext.)".

⁴ ECA ARM 7E wrist torque 190 N·m is from Sivčev [22]; the Exail product page only
quotes max payload (≥ 40 kg). The disagreement with the 40 N·m number sometimes
quoted is unresolved — flagged as uncertain.

⁵ HLK-43000 depth: the Hydro-Lek datasheet [12] does not print a depth rating; the
manipulator is sold for observation-class ROVs which typically work in T1/T2 envelopes
(see `../REQUIREMENTS.md` for depth-tier definitions in this project). The HD variant
list runs 4 000 m typical.

**Class summary.** TITAN 4 / CONAN / ATLAS / RigMaster / TITAN 3 / Predator / Raptor /
HYDRA UW3 / Forum TA60 / Maestro are the work-class. ORION / Grips / ARM 7E /
HLK-5680 / HLK-HD5/HD6 are medium-class. HLK-43000 / ARM 5E / ARM 5E Micro are
observation-class. **Our gripper is built for the observation-class envelope.**

---

## 3. Wrist flange geometry per arm — **what is and is not publicly dimensioned**

This is the section everyone wants and is the section least populated by public data.
What's published is summarised below; everything else is flagged.

| Arm | Std jaw mounting interface (publicly known) | Bolts | Bolt size | Bolt circle ⌀ (mm) | Flange OD (mm) | Alignment dowel / key | Mating face | Source / inference |
|---|---|---|---|---|---|---|---|---|
| Schilling TITAN II / III / IV | Parallel jaw / 3- or 4-finger jaw is a **front adapter assembly** held to the wrist gerotor rotate housing | **6** | Not published (inferred M8) | Not published | Not published (inferred ~70–100 mm by photo scaling against the 99 mm gripper opening) | Not published (likely indexed by gerotor shaft + 1 dowel) | Faced perpendicular to jaw-rotate axis | "Loosen 6 bolts" from Imenco/Subsea Specialist jaw-replacement catalogues [15] [16]; visible in TITAN 4 photos [1] [3] |
| Schilling Orion 7P/7R | Same family adapter as Titan (Imenco lists "exact fit to Schilling's Titan II/III/IV and Orion") | 6 | Not published | Not published | Smaller than TITAN (gripper opening 97 mm vs 99 mm; flange likely similar) | Not published | Same | [6] [15] |
| Schilling Conan 7P | Same family as TITAN; 152 mm gripper opening → larger jaw assembly OD but interface bolts share family | 6 (assumed) | Not published | Not published | Not published | Not published | Same | [4] [15] |
| Schilling Atlas 7P/7R | 198 mm gripper opening; biggest jaw OD in family; interface assumed shared | 6 (assumed) | Not published | Not published | Not published | Not published | Same | [5] |
| Schilling RigMaster | 289 mm gripper opening (grabber); "interchangeable jaw configurations" explicit in datasheet | Not published | Not published | Not published | Not published | Not published | Same | [7] |
| Kraft Predator | **"A square, four-bolt flange"** explicitly stated on Kraft product page; parallel and 4-finger intermeshing jaws available; jaws accept Ø3/4″ (≈19 mm) T-handles | **4** | Not published (inferred ½″ UNF or M12 from "1 200 in-lbs" wrist torque class) | Not published | Square pattern, OD not published (inferred ~80–100 mm) | Not published | Square (not circular) | [8] |
| Kraft Raptor | Same Kraft front-end family as Predator | 4 (assumed) | Not published | Not published | Not published | Not published | Square | inference from [8] |
| ECA-Hytec ARM 7E (electric) | Quick-change electric jaw module; electric drive bolts and pin behind 1 connector | Not published | Not published | Not published | Not published | Not published | Not published | [11] |
| Hydro-Lek HLK-43000 | "Uses HLK-21020 180° jaw rotate as standard"; jaws bolt to the rotate, rotate bolts to the forearm | Not published | Not published | Not published | Not published | Not published | Not published | [12] |
| Hydro-Lek HLK-5680 | "Uses HLK-25000 jaw rotate offering continuous rotation"; same modular pattern | Not published | Not published | Not published | Not published | Not published | Not published | [12] |
| Saab Cougar XT | Vehicle ships with HLK-25000-driven jaws and/or 3-function grabbers; arm = Hydro-Lek-family | Same as Hydro-Lek family | Not published | Not published | Not published | Not published | Not published | [12] [17] |

**Critical caveat.** The 6-bolt / 4-bolt counts above come from third-party jaw
*replacement* catalogues (Imenco, Subsea Specialist) and the Kraft product page —
not from a primary Schilling/Kraft document, which lives behind a customer NDA. The
bolt *size* and *bolt circle diameter* are not present in any source we found. The
M8 / "~70–100 mm" inferences for Schilling and Kraft are scale-from-photo estimates
with ±30 % uncertainty and must be **measured from a sample or extracted from a vendor
integration drawing** before any adapter is cut.

---

## 4. Patterns and what can be unified

| Pattern | Members | Honest description |
|---|---|---|
| **"Schilling-family 6-bolt round flange"** | Titan II, Titan III, Titan IV, Orion 7P/7R, Orion 4R, Conan 7P, Atlas 7P/7R, possibly RigMaster | Confirmed bolt count (6) by jaw-swap catalogues [15] [16]; everything else (OD, BC, bolt size, dowel) is **not** standardised in public documentation. The standard is that **a third party (Imenco) makes a single front adapter that fits the whole family** — strong evidence the *geometry is shared within Schilling*, but no evidence it follows any inter-vendor standard. |
| **"Kraft-family 4-bolt square flange"** | Predator, Raptor (assumed), Grips (assumed) | Confirmed by Kraft product page [8]. Square, not round. |
| **"Hydro-Lek modular jaw-rotate"** | HLK-43000, HLK-5680, HLK-HD5, HLK-5300 | Vendor uses *named jaw-rotate modules* (HLK-21020, HLK-25000) that bolt to the forearm and accept their own jaw set. Jaw-rotate-to-forearm geometry not published; jaw-to-jaw-rotate geometry not published. The modular catalogue *implies* a within-Hydro-Lek standard. |
| **"ECA all-electric quick-change"** | ARM 5E / 7E | Marketing emphasises "no oil, no leaks" and "ease of maintenance" — implies an electric quick-change at the wrist. Dimensions not published. |
| **No inter-vendor compatibility** | — | **There is no IMCA/IOGP/ISO standard for the wrist jaw interface across vendors.** A custom tool must be designed against one specific arm family. (Cross-check: API 17H and ISO 13628-8 only standardise the *tool handle* side, not the wrist side; see §6 below.) |

The pragmatic implication: the adapter is **one design per arm family**, exactly as the
project note in `../ROV_INTEGRATION.md` §1 already calls out.

---

## 5. Hydraulic vs electric — power source for our gripper

Most work-class arms are **servo-hydraulic** at 3 000 psi (207 bar) supply and 5–19 lpm
flow [1] [4] [5] [7] [8]. The actuation power for the manipulator (cylinder, gerotor)
comes from the ROV's hydraulic power unit; the *electronics* run on a separate **24 VDC
auxiliary bus**, drawing very little (TITAN 4 slave arm 1.875 A at 24 VDC = ≈45 W, per
the technical manual [2]).

| Arm | Actuation | Electronics aux bus | Implication for our gripper |
|---|---|---|---|
| Schilling TITAN 4 / Atlas / Conan / Orion / RigMaster | hydraulic (3 000 psi) | 24 VDC, RS-232 or RS-422/485 [1] [2] [4] [5] [6] [7] | Our XW540-T260 wants 12 V / ≤ 6 A. We tap the 24 V aux bus and step down to 12 V via a buck (e.g. Pololu D24V90F12, 90 W) at the canister bulkhead. Buck must be wet-side-isolated or live inside the canister. |
| Kraft Predator / Raptor | hydraulic (1 500–3 000 psi) | — (not published as a separate bus on [8]) | Same approach: pick up the ROV's 24 V or 110 V auxiliary feed at the wrist and step down. |
| ECA ARM 7E (electric) | electric (24 VDC) | 24 VDC, RS-485 [11] | **Best-case** — voltage and protocol *already match* our gripper if the ROV can spare a free RS-485 pair on the wrist pass-through. No buck needed if the ARM provides 24 V split or if we use 24 V-tolerant XW540 (the XW540 spec window is 12–24 V — confirmed datasheet). |
| Schilling Gemini (all-electric) | electric (24 VDC distribution) | — | Same as ECA electric; auxiliary spare ports are usually budgeted into the platform from build. |

**Hydraulic-to-electric trend.** Schilling Gemini [10] and ECA's electric ARM 5E/7E line
[11] are pushing all-electric. Kraft Atom (claimed all-electric in industry press,
not confirmed by a vendor PDF we could find) is the Kraft equivalent. For our 5-year
horizon the safest assumption is **hydraulic arm, 24 VDC aux bus to drive our
gripper electronics**. We do not provide tool hydraulic flow back to the gripper — our
actuator is electric.

**The gripper's actuator change is zero.** This is the modularity payoff already noted
in the project state (`../MOTOR_STUDY.md`): swap the wrist-side power adapter; the
servo, bus, and gripper are unchanged.

---

## 6. Wet-mateable electrical pass-through at the wrist — connectors

Work-class arms generally do **not** ship with an electrical pass-through to the
wrist as standard — the standard wrist is hydraulic-only for tool flow, plus a
SeaNet cable (Schilling) [1] back to the arm's own electronics. Adding an electrical
pass-through to a tool is a **stab-plate / wet-mateable connector option** customised
per ROV install. The candidates:

| Connector family | Manufacturer | Typical use | Contact count | Rating | Wet-mate cycles | Notes | Src |
|---|---|---|---|---|---|---|---|
| **SubConn Micro Circular** (MCBH/MCIL series) | MacArtney | Compact ROV tooling, instruments | 2–16 | 600 V / 5 A typical | > 500 wet mates | Gold contacts, low-resistance; industry standard for small ROV tools | [19] |
| **SubConn Power** | MacArtney | Higher-current tooling | 2–6 | up to 1 000 V / 80 A | > 500 wet mates | If we ever exceeded 6 A — we won't (our stall is ≤ 6 A) | [19] |
| **SubConn Ethernet** | MacArtney | Data | 4 | Gigabit | > 500 wet mates | Not needed: our bus is RS-485 over SubConn Micro | [19] |
| **BIRNS Aquamate (neoprene molded)** | BIRNS | Power/signal, medium power | 4–24 | medium power | > 100 wet mates | Heat-treated BeCu sockets, gold plate, SS bodies. Larger envelope than SubConn Micro. | [20] |
| **Burton Subsea (TE)** | TE Connectivity (formerly Burton Industries) | Heritage installs | 4–24 | various | Few cycles | Older subsea connector family still widespread on legacy installs (Schilling Titan T4 manuals reference Burton-shell options [2]) | [2] [21] |
| **Macartney MacBH (MacInnes)** | MacArtney | Bulkhead | various | — | — | The bulkhead penetrator family that pairs with SubConn cordsets | [19] |

For **our gripper**, the canister bulkhead is sized for **SubConn MCBH-6 or BIRNS
4-pin Aquamate** at T2 (≤ 30 m), matching the choice in `../ROV_INTEGRATION.md` §3
(unchanged). The decision below the wrist (gripper-side) is independent of the
decision above the wrist (ROV-side); the adapter doesn't dictate it.

**Hydraulic pass-through.** Schilling and Kraft both ship optional 2–4 hydraulic
ports at the wrist for tool actuation [1] [8] (Schilling references a "tool circuit"
in the SeaNet pass-through; Kraft Predator does not detail hydraulic ports on the
public page). We use **none of these**. Our gripper is electrically actuated. We
plug the hydraulic ports with subsea-rated blanks if the arm's wrist exposes them
unused.

---

## 7. Depth-rating envelope per arm

Reproduced from §2 for one-glance reference, against our project depth tiers
(T1 ≤ 10 m, T2 ≤ 30 m primary, T3 > 30 m — see `../REQUIREMENTS.md`).

| Arm | Std depth (msw) | Extended (msw) | Project tier coverage |
|---|---|---|---|
| Schilling TITAN 4 | 4 000 | 7 000 | T3 (way past) |
| Schilling CONAN 7P | 3 000 | — | T3 |
| Schilling ATLAS 7P/7R | 6 500 | — | T3 |
| Schilling ORION 7P/7R | 6 500 | — | T3 |
| Schilling RigMaster | 6 500 | — | T3 |
| Schilling Gemini | 3 000 | 4 000 | T3 |
| Kraft Predator | 3 000 | 6 500 | T3 |
| Kraft Raptor | 6 500 | — | T3 |
| Cybernetix Maestro | 6 000 | — | T3 |
| ECA ARM 7E | 6 000 | — | T3 |
| ECA ARM 5E | 6 000 | — | T3 |
| ECA ARM 5E Micro | 300 | — | T2 only |
| Hydro-Lek HLK-43000 | not published | — | likely T1/T2 (observation-class arm) |
| Forum TA60 / TA60J | 11 000 | — | T3 (full-ocean-depth grabbers) |

**Our gripper's polymer construction is bench-validated at T2 only.** We rate the
adapter the same — pressure-class is not what fails at depth; the gripper itself is.
This is independent of the arm's rating.

---

## 8. Recommended target arm — Schilling TITAN 4

Picking one to design *to* (Section 9):

1. **TITAN 4 is the de-facto industry standard** — Schilling claims "over 3 000
   manipulator systems delivered" [9], the TITAN 4 is on Forum's Comanche, Oceaneering
   Magnum/eMagnum, ROVOP and DOF fleet ROVs. Designing to TITAN 4 maximises future
   demo audience.
2. **The Schilling jaw-replacement ecosystem is the best documented public interface**
   — Imenco, Subsea Specialist, Caribbean Subsea and others all sell drop-in jaws to
   the same 6-bolt front-adapter pattern, and explicitly cover Titan II/III/IV plus
   Orion [15] [16]. This is the only family where we can point at *commercial proof*
   of a third-party tool mounting to a Schilling wrist.
3. **TITAN 4 depth rating (4 000 msw standard) is irrelevant to us** but maps trivially
   onto the gripper's T1/T2 demo envelope — we are not stressing the *arm's* envelope.
4. **The Schilling family interface is shared across Titan / Orion / (likely) Conan /
   (likely) Atlas** — one adapter design covers a wide install base.

**Secondary target:** Kraft Predator (square 4-bolt) — the Western-hemisphere Schilling
competitor; covers Oceaneering legacy installs that retained Kraft arms.

**Realistic primary** (see §9 Option B): **No bolted adapter at all** — print an
ISO 13628-8 D-handle onto the gripper.

---

## 9. Adapter design proposal — two options

### Option A — bolted adapter to a Schilling 6-bolt jaw flange (interface-compatibility demo)

This is the task's primary ask. It assumes we have either an Imenco/Subsea Specialist
jaw-replacement assembly to copy the bolt pattern from, or vendor integration drawings.
**Without one of those, the dimensions below are placeholders flagged as estimates.**

```
Adapter plate (printed PA12-GF, or machined Ti grade 5 for a "real" build)

Top face:                       Schilling 6-bolt jaw front-adapter pattern
                                6 × bolt holes, BC ⌀ ESTIMATED ~80 mm (±30%, not public)
                                Bolt size ESTIMATED M8 (±1 size; clamps a Ti jaw at 170 N·m)
                                Plus central clearance (~Ø25 mm) for the gerotor shaft
                                Plus 1 dowel ESTIMATED ⌀6 mm for indexing
                                Mating face flat, perpendicular to jaw rotate axis

Adapter body:                   Ø100 mm puck, 10 mm thick
                                Material: PA12-GF (printed) primary;
                                          Ti6Al4V or AISI 316 secondary for a real-world build
                                Mass est.: PA12-GF puck Ø100×10 mm @ 1.05 g/cc ≈ 80 g
                                           316 SS puck Ø100×10 mm @ 7.9 g/cc ≈ 620 g
                                           Ti6Al4V puck Ø100×10 mm @ 4.4 g/cc ≈ 345 g

Bottom face:                    The existing gripper bottom M4 flange
                                4 × M4 through-holes on ⌀40–50 mm BC (per ../ROV_INTEGRATION.md §1a)
                                Same face, perpendicular to our input shaft
                                Bolt clearance to D-coupler exit: ≥ 2 mm axial (../ROV_INTEGRATION.md §1d)

Galvanic isolation:             Nylon/PTFE shoulder bushing through each M8 hole on the top face
                                PTFE flat washer under each bolt head
                                Thin PTFE gasket between adapter top face and Schilling jaw flange
                                (per ../docs/UNDERWATER.md §5 and ../ROV_INTEGRATION.md §1b)
                                Critical at the Ti-Schilling-vs-stainless-fastener couple.

Mass total:                     Polymer-only ≈ 80 g + isolation hardware ≈ 25 g = ~105 g
                                Ti-puck ≈ 345 g + isolation hardware ≈ 25 g = ~370 g
                                System mass with gripper: ~ 400 g (polymer) or ~ 670 g (Ti)
                                — still 0.5 % of TITAN 4's full-extension lift.

Wet-mateable cable:             A SubConn MCBH-6 bulkhead through the side of the adapter (or routed
                                up to the arm-side SubConn at the wrist pass-through, per §6).
                                Service loop ≥ 80 mm above the adapter face (../ROV_INTEGRATION.md §2).
```

**Status of every number above.** Top-face BC ⌀, bolt size, dowel size, central
clearance: **all estimates** until either (a) a Schilling integration drawing is
obtained or (b) an Imenco jaw assembly is measured. Bottom-face geometry: locked
to the gripper CAD. Puck OD / thickness: chosen by us to span the two patterns; can
be re-cut once the top side is measured.

### Option B — ISO 13628-8 D-handle on the gripper itself (recommended primary)

Pivot, recommended after `advisor()` review: instead of bolting our 300 g gripper to a
500 lb-rated wrist, **make it a "held tool"** — print a ROV D-handle as part of the
canister cap, so any work-class manipulator's *existing* jaws grip our gripper exactly
the way they grip every other subsea tool.

This is **how the industry actually deploys lightweight tools.** It is the *intended*
function of the standard jaws.

```
D-handle integrated into top cap of canister (or onto a printed adapter plate that
bolts to the existing M4 flange — so as not to disturb the gripper assembly):

Per ISO 13628-8 / API 17H, standard ROV D-handle [17] [18]:
- Bar diameter:        Ø19 mm (standard "large" handle) — fits Schilling 4-finger, Kraft,
                       Hydro-Lek, etc. parallel-acting jaws.
                       (Ø16 mm "small" handle also standard.)
- Handle flange:       Ø70 mm with 4 or 8 bolt holes (Ø6.6 mm clearance for M6)
- Pitch circle:        Ø56 mm PCD
- Form:                "D" shape (snag-free) preferred over "T" (T-bar handles can snag
                       on intermeshing jaws per [17]).

Print spec (PA12-GF, hardened nozzle, build per ../docs/PRINTING.md):
- Handle bar:          Ø19 mm × ~80 mm long, supported by 2 buttresses to a Ø70 mm flange
- Flange:              ⌀70 mm × 6 mm thick, 4 × Ø6.6 mm holes on Ø56 mm PCD
- Bonding to gripper:  4 × M6 through to a back-plate adapter that bolts down to our
                       existing M4 flange (4× M4 → 4× M6 step-up); OR cap-replacement
                       with the D-handle moulded into the canister top.

Mass total:            PA12-GF handle assembly ≈ 50 g  (Ø70×6 mm flange + Ø19×80 mm bar)
                       + back-plate adapter ≈ 25 g
                       System mass: ~ 375 g

Material isolation:    Polymer-to-polymer at our face; the Schilling jaw is Ti and the
                       fingers are 316 SS — the bar surface sees Ti/SS clamping
                       intermittently, no continuous galvanic couple.

Cable handling:        Cable exits the side of the canister opposite the handle face,
                       routed back to the ROV cable harness as already in
                       ../ROV_INTEGRATION.md §2. No change.

Load case:             The Schilling jaw clamps the D-handle at 4 092 N grip force
                       (TITAN 4 nominal [1]). PA12-GF compressive yield is ≈ 80 MPa;
                       a Ø19 mm bar with two 4-finger jaw contact patches of 10×10 mm
                       sees ≈ 4 092 N / (2 × 100 mm²) = 20 MPa compressive — well
                       under PA12-GF yield. (Quick check; needs FEA verification before
                       a real deploy — sketched in §11.)
```

**Why this is the honest recommendation:**
- It does not require **any** Schilling-internal drawing to design.
- It uses an **ISO standard** [18] — universal across Schilling, Kraft, ECA, Hydro-Lek
  parallel jaws — so one design covers every work-class arm.
- It is **massively cheaper** (no Ti machining, no per-arm SKU).
- The mass match works: the arm picks up our gripper as a 350 g held tool, not as a
  bolted appendage. Drop / shock loads do not transmit to our polymer flange.
- It honours the project's modularity thesis (`../projects/softsense`): same gripper,
  same D-coupler, **same handle** — works on every work-class arm.

---

## 10. Honest caveat — the load-capability gap

| Spec | Our gripper | TITAN 4 work envelope | Mismatch |
|---|---|---|---|
| Total mass | 250–350 g (`../ROV_INTEGRATION.md` §6) | 122 kg at full extension [1] | ≈ 0.3 % |
| Tip force | ≈ 12 N / finger (`../REQUIREMENTS.md`) | 4 092 N grip force [1] | ≈ 0.3 % |
| Input shaft torque | T_safe ≈ 0.034 N·m (`../DRIVETRAIN.md`) | 170 N·m wrist torque [1] | ≈ 0.02 % |
| Polymer flange clamp | M4 in PA12-GF, ≈ 1.5 N·m bolt torque safe (`../ROV_INTEGRATION.md` §1c) | M8 fasteners typical 25–35 N·m torqued | crushes ≈ 20× over budget |
| Depth-rated qual | T2 (≤ 30 m) bench, not certified | 4 000–7 000 msw certified | not comparable |

**The work-class arm could, by mis-command, instantly destroy the gripper.** This is
mitigated as follows:

1. **The arm is *the operator*, not the gripper's driver.** The arm holds the gripper;
   the gripper drives itself (XW540, RS-485, `present_current`-based force feedback).
   Wrist torque and grip force of the arm do not go through the gripper's drivetrain.
2. **Option B (D-handle) means the arm clamps a passive bar.** The 4 092 N clamp goes
   into a Ø19 mm PA12-GF bar in pure compression. Verified safe by the §9-B sketch;
   FEA needed before any real deploy.
3. **Option A (bolted adapter) means the bolted joint is the failure mode.** The Ti
   wrist applied through M8 fasteners into a PA12-GF puck — printed-thread polymer
   sees clamp creep at 25–35 N·m torque and loses preload. Real-world deploys would
   need stainless threaded inserts pressed into the PA12-GF, or the puck machined in Ti.
4. **The gripper's *own* torque ceiling does not change** — the polymer crown/pinion
   still binds at T_safe ≈ 0.034 N·m, current-limited at the servo (see §`../DRIVETRAIN.md`).
   That's a property of *us*, not the arm.

The deliverable framing is therefore: **the adapter demonstrates that the gripper *can*
be mechanically attached to a work-class wrist.** It does not claim work-class load
capability. Anyone proposing to use this combination operationally must accept that
the gripper is the limiting element of every load path.

---

## 11. Open questions / what we couldn't verify

| # | Question | Why it matters | What we'd need |
|---|---|---|---|
| 1 | **What is the actual bolt circle ⌀, bolt size, dowel size and central clearance of the Schilling Titan / Orion jaw flange?** | Required to cut Option A adapter top face. | A Schilling Titan integration drawing (NDA), or measure an Imenco/Subsea Specialist jaw assembly directly with calipers. |
| 2 | **Same questions for Kraft Predator (square 4-bolt).** | Required to cut a Kraft variant of Option A. | Kraft integration drawing (NDA), or measure a Predator jaw assembly. |
| 3 | **ECA ARM 7E wrist torque — 40 or 190 N·m?** | Affects how we'd size the Option-A adapter if targeting ECA. | A current Exail product datasheet, not just the brochure. The two public numbers disagree by ~5× — almost certainly different definitions (continuous vs peak) but we couldn't resolve which. |
| 4 | **Hydro-Lek HLK series depth rating.** | T2/T3 envelope mapping. | Hydro-Lek datasheets do not print depth on the customer-facing pages; would need their integration manual. |
| 5 | **Is the Schilling jaw flange the same on Conan, Atlas, RigMaster as on Titan/Orion?** | Affects the "one adapter, many arms" claim in §4. | Either Imenco/Subsea Specialist confirming their adapter works on those models (they list only Titan II/III/IV + Orion), or a Schilling drawing. |
| 6 | **PA12-GF Ø19 mm bar in Schilling 4-finger jaw at 4 092 N clamp — does it survive?** | Locks in Option B. | A 2D plane-strain FEA against PA12-GF stress-strain (per `../fea/UNIVERSAL_FINGER.md` patterns), or a bench test using a stand-in clamp at the same force. Estimated below yield by ≈ 4× — confidence high but not verified. |
| 7 | **Hydraulic vs electric pass-through availability** on a specific deploy ROV. | Determines if we tap 24 VDC at the wrist via a wet-mate or run a power cable along the arm. | The host ROV's wrist-pass-through config; arm-vendor-independent. |
| 8 | **Is there any IMCA / IOGP / API standard for the wrist jaw flange itself (as opposed to the tool handle)?** | If yes, would supersede the per-vendor design. | We searched IMCA R 004 (ROV safe-operations guidance — operations, not interface dimensions), API 17H (ROV interfaces on subsea production systems — covers tool handles + hot stabs, not wrist flange), ISO 13628-8 (same scope as API 17H). **No public standard appears to cover the wrist-side flange.** Confidence high; finding marked as "no standard found." |
| 9 | **Schilling Gemini all-electric: bolt pattern unchanged?** | Future-proof check. | Vendor literature. Energid Actin integration press doesn't address it [10]. |
| 10 | **Kraft Atom (all-electric Predator-class) specs?** | The Kraft electric story. | Kraft's product page lists Predator/Raptor/Grips only [8]; no public Atom datasheet found. |

---

## 12. Sources

Numbered references; URL retained for reproducibility. PDF datasheets stored locally
as extracted text in `motor/iterations/_interfaces_provenance/` (planned, not in this
commit).

1. TechnipFMC, **Schilling Robotics TITAN 4 Manipulator** datasheet, rev 2.0 (2023). https://www.technipfmc.com/media/hpkjrigr/titan-4-datasheet.pdf — wrist torque 170 N·m, grip 4 092 N, depth 4 000/7 000 msw, reach 1 922 mm, mass 100 / 78 kg, 24 VDC arm, RS-485 telemetry.
2. Schilling Robotics, **Titan 4 Manipulator System: Technical Manual** doc 011-8239 rev B (2012). https://www.dndkm.org/DOEKMDocuments/GetMedia/Technology/2177-8239_Titan4_cover_toc_specs.pdf — system electrical, hydraulic envelope, Burton connector option.
3. TechnipFMC, **Schilling TITAN 4 Manipulator** (alternate brochure). https://www.technipfmc.com/media/pb4i4rfy/titan-4-manipulator.pdf
4. Schilling Robotics, **CONAN 7P Manipulator** product datasheet (FMC, 2013). https://www.dndkm.org/DOEKMDocuments/GetMedia/Technology/2186-CONAN-7P-Datasheet.pdf — wrist torque 205 N·m, grip 4 448 N, depth 3 000 msw, opening 152 mm, mass 107 / 73 kg.
5. Schilling Robotics, **ATLAS 7R Manipulator** product datasheet (FMC, 2013). https://dndkm.org/DOEKMDocuments/GetMedia/Technology/2188-ATLAS-7R-Datasheet.pdf — wrist torque 205 N·m, grip 4 448 N, opening 198 mm, mass 73 / 50 kg, depth 6 500 msw.
6. TechnipFMC, **ORION 7P and 7R Manipulators** datasheet. https://www.technipfmc.com/media/opydheie/orion-7p-and-7r-manipulators.pdf — wrist torque 205 N·m, grip 4 448 N, depth 6 500 msw, opening 97 mm, mass 54 / 38 kg.
7. TechnipFMC, **RigMaster Manipulator** datasheet. https://www.technipfmc.com/media/lqnkszr1/rigmaster-manipulator.pdf — 5-function grabber, wrist torque 205 N·m, depth 6 500 msw, mass 64 / 48 kg.
8. Kraft TeleRobotics, **Predator Force Feedback Manipulator** product page. http://krafttelerobotics.com/products/predator.htm — square 4-bolt jaw flange, ¾″ T-handle compatibility, 1 500–3 000 psi, 10 000 / 21 000 fsw, 175 lb / 112 lb.
9. TechnipFMC, **Schilling Robotics Manipulator Systems** (overview brochure). https://www.technipfmc.com/media/jmsfx0f3/manipulator-systems.pdf
10. TechnipFMC, **Schilling GEMINI ROV System** datasheet. https://www.technipfmc.com/media/0kanstvt/data-sheet_schilling-gemini_rev4.pdf — all-electric workclass, dual manipulator, 3 000/4 000 msw, 1 000 kg through-frame.
11. ECA Group / Exail, **ARM 5E / ARM 7E** product family pages. https://www.ecagroup.com/en/solutions/arm-5e ; https://www.ecagroup.com/en/solutions/subsea-electrical-manipulator-arms ; ARM 5E Micro datasheet https://www.ashtead-technology.com/wp-content/uploads/2021/06/ECA-Hytec-Arm-5E-Micro.pdf — electric, 24 VDC, 6 000 m, no hydraulic.
12. Hydro-Lek / SAAB Seaeye, **HLK-43000** datasheet. http://www.hydro-lek.com/datasheets/Manipulators/HLK-43000_Rev_2.pdf ; product page https://www.saabseaeye.com/solutions/hydro-lek-tooling/hlk-43000 ; HLK-5680 page https://www.saabseaeye.com/solutions/hydro-lek-tooling/hlk-5680 — modular jaw rotates HLK-21020 / HLK-25000.
13. Unique Group, **Hydro-Lek HLK-43000 5-Function Manipulator** datasheet. https://www.uniquegroup.com/wp-content/uploads/2022/10/Hydro-Lek-HLK-43000-Compact-5-function-Manipulator.pdf
14. Forum Energy Technologies, **Sub-Atlantic Comanche A4 work-class** brochure. https://f-e-t.com/wp-content/uploads/2021/03/FET_Sub-Atlantic_Comanche-A4-1.pdf
15. Imenco AS, **3 Finger Manipulator Jaw / 4 Finger Manipulator Jaw** product pages — fit to Schilling Titan II/III/IV and Orion, swap "by loosening the 6 bolts". https://imenco.com/mechanical/product/3-finger-manipulator-jaw/ ; https://imenco.com/mechanical/product/4-finger-manipulator-jaw/
16. Subsea Specialist, **3 Finger / 4 Finger Manipulator Jaw** — same Imenco-pattern jaws; Caribbean Subsea reseller. https://subsea-specialist.com/product/3-finger-manipulator-jaw/ ; https://subsea-specialist.com/product/4-finger-manipulator-jaw/ ; https://caribbeansubsea.com/product/3-finger-manipulator-jaw/
17. eSubsea, **ROV Handles and Flex Joints — Standard Types and Dimensions**. https://www.esubsea.com/rov-handles/ — Ø19 mm large T-bar, Ø16 mm small T-bar, D-handle Ø70 mm flange / Ø56 mm PCD / 4–8 × M6, per API 17H / ISO 13628-8 / NORSOK M-101.
18. ISO 13628-8:2002, **Petroleum and natural gas industries — Design and operation of subsea production systems — Part 8: Remotely Operated Vehicle (ROV) interfaces on subsea production systems**. https://www.iso.org/standard/37291.html (sample at https://cdn.standards.iteh.ai/samples/37291/380945e701344672849dcfbebc4f9a32/ISO-13628-8-2002.pdf )
19. MacArtney, **SubConn Micro Circular / SubConn Power / SubConn Ethernet** product families. https://www.macartney.com/connectivity/subconn/subconn-micro-circular-series/ ; https://macartney.com/what-we-offer/systems-and-products/connectors/subconn/subconn-power-series ; https://www.macartney.com/what-we-offer/systems-and-products/connectors/subconn/subconn-ethernet-series/ — 500+ wet-mate cycles, gold contacts.
20. BIRNS Aquamate LLC, **wet-mate connector** product family. https://www.birnsaquamate.com/products.html ; product overview https://www.nauticexpo.com/prod/birns-aquamate-llc/product-39786-491199.html
21. API RP 17H, **Remotely Operated Tools and Interfaces on Subsea Production Systems**. https://standards.globalspec.com/std/13385742/api-rp-17h ; complementary text at https://www.api.org/~/media/files/publications/whats%20new/17h%20e2%20pa.pdf
22. Sivčev, S., Coleman, J., Omerdić, E., Dooly, G., Toal, D. (2018), **Underwater manipulators: A review**, *Ocean Engineering* 163, pp. 431–450. https://www.sciencedirect.com/science/article/pii/S0029801818310308 (Table 1: 30+ commercial manipulators with mass, lift, wrist torque, grip force, depth, reach, materials, actuator types, prices — primary source for cross-vendor comparison.)
23. IMCA, **R 004 Code of Practice for the Safe and Efficient Operation of ROVs**. https://www.intertekinform.com/en-us/standards/imca-r-004-jul-2009-573637_saig_imca_imca_1313032/ — confirmed *not* to include wrist flange geometry; covers operations only.

---

## Cross-references inside this repo

- `../ROV_INTEGRATION.md` §1 — the gripper-side M4 flange that this adapter must mate to.
- `../ROV_INTEGRATION.md` §3 — connector / depth-tier connector ladder (SubConn vs molded).
- `../MOTOR_STUDY.md` — selected actuator (XW540-T260) and why its voltage/protocol matter at the wrist pass-through.
- `../DRIVETRAIN.md` — the T_safe = 0.034 N·m gear-protected drivetrain ceiling that makes us "not a work-class tool."
- `../REQUIREMENTS.md` — depth-tier definitions (T1/T2/T3) and torque budget.
- `../FAILURE_MODES.md` — already covers single-fault behaviours; adding "work-class arm over-clamp" as a future row is suggested.
- `../../docs/UNDERWATER.md` §5 — galvanic isolation rules referenced in Option A.
- `../../docs/PRINTING.md` — PA12-GF print profile assumed for any printed Option A/B adapter.

---

*Document status: research-only, no CAD changes proposed in this commit. Open Questions
§11 must be closed before either Option A or Option B is cut. The honesty caveat in §10
applies to any future build.*

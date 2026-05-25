# Actuator survey — waterproof drive options for the gripper

Every plausible way to drive the gripper's input D-coupler underwater, scored
against the `REQUIREMENTS.md` card (R1–R10) and tagged by depth tier
(T1 ≤ 10 m, **T2 ≤ 30 m primary**, T3 > 30 m). Because the **actuator is now the
force sensor** (R10 / `REQUIREMENTS.md` §8), every row also carries four sensing
columns and candidates that cannot sense are kept but tagged **DEAD**.

## How this was built (honest provenance)

A **12-agent research swarm** ran concurrently — one agent per actuator class
(7) and one per sensing modality (5) — each pulling manufacturer datasheets and
retailer pages via live web search. Every torque/voltage/price/IP figure traces
to a cited source (numbered per section); anything an agent could not verify is
marked `n/a`. Torque converted to N·m (1 kg·cm = 0.0981 N·m). Prices in AUD
(USD × 1.55 where only USD was found, both shown). Swarm roster + agent IDs:
`motor/iterations/_survey_provenance.md`.

> **The sensing pivot reshuffles the ranking.** Before sensing, the best option
> was simply the best-sealed servo. After R10, the *best-sealed* option (Blue
> Trail Engineering's 200–400 m servos) is **DEAD** — it wraps an open-loop PWM
> servo with no current readback. The survivors are the few classes that deliver
> **both** waterproofing *and* torque telemetry: smart serial-bus servos, FOC
> BLDC, and closed-loop steppers — or any of those in a magnetically-coupled dry
> pod. That tension (seal vs sense) is what Phase 3 resolves.

---

## Class 1 — Submersible / IP-rated servos (ready-to-dive)

| Model | Torque cont/stall (N·m) | Range | V | IP / depth | Sensing modality | Tele rate | Protocol | Force-res | Price AUD | Tiers | Src |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Blue Trail Eng. SER-2010** (Hitec D954SW in Delrin) | ~0.57/2.84 | ±70° (140°) | 4.8–7.4 | quad-ring seal, **200 m** | **none — PWM, no readback** | — | PWM | — | ~581 (USD 375) | **DEAD-sense**; seal T2/T3 | [1] |
| **Blue Trail Eng. SER-2020** (HSR-M9382TH) | ~0.67/3.34 | ±230° | 6–7.4 | quad-ring, **200 m** | **none — PWM** | — | PWM | — | ~721 (USD 465) | **DEAD-sense**; seal T2/T3 | [1] |
| Savox SW-2290SG-BE | ~1.0/5.4 @7.4V | ~130° | 6–8.4 | IP67 (1 m) | none — PWM | — | PWM | — | ~215 | DEAD-sense; T1 | [2] |
| Savox SW-1212SG | ~0.9/4.5 @7.4V | ~130° | 6–7.4 | IP67 (1 m) | none — PWM | — | PWM | — | ~170 | DEAD-sense; T1 | [3] |
| Hitec DB961WP | ~1.1/5.4 | ~180° | 4.8–7.4 | IP67 (1 m) | none — PWM | — | PWM | — | ~310 (USD 200) | DEAD-sense; T1 | [4] |
| Traxxas 2255 | ~0.7/3.5 | ~180° | 6–7.4 | "waterproof" (no IP) | none — PWM | — | PWM | — | ~155 | DEAD-sense; T1 | [5] |

**Verdict.** Torque and sealing are excellent (BTE genuinely reaches T2/T3), but
**every unit is open-loop PWM with no current/torque telemetry → all DEAD on R10.**
The category that *looked* like the obvious answer is eliminated by the sensing
pivot. Retained only to document the elimination. (Stall currents on the big
Savox SW units, 7.5–10.5 A, also blow the §7 6 A budget without limiting.)

---

## Class 2 — Potted / oil-filled DIY hobby servos

| Base servo + mod | Torque cont/stall (N·m) | V | Mod | Depth (anecdotal) | Sensing | Force-res | Price AUD | Tiers | Src |
|---|---|---|---|---|---|---|---|---|---|---|
| Savox SC-1256TG + oil-fill | ~0.6/1.96 | 4.8–6 | mineral-oil + diaphragm | ≤3 m community | none — PWM base | — | ~110 | DEAD-sense; T1 | [6] |
| Hitec HS-5685MH + oil-fill | ~0.5/1.27 | 6–7.4 | oil-fill | ≤5 m anecdotal; crystal fail ~400 m | none — PWM base | — | ~57 | DEAD-sense; T1 | [6] |
| ANNIMOS/Miuzei 35 kg + oil-fill | ~1.0/3.43 | 5–7.4 | oil-fill | ≤5 m anecdotal | none — PWM base | — | ~27 | DEAD-sense; T1 | [6] |

**Verdict.** Oil-fill is the proven *cheap-depth* technique (T1 solid, T2
plausible but anecdotal and per-unit-validated). But the cheap base servos are
**PWM → DEAD on sensing**. This route only re-enters the running if the *base*
is a smart serial servo (→ Class 7) that is then potted/oil-filled — i.e. it
becomes "Class 7 + a sealing method," not its own answer. Good T1 bench path;
oil cools windings (a plus); dry-potting traps heat (avoid).

---

## Class 3 — Brushed DC gearmotor + custom sealed/flooded canister

| Motor + gearhead | Output torque (N·m) | rpm | V | Back-drive | Sensing modality | Force-res | Sealing | Price AUD | Tiers | Src |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Motion Dynamics ZD1530R** worm 12V 50W | **5.0 cont / 29 stall** | 45/65 | 12 | **No (worm self-locks → 0 hold current)** | external shunt + back-EMF | ±10–20 % uncal | dry canister + lip seal | ~80 | T1–T2 | [7] |
| Bringsmart A58SW31ZY worm (16 rpm) | ~6.9 cont | ~16 | 12 | No (worm) | external shunt | ±10–20 % | dry canister | ~25–73 | T1–T2 | [8] |
| Pololu 37D 100:1 (spur) | ~0.98 cont / 3.3 stall | 100 nl | 12 | Yes | external shunt | ±10–20 % | dry canister | ~95 | T1–T2 | [9] |
| Maxon DCX22S + GPX22 103:1 | 3.3 cont / 3.8 pk | 97 | 12 | Yes | external shunt (clean motor) | ±10–15 % | dry/oil canister | ~1130 (USD 730) | T1–T3 | [10] |

**Sensing (modality M1, current-shunt):** resolution is *not* the limit (INA226/INA240
+ filter → 5–20 mA RMS noise floor, well under the ΔI target), but accuracy is
**±10–20 % uncalibrated, ±5–10 % with a load-cell calibration** — brushed
commutation/PWM ripple (~5 %) and the speed/temperature-dependent no-load current
`I_0` dominate. Robotiq's own docs confirm current→force is approximate without
calibration [M1].

**Verdict.** The **worm-gear** sub-class is uniquely attractive on **holding**:
self-locking → **zero holding current** (a stepper/servo must power-hold and heat
the canister). Strong torque, cheap, AU-stocked. Cost: you build the canister +
rotary shaft seal, add a motor driver (H-bridge) and position feedback
(limit-switch or magnetic encoder), and accept *coarse* force sensing. Realistic
**T1–T2**; T3 wants oil-fill (brushes foul in oil → prefer BLDC for T3).

---

## Class 4 — BLDC / robot-actuator in a sealed or oil-compensated housing

| Actuator | Torque cont/peak (N·m) | rpm | V | Comms | Sensing modality | Force-res | Sealing / depth | Price AUD | Tiers | Src |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Volz DA 26-SUB** (BLDC rotary servo, oil-fill) | 2.7/5.0 | ~33 | 12–32 | PWM **or RS-485** | RS-485 position/load feedback | good (cal.) | oil-filled, **6000 m** | quote-only | **T2/T3** | [11] |
| Volz DA 22-SUB | 1.8/3.0 | ~17 | 12–30 | PWM/RS-485 | RS-485 feedback | good (cal.) | oil-filled, **100 m** | quote-only | T2 | [11] |
| CubeMars AK60-6 / AK70-10 (FOC) | 3 / 8.3 | 230+ | 24/48 | CAN+UART, FOC iq | **FOC iq (±2–5 % cal)** | excellent | none — needs housing | ~463 / 618 | T1; T2 in canister | [12] |
| MyActuator RMD-X6 / X8 (FOC) | 4.5 / 9 | 170–310 | 24–48 | CAN/RS-485, FOC iq | FOC iq | excellent | none — needs housing | ~550 / 587 | T1; T2 in canister | [13] |
| moteus/ODrive + BLDC + gearhead | sized to 1.2–3 | — | 12–48 | CAN-FD, FOC iq (int32 1 mA/1 mN·m) | **FOC iq, holds at stall** | excellent | none — needs housing | ~146/231 + motor | T1–T2 | [14] |
| Blue Robotics M200 (flooded BLDC) + gearbox | ~0.5 bare → ~2 geared | high | 7–20 | sensorless ESC | **back-EMF — BLIND AT STALL** | poor at hold | **flooded, 300 m** | ~290 | T2/T3 *(no hold sense)* | [15] |

**Sensing (modality M2, FOC iq):** the **cleanest** route — sinusoidal commutation,
no brush noise, and it **holds a true torque estimate at zero speed (stall)** =
the grip-hold state. Binding error is K_t tolerance (±5–10 %) + cogging + gearbox
friction → **±2–5 % with calibration, ±5–10 % raw** [M2]. moteus int32 telemetry
= 1 mA / 1 mN·m at ≥ 1 kHz over CAN-FD — far past S1–S4.

**Verdict.** Highest torque and the best *dynamic* sensing, and the flooded-BLDC
(M200) is naturally pressure-tolerant. But two penalties: (1) **control overhead**
— FOC driver + CAN + tuning + a sealed/oil housing you design, far beyond a
single PWM/serial wire; (2) the cheap flooded-BLDC path (M200 + basic ESC) is
**sensorless → blind at stall** (modality M3), so it *cannot* hold a calibrated
grip force — only detect the contact spike. The **Volz DA-SUB** is the one
turnkey BLDC rotary servo that is *both* depth-rated and telemetry-capable, but
it is defence/offshore-priced (quote-only). Powerful, mostly **over-specified +
complex** for a small gripper.

---

## Class 5 — Stepper + custom sealed/flooded enclosure

| Stepper + driver | Holding torque (N·m) | I/phase | V | Sensing modality | Tele rate | Force-res | Sealing | Price AUD | Tiers | Src |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **JMC IHSS57-36-20 (RS485/CAN integrated closed-loop)** | **2.0** | 4.0 | 24–50 | **RS-485 current+position readback** | >50 Hz (bus) | good (cal.) | dry canister, Ø8 shaft | ~200 | **T1–T2** | [16] |
| MKS SERVO57C + NEMA23 (FOC closed-loop) | 2–3 (motor-dep.) | ≤5.2 | 12–36 | FOC current, RS-485 | >50 Hz | good | canister (pot PCBA) | ~120–200 | T1–T2 | [17] |
| NEMA23 23HS30 + TMC5160 (StallGuard) | 1.9 | 2.8 | 24–36 | StallGuard load index | **~3 Hz @ 20 rpm (too slow)** | poor at low speed | dry canister | ~56 | T1–T2 (weak sense) | [18] |
| NEMA23 23HS30 + DM542T (open-loop) | 1.9 | 2.8 | 24–48 | **none (no readback)** | — | — | dry canister | ~40 | DEAD-sense; T1–T2 | [18] |

**Verdict.** Steppers have strong energised holding torque + detent — but **holding
heats the sealed canister** (a 4.2 A NEMA23 dissipates ~15 W with no convection;
the worm-DC and FOC options beat it on hold-power). For sensing, **open-loop
step/dir is DEAD**, and **StallGuard updates once per fullstep → only ~3 Hz at the
gripper's 20 rpm** (fails S3). The fix is a **closed-loop integrated stepper
(JMC IHSS57 RS485)** which streams current+position at >50 Hz from one sealed
body on a single 4-wire bus — satisfying R10 with the fewest penetrations.
Realistic **T1–T2**.

---

## Class 6 — Magnetically-coupled drive (no shaft penetration)

| Coupling | Max (pole-slip) torque (N·m) | Ø (mm) | Barrier gap | Pod motor (= sensing source) | Depth | Price AUD | Tiers | Src |
|---|---|---|---|---|---|---|---|---|---|
| KTR MINEX-S SA 46/6 | 3.0 | ~69 | ~6.5 mm | any dry motor: smart serial / FOC BLDC / worm-DC | **pod-limited only** | quote (~USD 300–800) | T1/T2/T3 | [19] |
| KTR MINEX-S SA 60/8 | ~7.0 | ~80 | — | any dry motor | pod-limited | quote | **T1/T2/T3** | [19] |
| Magnetic Tech MTC-3 | 3.0 nom / 3.5 pk | 64 | SS shell (450 psi) | any dry motor | pod-limited | quote | T1/T2/T3 | [20] |
| DIY N52 ring, 80 mm, 6 mm gap | ~6 (builder-measured) | ~80 | 2–3 mm printed wall | any dry motor | pod-limited | ~15–50 | T1/T2 (T3 machined wall) | [21] |

**Verdict.** The **no-seal architecture** — torque crosses a solid sealed wall, so
there is *no dynamic shaft seal to fail*. Depth is set by the dry pod's *static*
O-rings only → **the natural T3 answer and a strong T2 contender, identical
drivetrain at every depth** (the cleanest modular-product story). Binding number:
pole-slip torque must exceed gripper stall (1.8–3.6 N·m) with ~1.5× margin → the
SA 60/8 (7 N·m) or an 80 mm N52 ring (~6 N·m) clear it; the SA 46/6 (3.0) is
marginal. **Pole-slip doubles as a built-in force limiter** (overload clutch —
protects gripper + specimen) but also **caps the senseable force** at the slip
torque. Sensing fidelity is **inherited from whatever motor sits in the dry pod**
(put a smart serial servo or FOC BLDC there → full telemetry; the pod motor never
gets wet, so it can be a cheap non-waterproof unit). Cost: outer-rotor bearing,
concentric barrier wall, dry pod, alignment.

---

## Class 7 — Smart serial-bus servos (the sensing-pivot front-runner)

| Model | Torque cont/stall (N·m) | V | IP / depth | Sensing (register) | Tele rate | Protocol | Force-res @ servo | Price AUD | Tiers | Src |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **DYNAMIXEL XW540-T260** ★ | ~1.9 / 9.5 | 10–14.8 | **IP68 (1 m FW)** | Present_Current 2.69 mA/u | ~100–200 Hz | RS-485 | **~0.005 N·m** ✓ | ~1925 (USD 1242) | **T1 stock / T2 canister** | [22] |
| **DYNAMIXEL XW540-T140** ★ | ~1.38 / 6.9 | 10–14.8 | **IP68 (1 m FW)** | Present_Current 2.69 mA/u | ~100–200 Hz | RS-485 | ~0.004 N·m ✓ | ~1925 | T1 / T2 canister | [22] |
| DYNAMIXEL XW430-T333 | ~0.62 / 3.1 | 10–14.8 | IP68 (1 m FW) | Present_Current 2.69 mA/u | ~100–200 Hz | RS-485 | ~0.006 N·m ✓ | ~1372 | T1 (cont below floor) | [22] |
| DYNAMIXEL XM430-W350 | ~0.82 / 4.1 | 10–14.8 | none (canister) | Present_Current 2.69 mA/u | ~100–200 Hz | RS-485 | ~0.005 N·m ✓ | ~517 | T1–T2 canister (cont marginal) | [22] |
| DYNAMIXEL XM540-W270 | ~2.1 / 10.6 | 10–14.8 | none (canister) | Present_Current 2.69 mA/u | ~100–200 Hz | RS-485 | ~0.007 N·m ✓ | ~766 | T1–T2 canister | [22] |
| **Feetech STS3215** ★ (cheap) | ~0.98 / 2.94 | 7.4–12.6 | none (canister) | Present_Current 6.5 mA/u | ~100 Hz | SCS TTL | ~0.007 N·m ✓ | **~34** | T1–T2 canister (cont marginal) | [22] |
| Hiwonder LX-16A / HX-35H / HTD-45H | 0.19–0.44 cont | 6–12.6 | none | **no current register** (pos/temp/V only) | ~30 Hz | TTL | — | 26–46 | **DEAD-sense** | [22] |

**Verdict — the natural R10 winner.** These expose `present_current` +
`present_position` on a **single daisy-chain bus** — position *and* force in one
part, the Robotiq principle, no external sensor or extra penetration. All
current-equipped models clear S1–S3 with margin. The **gap is waterproofing**:
only the **XW series is IP68** (1 m freshwater → T1 stock; T2 needs a thin
pressure canister because 30 m ≈ 3.1 bar ≫ the 1.1 bar IP68 test, and seawater
adds corrosion). Torque-wise only **XW540-T260 (≈1.9 N·m)** and **XW540-T140
(≈1.38 N·m)** clear the 1.2 N·m continuous floor *and* are IP68 — but at ~AUD 1925.
The **Feetech STS3215 (~AUD 34)** has the telemetry and stall (2.94 N·m) but is
canister-only and marginal on continuous (0.98 N·m) — the obvious **cheap T1
dev** part. Note Hiwonder serial servos are **DEAD** (serial bus but *no current
register*).

---

## Sensing-modality cross-table (which physics, how good)

| Modality | Works at stall? | Resolution vs S1/S2 | Accuracy class | Best paired class | Role |
|---|---|---|---|---|---|
| **Smart-servo `present_current`** (M4) | **Yes** | ~0.004–0.007 N·m ✓ | ±5–10 % raw, ±3–5 % cal | Class 7 | **primary** |
| **FOC `iq`/torque** (M2) | **Yes** | 1 mA/1 mN·m ✓ | ±2–5 % cal, ±5–10 % raw | Class 4, 5(FOC) | **primary** |
| Closed-loop stepper current (M2-like) | Yes | good | ±5–10 % cal | Class 5 (JMC/MKS) | primary |
| **Current-shunt + back-EMF** (M1) | partial (running term drifts) | fine res, coarse accuracy | ±10–20 % raw, ±5–10 % cal | Class 3 (brushed) | secondary |
| **Sensorless hall/back-EMF** (M3) | **NO — blind < 10–20 % rated speed** | n/a at hold | contact-detect only | Class 4 (flooded M200) | **fallback / contact trigger only** |
| **Strain-gauge / load cell** (M5) | Yes | 0.001–0.03 N (bench) | reference-grade | bench rig | **calibration ground-truth** (not in-situ) |

**Calibration (M5).** A dry bench load cell (Phidgets 10 kg @ 0.03 % FS / NAU7802
24-bit ≥ 80 SPS, ~AUD 60 total) applies known tip forces (weights + lever arm)
and regresses `F = f(I_motor)`; reference uncertainty < 0.05 N — well under the
0.3 N target. An **in-situ** strain gauge is **not recommended**: it re-introduces
4-wire bridge penetrations through the TPU finger — the exact failure class the
foam removal eliminated. Redundancy, if needed, comes from dual current-sense
paths or a slip-detecting position encoder, not finger wiring [M5].

---

## Shortlist that survives R1–R10 → into Phase 3

| # | Candidate | Why it survives | Main weakness | Natural tier |
|---|---|---|---|---|
| A | **DYNAMIXEL XW540-T260** | IP68 + native current telemetry + ≥1.2 N·m, single bus, fewest parts | **price (~AUD 1925)**; IP68 only 1 m FW → T2 needs canister | T1 stock, T2 canister |
| B | **FOC BLDC (moteus/ODrive) + gearmotor in a builder canister** | best dynamic sensing, holds at stall, high torque | control + housing overhead | T1–T2 (T3 oil) |
| C | **JMC IHSS57 closed-loop stepper (RS-485)** | current+position telemetry, 2.0 N·m, one sealed body, ~AUD 200 | holding heat in canister | T1–T2 |
| D | **Magnetic coupling + smart-servo/FOC dry pod** | no dynamic seal → T3; sensing inherited; pole-slip force-limit | most mechanical build (pod, barrier, rotor bearing) | **T2–T3** |
| E | **Feetech STS3215 (canister)** | telemetry at ~AUD 34 — the cheap bench/dev part | cont. torque 0.98 N·m (marginal), not waterproof stock | **T1 dev** |
| — | brushed worm-DC + shunt | cheap, strong torque, zero hold-current | only ±10–20 % sensing | T1–T2 (sense-limited) |
| ✗ | all IP PWM servos, oil-potted PWM, Hiwonder serial, sensorless M200 | — | **fail R10 (no usable force telemetry / blind at stall)** | DEAD |

Phase 3 (`SELECTION.md`) weights A–E (+ the worm-DC edge) against R1–R10 with
**sensing fidelity as a primary axis**, sweeps the weights ±50 % including depth
tier, and picks a **tier-2 primary + a fallback**.

---

## Sources

*Class 1–2 (servos / potted):* [1] bluetrailengineering.com SER-201X/202X; [2] savoxusa.com SW-2290SG + campbelltownhobbies.com.au; [3] chequeredflagracing.com.au SW-1212SG; [4] hiteccs.com DB961WP; [5] traxxas.com 2255; [6] savox-servo.com SC-1256TG, rcsuperstore HS-5685MH, metalpartmaker ANNIMOS 35 kg, discuss.bluerobotics.com oil-comp thread, homebuiltrovs.com potting threads.
*Class 3 (brushed):* [7] motiondynamics.com.au ZD1530R; [8] bringsmart.com / alitools A58SW31ZY; [9] pololu.com 37D + core-electronics.com.au; [10] rsdelivers maxon DCX22S+GPX22.
*Class 4 (BLDC):* [11] volz-servos.com DA 22/26-SUB; [12] cubemars.com AK60-6/AK70-10; [13] aifitlab.com RMD-X6/X8; [14] mjbots.com moteus, shop.odriverobotics.com S1; [15] bluerobotics.com M200.
*Class 5 (stepper):* [16] namicam.com / jmc-motor.com IHSS57-36-20, amazon IHSS57-RC; [17] makerbase3d.com SERVO57C; [18] omc-stepperonline.com 23HS30 + DM542T, analog.com TMC5160.
*Class 6 (magnetic):* [19] ktr.com / ach.nu MINEX-S; [20] magnetictech.com MTC; [21] pettersen-prod.com DPV coupling, osencmag.com torque formula.
*Class 7 (smart serial):* [22] emanual.robotis.com XW540/XW430/XM430/XM540 + robotis.us, akizukidenshi STS3215 + core-electronics.com.au, hiwonder.com LX-16A/HX-35H/HTD-45H.
*Sensing modalities:* [M1] ti.com INA226/INA240/INA228, allegromicro ACS712/723, faulhaber Kt tutorial, robotiq.zendesk force article; [M2] docs.odriverobotics.com, mjbots register ref, github VESC comm_can, st.com B-G431B-ESC1, maxongroup EPOS4 0x6077, faulhaber MC 5005; [M3] bluerobotics M200/BlueESC, mathworks six-step sensorless, pmc.ncbi PMC3231115, digikey back-EMF article; [M5] phidgets load-cell table, adafruit/sparkfun NAU7802, ti ADS1232, micro-measurements M-Coat, kyowa KFWB.

Full per-agent tables, every row, and all fetched URLs: `motor/iterations/_survey_provenance.md`.

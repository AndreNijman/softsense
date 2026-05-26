# Power-supply chain — per-interface electrical bring-up

The full power chain for the gripper, from arm-side bus to the XW540's
4-pin RS-485 connector, **one chain per interface family**. The actuator
selection (`SELECTION.md`) and interface-mount campaign (`INTERFACES.md`,
`interfaces/*.md`) are settled; this document closes the gap they left:
**how the 12 V at ≤ 6 A peak actually arrives at the servo on each
mounting platform.**

> **Honesty rule.** Same posture as `ROV_INTEGRATION.md` and the
> interface dossiers: every part number traces to a vendor page; every
> dimension/spec is cited; every computed estimate (voltage drop, fuse
> margin, cost) is flagged. SKUs the original brief mentioned that
> **do not exist** (Pololu D24V90F12, DYNAMIXEL U2D3) are called out
> explicitly so the catalogue stays clean.
>
> **Boundary with `ELECTRICAL.md`.** ELECTRICAL.md owns the
> **canister-internal** wiring, RS-485 telemetry, ground scheme, and
> current-limit firmware (its §3 has the canonical AWG 18/20/22 × 10/20/30 m
> tether ΔV tables for stall). This doc owns the **per-interface upstream
> chain** — arm bus → fuse → wire → bulkhead → regulator → fuse →
> servo connector — and the short (~1–3 m) AWG 16 wire run inside the
> ROV / cobot side of that chain. Where they overlap (the canister
> penetrator and the servo connector), this doc references ELECTRICAL.md
> rather than restate.

---

## 1. Why a unified power-supply spec

The actuator campaign converged on **DYNAMIXEL XW540-T260** (12 V
nominal, 11.1–14.8 V range, ≤ 5.9 A stall at 14.8 V, ≤ 4.9 A at 12 V,
~0.5–1.5 A continuous typical) [1]; the mounting campaign converged on
**four interface families** [INTERFACES.md]. The actuator is the same in
every case — **but the upstream power chain is not.** The four
deployment families differ in:

| Interface | Source bus | Tap voltage | Cont. current available | Regulation needed? |
|---|---|---|---|---|
| **BR2 chassis-mount** (BlueROV2) | 4S Li-ion 14.8 V nominal | **12.0 V (low) ↔ 16.8 V (full charge)** [2] | 5–10 A/channel budget on main bus [3] | **YES — buck** (full charge 16.8 V > XW540 max 14.8 V) |
| **ISO 9409-1 cobot wrist** (UR / Franka / Doosan / Fanuc CRX / etc.) | Tool I/O 24 V (UR) | 24 V signal-power | **600 mA continuous, ≥ 2 A peak ≤ 1 ms** [4] | **N/A — wrist I/O too small for 6 A stall.** External bench PSU runs in parallel |
| **Reach Bravo 7 arm** | Arm bus 20–48 V DC | 20–48 V at the elbow Accessory Port (RB-1006) [5] | NDA pin breakdown; arm itself is 400 W class | **YES — buck** (20–48 V → 12 V) |
| **Schilling / Kraft work-class wrist** | Aux bus 24 V DC | 24 V at the slave-arm aux bus | **~1.875 A continuous at TITAN 4 slave** [6] | **YES — buck + ROV-side parallel feed** (1.875 A < 5.9 A stall) |
| **Bench / lab (cobot deployment)** | AC mains | 12 V from a Mean Well RS-150-12 or RSP-150-12 (12.5 A) [7] | 12.5 A continuous | **NO — already 12 V** (still need fuse + soft-start) |

> **Bottom line.** Same XW540 inside the canister; **four different
> upstream chains** — and in three of the four (BR2 included, despite
> the original brief's wording), **a buck regulator at the canister
> bulkhead is mandatory** because the source bus is either too high
> (BR2 full-charge, Bravo, Schilling, bench-with-24V-supply) or too
> low-current (cobot wrist) for the servo's stall demand.

The cobot case is **architecturally different**: the cobot wrist
cannot feed the servo at all — the Tool I/O carries signals + bus
power for sensing/signalling but cannot source 6 A. So the cobot
chain is **two parallel paths**: RS-485 down the cobot wrist *or*
external (operator's choice), and 12 V always from a separate bench
PSU running along the cobot arm to the canister bulkhead.

---

## 2. Bus survey — what's available at each interface

### 2a. Voltage and current at the tap point

Numbers cited to primary sources. ΔV at the tap is **for the bus segment
between the source and our tap point**, not the canister-side tether
(`ELECTRICAL.md §3` owns that).

| Bus | V_nominal | V_min | V_max | Cont. current ceiling | Bus protocol present | Source |
|---|---|---|---|---|---|---|
| **BR2 main tube battery** | 14.8 V (Li-ion 4S) | 12.0 V (cutoff) | **16.8 V (4×4.20 V full charge)** | 5–10 A/channel routed via WetLink penetrator; battery total 18 Ah ≈ ~250 Wh | none (raw V+/GND from battery bus) | [2] [3] |
| **UR3e / UR5e / UR10e / UR16e Tool I/O M8** | 12 or 24 V software-select | n/a | n/a | **600 mA cont., ≥ 2 A peak ≤ 1 ms** | RS-485 over pins 1/2 (`set_tool_communication`) [4] | [4] |
| **UR20 Tool Connector** | same as UR e-Series | n/a | n/a | ~600 mA (same M8 family) | RS-485 [4] | [4] |
| **Franka FCI tool connector** | 24 V | n/a | n/a | ~1.5 A | RS-485 / digital I/O | [INTERFACES.md] |
| **Kinova Gen3 wrist (PoE+ class)** | 48 V via PoE+ injector | n/a | n/a | depends on injector PD class — marginal | RS-485 + Ethernet | [INTERFACES.md] |
| **Reach Bravo 7 arm base** | **20–48 V DC** | 20 V | 48 V | arm is 400 W class (≥ 8 A at 48 V) [5] | RS-485 / RS-232 / Ethernet at base; **NDA at the elbow Accessory Port RB-1006** | [5] [INTERFACES.md] |
| **Reach Bravo elbow Accessory Port RB-1006** | **12–24 V DC** (split) | 12 V | 24 V | NDA, but rated for wrist-camera RB-1057 — order ≥ 1 A | RS-485 *or* Ethernet (selectable) via MCBH8F [5] | [5] |
| **Schilling TITAN 4 slave-arm 24 V aux** | 24 V DC | n/a | n/a | **~1.875 A continuous** (= 45 W) [6] | RS-232 or RS-422/485 on the SeaNet pair [6] | [6] |
| **Bench / lab AC mains** | 100–240 VAC | 85 V | 264 V | 12.5 A at 12 V via 150 W PSU [7] | n/a (RS-485 from U2D2 over USB) | [7] |

> **Bravo 7 caveat (NDA gap, carried from `interfaces/reach-bravo-alpha.md` Q6).**
> The RB-1006 elbow port's per-pin voltage / current / RS-485 wiring is
> in the **RSCP integration manual under NDA** — request from Reach
> Sales. Public datasheet only confirms the **20–48 V envelope** and
> the **MCBH8F bulkhead** [5]. The chain in §3c below assumes the
> conservative case: 24 V at the elbow (the lower end of the 12–24 V
> Accessory Port range), 1 A available; if the actual pin-out
> supplies only 12 V, the buck-down step is unnecessary and the
> chain shortens.

### 2b. ΔV at the source — what the bus actually delivers under load

Battery sag and tap-cable resistance reduce the nominal tap voltage at
6 A peak. We need the **lowest** voltage we will see at the buck input
(this sets buck dropout headroom) and the **highest** (this sets buck
input rating). Computed estimates; bench-measure before commissioning:

| Bus | Nominal | -ΔV (sag) at 5–6 A | V_min at input to buck | +ΔV (full charge / surge) | V_max at input to buck |
|---|---|---|---|---|---|
| BR2 4S Li-ion (1 m tap to penetrator) | 14.8 V | −0.3 V (battery internal R + 1 m AWG 16 round trip) | ~12–13 V (mid-discharge under 5 A load) | 14.8→16.8 V at 100 % SoC | **16.8 V** |
| UR Tool I/O 24 V (n/a for motor power) | 24 V | — | — | — | — |
| Reach Bravo arm | 24 V (assumed) | −0.5 V along 1.5 m arm-internal harness | ~19.5 V at the elbow tap | 48 V (if upstream bus runs high) | **48 V** |
| Schilling 24 V aux | 24 V | −0.4 V at 1.875 A through SeaNet wiring (cited estimate, manual silent on aux-bus impedance) | ~22 V | up to ~28 V (battery-backed bus surge worst case) | **28 V** |
| Bench Mean Well RS-150-12 | 12.0 V | −0.1 V along 1 m AWG 14 to fuse holder | 11.9 V at fuse | 12.5 V (open-circuit overshoot) | **12.5 V** |

> **Reference for the buck's input-voltage rating below (§3):** Pololu
> **D36V50F12** accepts **13.3 V – 50 V** input [8]. It covers
> **everything except the BR2 mid-discharge floor of ~12 V** — at 12 V
> input with 12 V output, the buck is below its dropout window. The
> BR2 chain therefore has a different buck choice (§3a) or, more
> simply, runs **without a buck** when the battery is below ~15 V and
> with a buck only above 14.8 V — a design choice that's discussed
> below and made explicit.

---

## 3. The chain — per-interface part lists

Format for every chain:

```
arm bus → series fuse → wire run → bulkhead penetrator → buck step-down → fuse → connector → XW540
                                   (canister boundary)        (inside canister)
```

The **bulkhead penetrator** is the canister boundary; everything
upstream of it is on the ROV / cobot side, everything downstream is
inside the actuator canister and owned by `ELECTRICAL.md`.

### 3a. BR2 chassis-mount chain

The BR2 main tube battery is 4S Li-ion **14.8 V nominal, 16.8 V at
full charge** [2]. This is **above the XW540's 14.8 V max** at full
charge — the original brief's "tap the 14 V battery bus" assumption is
wrong on one end of the envelope. The fix: a **buck step-down to 12 V
fixed** between the battery tap and the canister. This regulates the
servo input across the entire SoC range and saves the XW540 from
charge-cycle overvoltage.

| # | Link | Part | SKU / Vendor URL | Cost (USD) | Notes |
|---|---|---|---|---|---|
| 1 | Battery tap | Existing BR2 main tube power-distribution PCB output, or a dedicated XT60/XT30 splitter off the BR2 battery cable | [BR Battery 14.8 V 18 Ah `BR-100789`](https://bluerobotics.com/store/comm-control-power/powersupplies-batteries/battery-li-4s-18ah-r3/) [2] | $0 (existing) | Use the existing BR power-distribution channel; don't drill the battery harness |
| 2 | Series fuse (battery side) | **Littelfuse ATO 8 A fast-blow blade fuse** + inline ATO holder | [Littelfuse ATOF 287 series 32 V](https://m.littelfuse.com/~/media/automotive/datasheets/fuses/passenger-car-and-commercial-vehicle/blade-fuses/littelfuse_atof_datasheet.pdf) [9] | $0.50 fuse + $3 holder | 8 A = 1.36× XW540 stall at 14.8 V (5.9 A) and 1.6× at 12 V (4.9 A) — passes inrush but blows on a true wire short. Per `ELECTRICAL.md §3c` baseline (1.5× stall) [ELECTRICAL.md] |
| 3 | Wire run (battery → bulkhead) | **AWG 16 stranded twisted pair, marine-grade tinned copper**, ~0.5–1.5 m inside the main tube | Belden 9501 / equivalent 16 AWG tinned-copper hookup wire ([Belden 9501 datasheet via Belden master tables](https://www.belden.com)) | $1–3 | AWG 16 = 13.2 mΩ/m solid Cu at 20 °C; stranded +5 % [10] [11]. See §5 below |
| 4 | Bulkhead penetrator (canister-side) | **Blue Robotics WetLink Penetrator M10, 6.5 mm cable Ø** | [WLP-VP `BR-100870-165`](https://bluerobotics.com/store/cables-connectors/penetrators/wlp-vp/) (M10 body, 6.5 mm seal, **standard WLP**) [12] | **$13** ea, 1000 m rated [12] | Carries V+ / GND / D+ / D- in one 4-conductor cable. **Choose 6.5 mm OD jacketed cable** to match the seal range |
| 5 | Buck step-down (inside canister) | **Pololu D36V50F12** — 12 V output, 13.3–50 V input, up to **6.5 A continuous** | [Pololu #4095 D36V50F12](https://www.pololu.com/product/4095) [8] | **$39.95** | Replaces the brief's "D24V90F12" (which **does not exist** in Pololu's catalogue — verified, see §9). D36V50F12 is the only Pololu 12 V buck rated > 6 A across an input range covering BR2 full charge (16.8 V → 12 V at 6 A is well within the 13.3–50 V envelope). **Dropout caveat:** if battery sags below ~13.3 V at full load, dropout fires and output drops. Practical mitigation: cell-cutoff is 12 V nominal — under load BR2 will be running below 13.3 V near end of mission. **Action:** monitor battery V before each grasp; if < 13.5 V, command lower current setpoint (gear protection is already enforced by firmware `current_limit` per `ELECTRICAL.md §6`). |
| 6 | Fuse (canister-side) | **Bel Fuse / Littelfuse 10 A self-resetting polyfuse** (radial-leaded PPTC, hold = 10 A, trip = ~17 A) OR discrete 10 A glass fuse + holder | Bel Fuse 0ZRC0750FF1E ([Mouser](https://www.mouser.com)) / Littelfuse RXEF 750 — polyfuse 7.5 A hold; or Schurter SPT 5×20 mm 10 A glass | $1 polyfuse / $3 glass + holder | Backstop after the buck. Lower than the upstream 8 A ATO so a downstream short is isolated at the canister, not at the battery. Polyfuse auto-resets after cool-down (favorable underwater); glass needs a hand swap. **Polyfuse preferred** for sealed canisters |
| 7 | Connector to servo | **3-pin or 4-pin Robotis Robot Cable** (JST-EH 3-pin for TTL; **Robotis 4-pin for RS-485**) — supplied with the XW540 | [Robotis X4P 180 mm convertible cable, 10 pcs](https://robotis.us/robot-cable-x4p-180mm-convertible-10pcs/) [13] | $8 / 10-pack | XW540-T260-R: 4-pin RS-485 connector, pinout per `ELECTRICAL.md §1a` and Robotis e-manual [1] [13]. **Pin 1 = GND, Pin 2 = V+, Pin 3 = D+, Pin 4 = D-** (Robotis X-series RS-485 convention [13]) |
| 8 | XW540-T260-R | DYNAMIXEL XW540-T260-R | [Robotis XW540-T260-R](https://robotis.us/dynamixel-xw540-t260-r/) (already in BOM) | $1241.89 (already in BOM) | The actuator — IP68 body, 12 V nominal, ≤ 5.9 A stall, native `present_current` telemetry [1] |

**BR2 chain summary cost** (new line items only, excluding the XW540 which is already in `docs/BOM.md`):

| Item | $ |
|---|---|
| Buck (Pololu D36V50F12) | 39.95 |
| Fuse + holder + 5 spares | 6.00 |
| Polyfuse (canister-side) | 1.00 |
| AWG 16 stranded wire, ~1 m | 2.00 |
| Robotis 4-pin cable (1 of 10-pack) | 0.80 |
| TVS SMBJ16A | 0.30 |
| WetLink penetrator WLP-VP M10 (1 unit) | 13.00 |
| **Subtotal — every new line** | **~$63.05** |
| Less: WLP already counted in `docs/BOM.md` §4 "Pressure canister assembly" (the kit already lists 2× WLP) | −13.00 |
| Less: Robotis cables ship with the XW540 servo (verify per ROBOTIS US store page [1]) | −0.80 |
| **Net BR2-chain delta to existing BOM** | **~$49** |

If the canister-side WLP is *not* yet allocated to the gripper cable in
the existing BOM (the BOM lists "2× WLP" but doesn't say which is the
gripper conductor), add it back: **~$62**. Treat **~$50–65** as the
honest band for the BR2 power-chain incremental cost. The WetLink
plug-count interaction with `docs/BOM.md` is the source of the spread
and should be resolved when the BOM delta in §8 is merged.

> **Why a buck for BR2 at all?** Two answers, both real: (1) at full
> charge the battery is **16.8 V > 14.8 V max** [1] [2] — direct tap
> will damage the servo over time. (2) Even within the in-spec
> envelope, a regulated 12 V rail decouples the servo from BR2
> thruster-current sag, giving the `present_current` telemetry a clean
> baseline. The buck is cheap insurance.

### 3b. ISO 9409-1 cobot chain (dry bench testing)

The cobot wrist Tool I/O is **not the power source.** A separate bench
PSU runs to the canister bulkhead in parallel. The wrist Tool I/O does
carry the **RS-485 bus** (UR's `set_tool_communication`, Franka FCI,
Kinova native RS-485 [4]) — so the cobot chain has **two parallel
upstream segments**: bench-PSU 12 V power, and either
cobot-wrist-RS-485 *or* an external RS-485 master via U2D2.

| # | Link | Part | SKU / Vendor URL | Cost (USD) | Notes |
|---|---|---|---|---|---|
| 1 | AC mains | wall outlet | — | $0 | Lab |
| 2 | Bench PSU | **Mean Well RS-150-12** — 150 W, 12 V, **12.5 A**, 85–264 VAC in | [Mean Well RS-150-12](https://www.meanwell-web.com/Article/DownloadAsset/RS-150-spec.pdf?documentId=assets/2057/357b4f0adf18408b90186c408d318d3e) [7] | **$33** [TRC Electronics] | 12.5 A at 12 V gives 2× headroom over XW540 stall. **The brief mentioned "RD-50A"** as an alternative — but the Mean Well RD-50A is a *dual-output 5 V + 12 V module at ~3 A* — **insufficient for 6 A stall.** Use RS-150-12 or its successor RSP-150-12 (semi-enclosed, same 12.5 A rating) |
| 3 | Series fuse | **Littelfuse ATO 8 A fast-blow** + inline holder | [Littelfuse ATOF datasheet](https://m.littelfuse.com/~/media/automotive/datasheets/fuses/passenger-car-and-commercial-vehicle/blade-fuses/littelfuse_atof_datasheet.pdf) [9] | $0.50 + $3 | Same as BR2 chain |
| 4 | NTC inrush limiter | **Ametherm SL22 series** (5 A class) in V+ leg | [Ametherm SL22 20005 (20 Ω / 5 A)](https://www.ametherm.com/datasheets/sl2220005/) [14] (the brief's "SL22 5R025" — a 5 Ω 5 A part — is on the SL22 family page but not in the indexed datasheets; SL22 10005 / 20005 are the documented 5 A line) | $3 | Limits cap-charge inrush; `ELECTRICAL.md §3c` calls this out |
| 5 | Wire run (PSU → cobot base → wrist → canister) | **AWG 16 stranded, ~3 m**, sleeved in polyurethane spiral wrap; cable-tied to cobot arm clips every 30 mm (avoid wrist sweep) | Generic 16 AWG marine tinned-copper | $5 | The cable wraps the cobot arm; UR e-Series has 360° wrist — provide a service loop at the wrist exit so cable wrap doesn't load the cobot's joint 6 |
| 6 | Bulkhead penetrator | WLP M10 6.5 mm (`BR-100870-165`) or, for the **dry-only cobot context**, a sealed M8 4-pin or M12 4-pin industrial connector | [WLP-VP](https://bluerobotics.com/store/cables-connectors/penetrators/wlp-vp/) [12] | $13 | If the canister is dry-bench-only (no immersion), an M8 4-pin (≈$8) replaces the WLP — cobot context is by-definition dry per `INTERFACES.md §3.5`. **Recommendation: keep the WLP** so the **same canister** swaps between cobot bench and BR2 dive |
| 7 | Buck step-down | Optional **bypassed** at 12 V bench supply (already 12 V). If the bench PSU is replaced with a 24 V option (`RSP-150-24`) for compatibility with the Reach Bravo chain (§3c), insert **Pololu D36V50F12** [8] | [Pololu #4095](https://www.pololu.com/product/4095) [8] | $0 / $40 | Skip for the 12 V Mean Well; install for any 24 V test rail |
| 8 | Canister-internal fuse + connector to servo | Same as BR2 chain (polyfuse + Robotis 4-pin cable) | as §3a | $9 | |
| 9 | XW540 | as §3a | as §3a | — | |
| **Parallel — RS-485 bus master path** | | | | | |
| A | Cobot wrist Tool I/O (option 1) | UR M8 8-pin cable | Lumberg RKMV 8-354 [4] | $25 | UR pins 1 (D+) / 2 (D-); `set_tool_communication(True, baud, ...)` activates `/dev/ur-ttylink/ttyTool` |
| B | Or external USB-RS485 master (option 2) | **DYNAMIXEL U2D2** | [Robotis U2D2](https://www.robotis.us/u2d2/) [15] | **$36.92** | The brief mentioned "U2D3" — **no such product exists.** U2D2 is the current Robotis bus master; recently upgraded to USB-C [15]. Supports RS-485 (4-pin JST) and TTL (3-pin JST) |

**Cobot chain summary cost** (incremental):

| Item | $ |
|---|---|
| Mean Well RS-150-12 | 33 |
| Ametherm SL22 inrush | 3 |
| Fuse + holder + spares | 6 |
| AWG 16 wire, ~3 m | 5 |
| WLP penetrator (if canister-mounted; n/a for bare-bench) | 13 |
| Polyfuse + Robotis 4-pin connector | 2 |
| **Subtotal — bench portion** | **~$62** |
| + U2D2 (external RS-485 path) — only if cobot RS-485 unused | +37 |
| **Total cobot bench rig** | **~$62 (cobot RS-485) / ~$99 (external U2D2)** |

### 3c. Reach Bravo 7 arm chain

Bravo arm supplies its own 20–48 V DC at the base [5]; tap point for
the gripper is **either the arm-base power split (MCBH4M)** or the
**elbow Accessory Port RB-1006 (MCBH8F)** [5]. The RB-1006 path is
preferred because it lands close to our canister mounting (the Bravo
7 wrist mounts the gripper at RB-1054); the arm-base path requires
running a cable up the full length of the arm. Both paths go through
a buck to 12 V.

| # | Link | Part | SKU / Vendor URL | Cost (USD) | Notes |
|---|---|---|---|---|---|
| 1 | Arm bus tap | **Reach Accessory Port RB-1006** (optional add-on to Bravo 7) → MCBH8F bulkhead | [Reach RB-1006 Accessory Port — order via Reach Sales] | quote (~$300–500 est., not posted) | Provides 12–24 V DC + RS-485 or Ethernet [5]. **NDA on pin breakdown.** Get from Reach Sales |
| 2 | Mating cable (Bravo → our canister) | SubConn **MCIL8M** in-line plug, custom-overmoulded into our cable | [MacArtney SubConn Micro 8-contact](https://www.macartney.com/connectivity/subconn/subconn-micro-circular-series/) [16] | $150–250 (custom termination) | 600 m rated, 5 A per contact (max 20 A per connector) [16] — comfortably above 6 A stall |
| 3 | Series fuse | **Littelfuse ATO 8 A fast-blow** (same as §3a) | [Littelfuse ATOF](https://m.littelfuse.com/~/media/automotive/datasheets/fuses/passenger-car-and-commercial-vehicle/blade-fuses/littelfuse_atof_datasheet.pdf) [9] | $3.50 | Fuse the *output* of the buck (12 V side) at 8 A. Input side (24 V) sees only ~3 A at peak — fuse there at 5 A |
| 4 | Wire run (RB-1006 → canister) | **AWG 16 stranded, 0.3–0.6 m** sleeved in polyurethane wrap; cable-tied to the Bravo's printed adapter and arm shell | Belden 16 AWG tinned | $1–2 | Very short run — Bravo elbow to gripper canister is ~50 cm |
| 5 | Bulkhead penetrator | **MCBH8F** (canister side) if using SubConn; or **WLP M10 6.5 mm** if running through a stripped jacket | [MacArtney MCBH6F (6-pin) or MCBH8F (8-pin)](https://www.macartney.com/connectivity/subconn/subconn-micro-circular-series/subconn-micro-circular-5-6-8-and-9-contacts-and-g2-2-3-and-4-contacts/) [16] / [WLP-VP](https://bluerobotics.com/store/cables-connectors/penetrators/wlp-vp/) [12] | **MCBH6F ~£145 ≈ $185**, MCBH8F ~$200+ [16]; or WLP at $13 [12] | SubConn is the **mate-able** choice (the Bravo arm runs subsea so the gripper bulkhead is exposed); WLP at $13 is the cost-saver if a clamped-jacket gland is acceptable |
| 6 | Buck step-down | **Pololu D36V50F12** (13.3–50 V → 12 V, 6.5 A) [8] | [Pololu #4095](https://www.pololu.com/product/4095) [8] | **$39.95** | Single buck handles the full 20–48 V Bravo bus range; the 50 V max [8] gives a small margin over the 48 V bus top — **but mark as a watch item** (transients on the arm bus can briefly exceed 48 V; absolute max input on the LMR16030 family the D36V50F12 wraps is typically 60 V, see Pololu page graphs [8]) |
| 7 | Canister-internal fuse + connector to servo | Same as BR2 chain | as §3a | $9 | |
| 8 | XW540 | as §3a | as §3a | — | |
| **Parallel — RS-485 bus master path** | | | | | |
| A | Bravo RS-485 (via RB-1006) | Wired through the same MCBH8F | as #2 | (in cable) | Reach RSCP protocol is NDA; **either** route the Bravo controller's RS-485 to the gripper through the arm (NDA pinout from Reach), **or** tether RS-485 separately from the ROV bulkhead per `interfaces/reach-bravo-alpha.md` §"the bus does not transit the arm" [interfaces/reach-bravo-alpha.md] |

**Bravo 7 chain summary cost** (incremental, single deployment, *with* SubConn MCBH6F at the canister): **~$300–500** depending on the RB-1006 accessory cost ($300–500 est.) + SubConn ($185) + buck ($40) + wire/fuse/polyfuse ($10) = ~$535–735. **With WLP-VP** in place of SubConn for cost-down: **~$365–565.**

### 3d. Schilling / Kraft work-class chain

Schilling TITAN 4 (and Kraft Predator, ECA ARM 5E/7E with the
caveats in `interfaces/schilling-kraft.md` §5) supply **24 V DC ~1.875 A**
on the slave-arm auxiliary bus [6]. **1.875 A is below the XW540's
4.9 A stall.** This means the **work-class arm cannot, on its own,
power our gripper through a stall** — it can deliver continuous run
power (typical 0.5–1.5 A) but stalls or peak inrush will brown out
the bus.

**Mitigation:** add a **large bulk capacitor (≥ 4700 µF)** between
the 24 V tap and the buck input — store enough energy that the buck
sees a stable rail through brief stall transients. **Or** add a
parallel ROV-side feed (the ROV's main 24 V or 48 V power bus, if
available outside the manipulator's aux feed) tapped before the
canister — this is the more honest fix and matches how the
work-class community wires tools.

| # | Link | Part | SKU / Vendor URL | Cost (USD) | Notes |
|---|---|---|---|---|---|
| 1 | Arm aux bus tap | TITAN 4 24 V aux + SeaNet pass-through | TechnipFMC / Schilling integration drawing (NDA) [6] | quote | NDA pin breakdown; per `interfaces/schilling-kraft.md` |
| 2 | **Optional ROV-side 24 V parallel feed** | dedicated **WetLink penetrator + cable** from the ROV main 24 V or 48 V channel, sized for 6 A continuous | per ROV (typically existing power-distribution channel) | — | The recommended approach when the slave-arm aux bus alone is < 6 A |
| 3 | Series fuse | **Littelfuse ATO 8 A fast-blow** | [Littelfuse ATOF](https://m.littelfuse.com/~/media/automotive/datasheets/fuses/passenger-car-and-commercial-vehicle/blade-fuses/littelfuse_atof_datasheet.pdf) [9] | $3.50 | |
| 4 | Bulk capacitor (V+ to GND, before buck) | **Nichicon UCC 4700 µF, 35 V** electrolytic (rated > 24 V × 1.5 margin) | [Nichicon UCC series — Mouser](https://www.mouser.com) | $3 | Stores ~1.6 J at 24 V; covers ~300 ms of 5 A draw with 1 V sag headroom. Sizing: `C × ΔV / I_stall = duration` → `4700e-6 × 1.0 / 5 ≈ 940 ms`-equivalent; conservative |
| 5 | Wire run (aux → canister) | AWG 16 stranded, ~1 m | as §3a | $2 | |
| 6 | Bulkhead penetrator | **SubConn MCBH6F or MCBH8F** (work-class deployment is subsea, wet-mate mandatory at T3) [16] | [MacArtney SubConn Micro](https://www.macartney.com/connectivity/subconn/subconn-micro-circular-series/subconn-micro-circular-5-6-8-and-9-contacts-and-g2-2-3-and-4-contacts/) [16] | $185–200 | Not a WLP — work-class arms operate to T3 (>1000 m on TITAN family); SubConn rated 300 bar PEEK = 3000 m [16] |
| 7 | Buck step-down | **Pololu D36V50F12** (13.3–50 V → 12 V, 6.5 A) [8] | [Pololu #4095](https://www.pololu.com/product/4095) [8] | $39.95 | Same buck as Bravo chain |
| 8 | Canister-internal fuse + connector to servo | Same as BR2 chain | as §3a | $9 | |
| 9 | XW540 | as §3a | as §3a | — | |
| **Parallel — RS-485 bus master path** | | | | | |
| A | RS-485 via SeaNet pass-through | Schilling SeaNet RS-422/485 [6] | per arm | quote | The SeaNet pair carries the bus; multiplex onto the same SubConn |

**Schilling chain summary cost** (incremental, with SubConn): **~$245** (SubConn $185 + buck $40 + bulk cap $3 + wire/fuse $5 + polyfuse $1 + connector $8) — excluding the SeaNet/RS-485 termination and the optional ROV-side parallel feed cable, which depend on the host ROV.

> **Honest scale flag, repeated from `INTERFACES.md §3.2`.** Our 0.3 kg
> gripper is 0.3 % of TITAN 4's full-extension lift rating. The
> Schilling chain is **architecturally valid** but **operationally
> a demo** — the work-class arm dwarfs the gripper. The cost-honest
> Schilling path is the **ISO 13628-8 D-handle** (`INTERFACES.md` Option B),
> in which case the arm holds the *whole gripper canister* as a
> tool, and the **canister's WetLink penetrator** is the bulkhead.
> The chain then **reduces to the BR2 chain (§3a) with a longer
> WetLink-to-ROV cable**. Cost = BR2 chain ~$50–65 + a few extra metres
> of AWG 16.

### 3e. Bench / lab chain (cobot-independent dry test)

Minimal bench chain for first-light dry testing on the lab desk (no
cobot, no ROV). Used to commission the XW540, flash firmware, set
`current_limit` per `ELECTRICAL.md §6`, and exercise the RS-485 bus
before any mount integration.

| # | Link | Part | SKU / Vendor URL | Cost (USD) | Notes |
|---|---|---|---|---|---|
| 1 | AC mains | wall outlet | — | $0 | |
| 2 | Bench PSU | **Mean Well RS-150-12** (or RSP-150-12) | [Mean Well RS-150-12](https://www.meanwell-web.com/Article/DownloadAsset/RS-150-spec.pdf?documentId=assets/2057/357b4f0adf18408b90186c408d318d3e) [7] | $33 | |
| 3 | Series fuse | Littelfuse ATO 8 A | as §3a [9] | $3.50 | |
| 4 | NTC inrush | Ametherm SL22 20005 (or 5 A class equivalent) | [Ametherm SL22 20005](https://www.ametherm.com/datasheets/sl2220005/) [14] | $3 | |
| 5 | Wire | AWG 16, 1 m | — | $2 | |
| 6 | Connector to servo | Robotis 4-pin RS-485 cable (no canister at this stage; the bare servo is fine on the bench) | as §3a [13] | $8 | |
| 7 | RS-485 master | **DYNAMIXEL U2D2** | [Robotis U2D2](https://www.robotis.us/u2d2/) [15] | $36.92 | |
| 8 | (Optional) RS-485 HAT for embedded test | **Waveshare RS485 CAN HAT** (Raspberry Pi GPIO HAT, SP3485 transceiver, MCP2515 CAN controller — RS-485 is what we use) | [PiShop RS485 CAN HAT](https://www.pishop.us/product/rs485-can-hat-for-raspberry-pi/) [17] | **$15.45** [17] | For an MCU-driven test rig in lieu of a laptop + U2D2. **Brief said "$17"; verified $15.45 at PiShop, $13–18 across retailers** [17] |

**Bench chain summary cost:** **~$95** (PSU $33 + U2D2 $37 + fuse/inrush/wire $8 + connector $8 + WLP optional). With Pi + HAT instead of laptop + U2D2: ~$75 + Pi cost.

---

## 4. Per-interface bring-up table

The one-row-per-interface summary that ties §3 together. Use this as
the procurement checklist when wiring a new platform.

| # | Interface | Source bus | Series fuse | Wire (run length) | Bulkhead | Buck | Canister fuse | Servo connector | Bus master |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **BR2 chassis** | 4S Li-ion 14.8–16.8 V | ATO 8 A | AWG 16, ~1 m | WLP-VP 6.5 mm ($13) | D36V50F12 ($40) | Polyfuse 10 A | Robotis 4-pin | U2D2 / topside MCU |
| 2 | **ISO 9409-1 cobot (UR / Franka / etc.)** | Mean Well RS-150-12 (PARALLEL); UR Tool I/O for RS-485 only | ATO 8 A | AWG 16, ~3 m (sleeve along cobot arm) | WLP-VP or M8 4-pin | bypassed (already 12 V) | Polyfuse 10 A | Robotis 4-pin | UR `set_tool_communication` **or** U2D2 |
| 3 | **Reach Bravo 7** | RB-1006 elbow 12–24 V | ATO 5 A (input) + ATO 8 A (output) | AWG 16, ~0.5 m | SubConn MCBH6/8F ($185+) or WLP-VP ($13) | D36V50F12 ($40) | Polyfuse 10 A | Robotis 4-pin | RSCP-NDA via Bravo or U2D2 |
| 4 | **Schilling / Kraft work-class** | 24 V aux + optional ROV-side parallel | ATO 8 A | AWG 16, ~1 m | SubConn MCBH6/8F ($185–200) | D36V50F12 ($40) + 4700 µF bulk cap | Polyfuse 10 A | Robotis 4-pin | SeaNet RS-422/485 |
| 5 | **Bench / lab dry test** | Mean Well RS-150-12 | ATO 8 A | AWG 16, ~1 m | n/a (canister optional) | bypassed | Polyfuse 10 A | Robotis 4-pin | U2D2 |

**The buck is the same SKU (Pololu D36V50F12) across BR2, Bravo, and
Schilling — and bypassed on the bench / cobot 12 V supply.** The same
Robotis 4-pin connector terminates every chain at the XW540. The same
ATO 8 A fuse leads every chain. **Variation lives in the bulkhead
penetrator and the bus source.**

---

## 5. Tether ΔV budget — short cable inside the ROV / cobot side

`ELECTRICAL.md §3` owns the long subsea tether ΔV table (AWG 18 / 20
/ 22 × 10 / 20 / 30 m × XW540 / XM540 / STS3250 / STS3215, computed
to ≤ 6 A stall) [ELECTRICAL.md]. This section is the **short
upstream wire** (1–3 m of AWG 16 between the arm bus tap and the
canister bulkhead, **before** the long subsea tether comes in on the
ROV-to-topside leg). The AWG choice is **AWG 16, not AWG 18**, for
two reasons: (1) lower drop at peak current, (2) handles 6 A
continuous comfortably with no derating in still air at 20 °C.

### 5a. Wire resistance reference

| Wire | Cu DC R at 20 °C | Source |
|---|---|---|
| AWG 16 solid | **13.2 mΩ/m** | Misumi USA AWG resistance chart [10]; matches NEC Chapter 9 Table 8 / ASTM B258 [11] |
| AWG 16 stranded (Class B 19/29 strands) | ~13.9 mΩ/m (+5 %) | Belden master wire tables; matches Cirris calculator [10] [11] |
| AWG 18 solid | **21.0 mΩ/m** | [10] (cited in `ELECTRICAL.md §3a` as 21 mΩ/m) |
| AWG 14 solid | **8.3 mΩ/m** | [10] |

### 5b. AWG 16, 3 m round-trip, XW540 stall — voltage drop computation

Round-trip = 2L per Ohm's law (current goes out V+, returns GND).

`V_drop = I × 2L × R_per_m`

| Run length L (one way) | 2L | I (A) | V_drop at 5 A | V_drop at 6 A (peak stall) |
|---|---|---|---|---|
| 0.5 m (Bravo elbow → canister) | 1.0 m | 5–6 | **0.07 V** | 0.083 V |
| 1.0 m (BR2 battery → canister) | 2.0 m | 5–6 | **0.14 V** | 0.167 V |
| 1.5 m (Schilling aux → canister) | 3.0 m | 5–6 | 0.21 V | **0.25 V** |
| 3.0 m (bench PSU → cobot wrist → canister) | 6.0 m | 5–6 | 0.42 V | **0.50 V** |
| 5.0 m (worst case: lab-to-test-rig) | 10.0 m | 5–6 | 0.69 V | **0.83 V** |

**At 6 A stall, AWG 16 over 3 m round-trip = 0.50 V** — about
**4.2 % of 12 V** at the buck input. Well below the 5 % rule of thumb
for DC supply lines [10]. For 5 m runs and beyond, AWG 16 starts
brushing 7 %; upgrade to AWG 14 (8.3 mΩ/m) or shorten the run.

### 5c. When to step up to AWG 14 + 24 V intermediate

If the chain stretches to ≥ 10 m (e.g. a topside Mean Well at the
operator's bench cable-tied along the cobot, ROV, or workboat 
deck-rail to a remote canister), AWG 16 at 12 V loses > 5 % at stall:

| Length | AWG | V_drop at 6 A | % of 12 V |
|---|---|---|---|
| 10 m round trip | AWG 16 | 1.67 V | 14 % — **fails** |
| 10 m round trip | AWG 14 | 1.05 V | 8.7 % — marginal |
| 10 m round trip | AWG 14 + 24 V intermediate + canister-side buck | 0.50 V at 3 A on the 24 V leg | 2.1 % — passes |

**Rule:** if cable run > 5 m and source is 12 V, **switch to a 24 V
intermediate bus** and step down at the canister with the same
D36V50F12. This is the same logic `ELECTRICAL.md §3b` applies to the
long subsea tether — and it's why every chain in §3 above already
includes a buck whenever the source bus exceeds 14 V.

> **Stranded-cable adder.** Stranded marine-grade tinned-copper hookup
> wire has roughly +5 % resistance over solid Cu at 20 °C [10] [11].
> The numbers above are solid-Cu — the stranded reality adds ~0.02
> V to a 3 m run at 6 A. Negligible against the 5 % rule of thumb.

### 5d. BR2 mid-discharge dropout scenario — the worst-case rail

The D36V50F12's 13.3 V minimum input [8] interacts with the BR2 4S
Li-ion's SoC curve in a specific way that's worth working through
because it's the **single point where the BR2 chain can lose
regulation**:

| BR2 SoC | Open-circuit V_bat | Under-load V_bat (4 A draw, ~50 mΩ pack R) | V_drop on 1 m AWG 16 round trip @ 4 A | V at buck input | Buck status |
|---|---|---|---|---|---|
| 100 % | 16.8 V | 16.6 V | 0.11 V | 16.5 V | regulating (3.2 V headroom) |
| 80 % | 15.6 V | 15.4 V | 0.11 V | 15.3 V | regulating (2.0 V headroom) |
| 50 % | 14.5 V | 14.3 V | 0.11 V | 14.2 V | regulating (0.9 V headroom) — **watch** |
| 25 % | 13.5 V | 13.3 V | 0.11 V | 13.2 V | **at dropout — 12 V output not guaranteed** |
| 10 % | 12.6 V | 12.4 V | 0.11 V | 12.3 V | **below dropout — output sags ~1 V** |
| Cutoff (3.0 V/cell) | 12.0 V | 11.8 V | 0.11 V | 11.7 V | output ~ V_in − 0.5 V switch loss = ~11.2 V — **still in XW540 11.1–14.8 V range, marginally** |

At low SoC the buck transitions from regulator to **near pass-through**
(the buck's PMOS goes 100 % duty and the output simply tracks the
input less switch losses [8]). The XW540 still operates because its
**10–14.8 V range** [1] is wider than the BR2 below-dropout band
(11.7–13.2 V) — but the rail is **no longer regulated** and the
servo's `present_voltage` will fluctuate with thruster transients.

**Operational rule for BR2:** treat the buck as the **overvoltage
clamp** (its job is mainly to cap 16.8 V → 12 V at full charge), and
plan grasp duty cycles such that the **highest-current operations
happen earlier in the dive when the battery is above 25 % SoC**.
Below 25 % SoC, command position-only mode with a conservative
current setpoint; force-feedback fidelity degrades when the buck
loses regulation. **Same gear protection** (firmware `current_limit`)
applies — it is set by raw mA count, not by the rail voltage [ELECTRICAL.md §6].

---

## 6. Pre-power-up checklist — pre-dive electrical checks

Before applying current to a newly-wired chain (BR2, cobot, Bravo,
Schilling, or bench), the following checks **all pass** or the bring-up
is aborted. Run with the **canister sealed** and the **buck output
verified** against a meter, **before** the servo is connected.

### 6a. Bench / pre-installation checks (servo NOT yet connected)

- [ ] **Continuity, V+ to GND, source bus open-circuit:** > 1 MΩ (i.e. no dead short). Run before connecting the bus.
- [ ] **Continuity, RS-485 D+ to D-:** open-circuit > 100 kΩ in steady state (the 120 Ω termination resistors at each end of the bus appear in parallel, ~60 Ω with both fitted; if reading < 50 Ω, suspect a short).
- [ ] **Buck output verified at no-load:** 12.0 V ± 0.5 V on the buck's `V_OUT` pin. Use a meter; do not rely on the buck's LED indicator alone.
- [ ] **Buck output under dummy load:** load the buck output with a 6 Ω power resistor (gives 2 A — half-way to stall, half the heat) for 30 s. Output should hold 11.8–12.2 V; output ripple < 100 mV pk-pk on a scope.
- [ ] **Insulation test (canister and tether):** with a 500 V megger between V+ and the canister shell (and between V+ and seawater-side connector shells), insulation resistance > 100 MΩ. This catches a pinched wire, partial wet ingress, or a connector flooded at a previous dive.
- [ ] **Fuse condition:** ATO fuse intact (visible filament for the upstream blade; for the canister-side polyfuse, ohms < 1 Ω at room temperature).
- [ ] **Connector seating:** each penetrator nut torqued to vendor spec (WLP: 1.5 N·m to start, see [12]); SubConn rotated through the bayonet and lubed with Molykote 44 [16]; Robotis 4-pin servo cable clicked home with both clip ears latched.

### 6b. Servo-connected checks (servo wired, bus not yet enabled)

- [ ] **Servo present in bus scan:** `dynamixel_sdk.PacketHandler.ping(servo_id)` returns within 100 ms with no error. If a 2-axis gripper, both IDs respond.
- [ ] **ID conflict scan:** no two servos on the bus share an ID (factory default for XW540 is ID 1 — a second servo MUST be reassigned per `ELECTRICAL.md §1`).
- [ ] **No-load current at idle:** `present_current` reads < 50 mA (≈ 20 raw LSBs at 2.69 mA/LSB) with `torque_enable = 1` and no command. Anything higher suggests a bus short or an internal fault.
- [ ] **`current_limit` register written:** read back `current_limit` (reg 38) and `goal_current` (reg 102) and confirm they match the per-servo profile in `ELECTRICAL.md §6b`. **If either reverts to factory default (1193 raw on XW540 = 3.2 A), abort — gear protection is not in place.**
- [ ] **Bus voltage from servo telemetry:** `present_voltage` (reg 144) reads the actual rail at the servo. Should be 11.8–12.2 V at the buck's `V_OUT`. Any deviation > 0.5 V suggests a wiring drop or a buck issue.
- [ ] **Bus temperature from servo telemetry:** `present_temperature` (reg 146) reads ambient (typically 20–25 °C). Anything > 40 °C at idle means heat from upstream — investigate.
- [ ] **Baseline `I_0` recorded:** servo no-load current logged for the session (`SENSING.md §3`). Used as the calibration tare; flag > 5 mA drift session-to-session per `FAILURE_MODES.md S2`.

### 6c. Wet / dive specific

- [ ] Pre-dive seal check (per `ROV_INTEGRATION.md §3` and `docs/UNDERWATER.md §6`).
- [ ] WetLink penetrator nuts re-torqued to vendor final spec (typ. 5 N·m for WLP-VP M10) after one warm-cool cycle.
- [ ] Canister vent / leak-port (if any) dry; no moisture.
- [ ] Buck output measured one last time after canister is sealed and bus connected — the *final* number must match the open-canister number ± 0.1 V.

---

## 7. Failure modes — the power-chain-specific additions

`FAILURE_MODES.md` owns the actuator + drivetrain + sensing failure
modes (M1–M6, S1–S5). The chain in §3 above adds **four new
power-chain-specific failure surfaces** that are **not** in the
existing M-code list. They are introduced here with the **P-code
family** (`P1`–`P4`); each cross-refs the closest existing M-code.

### P1 — Buck fails OPEN (regulator dead, no output)

| Field | Detail |
|---|---|
| **Cause** | Buck IC dies (thermal runaway, over-input transient, ESD); input capacitor opens; output capacitor opens; inductor open. **No 12 V at the servo input. Cross-refs `FAILURE_MODES.md M3` brown-out.** |
| **Detection** | Servo `present_voltage` reads 0 V (servo reboots and never replies); RS-485 comms timeout from the servo within ~50 ms of the buck dying; topside `COMM_RX_TIMEOUT` alarm fires |
| **Mitigation** | Pick the same buck for every chain (D36V50F12) so a single spare covers all interfaces. Carry one spare in the dive box. Run with a buck-output voltage telemetry channel (a topside ADC reading the canister-internal 12 V rail through the same RS-485 over a spare pair, or — simpler — rely on the XW540's `present_voltage` register) |
| **Graceful degradation** | Servo loses power, gripper opens (back-drivable per `FAILURE_MODES.md M3`). **Identical safety outcome to a brown-out.** Held object is dropped; no mechanical damage |

### P2 — Buck fails SHORT (input shorts to output — CRITICAL)

| Field | Detail |
|---|---|
| **Cause** | Buck's high-side MOSFET fails closed (shorts V_IN to V_OUT, bypassing the regulator). At a 24–48 V input bus, this dumps **24 V or 48 V** onto the servo's 14.8 V max input. **Servo input MOSFETs can fail short within milliseconds**, then cascade into the servo's stator. Cross-refs nothing in `FAILURE_MODES.md` — this is the new mode and the highest-severity power-chain failure |
| **Detection** | Servo `present_voltage` reads > 14.8 V (the firmware's voltage error register will set the over-voltage bit on the XW540 [1]); if the servo dies first, comms go silent and the bus is at the unregulated source voltage |
| **Mitigation** | (a) **Canister-side polyfuse rated below the unregulated bus's source current** — at Bravo 24 V × the buck's ~3 A draw, fuse blows in < 1 s when the upstream is shorted to the downstream and starts pulling the bus's stall-equivalent through the chain. (b) **TVS diode** (e.g. SMBJ16A, 16 V working / 26 V clamp) across the buck output, V+ to GND — clamps to 26 V max and crowbars to the polyfuse. **Add the TVS as a mandatory BOM line for chains where source > 14.8 V (i.e. BR2 full charge, Bravo, Schilling) — but NOT bench (12 V source can't drive overvoltage)**. (c) Continuous `present_voltage` monitoring with a topside trip threshold at 14.5 V. |
| **Graceful degradation** | TVS clamps; polyfuse trips; servo may survive a sub-millisecond transient if the TVS catches it. **Without these protections, the servo is destroyed silently.** This is the most expensive single failure in the chain |

### P3 — Fuse pops (upstream or canister-side)

| Field | Detail |
|---|---|
| **Cause** | Wire-short during installation; servo internal fault that draws stall continuously; inrush at power-on exceeds the slow-blow rating (rare with fast-blow ATO + bulk cap); buck inrush at the canister side |
| **Detection** | Power loss to the servo; identical telemetry pattern to P1. Pre-installation: visible blown filament on ATO blade; polyfuse reads > 100 Ω cold |
| **Mitigation** | Carry 5 spare ATO 8 A blades + 5 spare polyfuse modules in the dive box. **Fuse hierarchy** (per chain): upstream ATO 8 A at the bus, canister-side polyfuse 10 A — when both pop, the chain is genuinely broken (suspect a hard short, not nuisance trip). Inrush limiter (Ametherm SL22 series) lives between the source and the ATO fuse [14] |
| **Graceful degradation** | Power loss → gripper opens (back-drivable). **Recovery in the field:** swap the ATO blade. If the polyfuse pops, it cools and auto-resets in ~30 s (sealed canister cools slowly — wait); if it doesn't reset, abort dive. Cross-refs `FAILURE_MODES.md M3` |

### P4 — Water in the bulkhead connector (WLP or SubConn)

| Field | Detail |
|---|---|
| **Cause** | WLP compression gland torqued to less than vendor spec; SubConn not greased with Molykote 44 [16]; cable jacket cracked at the gland; canister hydrostatic test skipped |
| **Detection** | Rising `present_current` at no-load (electrolysis between V+ and the seawater-grounded shell); topside ground-fault detector trips; RS-485 packet errors / CRC failures; servo `present_voltage` drops as the seawater path becomes a resistive shunt. **Same detection pattern as `FAILURE_MODES.md M5`** (connector flood) |
| **Mitigation** | (a) **Pre-dive insulation test** (§6a, 500 V megger > 100 MΩ); (b) **Molykote 44 on every SubConn mate** [16]; (c) WLP torque to vendor final spec after warm-cool cycle (§6c). (d) Single-point ground at battery negative (`ELECTRICAL.md §5`) so a shorted shell trips the upstream fuse rather than electrolysing the gripper |
| **Graceful degradation** | Fuse blows → P3 → power loss → gripper opens. **Same safety outcome as P1** — the held object is dropped. The connector is the spareable piece; replace it dockside |

### P-code detection procedures (what to actually do in the lab)

**P1 (buck fails open) — confirm before swapping the buck:**

1. Power down. Disconnect the buck from the canister. Probe the buck output (V_OUT to GND) with a meter on DC volts.
2. Re-apply input power with the buck disconnected from the servo. **No-load output should be 12.0 ± 0.5 V.** If 0 V or near input voltage, the buck IC is dead — replace.
3. If buck output is correct at no-load, reconnect the servo and probe again. If output now collapses to < 11 V, the servo is drawing more than the buck can supply (suggests a downstream short, polyfuse OK but a wire crushed, or the servo is faulted).
4. Scope the buck output for switching artefacts: a working LMR16030-class part shows ~500 kHz–1 MHz ripple at ~30–50 mV pk-pk; an oscillation at < 10 kHz or > 100 mV pk-pk indicates loop instability (likely input cap dead).

**P2 (buck fails short) — pre-installation gate so the field never sees this:**

1. Bench-test every buck before installation in a canister. Apply nominal input (e.g. 24 V for Bravo, 16.8 V for BR2-full-charge); confirm output = 12.0 V ± 0.4 V at no-load and at 3 A load (use a 4 Ω 50 W resistor).
2. **Apply 26 V (the TVS clamp voltage)** briefly (1 s, ≤ 100 mA limit-set) to the buck input and verify the output does **not** rise above 12.5 V; the buck's internal overvoltage protection [8] should engage. Note: do not exceed 50 V absolute max input on the D36V50F12 — beyond that the part is unrecoverable [8].
3. If the buck shows any output above 14 V at any input < 50 V — **reject the buck**, do not deploy.
4. **In service**, monitor `present_voltage` continuously (every telemetry poll, ≥ 50 Hz). Topside trip threshold at 14.5 V → fire fault, cut bus power upstream via the ROV's ground-fault breaker or the upstream ATO fuse. **Reaction time critical: a faulted buck can destroy the XW540 in < 100 ms.**

**P3 (fuse pops) — diagnostic flow:**

1. Power down, remove the blown fuse, **inspect the filament** (ATO blade with clear plastic body — visible blown section). Polyfuse: measure resistance cold (room temperature ~ 1 hour after trip). If polyfuse reads > 100 Ω cold, it's degraded — replace; a healthy reset polyfuse reads < 1 Ω.
2. **Find the root cause** before replacing the fuse — never just swap a blown fuse and re-power. Common causes:
   - Wire short (pinched at bulkhead, frayed insulation): megger test V+ to GND with bus disconnected. < 100 MΩ → wiring fault.
   - Servo over-stall: `present_current` history at last command. If pinned at `current_limit` for > 1 s, the firmware ceiling was set too high or operator commanded sustained stall.
   - Inrush: only on first power-on. Verify SL22 NTC limiter is installed and not bypassed.
3. **Replace the fuse**, restore the ATO holder cap, and re-run the §6 pre-power checklist before re-energizing the bus.

**P4 (connector flood) — leak-locate after a wet event:**

1. Dockside, with canister removed from arm: dry the exterior, inspect penetrators visually for grease (Molykote 44) coverage and seal compression.
2. Megger test V+ to seawater (a wet cloth grounded to the canister shell): > 100 MΩ pass.
3. If insulation fails, sequentially disconnect penetrators and re-test until the leak is isolated. Replace the failed penetrator (WLP or SubConn — entire connector body, not just the seal).
4. If the canister itself shows water inside (drain through the dry-side cap): **abort and dismantle.** Dry electronics with desiccant for 48 h; bench-test all components; replace any showing corrosion. The XW540 IP68 body is robust [1] but its servo connector is not pressure-rated.

### Summary — power-chain P-codes vs existing M-codes

| Code | New? | Severity | Likelihood | Cross-ref |
|---|---|---|---|---|
| **P1** Buck fails open | NEW | 3 (drops object, no damage) | L–M | M3 |
| **P2** Buck fails short | **NEW** | **5 (servo destroyed)** | L | (none — this section is the addition) |
| **P3** Fuse pops | NEW | 3 (drops object) | L | M3 |
| **P4** Connector flood | partial overlap | 4–5 | M | M5 |

The single new high-severity item is **P2 (buck fails short)** — and
its mitigation is a single TVS diode (~$0.30) on every chain where
the source bus exceeds 14.8 V. **Cheap, mandatory, and not currently
in the BOM.**

---

## 8. BOM delta proposal

Proposed lines to **add** to `docs/BOM.md`. Format mirrors the existing
"§4 User-supplied items" table. **Do not merge silently** — these are
proposed for review; the existing BOM lists power as
"connect 12 V to the servo" without itemising the chain.

Cost summary for the simplest (BR2) chain, excluding the XW540 itself
(already in BOM) and the canister assembly (already in BOM):

| Line | Part | Qty | Vendor | Cost (USD) | Source |
|---|---|---|---|---|---|
| **POW-1** | **Pololu D36V50F12** 12 V buck (13.3–50 V in, 6.5 A out) | 1 per chain | Pololu | **$39.95** | [Pololu #4095](https://www.pololu.com/product/4095) [8] |
| **POW-2** | **Littelfuse ATO 8 A fast-blow blade fuse** + inline holder | 1 fuse + 1 holder, 5 spares | Littelfuse / generic auto-parts retailer | **$0.50 fuse + $3 holder + $2.50 (5 spares)** = **$6** | [Littelfuse ATOF datasheet](https://m.littelfuse.com/~/media/automotive/datasheets/fuses/passenger-car-and-commercial-vehicle/blade-fuses/littelfuse_atof_datasheet.pdf) [9] |
| **POW-3** | **Polyfuse 10 A radial-leaded PPTC** (canister-internal backstop) | 1 + 1 spare | Bel Fuse 0ZRC0750FF1E or Littelfuse RXEF750 | **$1 + $1 spare** = **$2** | Mouser / Digi-Key |
| **POW-4** | **AWG 16 stranded marine-grade tinned-Cu hookup wire, twisted pair**, ~3 m | 1 reel (covers all chains) | Belden 9501 or generic marine-grade | **$3–5** | [Belden master tables](https://www.belden.com) [10] [11] |
| **POW-5** | **Robotis 4-pin Robot Cable** (X4P 180 mm, 10-pack) | 1 pack | Robotis | **$8** | [Robotis X4P 180 mm 10-pcs](https://robotis.us/robot-cable-x4p-180mm-convertible-10pcs/) [13] |
| **POW-6** | **DYNAMIXEL U2D2** (USB-RS485 bus master) | 1 | Robotis | **$36.92** | [Robotis U2D2](https://www.robotis.us/u2d2/) [15] |
| **POW-7** | **Bench PSU — Mean Well RS-150-12** (12 V / 12.5 A enclosed) — only required for cobot / bench chain | 1 (bench-only) | TRC Electronics / Digi-Key | **$33** | [Mean Well RS-150 datasheet](https://www.meanwell-web.com/Article/DownloadAsset/RS-150-spec.pdf?documentId=assets/2057/357b4f0adf18408b90186c408d318d3e) [7] |
| **POW-8** | **Ametherm SL22 20005** NTC inrush limiter (5 A class) | 1 | Ametherm / Mouser | **$3** | [Ametherm SL22 20005 datasheet](https://www.ametherm.com/datasheets/sl2220005/) [14] |
| **POW-9** | **TVS diode SMBJ16A** (16 V working, 26 V clamp, 600 W) on buck output for chains with source > 14.8 V (BR2 / Bravo / Schilling) — **MANDATORY GEAR PROTECTION per §7 P2** | 1 + 1 spare | Littelfuse / Bourns / Vishay | **$0.30 + $0.30 spare** | [Littelfuse SMBJ series datasheet](https://www.littelfuse.com) |
| **POW-10** | **Bulk capacitor — Nichicon UCC 4700 µF / 35 V** electrolytic (Schilling chain only) | 1 (Schilling-only) | Nichicon / Mouser | **$3** | Mouser |
| **POW-11** | **Waveshare RS485 CAN HAT** (Raspberry Pi GPIO HAT; alternative to U2D2 for embedded test rigs) | 1 (optional) | PiShop / Waveshare | **$15.45** | [PiShop RS485 CAN HAT](https://www.pishop.us/product/rs485-can-hat-for-raspberry-pi/) [17] |

### Lines to **modify** in `docs/BOM.md` §4

| Line | Existing | Proposed change |
|---|---|---|
| §4 "Waterproof actuator" row | Lists XW540 / XM540 / STS3250 / STS3215 with prices; no power chain | **No change** — but cross-ref **the new POW-1 … POW-9 lines** in §4 as "see POWER_SUPPLY.md §8 for the upstream power chain (regulator + fuses + connector)" |
| §4 "Pressure canister assembly" row | Lists tube + caps + WetLink penetrator (2× WLP at $13 ea) | **Optional add:** for the BR2 / Bravo / Schilling chains, note that the WLP carries the **4-conductor** cable into the canister — no change to the penetrator count, just clarify the conductor count |
| §4 "M4 bolts" row | n/a | **No change** |
| (new) §4 "Power supply chain" row | n/a | **NEW row:** "POW-1 to POW-11 — per-interface power chain (regulator + fuse + connector + RS-485 master); see [`POWER_SUPPLY.md §8`](../motor/POWER_SUPPLY.md). Estimated incremental cost: BR2 ~$50–65 (range driven by WLP-already-in-canister-BOM accounting), cobot ~$100, Bravo ~$365–565, Schilling ~$245." |

### Lines to **REMOVE / mark non-existent**

| Item | Status | Action |
|---|---|---|
| **Pololu D24V90F12** (mentioned in brief as primary buck) | **Does not exist** — Pololu catalogue has no D24V90F12 (verified by direct search of [Pololu category 131](https://www.pololu.com/category/131/step-down-buck-voltage-regulators) and [D24V10Fx category](https://www.pololu.com/category/248/d24v10fx-step-down-voltage-regulators)). The D24V90Fx family exists in **5 V variants only** (D24V90F5 at SKU #2866) [8] | Replaced by **Pololu D36V50F12 (#4095)** in POW-1 above. **Do not add D24V90F12 to BOM** |
| **DYNAMIXEL U2D3** (mentioned in brief) | **Does not exist** — current Robotis bus master is **U2D2** (recently upgraded to USB-C [15]); no U2D3 is in the Robotis catalogue | Replaced by **U2D2** in POW-6 above. **Do not add U2D3 to BOM** |
| **Mean Well RD-50A** (mentioned in brief as bench-PSU alternative) | **Exists but is the wrong product for our load** — RD-50A is a 50 W **dual-output 5 V + 12 V module** rated ~3 A on the 12 V channel. **Below our 5 A stall requirement.** | Replaced by **Mean Well RS-150-12** (single-output 12 V / 12.5 A, $33) in POW-7. Optional fallback: **Mean Well RSP-150-12** (semi-enclosed, 12.5 A, ~$45) |

### Total BOM-delta cost summary

| Chain | Incremental cost (USD) |
|---|---|
| **BR2 chassis (simplest)** | **~$50–65** — see §3a for the per-line breakdown (full sum $63.05; net delta against `docs/BOM.md` is ~$49 once the WLP-already-in-canister-BOM and Robotis-cable-ships-with-servo credits are taken; ~$63 if those credits are *not* taken). Sans bench-only U2D2 (assumed reused) and sans the XW540 itself (already in BOM at $1241.89) |
| Cobot bench | ~$95 = above + $33 bench PSU + $36.92 U2D2 |
| Reach Bravo 7 | ~$365–565 (WLP path) / ~$535–735 (SubConn path); driven by Reach RB-1006 accessory cost |
| Schilling / Kraft work-class | ~$245 (SubConn path) |
| Bench-only dry test | ~$95 |

---

## 9. Sources

[1] **ROBOTIS DYNAMIXEL XW540-T260-R product description and e-manual.** Voltage 10.0–14.8 V (recommended 12.0 V); stall current 4.5 A @ 11.1 V, 4.9 A @ 12 V, 5.9 A @ 14.8 V; weight 185 g. <https://emanual.robotis.com/docs/en/dxl/x/xw540-t260/> ; product description PDF: <https://www.mouser.com/pdfDocs/XW540-T260-R_ProductDescription.pdf> ; ROBOTIS store: <https://robotis.us/dynamixel-xw540-t260-r/>

[2] **Blue Robotics Lithium-ion Battery for the BlueROV2 (14.8 V, 18 Ah).** Part `BR-100789`. 4S Li-ion configuration; nominal 14.8 V, full-charge 16.8 V (4×4.20 V); minimum safe cutoff 12 V (3.0 V/cell). <https://bluerobotics.com/store/comm-control-power/powersupplies-batteries/battery-li-4s-18ah-r3/> ; battery handling: <https://bluerobotics.com/learn/battery-info/>

[3] **BlueROV2 main power distribution.** 4S Li-ion to the main electronics tube via WetLink penetrator; per-channel budget 5–10 A; see also `motor/interfaces/fixed-rov-chassis.md` for the Newton-footprint cable run patterns. <https://bluerobotics.com/learn/newton-subsea-gripper-installation/>

[4] **Universal Robots — Tool Connector for Electrical Interfaces.** UR e-Series M8 8-pin Tool I/O; 0/12/24 V software-selectable; 600 mA continuous, ≥ 2 A peak ≤ 1 ms; RS-485 over pins 1/2 via `set_tool_communication()`. <https://www.universal-robots.com/developer/hardware-and-motion/electrical-interfaces-tool-connector/>

[5] **Reach Robotics Bravo 7 Integration Manual** (partial public excerpts + NDA RSCP protocol). Bus envelope 20–48 V DC; base 4-pin power MCBH4M + 8-pin comms MCBH8ME; **elbow Accessory Port RB-1006**: 12–24 V DC + RS-485 or Ethernet via MCBH8F. Per-pin breakdown is NDA — request from Reach Sales. Public datasheet: <https://reachrobotics.com/products/manipulators/bravo-7/> ; per-feature dossier: `motor/interfaces/reach-bravo-alpha.md`.

[6] **Schilling Robotics — TITAN 4 Manipulator System Technical Manual.** Doc 011-8239 rev B (2012). 24 V DC slave-arm aux bus ~1.875 A; RS-232 or RS-422/485 on SeaNet pair. <https://www.dndkm.org/DOEKMDocuments/GetMedia/Technology/2177-8239_Titan4_cover_toc_specs.pdf>

[7] **Mean Well RS-150-12.** Enclosed power supply, 150 W, 12 V, 12.5 A, 85–264 VAC input, 83 % efficiency, 3-year warranty. Mean Well datasheet PDF: <https://www.meanwell-web.com/Article/DownloadAsset/RS-150-spec.pdf?documentId=assets/2057/357b4f0adf18408b90186c408d318d3e> ; TRC Electronics product page: <https://www.trcelectronics.com/products/mean-well-rs-150-12> ; Jameco: <https://www.jameco.com/z/RS-150-12-MEAN-WELL-RS-150-12-Enclosed-Power-Supply-12VDC-12500mA_323839.html>

[8] **Pololu D36V50F12 — 12 V, 2.3–6.5 A step-down voltage regulator.** SKU #4095. Input 13.3–50 V; output 12 V ± 4 %; typical max continuous output 2.3–6.5 A (input-voltage dependent); efficiency 90–95 %; price USD 39.95 (single); 1″×1″×0.375″; reverse-voltage protection (up to 40 V), over-current and short-circuit protection, over-temperature shutoff, soft-start. <https://www.pololu.com/product/4095> ; category page: <https://www.pololu.com/category/131/step-down-buck-voltage-regulators> ; **Note on D24V90F12** (mentioned in brief): does not exist — only D24V90F**5** (5 V variant, #2866) exists in the D24V90Fx family. The 12 V high-input-V high-current Pololu modules are D36V50F12 and D36V28F12 (2.4 A): <https://www.pololu.com/product/3786>

[9] **Littelfuse ATOF / ATO blade fuse series.** 32 V DC, fast-acting, ISO 8820-3 / SAE J1284 compliant, -40 to +105 °C. Standard amp ratings 1–40 A. Datasheet PDF: <https://m.littelfuse.com/~/media/automotive/datasheets/fuses/passenger-car-and-commercial-vehicle/blade-fuses/littelfuse_atof_datasheet.pdf> ; product page: <https://www.littelfuse.com/products/fuses-overcurrent-protection/fuses/automotive-aftermarket-products-fuses/blade-fuses-shunts-automotive-aftermarket/ato>

[10] **Copper wire resistance vs AWG chart.** AWG 16 solid Cu: 13.2 mΩ/m at 20 °C; AWG 14 solid: 8.3 mΩ/m; AWG 18 solid: 21.0 mΩ/m. Misumi USA wire resistance chart: <https://us.misumi-ec.com/blog/copper-wire-resistance-awg-chart/> ; HyperPhysics electrical wire gauges: <http://hyperphysics.phy-astr.gsu.edu/hbase/Tables/wirega.html> ; Cirris resistance calculator: <https://cirris.com/wire-resistance-calculator/>

[11] **NEC Chapter 9 Table 8 / ASTM B258 / Belden master wire tables.** Standard reference for stranded vs solid copper resistance. Belden hookup wire 9501 series tinned copper: <https://www.belden.com/> (master tables published on Belden product family pages). Stranded Class B 19/29 strands: +5 % over solid resistance at 20 °C.

[12] **Blue Robotics WetLink Penetrator (WLP-VP).** M10 / M14 / M06 bulkhead body, 1000 m depth rating; FKM seal (-25 to +200 °C); Aluminum 7075-T6 type III anodized. Cable jacket diameter 4.0–9.5 mm via interchangeable seals (M10 supports 6.5 mm with `BR-100870-165`). Price USD 13–17 per unit. <https://bluerobotics.com/store/cables-connectors/penetrators/wlp-vp/> ; JPT variant (no jacket strip): <https://bluerobotics.com/store/cables-connectors/penetrators/wetlink-penetrator/> ; M10 blank for unused holes (`BR-100434-010`): <https://bluerobotics.com/store/cables-connectors/wlp-blank/>

[13] **ROBOTIS Robot Cable — X4P 180 mm (10 pcs, convertible).** 4-pin RS-485 JST connector cable for X-series DYNAMIXELs (including XW540). Daisy-chain capable. <https://robotis.us/robot-cable-x4p-180mm-convertible-10pcs/> ; cable selection guide: <https://robotis.us/tech-tips-picking-the-right-cables-for-your-dynamixel> ; DXL Communication Bridge / pinout: <https://emanual.robotis.com/docs/en/parts/interface/dxl_bridge/>

[14] **Ametherm SL22 series inrush current limiters.** 5 A class radial thermistors; SL22 series datasheets at <https://www.ametherm.com/inrush-current/inrush-current-data-sheets/>. Specific datasheets: SL22 10005 (10 Ω / 5 A) <https://www.ametherm.com/datasheets/sl2210005/>; SL22 20005 (20 Ω / 5 A) <https://www.ametherm.com/datasheets/sl2220005/>; SL22 25005 (25 Ω / 5 A) <https://www.ametherm.com/datasheets/sl2225005.html>.

[15] **ROBOTIS U2D2** USB-RS485/TTL converter for DYNAMIXEL. Price USD 36.92 (2026). USB-C upgrade; supports both RS-485 (4-pin JST) and TTL (3-pin JST). Does not supply power — external PSU required for servos. <https://www.robotis.us/u2d2/> ; e-manual: <https://emanual.robotis.com/docs/en/parts/interface/u2d2/>. **No U2D3 product exists** as of 2026-05.

[16] **MacArtney SubConn Micro Circular Connectors.** 5/6/8/9-contact circular series, 300 V DC/AC rms, 5 A per contact (20 A per connector max), > 500 mating cycles, depth-rated 300 bar (3000 m) PEEK; chloroprene rubber body; gold-plated BeCu contacts. Bulkhead variants: brass, stainless steel, titanium, anodised aluminium, or PEEK. Molykote 44 grease required at every mate. <https://www.macartney.com/connectivity/subconn/subconn-micro-circular-series/> ; 5/6/8/9-contact variant: <https://www.macartney.com/connectivity/subconn/subconn-micro-circular-series/subconn-micro-circular-5-6-8-and-9-contacts-and-g2-2-3-and-4-contacts/> ; MCBH6F retail (UK): £145.36 at Survey Spares: <https://surveyspares.com/products/mcbh6f-subconn-connector-1>

[17] **Waveshare RS485 CAN HAT for Raspberry Pi.** SP3485 RS-485 transceiver + MCP2515 CAN controller; 40-pin GPIO header; 3.3 V logic; onboard TVS suppression. Price USD 15.45 at PiShop. <https://www.waveshare.com/rs485-can-hat.htm> ; wiki: <https://www.waveshare.com/wiki/RS485_CAN_HAT> ; PiShop: <https://www.pishop.us/product/rs485-can-hat-for-raspberry-pi/>

[18] **`motor/ELECTRICAL.md`** (sibling doc in this repository). Tether ΔV tables for AWG 18/20/22 over 10/20/30 m; fusing baseline (1.5 × stall); RS-485 baud vs cable length; current-limit register profile per servo. The canonical reference for canister-internal wiring and telemetry; this document defers to it for everything past the canister bulkhead.

[19] **`motor/ROV_INTEGRATION.md`** (sibling doc). Mounting, cable routing, connector tiering by depth, buoyancy trim, and canister assembly (Blue Robotics 3″ locking series). Per-tier connector recommendations (WLP at T1/T2, SubConn at T3) match the choices in §3 above.

[20] **`motor/INTERFACES.md`** and **`motor/interfaces/*.md`** (sibling docs). Mounting-interface dossiers: BR2 chassis Newton-footprint (16° canted), ISO 9409-1 50-4-M6 + 80-6-M8, Reach Bravo 7 (RB-1054) + Alpha 5, Schilling/Kraft work-class. Bus pass-through availability per interface — the §2a table above is the boiled-down summary.

[21] **`motor/SELECTION.md`** and **`motor/SURVEY.md`** (sibling docs). Actuator selection process, scoring, and the four-step servo ladder (XW540 / XM540 / STS3250 / STS3215). Voltage and current numbers cited in §1 and §2a trace back here.

[22] **`motor/FAILURE_MODES.md`** (sibling doc). Existing M1–M6 + S1–S5 failure modes; this document adds **P1–P4** as the power-chain-specific addendum (§7 above).

[23] **`docs/BOM.md`** (sibling doc). The current bill of materials, which the §8 BOM delta proposes to extend.

---

## Cross-links

`ELECTRICAL.md` (canister-internal wiring, RS-485 telemetry, current-limit
firmware) · `ROV_INTEGRATION.md` (canister assembly, connector tiering,
buoyancy) · `INTERFACES.md` + `interfaces/*.md` (mounting dossiers per
interface) · `SELECTION.md` + `SURVEY.md` (actuator selection) ·
`FAILURE_MODES.md` (M1–M6 + S1–S5; this doc adds P1–P4) ·
`docs/BOM.md` (target of the §8 delta) · `docs/UNDERWATER.md` §5–§6
(galvanic isolation, connector sealing).

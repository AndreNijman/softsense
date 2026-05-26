# Mounting interfaces — comparison + modelling order

Synthesis of the four interface dossiers in `motor/interfaces/`. Each dossier
is the primary-source research; this file is the cross-cut: which to model
first, which open questions block which, and what the load + power + depth
matrix actually says.

| Dossier | File | Lines | Status |
|---|---|---|---|
| Reach Robotics Alpha 5 + Bravo 7 wrist | [`interfaces/reach-bravo-alpha.md`](interfaces/reach-bravo-alpha.md) | 774 | Bravo 7 ready; Alpha 5 blocked |
| ISO 9409-1 cobot/robot tool flange | [`interfaces/iso-9409-1.md`](interfaces/iso-9409-1.md) | 739 | Both 50-4-M6 + 80-6-M8 ready |
| Schilling/Kraft/ECA/Hydro-Lek work-class wrist | [`interfaces/schilling-kraft.md`](interfaces/schilling-kraft.md) | 482 | Bolt-on Option A blocked; ISO 13628-8 D-handle Option B ready |
| Fixed BlueROV2-chassis mount (no manipulator) | [`interfaces/fixed-rov-chassis.md`](interfaces/fixed-rov-chassis.md) | 678 | BR2 Newton-footprint ready (Roof Rack + Skid + Bottom Panel variants) |

> **Honesty rule** (carried from the campaign). All four dossiers cite every
> published number to a primary source. Where a vendor keeps a dimension
> behind NDA (Schilling/Kraft wrist flange geometry; Reach Alpha 5 jaw
> mating thread; BR2 side-panel hole grid), the gap is **flagged**, not
> filled in with inference disguised as fact.

---

## 1. The headline table

How each interface lands against the seven things a CAD-modelable adapter
actually needs.

| Interface | Bolt pattern public? | Alignment feature public? | Electrical pass-through public? | Mass/load ratio | Depth fit | Adapter material | Modelling readiness |
|---|---|---|---|---|---|---|---|
| **Reach Bravo 7 (RB-1054)** | ✅ Ø71 mm, 6×M6 + 6×M5 CSK | ✅ 2× Ø3 dowel | ⚠️ NDA-only RSCP comms; arm has RS-485/232/Ethernet to controller | gripper ≪ arm (0.3 kg vs 9.5 kg) — appropriate | T1/T2 (arm = 450 MSW) | PA12-GF printed | **READY — model now** |
| **Reach Alpha 5 (RA-1013)** | ❌ thread / collar OD unspecified | ❌ dowel pattern unpublished | ⚠️ 18–30 V DC, RS-485 | gripper ≈ 25 % of arm (0.3 kg vs 1.36 kg air) — appropriate | T1/T2 (arm = 300 MSW) | PA12-GF printed | **BLOCKED — needs RA-1013 drawing or reverse-measurement** |
| **ISO 9409-1-50-4-M6** | ✅ standard, every dimension | ✅ Ø6 H7 dowel at +Xm | ⚠️ per vendor (UR M8 600 mA, Franka FCI, Kinova PoE, ABB DSQC); none carries 6 A stall | gripper ≪ all cobots (1.8 N·m flange-side ÷ 9 N·m UR3e wrist = 5× headroom) | **DRY ONLY** — bench testing on lab cobots | PA12-GF printed (+ PTFE shim) or Al-6082 | **READY — model now** |
| **ISO 9409-1-80-6-M8** | ✅ standard, every dimension | ✅ Ø8 H7 dowel | as above | ditto, 2.4× polar inertia of 50 | DRY ONLY | PA12-GF or Al-6082 | READY — model second variant after 50 |
| **Schilling family (TITAN/Orion/Atlas/Conan) bolt-on (Option A)** | ❌ bolt count = 6 (third-party catalogues); BC/size/OD all NDA | ❌ key/dowel not published | ❌ wrist is hydraulic + SeaNet — electrical pass-through is a per-install stab plate | **gripper = 0.3 % of TITAN 4 lift** — interface demo only | T3+ (arms 4 000–7 000 m) but irrelevant — wrong scale | Ti/SS adapter or printed PA12-GF demo | **BLOCKED + WRONG SCALE — only as interface demo** |
| **Schilling/Kraft via ISO 13628-8 D-handle (Option B)** | ✅ Ø70 mm flange, Ø56 PCD, 4 or 8 × M6, Ø19 mm bar | ✅ standardised | n/a — held tool, no electrical at wrist | mass-appropriate (handle adds ~50 g to gripper) | T1–T3 (handle is the existing standard the arm clamps anyway) | PA12-GF printed | **READY — and the actually-pragmatic Schilling answer** |
| **Kraft Predator 4-bolt square (Option A)** | ❌ bolt size/OD all NDA | ❌ not published | ❌ same as Schilling | same scale mismatch | T3 (3 000–6 500 m) | Ti/SS or printed demo | BLOCKED + WRONG SCALE |
| **BR2 Bottom Panel (Newton-mount footprint)** | ✅ 2× Ø5.5 mm, 100 mm pitch, **16° tilt**, 16/31 mm edge offsets | ✅ 16° tilt is itself the alignment | ✅ WetLink penetrator into main electronics tube (BR-canonical) | mass-appropriate (gripper consumes ~950 g of BR2's ~1.2 kg ballast budget) | T1/T2 (BR2 = 100 m rated, 130 m tested) | PA12-GF printed | **READY — model now** |
| **BR2 Roof Rack (BR-200126)** | ⚠️ has 2-hole Newton positions but per-feature coords unpublished | ⚠️ 0° or 10° tilt via bolt-hole pair selection | as above | ditto | T1/T2 | PA12-GF printed | NEAR-READY — needs a Roof Rack to photogrammetry, OR reuse the 2-hole Newton footprint that's printed on the rack |
| **BR2 Payload Skid (BR-100233)** | ✅ accommodates 3" canister natively + 2× M5 Newton footprint | ✅ skid-frame alignment | as above | larger payload budget (12× 200 g = 2.4 kg ballast) | T1/T2 | PA12-GF printed | READY — model as the "full kit" variant |

---

## 2. Recommended modelling order

Three are ready *now* and span the realistic deployment matrix from one
end to the other (lab → ROV → conservation field):

### 2.1 Model first (P0 — three adapters, all ready, all useful, all printable in PA12-GF)

1. **`adapter_bravo7.step`** — Reach Bravo 7 RB-1054 → our M4 flange.
   - Top face: Ø71 mm circular plate, 6×M6 + 6×M5 CSK, 2×Ø3 dowel.
   - Bottom face: our 4×M4 flange pattern (TBD bolt-circle from `gripper.py`).
   - Material: PA12-GF, estimate 70–100 g; total ≤120 g including A4-316 M5
     bolts + nylon bushings.
   - Cable: RS-485 stub via Reach connector pass-through on the wrist.
   - **Why first:** fully spec'd; market is the largest installed base of
     small-ROV manipulators (Bravo runs on BR2 Heavy, FathomOne, etc.); the
     Bravo path validates the whole "modular adapter" thesis.

2. **`adapter_iso9409_50_4_M6.step`** — ISO 9409-1 50-4-M6 → our M4 flange.
   - Top face: Ø63 mm OD face, Ø50 bolt circle 4×M6 clearance, Ø31.5 H7 spigot,
     Ø6 H7 dowel at +Xm, 0.04 mm flatness band (achieve with PTFE shim).
   - Bottom face: our 4×M4 flange.
   - Material: PA12-GF, estimate ~40 g.
   - Note: **dry-bench-only**. Use to mount on UR3/5/10/16, Franka FR3, Doosan A,
     Fanuc CRX for lab validation of the actuator-current force-sensor chain
     against an ATI Mini40 / Robotiq FT sensor.
   - **Why second:** unlocks ground-truth force comparison; same printed part
     fits 8+ cobot families with no per-vendor variation; the 0 % marginal
     cost of writing the second STEP is decisive.

3. **`adapter_br2_bottom_newton.step`** — BR2 bottom-panel Newton-footprint.
   - Bottom-of-vehicle face: 2× M5 holes on 100 mm pitch with **16° canted axis**,
     16 mm / 31 mm edge offsets — drops into Newton's existing slot with zero
     chassis modification.
   - Top face (= gripper side, since the gripper points down): our 4×M4 pattern.
   - Material: PA12-GF, estimate ~30 g.
   - Cable: 0.6 m service loop to a BR WetLink penetrator on the 4" main tube.
   - **Why third:** the BR2 chassis-mount is the cheapest entry — a hobby user
     replaces a Newton with our gripper for the same 2 bolts and the same
     cable run. Greatest market by unit count.

### 2.2 Model second wave (P1 — variants of the P0 adapters, same printed pattern, extra surface)

4. **`adapter_iso9409_80_6_M8.step`** — same pattern for UR20-class arms.
   Same source as #2; takes ~30 min once the 50-4-M6 part is parametric.

5. **`adapter_br2_roof_rack.step`** — front-mount variant. Reuses the 2-hole
   Newton footprint that's printed on the Roof Rack itself, plus a 10°-tilt
   option from the rack's two top-mount positions. Same gripper underside.

6. **`adapter_br2_payload_skid.step`** — Payload Skid 3" canister cradle +
   Newton footprint underneath. Production "full kit" path.

### 2.3 Model last (P2 — held-tool option for work-class arms)

7. **`adapter_iso13628_d_handle.step`** — print an ISO 13628-8 / API 17H
   D-handle directly onto our gripper's canister body (Ø19 mm bar, Ø70 mm
   flange, Ø56 PCD, 4–8 × M6). The work-class arm clamps the handle with
   its existing jaws — no bolt-on, no scale mismatch, vendor-agnostic
   across Schilling/Kraft/ECA/Hydro-Lek. This is the Schilling Option B
   from the dossier and the honest answer to "can it work on a TITAN 4?"
   (Answer: yes, as a held tool, not as a bolted jaw replacement.)

### 2.4 Blocked / out of scope

- **Reach Alpha 5 dedicated adapter.** Needs RA-1013 drawing from Reach
  Sales OR a delivered RA-1014 stock jaw to reverse-measure. Track as an
  open question; do not model speculatively.
- **Schilling/Kraft bolted Option A.** Pursued only if a vendor integration
  drawing becomes available. Out of scope for a polymer 250 g gripper anyway.
- **Mecademic Meca500.** Out of scope (non-ISO 4×M3 pattern + 0.5 kg
  payload + 3.4 N·m moment ceiling — at the lower edge of our envelope).

---

## 3. Cross-cutting findings (the patterns that show up in all four dossiers)

### 3.1 No wrist on any real arm can power our 6 A stall — external supply mandatory

| Source bus | Max continuous current | Verdict |
|---|---|---|
| UR Tool I/O M8 (24 V) | 600 mA | ❌ insufficient (10× short of 6 A stall) |
| Franka FCI tool connector | ~1.5 A | ❌ insufficient |
| Kinova Gen3 wrist (PoE+) | depends on injector | ⚠️ marginal; needs class-aware PD |
| Reach Bravo controller pass-through | NDA, but arm itself is 400 W class | ✅ likely sufficient (request from sales) |
| Schilling 24 V aux bus | 1.875 A at TITAN 4 slave | ❌ insufficient — needs ROV-side step-down |
| BR2 main tube 14 V power bus | 5–10 A budget per channel | ✅ sufficient via WetLink |

**Consequence:** every adapter spec lists a separate XW540 power feed
(WetLink penetrator → buck/regulator → canister) regardless of arm. The
adapter geometry does not carry the power circuit.

### 3.2 Mass / load mismatch is the real Schilling story

Our gripper is **0.3 % of a Schilling TITAN 4's full-extension lift rating.**
A bolted Schilling jaw-replacement adapter is technically possible but
*operationally dangerous* — the arm could crush the polymer gripper with a
miscommand. The dossier's pivot to the **ISO 13628-8 D-handle** (held tool)
is the correct response: the work-class arm grips a standardised handle
*as it grips any other tool*, applying a finite, gentle clamp force that
the gripper handle can be designed to absorb.

The same scale honesty applies — softly — to the Mecademic Meca500 on the
ISO 9409-1 side: 0.5 kg payload limit is below our ~0.3 kg gripper but the
inertia + finger contact forces during cycling can exceed Meca's joint-6
shear. Excluded from scope.

### 3.3 The Bravo 7 is the cheapest "real adapter" to ship — fully spec'd today

It's the only manipulator interface in the four dossiers where:
- Every dimension is published.
- The arm is mass-appropriate for our gripper.
- The arm runs RS-485 + 24 V (matches our actuator).
- The market is the largest in our deployment envelope (BR2 Heavy +
  inspection-class).

The fact the dossier produced 774 lines and the adapter parameters fit on a
single screen reflects how complete the Reach Robotics documentation is.

### 3.4 BR2 chassis-mount inherits Newton's 16° tilt — non-obvious

BR's drilling template canted the Newton's two-hole footprint 16° so the
jaws clear the bottom panel and aim into the front-camera frustum. **Any
third-party gripper that wants to drop into the Newton slot must inherit
that 16° rotation in the printed adapter** — or publish its own offset
that re-aims the jaws.

This is captured in the BR2 dossier §3c. It is the single design constraint
the original brief hadn't anticipated.

### 3.5 The depth-tier map is unchanged by interface choice

| Interface | T1 (≤10 m) | T2 (≤30 m, primary) | T3 (>30 m) |
|---|---|---|---|
| Reach Bravo 7 | ✅ | ✅ | ✅ (arm 450 MSW) |
| Reach Alpha 5 | ✅ | ✅ | ✅ (arm 300 MSW) |
| ISO 9409-1 cobot | dry only | dry only | dry only |
| Schilling D-handle | ✅ | ✅ | ✅ (arms 4 000–7 000 m) |
| BR2 chassis | ✅ | ✅ | ❌ (BR2 = 100 m rated) |

The lip-seal / magnetic-coupling decision (`ROV_INTEGRATION.md §2d`) is
unaffected — depth tier still determines that crossing, not the upstream
mount.

---

## 4. Open questions (the gaps each dossier flagged)

| # | Question | Blocks | Resolution path |
|---|---|---|---|
| Q1 | Reach Alpha 5 jaw mating thread + collar OD + dowel pattern | `adapter_alpha5.step` | Request RA-1013 drawing from Reach Sales OR reverse-measure a delivered RA-1014 jaw |
| Q2 | Schilling/Kraft wrist flange BC + bolt size + OD + dowel (across vendors) | bolted Option A only | NDA integration manual OR measure a delivered jaw assembly; ignore unless someone funds a TITAN 4 demo |
| Q3 | BR2 side-panel hole grid (the often-repeated "25 mm M3" claim) | nothing critical (we use Newton + Roof Rack + Skid instead) | Photogrammetry of a delivered BR2 side panel; not on critical path |
| Q4 | BR2 Roof Rack per-feature hole coordinates | `adapter_br2_roof_rack.step` precision | Buy a Roof Rack + measure; or reuse the Newton 2-hole subset that's printed on it |
| Q5 | Newton-bracket OEM outer dimensions (the aluminium L-bracket) | not on critical path | Photogrammetry of a delivered Newton; or design freestanding without referencing Newton's L-bracket envelope |
| Q6 | Reach Bravo RB-1054 cable pin-out + RS-485 wiring on the Reach side | Bravo demo electrical bring-up | RSCP protocol document (NDA from Reach Sales) |

Q1 + Q2 are the only **modelling-blocking** questions; the rest are
deferrable.

---

## 5. Cross-refs

- Mounting baseline (M4 flange, galvanic isolation, fastener selection):
  [`ROV_INTEGRATION.md`](ROV_INTEGRATION.md) §1.
- Actuator + sensing tying the bus to the interface choice:
  [`SELECTION.md`](SELECTION.md), [`SENSING.md`](SENSING.md),
  [`MOTOR_STUDY.md`](MOTOR_STUDY.md).
- Depth-tier sealing choice (which is the upstream choice — lip seal vs
  magnetic coupling — that determines the canister, not the wrist):
  [`ROV_INTEGRATION.md`](ROV_INTEGRATION.md) §2d.
- Underwater materials + galvanic isolation:
  [`../docs/UNDERWATER.md`](../docs/UNDERWATER.md) §5.
- Drivetrain ceiling that bounds all transmitted force across every interface:
  [`DRIVETRAIN.md`](DRIVETRAIN.md), `T_safe ≈ 0.034 N·m`.

---

## 6. Provenance

Research executed 2026-05-26 by a 4-agent concurrent web-research swarm
(one general-purpose agent per interface family). Each agent's transcript
ID and source-citation set are preserved at the end of its dossier file.
Cumulative output: 2 673 lines across the four dossiers, ~150 numbered
sources, every published dimension cited.

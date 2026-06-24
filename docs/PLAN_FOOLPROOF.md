# Plan — make the gripper fool-proof & maintenance-free

**Goal (one sentence):** dive it, rinse it, forget it — a user cannot assemble it
wrong, cannot lose a part, cannot leave a joint half-seated, and the post-dive
routine collapses to a single freshwater dunk with **no scheduled inspect /
tighten / replace**.

This is *not* a kinematic or drive change. The mechanism, the crown/pinion mesh,
the four-bar, and the flooded/zero-hardware/all-printed architecture are all
**frozen**. Everything here is hardening the human-and-environment interface
around that frozen core.

Method: walk the **two lists that already exist in the repo** and assign one CAD
change to each line. No new taxonomy.

---

## List A — every post-dive maintenance burden (UNDERWATER §checklist) → kill it

| Today's burden (UNDERWATER post-dive) | CAD change that removes/reduces it | Item # |
|---|---|---|
| "Cycle to flush grit; inspect teeth for wear" | Grit-**tolerant** mesh: enlarged tooth-root debris relief + a touch more backlash so sand passes instead of jamming; nothing to inspect | 6 |
| "Rinse thoroughly… salt crystallizes and abrades" (implies trapped sediment) | Swept, ledge-free cavity floor + bigger wash-through path so one dunk self-clears; no flat shelf holds sand | 7 |
| "Inspect every pivot pin / cover clip for loss of engagement; **replace pins that loosened**" | Retention is geometric (ENGAGEMENT.md); the old one-piece sprung-barb finger pin is **now replaced** by the creep-immune two-piece heat-stake pin (plain journal pin + separate PETG-HF cap melted into a thermal-rivet head wider than the bore — DONE); cover gets a secondary detent so it can't back out | 4, 8 |
| Implicit: user must verify cavity actually flooded (front-up RISK) | Already mitigated (3 cover vents); plan keeps them, no new burden | — |

Target end state of the checklist: **"Rinse with fresh water. Done."**

## List B — every plausible user mistake → make it physically impossible

| Mistake a user can make today | Poka-yoke that prevents it | Item # |
|---|---|---|
| Install `finger_L` / `drive_arm_L` on the right side (chiral) | Embossed **L/R + arrow**, *and* an asymmetric key step so the mirror part physically won't seat | 1, 2 |
| Print a part in the wrong polymer (PLA / ester-TPU / unfilled nylon) | Embossed **material code** sunk into each part (`PA12-GF`, `PETG-HF`, `TPU`) | 1 |
| Lose one of 12 loose small parts (8 pins + 4 dowels) | **Captive pins** — see the FORK below; loose-part count → 0 | 3 |
| Insert a pin from the wrong face / backwards | Directional lead already exists; add a visibly oversized flag end + the captive tether only reaches one way | 3 |
| Snap the cover on **half-latched** and not notice | Cover sits **~0.5 mm proud until fully clicked** (visible witness) + secondary detent on ≥2 clips so it can't creep back out | 4 |
| Over-drive the actuator into a dead-point / over-travel and strip teeth or snap a link | **Integral hard stops** at open & closed end-of-travel, rigid in the enclosure | 5 |
| Forget the assembly order (dowels-before-cover) and have dowels back out underwater | Captive tether (#3) removes the consequence; plus an embossed "1·2·3" order hint near each feature | 1, 3 |

---

## Ranked change list (impact × ease)

1. **Embossed callouts** — `L`/`R`, material code, and step-number hints sunk
   ~0.4–0.6 mm into every chiral / material-sensitive part. Trivial geometry,
   eats ~80 % of mis-assembly + wrong-material risk. *Do first.*
2. **Chiral keying** — an asymmetric mount step / key-rib so a mirrored part
   refuses the wrong side. Cheap, total poka-yoke. (Fingers + drive arms; the
   `follower` is already a symmetric shared part — no keying needed there.)
3. **Captive pins** — the biggest single win: 12 loose parts → 0. **This is the
   one real fork — see below.** Default plan: tethered (3a).
4. **Cover full-seat witness + secondary detent** — FINAL_QA §5 deliberately
   skipped the C-4 detent; this mandate is exactly the reason to revisit. Make a
   partial latch *visible* (proud cover) and add a secondary lip on ≥2 of 4
   clips so a creep-relaxed arm can't back out under vibration.
5. **Integral hard stops** at open/closed travel limits — rigid bumpers in the
   enclosure that bottom the cranks just past the kinematic end-points, so an
   over-driven actuator dumps load into the housing, not into the gear teeth or a
   link. (Must sit *outside* the verified arm sweep — places at ≥travel-limit.)
6. **Grit-tolerant mesh** — enlarge tooth-root debris relief + a hair more
   backlash so sand passes through. Kills the "cycle to flush grit / inspect
   teeth" item. (Backlash up only — never tighten; UNDERWATER C-5/6.)
7. **Swept, ledge-free cavity floor** — fillet/slope the internal floor so no
   flat shelf traps sediment and one rinse drains it. Reduces the rinse burden.
8. **Two-piece captive finger pin** — **DONE via heat-stake melt caps.** The
   one-piece sprung barb (least creep-proof feature even after the counterbore
   fix) is replaced by a plain journal pin + a separate PETG-HF cap melted over
   its stud with a soldering iron into a thermal-rivet head wider than the bore
   (geometric formed-head retention, UNDERWATER constraint #3). All 8 pivot pins
   now use this scheme.

---

## THE ONE FORK (pin retention) — needs your call

- **3a — Tethered captive pins (RECOMMENDED).** Each pin/dowel keeps its current
  creep-proof geometric capture but gains a thin printed flex lanyard to its host
  part. Can't be lost, can't be installed in the wrong hole (tether only reaches
  its own), still removable for service. Lowest risk; preserves every FINAL_QA
  pass.
- **3b — Print-in-place pivots.** Eliminate the separate dowels entirely; print
  the four-bar joints in place with built-in clearance. Maximum fool-proofing
  (truly zero loose parts) **but** FDM-quality-dependent and can *introduce* a
  fused/jam-in-place failure that needs… maintenance — the opposite of the goal.
  Not recommended.
- **3c — Conservative.** Keep discrete loose pins; do only labeling (#1) +
  keying (#2) + the two-piece finger pin (#8). Smallest change.

---

## Out of scope (so this doesn't grow legs)

- Slip-clutch / torque-limiting coupler — FDM repeatability is dicey; **hard
  stops (#5) + grit-tolerant teeth (#6)** cover the same failure more reliably.
- Removing the snap-clip cover or going to a screwed/sealed lid.
- Any change to kinematics, gear ratio, or the crown/pinion mesh.
- Tightening any running/print clearance (UNDERWATER C-5/6 forbids it).

## Invariants — must still hold after every step (re-run FINAL_QA)

- Kinematics monotonic, no dead-point (base/tip gap, finger_rot tables unchanged).
- Interference 0 mm³ across motion (project recipe) at open 0/.25/.5/.75/1.
- All STLs watertight / single-body / single-shell; flooded, no enclosed void.
- Wall minimums met; finger-vs-finger = 0 at closed.
- All-printed, zero-hardware, 0.4 mm-nozzle FDM-printable, flooded.

## Process (unchanged from prior work)

Per item: measure → advisor → implement (Claude agent swarm where parallelizable)
→ verify (build + interference + manifold, in my own hands for strain/interference
gates) → render → `regen.sh` → reconcile docs → commit. Strain-critical and
authoritative-interference builds stay on me (delegated geometry has
false-positived before).

## Suggested sequencing (phases)

- **Phase 1 (zero-risk, do immediately):** #1 embossed callouts, #2 chiral keying.
- **Phase 2 (retention):** #3 (per your fork choice) + #8 two-piece finger pin.
- **Phase 3 (robustness):** #5 hard stops, #4 cover witness+detent.
- **Phase 4 (maintenance-free):** #6 grit-tolerant mesh, #7 swept cavity floor.
- Commit per phase; full FINAL_QA re-run before the final commit.

## Pin-retention memo — alternatives to the heat-stake melt cap

**To:** gripper designer  **From:** DFM/fastening lead  **Re:** 8 pivot pins (4 axle A/B, 4 finger C/D)

### Framing — what we're actually replacing
The heat-stake works and is the bar: **geometric, creep-proof, friction-independent**, formed in rigid PETG-HF, head ~1.0–1.1 mm wider than every bore it crosses (finger eye `FP_ARM_BORE_R` 1.6 → 1.0 mm shoulder; axle flood hole 1.5 → 1.1 mm shoulder). It already buried the two real failures: the **brittle barb** (split cantilever fractured, twice in the field) and the **loose dowel** (running fit + seating gap → wobble + slide-out). Any replacement that re-introduces an *elastic* catch or leans on *friction/press* is dead on arrival.

What we're paying to escape is narrow and specific: (a) a **freehand soldering iron** whose result is operator-judgment-dependent, (b) it's **permanent** — service = slice + reprint, (c) **8 loose caps** to handle. So "better" = keep the formed-head physics, kill the iron *or* make the forming idiot-proof, and ideally make it come apart for service. Everything below is judged on exactly that, at GRIPPER_SCALE 1 on a 0.4 mm nozzle, flooded.

A blunt reality first: **nothing fully tool-free beats a formed solid head on the no-creep axis.** Snap-style anything trades creep-immunity back for an elastic feature. So the honest play is a *portfolio*: a tool-free mechanical equivalent of a formed head where it can be made truly geometric (cross-pin), a better-formed-head process where we keep forming but remove the freehand skill (collet/heat-set or a press/jig), and a serviceable geometric capture for the joints we'll actually want to open. Match the method to the pin, don't seek one winner.

---

### TOP PICKS (pursue these)

**1. Printed cross-pin / cotter through a transverse hole (the tool-free formed-head equivalent).**
The pin protrudes past the retaining face and carries a small **cross-bore**; a second tiny printed **cotter pin** (or a printed split-tab wedge) pushes through it, sitting proud of the bore on both sides = a hard geometric stop, exactly like a clevis pin. **This is the only genuinely tool-free option that stays purely geometric** — no melt, no elastic catch, no friction. It directly answers downside (a) [no iron] and (c) [it *is* a part, but it's a positive captured one, and it's removable]. **Reversible:** pull the cotter, pin drops out, re-pin to service — beats the heat-stake outright on serviceability.
- *Suits:* **AXLE pins first** — the back wall is open and accessible from outside, there's room for the transverse hole and cotter in free space behind the wall, and the cotter can be a tethered flag so it can't be lost or mis-installed (ties straight into the existing "tethered captive pins / 3a" plan in PLAN_FOOLPROOF.md).
- *Watch:* at SCALE 1 the cross-bore is ~1.0–1.3 mm in a ~2.6 mm stud — printable on a 0.4 mm nozzle but it's the small-feature limit; orient the hole vertically when printing the pin (or print the cotter separately and ream the bore) so it isn't a sagging horizontal hole. Finger pins are tighter for room inside the eye boss — viable as a bench-sub-assembly cotter but the axle is the cleaner home.

**2. Heat-SET (soldering-iron-driven collet / forming jig) — keep the melt, delete the freehand.**
Same formed-PETG physics, but instead of mushrooming a cap by eye you press the stud into a **flared printed collar with a shaped forming tool** (a printed/CNC tip the iron heats, with a cone that forms a *repeatable* head every time) — the heat-set-insert workflow, applied to plastic-on-plastic. You still use heat, but the **head shape is set by the tool, not the operator's judgment**, which kills downside (a)'s real sting (quality variance) even though it doesn't go fully tool-free. Lowest-risk delta from today: the bores, the studs, the assembly sequence, and the proven capture geometry are all **unchanged** — you're only swapping a freehand action for a piloted one.
- *Suits:* **both axle and finger pins** — it's a drop-in process change over the current scheme, so it inherits the finger bench-sub-assembly and the axle back-wall-outside capping verbatim.
- *Watch:* still permanent (no service win), still needs heat. But it's the safest path to "less operator-dependent" with zero geometry re-verification, so it's the conservative hedge if cross-pinning slips.

**3. Two-piece pin + printed wedge/taper-lock collar (snap-free positive capture, serviceable).**
A separate **collar** drives down a **shallow taper** on the protruding stud and **bottoms hard in the face recess** (`MELT_RECESS_*` plumbing already exists) so capture is a **wedged solid in compression against a rigid shoulder — geometric, not a sprung catch.** Critically: design it to **lock by seating geometry, not by an elastic cantilever** — that's the line that keeps it on the right side of the barb failure. Hand-press to assemble (tool-free), and it's **removable** with a pry at the recess for service. It's the "snap-together-by-hand" feel the philosophy wants without the brittle split-finger.
- *Suits:* **finger pins** — the bench sub-assembly gives you both ends and a backstop to press against, and the eye boss (`FP_EYE_BOSS_R` 3.9) already carries a confining ring for the collar.
- *Watch:* this is the riskiest of the four — a taper/wedge in PETG can relax if it's relying on interference rather than a hard bottoming shoulder. Spec it so the collar **bottoms metal-to-metal (shoulder-to-shoulder)** and the taper only centers/aligns; if it ends up holding by press, it has quietly become the dowel failure. Prototype and pull-test before trusting it.

**4. Riveted second-head by cold-forming a press / arbor jig (no heat at all).**
For the **axle pins specifically**, the head is formed from outside the back wall — a place a small **bench arbor / clamp** can reach. Form the rivet head by **cold upset / mechanical press into the recess** instead of melting it. Fully **tool-free for the operator at the dive site** in the sense that the *forming* moves to a one-shot bench jig (squeeze, done) — no iron, no skill, repeatable by the jig stop. Geometric formed head, creep-proof, same physics as the heat-stake minus the thermal variance.
- *Suits:* **AXLE pins only** (back-wall access + a flat exterior face to press against). Not the finger pins (no clean press reaction path inside the housing).
- *Watch:* PETG cold-forms less cleanly than it melts; may need a warm (not molten) stud or a stud geometry tuned to fold rather than crack. Treat as an axle-only experiment, validate the head won't split on upset.

---

### Where the heat-stake is genuinely hard to beat (be honest)
- **No-creep formed head is its superpower.** Every tool-free *snap/wedge* option re-opens an elastic-relaxation question the melt cap simply doesn't have. The melt cap's head is a solid larger than the hole, full stop — only the **cross-pin (#1)** matches that with zero elastic content, and only the **press-rivet (#4)** matches it with zero parts-added.
- **Zero special tooling, ubiquitous.** A soldering iron is something every builder already owns; a forming jig or arbor (#2/#4) is one more thing to make and ship. The iron's *skill* is the problem, not the iron.
- **Part count is already low for what it does.** The cap is one tiny identical SKU ×8. Cross-pins (#1) *add* a second tiny part per joint (mitigated only by tethering); the heat-stake's loose-part pain is real but small.
- **It's fully verified.** ENGAGEMENT.md gates, interference-clean at 0/0.5/1.0, single-valid-solid checks all currently pass *for this geometry*. #1, #3, #4 all force a re-verification pass. #2 is the only one that doesn't.

So the heat-stake stays the **baseline**, not a mistake. We're buying serviceability and skill-removal, and we should only pay for them where they matter.

---

### Recommendation in one line
**Cross-pin the axle pins (#1) for a tool-free, reversible, purely-geometric capture that folds into the existing tethered-captive-pin plan; keep the finger pins on a heat-SET/jig-formed head (#2) so the bench sub-assembly is unchanged but the freehand variance is gone.** That splits the problem the way the hardware splits: open-access axles get the real upgrade, the fiddly captured finger joints get the low-risk one.

### Next step (concrete)
**Print one axle-pin coupon with the cross-bore + a tethered printed cotter at SCALE 1**, plus a scrap back-wall recess block, and run the same gate the heat-stake passed: confirm (i) the cross-bore prints clean on the 0.4 mm nozzle without sagging, (ii) the cotter seats proud both sides and gives a head wider than the flood hole, and (iii) a pull test on the assembled pin can't extract it and a hand-pull on the cotter *can* (the service path). If the 1.0–1.3 mm cross-bore is marginal, fall back to #2 (heat-set jig) for the axles too. One print, one afternoon, decides it.

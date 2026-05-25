# SURVEY.md provenance — the research swarm

`SURVEY.md` was merged from a **12-agent concurrent research swarm** (Claude
sonnet sub-agents, live web search against manufacturer datasheets + retailer
pages, May 2026). Each agent was instructed: cite every torque/voltage/price/IP
number or mark it `n/a`; never invent specs; convert torque to N·m; price in AUD.
This file records the roster for traceability; the merged data + inline source
numbers live in `SURVEY.md`.

## Actuator-class agents (one per class)

| Agent ID | Class | Headline finding |
|---|---|---|
| af11a1c64713d742b | Submersible / IP servos | Blue Trail Eng. genuinely T2/T3-sealed (200–400 m) but **all PWM → DEAD on sensing**; Savox/Hitec IP67 = T1 splash only |
| ae8d73676afe3c01f | Potted / oil-fill DIY servos | oil-fill proven T1, anecdotal T2; cheap PWM bases → DEAD-sense; only meaningful if base is a smart serial servo |
| a62b1666875372193 | Brushed DC + canister | worm-gear (ZD1530R 5 N·m) self-locks → **zero hold current**; sensing via external shunt = coarse (±10–20 %) |
| ab7957d651941113b | BLDC / robot-actuator | FOC iq = best dynamic sensing; **Volz DA-SUB** is the turnkey T2/T3 telemetry servo (quote-only); flooded M200 **blind at stall** |
| a2edc31b946577698 | Stepper + canister | **JMC IHSS57 RS-485 closed-loop** streams current+position >50 Hz; StallGuard too slow (~3 Hz @ 20 rpm); holding heat |
| a34ea32f04c134249 | Magnetic coupling | no dynamic seal → **T3 winner**; KTR MINEX-S SA 60/8 (7 N·m) / N52 80 mm (~6 N·m) clear stall; pole-slip = force limiter; sensing inherited from pod motor |
| aedb09c893b9dec6a | Smart serial servos (+ telemetry, M4) | **the R10 front-runner** — native `present_current`; DYNAMIXEL XW = IP68 + telemetry; Feetech STS3215 cheap; Hiwonder **lacks current register → DEAD** |

## Sensing-modality agents (one per modality)

| Agent ID | Modality | Headline finding |
|---|---|---|
| a65776d326669e5a5 | M1 current-shunt + back-EMF (brushed) | resolution fine (INA226/240); accuracy ±10–20 % raw, ±5–10 % calibrated; `I_0` + ripple dominate |
| a3afc7395b58b7f0c | M2 FOC iq telemetry | cleanest; **holds torque at stall**; ±2–5 % cal; moteus int32 = 1 mA/1 mN·m over CAN-FD |
| a4b4338f03a256079 | M3 sensorless hall/back-EMF | **blind below ~10–20 % rated speed = blind at stall**; contact/stall detection only, never primary force readout |
| a498140ea8923cf9b | M5 strain-gauge / load cell | bench load cell = calibration ground truth (<0.05 N ref unc.); **in-situ NOT recommended** (re-adds TPU wiring penetrations) |

*M4 (smart-servo serial telemetry) was folded into the Class-7 agent
(aedb09c893b9dec6a), which captured the `present_current` register resolution,
poll rate and protocol per servo — avoiding a redundant agent.*

## Honesty notes carried into SURVEY.md / SELECTION.md
- The **sensing pivot eliminates the best-sealed option** (Blue Trail Eng.) — a
  result worth stating plainly to judges, not hiding.
- Smart-serial waterproofing gap: only DYNAMIXEL **XW** is IP-rated, and only to
  1 m freshwater → T2 still needs a canister; seawater adds corrosion.
- All prices are indicative (May 2026), AUD via USD×1.55 where AU retail was not
  found; treat as ranking inputs, not quotes.

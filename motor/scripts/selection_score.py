"""Weighted multi-criteria actuator selection + +/-50% weight sensitivity, swept
across all three depth tiers. Mirrors grip/scripts/sensitivity.py discipline:
state the weights, score each candidate, then perturb every weight +/-50% and
re-rank to show how stable the winner is (and where it flips).

Scores are engineering judgements (0..1) read off SURVEY.md's sourced data; the
point of the sweep is not false precision but to show WHICH assumption flips the
choice -- exactly the honesty the campaign requires. Depth-fit is the only
tier-dependent criterion (an actuator's sealing suits some depths better).

Run:  python motor/scripts/selection_score.py
"""
import json
import os

# ---- criteria + baseline weights (stated; sum = 1.0) ----------------------
WEIGHTS = {
    "sensing":        0.25,  # R10: force-telemetry fidelity (the pivot) -> primary axis
    "torque":         0.15,  # R1: meets >=1.2 N.m cont + stall band
    "depth_fit":      0.20,  # R7: how well it serves the active depth tier
    "modularity":     0.15,  # drop-in at the D-coupler; single-bus; same part across depths
    "integration":    0.10,  # electrical/build simplicity (1 wire vs FOC+CAN+housing)
    "holding_thermal":0.07,  # hold-power + heat in a sealed/flooded enclosure
    "cost":           0.08,  # AUD
}

# ---- per-candidate scores (0..1), from SURVEY.md ---------------------------
# depth_fit is given per tier: (T1, T2, T3)
CAND = {
    "A_dynamixel_XW540": dict(
        label="DYNAMIXEL XW540-T260 (smart serial)",
        sensing=0.95, torque=0.85, modularity=0.85, integration=0.90,
        holding_thermal=0.80, cost=0.20, depth_fit=(0.95, 0.70, 0.35)),
    "B_foc_bldc": dict(
        label="FOC BLDC (moteus/ODrive)+gearmotor+canister",
        sensing=0.90, torque=0.90, modularity=0.60, integration=0.35,
        holding_thermal=0.70, cost=0.45, depth_fit=(0.70, 0.72, 0.78)),
    "C_jmc_stepper": dict(
        label="JMC IHSS57 closed-loop stepper (RS-485)",
        sensing=0.75, torque=0.88, modularity=0.65, integration=0.65,
        holding_thermal=0.30, cost=0.75, depth_fit=(0.75, 0.65, 0.30)),
    "D_magnetic_pod": dict(
        label="Magnetic coupling + smart-servo/FOC dry pod",
        sensing=0.85, torque=0.75, modularity=0.90, integration=0.45,
        holding_thermal=0.75, cost=0.45, depth_fit=(0.80, 0.90, 0.95)),
    "E_feetech_STS3215": dict(
        label="Feetech STS3215 (canister)",
        sensing=0.80, torque=0.55, modularity=0.75, integration=0.85,
        holding_thermal=0.70, cost=0.98, depth_fit=(0.80, 0.45, 0.15)),
    "F_worm_dc": dict(
        label="Brushed worm-DC + current shunt",
        sensing=0.40, torque=0.95, modularity=0.55, integration=0.45,
        holding_thermal=0.98, cost=0.85, depth_fit=(0.75, 0.65, 0.30)),
}
TIERS = ("T1", "T2", "T3")


def score(cand, weights, tier):
    c = CAND[cand]
    s = 0.0
    for k, w in weights.items():
        v = c["depth_fit"][TIERS.index(tier)] if k == "depth_fit" else c[k]
        s += w * v
    return s


def ranking(weights, tier):
    return sorted(CAND, key=lambda c: score(c, weights, tier), reverse=True)


def _norm(w):
    tot = sum(w.values())
    return {k: v / tot for k, v in w.items()}


def sensitivity(tier, primary):
    """Perturb each weight x1.5 and x0.5 (renormalised); count how often `primary`
    stays #1 at this tier."""
    settings = []
    stable = 0
    total = 0
    for k in WEIGHTS:
        for f, tag in ((1.5, "+50%"), (0.5, "-50%")):
            w = dict(WEIGHTS)
            w[k] *= f
            w = _norm(w)
            win = ranking(w, tier)[0]
            ok = (win == primary)
            stable += ok
            total += 1
            settings.append((f"{k} {tag}", win, ok))
    return stable, total, settings


if __name__ == "__main__":
    out = {"weights": WEIGHTS, "tiers": {}}
    print("=== baseline weighted scores by depth tier ===")
    for tier in TIERS:
        ranked = ranking(WEIGHTS, tier)
        print(f"\n--- {tier} ---")
        scores = {}
        for c in ranked:
            sc = score(c, WEIGHTS, tier)
            scores[c] = sc
            print(f"  {sc:.3f}  {c:20s} {CAND[c]['label']}")
        primary = ranked[0]
        stable, total, settings = sensitivity(tier, primary)
        print(f"  winner={primary}  sensitivity: stays #1 in {stable}/{total} "
              f"+/-50% weight perturbations")
        flips = [(s, w) for (s, w, ok) in settings if not ok]
        if flips:
            print("  flips ->", "; ".join(f"{s}=>{w}" for s, w in flips))
        out["tiers"][tier] = dict(
            ranking=ranked, scores=scores, primary=primary,
            stability=f"{stable}/{total}",
            flips=[{"perturb": s, "winner": w} for (s, w, ok) in settings if not ok])

    itdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "iterations")
    os.makedirs(itdir, exist_ok=True)
    with open(os.path.join(itdir, "_selection.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nwrote {os.path.join(itdir, '_selection.json')}")

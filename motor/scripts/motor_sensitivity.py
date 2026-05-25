"""Phase-5: +/-50% sensitivity envelope for the motor model (grip campaign discipline).

Perturbs each uncertain coefficient +/-50% and checks whether the model's QUALITATIVE
conclusions survive:
  C1  "the gear ceiling binds, not the servo"   (T_safe < servo continuous torque)
  C2  "achievable grip stays below the 12 N FEA level" (even at the proposed re-size)
  C3  "the chain is back-drivable -> active hold, but holding current is sub-amp"
Coefficients swept: eta (efficiency), T_safe (gear allowable), MA (Jacobian),
Kt (torque constant).  Run: python motor/scripts/motor_sensitivity.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kinematics_chain as kc  # noqa: E402

ITER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "iterations")

BASE = dict(eta=0.5, T_safe=0.40, MA=kc.contact_MA(0.05, 0.55), Kt=1.86, i_g=2.0,
            servo_cont=0.98, stall=9.5)   # proposed re-size + weakest servo cont torque


def evaluate(p):
    F_mid = p["T_safe"] * 1000.0 * p["i_g"] * p["MA"] * p["eta"] / 2.0
    gear_binds = p["T_safe"] < p["servo_cont"]
    below_12 = F_mid < 12.0
    hold_current = p["T_safe"] / p["Kt"]
    return dict(F_mid=round(F_mid, 2), gear_binds=gear_binds, below_12=below_12,
                hold_current_A=round(hold_current, 3))


def run():
    base = evaluate(BASE)
    rows = []
    flips = []
    for k in ("eta", "T_safe", "MA", "Kt"):
        for f, tag in ((1.5, "+50%"), (0.5, "-50%")):
            p = dict(BASE); p[k] = BASE[k] * f
            r = evaluate(p)
            ok = (r["gear_binds"] == base["gear_binds"]) and (r["below_12"] == base["below_12"])
            if not ok:
                flips.append(f"{k} {tag}")
            rows.append((f"{k} {tag}", r))
    return base, rows, flips


if __name__ == "__main__":
    base, rows, flips = run()
    print(f"BASE (proposed re-size): F_mid={base['F_mid']}N gear_binds={base['gear_binds']} "
          f"below_12={base['below_12']} hold={base['hold_current_A']}A\n")
    for tag, r in rows:
        print(f"  {tag:12s} F_mid={r['F_mid']:5.1f}N  gear_binds={r['gear_binds']!s:5s}  "
              f"below_12={r['below_12']!s:5s}  hold={r['hold_current_A']}A")
    print(f"\nC1 gear-binds + C2 below-12N invariant under +/-50%: "
          f"{'YES (no flips)' if not flips else 'FLIPS: ' + ', '.join(flips)}")
    print("C3 holding current stays sub-amp across all perturbations: "
          f"{'YES' if all(r['hold_current_A'] < 1.0 for _, r in rows) else 'NO'}")
    json.dump(dict(base=base, rows=[{"perturb": t, **r} for t, r in rows], flips=flips),
              open(os.path.join(ITER, "_motor_sensitivity.json"), "w"), indent=2)
    print("wrote _motor_sensitivity.json")

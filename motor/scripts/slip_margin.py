"""Phase-5 sim 2: slip-margin vs object class (RANK-ONLY).

Couples the actuator force chain (torque_chain.py / kinematics_chain.py) to the
wet-grip model (grip/scripts/grip_model.py) for the SHIPPED crosshatch texture.

Slip margin in an object class = (available per-finger normal force from the
actuator, capped by the Phase-4 gear ceiling) x (the texture's holding-friction
coefficient mu_hold in that class). Object weight/drag is a constant reference, so
across classes the RELATIVE ranking is what this reports -- NOT an absolute slip
force. grip_model.py is itself rank-only (no absolute newtons); this inherits that.

The point: which object classes are slip-risky, and how the gear-limited force
scales the whole curve. Output: motor/iterations/_slip_margin.json + a bar plot.

Run:  python motor/scripts/slip_margin.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "grip", "scripts"))
import kinematics_chain as kc          # noqa: E402
import grip_model as gm                # noqa: E402
import patterns as pat                 # noqa: E402

ITER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "iterations")
PICS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pictures")

# shipped crosshatch (gripper.py FR_GRIP_*: pitch 1.8 / land 1.26 / depth 0.6)
SHIPPED = dict(pitch=1.8, land=1.26, depth=0.6)
# available per-finger force: gear-limited (shipped 0.034 / proposed 0.40 N.m), mid-pose
FORCE_CASES = {"shipped gears (T_safe 0.034 N·m)": (0.034, 2.667),
               "proposed re-size (T_safe 0.40 N·m)": (0.40, 2.0)}


def available_force(T_safe, i_g, eta=0.5):
    return kc.force_for_input_torque(T_safe, kc.contact_MA(0.05, 0.55), eta, i_g)


def run():
    geom = pat.resolve("crosshatch", SHIPPED)
    C = gm.COEFFS
    per_cond = []
    for cond in gm.CONDITIONS:
        r = gm.grip_in_condition(geom, cond, C)
        per_cond.append(dict(name=cond["name"], label=cond["label"],
                             mu_hold=round(r["mu_hold"], 4)))
    out = {"texture": "crosshatch (shipped)", "params": SHIPPED, "per_condition": per_cond,
           "force_cases": {}, "caveat": "RANK-ONLY: relative slip margin across object "
           "classes; not an absolute slip force (grip_model is rank-only)."}
    for cname, (tsafe, i_g) in FORCE_CASES.items():
        F = available_force(tsafe, i_g)
        margins = {c["name"]: round(F * c["mu_hold"], 4) for c in per_cond}
        out["force_cases"][cname] = dict(F_available_N=round(F, 2), slip_margin=margins)
    return out


def plot(out):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception as e:
        print("matplotlib unavailable:", e); return
    conds = [c["name"] for c in out["per_condition"]]
    x = np.arange(len(conds))
    fig, ax = plt.subplots(figsize=(11, 4.6))
    w = 0.38
    for i, (cname, cdat) in enumerate(out["force_cases"].items()):
        vals = [cdat["slip_margin"][c] for c in conds]
        ax.bar(x + (i - 0.5) * w, vals, w, label=f"{cname} (F={cdat['F_available_N']} N)")
    ax.set_xticks(x); ax.set_xticklabels(conds, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("relative slip margin  (F_available × μ_hold)")
    ax.set_title("Slip margin vs object class — crosshatch (RANK-ONLY, not absolute N)")
    ax.grid(axis="y", alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout()
    os.makedirs(PICS, exist_ok=True)
    fig.savefig(os.path.join(PICS, "slip_margin.png"), dpi=110)
    print("wrote", os.path.join(PICS, "slip_margin.png"))


if __name__ == "__main__":
    o = run()
    print("per-condition mu_hold (crosshatch):")
    for c in o["per_condition"]:
        print(f"  {c['name']:13s} mu_hold={c['mu_hold']:.3f}  ({c['label']})")
    for cname, cdat in o["force_cases"].items():
        worst = min(cdat["slip_margin"], key=cdat["slip_margin"].get)
        print(f"\n{cname}: F_avail={cdat['F_available_N']} N -> worst class = {worst} "
              f"(margin {cdat['slip_margin'][worst]})")
    os.makedirs(ITER, exist_ok=True)
    json.dump(o, open(os.path.join(ITER, "_slip_margin.json"), "w"), indent=2)
    plot(o)
    print("wrote _slip_margin.json")

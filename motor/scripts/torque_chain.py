"""Phase-5 sim 1: closed-form motor -> tip-force chain across the full travel.

Builds on kinematics_chain.py (the exact four-bar Jacobian) and adds:
  * the efficiency/friction band (flooded printed drivetrain, UNDERWATER.md context)
  * the Phase-4 gear ceiling T_safe (gear_fea.py) -- the force is the MIN of what
    the servo can push and what the teeth survive
  * per-servo + per-geometry curves (XW540 / STS3215; shipped vs proposed re-size)

This is a RANK/SIZE model, not a calibrated absolute-newton predictor (MOTOR_MODEL.md):
the friction band is an estimate and the texture/contact compliance is bounded, not
measured. Output: motor/iterations/_torque_chain.json + motor/pictures/torque_chain.png

Run:  python motor/scripts/torque_chain.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kinematics_chain as kc  # noqa: E402

ITER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "iterations")
PICS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "pictures")

# selected actuators (continuous torque, N.m) -- SURVEY.md / SELECTION.md
SERVOS = {"XW540-T260": 1.9, "STS3215": 0.98}
# gear ceiling T_safe (N.m): three bounds reported now (per docs/OVERNIGHT_FIXES.md #2):
#   * shipped, single-station 2D crown FEA (gear_fea.py)              = 0.034 N.m
#   * shipped, radial 2D crown FEA inner-edge bound (gear_fea_radial)  = 0.013 N.m
#   * proposed re-size (un-implemented)                                 = 0.40  N.m
T_SAFE = {
    "shipped, radial 2D crown (inner-edge bound)": (0.013, 2.667),
    "shipped, single-station 2D crown": (0.034, 2.667),
    "proposed re-size (i_g 2.0)": (0.40, 2.0),
}
ETA_LO, ETA_HI = kc.efficiency_envelope()


def tip_force_curve(T_motor, i_g, eta, y_frac=0.55):
    """F_tip across open_norm at fixed motor torque, contact at y_frac up the blade."""
    os_ = np.linspace(0.0, 1.0, 41)
    F = [kc.force_for_input_torque(T_motor, kc.contact_MA(o, y_frac), eta, i_g) for o in os_]
    return os_, np.array(F)


def run():
    out = {"eta_band": [round(ETA_LO, 3), round(ETA_HI, 3)], "servos": SERVOS,
           "T_safe": {k: v[0] for k, v in T_SAFE.items()}, "curves": {}}
    for gname, (tsafe, i_g) in T_SAFE.items():
        for sname, tcont in SERVOS.items():
            # the binding torque is min(servo continuous, gear ceiling)
            t_bind = min(tcont, tsafe)
            os_, F_mid = tip_force_curve(t_bind, i_g, 0.5)         # mid-face, mid-eta
            _, F_lo = tip_force_curve(t_bind, i_g, ETA_LO)
            _, F_hi = tip_force_curve(t_bind, i_g, ETA_HI)
            out["curves"][f"{gname} | {sname}"] = dict(
                i_g=i_g, T_cont=tcont, T_safe=tsafe, T_binding=round(t_bind, 3),
                binding="gear" if tsafe < tcont else "servo",
                F_mid_closed=round(float(F_mid[0]), 2), F_mid_open=round(float(F_mid[-1]), 2),
                F_band_closed=[round(float(F_lo[0]), 2), round(float(F_hi[0]), 2)])
    out["open_norm"] = list(np.round(np.linspace(0, 1, 41), 3))
    return out


def plot(out):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        print("matplotlib unavailable:", e); return
    fig, axs = plt.subplots(1, len(T_SAFE), figsize=(4.5 * len(T_SAFE), 4.6), sharey=True)
    if len(T_SAFE) == 1:
        axs = [axs]
    for ax, (gname, (tsafe, i_g)) in zip(axs, T_SAFE.items()):
        for sname, tcont in SERVOS.items():
            t_bind = min(tcont, tsafe)
            os_, F = tip_force_curve(t_bind, i_g, 0.5)
            _, Flo = tip_force_curve(t_bind, i_g, ETA_LO)
            _, Fhi = tip_force_curve(t_bind, i_g, ETA_HI)
            ln, = ax.plot(os_, F, lw=2, label=f"{sname} (bind={'gear' if tsafe<tcont else 'servo'})")
            ax.fill_between(os_, Flo, Fhi, alpha=0.15, color=ln.get_color())
        ax.axhline(12.0, ls="--", c="k", lw=1, alpha=0.6)
        ax.text(0.02, 12.4, "12 N FEA stress-probe", fontsize=8, alpha=0.7)
        ax.set_title(f"{gname}\n(T_safe = {tsafe} N·m)", fontsize=9)
        ax.set_xlabel("open_norm (0=closed → 1=open)")
        ax.grid(alpha=0.3, which="both"); ax.legend(fontsize=7); ax.set_yscale("log")
    axs[0].set_ylabel("per-finger tip force (N), mid-face")
    axs[0].set_ylim(0.05, 14)
    fig.suptitle("Motor → tip-force chain: gear ceiling binds, not the servo "
                 "(12 N is FEA stress-probe, not operating force)", fontsize=11)
    fig.tight_layout()
    os.makedirs(PICS, exist_ok=True)
    fig.savefig(os.path.join(PICS, "torque_chain.png"), dpi=110)
    print("wrote", os.path.join(PICS, "torque_chain.png"))


if __name__ == "__main__":
    o = run()
    print(f"eta band {o['eta_band']}")
    for k, c in o["curves"].items():
        print(f"  {k:38s} T_bind={c['T_binding']:.3f} ({c['binding']})  "
              f"F_mid closed={c['F_mid_closed']:.1f}N open={c['F_mid_open']:.1f}N")
    os.makedirs(ITER, exist_ok=True)
    json.dump(o, open(os.path.join(ITER, "_torque_chain.json"), "w"), indent=2)
    plot(o)
    print("wrote _torque_chain.json")

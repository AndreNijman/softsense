"""Phase-5 sim 3: holding current, thermal duty, and the back-drive check.

For the selected servos, answers three operations questions:
  1. HOLDING current at the working/holding torque (is sustained grip-hold cheap?)
  2. STALL current (the §7 bus/fuse budget = stall, not run) + a thermal-duty note
  3. BACK-DRIVE: is the chain back-drivable? (low ratio + four-bar -> yes) -> the
     actuator must hold position actively; quantify the hold torque vs a tip pull.

Torque constants Kt from SURVEY.md present_current resolution
(XW540: 0.005 N.m / 2.69 mA -> 1.86 N.m/A; STS3215: 0.007 / 6.5 mA -> 1.08 N.m/A).
Stall torque from SURVEY.md. RANK/SIZE estimates, not bench data (MOTOR_MODEL.md).

Run:  python motor/scripts/holding_stall.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kinematics_chain as kc  # noqa: E402

ITER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "iterations")

SERVOS = {
    "XW540-T260": dict(Kt=1.86, stall_Nm=9.5, cont_Nm=1.9, V=12.0),
    "STS3215":    dict(Kt=1.08, stall_Nm=2.94, cont_Nm=0.98, V=12.0),
}
# the chain is gear-limited: the useful holding torque is at/below T_safe
T_HOLD_CASES = {"shipped (T_safe 0.034)": (0.034, 2.667),
                "proposed re-size (T_safe 0.40)": (0.40, 2.0)}
TIP_PULL_N = 5.0   # external disturbance pull at the fingertip, for the back-drive check


def backdrive_hold_torque(F_tip, i_g, eta=0.5):
    """Input-shaft torque the servo must hold to resist a tip pull F_tip [N.m].
    Back-drive is the inverse chain; with positive efficiency the chain transmits
    the disturbance back to the motor (no worm/self-lock), so the servo holds it."""
    MA = kc.contact_MA(0.0, 0.55)
    # F_tip = T_motor * i_g * MA * eta / 2  ->  invert
    return kc.input_torque_for_force(F_tip, MA, eta, i_g)


def run():
    out = {"servos": {}, "tip_pull_N": TIP_PULL_N,
           "backdrivable": True,
           "backdrive_note": "ratio 2.667:1 spur + four-bar, no worm/self-lock -> "
           "back-drivable; a positional servo holds actively, an unpowered chain releases."}
    for name, s in SERVOS.items():
        hold = {}
        for cname, (tsafe, i_g) in T_HOLD_CASES.items():
            # holding the gear-ceiling torque (the max useful grip-hold)
            i_hold = tsafe / s["Kt"]
            # holding against a 5 N tip pull (back-drive resistance)
            t_bd = backdrive_hold_torque(TIP_PULL_N, i_g)
            i_bd = min(t_bd, tsafe) / s["Kt"]
            hold[cname] = dict(hold_torque_Nm=round(tsafe, 3),
                               hold_current_A=round(i_hold, 3),
                               backdrive_hold_torque_Nm=round(t_bd, 3),
                               backdrive_current_A=round(i_bd, 3))
        out["servos"][name] = dict(
            Kt=s["Kt"], stall_Nm=s["stall_Nm"],
            stall_current_A=round(s["stall_Nm"] / s["Kt"], 2),
            cont_current_A=round(s["cont_Nm"] / s["Kt"], 2),
            holding=hold,
            thermal="holding current is sub-amp (gear-limited torque is tiny vs Kt) -> "
                    "sustained grip-hold is thermally trivial; flooded body aids cooling.")
    return out


if __name__ == "__main__":
    o = run()
    print(f"back-drivable: {o['backdrivable']} -- {o['backdrive_note']}\n")
    for name, s in o["servos"].items():
        print(f"{name}: Kt={s['Kt']} N.m/A  stall {s['stall_Nm']} N.m -> "
              f"stall current {s['stall_current_A']} A  (cont {s['cont_current_A']} A)")
        for cname, h in s["holding"].items():
            print(f"   {cname}: hold {h['hold_torque_Nm']} N.m @ {h['hold_current_A']} A; "
                  f"resist {o['tip_pull_N']} N tip-pull needs {h['backdrive_hold_torque_Nm']} N.m "
                  f"@ {h['backdrive_current_A']} A")
        print(f"   thermal: {s['thermal']}")
    os.makedirs(ITER, exist_ok=True)
    json.dump(o, open(os.path.join(ITER, "_holding_stall.json"), "w"), indent=2)
    print("\nwrote _holding_stall.json")

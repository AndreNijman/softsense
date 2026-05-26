"""Drivetrain-deliverable per-finger force envelope.

This is the missing link between motor/gear_fea.py (T_safe = ceiling input-shaft
torque the printed crown/pinion can take without root-bending failure) and the
finger-FEA campaign (which reported margins at TARGET_GRIP = 12 N — a stress-
probe load used to rank designs, NOT a force the shipped drivetrain can safely
deliver).

It runs gear_fea.run() to get T_safe, kinematics_chain to get the i_g, MA(P) and
efficiency band, and computes the per-finger force band the drivetrain can
*safely* deliver via:

    F = T_in * i_g * MA(P) / 2 * eta            (kinematics_chain eq.)

over the (MA_low, MA_high) and (eta_low, eta_high) corners. The result is a 4-
corner band (worst .. best) at the currently-shipped gear design AND at the
proposed (un-implemented) re-size from gear_fea.proposed_resize().

It also reports the implied finger-FEA margin at F_drive_safe vs at the 12 N
stress-probe load, assuming the von Mises stress field scales linearly with the
applied force (a clean approximation in the small-strain corotational regime
the harness operates in — the contact patch grows sub-linearly, so the linear-
scaling margin is itself a conservative lower bound on the true margin).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gear_fea
import kinematics_chain as kc


# --------------------------------------------------------------------------
# Operating points to anchor: the FEA stress-probe load and the published margins
# --------------------------------------------------------------------------
STRESS_PROBE_F_N = 12.0          # finger-FEA TARGET_GRIP
PUBLISHED_MARGIN_BAND = (5.7, 8.6)   # universal-finger battery min .. max at 12 N
TPU_STRENGTH_MPA = 25.0


def envelope_for_T_safe(T_safe_Nm, label):
    i_g = kc.chain_ratio()
    eta_lo, eta_hi = kc.efficiency_envelope()
    # MA across the contact face at the near-closed clamp pose
    # (kinematics_chain.contact_MA returns 1/mm). Use the practical mid (0.55)
    # and conservative tip (0.95) points -- the conservative end is the worst-
    # case sizing point; the mid is the engineering-typical point.
    MA_tip = kc.contact_MA(0.0, 0.95)
    MA_mid = kc.contact_MA(0.0, 0.55)

    # F = T_in * i_g * MA / 2 * eta  (T_in in N.mm; F in N)
    def F_of(T_Nm, MA, eta):
        return (T_Nm * 1000.0) * i_g * MA / 2.0 * eta

    corners = {
        "F_worst_tip_eta_lo": F_of(T_safe_Nm, MA_tip, eta_lo),
        "F_mid_eta_lo":       F_of(T_safe_Nm, MA_mid, eta_lo),
        "F_tip_eta_hi":       F_of(T_safe_Nm, MA_tip, eta_hi),
        "F_best_mid_eta_hi":  F_of(T_safe_Nm, MA_mid, eta_hi),
    }
    F_lo = corners["F_worst_tip_eta_lo"]
    F_hi = corners["F_best_mid_eta_hi"]
    # implied finger-FEA margin at the operating force, assuming linear stress
    # scaling with applied force (small-strain corotational regime, conservative
    # because the contact patch grows sub-linearly with load).
    # margin(F_op) = margin(F_probe) * F_probe / F_op
    margin_op_lo = PUBLISHED_MARGIN_BAND[0] * STRESS_PROBE_F_N / F_hi
    margin_op_hi = PUBLISHED_MARGIN_BAND[1] * STRESS_PROBE_F_N / F_lo
    return {
        "label": label,
        "T_safe_Nm": T_safe_Nm,
        "i_g": i_g,
        "MA_tip_per_mm": MA_tip,
        "MA_mid_per_mm": MA_mid,
        "eta_low": eta_lo,
        "eta_high": eta_hi,
        "F_per_finger_corners_N": {k: round(v, 3) for k, v in corners.items()},
        "F_per_finger_band_N": [round(F_lo, 3), round(F_hi, 3)],
        "stress_probe_F_N": STRESS_PROBE_F_N,
        "published_margin_at_probe": list(PUBLISHED_MARGIN_BAND),
        "implied_margin_at_operating_force":
            [round(margin_op_lo, 1), round(margin_op_hi, 1)],
        "operating_force_vs_probe_ratio":
            [round(F_lo / STRESS_PROBE_F_N, 3),
             round(F_hi / STRESS_PROBE_F_N, 3)],
        "note":
            "F is the per-FINGER clamp force at the contact face; T_in is "
            "input-shaft torque, gated by gear-tooth root-bending at T_safe. "
            "Stress-margin scaling is linear in F as a conservative lower "
            "bound (contact patch grows sub-linearly with load).",
    }


def run():
    gf = gear_fea.run()
    T_safe_shipped = gf["T_safe_input_Nm"]                         # = 0.034 N.m
    T_safe_proposed = gear_fea.proposed_resize()["T_safe_input_Nm_conservative"]
    shipped = envelope_for_T_safe(T_safe_shipped, "shipped (crown binds)")
    proposed = envelope_for_T_safe(T_safe_proposed, "proposed re-size (un-implemented)")
    return {
        "shipped": shipped,
        "proposed_resize": proposed,
        "interpretation": [
            "The finger-FEA TARGET_GRIP of 12 N is a STRESS-PROBE LOAD used to "
            "rank designs at a closure the FEA can reach in software. It is "
            "NOT the operating force the shipped drivetrain can safely deliver.",
            "Per the gear-tooth FEA, the SHIPPED crown gear binds at T_safe = "
            f"{T_safe_shipped:.3f} N.m. Through kinematics_chain, this maps to "
            f"a per-finger force band of {shipped['F_per_finger_band_N'][0]:.2f}"
            f"..{shipped['F_per_finger_band_N'][1]:.2f} N -- an order of "
            "magnitude below the 12 N stress-probe load.",
            "The implied finger-FEA vM margin at the operating force is "
            f"{shipped['implied_margin_at_operating_force'][0]:.0f}..{shipped['implied_margin_at_operating_force'][1]:.0f}x "
            "(conservative; small-strain linear scaling), i.e. the finger is "
            "WAY safer than the 5.7-8.6x at 12 N suggests, because the gear "
            "cap limits the actual stress reached.",
            "The headline finger-FEA conclusions are therefore: the DESIGN "
            "RANKING is valid at any sub-T_safe load (small-strain elastic "
            "regime preserves rank), the ABSOLUTE force in newtons is not "
            "delivered by the current drivetrain, and the absolute stress "
            "magnitudes (2.7 MPa peak vM) only apply if the drivetrain were "
            "re-sized to reach 12 N. The proposed gear re-size in "
            "gear_fea.proposed_resize() would deliver "
            f"{proposed['F_per_finger_band_N'][0]:.1f}..{proposed['F_per_finger_band_N'][1]:.1f} "
            "N per finger.",
        ],
    }


if __name__ == "__main__":
    out = run()
    s = out["shipped"]
    p = out["proposed_resize"]
    print("=== Drivetrain-deliverable per-finger force envelope ===")
    print(f"shipped:  T_safe = {s['T_safe_Nm']:.3f} N.m")
    print(f"          MA_mid = {s['MA_mid_per_mm']:.4f}/mm   "
          f"MA_tip = {s['MA_tip_per_mm']:.4f}/mm")
    print(f"          eta    = {s['eta_low']:.3f} .. {s['eta_high']:.3f}")
    print(f"          F_per_finger band = "
          f"{s['F_per_finger_band_N'][0]:.2f} .. "
          f"{s['F_per_finger_band_N'][1]:.2f} N   "
          "(vs 12 N stress-probe)")
    print(f"          implied finger-FEA margin at operating F: "
          f"{s['implied_margin_at_operating_force'][0]:.0f} .. "
          f"{s['implied_margin_at_operating_force'][1]:.0f}x  "
          "(vs 5.7-8.6x at 12 N)")
    print()
    print(f"proposed-resize (un-implemented): T_safe = {p['T_safe_Nm']:.3f} N.m")
    print(f"          F_per_finger band = "
          f"{p['F_per_finger_band_N'][0]:.2f} .. "
          f"{p['F_per_finger_band_N'][1]:.2f} N")
    print()
    print("Interpretation:")
    for line in out["interpretation"]:
        print(f"  - {line}")
    outpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "iterations", "_drivetrain_force_envelope.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"wrote {outpath}")

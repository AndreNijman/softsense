"""Drive-chain kinematics: input-shaft torque <-> fingertip clamp force.

This is the shared, reproducible core that REQUIREMENTS.md (Phase 1) and the
Phase-5 sims (torque_chain.py) both build on. It imports the *live* gripper.py
so every number tracks the real model -- nothing is hand-copied.

The chain (motor -> object), with all geometry read from gripper.py:

    motor / input shaft  (the D-coupler)
      |  crown/pinion stage      reduction i_g = CROWN_TEETH / PINION_TEETH
      v
    LEFT sector gear (crank A_L)
      |  spur mesh 1:1 to the RIGHT sector gear (crank A_R)
      v                          -> the LEFT gear therefore carries BOTH fingers
    four-bar (A->C crank, B->D follower, C->D coupler == finger)
      v
    fingertip / contact-face clamp force F

Quasi-static torque balance (lossless, then de-rated by efficiency eta):

    left-gear torque  T_L = T_motor * i_g
    by symmetry each finger's crank reaction is T_finger, and the 1:1 mesh
    makes the left gear supply both:        T_L = 2 * T_finger
    four-bar virtual work at a contact point P on the finger:
        F * dx_P = T_finger * dtheta_crank   ->   MA(P) = F / T_finger = dtheta/dx_P
    so:   F = T_motor * i_g * MA(P) / 2 * eta          (eta in (0,1])
    and:  T_motor = F / (i_g * MA(P) / 2 * eta)

MA(P) is the kinematic Jacobian |dtheta_crank / dx_P| at the contact point P,
computed numerically from gripper.py's four-bar solver. It is largest near the
finger base (short moment arm) and smallest at the tip -> the TIP is the
sizing-conservative point; the contact-face centre is the practical-use point.

This module RANKS / SIZES via mechanics; it does not claim a calibrated
absolute newton output of the built tool (friction, contact compliance and the
real grip texture are bounded, not measured). See MOTOR_MODEL.md.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gripper as g  # noqa: E402


# --------------------------------------------------------------------------
# fixed chain ratio
# --------------------------------------------------------------------------
def chain_ratio():
    """Crown/pinion reduction i_g = CROWN_TEETH/PINION_TEETH (motor -> crank)."""
    return g.CROWN_TEETH / g.PINION_TEETH


# --------------------------------------------------------------------------
# four-bar Jacobian -> mechanical advantage at a point on the finger
# --------------------------------------------------------------------------
_refR = g.solve_side_right(0.0)
_a0 = _refR["coupler_ang"]
_BL = g.FR_BLADE_LEN * g.FINGER_SCALE


def _finger_point_world(open_norm, y_frac, x_off):
    """World (x,y) of a point rigid with the RIGHT finger: y_frac up the blade
    from the C pin, x_off from the finger centreline (- = toward the gripper
    centre, the contact-face side). The finger rotates with the coupler CD."""
    R = g.solve_side_right(open_norm)
    d_ang = math.radians(R["coupler_ang"] - _a0)
    vx, vy = x_off, y_frac * _BL
    rx = vx * math.cos(d_ang) - vy * math.sin(d_ang)
    ry = vx * math.sin(d_ang) + vy * math.cos(d_ang)
    return (R["C"][0] + rx, R["C"][1] + ry)


def contact_MA(open_norm, y_frac=0.55, x_off=None):
    """Mechanical advantage MA = |dtheta_crank / dx_P|  [1/mm] at finger point P
    (closing/X direction), via central difference on the live four-bar."""
    if x_off is None:
        x_off = -g.FR_CONTACT_OFFSET  # right-finger contact face faces -X (centre)
    h = 1e-4
    o0, o1 = max(0.0, open_norm - h), min(1.0, open_norm + h)
    x0, _ = _finger_point_world(o0, y_frac, x_off)
    x1, _ = _finger_point_world(o1, y_frac, x_off)
    th0 = math.radians(g.crank_angle_deg(o0))
    th1 = math.radians(g.crank_angle_deg(o1))
    return 1.0 / abs((x1 - x0) / (th1 - th0))


def input_torque_for_force(F_tip, MA, eta=1.0, i_g=None):
    """Required input-shaft torque [N.m] for per-finger clamp force F_tip [N]."""
    if i_g is None:
        i_g = chain_ratio()
    T_motor_Nmm = F_tip / (i_g * MA / 2.0 * eta)
    return T_motor_Nmm / 1000.0


def force_for_input_torque(T_motor_Nm, MA, eta=1.0, i_g=None):
    """Per-finger clamp force [N] produced by input-shaft torque [N.m]."""
    if i_g is None:
        i_g = chain_ratio()
    return (T_motor_Nm * 1000.0) * i_g * MA / 2.0 * eta


# --------------------------------------------------------------------------
# travel / speed
# --------------------------------------------------------------------------
def input_travel_deg():
    """Input-shaft rotation for a full open<->close stroke [deg]."""
    return g.OPEN_TRAVEL * chain_ratio()


def input_speed_rpm(stroke_time_s):
    """Input-shaft speed [rpm] to do a full stroke in stroke_time_s seconds."""
    return (input_travel_deg() / 360.0) / (stroke_time_s / 60.0)


# --------------------------------------------------------------------------
# efficiency envelope (printed flooded drivetrain) -- ESTIMATE band
# --------------------------------------------------------------------------
# per-stage drive efficiency ranges (literature for plastic/printed gears +
# unlubricated plain bearings, de-rated for flooded plastic-on-plastic running):
STAGE_ETA = {
    "crown_pinion": (0.65, 0.85),   # printed straight-flank right-angle mesh, dry/flooded
    "spur_1to1":    (0.85, 0.95),   # printed spur mesh
    "fourbar":      (0.80, 0.90),   # two loaded plastic journal pivots per finger, flooded
    "input_journal": (0.90, 0.97),  # two flooded plastic journal bearings on the shaft
}


def efficiency_envelope():
    """(eta_low, eta_high) total drivetrain efficiency = product of stage bands."""
    lo = 1.0
    hi = 1.0
    for a, b in STAGE_ETA.values():
        lo *= a
        hi *= b
    return lo, hi


if __name__ == "__main__":
    import json

    i_g = chain_ratio()
    eta_lo, eta_hi = efficiency_envelope()
    travel = input_travel_deg()

    print(f"chain ratio i_g (crown/pinion) = {g.CROWN_TEETH}/{g.PINION_TEETH} = {i_g:.4f}:1")
    print(f"sector gears 1:1 (R_GEAR={g.R_GEAR}) -> left gear carries both fingers")
    print(f"efficiency envelope eta = {eta_lo:.3f} .. {eta_hi:.3f}")
    print(f"input travel (full open<->close) = {travel:.1f} deg "
          f"(crank {g.OPEN_TRAVEL} deg x {i_g:.3f})")
    print()

    # MA along the contact face (y_frac), at the near-closed clamp pose
    print("MA along the contact face at open=0.0 (clamp pose):")
    pts = {}
    for name, yf in (("base_0.15", 0.15), ("mid_0.55", 0.55),
                     ("tip_face_0.95", 0.95), ("tip_centreline_1.0", 1.0)):
        xo = 0.0 if name.startswith("tip_centreline") else -g.FR_CONTACT_OFFSET
        ma = contact_MA(0.0, yf, xo)
        pts[name] = ma
        print(f"  {name:20s} MA={ma:.5f}/mm")
    print()

    # torque band: force range x efficiency envelope, at the two reference points
    F_RANGE = (8.0, 12.0, 15.0)        # working clamp-force band (FEA anchor = 12 N)
    MA_tip = pts["tip_centreline_1.0"]
    MA_mid = pts["mid_0.55"]
    print("Required input-shaft torque [N.m]  (mid-face practical .. tip conservative,"
          " across eta envelope):")
    table = {}
    for F in F_RANGE:
        t_mid_hi = input_torque_for_force(F, MA_mid, eta_hi)  # best case (mid face, high eta)
        t_tip_lo = input_torque_for_force(F, MA_tip, eta_lo)  # worst case (tip, low eta)
        t_ideal_tip = input_torque_for_force(F, MA_tip, 1.0)
        table[f"F{int(F)}"] = dict(mid_eta_hi=t_mid_hi, tip_eta_lo=t_tip_lo,
                                   ideal_tip=t_ideal_tip)
        print(f"  F_tip={F:4.1f} N : {t_mid_hi:.3f} .. {t_tip_lo:.3f}  "
              f"(ideal@tip {t_ideal_tip:.3f})")
    print()

    for t in (0.5, 1.0, 2.0):
        print(f"  full stroke in {t:.1f} s -> input speed {input_speed_rpm(t):5.1f} rpm "
              f"({input_travel_deg()/t:5.1f} deg/s)")

    out = dict(
        i_g=i_g, R_GEAR=g.R_GEAR, CROWN_TEETH=g.CROWN_TEETH, PINION_TEETH=g.PINION_TEETH,
        eta_low=eta_lo, eta_high=eta_hi, stage_eta=STAGE_ETA,
        input_travel_deg=travel, crank_travel_deg=g.OPEN_TRAVEL,
        MA=pts, force_range_N=list(F_RANGE), torque_band_Nm=table,
        speed_rpm={f"{t}s": input_speed_rpm(t) for t in (0.5, 1.0, 2.0)},
        coupler=dict(R=g.SHAFT_COUPLER_R, dflat=g.SHAFT_DFLAT, len=g.SHAFT_COUPLER_LEN),
    )
    itdir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "iterations")
    os.makedirs(itdir, exist_ok=True)
    with open(os.path.join(itdir, "_requirements.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nwrote {os.path.join(itdir, '_requirements.json')}")

"""Crown-gear face-tooth FEA across MULTIPLE RADIAL STATIONS.

The shipped `gear_fea.py` treats the crown gear as a 2D plane-stress straight-
flank spur tooth at a SINGLE radial station (the pitch radius CROWN_RC). A real
crown/face gear is a 3D problem -- the contact line sweeps radially across the
tooth length under load, the tangential tooth thickness s_root(r) is r-
dependent (smaller at the inner radius, larger at the outer), and the
worst-case root stress is at the inner radius where s_root is smallest.

This script computes the per-station 2D plane-stress root stress from the same
machinery as `gear_fea.tooth_root_stress` at multiple radial stations
{r_in, r_mid = CROWN_RC, r_out}, plus a uniformly-distributed-line-load
analytic check (3D thin-plate Kirchhoff style: w = F_t / (r_out - r_in)). The
binding stress comes from the inner-radius slice; T_safe(crown) is recomputed
from that bound.

This is STILL not a real 3D FEA of the crown -- the base-disk bending
compliance and the moving contact line are not captured. The honest claim is:
this is a tighter upper-bound on T_safe than the single-station 2D FEA in
`gear_fea.py`, and the only real answer remains the bench measurement in
`motor/BENCH_TEST.md`.
"""
import math
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gripper as g  # noqa: E402
import gear_fea as gf  # noqa: E402

SIGMA_ALLOW = gf.SIGMA_ALLOW
ITER = gf.ITER
F_REF = 10.0          # N reference tooth force (linear-elastic, scale to allowable)


def crown_stress_at_radius(r, land_frac=0.5, b_eff=None):
    """Plane-stress root stress of a crown FACE tooth at radial station r.

    Tangential tooth thickness at radius r:
        s_root(r) = (2*pi/CROWN_TEETH) * land_frac * r
    Face height h = CROWN_FACE_H. Tangential tooth force F_REF applied at the
    tip (worst case). Loaded face width b_eff for the radial-station 2D FEA is
    the same b_eff that gear_fea.run() uses (the radial band 2*CROWN_TOOTH_H
    capped by the mating face PINION_T)."""
    if b_eff is None:
        b_eff = min(g.PINION_T, 2.0 * g.CROWN_TOOTH_H)
    step = 2 * math.pi / g.CROWN_TEETH
    s_root = step * land_frac * r
    h = g.CROWN_FACE_H
    sigma = gf.tooth_root_stress(s_root, h, b_eff, F_REF)
    return dict(r=r, s_root=s_root, h=h, b_eff=b_eff,
                sigma_at_Fref=sigma)


def integrated_thin_plate_root_stress(land_frac=0.5):
    """Crown tooth as a thin plate of variable tangential thickness clamped on
    its base edge (the disk), tangentially loaded at its top edge (the mesh
    contact). The load is uniformly distributed in r over the tooth's radial
    extent [r_in, r_out] = [CROWN_RC - CROWN_TOOTH_H, CROWN_RC + CROWN_TOOTH_H].

    Conservative analytic bound: take the worst-case radial station (smallest
    s_root, i.e. r = r_in), apply ALL of F_REF as the resultant tooth tangential
    force there (uniform-w * (r_out - r_in) integrated), and compute
    sigma = 6 * (F_REF) * h / (b_local * s_root**2)
    with b_local = (r_out - r_in) — the loaded radial band — i.e. the same b_eff
    as the gear_fea baseline but the s_root is the inner-station value.

    Returns the analytic Lewis-form-factor stress with s_root = s_in, plus the
    fea_check at the same s_root via gear_fea.tooth_root_stress."""
    r_in = g.CROWN_RC - g.CROWN_TOOTH_H
    r_out = g.CROWN_RC + g.CROWN_TOOTH_H
    step = 2 * math.pi / g.CROWN_TEETH
    s_in = step * land_frac * r_in
    h = g.CROWN_FACE_H
    b_eff = min(g.PINION_T, r_out - r_in)
    # analytic Lewis-style bound (rectangular cantilever, tip line-load):
    # sigma = 6 * F * h / (b * s^2). Conservative because it ignores fillet,
    # ignores base-disk compliance, ignores load-sharing with adjacent teeth.
    sigma_analytic = 6.0 * F_REF * h / (b_eff * s_in * s_in)
    sigma_fea = gf.tooth_root_stress(s_in, h, b_eff, F_REF)
    return dict(r_in=r_in, r_out=r_out, s_in=s_in, h=h, b_eff=b_eff,
                sigma_inner_Lewis_MPa=sigma_analytic,
                sigma_inner_2DFEA_MPa=sigma_fea)


def run():
    # baseline single-station (the gear_fea.py headline)
    base = gf.run()
    T_shipped_single = base["gears"]["crown"]["T_safe_input_Nm"]
    sigma_shipped_at_10N = base["gears"]["crown"]["sigma_ref_at_10N"]

    # radial-station 2D FEA: 5 stations across the crown's radial extent
    r_in = g.CROWN_RC - g.CROWN_TOOTH_H
    r_out = g.CROWN_RC + g.CROWN_TOOTH_H
    stations = []
    for k in range(5):
        r = r_in + (r_out - r_in) * k / 4.0
        stations.append(crown_stress_at_radius(r))
    # binding (worst) station
    worst = max(stations, key=lambda s: s["sigma_at_Fref"])
    F_allow_worst = SIGMA_ALLOW / worst["sigma_at_Fref"] * F_REF
    # crown contact-force lever = PINION_RP (same as gear_fea.py)
    T_safe_radial = F_allow_worst * g.PINION_RP / 1000.0

    # thin-plate inner-edge bound (analytic + FEA at inner radius)
    plate = integrated_thin_plate_root_stress()
    F_allow_plate = SIGMA_ALLOW / plate["sigma_inner_2DFEA_MPa"] * F_REF
    T_safe_plate = F_allow_plate * g.PINION_RP / 1000.0

    return dict(
        baseline_single_station=dict(
            sigma_at_10N_MPa=sigma_shipped_at_10N,
            T_safe_Nm=T_shipped_single,
            s_root_mm=base["gears"]["crown"]["s_root"]),
        radial_stations=stations,
        worst_radial_station=dict(
            r=worst["r"], s_root=worst["s_root"],
            sigma_at_10N_MPa=worst["sigma_at_Fref"],
            F_allow_tooth_N=F_allow_worst,
            T_safe_Nm=round(T_safe_radial, 4)),
        thin_plate_inner_edge=dict(
            **plate,
            F_allow_tooth_N=F_allow_plate,
            T_safe_Nm=round(T_safe_plate, 4)),
        interpretation=[
            "The crown is a 3D face-gear tooth. Tangential tooth thickness "
            "s_root grows with radius. The SHIPPED gear_fea.py single-station "
            "model evaluates at r=CROWN_RC (mid-station); a multi-station "
            "evaluation shows the INNER-edge slice (r=CROWN_RC-CROWN_TOOTH_H) "
            "is more highly stressed -- s_root there is smaller, so for the "
            "same tangential tooth force the root stress rises.",
            "Per-station 2D plane-stress FEA across 5 radial stations: the "
            f"worst is at r={worst['r']:.2f} mm with sigma@10N = "
            f"{worst['sigma_at_Fref']:.2f} MPa (vs the single-station "
            f"baseline of {sigma_shipped_at_10N:.2f} MPa at r=CROWN_RC). "
            f"Recomputed T_safe(crown, radial) = {T_safe_radial:.3f} N.m, "
            f"vs the baseline {T_shipped_single:.3f} N.m.",
            "An analytic 'thin-plate inner-edge' bound (Lewis-style cantilever "
            "at s_root = s_in, F applied at the tooth tip with the full mesh-"
            f"band b_eff = {plate['b_eff']:.2f} mm) gives sigma = "
            f"{plate['sigma_inner_Lewis_MPa']:.1f} MPa at 10 N reference and "
            f"T_safe = {T_safe_plate:.3f} N.m.",
            "WHAT IS STILL MISSING: the base-disk bending compliance, the "
            "moving contact line under rotation, the tangential+radial+axial "
            "load decomposition of a real crown mesh, and the printed straight-"
            "flank-vs-involute edge-loading effect (PA12-GF face teeth in a "
            "real mesh will gall and edge-load, not roll cleanly). The 2D FEA "
            "here is a tighter upper bound, not a validated ceiling. The only "
            "real answer is the printed-coupon torque-to-failure measurement "
            "in motor/BENCH_TEST.md.",
        ],
    )


if __name__ == "__main__":
    out = run()
    base = out["baseline_single_station"]
    worst = out["worst_radial_station"]
    plate = out["thin_plate_inner_edge"]
    print("=== Crown-gear FACE-tooth FEA across radial stations ===")
    print(f"baseline (gear_fea.py, single station r=CROWN_RC):")
    print(f"  s_root = {base['s_root_mm']:.2f} mm, "
          f"sigma@10N = {base['sigma_at_10N_MPa']:.2f} MPa  -> "
          f"T_safe = {base['T_safe_Nm']:.4f} N.m")
    print()
    print("radial 5-station 2D plane-stress:")
    for s in out["radial_stations"]:
        print(f"  r = {s['r']:5.2f} mm   s_root = {s['s_root']:.3f} mm   "
              f"sigma@10N = {s['sigma_at_Fref']:6.2f} MPa")
    print(f"  -> WORST station r = {worst['r']:.2f} mm   "
          f"T_safe = {worst['T_safe_Nm']:.4f} N.m")
    print()
    print("thin-plate inner-edge bound (Lewis-style):")
    print(f"  s_in = {plate['s_in']:.3f} mm   "
          f"sigma_Lewis@10N = {plate['sigma_inner_Lewis_MPa']:.1f} MPa   "
          f"sigma_2DFEA@10N = {plate['sigma_inner_2DFEA_MPa']:.1f} MPa")
    print(f"  -> T_safe (FEA at s_in) = {plate['T_safe_Nm']:.4f} N.m")
    print()
    for line in out["interpretation"]:
        print(f"  - {line}")
    outpath = os.path.join(ITER, "_gear_fea_radial.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\nwrote {outpath}")

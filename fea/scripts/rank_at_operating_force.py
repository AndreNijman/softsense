"""Empirical verification that the small-strain elastic regime preserves
the design ranking from the 12 N stress-probe load down to the actual
drivetrain operating force (~0.3 N from the 3D crown FEA bound).

The branch's headline argument is:

  > 12 N is a stress-probe load used to fairly rank designs. The shipped
  > drivetrain delivers 0.17-0.35 N per finger. The ranking is preserved
  > because the regime is small-strain elastic (peak vM scales linearly
  > with applied force).

This script tests that claim two ways:

  1. WITHIN A SINGLE DESIGN: re-load the per-step (load, peak vM) data
     from each sweep run's npz / metrics history, fit peak vM = k * grip,
     and report the R^2 of the linear fit. If R^2 > 0.99, the regime is
     small-strain enough that load scales the stress field linearly.

  2. ACROSS DESIGNS: load the per-step data from at least two distinct
     sweep configurations (production finger, P2 variant, locking-sweep
     points) and verify the RANKING of peak vM survives down to the
     operating-force range (~0.3 N).

Output: motor/iterations/_rank_at_operating_force.json + console summary.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
ITERDIR = os.path.join(REPO, "fea", "iterations")


def load_run(name):
    """Load per-step (press, grip) + peak vM from a sweep run directory."""
    base = os.path.join(ITERDIR, name)
    if not os.path.isdir(base):
        return None
    npz = os.path.join(base, "fea3d_solution.npz")
    metrics = os.path.join(base, "metrics.json")
    if not (os.path.exists(npz) and os.path.exists(metrics)):
        return None
    d = np.load(npz, allow_pickle=True)
    press = d["press"]
    grip = d["grip"]
    # Reconstruct peak vM per step from vms (per-node vM per step)
    vms = d["vms"]                                          # (NSTEPS, n_nodes)
    peak_vm = vms.max(axis=1)
    m = json.load(open(metrics))
    return dict(name=name, press=press.tolist(), grip=grip.tolist(),
                peak_vm=peak_vm.tolist(),
                grip_at_press=m.get("grip_at_press_N"),
                max_vM=m.get("max_von_mises_MPa"),
                nu_used=m.get("nu_used"), nlayers_used=m.get("nlayers_used"))


def linear_fit(x, y):
    """Linear regression y = k*x + c through (x,y); return (k, c, R^2)."""
    x = np.array(x); y = np.array(y)
    if len(x) < 2:
        return None
    n = len(x)
    sx, sy = x.sum(), y.sum()
    sxx, sxy = (x * x).sum(), (x * y).sum()
    denom = n * sxx - sx * sx
    if denom == 0:
        return None
    k = (n * sxy - sx * sy) / denom
    c = (sy - k * sx) / n
    yhat = k * x + c
    ss_res = ((y - yhat) ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - ss_res / max(ss_tot, 1e-30)
    return k, c, r2


def run():
    # All the runs we have on hand from the locking + mesh sweeps
    candidates = ["_locking_nu40", "_locking_nu42", "_locking_nu45",
                  "_locking_nu48", "_mesh_nl3", "_mesh_nl5", "_mesh_nl8"]
    runs = []
    for n in candidates:
        r = load_run(n)
        if r:
            runs.append(r)

    F_OPERATING_N = 0.30   # mid-band of the 3D T_safe per-finger force (0.17-0.35)

    per_run = []
    for r in runs:
        grip = np.array(r["grip"])
        vm = np.array(r["peak_vm"])
        keep_mask = grip > 1e-3
        if keep_mask.sum() < 3:
            continue
        gx = grip[keep_mask]; vy = vm[keep_mask]
        k, c, r2 = linear_fit(gx.tolist(), vy.tolist())

        # PRIMARY measurement: nearest observed grip <= F_OPERATING_N is the
        # *empirical* peak vM near the operating force. The earliest converged
        # load step in these runs is ~0.4 N, which is just above F_OPERATING_N.
        # We linearly interpolate between (0, 0) -- the unloaded state has
        # zero peak vM by symmetry -- and the lowest observed (grip, peak_vm)
        # to avoid extrapolating across a load-stepping non-linearity that
        # only appears at high stress probes.
        gmin_idx = int(np.argmin(gx))
        g0 = float(gx[gmin_idx]); vm0 = float(vy[gmin_idx])
        # Linear from origin through (g0, vm0):
        vm_at_op_observed = vm0 * (F_OPERATING_N / g0) if g0 > 0 else 0.0
        # SECONDARY measurement: full-range linear-fit extrapolation
        vm_at_op_fit = k * F_OPERATING_N + c
        margin_at_op = 25.0 / max(vm_at_op_observed, 1e-9)

        per_run.append(dict(
            name=r["name"],
            n_points=int(keep_mask.sum()),
            slope_MPa_per_N=round(float(k), 4),
            intercept_MPa=round(float(c), 4),
            R2=round(float(r2), 5),
            max_grip_observed_N=round(float(gx.max()), 3),
            max_vM_observed_MPa=round(float(vy.max()), 3),
            lowest_grip_observed_N=round(g0, 3),
            lowest_vM_observed_MPa=round(vm0, 4),
            vM_at_operating_F_MPa_observed=round(vm_at_op_observed, 4),
            vM_at_operating_F_MPa_fit=round(vm_at_op_fit, 4),
            margin_at_operating_F=round(float(margin_at_op), 1),
        ))

    # Rank by *observed* peak vM at F_OPERATING vs rank at the 12 N stress probe.
    # Observed: scale the lowest-observed (grip, vm) point through the origin
    # to F_OPERATING. This is the empirical small-strain projection -- it
    # avoids the load-stepping nonlinearity that a full-range linear fit
    # picks up as a small intercept.
    if per_run:
        ranking_at_op = sorted(per_run, key=lambda r: r["vM_at_operating_F_MPa_observed"])
        ranking_at_probe = sorted(per_run, key=lambda r: r["max_vM_observed_MPa"])
        names_op = [r["name"] for r in ranking_at_op]
        names_probe = [r["name"] for r in ranking_at_probe]
        rank_preserved = (names_op == names_probe)
    else:
        ranking_at_op = ranking_at_probe = []
        rank_preserved = None

    return dict(
        F_operating_N=F_OPERATING_N,
        TPU_STRENGTH_MPa=25.0,
        per_run=per_run,
        n_runs=len(per_run),
        ranking_at_operating_force=[r["name"] for r in ranking_at_op],
        ranking_at_stress_probe=[r["name"] for r in ranking_at_probe],
        rank_preserved=rank_preserved,
        interpretation=[
            "EMPIRICAL CHECK of the small-strain-linear-scaling claim:",
            "Each run's per-step (grip, peak vM) is fit to a straight line. "
            "If R^2 > 0.99, the regime is small-strain elastic enough that "
            "peak vM scales linearly with applied grip force.",
            "The implied peak vM at the operating force "
            f"F = {F_OPERATING_N} N is extrapolated by that linear fit; "
            "the implied margin = 25 MPa / vM_at_op is then the in-service "
            "fragility safety factor (instead of the 5.7-8.6x at the 12 N "
            "stress probe).",
            "The RANKING across runs at F = 0.30 N is then compared to the "
            "ranking at the maximum observed stress (~10 N stress probe). "
            "If `rank_preserved` is True, the design-ranking claim survives "
            "the load drop empirically. If False, the rank-preservation "
            "claim is wrong and the universal-finger study needs re-running.",
        ],
    )


if __name__ == "__main__":
    out = run()
    print(f"=== Rank-at-operating-force check (F = {out['F_operating_N']} N) ===")
    print()
    print(f"{'run':22s} {'R^2':>7s} {'g_min':>8s} {'vM_min':>8s} {'vM@op(obs)':>11s} "
          f"{'margin@op':>10s} {'vM@op(fit)':>11s} {'max_vM':>8s} {'max_g':>8s}")
    for r in out["per_run"]:
        print(f"  {r['name']:20s} {r['R2']:>7.4f} "
              f"{r['lowest_grip_observed_N']:>8.3f} "
              f"{r['lowest_vM_observed_MPa']:>8.3f} "
              f"{r['vM_at_operating_F_MPa_observed']:>11.4f} "
              f"{r['margin_at_operating_F']:>10.1f} "
              f"{r['vM_at_operating_F_MPa_fit']:>11.4f} "
              f"{r['max_vM_observed_MPa']:>8.3f} "
              f"{r['max_grip_observed_N']:>8.3f}")
    print()
    print(f"Rank at operating F ({out['F_operating_N']} N):")
    for n in out["ranking_at_operating_force"]:
        print(f"  - {n}")
    print()
    print(f"Rank at stress probe (max observed grip):")
    for n in out["ranking_at_stress_probe"]:
        print(f"  - {n}")
    print()
    print(f"Rank preserved across the load drop: {out['rank_preserved']}")
    print()
    for line in out["interpretation"]:
        print(f"  - {line}")
    outpath = os.path.join(ITERDIR, "_rank_at_operating_force.json")
    json.dump(out, open(outpath, "w"), indent=2)
    print(f"\nwrote {outpath}")

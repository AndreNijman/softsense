"""Aggregate the locking-sweep + mesh-convergence-sweep metrics into one
summary JSON, plus a console table. Run AFTER all `_locking_nu*` and
`_mesh_nl*` runs have produced metrics.json.

Usage: python fea/scripts/aggregate_sweeps.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
ITERDIR = os.path.join(REPO, "fea", "iterations")


def load_metrics(name):
    p = os.path.join(ITERDIR, name, "metrics.json")
    if not os.path.exists(p):
        return None
    return json.load(open(p))


def aggregate():
    locking = []
    for nu in (0.40, 0.42, 0.45, 0.48):
        name = f"_locking_nu{int(nu*100):02d}"
        m = load_metrics(name)
        locking.append(dict(name=name, nu=nu, metrics=m))
    mesh = []
    for nl in (3, 5, 8):
        name = f"_mesh_nl{nl}"
        m = load_metrics(name)
        mesh.append(dict(name=name, nlayers=nl, metrics=m))
    return dict(locking=locking, mesh=mesh)


def print_summary(agg):
    print("=" * 72)
    print("LOCKING SWEEP  (shipped finger, NLAYERS=3, ν varied)")
    print("-" * 72)
    print(f"  {'ν':>5}  {'grip_N':>10}  {'peak_vM':>10}  {'margin':>8}  "
          f"{'converged':>11}  {'max_it':>6}")
    base_grip = None
    base_vm = None
    for r in agg["locking"]:
        m = r["metrics"]
        if m is None:
            print(f"  {r['nu']:>5.2f}  (no metrics yet)")
            continue
        g = m.get("grip_at_press_N", 0.0)
        vm = m.get("max_von_mises_MPa", 0.0)
        mg = m.get("margin_x", 0.0)
        dc = m.get("did_converge_all_steps")
        mi = m.get("newton_iters_max_used", 0)
        if r["nu"] == 0.42:
            base_grip = g; base_vm = vm
        print(f"  {r['nu']:>5.2f}  {g:>10.2f}  {vm:>10.3f}  {mg:>8.2f}  "
              f"{str(dc):>11}  {mi:>6}")
    if base_grip:
        print()
        print(f"  baseline ν=0.42:  grip = {base_grip:.2f} N   vM = {base_vm:.3f} MPa")
        for r in agg["locking"]:
            m = r["metrics"]
            if m is None or r["nu"] == 0.42:
                continue
            g = m.get("grip_at_press_N", 0.0)
            vm = m.get("max_von_mises_MPa", 0.0)
            dg = (g - base_grip) / base_grip * 100
            dv = (vm - base_vm) / base_vm * 100
            print(f"  ν={r['nu']:.2f}:   Δgrip = {dg:+.1f}%   "
                  f"Δpeak_vM = {dv:+.1f}%")

    print()
    print("=" * 72)
    print("MESH-CONVERGENCE SWEEP  (shipped finger, ν=0.42, NLAYERS varied)")
    print("-" * 72)
    print(f"  {'NLAYERS':>7}  {'grip_N':>10}  {'peak_vM':>10}  {'margin':>8}  "
          f"{'converged':>11}  {'max_it':>6}")
    base_grip3 = None
    base_vm3 = None
    for r in agg["mesh"]:
        m = r["metrics"]
        if m is None:
            print(f"  {r['nlayers']:>7d}  (no metrics yet)")
            continue
        g = m.get("grip_at_press_N", 0.0)
        vm = m.get("max_von_mises_MPa", 0.0)
        mg = m.get("margin_x", 0.0)
        dc = m.get("did_converge_all_steps")
        mi = m.get("newton_iters_max_used", 0)
        if r["nlayers"] == 3:
            base_grip3 = g; base_vm3 = vm
        print(f"  {r['nlayers']:>7d}  {g:>10.2f}  {vm:>10.3f}  {mg:>8.2f}  "
              f"{str(dc):>11}  {mi:>6}")
    if base_grip3:
        print()
        print(f"  baseline NLAYERS=3:  grip = {base_grip3:.2f} N   vM = {base_vm3:.3f} MPa")
        for r in agg["mesh"]:
            m = r["metrics"]
            if m is None or r["nlayers"] == 3:
                continue
            g = m.get("grip_at_press_N", 0.0)
            vm = m.get("max_von_mises_MPa", 0.0)
            dg = (g - base_grip3) / base_grip3 * 100
            dv = (vm - base_vm3) / base_vm3 * 100
            print(f"  NLAYERS={r['nlayers']}:   Δgrip = {dg:+.1f}%   "
                  f"Δpeak_vM = {dv:+.1f}%")


def main():
    agg = aggregate()
    print_summary(agg)
    outpath = os.path.join(ITERDIR, "_sweep_summary.json")
    json.dump(agg, open(outpath, "w"), indent=2)
    print(f"\nwrote {outpath}")


if __name__ == "__main__":
    main()

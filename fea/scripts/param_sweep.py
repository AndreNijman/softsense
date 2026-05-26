"""Re-run iter_harness.py at non-default (nu, NLAYERS, E_TPU, NSTEPS) values
WITHOUT touching the validated production solver.

Two studies live here:
  * locking_sweep   -- nu in {0.40, 0.42, 0.45, 0.48} at fixed NLAYERS=3.
                       Diagnoses linear-tet volumetric locking on the shipped
                       finger geometry; checks whether the truss-vs-flexure
                       ranking is preserved across nu (FEA.md A.12 / TESTING
                       A.12 claim).
  * mesh_convergence -- NLAYERS in {3, 5, 8} at fixed nu=0.42.
                        Tests whether peak_vm and grip are mesh-converged at
                        the shipped NLAYERS=3 (linear tets in bending; the
                        critical review's #16).

Usage:
  python param_sweep.py locking
  python param_sweep.py mesh_convergence
  python param_sweep.py one <name> NU=0.45 NLAYERS=5  ...      # arbitrary

It calls iter_harness.main() once per parameter point, with the env vars
(GRIPPER_NU, GRIPPER_NLAYERS, GRIPPER_NSTEPS_OVERRIDE, ...) set so the
production code path runs identically. The harness's metrics.json is the
per-point output; this script aggregates them into a summary JSON +
console table.

For speed, set GRIPPER_NSTEPS_OVERRIDE=12 (default for sweeps) to use 12 load
steps instead of the production 24 -- the comparative shifts across nu /
NLAYERS converge well before 24 steps and the relative numbers are what we
want here. Set to 24 for production-fidelity runs.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
ITERDIR = os.path.join(REPO, "fea", "iterations")


def run_one(name, env_overrides, params_json='{}'):
    env = os.environ.copy()
    env.update(env_overrides)
    env.setdefault("GRIPPER_REPO", REPO)
    env.setdefault("PYTHONUNBUFFERED", "1")
    cmd = [sys.executable, "-u",
           os.path.join(HERE, "iter_harness.py"),
           name, params_json]
    t0 = time.time()
    log = os.path.join(ITERDIR, name, "sweep_log.txt")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    with open(log, "w") as fh:
        fh.write(f"# env overrides: {env_overrides}\n")
        fh.flush()
        proc = subprocess.run(cmd, env=env, stdout=fh, stderr=subprocess.STDOUT)
    dt = time.time() - t0
    metrics_path = os.path.join(ITERDIR, name, "metrics.json")
    m = None
    if os.path.exists(metrics_path):
        m = json.load(open(metrics_path))
    return dict(name=name, env=env_overrides, runtime_s=round(dt, 1),
                exit_code=proc.returncode, metrics=m, log=log)


def locking_sweep(nsteps_override=None):
    """nu in {0.40, 0.42, 0.45, 0.48} at fixed NLAYERS=3, shipped geometry."""
    results = []
    nu_list = [0.40, 0.42, 0.45, 0.48]
    for nu in nu_list:
        name = f"_locking_nu{int(nu*100):02d}"
        env = {"GRIPPER_NU": str(nu)}
        if nsteps_override:
            env["GRIPPER_NSTEPS_OVERRIDE"] = str(nsteps_override)
        results.append(run_one(name, env))
    summary = dict(
        sweep="locking",
        nu_values=nu_list,
        nsteps=nsteps_override or 24,
        results=[dict(name=r["name"], nu=float(r["env"]["GRIPPER_NU"]),
                      runtime_s=r["runtime_s"], exit_code=r["exit_code"],
                      grip_at_press_N=r["metrics"].get("grip_at_press_N")
                      if r["metrics"] else None,
                      max_von_mises_MPa=r["metrics"].get("max_von_mises_MPa")
                      if r["metrics"] else None,
                      margin_x=r["metrics"].get("margin_x")
                      if r["metrics"] else None,
                      did_converge_all_steps=r["metrics"].get("did_converge_all_steps")
                      if r["metrics"] else None,
                      newton_iters_max_used=r["metrics"].get("newton_iters_max_used")
                      if r["metrics"] else None)
                 for r in results],
    )
    return summary


def mesh_convergence(nsteps_override=None):
    """NLAYERS in {3, 5, 8} at fixed nu=0.42, shipped geometry."""
    results = []
    nl_list = [3, 5, 8]
    for nl in nl_list:
        name = f"_mesh_nl{nl}"
        env = {"GRIPPER_NLAYERS": str(nl)}
        if nsteps_override:
            env["GRIPPER_NSTEPS_OVERRIDE"] = str(nsteps_override)
        results.append(run_one(name, env))
    summary = dict(
        sweep="mesh_convergence",
        nlayers_values=nl_list,
        nsteps=nsteps_override or 24,
        results=[dict(name=r["name"], nlayers=int(r["env"]["GRIPPER_NLAYERS"]),
                      runtime_s=r["runtime_s"], exit_code=r["exit_code"],
                      grip_at_press_N=r["metrics"].get("grip_at_press_N")
                      if r["metrics"] else None,
                      max_von_mises_MPa=r["metrics"].get("max_von_mises_MPa")
                      if r["metrics"] else None,
                      margin_x=r["metrics"].get("margin_x")
                      if r["metrics"] else None,
                      did_converge_all_steps=r["metrics"].get("did_converge_all_steps")
                      if r["metrics"] else None,
                      newton_iters_max_used=r["metrics"].get("newton_iters_max_used")
                      if r["metrics"] else None)
                 for r in results],
    )
    return summary


def print_locking_summary(summary):
    print("=" * 64)
    print("Volumetric-locking sweep on the shipped finger geometry")
    print(f"  (NSTEPS = {summary['nsteps']}, NLAYERS = 3, GRIPPER_NSTEPS_OVERRIDE used for speed)")
    print("-" * 64)
    print(f"  {'nu':>5}  {'grip_N':>10}  {'peak_vM_MPa':>12}  {'margin':>8}  "
          f"{'converged':>11}  {'max_iters':>9}")
    for r in summary["results"]:
        print(f"  {r['nu']:>5.2f}  {r['grip_at_press_N'] or 0:>10.2f}  "
              f"{r['max_von_mises_MPa'] or 0:>12.3f}  {r['margin_x'] or 0:>8.2f}  "
              f"{str(r['did_converge_all_steps']):>11}  {r['newton_iters_max_used'] or 0:>9}")


def print_mesh_summary(summary):
    print("=" * 64)
    print("Mesh-convergence sweep on the shipped finger geometry")
    print(f"  (NSTEPS = {summary['nsteps']}, nu = 0.42)")
    print("-" * 64)
    print(f"  {'NLAYERS':>7}  {'grip_N':>10}  {'peak_vM_MPa':>12}  {'margin':>8}  "
          f"{'converged':>11}  {'max_iters':>9}")
    for r in summary["results"]:
        print(f"  {r['nlayers']:>7d}  {r['grip_at_press_N'] or 0:>10.2f}  "
              f"{r['max_von_mises_MPa'] or 0:>12.3f}  {r['margin_x'] or 0:>8.2f}  "
              f"{str(r['did_converge_all_steps']):>11}  {r['newton_iters_max_used'] or 0:>9}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: param_sweep.py {locking,mesh_convergence,one} [args...]")
        sys.exit(2)
    nsteps = int(os.environ.get("GRIPPER_NSTEPS_OVERRIDE", "12"))
    cmd = sys.argv[1]
    if cmd == "locking":
        summary = locking_sweep(nsteps_override=nsteps)
        outpath = os.path.join(ITERDIR, "_locking_sweep.json")
        json.dump(summary, open(outpath, "w"), indent=2)
        print_locking_summary(summary)
        print(f"\nwrote {outpath}")
    elif cmd == "mesh_convergence":
        summary = mesh_convergence(nsteps_override=nsteps)
        outpath = os.path.join(ITERDIR, "_mesh_convergence.json")
        json.dump(summary, open(outpath, "w"), indent=2)
        print_mesh_summary(summary)
        print(f"\nwrote {outpath}")
    elif cmd == "one":
        name = sys.argv[2]
        env = dict(kv.split("=", 1) for kv in sys.argv[3:])
        r = run_one(name, env)
        print(json.dumps(r, indent=2))
    else:
        print(f"unknown command: {cmd}")
        sys.exit(2)

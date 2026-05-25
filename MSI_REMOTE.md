# MSI as a remote FEA / render node

The MSI laptop is provisioned to run the heavy FEA + render pipeline off the main
machine. Verified working: a screen-battery FEA on the MSI reproduces the local
result **exactly** (`SCORE 0.6452`, deterministic).

## Connection
- `ssh andremsi` → 192.168.1.160, user `andre`, key `~/.ssh/id_ed25519`.
- The MSI's SSH default shell is **cmd.exe** (not PowerShell): `%VAR%` expands, `&&`
  chains, use **absolute Windows paths**, redirect with `>nul`.

## Environment (already installed)
- venv: **`C:\Users\andre\cad-venv`** — python `C:\Users\andre\cad-venv\Scripts\python.exe`
- packages: build123d 0.10.0, cadquery-ocp 7.8.1, gmsh 4.15.2, numpy 2.4, scipy 1.17,
  matplotlib 3.10, vtk 9.3 (full FEA + render stack; same build123d version as local).
- repo clone: **`C:\Users\andre\gripper-cad`** (cloned from GitHub `master`).

## Run an FEA on the MSI
```bash
ssh andremsi "cd /d C:\Users\andre\gripper-cad && set PYTHONPATH=C:\Users\andre\gripper-cad && C:\Users\andre\cad-venv\Scripts\python.exe fea\scripts\eval_finger.py <name> production \"{}\" full"
```
- `eval_finger.py` / `iter_harness.py` / `render_wrap.py` all run unchanged (paths are
  `os.path.join`, cross-platform). Results land in `C:\Users\andre\gripper-cad\fea\iterations\<name>\`.
- For a long job, wrap with `start /b` or just let the SSH session stream; it's CPU-bound.

## Keep the MSI repo current / pull a branch
```bash
ssh andremsi "cd /d C:\Users\andre\gripper-cad && git fetch origin && git checkout <branch> && git pull"
```

## Pull results back to this machine
```bash
# a single results dir
scp -r andremsi:C:/Users/andre/gripper-cad/fea/iterations/<name> fea/iterations/
# or commit on the MSI and pull here via git
```

## Notes / gotchas
- Don't chain `python -m venv ...` with `&& ... 1>nul` in one line over SSH — it has
  tripped "system cannot find the path"; run venv creation as its own command.
- TPU **printing** is unrelated to this — see `PRINT_PROFILE_P1S_TPU.md` for the P1S
  profiles. This node is for FEA/render compute only.
- Performance: the MSI screen battery ran ~263 s (≈ local); it mainly **offloads**
  the main machine rather than being dramatically faster for this CPU-bound solver.

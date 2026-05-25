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

## GPU solver (CuPy / RTX 3070) — works, but CPU is faster at this scale

The FEA solve has an optional GPU backend (`GRIPPER_FEA_GPU=1`, opt-in; default is the
CPU path). It runs the full corotational contact solve on the GPU (CuPy + CG/Jacobi),
and is **numerically validated** — GPU results are identical to CPU (grip/margin/arc
match). But at the gripper's mesh sizes it is **slower than CPU**, so CPU stays default.

**Enable (on the MSI):**
```bash
ssh andremsi "cd /d C:\Users\andre\gripper-cad && set PYTHONPATH=C:\Users\andre\gripper-cad && set \"PATH=C:\Users\andre\cad-venv\Lib\site-packages\nvidia\cuda_nvrtc\bin;%PATH%\" && set \"GRIPPER_FEA_GPU=1\" && C:\Users\andre\cad-venv\Scripts\python.exe fea\scripts\eval_finger.py <name> production \"{}\" full"
```
- One-time installs (done): `cupy-cuda12x[ctk]` + `nvidia-cuda-nvrtc-cu12`.
- **Required:** put `...\nvidia\cuda_nvrtc\bin` on `PATH` (above) or CuPy can't find
  `nvrtc-builtins64_129.dll` at kernel-compile time → `NVRTC_ERROR`.
- Use `set "VAR=1"` (quoted) not `set VAR=1 &&` — the latter assigns `"1 "` (trailing
  space) in cmd.exe and the flag silently reads as off. (The code now `.strip()`s it.)

**Benchmark (RTX 3070, 6 steps, one R22 circle, production finger):**

| mesh | tets | DOF | CPU solve | GPU solve |
|---|---|---|---|---|
| 1.30 | 18.5k | 16.0k | **56 s** | 142 s |
| 0.85 | 27.4k | 23.1k | **102 s** | 132 s |

**Read it honestly:** the GPU is **overhead/latency-bound** here — its time barely
changes with mesh (142→132 s) while CPU's nearly doubles (56→102 s). SciPy's sparse
*direct* solve is extremely fast at ≤25k DOF; the GPU's per-Newton-iteration host
syncs + batched 3×3 SVD + kernel-launch latency dominate. The crossover where GPU wins
is at **much finer meshes (100k+ DOF)** — beyond the resolution this project uses.
**Default to CPU.** The GPU path is there for future high-res / large multi-body runs;
to make it competitive at small sizes would need an iterative polar decomposition
(drop the cuSOLVER SVD) and removing the per-iteration device→host syncs.

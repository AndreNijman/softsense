"""GPU-vs-CPU benchmark for the FEA solver. Times the SOLVE (what the GPU
accelerates) separately from meshing (always CPU). Run once per backend:

  GRIPPER_FEA_GPU=0 python bench_gpu.py <mesh_max> <nsteps>
  GRIPPER_FEA_GPU=1 python bench_gpu.py <mesh_max> <nsteps>

Same finger (production) pressed by one R22 circle, so the only variable is the
backend + mesh density.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
import iter_harness as H

mm = float(sys.argv[1]) if len(sys.argv) > 1 else 1.3
ns = int(sys.argv[2]) if len(sys.argv) > 2 else 12
H.MESH_MAX = mm; H.MESH_MIN = max(0.3, mm * 0.45); H.NSTEPS = ns
H.REPORT_MODE = "grip"; H.OBJ_SHAPE = "circle"; H.R_NECK = 22.0; H.YC = 80.0
work = os.environ.get("TEMP", "/tmp")

p2d, tris, lm = H.regen_section({}, work)
t1 = time.time()
sol = H.run_fea(p2d, tris, lm, verbose=False)
tsolve = time.time() - t1
m = H.metrics(sol)
ndof = sol["rest"].shape[0] * 3
print("BACKEND=%s mesh=%.2f tets=%d ndof=%d | solve_s=%.1f | grip=%.1f margin=%.1f arc=%.1f score_check"
      % ("GPU" if H.GPU else "CPU", mm, sol["tets"].shape[0], ndof, tsolve,
         m["grip_at_press_N"], m["margin_x"], m["contact_arc_deg"]))

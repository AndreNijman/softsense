# FEA plan — gripper stats + FEA-driven finger morph for the underwater render

**Run location decision (final):** FEA runs on the **Surface** (Linux, `.cad-venv`
with build123d — needed to extract the Fin Ray cross-section; the solve is a small
2D CPU job, no GPU benefit). The **MSI laptop** (Windows 11, RTX 3070, Blender 5.1)
does the **photoreal render only** — that is the genuinely heavy, GPU-bound task.

**SSH:** key `~/.ssh/id_ed25519` (comment `andre@void`, the mislabel). Alias
`andremsi` in `~/.ssh/config` → `192.168.1.160`, user `andre`. `ssh andremsi` works.

---

## Why 2D plane-strain is the CORRECT model (not a simplification)
UNDERWATER §3: the Fin Ray finger is a **2.5-D extrusion through the full 10 mm Z
depth** — every rib/cell is constant in Z. The Fin Ray effect is inherently a 2D
truss mechanism; full 3D adds mesh pain, not physics. So the finger compliance is a
**plane-strain 2D problem**, extruded back to 10 mm for the render.

## Solver
`scikit-fem` (pip into the venv; pure Python; 2D plane-strain; incremental Newton
for geometric nonlinearity; penalty-method contact against the rigid artifact).
`meshio` + `matplotlib` for IO + the stress/deformation animation.

## Deliverable 1 — Fin Ray finger compliance (the centerpiece)
- Extract the finger cross-section polygon from `gripper.py` (build123d section at
  mid-Z), mesh it (triangles).
- Material: TPU ~95A, neo-Hookean (or Mooney-Rivlin). **Coefficients are ASSUMED
  literature values for 95A, not measured on the print** — stated in FEA_NOTES.
- Boundary conditions: fix the mount eyes (C/D pivot region); drive the actuation by
  prescribing the finger base motion through the `GRIPPER_OPEN` closing stroke;
  rigid circular artifact boundary as a penalty contact obstacle.
- Outputs: per-step deformed node field (`finray_morph_<frame>.npz`) = the Blender
  morph driver; von Mises field; **grip/contact reaction force vs actuation** curve.

## Deliverable 2 — rigid load-path stats (linear-elastic)
Quick linear-elastic 2D/section checks → max von Mises + deflection + FoS vs
material allowable, to corroborate the repo hand-calcs:
- snap clip cantilever (repo: 1.36 % worst-tight strain, PA12-GF)
- ~~finger-pin barb seat / counterbore shoulder (2.78 % insertion)~~ **obsolete** — pins no longer flex; retention is now a melted PETG-HF cap head (geometric formed head, no insertion strain to check)
- gear tooth root (drive torque) and drive-arm at the C-eye boss
Emit `stats.json` + `stats.md`.

## Deliverable 3 — sediment is a Blender SIM SPEC, not FEA
Do not FEM the sediment. The FEA supplies the **grip-break force** that justifies
*when* the artifact releases from the silt; the sediment dynamics (particle emit on
break, Stokes-drag drift, slow settle) are authored in Blender. Spec goes in the
render prompt.

## Pre-declared convergence escape valves (planned graceful degradation)
1. If hyperelastic + penalty contact won't converge → drop to **geometrically-
   nonlinear linear-elastic (corotational / Saint-Venant–Kirchhoff)**. Still a
   physical deformation field, far more robust.
2. If the full closing stroke diverges → solve **piecewise**: short load
   increments, store each converged step, animate the sequence. Never one big solve.

## Honesty floor (ships in fea/FEA_NOTES.md)
- TPU coefficients assumed (cite typical 95A), not measured.
- Plane-strain assumption (justified by Z-extrusion geometry).
- Contact = penalty method, friction value stated.
- Rigid four-bar motion is EXACT (kinematics); finger compliance is FEA; sediment is
  artistic Blender sim. The render is **"FEA-driven compliance + keyframed kinematics
  + artistic sediment"** — NOT "fully simulated physics."

## Bundle (copied to the MSI for rendering)
```
/home/andre/gripper-cad/render_bundle/
  geometry/   per-part GLB + per-part transform JSON (the rigid kinematics morph)
  fea/        stats.json, stats.md, finray_morph_<frame>.npz, stress_animation.mp4,
              force_curve.png, FEA_NOTES.md
  prompt.txt  PC-ready Blender prompt referencing these bundle paths
  README.md   contents + what is exact vs approximated
```
Copy to MSI: `tar` the bundle here, `scp` it to `andremsi`, untar with Windows
`tar.exe` (ships since Win10 1803). `scp -r` as the fallback (rsync likely absent
on stock Windows).

# RENDER NOTES — Underwater archaeology gripper (FEA-driven, side grip)

Photoreal Cycles/OptiX render of a 3D-printed compliant Fin Ray gripper reaching in
**horizontally from the side** to grip a weathered ceramic amphora by the neck and
lift it clear of a silty seabed. Rendered on RTX 3070 (Blender 5.1, Cycles GPU/OptiX).

This build deviates from the original bundle brief in two user-requested ways:
1. **Side grip** — the gripper approaches horizontally and grips the vertical neck,
   instead of descending fingers-down from above.
2. **A custom, full 3D FEA** of the finger wrap was solved here (replacing the bundled
   2D plane-strain wrap), so the finger compliance is accurate to the *actual* neck
   geometry and grasp position. See `fea3d/`.

---
## What is EXACT vs SIMULATED vs ARTISTIC

### 1. Rigid open/close kinematics — EXACT
The 17 parts are posed from `geometry/transforms.json` (the CAD four-bar solver output,
Kabsch-rigid, residual ~0). Each part's matrix is interpolated (lerp position / slerp
rotation) through the 13 solver samples and keyframed, so the open/close morph is the
real mechanism motion. Finger splay at open=1 is 20.07° (within the 18–20° spec).

### 2. Finger wrap — CUSTOM FULL 3D FEA (the centrepiece), genuine simulation
Not the bundled 2D field, and not an artistic bend. Solved fresh in `scripts/fea3d_finger.py`:
- **Geometry:** the real finger structural cross-section (`fea/finray_morph.npz`,
  1655 nodes / 2791 tris — the toothed contact face + Fin Ray rib truss + mount) **extruded
  through the 10 mm finger thickness into linear tetrahedra → 25,119 tets / 19,860 DOF.**
- **Constitutive:** 3D **corotational elasticity** (polar-decomposition warped stiffness),
  the right model for this regime — TPU strains are small (~few %) while rotations are
  large; corotational captures the big bending exactly with a symmetric tangent.
  Newton–Raphson with displacement (press) load-stepping; converged (penalty penetration
  < 0.01 mm).
- **Contact:** **penalty contact against the analytic rigid amphora neck (cylinder, R=22 mm)**,
  axis vertical = matches the upright neck in the side grip. The neck is placed at its true
  position in the finger frame (finger-local y≈80 mm, first contact at gripper open≈0.55) and
  pressed in by the gripper's over-close; the Fin Ray truss converts the push into the
  emergent conforming wrap (tip curls **inward, around the neck** — the physically correct
  direction comes out of the contact solve for free).
- **Result at the grasp working point:** peak **von Mises ≈ 2.70 MPa** vs 27.3 MPa Bambu TPU 95A HF (in-plane)
  strength → **~9–15× margin → a gentle, fragile-safe grip**; tip wrap ≈ 12 mm; grip reaction
  ≈ 18 N (displacement-controlled).
- The 3D displacement field is mapped (inverse-distance) onto the Blender finger meshes as a
  shape key, animated 0→1 over the grasp, synchronised with the rigid close so the conform
  tracks the neck without clip-through. `finger_L` = x-mirror of the `finger_R` solve.
- Full stress field, force/wrap curves, an animation of the wrap forming, and stats are in
  `fea3d/` (`wrap_stages.png`, `wrap_3d.png`, `force_curves.png`, `fea3d_wrap.mp4`,
  `stats_finray_3d.json`, `STATS_3D.md`).

**Honesty on the FEA:**
- Bambu TPU 95A HF: E=9.8 MPa (in-plane) is **MEASURED** (ISO 527); ν is a literature estimate. (Legacy bundle figures here predate the switch — at the old E=40.)
- **ν relaxed 0.45→0.42** to limit linear-tetrahedron volumetric locking of near-incompressible
  TPU (the bundle's 2D solve made the same compromise). The von Mises field (the fragility
  metric) is reliable; the absolute grip **reaction force is an upper bound** because (a) residual
  locking stiffens the response and (b) it is displacement-controlled, so it can pass the
  load-control limit point the bundled 2D solve capped at (5.4 N).
- Contact is **frictionless** (the wrap is structural, not friction-held; real friction would
  only grip better).
- The 3D mesh is the structural cross-section extruded (consistent with the bundle's plane-strain
  assumption lifted to 3D); fine tooth detail on the render mesh is carried by the mapped field.

### 3. Sediment puff, marine snow, water optics — ARTISTIC (FEA-*timed*, not FEA)
No fluid/DEM simulation. The sediment is a Blender particle burst + a volumetric silt cloud
**timed to the FEA grip-break/lift beat** (the artifact detaches → puff blooms from the silt
depression, decays over ~0.5 s emission and settles over several seconds; a fine silt stream
sheets off the rising artifact). Marine snow is a suspended particle system with current +
turbulence + drag fields. Water is a volume (scatter + wavelength absorption → teal, depth
haze, visibility falloff); caustics + light shafts are a textured spotlight gobo through the
volume. All scene art.

**So:** *FEA-driven finger compliance + exact keyframed kinematics + artistic sediment/water* —
never "fully simulated physics."

---
## Scene & render setup
- **Gripper materials:** PA12-GF (charcoal, matte, glass-fill speckle, faint FDM layer lines,
  wet coat) on the structural parts; TPU ~95A (safety-yellow, semi-matte, slight SSS) on the
  fingers; pale silt dusting on upward faces + wet sheen on everything underwater.
- **Amphora:** procedural weathered Greek transport amphora (surface of revolution + 2 handles,
  one broken), neck ≈ 44 mm dia (sized to the FEA grasp), aged terracotta + calcareous
  encrustation + biofilm, partially buried in a settled silt depression.
- **Environment:** PolyHaven CC0 sand PBR seabed (displaced ripples + dunes + a bowl depression),
  teal volumetric water, animated caustic gobo + god-ray shafts, marine snow, scattered rock
  debris + a second half-buried sherd, HDRI surface-down ambient, ROV cool-white key light.
- **Choreography (~15 s @ 24 fps, 360 frames):** establish wide → reach in horizontally → grasp
  (rigid close to first contact, then FEA wrap 0→1) → lift (Child-Of pickup, sediment bloom at
  the break) → raise clear & hold. Cinematic camera: wide → push-in → tight shallow-DoF hero on
  the conforming grasp → pull back/up on the lift; subtle ROV/handheld float.
- **Render:** Cycles GPU (OptiX), adaptive sampling + OptiX denoise, volumetrics + motion blur,
  AgX view transform. Animation 1920×1080 PNG sequence → ffmpeg H.264 (24 fps, yuv420p).
  Hero stills at 3840×2160.

## Outputs
- `render_out/animation.mp4` — the H.264 movie
- `render_out/frames/` — the 1080p PNG sequence
- `render_out/hero/hero_1_approach.png … hero_4_held.png` — 4K hero stills
- `fea3d/` — the custom 3D FEA: stress renders, wrap animation, force curves, stats

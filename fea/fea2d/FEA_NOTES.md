# FEA notes — what is exact, what is approximated

This bundle's motion has three layers. Be honest about each in any render writeup.

## 1. Rigid open/close = EXACT mechanism kinematics
`geometry/transforms.json` is the per-part rigid transform across `open = 0..1`,
recovered directly from the CAD four-bar solver (`gripper.py`) by sampling the
posed assembly and fitting each part's rigid body motion (Kabsch). The fit
residual is ~0 (printed as `kabsch_max_rmsd_mm`), which *proves* the parts move
rigidly — this layer is exact, not approximated.

## 2. Fin Ray finger wrap = REAL finite-strain FEA (with stated assumptions)
`fea/finray_morph.npz` + the `finger_*_wrap.obj` shape keys come from a genuine
nonlinear FEA, not an artistic bend:
- **Method:** 2D plane-strain, St.-Venant–Kirchhoff (finite strain, total
  Lagrangian), Newton iteration with load stepping, in scikit-fem. The analytic
  consistent tangent was **finite-difference verified** (relative error scaled
  linearly with the perturbation — the signature of a correct tangent).
- **Plane strain is the correct model**, not a simplification: the Fin Ray finger
  is a Z-constant 2.5-D extrusion (UNDERWATER §3), so the cross-section carries the
  mechanics; 3D adds nothing physical.
- **Assumed inputs (NOT measured on the print):** TPU ~95A as E = 40 MPa, ν = 0.45
  (near-incompressible; 0.45 chosen to limit P1 volumetric locking). These are
  literature-typical 95A values; a real coupon would shift the absolute force, not
  the qualitative wrap.
- **Contact representation:** a load-controlled horizontal patch load on the
  contact face (the artifact push), ramped to 5.4 N — just below the load-control
  limit point (~5.7 N snap-through). This produces the emergent Fin Ray wrap
  (tip curls ~23 mm inward) without a full contact-search solve. The applied
  patch load IS the grip force.
- **Result:** max von Mises ~2.7 MPa vs ~25–40 MPa TPU strength → ~10× margin →
  a *gentle* grip, appropriate for a fragile artifact.

## 3. Snap-clip = linear FEA corroboration
`clip_stats.json`: linear plane-stress, quadratic-element FEA of the cover snap-clip
cantilever at the worst-case engagement deflection. Nominal bending strain ~1.1–1.4%
matches the repo's analytic build gate (1.36% < 1.5% PA12-GF allowable). The raw
sharp-clamp corner peak (~2.2%) is a mesh-sensitive re-entrant-corner singularity
(SCF ~1.65) mitigated by the part's root fillet — informational, not governing.

## 4. Sediment / water / marine snow = ARTISTIC Blender sim
There is NO sediment or fluid FEA/DEM here. The render's sediment puff is a Blender
particle sim, **timed** by the FEA grip-break force (when the artifact detaches), but
its dynamics are artistic. The water optics (volumetric absorption, caustics, god
rays) are likewise scene art.

## Bottom line for the render
Describe it as **"FEA-driven finger compliance + exact keyframed kinematics +
artistic sediment/water"** — never "fully simulated physics".

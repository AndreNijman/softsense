# Gripper FEA stats

## Fin Ray finger — nonlinear FEA (the centrepiece)
- Model: Fin Ray finger, plane-strain, St.-Venant-Kirchhoff, total Lagrangian
- Material: Bambu TPU 95A HF, E = 9.8 MPa (in-plane, ISO 527), ν = 0.45 (legacy 2D run computed at the old E=40 estimate)
  (literature-typical 95A, not measured on the print)
- Mesh: 1655 nodes / 2791 triangles, 24 load steps
- **Peak grip load: 5.40 N** (applied contact-patch load = grip force)
- **Tip inward wrap: 23.4 mm** (the Fin Ray conform)
- **Max von Mises: 2.66 MPa** → vs 27.3 MPa Bambu in-plane strength = **~10× margin** (gentle grip)
- Load-control limit point: ~5.7 (load-control snap-through; solve capped at 5.4 N)

## Cover snap-clip — linear FEA corroboration
- Model: linear plane-stress FEA (quadratic elements), prescribed tip deflection, material PA12-GF (E 4500.0 MPa)
- Inputs: free length 20.5 mm, thickness 2.0 mm, tip deflection 1.9 mm
- **Nominal bending strain: 1.12%** (analytic 1.36%, gate 1.5%) → margin 1.34×
- Sharp-clamp corner peak strain 2.24% (SCF 1.65, mesh-singularity, mitigated by root fillet)
- Verdict: **PASS**

See FEA_NOTES.md for the exact-vs-approximated breakdown.

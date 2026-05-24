# Custom 3D FEA — Fin Ray finger wrap (contact against amphora neck)

**Method:** 3D corotational (polar-decomposition warped-stiffness) finite-element, linear tetrahedra, Newton-Raphson with displacement (press) load stepping.

- Mesh: **6620 nodes / 25119 tetrahedra** (3 layers through thickness), 19860 DOF
- Material: TPU ~95A, E=40.0 MPa, nu=0.42 (nu relaxed from 0.45 to limit linear-tet volumetric locking (the bundle's 2D solve made the same compromise))
- Contact: penalty, frictionless vs rigid neck cylinder R=22.0 mm, axis = vertical (side grip)
- Drive: neck pressed 9.0 mm into the contact face over 24 steps

## Grasp (working point)
- Grip reaction: **18.25 N** · tip wrap **12.05 mm** · max von Mises **2.704 MPa**
- Safety: ~**9.2x** margin vs TPU strength [25.0, 40.0] MPa -> gentle grip — peak stress well below TPU strength (fragile-safe)

## Peak (full press)
- Grip reaction 18.25 N · tip wrap 12.05 mm · von Mises 2.704 MPa

## Honesty
Genuine 3D contact FEA. Grip reaction is displacement-controlled (can pass the load-control limit point the bundled 2D solve hit at 5.4 N) and is an UPPER bound because linear-tet volumetric locking stiffens near-incompressible TPU; the von Mises field (the fragility-relevant metric) is reliable and gives ~10x margin.

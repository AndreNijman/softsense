# Design-for-3D-printing (DFM) standards & compliance

This gripper is built to standard FDM design-for-additive-manufacturing rules so
every part prints reliably on a normal 0.4 mm-nozzle FDM machine with no exotic
settings. The rules below are the widely-published FDM guidelines; the right
column is how this model meets them.

| Rule (FDM standard) | Target | This design |
|---|---|---|
| **Min wall thickness** | ≥0.8 mm (≥2 perimeters); 1.5 mm for functional walls | enclosure/cover walls **3.0 mm**; snap-clip arm **2.0 mm**; axle-boss walls **2.0 mm** (`BOSS_OD_R = AXLE_SCREW_R + 2`); shaft-bushing wall **1.6 mm**. Fin Ray finger: spine **1.8 mm**, ribs **1.6 mm**, contact beam **1.2 mm** — the contact beam is **intentionally below 1.5 mm** (3 full perimeters @0.4 nozzle = solid, ≥ the 0.8 mm / 2-perimeter floor) so the face stays compliant and spreads pressure (FEA-chosen, `fea/UNIVERSAL_FINGER.md`). |
| **Overhang angle** | ≤45° from vertical without support | boxy parts print flat; gear teeth, Fin Ray ribs and grip teeth are in-plane (no Z overhang); snap-pin barb is a narrowing cone (self-supporting); cover clips print pointing up |
| **Hole diameter** | ≥1 mm (vertical) / ≥2 mm (horizontal); oversize 0.2–0.4 mm | pivot bores Ø5.2 mm, drains Ø5 mm — all well above min, with built-in clearance |
| **Mating clearance** | ~0.3 mm per side | `PRINT_CLEAR = 0.3` on every pivot/slide; `SNAP_CLEAR = 0.35` on snap engagements |
| **Sharp edges** | fillet/chamfer to relieve stress & ease printing | Fin Ray rib-cell corners filleted (R0.8), tip/teeth rounded, base chamfered (anti-elephant-foot); link bars **and** drive-arm arms get a 0.4 mm edge-break (`DFM_EDGE`) top & bottom; snap-pin head-flange rims chamfered; enclosure/cover perimeter filleted (R4/R2) and boss roots filleted (R0.8). **Intentionally crisp:** gear-tooth flanks (functional meshing, sealed inside the housing, printed in-plane) and the snap-pin barb catch face (positive lock). |
| **Bridge span** | ≤10 mm reliable | no unsupported bridge exceeds the wall spans; drain/window openings are short |
| **Elephant foot** | chamfer bottom edges | bed-face edges chamfered on fingers & link bars |

**Materials (seawater):** Fin Ray fingers in ether-based **TPU 95A** (compliance
is the grip mechanism — never ester-TPU: it hydrolyzes); snap pins in **PETG**
(springy to snap, stiff enough to resist creep — never TPU, which creeps and
wallows the bore); structural parts in **PETG / ASA / glass-filled nylon** (ASA
for UV/topside, GF-nylon for deep/long dives). **Never PLA** (hydrolyzes wet) and
**never unfilled nylon** (absorbs water, swells). All-polymer → no galvanic
corrosion. **Creep (resolved):** the load-bearing barbed finger pins no longer
rely on elastic preload. The expanded lip now drops into a **rigid counterbore
pocket** that radially confines it (creep relaxes it *outward*, away from
escape) and bears the pull-out load on a solid shoulder; `SNAP_BARB_SEAT` is
1.2 mm (audit floor ≥1.0). Axle dowels are captured geometrically between a
back-bore step and the cover boss. Capture is now geometric, not creep-prone.
See `ENGAGEMENT.md` (measured numbers), `UNDERWATER.md`, `PRINTING.md`, `BOM.md`.

**Tuning knobs** (in `gripper.py`): `PRINT_CLEAR` (fit), `SNAP_CLEAR` (clip/barb
engagement), `DFM_EDGE` (edge-break size). Print one snap pin + a scrap bore
first and adjust `PRINT_CLEAR` ±0.05 mm if the click is too tight/loose.

## Sources
- [3D On Demand — FDM design guidelines (wall thickness, tolerances)](https://www.3d-demand.com/blog/design-guidelines-for-fdm-3d-printing-wall-thickness-tolerances-file-prep)
- [Hydra Research — FFF design rules](https://www.hydraresearch3d.com/design-rules)
- [UltiMaker — Design for FFF](https://ultimaker.com/learn/design-for-fff-3d-printing-maximize-your-success/)
- [Xometry — FDM design tips](https://xometry.pro/en/articles/fdm-design-tips/)

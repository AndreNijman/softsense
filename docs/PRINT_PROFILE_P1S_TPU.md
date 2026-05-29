# Gripper fingers — Bambu TPU 95A HF on a Bambu Lab P1S (0.4 mm hardened nozzle)

Complete, importable print stack for the two Fin Ray fingers, with **every setting
specified and justified**, plus the FEA re-check confirming all the stats hold for
**Bambu TPU 95A HF** specifically. Target machine: **Bambu Lab P1S, 0.4 mm hardened
steel nozzle**, slicer **Bambu Studio**.

> The fingers are the only TPU parts. The rigid parts (PA-class) and the snap pins
> (PETG-HF) print on the same P1S with stock Bambu system profiles — see §6.

> **Why Bambu TPU 95A HF (vs the old eSUN eTPU-95A):** the "HF" (high-flow) grade
> prints at ~3× the throughput of standard TPU 95A (max volumetric speed ~12 mm³/s,
> up to ~200 mm/s) and — decisively for this repo — Bambu **publishes ISO 527
> printed-specimen mechanical data**, so the finger FEA now runs on a *measured*
> modulus and strength instead of the old 40 MPa guess. See §5.

## TL;DR

1. Import the two profiles in `profiles/` (Bambu Studio → **File → Import → Import
   Configs…**): the **filament** profile `Bambu_TPU-95A-HF_@P1S_0.4.json` and the
   **process** profile `finger_TPU_0.16mm_@P1S_0.4.json`. (Or start from Bambu Studio's
   own system **Bambu TPU 95A HF** preset and apply the process profile.)
2. **Dry first: 70 °C for 8 h** (Bambu spec). TPU 95A HF is AMS-compatible, but for the
   critical cyclically-flexed finger an **external spool + desiccant box** removes any
   AMS PTFE-bend stringing risk.
3. **Use the Textured PEI plate, NO glue** (see §1 — glue *over*-adheres TPU on
   textured PEI; glue is only for smooth plates). Select the imported filament +
   process, slice `print_plates/plate_tpu_1.stl` (both fingers), print.

The FEA (`fea/UNIVERSAL_FINGER.md`, `fea/SCALABILITY.md`) is **confirmed valid for
Bambu TPU 95A HF**: see §5 — the force-targeted safety margins stay **~8×** (and edge
slightly up on the measured 27.3 MPa strength), and the design ranking is unchanged.

---

## 1. Hardware & material prep (do these or the print fails)

| Item | Setting | Why |
|---|---|---|
| Spool path | **External spool (recommended) or AMS** | TPU 95A HF is rated AMS-compatible (unlike soft standard TPU). For this critical flexing part an external spool fed straight to the toolhead removes the AMS long-PTFE bend as a stringing/consistency variable. Either works on the P1S. |
| Drying | **70 °C ≥ 8 h** (Bambu spec; or X1-bed 80–90 °C 12 h), keep in a dry box while printing; storage <20 % RH | TPU 95A HF is "highly sensitive to humidity"; wet TPU = stringing, bubbles, weak layers. |
| Nozzle | **0.4 mm hardened steel** (you have this) | Fine for TPU. Use a clean/new or cold-pulled nozzle — TPU drags old residue. Do **not** use a 0.2 mm nozzle for TPU. |
| Extruder | P1S stock direct extruder | HF flows easily; the P1S direct extruder handles it. Feed straight (external spool) or via AMS. |
| Plate | **Textured PEI plate, NO glue** (preferred) | Bambu Wiki TPU guidance: the textured PEI keys TPU mechanically — "excellent adhesion without adhesives," and *"applying glue may cause excessive adhesion."* Keep the bed at **30–35 °C** (low) so the large flat 28×96 finger footprint stays removable; release by cooling, lifting a corner, squirting **IPA** into the gap, then peeling slowly (don't pry a hot part — chips the PEI). **Alternative:** a smooth plate (Cool/Engineering/High-Temp) needs **glue** there as a release barrier — the datasheet's blanket "Bed prep: Glue" line is for those smooth plates, not the textured one. The Engineering plate gives a glossy bottom you don't need on a finger base, so textured-PEI/no-glue is the pick. |
| Orientation | **Flat on the 28×96 face** (as in `print_plates/`) | Fin Ray cells lie in the build plane → self-supporting, no supports; in-plane bending (the grip mechanism) runs in the **strong X-Y direction** (E 9.8 MPa / 27.3 MPa vs the weaker through-Z 7.4 / 22.3). |

---

## 2. The two importable profiles

| File | Type | Inherits (system base) | Shows up for |
|---|---|---|---|
| `profiles/Bambu_TPU-95A-HF_@P1S_0.4.json` | filament | `Generic TPU @base` | **Bambu Lab P1S / P1P / X1C 0.4 nozzle** |
| `profiles/finger_TPU_0.16mm_@P1S_0.4.json` | process | `0.20mm Standard @BBL X1C` | Bambu Lab P1S / P1P / X1C, 0.4 nozzle |

Both are `"from": "User"`, `instantiation: "true"`, and inherit a real Bambu system
profile so any value not overridden resolves cleanly. (The P1S has no dedicated
`@BBL P1S` process; it uses the X1C process via `upward_compatible_machine` — so the
process profile inherits the X1C base, which is correct for the P1S.) If your Bambu
Studio ships a system **Bambu TPU 95A HF** filament preset, you can re-base the
filament profile on it (change `"inherits"`) for vendor-tuned pressure-advance, etc.

**Import:** Bambu Studio → File → Import → *Import Configs…* → pick both `.json`. They
appear under **User Presets** in the filament and process dropdowns when a P1S 0.4 is
selected. If a profile is rejected on an older Studio build, bump `"version"` to match
your installed profile version (top of your `BBL.json`).

---

## 3. Filament settings — every value + why (`Bambu TPU 95A HF @P1S 0.4`)

Bambu's TDS recommends nozzle 220–240 °C, bed 30–35 °C (glue prep — but see §1: that
glue line is for *smooth* plates; on the recommended textured PEI use NO glue), drying 70 °C 8 h,
chamber 25–45 °C, cooling fan on, printing speed <200 mm/s, retraction 0.8–1.4 mm @
20–40 mm/s. The profile sets:

| Setting | Value | Rationale |
|---|---|---|
| `filament_type` | TPU | — |
| `filament_vendor` | Bambu Lab | — |
| `filament_density` | **1.22 g/cm³** | Bambu TDS (ISO 1183; used for weight/cost only). |
| `filament_flow_ratio` | **0.95** | Soft 95A over-extrudes; slight under-flow keeps the 1.2 mm contact wall dimensionally true. |
| `filament_max_volumetric_speed` | **12 mm³/s** | The HF headline — ~4× the old eSUN cap (3.0). The finger's slowest member draws ~1.3 mm³/s, so this is a generous ceiling, not a bottleneck; it's what lets the process speeds in §4 rise. |
| `nozzle_temperature` | **230 °C** | Bambu's specimen-test temperature; mid of the 220–240 band; balances flow against the layer bonding a cyclically-flexed part needs. |
| `nozzle_temperature_initial_layer` | **235 °C** | Hotter first layer = better bed bond on flexible filament. |
| `nozzle_temperature_range_low/high` | 220 / 240 | Bambu bounds. |
| `hot_plate_temp` / `textured_plate_temp` / `cool_plate_temp` / `eng_plate_temp` | **35 °C** (initial 35) | Bambu's 30–35 °C band. TPU 95A HF wants a cooler plate than the old eSUN 45 °C; on the recommended **textured PEI** the texture does the adhesion (NO glue — see §1), and the low temp keeps the large flat footprint removable. |
| `filament_retraction_length` | **0.8 mm** | TPU needs minimal retraction (Bambu 0.8–1.4). 0.8 mm is safe for the P1S direct path; more pulls soft filament into the heatbreak → jams. |
| `filament_retraction_speed` | **30 mm/s** | Mid of Bambu's 20–40; slow retract for soft filament. |
| `filament_z_hop` | **0.4 mm** (Auto Lift) | Clears the 0.6 mm grip teeth on travel without stringing across the contact face. |
| `fan_min_speed` / `fan_max_speed` | **50 / 80 %** | **Conservative deviation from "fan on"** — NOT claimed optimal. The finger flexes in service; lower fan protects the interlayer (Z) bonds that shear during flex (the weak 7.4 MPa / 22.3 MPa direction), at the predicted-safe (~8× margin) loads. **Untested under cycling.** If you fatigue-test and it holds, full cooling may give cleaner ribs/teeth — treat 100 % as the validated-once-tested setting. |
| `overhang_fan_speed` | 100 % | Full cooling on any short overhang (rib undersides). HF overhang limit ~55°. |
| `additional_cooling_fan_speed` | 70 % | Aux part fan. |
| `close_fan_the_first_x_layers` | **3** | Fans off for the first 3 layers → strong bed adhesion (critical for the narrow TPU footprint). |
| `fan_cooling_layer_time` / `slow_down_layer_time` | 60 / 8 s | Slow small layers so they cool/bond. |
| `temperature_vitrification` | **30 °C** | Filament soften-point for the slow-down logic (Generic-TPU system value — *not* the bed temp). |
| `filament_start_gcode` | reminder note | "Textured PEI, NO glue; bed 30–35 °C; dry 70 °C 8 h; external spool safest for the flexing part." |
| `compatible_printers` | **P1S / P1P / X1C 0.4** | The profile assumes the hardened nozzle; keep it off machines that may have a brass nozzle (TPU wears brass). |

---

## 4. Process (print) settings — every value + why (`Gripper finger TPU 0.16mm`)

The shipped finger has **thin graded walls** (contact 1.2 / rib 1.6 / spine 1.8 mm)
and **0.6 mm grip teeth** at 2.2 mm pitch — the process is tuned to print every wall
**fully solid** (the FEA's 100 %-dense-wall basis) and resolve the teeth/ribs.

> **HF speed-up:** because TPU 95A HF allows ~12 mm³/s, the wall/infill speeds below
> are raised vs the old eSUN profile (outer 20→30, inner 30→60, infill 40→90,
> solid 35→70 mm/s). The 12 mm³/s volumetric cap in the filament profile still governs
> the true ceiling on any thick move, so quality on the fine ribs/teeth is preserved
> while bulk infill runs much faster. First-layer and outer-wall stay slow for a clean
> grip face.

| Setting | Value | Rationale |
|---|---|---|
| `layer_height` | **0.16 mm** | Resolves the 2.2 mm-pitch grip teeth and thin ribs cleanly; finer Z also bonds better. |
| `initial_layer_print_height` | 0.20 mm | Robust first layer. |
| `wall_loops` | **5** | Enough loops that every member fills with perimeters (the slicer uses only as many as fit). |
| `line_width` / `outer_wall` / `inner_wall` | **0.40 mm** (all walls) | **Critical:** at 0.40 mm the **1.2 mm contact beam = exactly 3 flush perimeters (0.40×3) — no gap-fill**. The contact beam is the most cyclically-loaded member, and gap-fill on TPU is where layer bonding gets unreliable; flush perimeters avoid it. Ribs 1.6 mm = 4 flush; spine 1.8 mm = 4 + a small 0.2 mm gap-fill (interior, non-critical). |
| `wall_generator` | **classic** | Predictable perimeters on thin TPU walls (Arachne adds variable-width gap-fill on near-integer walls). |
| `detect_thin_wall` | 1 | Captures the 1.2 mm contact beam as solid wall. |
| `initial_layer_line_width` / `sparse_infill_line_width` | 0.50 / 0.45 | Wider first layer for adhesion; wider infill is fine (interior). |
| `top/bottom_shell_layers` | **4 / 4** | Dense skins on the base floor/cap. |
| `sparse_infill_density` | **100 %** | Matches the FEA assumption (fully-dense walls) and keeps the solid base/bracket and grip-ridge insets dense. The finger is small (~30 g), so 100 % is cheap. |
| `sparse_infill_pattern` | rectilinear | Moot at 100 %. |
| `outer_wall_speed` | **30 mm/s** | Slow walls = clean grip face. Raised modestly from 20 (HF tolerates it) but kept slow for surface quality. |
| `inner_wall_speed` | 60 mm/s | HF throughput. |
| `sparse_infill_speed` | 90 mm/s | HF — bulk interior; volumetric cap (12) governs. |
| `internal_solid_infill_speed` | 70 mm/s | — |
| `top_surface_speed` | 30 mm/s | Clean top skins. |
| `gap_infill_speed` | 40 mm/s | — |
| `initial_layer_speed` | **18 mm/s** | Slow, sure first layer. |
| `travel_speed` | 200 mm/s | Travel can be fast (no extrusion). |
| `default_acceleration` | **3000 mm/s²** | **Reduced from the P1S stock 10000.** Soft TPU lags under high accel → blobs/ringing; lower accel = consistent extrusion. |
| `outer_wall_acceleration` | 1500 mm/s² | Gentle on the visible/grip walls. |
| `initial_layer_acceleration` | 500 mm/s² | Calm first layer. |
| `seam_position` | **back** | Keeps the layer seam **off the grip-ridge contact face** (the object side). |
| `brim_type` / `brim_width` | outer_only / **5 mm** | TPU + narrow footprint needs a brim to not peel. |
| `brim_object_gap` | 0.10 mm | Easy brim removal from the flexible part. |
| `elefant_foot_compensation` | 0.15 mm | With the part's base chamfer, keeps the first layer true. |
| `enable_support` | **0 (off)** | Flat orientation is self-supporting. |
| `ironing_type` | no ironing | Would smear the grip teeth. |
| `wall_sequence` | inner → outer | Better outer-wall surface on the grip face. |
| `compatible_printers` | P1S / P1P / X1C 0.4 | P1S visibility. |

---

## 5. FEA re-check for Bambu TPU 95A HF (the stats hold — now on MEASURED data)

**Bambu TPU 95A HF TDS (V1.0)** — ISO 527 / ISO 178 / ISO 1183, **printed specimens**
(this is the upgrade: eSUN never published a modulus, so the repo used a 40 MPa guess):

| property | Bambu value | used in FEA | note |
|---|---|---|---|
| Young's modulus | **9.8 MPa (X-Y) / 7.4 MPa (Z)** (ISO 527, anisotropic) | E **9.8 MPa** in-plane (grip); **7.4 MPa** through-Z (underwater crush) | The finger prints flat, so in-plane bending uses 9.8. Caveat: this is the ISO 527 **initial-tangent** modulus; a Fin-Ray at finite wrap strain is hyperelastic, so absolute forces are order-of-magnitude. Part of the change from the old 40 MPa "secant guess" is therefore *definitional*, not the material being weaker. |
| Tensile strength | **27.3 MPa (X-Y) / 22.3 MPa (Z)** (ISO 527) | strength **27.3 MPa** in-plane; **22.3 MPa** through-Z | Measured printed-specimen values replace the old shaky "25 MPa" estimate. For a 95A elastomer at >650 % elongation this is a stress-ceiling proxy, not a brittle yield. |
| Poisson ratio | (not published) | ν **0.42** | typical TPU 0.42–0.48. **ν relaxed from a TPU-realistic ~0.48 to 0.42 to partially mitigate linear-tet volumetric locking** — not a cure; see `fea/FEA.md` locking-diagnostic ν-sweep. |
| Density | 1.22 g/cm³ | — | (was 1.21 for eSUN — buoyancy change negligible). |
| Elongation at break | >650 % (X-Y) / >480 % (Z) | — | hugely ductile; failure is fatigue/tear, not brittle yield. |
| Water absorption | 1.08 % saturated (25 °C/55 % RH) | — | low uptake; soak-test still advised for sustained immersion (chemistry not stated). |
| Hardness | 95 A | — | — |

**Modulus sensitivity** — the baseline finger sensitivity bracket is re-centered on the
measured 9.8 MPa: **E = 7 / 9.8 / 12 MPa** (force-targeted to a 12 N grasp, strength
27.3 MPa). Because internal stress at a *fixed force* is set by the load, not the
stiffness (St-Venant), the von-Mises margins are **essentially modulus-independent
(~8× across the bracket)** — exactly as the old 30/40/60 bracket showed; only the
absolute number-line shifted. The measured strength rising 25→27.3 MPa nudges the
margin slightly **up**.

**Two reporting frames (both honest, don't conflate them):**
- **Force-targeted** (`REPORT_MODE="grip"`, the basis for the published per-shape
  margins and the universal ranking): margins and ranking are **modulus-insensitive →
  UNCHANGED** by the eSUN→Bambu switch. The (~0.65) universal score and the
  scalability band (0.6–1.1×) **stand as published**.
- **Closure-targeted** (`REPORT_MODE="closure"` at 8 mm, the production code default
  used for the wrap renders): grip force and stress scale ~linearly with E, so at the
  measured E = 9.8 MPa the absolute grip-at-8 mm baseline is **~2.3 N / peak vM
  ~0.81 MPa** (down ~4× from the old 40 MPa figure of 9.3 N / 3.30 MPa) — but this is
  an actuator-travel/absolute-force detail, and the repo's posture is rank/size, not
  certified absolute newtons. Margin at this closure is still ~34× vs 27.3 MPa.

Re-run yourself: `eval_finger.py <name> production '{"_E":9.8,"_strength":27.3}' screen`
(the harness accepts `_E` and `_strength` overrides), or sweep E with
`GRIPPER_E_TPU=7 python iter_harness.py …`.

---

## 6. The other gripper parts on the P1S (not TPU)

The fingers are the only TPU parts. For completeness on the same P1S + 0.4 hardened
nozzle:

- **Snap pins (`snap_pin_*`) — PETG-HF.** Use Bambu's stock **Bambu PETG-HF @BBL P1S**
  filament + a 0.16–0.20 mm process; 100 % infill, 5–6 walls (they're small locking
  parts). Prints cleanly on the P1S.
- **Rigid parts (enclosure, arms, followers, cover, shaft) — spec'd PA12-GF.**
  PA12-GF is marginal on a P1S: it needs ~260–290 °C (within the P1S's hardened-hotend
  range) **but the P1S has no actively heated chamber**, so glass-filled nylon is
  warp-prone on larger parts. Realistic P1S-friendly substitutions that keep the
  rigidity: **Bambu PAHT-CF** or **PETG-CF** (both have stock P1S 0.4 profiles and want
  the hardened nozzle you have), or plain **PETG-HF** for a lower-spec build. Keep the
  enclosure closed and use a brim.

---

## Sources

- **Bambu TPU 95A HF Technical Data Sheet V1.0** — Bambu Lab (ISO 527 Young's modulus
  9.8/7.4 MPa, tensile 27.3/22.3 MPa, elongation >650 %/>480 %, density 1.22 g/cm³,
  water absorption 1.08 %, melting 183 °C; nozzle 220–240 °C, bed 30–35 °C (glue for
  smooth plates; textured PEI no-glue per the Bambu Wiki TPU guide),
  dry 70 °C 8 h, max vol speed ~12 mm³/s, <200 mm/s, fan on, retraction 0.8–1.4 mm).
- Bambu Studio profile schema — `github.com/bambulab/BambuStudio`
  `resources/profiles/BBL/{filament,process,machine}` (Generic TPU + 0.20mm Standard
  @BBL X1C + P1S machine profile; key names, `compatible_printers`, inheritance).
- FEA: `fea/UNIVERSAL_FINGER.md`, `fea/SCALABILITY.md`, `fea/scripts/eval_finger.py`.

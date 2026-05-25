# Gripper fingers — eSUN eTPU-95A on a Bambu Lab P1S (0.4 mm hardened nozzle)

Complete, importable print stack for the two Fin Ray fingers, with **every setting
specified and justified**, plus the FEA re-check confirming all the stats hold for
**eSUN eTPU-95A** specifically. Target machine: **Bambu Lab P1S, 0.4 mm hardened
steel nozzle**, slicer **Bambu Studio**.

> The fingers are the only TPU parts. The rigid parts (PA-class) and the snap pins
> (PETG-HF) print on the same P1S with stock Bambu system profiles — see §6.

## TL;DR

1. Import the two profiles in `profiles/` (Bambu Studio → **File → Import → Import
   Configs…**): the **filament** profile `eSUN_eTPU-95A_@P1S_0.4.json` and the
   **process** profile `finger_TPU_0.16mm_@P1S_0.4.json`.
2. Load eSUN eTPU-95A on an **external spool** (NOT the AMS). **Dry it first:
   55 °C for ≥4 h.**
3. Select the imported filament + process, slice `print_plates/plate_tpu_1.stl`
   (both fingers), print.

The FEA (`fea/UNIVERSAL_FINGER.md`, `fea/SCALABILITY.md`) is **confirmed valid for
eSUN eTPU-95A**: see §5 — safety margins stay **7–8×** and the conclusions are
unchanged.

---

## 1. Hardware & material prep (do these or the print fails)

| Item | Setting | Why |
|---|---|---|
| Spool path | **External spool, AMS removed/bypassed** | Soft 95A TPU buckles in the AMS feed + long PTFE; it must feed straight to the toolhead. Mandatory on P1S. |
| Drying | **55 °C ≥ 4 h** (eSUN spec), keep in a dry box while printing | TPU is hygroscopic; wet TPU = stringing, bubbles, weak layers. |
| Nozzle | **0.4 mm hardened steel** (you have this) | Fine for TPU. Use a clean/new or cold-pulled nozzle — TPU drags old residue. Do **not** use a 0.2 mm or generic high-flow nozzle for TPU. |
| Extruder | P1S stock direct extruder, external spool, **slow** | eSUN TDS: needs a "short-range" extruder; the P1S direct extruder qualifies if fed from an external spool at low speed. |
| Plate | **Textured PEI**, light IPA wipe | Best TPU grip without over-adhesion; the textured surface releases the flexible part cleanly. |
| Orientation | **Flat on the 28×96 Z-face** (as in `print_plates/`) | Fin Ray cells lie in the build plane → self-supporting, no supports; bending stress runs in-plane (the strong direction). |

---

## 2. The two importable profiles

| File | Type | Inherits (system base) | Shows up for |
|---|---|---|---|
| `profiles/eSUN_eTPU-95A_@P1S_0.4.json` | filament | `Generic TPU @base` | **Bambu Lab P1S 0.4 nozzle** (locked to P1S — the profile bakes in the hardened-nozzle assumption) |
| `profiles/finger_TPU_0.16mm_@P1S_0.4.json` | process | `0.20mm Standard @BBL X1C` | Bambu Lab P1S / P1P / X1C, 0.4 nozzle |

Both are `"from": "User"`, `instantiation: "true"`, and inherit a real Bambu system
profile so any value not overridden resolves cleanly. (The P1S has no dedicated
`@BBL P1S` process; it uses the X1C process via `upward_compatible_machine` — so the
process profile inherits the X1C base, which is correct for the P1S.)

**Import:** Bambu Studio → File → Import → *Import Configs…* → pick both `.json`. They
appear under **User Presets** in the filament and process dropdowns when a P1S 0.4 is
selected. If a profile is rejected on an older Studio build, bump `"version"` to match
your installed profile version (top of your `BBL.json`).

---

## 3. Filament settings — every value + why (`eSUN eTPU-95A @P1S 0.4`)

eSUN TDS recommends nozzle 220–250 °C, bed 45–60 °C, 20–50 mm/s, fan 100%, 4
perimeters, dry 55 °C >4 h. The profile sets:

| Setting | Value | Rationale |
|---|---|---|
| `filament_type` | TPU | — |
| `filament_vendor` | eSUN | — |
| `filament_density` | **1.21 g/cm³** | eSUN TDS (used for weight/cost only). |
| `filament_flow_ratio` | **0.95** | Soft 95A over-extrudes; slight under-flow keeps the 1.2 mm contact wall dimensionally true. |
| `filament_max_volumetric_speed` | **3.0 mm³/s** | P1S TPU ceiling (community 2.5–3.6). The finger's slowest member draws ~1.3 mm³/s, so this is a safety cap, not a bottleneck. |
| `nozzle_temperature` | **235 °C** | Mid of eSUN's 220–250; balances flow against the layer bonding a cyclically-flexed part needs. |
| `nozzle_temperature_initial_layer` | **240 °C** | Hotter first layer = better bed bond on flexible filament. |
| `nozzle_temperature_range_low/high` | 220 / 250 | eSUN bounds. |
| `hot_plate_temp` / `textured_plate_temp` | **45 °C** (initial 45) | eSUN low end; enough TPU adhesion on textured PEI without elephant-foot/over-stick. |
| `cool_plate_temp` | 35 °C | If using a smooth/cool plate instead. |
| `filament_retraction_length` | **0.8 mm** | TPU needs minimal retraction (oozing is managed by temp/speed). 0.8 mm is safe for the P1S direct path; more pulls soft filament into the heatbreak → jams. |
| `filament_retraction_speed` | **30 mm/s** | Slow retract for soft filament. |
| `filament_z_hop` | **0.4 mm** (Auto Lift) | Clears the 0.6 mm grip teeth on travel without stringing across the contact face. |
| `fan_min_speed` / `fan_max_speed` | **50 / 80 %** | **Conservative deviation from eSUN's generic 100%** — NOT claimed optimal. The finger flexes in service; lower fan protects the interlayer (Z) bonds that shear during flex, at the (predicted-safe, 7–8× margin) loads. **Untested under cycling.** If you fatigue-test and it holds, eSUN's 100% is the manufacturer default and may give cleaner ribs/teeth — treat 100% as the validated-once-tested setting. |
| `overhang_fan_speed` | 100 % | Full cooling on any short overhang (rib undersides). |
| `additional_cooling_fan_speed` | 70 % | Aux part fan. |
| `close_fan_the_first_x_layers` | **3** | Fans off for the first 3 layers → strong bed adhesion (critical for the narrow TPU footprint). |
| `fan_cooling_layer_time` / `slow_down_layer_time` | 60 / 8 s | Slow small layers so they cool/bond. |
| `temperature_vitrification` | **30 °C** | Filament soften-point for the slow-down logic (the Bambu Generic-TPU system value — *not* the bed temp). |
| `filament_start_gcode` | reminder note | "External spool, not AMS; dry 55 °C >4 h." |
| `filament_notes` | hardened-nozzle + external-spool + drying reminder | Carried with the profile. |
| `compatible_printers` | **P1S 0.4 only** | Locked to the P1S — the profile assumes the hardened nozzle; don't silently offer it for machines that may have a brass nozzle (TPU wears brass). |

---

## 4. Process (print) settings — every value + why (`Gripper finger TPU 0.16mm`)

The shipped finger has **thin graded walls** (contact 1.2 / rib 1.6 / spine 1.8 mm)
and **0.6 mm grip teeth** at 2.2 mm pitch — the process is tuned to print every wall
**fully solid** (the FEA's 100 %-dense-wall basis) and resolve the teeth/ribs.

| Setting | Value | Rationale |
|---|---|---|
| `layer_height` | **0.16 mm** | Resolves the 2.2 mm-pitch grip teeth and thin ribs cleanly; finer Z also bonds better. |
| `initial_layer_print_height` | 0.20 mm | Robust first layer. |
| `wall_loops` | **5** | Enough loops that every member fills with perimeters (the slicer uses only as many as fit). |
| `line_width` / `outer_wall` / `inner_wall` | **0.40 mm** (all walls) | **Critical:** at 0.40 mm the **1.2 mm contact beam = exactly 3 flush perimeters (0.40×3) — no gap-fill**. The contact beam is the most cyclically-loaded member, and gap-fill on TPU is where layer bonding gets unreliable; flush perimeters avoid it. Ribs 1.6 mm = 4 flush; spine 1.8 mm = 4 + a small 0.2 mm gap-fill (interior, non-critical). At 0.42 mm the contact beam would have been 2 perimeters + a 0.36 mm gap strip — avoided. |
| `wall_generator` | **classic** | Predictable perimeters on thin TPU walls (Arachne adds variable-width gap-fill on near-integer walls). |
| `detect_thin_wall` | 1 | Captures the 1.2 mm contact beam as solid wall. |
| `initial_layer_line_width` / `sparse_infill_line_width` | 0.50 / 0.45 | Wider first layer for adhesion; wider infill is fine (interior). |
| `top/bottom_shell_layers` | **4 / 4** | eSUN-recommended shell count; dense skins on the base floor/cap. |
| `sparse_infill_density` | **100 %** | Matches the FEA assumption (fully-dense walls) and keeps the solid base/bracket and grip-ridge insets dense. The finger is small (~30 g), so 100 % is cheap. |
| `sparse_infill_pattern` | rectilinear | Moot at 100 %. |
| `outer_wall_speed` | **20 mm/s** | Slow walls = clean grip face + the soft filament keeps up. eSUN low end. |
| `inner_wall_speed` | 30 mm/s | — |
| `sparse_infill_speed` | 40 mm/s | eSUN allows faster infill. |
| `internal_solid_infill_speed` | 35 mm/s | — |
| `top_surface_speed` | 20 mm/s | Clean top skins. |
| `initial_layer_speed` | **18 mm/s** | Slow, sure first layer. |
| `travel_speed` | 200 mm/s | Travel can be fast (no extrusion). |
| `default_acceleration` | **3000 mm/s²** | **Reduced from the P1S stock 10000.** Soft TPU lags under high accel → blobs/ringing; lower accel = consistent extrusion. |
| `outer_wall_acceleration` | 1500 mm/s² | Gentle on the visible/grip walls. |
| `initial_layer_acceleration` | 500 mm/s² | Calm first layer. |
| `seam_position` | **back** | Keeps the layer seam **off the grip-ridge contact face** (the object side). |
| `brim_type` / `brim_width` | outer_only / **5 mm** | TPU + narrow footprint needs a brim to not peel. |
| `brim_object_gap` | 0.10 mm | Easy brim removal from the flexible part. |
| `elefant_foot_compensation` | 0.15 mm | With the part's base chamfer, keeps the first layer true. |
| `enable_support` | **0 (off)** | Flat orientation is self-supporting — there's nothing to remove from a compliant truss anyway. |
| `ironing_type` | no ironing | Not needed; would smear the grip teeth. |
| `wall_sequence` | inner → outer | Better outer-wall surface on the grip face. |
| `compatible_printers` | P1S / P1P / X1C 0.4 | P1S visibility. |

---

## 5. FEA re-check for eSUN eTPU-95A (the stats hold)

**eSUN eTPU-95A TDS (V4.0)** — the only published mechanical numbers:

| property | eSUN value | used in FEA | note |
|---|---|---|---|
| Tensile strength | **35 MPa** (GB/T 1040, injection-molded) | strength **25 MPa** | 3D-printed TPU is ~60–85 % of injection-molded → ≈ 21–30 MPa printed. **The FEA's 25 MPa is a realistic *printed* strength**, not arbitrary. |
| Young's / flexural modulus | **not published** ("N/A") | E **40 MPa** (estimate) | bracketed below. |
| Poisson ratio | (not published) | ν **0.42** | typical TPU 0.42–0.48; minor effect. |
| Density | 1.21 g/cm³ | — | — |
| Elongation at break | ≥800 % | — | hugely ductile; failure is fatigue/tear, not brittle yield. |
| Hardness | 95 A | — | — |

**Modulus sensitivity** — because eSUN doesn't publish a modulus, the baseline finger
was re-run at E = 30 / 40 / 60 MPa (printed strength 25 MPa), force-targeted to a 12 N
grasp:

| E (MPa) | small-circle margin | grip | universal score |
|---|---|---|---|
| 30 | 7.7–8.8× | 11–12 N | 0.577 |
| 40 (used) | 7.2–8.2× | 12–13 N | 0.645 |
| 60 | 7.6–8.1× | 12–15 N | 0.622 |

**Conclusion:** at a fixed grip force the **von-Mises margins are essentially
modulus-independent (7–8× across the whole bracket)** — linear elasticity says the
internal stress is set by the *load*, not the stiffness. The modulus only changes how
far the four-bar must close to reach the grip (an actuator-travel detail). So eSUN's
unpublished modulus does **not** change the safety margins or any design conclusion;
the universal-grasp result (0.65) and the scalability band (0.6–1.1×) stand as
published. With the real printed strength (~25 MPa) the finger sits at a **comfortable
7–8× safety margin** at a firm 12 N grip.

Re-run yourself: `eval_finger.py <name> production '{"_E":40,"_strength":25}' screen`
(the harness now accepts `_E` and `_strength` overrides).

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
  enclosure closed and use a brim. (Full tuned profiles for these are out of scope of
  this TPU-focused task — the stock Bambu profiles are a good starting point.)

---

## Sources

- eSUN eTPU-95A Technical Data Sheet V4.0 (Nov 2021) — `esun3d.com` (tensile 35 MPa,
  density 1.21, ≥800 % elong., nozzle 220–250 °C, bed 45–60 °C, fan 100 %, 20–50 mm/s,
  4 perimeters, dry 55 °C >4 h; modulus N/A).
- Bambu Lab P1S TPU guidance — Bambu Lab community forum + vendor guides (external
  spool, hardened-nozzle notes, ~2.5–3.6 mm³/s volumetric, textured PEI, low retraction).
- Bambu Studio profile schema — `github.com/bambulab/BambuStudio`
  `resources/profiles/BBL/{filament,process,machine}` (Generic TPU + 0.20mm Standard
  @BBL X1C + P1S machine profile; key names, `compatible_printers`, inheritance).
- FEA: `fea/UNIVERSAL_FINGER.md`, `fea/SCALABILITY.md`, `fea/scripts/eval_finger.py`.

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
2. **Dry first: 70 °C for 8 h** (Bambu spec). Run it from an **external spool, NOT the
   AMS** — Bambu's own system profile states 95A HF is *"too soft and not compatible
   with the AMS."* Keep it in a dry box while printing.
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
| Spool path | **External spool — NOT the AMS** | Bambu's own `Bambu TPU 95A HF @base` profile states: *"This filament is too soft and not compatible with the AMS."* Feed it straight to the toolhead from an external spool; the soft 95A buckles in the AMS feed + long PTFE. |
| Drying | **70 °C ≥ 8 h** (Bambu spec; or X1-bed 80–90 °C 12 h), keep in a dry box while printing; storage <20 % RH | TPU 95A HF is "highly sensitive to humidity"; wet TPU = stringing, bubbles, weak layers. |
| Nozzle | **0.4 mm hardened steel** (you have this) | Fine for TPU. Use a clean/new or cold-pulled nozzle — TPU drags old residue. Do **not** use a 0.2 mm nozzle for TPU. |
| Extruder | P1S stock direct extruder | HF flows easily; the P1S direct extruder handles it, fed straight from the external spool. |
| Plate | **Textured PEI plate, NO glue** (preferred) | Bambu Wiki TPU guidance: the textured PEI keys TPU mechanically — "excellent adhesion without adhesives," and *"applying glue may cause excessive adhesion."* Keep the bed at **30–35 °C** (low) so the large flat 28×96 finger footprint stays removable; release by cooling, lifting a corner, squirting **IPA** into the gap, then peeling slowly (don't pry a hot part — chips the PEI). **Alternative:** a smooth plate (Cool/Engineering/High-Temp) needs **glue** there as a release barrier — the datasheet's blanket "Bed prep: Glue" line is for those smooth plates, not the textured one. The Engineering plate gives a glossy bottom you don't need on a finger base, so textured-PEI/no-glue is the pick. |
| Orientation | **Flat on the 28×96 face** (as in `print_plates/`) | Fin Ray cells lie in the build plane → self-supporting, no supports; in-plane bending (the grip mechanism) runs in the **strong X-Y direction** (E 9.8 MPa / 27.3 MPa vs the weaker through-Z 7.4 / 22.3). |

---

## 2. The two importable profiles

| File | Type | Inherits (real system preset) | Shows up for |
|---|---|---|---|
| `profiles/Bambu_TPU-95A-HF_@P1S_0.4.json` | filament | **`Bambu TPU 95A HF @BBL P1S`** | **Bambu Lab P1S 0.4 nozzle** |
| `profiles/finger_TPU_0.16mm_@P1S_0.4.json` | process | `0.20mm Standard @BBL X1C` | Bambu Lab P1S / P1P / X1C, 0.4 nozzle |

Both are `"from": "User"`, `instantiation: "true"`, and inherit a real Bambu system
preset so every value not overridden resolves to Bambu's tested defaults.

- **Filament** inherits Bambu's own **`Bambu TPU 95A HF @BBL P1S`** (verified against
  the BambuStudio profile repo). You own the filament, so your Studio already ships
  that preset — the import resolves cleanly and you get Bambu's tested nozzle/flow/
  retraction and the *Direct Drive High Flow* template for free. This preset overrides
  **only** the gripper-specific notes + start g-code (external-spool / textured-PEI /
  drying reminders) and locks `compatible_printers` to P1S 0.4. **Nothing material is
  re-typed**, so there's nothing to drift from Bambu's calibration.
- **Process** inherits `0.20mm Standard @BBL X1C` (the P1S has no dedicated `@BBL P1S`
  process; it uses the X1C process via `upward_compatible_machine`, confirmed present
  in your Studio's process dropdown).

**Import:** Bambu Studio → File → Import → *Import Configs…* → pick both `.json`. They
appear under **User Presets** in the filament and process dropdowns when a P1S 0.4 is
selected.

> **Version must match your installed profiles.** Bambu Studio silently drops configs
> whose `version` is incompatible with the loaded BBL vendor profile ("There are 0
> configs imported. Only non-system and compatible configs"). These files are set to
> **`"version": "2.6.0.5"`** to match BBL profile **02.06.00.05** (Bambu Studio 2.6).
> If your Studio is a different release, set both files' `version` to your installed
> BBL major.minor (Help → About → version, or check `BambuStudio.conf`). The files use
> the exact user-preset shape Studio writes (`from: User`, `inherits`, `*_settings_id`,
> extruder-variant arrays — no `type`/`instantiation`/`setting_id`).

If the filament import ever warns the *parent* preset is missing, your Studio's
TPU-95A-HF system preset name differs — re-point `"inherits"` to the exact name in your
filament dropdown (or duplicate Bambu's preset in Studio and paste the two
`filament_notes`/start-g-code reminders in).

---

## 3. Filament settings — what you inherit + what we override

This preset **inherits `Bambu TPU 95A HF @BBL P1S`** and deliberately re-types
**nothing** mechanical, so the finger prints on Bambu's own tested values (verified
against the BambuStudio profile repo). The inherited values are:

| Setting | Inherited value (Bambu system) | Note |
|---|---|---|
| `nozzle_temperature` / initial layer | **230 °C / 230 °C** | Bambu's tested temp for 95A HF (same for both — no hotter first layer). |
| `filament_flow_ratio` | **1.0** | Bambu's calibrated flow for HF on the P1S. (Don't drop it to "under-extrude for thin walls" without a flow-calibration print — Bambu tuned 1.0.) |
| `filament_max_volumetric_speed` | **12 mm³/s** | The HF headline — ~4× the old eSUN cap (3.0). The finger's slowest member draws ~1.3 mm³/s, so it's a generous ceiling; it's what lets the §4 process speeds rise. |
| `filament_retraction_length` / speed / deretraction | **0.8 mm / 10 mm/s / 10 mm/s** | Bambu's values; minimal, slow retract so soft filament isn't pulled into the heatbreak. |
| `filament_density` | **1.22 g/cm³** | ISO 1183 (weight/cost only). |
| HF flow template, pressure advance, fan curve | inherited | comes with the `Direct Drive High Flow` template the system preset includes. |

We override **only** the non-mechanical reminders, so there's nothing to drift from
Bambu's calibration:

| Override | Value | Why |
|---|---|---|
| `name` | `Bambu TPU 95A HF @P1S 0.4 (gripper fingers)` | identifies the gripper preset. |
| `compatible_printers` | **P1S 0.4 only** | locks it to the hardened-nozzle P1S (TPU wears brass). |
| `filament_start_gcode` / `filament_notes` | external-spool-not-AMS · textured-PEI-no-glue · dry 70 °C 8 h · 0.4 hardened nozzle | carried with the profile so the operator can't miss them. |

> **Cooling note (not overridden — read before a fatigue-critical build):** the finger
> flexes in service, and high part-cooling can weaken the interlayer (Z) bonds (the
> weak 7.4 MPa / 22.3 MPa direction). This preset leaves fan at Bambu's TPU default;
> if you want to protect Z-bonds you can lower max fan to ~50–80 % — **untested under
> cycling**, so treat Bambu's default as the validated setting unless you fatigue-test.

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
| `sparse_infill_pattern` | **`zig-zag`** | Bambu's serialized value for the UI's "Rectilinear" pattern (plain `"rectilinear"` is **not** a valid enum value — Studio silently falls back to `cubic`, which then conflicts with 100 % density). `zig-zag` supports 100 %. Moot at 100 % anyway (solid), but must be a 100 %-capable pattern to avoid the import-time "Cubic doesn't support 100 %" dialog. |
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

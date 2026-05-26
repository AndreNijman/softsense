# motor/cad — every bought + printed actuator-system part, in CAD

Each component referenced by the BOM's actuator-system row is modelled
parametrically here as a `build123d` envelope (cited dimensions, not
manufacturer-equivalent CAD), so the whole gripper-plus-canister-plus-
actuator stack can be assembled, clearance-checked, and rendered in one
file.

## Files

| file | what |
|---|---|
| [`external_parts.py`](external_parts.py) | 13 bought parts: 4 servos (XW540 / XM540 / STS3250 / STS3215), 3" canister (tube + 2 end caps), WetLink penetrator + blank M10 plug, lip seal, goBILDA shaft, KTR MINEX-S magnetic coupling, DIY N52 rotor. Every dimension cited to its primary source in the docstring. |
| [`printed_adapters.py`](printed_adapters.py) | 5 printed parts the BOM names but `gripper.py` doesn't model: `servo_horn_adapter` (dry side), `wet_d_socket` (wet side, mates the gripper coupler), `servo_cradle` (locates servo inside the 3" tube), `cradle_endcap_spacer`. Surfaces the `servo_cradle` design gap the BOM hadn't itemised. |
| [`system_assembly.py`](system_assembly.py) | Integrated assembly. Brings the **existing gripper** (via `gripper.gen_step()`) plus every external + printed part into one Compound. Variants: `T2` (lip-seal, primary), `T3` (magnetic-coupling fallback), `LINEUP` (side-by-side servo choices). Asserts headroom > 0 inside the canister. |
| `output/*.step` | One STEP per part + one per assembly. |
| `output/hero_T2_STS3250.png` | Hero render of the primary integrated assembly. |

## Build everything

```bash
source ~/.cad-venv/bin/activate

# individual parts (smoke test)
python motor/cad/external_parts.py
python motor/cad/printed_adapters.py

# integrated assemblies (T2 PRIMARY first)
GRIPPER_CANISTER_VARIANT=T2 GRIPPER_CANISTER_SERVO=STS3250 \
    python ~/.claude/skills/cad/scripts/step motor/cad/system_assembly.py \
    -o motor/cad/output/hero_T2_STS3250.step

# T3 magnetic-coupling fallback
GRIPPER_CANISTER_VARIANT=T3 python motor/cad/system_assembly.py

# four-servo lineup
GRIPPER_CANISTER_VARIANT=LINEUP python motor/cad/system_assembly.py

# hero render
python ~/.claude/skills/render/scripts/snapshot \
    --input motor/cad/output/hero_T2_STS3250.step \
    --output motor/cad/output/hero_T2_STS3250.png \
    --size-profile assembly
```

## Coordinate frame

The gripper `gen_step()` reorients by +90X so fingers point world +Z.
Every part in `system_assembly.py` is placed in that same world frame:

- fingers at `+Z`
- gripper input D-coupler exits the flange face at world `(x, y, z) = (-12, -11.72, -25)`
- canister axis = world `Z`, hanging straight down from the gripper
- penetrators exit world `-Z` (downward) out of the dry end cap

## Honesty caveats

- All bought-part dims are **datasheet envelopes** for clearance checks,
  not manufacturer-replacement CAD. Caliper-verify before final fit.
- The STS3250 case dims (20 × 54 × 47 mm) were inferred from Feetech
  catalogue cross-reference + distributor photos — OpenELAB's product
  page does not publish them. Tagged APPROXIMATE in the source.
- Blue Robotics end-cap exact flange OD / mating-boss geometry was not
  in the public spec table; we used 98 mm flange OD, 7 mm boss insertion,
  consistent with photos and the 3" series' published `K` screw-PCD of
  ~63.5 mm. CAD package from the BR tech-details download is the authoritative
  source for production drawings.
- The integrated assembly's `assert headroom > 0` confirms the servo +
  cradle + horn-adapter stack fits inside the 240 mm tube with at least
  ~150 mm of cable-bend slack on all four servo options. If you swap
  to a longer servo or shorter tube, the assertion is your sentinel.

## Cross-links

- BOM canister row → `../../BOM.md` (line ~185)
- Architecture rationale → `../ROV_INTEGRATION.md` §2c–§2d
- Selection rationale → `../SELECTION.md`, `../MOTOR_STUDY.md`

#!/usr/bin/env python3
"""
export_parts.py -- Per-part STEP + STL exporter for the geared four-bar gripper.

Reads the assembly from gripper.gen_step() (CLOSED pose), identifies the UNIQUE
printable parts (collapsing geometric duplicates so you don't print more SKUs
than there really are), translates each unique part to the origin, and writes
parts/<name>.step and parts/<name>.stl for each.

A summary table (stdout + parts/MANIFEST.md) lists every part with its print
quantity, suggested material, bounding box and a print-orientation note.

Run:
    cd /home/andre/gripper-cad
    source /home/andre/.cad-venv/bin/activate
    python export_parts.py

NOTE: this script does NOT edit gripper.py. It only imports it.

------------------------------------------------------------------------------
THIS GRIPPER IS NOW FULLY 3D-PRINTED -- ZERO BOUGHT HARDWARE.
The pivot pins are printed PETG-HF HEAT-STAKE pins -- a plain journal pin plus a
separate cap melted onto the pin's stud with a soldering iron (no barbs to break,
no press fits to slide out). The bolted front cover is a snap-clip cover with
integral cantilever clips. Every part in this manifest is printed.

------------------------------------------------------------------------------
De-duplication logic (LABEL-based)
------------------------------------------------------------------------------
gen_step() returns 17 labelled leaf solids in assembled world coordinates:

    enclosure
    drive_arm_R, drive_arm_L
    follower_R,  follower_L
    finger_R,    finger_L
    pin_A_R, pin_A_L, pin_B_R, pin_B_L  (internal axle HEAT-STAKE pins)
    pin_C_R, pin_D_R, pin_C_L, pin_D_L  (finger-pivot HEAT-STAKE pins)
    cap_{A,B,C,D}_{R,L}                  (one melt-on retaining cap per pin -> x8)
    front_cover                          (integral snap clips)
    input_pinion_shaft                   (pinion + shaft + bottom shoulder + D-coupler)

We collapse duplicates by the part LABEL via an explicit map (LABEL_TO_NAME),
NOT by a geometric/bounding-box fingerprint. Mapping by label is unambiguous and
never collides (the old fingerprint approach silently overwrote pins with similar
bounding boxes).

Grouping (25 children -> 12 unique part files):

  * follower_R / follower_L -> one file `follower`, qty 2. A follower is a
    symmetric link bar; left and right are congruent.

  * The 4 internal axle pins (pin_A_R, pin_A_L, pin_B_R, pin_B_L) are one
    geometry -> `melt_pin_axle`, qty 4.

  * The 4 finger-pivot pins split by DEPTH: C reaches the crank layer, D only the
    follower layer, so they are different lengths -> `melt_pin_finger_C` (qty 2)
    and `melt_pin_finger_D` (qty 2). (The old code wrongly merged them.)

  * The 8 melt-on retaining caps are one geometry -> `melt_cap`, qty 8.

  * finger_R / finger_L stay SEPARATE (chiral Fin Ray ribs all slant the same
    way within a finger; a mirror flips the slant -> not superimposable).

  * drive_arm_R / drive_arm_L stay SEPARATE (both are plain gear+arm plates that
    ride on the heat-stake axle pins; drive_arm_L carries the crown gear on its
    +Z face but has no integral shaft).

  * enclosure qty 1, front_cover qty 1, input_pinion_shaft qty 1.

Any label not in the map falls back to its own name (qty 1) so a newly-added
part is still exported and listed instead of being dropped.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent   # script lives in scripts/
sys.path.insert(0, str(REPO_ROOT))                   # so `import gripper` works

# CLOSED pose: must be set BEFORE importing gripper (it reads the env at import).
os.environ["GRIPPER_OPEN"] = "0"

from build123d import export_step, export_stl  # noqa: E402

import gripper  # noqa: E402  -- imported after GRIPPER_OPEN is set

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
# Output dir override (GRIPPER_PARTS_DIR) so a scaled variant (GRIPPER_SCALE) can be
# exported into its own tree, e.g. variants/scale_2.0x/parts, without touching the 1x.
OUT_DIR = Path(os.environ["GRIPPER_PARTS_DIR"]) if os.environ.get("GRIPPER_PARTS_DIR") else REPO_ROOT / "parts"

# STL mesh quality: 0.05 mm linear deviation is the FDM sweet spot -- smooth
# enough for the gear teeth / Fin Ray ribs / snap barbs without bloating the mesh.
STL_TOL = 0.05
STL_ANG_TOL = 0.1

# --------------------------------------------------------------------------
# Label -> unique part file name. This is the SINGLE source of truth for
# de-duplication: every child label maps to the file it belongs to. Multiple
# labels mapping to the same name collapse into one file (qty = how many).
# The first child encountered for a name becomes the canonical instance that
# gets exported; later ones only bump the quantity.
# --------------------------------------------------------------------------
LABEL_TO_NAME = {
    "enclosure": "enclosure",
    "drive_arm_R": "drive_arm_R",
    "drive_arm_L": "drive_arm_L",
    "follower_R": "follower",
    "follower_L": "follower",
    "finger_R": "finger_R",          # chiral -> kept separate
    "finger_L": "finger_L",          # chiral -> kept separate
    "pin_A_R": "melt_pin_axle",      # internal axle heat-stake pins x4 (identical length)
    "pin_A_L": "melt_pin_axle",
    "pin_B_R": "melt_pin_axle",
    "pin_B_L": "melt_pin_axle",
    # finger-pivot heat-stake pins: C (to the crank layer) and D (to the follower
    # layer) sit at different Z depths -> DIFFERENT lengths, so they are two SKUs.
    # (The old single "snap_pin_finger" SKU was the C length, so the 2 D pins did
    # not seat -- fixed here.) x2 each.
    "pin_C_R": "melt_pin_finger_C",
    "pin_C_L": "melt_pin_finger_C",
    "pin_D_R": "melt_pin_finger_D",
    "pin_D_L": "melt_pin_finger_D",
    # one separate melt-on retaining cap, the SAME part on every pin -> qty 8.
    "cap_A_R": "melt_cap", "cap_A_L": "melt_cap",
    "cap_B_R": "melt_cap", "cap_B_L": "melt_cap",
    "cap_C_R": "melt_cap", "cap_C_L": "melt_cap",
    "cap_D_R": "melt_cap", "cap_D_L": "melt_cap",
    "front_cover": "front_cover",
    "input_pinion_shaft": "input_pinion_shaft",  # pinion + shaft + collar + D-coupler
}


def name_for(label: str) -> str:
    """Unique file name for a child label (fallback: the label itself)."""
    return LABEL_TO_NAME.get(label, label)


# --------------------------------------------------------------------------
# Per-part metadata: material + print-orientation note, keyed by the unique
# part NAME. Anything unknown falls back to a sane default so a newly-added
# part still gets exported and listed.
#
# Materials (EVERYTHING is printed -- no bought hardware):
#   PETG / Nylon -> structural body parts (enclosure, arms, followers, cover)
#   PETG         -> snap pins (semi-flexible for the snap barb to flex, but
#                   stronger than TPU so the loaded pivot shank doesn't creep)
#   TPU          -> compliant Fin Ray fingers
# --------------------------------------------------------------------------
def part_meta(name: str):
    """Return (material, print_note) for a given unique part name."""
    if name == "enclosure":
        return ("PETG / Nylon",
                "open cavity face UP on the bed (back flange down); supports "
                "only inside the shaft bore.")
    if name == "front_cover":
        return ("PETG / Nylon",
                "outer face DOWN on the bed, snap clips pointing UP; the clips "
                "print as unsupported cantilevers off the inner face -- no "
                "supports needed.")
    if name == "input_pinion_shaft":
        return ("PA12-GF",
                "print shaft-axis VERTICAL: rotate 90 about X so the shaft stands "
                "up; D-coupler/shoulder end DOWN on the bed (r=5.0mm, wider base), "
                "pinion teeth UP. Shaft cylinder = self-supporting rings; the "
                "bottom shoulder bridges ~1.8mm radially (1-2 layers). SUPPORTLESS. "
                "Installs into the housing FROM BELOW (pinion-first).")
    if name.startswith("drive_arm"):
        return ("PA12-GF",
                "lay the flat gear+arm plate face-down on the bed (5 mm thick). "
                "Both arms ride on the heat-stake axle pins (no integral shaft).")
    if name.startswith("follower"):
        return ("PETG / Nylon",
                "lay the flat link bar face-down on the bed (5 mm thick).")
    if name.startswith("finger"):
        return ("TPU (shore ~95A)",
                "lay the Fin Ray plane FLAT on the bed, RIDGE (contact-face) "
                "side DOWN for clean grip ridges; the 10 mm depth is the Z "
                "height (may want a 90 deg rotate from the exported pose).")
    if name == "melt_cap":
        return ("PETG-HF",
                "tiny cup: print OPEN-END UP (closed crown on the bed) so the "
                "blind pocket needs no bridging; no supports. Slip over a pin's "
                "melt-stud and fuse the crown with a soldering iron.")
    if name.startswith("melt_pin"):
        return ("PETG-HF",
                "stand the pin AXIS VERTICAL, HEAD DOWN, melt-stud UP; no "
                "supports (plain stepped cylinder). melt_pin_finger_C is the long "
                "(crank-layer) pin, melt_pin_finger_D the short (follower-layer) "
                "pin, melt_pin_axle the back-wall pin. After assembly, slip a "
                "melt_cap on the protruding stud and fuse it.")
    # Fallback for any unexpected new part.
    return ("PETG / Nylon",
            "orientation TBD -- inspect and lay the largest flat face on the bed.")


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------
def to_origin(solid):
    """Return a copy translated so its bounding-box min corner sits at (0,0,0).

    Slicers expect each part near the origin; the assembly leaves parts in
    their world poses (e.g. pins offset to their pivot points)."""
    mn = solid.bounding_box().min
    return solid.moved(gripper.Location((-mn.X, -mn.Y, -mn.Z)))


def clean_out_dir():
    """Remove stale per-part STEP/STL so an old naming scheme can't leave
    orphaned files that misrepresent the current design (e.g. the obsolete
    pin_axle/pin_finger from before the snap-pin rename)."""
    if not OUT_DIR.exists():
        return
    for f in OUT_DIR.glob("*.step"):
        f.unlink()
    for f in OUT_DIR.glob("*.stl"):
        f.unlink()


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clean_out_dir()

    asm = gripper.gen_step()
    children = [c for c in asm.children if getattr(c, "label", None)]
    if not children:
        print("ERROR: gen_step() returned no labelled children", file=sys.stderr)
        return 1

    # ---- group children into unique parts BY LABEL ----
    # groups: ordered list of dicts {canonical, name, qty, labels}
    groups = []
    name_index = {}  # unique name -> group dict

    for c in children:
        name = name_for(c.label)
        grp = name_index.get(name)
        if grp is None:
            grp = {"canonical": c, "name": name, "qty": 1, "labels": [c.label]}
            groups.append(grp)
            name_index[name] = grp
        else:
            grp["qty"] += 1
            grp["labels"].append(c.label)

    # ---- export each unique part, translated to origin ----
    rows = []
    for grp in groups:
        name = grp["name"]
        part = to_origin(grp["canonical"])
        bb = part.bounding_box().size
        step_path = OUT_DIR / f"{name}.step"
        stl_path = OUT_DIR / f"{name}.stl"

        try:
            export_step(part, str(step_path))
            export_stl(part, str(stl_path),
                       tolerance=STL_TOL, angular_tolerance=STL_ANG_TOL)
        except Exception as exc:  # keep going if one part fails
            print(f"WARNING: failed to export {name}: {exc}", file=sys.stderr)
            continue

        material, note = part_meta(name)
        rows.append({
            "name": name,
            "qty": grp["qty"],
            "instances": ", ".join(grp["labels"]),
            "printable": "yes",          # everything is printed now
            "material": material,
            "bbox": f"{bb.X:.1f} x {bb.Y:.1f} x {bb.Z:.1f}",
            "note": note,
        })

    # ---- summary table (stdout) ----
    print()
    print("Exported unique gripper parts -> {}".format(OUT_DIR))
    print("Pose: CLOSED (GRIPPER_OPEN=0).  STL tol={} mm.".format(STL_TOL))
    print("FULLY 3D-PRINTED gripper: zero bought hardware -- every part below "
          "is printed.")
    print()
    header = ("{:<16} {:>4} {:<11} {:<18} {:<22}"
              .format("PART", "QTY", "PRINTABLE", "MATERIAL", "BBOX (mm)"))
    print(header)
    print("-" * len(header))
    for r in rows:
        print("{:<16} {:>4} {:<11} {:<18} {:<22}".format(
            r["name"], r["qty"], r["printable"], r["material"], r["bbox"]))
    print()
    print("Print-orientation notes:")
    for r in rows:
        print("  - {}: {}".format(r["name"], r["note"]))
    print()
    n_axle = next((r["qty"] for r in rows if r["name"] == "melt_pin_axle"), 0)
    n_finC = next((r["qty"] for r in rows if r["name"] == "melt_pin_finger_C"), 0)
    n_finD = next((r["qty"] for r in rows if r["name"] == "melt_pin_finger_D"), 0)
    n_cap = next((r["qty"] for r in rows if r["name"] == "melt_cap"), 0)
    print("Pins are PRINTED PETG-HF HEAT-STAKE pivots (melt_pin_axle x{}, "
          "melt_pin_finger_C x{}, melt_pin_finger_D x{}) + melt_cap x{}. No barbs, "
          "no metal: insert each pin, slip a cap on the protruding stud, melt the "
          "cap with a soldering iron.".format(n_axle, n_finC, n_finD, n_cap))
    print("R/L Fin Ray fingers are chiral mirrors -> exported as two separate "
          "files (finger_R, finger_L), each qty 1.")
    print("ZERO bought hardware: every part is 3D-printed.")

    # ---- MANIFEST.md ----
    manifest = OUT_DIR / "MANIFEST.md"
    lines = []
    lines.append("# Gripper print manifest")
    lines.append("")
    lines.append("Generated by `export_parts.py` from `gripper.gen_step()` at the "
                 "**CLOSED** pose (`GRIPPER_OPEN=0`).")
    lines.append("")
    lines.append("**This gripper is FULLY 3D-PRINTED -- zero bought hardware.** "
                 "The pivot pins are printed PETG-HF HEAT-STAKE pins (a separate "
                 "cap is melted onto each pin's stud with a soldering iron) and "
                 "the front cover snaps on with integral cantilever clips. Every "
                 "part below is printed.")
    lines.append("")
    lines.append("STL mesh tolerance: `{} mm` (linear), `{}` (angular). "
                 "Each part is translated so its bounding-box min corner is at "
                 "the origin.".format(STL_TOL, STL_ANG_TOL))
    lines.append("")
    lines.append("| Part | Qty | Printable | Material | Bbox (mm) | Instances | "
                 "Print orientation |")
    lines.append("|------|-----|-----------|----------|-----------|-----------|"
                 "-------------------|")
    for r in rows:
        lines.append("| `{}.step`/`.stl` | {} | {} | {} | {} | {} | {} |".format(
            r["name"], r["qty"], r["printable"], r["material"], r["bbox"],
            r["instances"], r["note"]))
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- **Everything is printed.** No screws, no dowel pins, no "
                 "bought fasteners. `melt_pin_axle` (x{}), `melt_pin_finger_C` "
                 "(x{}, the long crank-layer pin), `melt_pin_finger_D` (x{}, the "
                 "short follower-layer pin) and `melt_cap` (x{}) are PETG-HF "
                 "HEAT-STAKE pivots (shank radius PIN_R = {} mm). Retention is a "
                 "geometric melted head, so nothing flexes (no broken barbs) and "
                 "nothing relies on friction (no pins sliding out)."
                 .format(n_axle, n_finC, n_finD, n_cap, gripper.PIN_R))
    lines.append("- **Heat-stake pins: print HEAD DOWN, axis vertical, no "
                 "supports.** Insert the pin, slip a `melt_cap` over the "
                 "protruding stud (open end toward the part), and fuse the cap "
                 "crown with a soldering iron -> a rivet head wider than the bore. "
                 "Finger pins (C/D) are staked at the arm/follower-eye bottom on "
                 "the bench; axle pins (A/B) are staked on the EXTERIOR back face. "
                 "See docs/ASSEMBLY.md.")
    lines.append("- **Front cover snaps on (no screws).** It carries 4 integral "
                 "cantilever clips (2 per long side) that hook into the body "
                 "side-wall windows. Print outer-face DOWN, clips UP. Push on "
                 "to click; flex the 4 hooks outward to release.")
    lines.append("- **Fingers are chiral.** `finger_R` and `finger_L` share a "
                 "bounding box / volume but are mirror images (Fin Ray ribs all "
                 "slant the same way within a finger), so both are exported. "
                 "Print in TPU, ridge side down.")
    lines.append("- **Followers are identical.** A follower is a symmetric link "
                 "bar; left and right are the same part -> one file, qty 2.")
    lines.append("- **Drive arms differ.** `drive_arm_L` carries the crown gear "
                 "on its +Z face (right-angle stage); `drive_arm_R` is a plain "
                 "gear+arm plate. Both arms ride on the heat-stake axle pins -- "
                 "neither has an integral shaft. The input shaft is a separate part: "
                 "`input_pinion_shaft`.")
    lines.append("- **input_pinion_shaft** (pinion + vertical shaft + bottom "
                 "shoulder + D-coupler) prints shaft-axis VERTICAL (rotate 90° "
                 "about X from exported pose): D-coupler/shoulder end on bed "
                 "(r=5.0 mm, wider base), pinion teeth up. Supportless. Installs "
                 "into the housing from below, pinion-first.")
    manifest.write_text("\n".join(lines) + "\n")
    print("Wrote {}".format(manifest))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

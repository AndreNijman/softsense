#!/usr/bin/env python3
"""
export_parts.py -- Per-part STEP + STL exporter for the geared four-bar gripper.

Reads the assembly from gripper.gen_step() (CLOSED pose), identifies the UNIQUE
printable parts (collapsing geometric duplicates so you don't print or buy more
SKUs than there really are), translates each unique part to the origin, and
writes parts/<name>.step and parts/<name>.stl for each.

A summary table (stdout + parts/MANIFEST.md) lists every part with its print
quantity, suggested material, bounding box and a print-orientation note.

Run:
    cd /home/andre/gripper-cad
    source /home/andre/.cad-venv/bin/activate
    python export_parts.py

NOTE: this script does NOT edit gripper.py. It only imports it.

------------------------------------------------------------------------------
De-duplication logic
------------------------------------------------------------------------------
gen_step() returns 14 labelled leaf solids in assembled world coordinates:

    enclosure
    drive_arm_R, drive_arm_L
    follower_R,  follower_L
    finger_R,    finger_L
    pin_A_R, pin_B_R, pin_B_L          (short hidden axle pins, visible=False)
    pin_C_R, pin_D_R, pin_C_L, pin_D_L (tall capped finger pins, visible=True)

Several of these are the SAME geometry placed at different positions:

  * follower_R / follower_L -- a follower is a straight link_bar (rod + two
    equal eyes). Such a bar is symmetric across its own long axis, so its
    mirror image is congruent. -> 1 unique part, qty 2.

  * The pins come from pin() in only TWO distinct shapes:
        - axle pin  (visible=False): pin_A_R, pin_B_R, pin_B_L  -> qty 3
        - finger pin (visible=True): pin_C_R, pin_D_R, pin_C_L, pin_D_L -> qty 4
    Each group is one shape repeated at different (x,y) translations.
    -> 2 unique pin parts. Both are REPRESENTATIONS of off-the-shelf M-screws,
       flagged "hardware, do not print".

We detect duplicates with a translation-invariant geometric fingerprint
(volume, surface area, sorted bounding-box extents, rounded). The FIRST part in
each group becomes the canonical instance that we export; the rest just bump the
quantity. This collapses 14 children -> 8 unique part files automatically, and
adapts gracefully if a part is added/removed (e.g. a later front_cover).

The Fin Ray fingers are the deliberate exception: finger_R / finger_L share a
fingerprint (mirroring preserves volume/area/AABB) but are CHIRAL -- the ribs
slant the same direction within a finger, so a mirror flips the slant and the
two are NOT superimposable. We force them to stay as two separate files.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# CLOSED pose: must be set BEFORE importing gripper (it reads the env at import).
os.environ["GRIPPER_OPEN"] = "0"

from build123d import export_step, export_stl  # noqa: E402

import gripper  # noqa: E402  -- imported after GRIPPER_OPEN is set

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
OUT_DIR = Path(__file__).resolve().parent / "parts"

# STL mesh quality: 0.05 mm linear deviation is the FDM sweet spot -- smooth
# enough for the gear teeth / Fin Ray ribs without bloating the mesh.
STL_TOL = 0.05
STL_ANG_TOL = 0.1

# Parts whose geometry happens to fingerprint-match but must NOT be merged
# (chiral mirrors). Keyed by label.
FORCE_UNIQUE = {"finger_R", "finger_L"}

# --------------------------------------------------------------------------
# Per-part metadata: material + print-orientation note, keyed by a stable
# "kind" derived from the label. Anything unknown falls back to a sane default
# so a newly-added part (e.g. front_cover) still gets exported and listed.
#
# Materials:
#   PETG / Nylon -> structural body parts (enclosure, arms, followers)
#   TPU          -> compliant Fin Ray fingers
#   hardware     -> pins are REPRESENTATIONS of bought M-screws: DO NOT PRINT
# --------------------------------------------------------------------------
def part_meta(label: str):
    """Return (material, print_note) for a given part label."""
    if label == "enclosure":
        return ("PETG / Nylon",
                "open cavity face UP on the bed (back flange down); supports "
                "only inside the shaft bore.")
    if label == "front_cover":
        return ("PETG / Nylon",
                "flat-face down on the bed.")
    if label == "drive_arm_L":
        return ("PETG / Nylon",
                "REORIENT MANUALLY: the 40 mm integral input shaft sticks out "
                "along +Z; lay the shaft horizontal so the flat gear/arm face "
                "is on the bed.")
    if label.startswith("drive_arm"):
        return ("PETG / Nylon",
                "lay the flat gear+arm plate face-down on the bed (5 mm thick).")
    if label.startswith("follower"):
        return ("PETG / Nylon",
                "lay the flat link bar face-down on the bed (5 mm thick).")
    if label.startswith("finger"):
        return ("TPU (shore ~95A)",
                "lay the Fin Ray plane flat on the bed, contact-face/ridge side "
                "down for clean ridges; print the 10 mm depth as the Z height "
                "(may want a 90 deg rotate from the exported pose).")
    if label.startswith("pin"):
        return ("stainless hardware (M-screw)",
                "HARDWARE -- do not print; buy the equivalent dowel pin / "
                "socket-head cap screw.")
    # Fallback for any unexpected new part.
    return ("PETG / Nylon",
            "orientation TBD -- inspect and lay the largest flat face on the bed.")


def is_hardware(label: str) -> bool:
    return label.startswith("pin")


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------
def fingerprint(solid):
    """Translation/mirror-invariant geometric fingerprint of a solid.

    (volume, surface area, sorted bbox extents) rounded. Two solids that are
    the same shape -- regardless of where they sit -- share this fingerprint.
    Note: a mirror image ALSO shares it, which is why chiral parts must be
    forced unique separately (see FORCE_UNIQUE)."""
    bb = solid.bounding_box().size
    extents = tuple(sorted((round(bb.X, 2), round(bb.Y, 2), round(bb.Z, 2))))
    return (round(solid.volume, 1), round(solid.area, 1)) + extents


def to_origin(solid):
    """Return a copy translated so its bounding-box min corner sits at (0,0,0).

    Slicers expect each part near the origin; the assembly leaves parts in
    their world poses (e.g. pins offset to their pivot points)."""
    mn = solid.bounding_box().min
    return solid.moved(gripper.Location((-mn.X, -mn.Y, -mn.Z)))


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    asm = gripper.gen_step()
    children = [c for c in asm.children if getattr(c, "label", None)]
    if not children:
        print("ERROR: gen_step() returned no labelled children", file=sys.stderr)
        return 1

    # ---- group children into unique parts ----
    # groups: list of dicts {canonical, qty, labels, fingerprint}
    groups = []
    fp_index = {}  # fingerprint -> group dict (only for mergeable parts)

    for c in children:
        label = c.label
        fp = fingerprint(c)
        if label in FORCE_UNIQUE or fp not in fp_index:
            grp = {"canonical": c, "name": label, "qty": 1,
                   "labels": [label], "fp": fp}
            groups.append(grp)
            # Only register mergeable (non-forced-unique) fingerprints so chiral
            # mirrors never absorb each other.
            if label not in FORCE_UNIQUE:
                fp_index[fp] = grp
        else:
            grp = fp_index[fp]
            grp["qty"] += 1
            grp["labels"].append(label)

    # Give merged groups a friendlier, side-agnostic name. The canonical was
    # named after the first instance encountered (e.g. "pin_A_R", "follower_R"),
    # which is misleading once it represents a quantity of identical parts.
    for grp in groups:
        if grp["name"].startswith("pin"):
            # axle pins are short (~14 mm), finger pins are tall (~23.6 mm)
            zext = grp["canonical"].bounding_box().size.Z
            grp["name"] = "pin_axle" if zext < 18.0 else "pin_finger"
        elif grp["qty"] > 1 and grp["name"] not in FORCE_UNIQUE:
            # A non-chiral part merged from R/L (e.g. "follower_R") -> drop the
            # trailing "_R"/"_L" so the file name doesn't imply one side.
            base = grp["name"]
            if base.endswith("_R") or base.endswith("_L"):
                grp["name"] = base[:-2]

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

        material, note = part_meta(grp["labels"][0])
        printable = "no (hardware)" if is_hardware(grp["labels"][0]) else "yes"
        rows.append({
            "name": name,
            "qty": grp["qty"],
            "instances": ", ".join(grp["labels"]),
            "printable": printable,
            "material": material,
            "bbox": f"{bb.X:.1f} x {bb.Y:.1f} x {bb.Z:.1f}",
            "note": note,
        })

    # ---- summary table (stdout) ----
    print()
    print("Exported unique gripper parts -> {}".format(OUT_DIR))
    print("Pose: CLOSED (GRIPPER_OPEN=0).  STL tol={} mm.".format(STL_TOL))
    print()
    header = ("{:<14} {:>4} {:<13} {:<28} {:<20}"
              .format("PART", "QTY", "PRINTABLE", "MATERIAL", "BBOX (mm)"))
    print(header)
    print("-" * len(header))
    for r in rows:
        print("{:<14} {:>4} {:<13} {:<28} {:<20}".format(
            r["name"], r["qty"], r["printable"], r["material"], r["bbox"]))
    print()
    print("Print-orientation notes:")
    for r in rows:
        print("  - {}: {}".format(r["name"], r["note"]))
    print()
    print("Pins (pin_axle x{}, pin_finger x{}) are REPRESENTATIONS of bought "
          "M-screws / dowel pins -- do NOT print them.".format(
              next((r["qty"] for r in rows if r["name"] == "pin_axle"), 0),
              next((r["qty"] for r in rows if r["name"] == "pin_finger"), 0)))
    print("R/L Fin Ray fingers are chiral mirrors -> exported as two separate "
          "files (finger_R, finger_L), each qty 1.")

    # ---- MANIFEST.md ----
    manifest = OUT_DIR / "MANIFEST.md"
    lines = []
    lines.append("# Gripper print manifest")
    lines.append("")
    lines.append("Generated by `export_parts.py` from `gripper.gen_step()` at the "
                 "**CLOSED** pose (`GRIPPER_OPEN=0`).")
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
    lines.append("- **Pins are hardware, not prints.** `pin_axle` (x{}) and "
                 "`pin_finger` (x{}) model off-the-shelf stainless dowel pins / "
                 "socket-head cap screws (PIN_R = {} mm). Source the real "
                 "fasteners; the STEP/STL are reference only.".format(
                     next((r["qty"] for r in rows if r["name"] == "pin_axle"), 0),
                     next((r["qty"] for r in rows if r["name"] == "pin_finger"), 0),
                     gripper.PIN_R))
    lines.append("- **Fingers are chiral.** `finger_R` and `finger_L` share a "
                 "bounding box / volume but are mirror images (Fin Ray ribs all "
                 "slant the same way within a finger), so both are exported.")
    lines.append("- **Followers are identical.** A follower is a symmetric link "
                 "bar; left and right are the same part -> one file, qty 2.")
    lines.append("- **Drive arms differ.** `drive_arm_L` carries the integral "
                 "input shaft + D-coupler; `drive_arm_R` rides on a separate "
                 "axle pin. Two distinct parts.")
    lines.append("- **drive_arm_L needs manual reorientation** for printing "
                 "(40 mm shaft sticks out along Z in the exported pose).")
    manifest.write_text("\n".join(lines) + "\n")
    print("Wrote {}".format(manifest))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
make_print_set.py -- Build a print-ready `output/` folder where every file name
encodes [part name + quantity to print + FINAL material].

Reads the already-exported clean-named STLs in `parts/` (produced by
`export_parts.py`) and copies each into `output/` renamed to:

    <name>_x<qty>_<material>.stl

so the filename alone tells you what it is, how many to print, and what to print
it in -- no need to open a BOM. Pure stdlib (no venv needed).

The (qty, material) map below is the single source of truth and matches BOM.md §5
(FINAL build materials): the rigid body/gear parts are PA12-GF, ALL the pivot pins
and caps are PETG-HF heat-stake parts (a cap is melted onto each pin's stud with a
soldering iron), and the two Fin Ray fingers are ether-based TPU ~95A.

Run:
    python3 make_print_set.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent   # script lives in scripts/
PARTS = ROOT / "parts"
OUT = ROOT / "output"

# part stl basename -> (quantity per assembly, FINAL material code)
# Materials per BOM.md §5. The ether requirement for the fingers is baked into
# the filename on purpose (ester-TPU hydrolyzes underwater -- UNDERWATER §1).
PRINT_SET = {
    "enclosure":          (1, "PA12-GF"),
    "front_cover":        (1, "PA12-GF"),
    "drive_arm_R":        (1, "PA12-GF"),
    "drive_arm_L":        (1, "PA12-GF"),
    "input_pinion_shaft": (1, "PA12-GF"),
    "follower":           (2, "PA12-GF"),
    "finger_R":           (1, "etherTPU-95A"),
    "finger_L":           (1, "etherTPU-95A"),
    # heat-stake pins + caps: all PETG-HF (one pin material; mushrooms cleanly
    # under a soldering iron). axle pins switched from PA12-GF (glass-filled, melts
    # poorly) to PETG-HF. finger pins split C (long) / D (short) -- different lengths.
    "melt_pin_axle":      (4, "PETG-HF"),
    "melt_pin_finger_C":  (2, "PETG-HF"),
    "melt_pin_finger_D":  (2, "PETG-HF"),
    "melt_cap":           (8, "PETG-HF"),
}


def main() -> int:
    if not PARTS.exists():
        print(f"ERROR: {PARTS} not found -- run export_parts.py first.",
              file=sys.stderr)
        return 1

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    rows = []
    total_prints = 0
    for name, (qty, material) in PRINT_SET.items():
        src = PARTS / f"{name}.stl"
        if not src.exists():
            print(f"ERROR: missing {src} -- run export_parts.py first.",
                  file=sys.stderr)
            return 1
        dst_name = f"{name}_x{qty}_{material}.stl"
        shutil.copy2(src, OUT / dst_name)
        rows.append((dst_name, qty, material))
        total_prints += qty

    # index file inside the folder
    idx = ["# Print set (output/)", "",
           "Each filename is `<part>_x<qty>_<material>.stl`: the part, how many "
           "to print, and the FINAL material to print it in (BOM.md §5).", "",
           "| File | Qty | Material |", "|------|-----|----------|"]
    for dst_name, qty, material in rows:
        idx.append(f"| `{dst_name}` | {qty} | {material} |")
    idx += ["",
            f"**{len(rows)} unique parts, {total_prints} physical prints total.**",
            "",
            "Materials: PA12-GF (rigid body/gear parts), PETG-HF (all 8 pivot "
            "pins + 8 melt-on caps -- heat-staked with a soldering iron), "
            "ether-based TPU ~95A (the 2 Fin Ray fingers -- never ester-TPU, it "
            "hydrolyzes underwater).",
            ""]
    (OUT / "README.md").write_text("\n".join(idx))

    print(f"Wrote {len(rows)} files to {OUT}")
    for dst_name, qty, material in rows:
        print(f"  {dst_name}")
    print(f"Total physical prints: {total_prints}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
(FINAL build materials): everything rigid is PA12-GF, the four finger snap pins
are the lone PETG-HF exception, the two Fin Ray fingers are ether-based TPU ~95A.

Run:
    python3 make_print_set.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
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
    "snap_pin_axle":      (4, "PA12-GF"),
    "snap_pin_finger":    (4, "PETG-HF"),
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
            "Materials: PA12-GF (all rigid parts), PETG-HF (the 4 finger snap "
            "pins only -- they flex on insertion), ether-based TPU ~95A (the 2 "
            "Fin Ray fingers -- never ester-TPU, it hydrolyzes underwater).",
            ""]
    (OUT / "README.md").write_text("\n".join(idx))

    print(f"Wrote {len(rows)} files to {OUT}")
    for dst_name, qty, material in rows:
        print(f"  {dst_name}")
    print(f"Total physical prints: {total_prints}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

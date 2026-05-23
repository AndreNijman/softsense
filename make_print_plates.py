#!/usr/bin/env python3
"""
make_print_plates.py -- Build "drop into your slicer" print plates for the
fully-3D-printed underwater gripper.

What it does
------------
1. Ensures per-part STLs exist in `parts/` (runs `export_parts.py` if any are
   missing, unless --no-export).
2. Loads each unique part, ROTATES it to its chosen SUPPORTLESS print
   orientation (see ORIENT below), drops it onto Z=0, and writes the oriented
   single part to `print_plates/oriented/<part>.stl`.
3. Replicates each part by its print QUANTITY and SHELF-PACKS the instances onto
   build plates for a common bed (default 256 x 256 mm, ~5 mm spacing),
   grouping by MATERIAL on SEPARATE plates: rigid (PA12-GF), petg (PETG-HF
   finger pins), tpu (flexible fingers).
4. Writes each plate as one combined STL: print_plates/plate_rigid_N.stl,
   print_plates/plate_petg_N.stl, print_plates/plate_tpu_N.stl.
5. Prints a summary: which part on which plate, per-part oriented bbox, count,
   overhang/support area in the chosen orientation, and (if a slicer CLI is on
   PATH) est. time + filament per plate.

This script is READ-ONLY on gripper.py / DFM.md / the *.md docs. It only reads
parts/*.stl (produced by export_parts.py) and writes into print_plates/.

IMPORTANT -- REGENERATE AFTER ANY GEOMETRY CHANGE
-------------------------------------------------
The plates are derived artifacts. If gripper.py geometry changes (e.g. the
snap-fit / pin agent finalizes the barb), the integrator MUST re-run:
    python export_parts.py     # regenerate parts/*.stl
    python make_print_plates.py
to refresh both the per-part STLs and the plates. Stale plates do not reflect
the current design.

Run:
    cd /home/andre/gripper-cad
    source /home/andre/.cad-venv/bin/activate
    python make_print_plates.py            # 256x256 bed
    python make_print_plates.py --bed 220 220
    python make_print_plates.py --no-export # use existing parts/*.stl
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parent
PARTS_DIR = ROOT / "parts"
OUT_DIR = ROOT / "print_plates"
ORIENTED_DIR = OUT_DIR / "oriented"

# --------------------------------------------------------------------------
# Per-part print plan.
#   rot        : list of (axis, degrees) rotations applied (in order) to take the
#                exported pose -> the chosen SUPPORTLESS print orientation.
#   qty        : how many of this part to print (matches parts/MANIFEST.md).
#   group      : 'rigid' (PETG/ASA/Nylon) or 'tpu' (flexible fingers).
#   note       : one-line orientation rationale.
# Rotations are about the GLOBAL axes; after rotating, the part is re-seated so
# its bounding-box min corner sits at (0,0,0) (min Z on the bed).
# --------------------------------------------------------------------------
ORIENT = {
    "enclosure": dict(
        rot=[], qty=1, group="rigid",
        note="as-exported: open slot/cavity face +Z up, solid floor (drain bores) "
             "on bed. Drains print as vertical bores. Back flange (+Y) may want a "
             "few support pillars/skirt -- see PRINTING.md.",
    ),
    "drive_arm_R": dict(
        rot=[], qty=1, group="rigid",
        note="as-exported: flat gear+arm plate (5 mm) face-down, pivot axis "
             "vertical. Eyes/teeth print as concentric perimeters. Supportless.",
    ),
    "drive_arm_L": dict(
        # drive_arm_L is now a plain gear+arm plate (crown on its +Z face).
        # No integral shaft -- it rides on a snap-pin axle like drive_arm_R.
        # As-exported the flat plate face is on the bed (5 mm thick). Supportless.
        rot=[], qty=1, group="rigid",
        note="as-exported: flat gear+arm plate (5 mm) face-down, pivot axis "
             "vertical. Crown gear on +Z face prints as concentric rings. "
             "No integral shaft. Supportless.",
    ),
    "follower": dict(
        rot=[], qty=2, group="rigid",
        note="as-exported: flat link bar (5 mm) face-down, both pivot eyes "
             "axis-vertical. Supportless.",
    ),
    "finger_R": dict(
        rot=[], qty=1, group="tpu",
        note="as-exported: lying flat on a 28x96 Z-face, build height 10 mm; Fin "
             "Ray cells in the X-Y build plane (self-supporting). Grip ridges on "
             "the -X contact face print as in-plane perimeters. Supportless.",
    ),
    "finger_L": dict(
        rot=[], qty=1, group="tpu",
        note="as-exported: lying flat on a 28x96 Z-face, build height 10 mm; Fin "
             "Ray cells in the X-Y build plane (self-supporting). Supportless.",
    ),
    "front_cover": dict(
        # Exported pose has the flat outer plate face at +Z (top) and the snap
        # clips hanging toward -Z. Flip 180 about X so the outer face is on the
        # bed and the clips point +Z up (print as self-supporting vertical beams).
        rot=[("x", 180)], qty=1, group="rigid",
        note="flip 180 about X: flat outer face on bed, 4 snap clips point +Z up "
             "as self-supporting vertical cantilevers. Hook underlips are small "
             "bridges. Supportless.",
    ),
    "snap_pin_axle": dict(
        # Exported pose: head disc at +Z (top), barb/lead-in tip at -Z (bottom).
        # Flip 180 about X => head flange on the bed (anchors the print), barb
        # tip points +Z up so the lead-in cone narrows as it rises (printable).
        rot=[("x", 180)], qty=4, group="rigid",
        note="flip 180 about X: head flange on bed, barb tip up. Lead-in cone "
             "narrows going up (self-supporting); '+' split slot is vertical. "
             "Supportless. PETG, slow + low cooling at the barb. "
             "Qty 4: pin_A_R, pin_A_L, pin_B_R, pin_B_L.",
    ),
    "input_pinion_shaft": dict(
        # The part is a vertical shaft (model-Y axis in the assembly) with a pinion
        # disc at one end (meshes the crown, r_tip=3.72mm), a capture collar
        # mid-shaft (r=5.8mm), and a D-coupler at the other end (actuator
        # interface, r=5.0mm shoulder + flat-D cut).
        # After export & to_origin, the shaft long axis runs along Y (33mm); the
        # D-coupler/shoulder end is at y=0, the pinion end is at y=33mm.
        # To print shaft-axis VERTICAL we need to stand it up: rotate 90 about X
        # so Y -> Z. After this rotation, the D-coupler/shoulder end (r=5.0mm)
        # lands on the bed -- wider, flatter base than the pinion teeth (r=3.72mm).
        #   * Shaft cylinder prints as self-supporting concentric rings (33mm tall).
        #   * Capture collar (r=5.8mm) is a slightly wider annular ring; its
        #     underside ramps outward ~1.8mm -> bridges 1-2 layers. Supportless.
        #   * Pinion teeth at the top print as a small-diameter gear crown. Fine.
        #   * D-flat slot on the bottom is a vertical rectangular cutout; it faces
        #     upward in the part (bed end) but the flat is a straight vertical wall
        #     facing inward -> no unsupported overhang on the bed side.
        rot=[("x", 90)], qty=1, group="rigid",
        note="rotate 90° about X: shaft-axis VERTICAL, D-coupler/shoulder end on "
             "bed (r=5.0mm, wider than pinion r=3.72mm), pinion teeth at top. "
             "Shaft is a 33mm self-supporting cylinder. Collar mid-shaft is a "
             "~1.8mm radial bridge (1-2 layers). SUPPORTLESS. PA12-GF. "
             "100% infill + 4+ perimeters for torsional shaft strength.",
    ),
    "snap_pin_finger": dict(
        # PETG-HF (final material): the split snap barb needs ductility; PA12-GF
        # is too brittle and would crack on insertion. Pull-out load is carried
        # by the PA12-GF counterbore shoulder, not the pin -> separate PETG plate.
        rot=[("x", 180)], qty=4, group="petg",
        note="flip 180 about X: head flange on bed, barb tip up. Locking lip is "
             "a ~0.7 mm bridge the printer spans in 1-2 layers. Supportless. "
             "PETG-HF (NOT PA12-GF -- barb must flex), slow + low cooling at the barb.",
    ),
}

# print order within a group (so the summary / plate reads logically)
RIGID_ORDER = ["enclosure", "front_cover", "drive_arm_L", "drive_arm_R",
               "follower", "snap_pin_axle", "input_pinion_shaft"]
PETG_ORDER = ["snap_pin_finger"]
TPU_ORDER = ["finger_R", "finger_L"]


# --------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------
def _rot_matrix(axis: str, deg: float) -> np.ndarray:
    a = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}[axis]
    return trimesh.transformations.rotation_matrix(math.radians(deg), a)


def oriented_mesh(name: str) -> trimesh.Trimesh:
    """Load parts/<name>.stl, apply the chosen rotations, seat min-corner at
    origin (min Z on the bed)."""
    m = trimesh.load(PARTS_DIR / f"{name}.stl", force="mesh")
    for axis, deg in ORIENT[name]["rot"]:
        m.apply_transform(_rot_matrix(axis, deg))
    m.apply_translation(-m.bounds[0])  # min corner -> (0,0,0)
    return m


def overhang_area(m: trimesh.Trimesh, thr_deg: float = 45.0) -> float:
    """mm^2 of down-facing surface steeper than thr_deg from horizontal (i.e.
    needing support), excluding the first-layer bed contact."""
    thr = math.cos(math.radians(thr_deg))
    n = m.face_normals
    a = m.area_faces
    fc = m.triangles.mean(axis=1)
    zmin = m.bounds[0][2]
    need = (n[:, 2] < -thr) & (fc[:, 2] > zmin + 0.4)
    return float(a[need].sum())


# --------------------------------------------------------------------------
# Shelf packing (descending width, left->right, wrap to new shelf, new plate)
# --------------------------------------------------------------------------
def shelf_pack(items, bed_x, bed_y, spacing, margin=5.0):
    """items: list of dicts with 'mesh','name','idx' and footprint w(x),d(y).
    Returns list of plates; each plate is a list of placements
    {name, idx, mesh, x, y} where (x,y) is the min-corner XY offset on the bed.
    Parts taller/wider than the bed raise ValueError."""
    # sort by footprint width desc, then depth desc, for tight shelves
    order = sorted(items, key=lambda it: (-it["w"], -it["d"]))
    plates = []

    def new_plate():
        return dict(placements=[], cursor_x=margin, cursor_y=margin,
                    shelf_h=0.0)

    plate = new_plate()
    for it in order:
        w, d = it["w"], it["d"]
        if w > bed_x - 2 * margin or d > bed_y - 2 * margin:
            raise ValueError(
                f"part {it['name']} footprint {w:.0f}x{d:.0f} exceeds bed "
                f"{bed_x}x{bed_y} (margin {margin})")
        # fit on current shelf?
        if plate["cursor_x"] + w > bed_x - margin:
            # wrap to next shelf
            plate["cursor_y"] += plate["shelf_h"] + spacing
            plate["cursor_x"] = margin
            plate["shelf_h"] = 0.0
        # fit on plate (vertical)?
        if plate["cursor_y"] + d > bed_y - margin:
            plates.append(plate)
            plate = new_plate()
        x = plate["cursor_x"]
        y = plate["cursor_y"]
        plate["placements"].append(dict(name=it["name"], idx=it["idx"],
                                        mesh=it["mesh"], x=x, y=y,
                                        w=w, d=d))
        plate["cursor_x"] += w + spacing
        plate["shelf_h"] = max(plate["shelf_h"], d)
    if plate["placements"]:
        plates.append(plate)
    return plates


def build_plate_mesh(plate):
    """Concatenate all placements into one mesh, each moved to its (x,y)."""
    parts = []
    for p in plate["placements"]:
        m = p["mesh"].copy()
        m.apply_translation([p["x"], p["y"], 0.0])
        parts.append(m)
    return trimesh.util.concatenate(parts)


# --------------------------------------------------------------------------
# Optional slicer CLI
# --------------------------------------------------------------------------
SLICERS = ["prusa-slicer", "prusa-slicer-console", "PrusaSlicer",
           "orca-slicer", "OrcaSlicer", "superslicer", "slic3r", "CuraEngine"]


def find_slicer():
    for s in SLICERS:
        p = shutil.which(s)
        if p:
            return p
    return None


def slice_estimate(slicer, stl_path, layer=0.2):
    """Best-effort: slice to a temp gcode and grep the time/filament estimate.
    Returns (time_str, filament_str) or (None, None) if it fails."""
    try:
        out = Path("/tmp") / (Path(stl_path).stem + ".gcode")
        cmd = [slicer, "--export-gcode", "--layer-height", str(layer),
               "-o", str(out), str(stl_path)]
        subprocess.run(cmd, capture_output=True, timeout=300, check=False)
        if not out.exists():
            return None, None
        txt = out.read_text(errors="ignore")
        t = f = None
        for line in txt.splitlines():
            low = line.lower()
            if "estimated printing time" in low and t is None:
                t = line.split("=")[-1].strip()
            if "filament used [g]" in low and f is None:
                f = line.split("=")[-1].strip()
        return t, f
    except Exception:
        return None, None


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bed", nargs=2, type=float, default=[256.0, 256.0],
                    metavar=("X", "Y"), help="bed size mm (default 256 256)")
    ap.add_argument("--spacing", type=float, default=5.0,
                    help="gap between parts mm (default 5)")
    ap.add_argument("--no-export", action="store_true",
                    help="use existing parts/*.stl, do not run export_parts.py")
    ap.add_argument("--layer", type=float, default=0.2,
                    help="layer height for slicer estimate (default 0.2)")
    args = ap.parse_args()
    bed_x, bed_y = args.bed

    # 1. ensure parts exist
    needed = list(ORIENT.keys())
    missing = [n for n in needed if not (PARTS_DIR / f"{n}.stl").exists()]
    if missing and not args.no_export:
        print(f"parts/ missing {missing}; running export_parts.py ...")
        subprocess.run([sys.executable, str(ROOT / "export_parts.py")],
                       check=True)
    elif missing:
        print(f"ERROR: missing parts {missing} and --no-export set", file=sys.stderr)
        return 1

    # clean output (derived artifact)
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    ORIENTED_DIR.mkdir(parents=True, exist_ok=True)

    # 2. orient each unique part, write oriented single STL, gather per-part data
    per_part = {}
    items_by_group = {"rigid": [], "petg": [], "tpu": []}
    for name in needed:
        m = oriented_mesh(name)
        trimesh.exchange.export.export_mesh(m, str(ORIENTED_DIR / f"{name}.stl"))
        ext = m.extents
        oh = overhang_area(m)
        per_part[name] = dict(
            ext=ext, overhang=oh, area=float(m.area_faces.sum()),
            vol=float(m.volume), qty=ORIENT[name]["qty"],
            group=ORIENT[name]["group"], note=ORIENT[name]["note"])
        # replicate by qty for packing
        for k in range(ORIENT[name]["qty"]):
            items_by_group[ORIENT[name]["group"]].append(dict(
                name=name, idx=k + 1, mesh=m,
                w=float(ext[0]), d=float(ext[1])))

    # 3. pack each group onto plates
    group_plates = {}
    for group in ("rigid", "petg", "tpu"):
        if items_by_group[group]:
            group_plates[group] = shelf_pack(
                items_by_group[group], bed_x, bed_y, args.spacing)
        else:
            group_plates[group] = []

    # 4. write combined plate STLs
    plate_files = []  # (label, path, placements)
    for group in ("rigid", "petg", "tpu"):
        for i, plate in enumerate(group_plates[group], 1):
            label = f"plate_{group}_{i}"
            path = OUT_DIR / f"{label}.stl"
            mesh = build_plate_mesh(plate)
            trimesh.exchange.export.export_mesh(mesh, str(path))
            plate_files.append((label, path, plate["placements"]))

    # 5. summary
    slicer = find_slicer()
    print()
    print("=" * 74)
    print("PRINT PLATES  (bed {:.0f} x {:.0f} mm, {:.0f} mm spacing)".format(
        bed_x, bed_y, args.spacing))
    print("=" * 74)
    print("Slicer CLI on PATH: {}".format(slicer if slicer else "NONE "
          "(no time/filament estimate; mesh-only)"))
    print()

    # per-part oriented table
    hdr = "{:<17}{:<6}{:<7}{:<22}{:>12}".format(
        "PART", "QTY", "GROUP", "ORIENTED BBOX (mm)", "SUPPORT mm2")
    print(hdr)
    print("-" * len(hdr))
    for group, order in (("rigid", RIGID_ORDER), ("petg", PETG_ORDER), ("tpu", TPU_ORDER)):
        for name in order:
            if name not in per_part:
                continue
            d = per_part[name]
            e = d["ext"]
            print("{:<17}{:<6}{:<7}{:<22}{:>12.0f}".format(
                name, d["qty"], d["group"],
                f"{e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f}", d["overhang"]))
    print()

    # plate layout
    print("PLATE LAYOUT")
    print("-" * 40)
    for label, path, placements in plate_files:
        counts = {}
        for p in placements:
            counts[p["name"]] = counts.get(p["name"], 0) + 1
        used_x = max((p["x"] + p["w"]) for p in placements)
        used_y = max((p["y"] + p["d"]) for p in placements)
        max_z = max(per_part[p["name"]]["ext"][2] for p in placements)
        contents = ", ".join(f"{n} x{c}" for n, c in counts.items())
        print(f"  {label}.stl  ({len(placements)} parts, "
              f"bbox {used_x:.0f} x {used_y:.0f} x {max_z:.0f} mm)")
        print(f"      {contents}")
        if slicer:
            t, f = slice_estimate(slicer, path, args.layer)
            if t or f:
                print(f"      est: time={t or '?'}  filament={f or '?'}")
    print()

    # totals
    n_plates = len(plate_files)
    n_parts = sum(d["qty"] for d in per_part.values())
    tot_vol = sum(per_part[n]["vol"] * per_part[n]["qty"] for n in per_part)
    print(f"TOTAL: {n_parts} printed parts on {n_plates} plate(s); "
          f"~{tot_vol/1000:.1f} cm3 of material (solid volume, before walls/infill).")
    print(f"Oriented single STLs: {ORIENTED_DIR}/<part>.stl  ({len(per_part)} files)")
    print(f"Combined plate STLs:  {OUT_DIR}/plate_*.stl  ({n_plates} files)")
    print()
    print("REGENERATE these plates after ANY gripper.py geometry change:")
    print("    python export_parts.py && python make_print_plates.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

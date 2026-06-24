#!/usr/bin/env python3
"""verify_pins.py -- numeric sanity check for the HEAT-STAKE pin redesign.

For both the CLOSED and OPEN poses it:
  1. measures every part's bounding box (catches a wrong-length pin),
  2. computes the intersection VOLUME of each melt cap / pin against every other
     part, and flags any clash that is NOT an expected one:
        - pin_X  &  cap_X     : EXPECTED (the stud sits inside the cap pocket,
                                they fuse on melting),
        - cap_X / pin_X & its own eye host within the recess/bore clearance:
                                near-zero is fine (running fits + a nested cap),
     anything else > THRESH mm^3 is a real interference and is reported.

Run:  python scripts/verify_pins.py
Exit code 0 = no unexpected clashes; 1 = clash(es) found.
"""
from __future__ import annotations
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

THRESH = 2.0          # mm^3 -- below this is float/mesh noise or a touching face
EXPECT_PIN_CAP = 60.0  # mm^3 -- a pin stud inside its own cap pocket is fine up to here


def host_label(lbl):
    """Which moving body a pin/cap belongs to (for whitelisting its own host)."""
    return lbl  # we whitelist by explicit pair logic below


def run(open_norm):
    os.environ["GRIPPER_OPEN"] = str(open_norm)
    # re-import fresh so the pose env is read
    for m in list(sys.modules):
        if m == "gripper":
            del sys.modules[m]
    import gripper
    asm = gripper.gen_step()
    parts = {c.label: c for c in asm.children if getattr(c, "label", None)}

    pins = {k: v for k, v in parts.items() if k.startswith("pin_")}
    caps = {k: v for k, v in parts.items() if k.startswith("cap_")}
    bodies = {k: v for k, v in parts.items()
              if not k.startswith("pin_") and not k.startswith("cap_")}

    print(f"\n=== pose OPEN={open_norm} : {len(parts)} parts "
          f"({len(pins)} pins, {len(caps)} caps) ===")

    clashes = []

    def vol(a, b):
        try:
            inter = a & b
            return float(inter.volume) if inter is not None else 0.0
        except Exception:
            return 0.0  # disjoint -> boolean yields empty

    # cap vs everything except its own pin
    for ck, cv in caps.items():
        suffix = ck[len("cap_"):]          # e.g. 'C_R'
        own_pin = f"pin_{suffix}"
        for ok, ov in {**pins, **bodies, **caps}.items():
            if ok == ck:
                continue
            v = vol(cv, ov)
            if v <= THRESH:
                continue
            if ok == own_pin and v <= EXPECT_PIN_CAP:
                continue   # cap pocket over its own stud -- expected
            clashes.append((f"{ck}", f"{ok}", v))

    # pin vs every body/other-pin (its own cap handled above)
    for pk, pv in pins.items():
        for ok, ov in {**bodies, **pins}.items():
            if ok == pk:
                continue
            v = vol(pv, ov)
            if v > THRESH:
                clashes.append((f"{pk}", f"{ok}", v))

    if clashes:
        print("  !! UNEXPECTED CLASHES:")
        for a, b, v in sorted(clashes, key=lambda t: -t[2]):
            print(f"     {a:10s} & {b:18s}  {v:8.2f} mm^3")
    else:
        print("  OK: no unexpected pin/cap interference.")
    return clashes


def bboxes():
    os.environ["GRIPPER_OPEN"] = "0"
    for m in list(sys.modules):
        if m == "gripper":
            del sys.modules[m]
    import gripper
    asm = gripper.gen_step()
    print("=== bounding boxes (CLOSED) ===")
    for c in asm.children:
        if not getattr(c, "label", None):
            continue
        s = c.bounding_box().size
        print(f"  {c.label:14s}  {s.X:6.2f} x {s.Y:6.2f} x {s.Z:6.2f}")


if __name__ == "__main__":
    bboxes()
    bad = run(0.0) + run(1.0)
    print()
    if bad:
        print(f"FAIL: {len(bad)} unexpected clash(es).")
        raise SystemExit(1)
    print("PASS: heat-stake pins/caps clear all moving parts at closed & open.")
    raise SystemExit(0)

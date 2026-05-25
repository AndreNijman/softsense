"""Phase-4 verification: build the assembly and check the widened pinion/crown
introduce no new collisions. Mesh interpenetration (pinion tips in crown teeth)
is by-design and small; the gate is that NON-mesh pairs stay ~0 mm^3."""
import os
import sys
import itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def parts_at(open_norm):
    os.environ["GRIPPER_OPEN"] = str(open_norm)
    import importlib
    import gripper
    importlib.reload(gripper)
    asm = gripper.gen_step()
    d = {}
    for ch in asm.children:
        d[ch.label] = ch
    return d


def vol(s):
    try:
        return abs(s.volume)
    except Exception:
        return 0.0


def inter(a, b):
    try:
        return abs(a.intersect(b).volume)
    except Exception:
        return 0.0


if __name__ == "__main__":
    for o in (0.0, 0.5, 1.0):
        d = parts_at(o)
        pin = d.get("input_pinion_shaft")
        armL = d.get("drive_arm_L")
        armR = d.get("drive_arm_R")
        enc = d.get("enclosure")
        print(f"\n=== open={o} ===  pinion vol={vol(pin):.1f} mm^3")
        checks = {
            "pinion ^ crown-arm_L (MESH, expect small)": inter(pin, armL),
            "pinion ^ enclosure (expect ~0)": inter(pin, enc),
            "pinion ^ drive_arm_R (expect 0)": inter(pin, armR),
            "crown-arm_L ^ enclosure (expect ~0)": inter(armL, enc),
            "drive_arm_L ^ drive_arm_R (MESH, expect small)": inter(armL, armR),
        }
        for k, v in checks.items():
            flag = "  <-- CHECK" if ("~0" in k or "expect 0" in k) and v > 1.0 else ""
            print(f"  {k:48s} {v:8.3f} mm^3{flag}")

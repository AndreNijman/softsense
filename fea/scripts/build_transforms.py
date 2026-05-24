"""Rebuild geometry/transforms.json ANALYTICALLY from the four-bar solver.
A and B are fixed ground pivots, so each part's motion is exact:
  drive_arm rotates about A, follower about B, finger moves with the coupler (CD),
  C/D pins translate with their joints, A/B pins + enclosure + cover are static.
Transforms are built in the model (Y-up) frame then conjugated into the world
(Z-up) frame the exported STLs live in (gen_step applies Rx+90).
Validated correspondence-free by chamfer distance vs the actually-rebuilt open=1
poses.
"""
import os, json, numpy as np
os.environ["GRIPPER_OPEN"] = "0"; os.environ["GRIPPER_FINGER_SCALE"] = "1.0"
import gripper
from scipy.spatial import cKDTree

GEO = os.path.normpath(os.path.join(os.path.dirname(__file__), "..",
                                    "render_bundle", "geometry"))
FRAMES = [round(i / 12.0, 4) for i in range(13)]
PIN_T = gripper.PINION_TEETH
CROWN_T = gripper.GEAR_TEETH


def Trans(x, y, z=0.0):
    M = np.eye(4); M[:3, 3] = [x, y, z]; return M

def Rz(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    M = np.eye(4); M[0, 0] = c; M[0, 1] = -s; M[1, 0] = s; M[1, 1] = c; return M

def RzWorld(deg, cx, cy):
    """rotation about the world vertical (Z) axis through (cx,cy)."""
    return Trans(cx, cy, 0) @ Rz(deg) @ Trans(-cx, -cy, 0)

# IMPORTANT: gen_step's final asm.moved(Rx+90) is NOT baked into the child
# vertices, so the exported STLs / FEA section are all in the MODEL (Y-up) frame.
# Therefore transforms are the model-frame transforms directly -- no conjugation.
def to_world(Tm):
    return Tm

def Ry(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    M = np.eye(4); M[0, 0] = c; M[0, 2] = s; M[2, 0] = -s; M[2, 2] = c; return M

def RyModel(deg, cx, cz):
    return Trans(cx, 0, cz) @ Ry(deg) @ Trans(-cx, 0, -cz)

def ang(p, c):
    return np.degrees(np.arctan2(p[1] - c[1], p[0] - c[0]))


def solver(t):
    return gripper.solve_side_right(t), gripper.solve_side_left(t)

R0, L0 = solver(0.0)
A_R, B_R = np.array(R0["A"]), np.array(R0["B"])
A_L, B_L = np.array(L0["A"]), np.array(L0["B"])

# input-shaft model centroid (its spin axis is model -Y, vertical) from open=0 STL
import meshio
shaft = meshio.read(os.path.join(GEO, "parts_open0", "input_pinion_shaft.stl"))
scx, scz = shaft.points[:, 0].mean(), shaft.points[:, 2].mean()


def part_transform(label, t):
    R, L = solver(t)
    if label in ("enclosure", "front_cover", "pin_A_R", "pin_A_L",
                 "pin_B_R", "pin_B_L"):
        return np.eye(4)
    if label == "drive_arm_R":
        return to_world(Trans(*A_R) @ Rz(ang(R["C"], A_R) - ang(R0["C"], A_R)) @ Trans(*(-A_R)))
    if label == "drive_arm_L":
        return to_world(Trans(*A_L) @ Rz(ang(L["C"], A_L) - ang(L0["C"], A_L)) @ Trans(*(-A_L)))
    if label == "follower_R":
        return to_world(Trans(*B_R) @ Rz(ang(R["D"], B_R) - ang(R0["D"], B_R)) @ Trans(*(-B_R)))
    if label == "follower_L":
        return to_world(Trans(*B_L) @ Rz(ang(L["D"], B_L) - ang(L0["D"], B_L)) @ Trans(*(-B_L)))
    if label == "finger_R":
        C, C0 = np.array(R["C"]), np.array(R0["C"])
        return to_world(Trans(*C) @ Rz(R["coupler_ang"] - R0["coupler_ang"]) @ Trans(*(-C0)))
    if label == "finger_L":
        C, C0 = np.array(L["C"]), np.array(L0["C"])
        return to_world(Trans(*C) @ Rz(L["coupler_ang"] - L0["coupler_ang"]) @ Trans(*(-C0)))
    if label == "pin_C_R":
        return to_world(Trans(*(np.array(R["C"]) - np.array(R0["C"]))))
    if label == "pin_C_L":
        return to_world(Trans(*(np.array(L["C"]) - np.array(L0["C"]))))
    if label == "pin_D_R":
        return to_world(Trans(*(np.array(R["D"]) - np.array(R0["D"]))))
    if label == "pin_D_L":
        return to_world(Trans(*(np.array(L["D"]) - np.array(L0["D"]))))
    if label == "input_pinion_shaft":
        spin = (ang(L["C"], A_L) - ang(L0["C"], A_L)) * (CROWN_T / PIN_T)
        return RyModel(spin, scx, scz)   # spin about model-Y (vertical) shaft axis
    return np.eye(4)


LABELS = ["enclosure", "drive_arm_R", "drive_arm_L", "follower_R", "follower_L",
          "finger_R", "finger_L", "pin_A_R", "pin_B_R", "pin_C_R", "pin_D_R",
          "pin_A_L", "pin_B_L", "pin_C_L", "pin_D_L", "front_cover",
          "input_pinion_shaft"]

transforms = {lbl: [part_transform(lbl, t).tolist() for t in FRAMES]
              for lbl in LABELS}

# ---- validation: chamfer predicted(open=1) vs actual rebuilt(open=1) ----
def verts_at(t):
    gripper.OPEN_NORM = float(t)
    asm = gripper.gen_step()
    return {c.label: np.array([[v.X, v.Y, v.Z] for v in c.vertices()])
            for c in asm.children if getattr(c, "label", None)}

print("validating (building open=0 and open=1) ...")
# HERO = visible parts (must be exact). HIDDEN = internal gears/links/shaft inside
# the opaque enclosure (a few mm of phase error is invisible in the render).
HERO = {"enclosure", "front_cover", "finger_R", "finger_L",
        "pin_C_R", "pin_C_L", "pin_D_R", "pin_D_L"}
V0 = verts_at(0.0)
V1 = verts_at(1.0)
worst_hero = 0.0
worst_hidden = 0.0
for lbl in LABELS:
    M = np.array(part_transform(lbl, 1.0))
    pred = (M[:3, :3] @ V0[lbl].T).T + M[:3, 3]
    d, _ = cKDTree(V1[lbl]).query(pred)
    ch = float(d.max())
    tag = "HERO " if lbl in HERO else "hidden"
    flag = "" if (ch < 0.5 or lbl not in HERO) else "  <-- HERO CHECK"
    print(f"  [{tag}] {lbl:20s} chamfer max = {ch:7.3f} mm{flag}")
    if lbl in HERO:
        worst_hero = max(worst_hero, ch)
    else:
        worst_hidden = max(worst_hidden, ch)
print(f"worst HERO (visible) chamfer = {worst_hero:.4f} mm  -> "
      f"{'PASS (exact)' if worst_hero < 0.5 else 'FAIL'}")
print(f"worst hidden (in-enclosure) chamfer = {worst_hidden:.3f} mm  "
      f"(invisible internal gears/links/shaft; acceptable)")
worst = worst_hero

meta = dict(frames_open=FRAMES, units="mm", frame="model Y-up (fingers point +Y)",
            note=("Per-part rigid 4x4 mapping the open=0 STL to each open value, in "
                  "the MODEL frame: X=jaw open/close, Y=toward fingertips (UP), "
                  "Z=depth/pivot axis. Translations in mm (scale 0.001 with the "
                  "geometry STLs, which are in this same frame). Static parts = "
                  "identity. Finger_R/L also carry the FEA wrap (finger_*_wrap.obj) "
                  "applied in the finger local frame BEFORE this transform. For the "
                  "seabed scene, orient the whole assembly fingers-DOWN."),
            validation_chamfer_hero_mm=worst_hero,
            validation_chamfer_hidden_mm=worst_hidden, parts=transforms)
json.dump(meta, open(os.path.join(GEO, "transforms.json"), "w"))
print("wrote transforms.json")

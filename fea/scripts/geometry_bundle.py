"""Export the Blender geometry bundle:
  - per-part STL at the open=0 world pose (parts/ inside the bundle)
  - transforms.json: each part's rigid 4x4 transform per open frame (rel. to open=0),
    recovered by Kabsch with a residual check that PROVES the motion is rigid.
The Fin Ray finger additionally carries the FEA wrap (finray_morph.npz) on top of
its rigid transform -- documented in the prompt.
"""
import os, json, numpy as np
os.environ["GRIPPER_OPEN"] = "0"
os.environ["GRIPPER_FINGER_SCALE"] = "1.0"
import gripper
from build123d import export_stl

OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..",
                                    "render_bundle", "geometry"))
PARTS = os.path.join(OUT, "parts_open0")
os.makedirs(PARTS, exist_ok=True)


def asm_at(t):
    gripper.OPEN_NORM = float(t)        # gen_step reads this module global
    return gripper.gen_step()


def parts_of(asm):
    return {c.label: c for c in asm.children if getattr(c, "label", None)}


def verts(solid):
    return np.array([[v.X, v.Y, v.Z] for v in solid.vertices()], dtype=float)


def kabsch(P, Q):
    """Rigid transform mapping P->Q (Q ~ R@P + t). Returns R,t,rmsd."""
    cP, cQ = P.mean(0), Q.mean(0)
    H = (P - cP).T @ (Q - cQ)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1.0, 1.0, d])
    R = Vt.T @ D @ U.T
    t = cQ - R @ cP
    resid = np.sqrt(np.mean(np.sum(((R @ P.T).T + t - Q) ** 2, axis=1)))
    return R, t, resid


FRAMES = [round(i / 12.0, 4) for i in range(13)]      # open = 0 .. 1, 13 samples

print("building open=0 reference assembly ...")
asm0 = asm_at(0.0)
P0 = parts_of(asm0)
labels = list(P0.keys())
print(f"{len(labels)} parts: {labels}")

# export each part at its open=0 world pose
for lbl, solid in P0.items():
    export_stl(solid, os.path.join(PARTS, f"{lbl}.stl"))
print(f"wrote {len(P0)} STLs to {PARTS}")

V0 = {lbl: verts(s) for lbl, s in P0.items()}

transforms = {lbl: [] for lbl in labels}
max_resid = 0.0
worst = None
for t in FRAMES:
    Pt = parts_of(asm_at(t))
    for lbl in labels:
        s = Pt.get(lbl)
        Vt = verts(s)
        if Vt.shape != V0[lbl].shape:
            # correspondence broke -> identity, flag
            M = np.eye(4); rr = -1.0
        else:
            R, tr, rr = kabsch(V0[lbl], Vt)
            M = np.eye(4); M[:3, :3] = R; M[:3, 3] = tr
        transforms[lbl].append(M.tolist())
        if rr > max_resid:
            max_resid, worst = rr, (lbl, t)
    print(f"  open={t:.3f} done")

print(f"max Kabsch rmsd = {max_resid:.4e} mm  (worst {worst}) "
      f"-> {'RIGID ok' if max_resid < 1e-3 else 'CHECK: non-rigid/corr break'}")

meta = dict(
    frames_open=FRAMES,
    units="mm",
    note=("Each transform maps the part's open=0 STL to its pose at that open "
          "value (4x4 row-major, world). Static parts ~ identity. Finger_R/L "
          "also carry the FEA wrap from fea/finray_morph.npz (apply in the "
          "finger's local frame BEFORE this rigid transform). Assembly is in "
          "Z-up world frame (fingers +Z); for the seabed scene orient fingers "
          "DOWN."),
    kabsch_max_rmsd_mm=max_resid,
    parts=transforms,
)
with open(os.path.join(OUT, "transforms.json"), "w") as fh:
    json.dump(meta, fh)
print("wrote transforms.json")

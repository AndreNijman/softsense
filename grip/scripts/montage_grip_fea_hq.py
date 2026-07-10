"""High-quality 3D FEA array of every grip-texture family (VTK-rendered).

Same physics as montage_grip_fea_3d.py (genuine 3D voxel FEM on each champion
relief, object presses + shears the post tops), but each panel is rendered in VTK
— smoothed surface, Phong studio lighting, anti-aliasing — then composited into a
labelled grid coloured by von Mises (turbo, shared scale). Shipped crosshatch in
gold.

Usage:  python grip/scripts/montage_grip_fea_hq.py [out.png]
"""
import os, sys, json, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from voxel_fea import solve_texture, P_NORM, MU
from vtk_render import render_panel

ITER = os.path.join(HERE, "..", "iterations")
_pos = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = _pos[0] if _pos else os.path.join(
    HERE, "..", "..", "renders", "grip_fea_3d_array_hq.png")

A = 0.13                       # voxel size (mm); VTK smoothing hides the rest
FAMILIES = [
    ("crosshatch_champ.json", "crosshatch",      "crosshatch",           False),
    ("conc_champ.json",       "concentric",      "concentric",           False),
    ("hexpad_champ.json",     "hexpad",          "hexpad",               False),
    ("chevron_champ.json",    "chevron",         "chevron",              False),
    ("dimple_champ.json",     "dimple",          "dimple",               False),
    ("ridge_champ.json",      "ridge",           "ridge",                False),
    ("hier_champ.json",       "hierarchical",    "hierarchical",         False),
    ("SHIP_crosshatch.json",  "crosshatch_ship", "crosshatch (shipped)", True),
]
NROWS, NCOLS = 2, 4
BG = (0.965, 0.965, 0.972)
GOLD_BG = (0.999, 0.961, 0.839)

# --- solve all (cached) -----------------------------------------------------
CACHE = os.path.join(ITER, "_hqcache")
os.makedirs(CACHE, exist_ok=True)
_KEYS = ("coords", "U", "fnodes", "fvm", "vm", "h", "L", "base_h", "root_vm", "peak_vm")
print(f"3D voxel FEA per family (a={A} mm)...")
panels = []
for fn, fam, title, ship in FAMILIES:
    d = json.load(open(os.path.join(ITER, fn)))
    cf = os.path.join(CACHE, f"{fam}_a{A}.npz"); t = time.time()
    if os.path.exists(cf):
        z = np.load(cf); S = {k: (z[k] if z[k].shape else float(z[k])) for k in _KEYS}
        src = "cache"
    else:
        S = solve_texture(fam, d["params"], a=A)
        np.savez(cf, **{k: S[k] for k in _KEYS}); src = f"{time.time()-t:.1f}s"
    S.update(title=title, ship=ship, score=d.get("score"),
             label=d["label"].replace("xhatch", "crosshatch"))
    panels.append(S)
    print(f"  + {title:22s} faces={len(S['fnodes']):6d} peak={float(S['peak_vm']):.2f} "
          f"root~{float(S['root_vm']):.2f} MPa ({src})")

VMAX = float(np.percentile(np.concatenate([p["vm"] for p in panels]), 98))
DEF = 0.45 / max(np.abs(p["U"]).max() for p in panels)
print(f"shared vmax={VMAX:.2f} MPa  shown deformation ×{DEF:.2f}")

# --- VTK render (load fraction s -> 8 panel images, fixed camera) -----------
def render_all(s):
    """Render every panel at grip-load fraction s: deform ×(DEF·s), colour by s·vM."""
    return [render_panel(p, VMAX, DEF*s, size=(900, 760), sload=s,
                         bg=(GOLD_BG if p["ship"] else BG)) for p in panels]

print("VTK rendering panels...")
imgs0 = render_all(1.0)                   # static = full load
for p, im in zip(panels, imgs0): p["img"] = im

# --- compose labelled grid --------------------------------------------------
C_TITLE, C_HDR, C_CAP = "#141414", "#15506e", "#666"
C_LABEL, C_GOLD, C_GOLDBR = "#222", "#b8860b", "#e6a700"
PW, PH = 3.35, 2.95
LM, RM, TOP, BOT, GX, GY = 0.15, 0.15, 1.05, 0.95, 0.06, 0.62
W = LM + NCOLS*PW + (NCOLS-1)*GX + RM
H = TOP + NROWS*PH + (NROWS-1)*GY + BOT
fig = plt.figure(figsize=(W, H), dpi=100, facecolor="#f6f6f8")

def ax_at(x, y, w, h): return fig.add_axes([x/W, 1-(y+h)/H, w/W, h/H])

ims = []
for k, P in enumerate(panels):
    r, c = divmod(k, NCOLS)
    px = LM + c*(PW+GX); py = TOP + r*(PH+GY)
    ax = ax_at(px, py, PW, PH)
    ims.append(ax.imshow(P["img"])); ax.set_xticks([]); ax.set_yticks([])
    win = P["ship"]
    for sp in ax.spines.values():
        sp.set_visible(win); sp.set_color(C_GOLDBR); sp.set_linewidth(3)
    ttl = ("★ SHIPPED — " if win else "") + P["title"]
    geom = P["label"].split(" ", 1)[1] if " " in P["label"] else P["label"]
    ax.set_title(f"{ttl}\n{geom} · score {P['score']:.2f} · root {P['root_vm']:.1f} MPa",
                 fontsize=9.0, color=(C_GOLD if win else C_LABEL),
                 fontweight=("bold" if win else "normal"), pad=3, linespacing=1.3)

sm = plt.cm.ScalarMappable(cmap=plt.cm.turbo, norm=plt.Normalize(0, VMAX))
cax = fig.add_axes([0.31, (BOT-0.50)/H, 0.38, 0.018])
cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
cb.set_label("von Mises stress (MPa) — shared scale", color=C_CAP, fontsize=10)
cb.ax.tick_params(colors=C_CAP, labelsize=8.5); cb.outline.set_edgecolor("#999")

fig.text(0.5, 1-0.34/H, "Grip textures in 3D — real pattern + its FEA stress  (high quality)",
         ha="center", va="center", fontsize=22, color=C_TITLE, fontweight="bold")
fig.text(0.5, 1-0.66/H,
         f"genuine 3D voxel finite-element solve on each champion relief · 5×5 mm patch to scale · "
         f"object presses + shears the tops (p={P_NORM} MPa, μ={MU}) · von Mises, deformation ×{DEF:.1f}",
         ha="center", va="center", fontsize=11, color=C_HDR)
fig.text(0.5, 0.02, "Bambu TPU 95A HF  E≈9.8 MPa, σ≈27.3 MPa, ν=0.42 · 8-node brick FEM, base clamped, "
         "surface smoothed for display · stress concentrates at the post roots (the durability limit)",
         ha="center", va="center", fontsize=8.5, color=C_CAP)

fig.savefig(OUT, dpi=200, facecolor="#f6f6f8")
print(f"WROTE  {OUT}  ({os.path.getsize(OUT)/1e6:.1f} MB)")

# --- optional HQ load-ramp GIF (the textures being FEA'd; camera fixed) ------
if "--anim" in sys.argv:
    from matplotlib.animation import FuncAnimation, PillowWriter
    OUT_GIF = OUT.rsplit(".", 1)[0] + ".gif"
    def smooth(t): return t*t*(3-2*t)                       # smoothstep ease
    up = [smooth(t) for t in np.linspace(0, 1, 16)]
    loads = up + [1.0]*6 + [smooth(t) for t in np.linspace(1, 0, 10)]   # press·hold·release (loops)
    sub = fig.text(0.5, 1-0.90/H, "", ha="center", va="center", fontsize=11,
                   color="#15506e", fontweight="bold")
    def upd(kf):
        s = loads[kf]
        for im, img in zip(ims, render_all(s)):
            im.set_data(img)
        sub.set_text(f"grip load {s*100:3.0f}%  —  posts shear, von Mises builds at the roots")
        print(f"  frame {kf+1}/{len(loads)}  load={s*100:.0f}%")
        return ims
    print(f"Rendering {len(loads)}-frame HQ load ramp...")
    an = FuncAnimation(fig, upd, frames=len(loads), blit=False)
    an.save(OUT_GIF, writer=PillowWriter(fps=14), savefig_kwargs={"facecolor": "#f6f6f8"}, dpi=95)
    print(f"WROTE  {OUT_GIF}  ({os.path.getsize(OUT_GIF)/1e6:.1f} MB)")

"""Montage of EVERY grip-texture family + its Tier-2 FEA into one synchronized GIF.

The grip study iterated SEVEN texture families (ridge, crosshatch, chevron, hexpad,
dimple, concentric, hierarchical), each swept by an agent against the wet-object
battery to a champion geometry. This renders each family's champion cross-section,
runs the SAME Tier-2 2D plane-strain contact/durability FEA on it (reusing
texture_fea.py), and tiles them to-scale as one animated array: every post-set is
loaded by a common grip load (normal pressure + tangential shear) ramped in sync,
coloured by von Mises on a shared scale, so root-stress / durability reads at a
glance. The shipped texture (conservative printable crosshatch) is highlighted.

Common test load (fair across geometries): p = 0.20 MPa normal, mu = 1.0 shear.
Linear-elastic, so the load ramp is U(s)=s*U_full, vM(s)=s*vM_full (one solve each).

Usage:  python grip/scripts/montage_grip_iterations.py [out.gif]
"""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from matplotlib.patches import Rectangle
from matplotlib.animation import FuncAnimation, PillowWriter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from texture_fea import (plane_strain_D, assemble, build_mesh, vonmises_at_nodes,
                         orphan_dofs, E_TPU, NU)
import scipy.sparse.linalg as spla

ITER = os.path.join(HERE, "..", "iterations")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    HERE, "..", "..", "renders", "grip_iterations_fea_array.gif")

# --- the seven families (champion JSON) + the shipped conservative crosshatch ---
# (json file, family title, shipped?)  ordered by surrogate score, ship last.
FAMILIES = [
    ("conc_champ.json",       "concentric",   False),
    ("hier_champ.json",       "hierarchical", False),
    ("crosshatch_champ.json", "crosshatch",   False),
    ("hexpad_champ.json",     "hexpad",       False),
    ("chevron_champ.json",    "chevron",      False),
    ("ridge_champ.json",      "ridge",        False),
    ("dimple_champ.json",     "dimple",       False),
    ("SHIP_crosshatch.json",  "crosshatch (shipped)", True),
]
NCOLS = 4

# --- common test load + mesh resolution -------------------------------------
P_NORM = 0.20      # MPa normal pressure (compression)
MU     = 1.0       # shear coefficient -> tangential traction tau = mu*p
BASE_H = 1.0       # substrate slab under the posts
WIN_W  = 6.0       # physical window width (mm) -> finer textures repeat more
EX     = 0.05      # element size (mm)

def quad_tris(elems):
    """Split each Q4 into two triangles (for tripcolor gouraud)."""
    t = []
    for a, b, c, d in elems:
        t.append([a, b, c]); t.append([a, c, d])
    return np.array(t)

def solve_family(w, g, h):
    """Build the post cross-section, apply common normal+shear load on the post
    tops with the base clamped, return rest nodes, triangles, full-load U, vM."""
    pitch = w + g
    n_pitch = max(2, int(round(WIN_W / pitch)))
    nodes, elems, T = build_mesh(w, g, h, base_h=BASE_H, n_pitch=n_pitch, ex=EX)
    D = plane_strain_D(E_TPU, NU)
    K = assemble(nodes, elems, D)
    ndof = 2 * len(nodes)
    top_y = T["top_y"]
    ref = np.unique(elems.ravel())
    top = np.array([n for n in np.where(np.abs(nodes[:, 1] - top_y) < 1e-6)[0] if n in ref])
    base = np.where(nodes[:, 1] < 1e-6)[0]
    fixed = np.concatenate([2 * base, 2 * base + 1, orphan_dofs(nodes, elems)])
    F = np.zeros(ndof)
    tau = MU * P_NORM
    # uniform consistent nodal load over each post-top node (tributary ~ EX)
    for n in top:
        F[2 * n]     += tau * EX        # +x shear
        F[2 * n + 1] += -P_NORM * EX    # -y normal
    free = np.setdiff1d(np.arange(ndof), fixed)
    U = np.zeros(ndof)
    U[free] = spla.spsolve(K[free][:, free], F[free])
    vm = vonmises_at_nodes(nodes, elems, U, D)
    return dict(nodes=nodes, tris=quad_tris(elems), U=U.reshape(-1, 2),
                vm=vm, top_y=top_y, W=T["W"], n_pitch=n_pitch)

# --- load + solve every family ----------------------------------------------
print("Solving Tier-2 FEA per family...")
panels = []
for fn, title, ship in FAMILIES:
    d = json.load(open(os.path.join(ITER, fn)))
    geom = d["geom"]; w, g, h = geom["w"], geom["g"], geom["h"]
    S = solve_family(w, g, h)
    S.update(title=title, ship=ship, score=d.get("score"),
             label=f"{title}\nw{w:.2f} g{g:.2f} h{h:.2f}  AR{geom['aspect']:.2f}",
             score_txt=f"score {d.get('score',0):.3f}")
    panels.append(S)
    print(f"  + {title:22s} w{w:.2f}/g{g:.2f}/h{h:.2f}  posts={S['n_pitch']}  "
          f"peak vM(full)={S['vm'].max():.3f} MPa")

# shared scale + deformation exaggeration (global, so panels stay comparable)
VMAX = float(np.percentile(np.concatenate([p["vm"] for p in panels]), 99))
gmax_disp = max(np.abs(p["U"]).max() for p in panels)
DEF_SCALE = 0.30 / gmax_disp                     # global max disp -> 0.30 mm visual
MAX_TOPY = max(p["top_y"] for p in panels)
print(f"shared vmax={VMAX:.2f} MPa   DEF_SCALE={DEF_SCALE:.3f} "
      f"(global max true disp {gmax_disp:.3f} mm -> 0.30 mm on screen)")

# --- theme + layout (mirror the finger array) -------------------------------
BG, C_TITLE, C_SUB, C_HDR, C_CAP = "#f6f6f8", "#141414", "#444", "#15506e", "#666"
C_LABEL, C_VAL, C_GOLD, C_GOLDBR, C_GOLDBG = "#222", "#1763a6", "#b8860b", "#e6a700", "#fff5d6"
OBJ = "#5a7d99"

NROWS = (len(panels) + NCOLS - 1) // NCOLS
PW, PH = 2.7, 1.85
GX, GY = 0.18, 0.50
LM, RM, TOP, BOT = 0.25, 0.25, 1.05, 0.80

GRIDW = NCOLS * PW + (NCOLS - 1) * GX
W = LM + GRIDW + RM
H = TOP + NROWS * PH + (NROWS - 1) * GY + BOT
fig = plt.figure(figsize=(W, H), dpi=100, facecolor=BG)

def ax_at(x_in, y_in, w_in, h_in):
    return fig.add_axes([x_in / W, 1 - (y_in + h_in) / H, w_in / W, h_in / H])

axes = []
for k, S in enumerate(panels):
    r, c = divmod(k, NCOLS)
    px = LM + c * (PW + GX)
    py = TOP + r * (PH + GY)
    ax = ax_at(px, py, PW, PH)
    ax.set_facecolor(BG)
    axes.append(ax)

# colorbar
cbw = 4.4
cax = fig.add_axes([(W / 2 - cbw / 2) / W, (BOT - 0.46) / H, cbw / W, 0.16 / H])
sm = plt.cm.ScalarMappable(cmap="inferno", norm=plt.Normalize(0, VMAX))
cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
cb.set_label("von Mises stress (MPa) — shared scale", color=C_CAP, fontsize=9)
cb.ax.tick_params(colors=C_CAP, labelsize=8); cb.outline.set_edgecolor("#999")

fig.text(0.5, 1 - 0.34 / H, "Grip texture — every family & its Tier-2 contact FEA",
         ha="center", va="center", fontsize=19, color=C_TITLE, fontweight="bold")
sub_t = fig.text(0.5, 1 - 0.62 / H, "", ha="center", va="center", fontsize=10.5, color=C_SUB)
fig.text(0.5, 1 - 0.86 / H,
         "champion cross-section of each swept family · 2D plane-strain Q4 contact FEA · "
         "common grip load p=0.20 MPa + μ=1.0 shear · shown to scale",
         ha="center", va="center", fontsize=9, color=C_HDR)
fig.text(0.5, 0.012,
         "Material: Bambu TPU 95A HF  E≈9.8 MPa (X-Y), σ≈27.3 MPa, ν=0.42   |   "
         "deformation scaled for visibility   |   posts clamped at base, "
         "rigid object shears across the top",
         ha="center", va="bottom", fontsize=7.5, color=C_CAP)

# --- animation: common load ramps 0->1 in sync ------------------------------
RAMP, HOLD = 20, 6
sweep = [i / (RAMP - 1) for i in range(RAMP)] + [1.0] * HOLD

def draw(k):
    s = sweep[k]
    for ax, S in zip(axes, panels):
        ax.clear(); ax.axis("off")
        ax.set_xlim(-0.2, WIN_W + 0.2)
        ax.set_ylim(-0.15, MAX_TOPY + 0.65)
        ax.set_aspect("equal")
        if S["ship"]:
            ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes, fill=True,
                                   facecolor=C_GOLDBG, edgecolor="none", zorder=-5, clip_on=False))
        P = S["nodes"] + DEF_SCALE * s * S["U"]
        tri = Triangulation(P[:, 0], P[:, 1], S["tris"])
        ax.tripcolor(tri, s * S["vm"], shading="gouraud", cmap="inferno",
                     vmin=0, vmax=VMAX, zorder=2)
        ax.triplot(tri, color="k", lw=0.08, alpha=0.18, zorder=3)
        # rigid object surface sliding across the post tops
        slide = DEF_SCALE * s * 0.5
        ax.add_patch(Rectangle((-0.2 + slide, S["top_y"] + 0.06), WIN_W + 0.4, 0.30,
                               facecolor=OBJ, edgecolor="none", alpha=0.85, zorder=4))
        if s > 0.02:
            ax.annotate("", xy=(WIN_W * 0.62, S["top_y"] + 0.22),
                        xytext=(WIN_W * 0.40, S["top_y"] + 0.22),
                        arrowprops=dict(arrowstyle="-|>", color="#16324a", lw=1.6), zorder=6)
        is_win = S["ship"]
        ax.set_title(S["label"], fontsize=8.2, color=(C_GOLD if is_win else C_LABEL),
                     fontweight=("bold" if is_win else "normal"), pad=3, linespacing=1.1)
        tag = ("★ SHIPPED  " if is_win else "") + S["score_txt"] + \
              f"   root {s*S['vm'].max():.2f} MPa"
        ax.text(0.5, -0.04, tag, transform=ax.transAxes, ha="center", va="top",
                fontsize=7.4, color=(C_GOLD if is_win else C_VAL),
                fontweight=("bold" if is_win else "normal"))
        if is_win:
            ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes, fill=False,
                                   edgecolor=C_GOLDBR, lw=2.6, zorder=20, clip_on=False))
    sub_t.set_text(f"grip load {s*100:3.0f}%   →   normal pressure + tangential shear, "
                   f"root stress concentrates at the post bases")

print(f"Rendering {len(sweep)} frames × {len(panels)} panels...")
anim = FuncAnimation(fig, draw, frames=len(sweep), blit=False)
anim.save(OUT, writer=PillowWriter(fps=9), savefig_kwargs={"facecolor": fig.get_facecolor()})
plt.close(fig)
print(f"\nWROTE  {OUT}  ({os.path.getsize(OUT)/1e6:.1f} MB)")

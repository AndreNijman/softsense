"""3D relief view of every grip-texture family — so you can SEE each pattern.

Builds the actual micro-relief height field z(x,y) for each swept family's champion
geometry (from the champion JSONs), renders each as a light-shaded 3D surface to
scale, and tiles all eight in a grid. The camera slowly orbits (surfaces are built
once; only the view moves each frame -> cheap). Emits an orbiting GIF + a crisp
high-DPI still. Shipped texture (conservative crosshatch) highlighted in gold.

Usage:  python grip/scripts/montage_grip_3d.py [out.gif]
"""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from matplotlib.patches import Rectangle
from matplotlib.animation import FuncAnimation, PillowWriter

HERE = os.path.dirname(os.path.abspath(__file__))
ITER = os.path.join(HERE, "..", "iterations")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    HERE, "..", "..", "renders", "grip_textures_3d_array.gif")
PNG = OUT.rsplit(".", 1)[0] + ".png"

L = 9.0       # physical patch side (mm) — same for all, so sizes are comparable
N = 170       # grid resolution per side
xs = np.linspace(0, L, N)
X, Y = np.meshgrid(xs, xs)

def band(coord, pitch, land):
    """1 where coord falls on a raised land within its pitch, else 0."""
    return ((coord % pitch) < land).astype(float)

def tri_wave(t, period):
    p = t % period
    return np.abs(p / period - 0.5) * 2.0      # 0..1 triangle

def hex_pads(X, Y, cell, channel, pointy=True):
    """Raised regular hexagons on a hex lattice (inradius ri, gap=channel)."""
    ri = (cell - channel) / 2.0
    dy = cell * np.sqrt(3) / 2.0
    Z = np.zeros_like(X)
    nrow = int(L / dy) + 2
    ncol = int(L / cell) + 2
    for r in range(-1, nrow):
        cy = r * dy
        xoff = (cell / 2.0) if (r % 2) else 0.0
        for c in range(-1, ncol):
            cx = c * cell + xoff
            ddx = X - cx; ddy = Y - cy
            ax_, ay_ = np.abs(ddx), np.abs(ddy)
            if pointy:                          # pointy-top hexagon
                inside = (ax_ <= ri) & (0.5 * ax_ + (np.sqrt(3) / 2) * ay_ <= ri)
            else:
                inside = (ay_ <= ri) & ((np.sqrt(3) / 2) * ax_ + 0.5 * ay_ <= ri)
            Z = np.where(inside, 1.0, Z)
    return Z

def dimples(X, Y, pitch, dia):
    """Flat top with circular pits on a square lattice (z dips in the pits)."""
    r = dia / 2.0
    fx = (X % pitch) - pitch / 2.0
    fy = (Y % pitch) - pitch / 2.0
    pit = (fx * fx + fy * fy) < r * r
    return np.where(pit, 0.0, 1.0)

def height_field(fam, p):
    """Return z (mm) and the max height for one family's champion geometry."""
    if fam == "ridge":
        h = p["depth"]; Z = band(X, p["pitch"], p["land"]) * h
    elif fam in ("crosshatch", "crosshatch_ship"):
        h = p["depth"]
        Z = band(X, p["pitch"], p["land"]) * band(Y, p["pitch"], p["land"]) * h
    elif fam == "chevron":
        h = p["depth"]
        amp = p["pitch"] * 0.9
        xp = X + amp * tri_wave(Y, 2.6)         # zig-zag the ridge -> chevrons
        Z = band(xp, p["pitch"], p["land"]) * h
    elif fam == "hexpad":
        h = p["depth"]; Z = hex_pads(X, Y, p["cell"], p["channel"]) * h
    elif fam == "dimple":
        h = p["depth"]; Z = dimples(X, Y, p["pitch"], p["dia"]) * h
    elif fam == "concentric":
        h = p["depth"]
        cx = cy = L / 2.0
        r = np.hypot(X - cx, Y - cy)
        Z = band(r, p["pitch"], p["land"]) * h
        Z = np.where(r < p.get("cavity", 0) , 0.0, Z)   # small central cavity
    elif fam == "hierarchical":
        Mh, mh = p["macro_depth"], p["micro_depth"]
        h = Mh + mh
        Mp, Mc = p["macro_pitch"], p["macro_channel"]
        Ml = Mp - Mc
        macro = band(X, Mp, Ml) * band(Y, Mp, Ml)
        micro = band(X, p["micro_pitch"], p["micro_land"]) * \
                band(Y, p["micro_pitch"], p["micro_land"])
        Z = macro * (Mh + micro * mh)
    else:
        raise ValueError(fam)
    return Z, h

# --- families: (json, family-key, title, shipped?) --------------------------
FAMILIES = [
    ("crosshatch_champ.json", "crosshatch",      "crosshatch",          False),
    ("conc_champ.json",       "concentric",      "concentric",          False),
    ("hexpad_champ.json",     "hexpad",          "hexpad",              False),
    ("chevron_champ.json",    "chevron",         "chevron",             False),
    ("dimple_champ.json",     "dimple",          "dimple",              False),
    ("ridge_champ.json",      "ridge",           "ridge",               False),
    ("hier_champ.json",       "hierarchical",    "hierarchical",        False),
    ("SHIP_crosshatch.json",  "crosshatch_ship", "crosshatch (shipped)", True),
]
NCOLS, NROWS = 4, 2

print("Building height fields...")
panels = []
for fn, fam, title, ship in FAMILIES:
    d = json.load(open(os.path.join(ITER, fn)))
    Z, h = height_field(fam, d["params"])
    panels.append(dict(Z=Z, h=h, title=title, ship=ship, score=d.get("score"),
                       label=d["label"].replace("xhatch", "crosshatch")))
    print(f"  + {title:22s} hmax={h:.2f} mm  z-range {Z.min():.2f}..{Z.max():.2f}")

HMAX = max(p["h"] for p in panels)
ZBOX = 0.46                         # vertical box fraction -> shared height exag
EXAG = (ZBOX / HMAX) / (1.0 / L)    # reported height-exaggeration factor
print(f"shared HMAX={HMAX:.2f} mm   height exaggerated ~x{EXAG:.1f}")

# --- figure -----------------------------------------------------------------
BG, C_TITLE, C_SUB, C_HDR, C_CAP = "#f6f6f8", "#141414", "#444", "#15506e", "#666"
C_LABEL, C_GOLD, C_GOLDBR, C_GOLDBG = "#222", "#b8860b", "#e6a700", "#fff5d6"

fig = plt.figure(figsize=(15.2, 8.6), dpi=100, facecolor=BG)
fig.subplots_adjust(left=0.005, right=0.995, top=0.86, bottom=0.05, wspace=0.02, hspace=0.10)

ls = LightSource(azdeg=315, altdeg=52)
cmap = plt.cm.cividis
axes = []
for k, P in enumerate(panels):
    ax = fig.add_subplot(NROWS, NCOLS, k + 1, projection="3d")
    ax.set_box_aspect((1, 1, ZBOX))
    Z = P["Z"]
    rgb = ls.shade(Z, cmap=cmap, vert_exag=4.0, blend_mode="soft",
                   vmin=0, vmax=HMAX)
    ax.plot_surface(X, Y, Z, facecolors=rgb, rcount=N, ccount=N,
                    linewidth=0, antialiased=False, shade=False)
    ax.set_zlim(0, HMAX)
    ax.set_axis_off()
    is_win = P["ship"]
    if is_win:                       # gold backing panel behind the subplot
        bb = ax.get_position()
        fig.add_artist(Rectangle((bb.x0 - 0.004, bb.y0 - 0.01),
                                 bb.width + 0.008, bb.height + 0.05,
                                 transform=fig.transFigure, facecolor=C_GOLDBG,
                                 edgecolor=C_GOLDBR, lw=2.6, zorder=-10, clip_on=False))
    ttl = ("★ SHIPPED — " if is_win else "") + P["title"]
    ax.set_title(f"{ttl}\n{P['label']}  ·  score {P['score']:.3f}",
                 fontsize=9.2, color=(C_GOLD if is_win else C_LABEL),
                 fontweight=("bold" if is_win else "normal"), pad=-2, linespacing=1.25)
    axes.append(ax)

fig.text(0.5, 0.965, "Grip textures in 3D — the seven swept families + the shipped pattern",
         ha="center", va="center", fontsize=20, color=C_TITLE, fontweight="bold")
fig.text(0.5, 0.925,
         f"actual micro-relief of each champion geometry · all shown to scale on a {L:.0f}×{L:.0f} mm "
         f"patch · height exaggerated ~×{EXAG:.0f} for visibility",
         ha="center", va="center", fontsize=11, color=C_HDR)
fig.text(0.5, 0.018, "Bambu TPU 95A HF printed relief · channel depth & land width are the "
         "swept levers · colour = surface height (dark valleys → bright lands)",
         ha="center", va="center", fontsize=8.5, color=C_CAP)

# --- crisp still ------------------------------------------------------------
for ax in axes:
    ax.view_init(elev=44, azim=-62)
fig.savefig(PNG, dpi=190, facecolor=BG)
print(f"WROTE  {PNG}")

# --- orbit (camera-only; surfaces persist) ----------------------------------
A0, A1 = -82, -38
seq = list(np.linspace(A0, A1, 16)) + list(np.linspace(A1, A0, 16))   # ping-pong loop
def upd(k):
    az = seq[k]
    for ax in axes:
        ax.view_init(elev=44, azim=az)

print(f"Rendering {len(seq)}-frame orbit...")
anim = FuncAnimation(fig, upd, frames=len(seq), blit=False)
anim.save(OUT, writer=PillowWriter(fps=12), savefig_kwargs={"facecolor": BG})
plt.close(fig)
print(f"WROTE  {OUT}  ({os.path.getsize(OUT)/1e6:.1f} MB)")

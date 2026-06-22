"""Montage of EVERY finger design-iteration FEA into one big synchronized GIF.

Reads each iteration's saved 3D FEA solution (fea3d_solution.npz), rebuilds the
mid-plane filled mesh coloured by von Mises (reusing render_wrap.load2d/_draw),
and tiles all iterations as a round-aligned grid. Every panel closes onto the
SAME frozen grasp object (R=22 cylinder) in sync, on a SHARED stress colour
scale, so the whole design journey reads at a glance. The shipped winner (w7)
is highlighted.

Usage:  python fea/scripts/montage_iterations.py [out.gif]
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.animation import FuncAnimation, PillowWriter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from render_wrap import load2d, _draw, MATERIAL  # reuse the canonical loader+drawer

ITER_ROOT = os.path.join(HERE, "..", "iterations")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    HERE, "..", "..", "renders", "finger_iterations_fea_array.gif")

# --- the design journey, grouped by round (each row = one round) -------------
# (dir_name, short label).  All on the frozen R=22 cylinder @ yc=80.
BANDS = [
    ("1   Baseline + Round 1  —  single-lever sweep (wall / ribs / taper / slant)", [
        ("iter00b_targetgrip", "iter00\nbaseline"),
        ("r1_wall20",          "wall 2.0"),
        ("r1_wall15",          "wall 1.5"),
        ("r1_ribs16",          "16 ribs"),
        ("r1_tip10",           "tip 10"),
        ("r1_tip16",           "tip 16"),
        ("r1_tipcap05",        "tipcap 0.5"),
        ("r1_slant22",         "slant 22°"),
    ]),
    ("2 + 3   Stiffness gradients, object position, finger length", [
        ("exp_slantneg38",        "slant −38°"),
        ("r2_spinetip10",         "spine→1.0"),
        ("r2b_stiffbeam_thinrib", "stiff beam\nthin rib"),
        ("r2c_thinrib_only",      "thin rib"),
        ("exp_yc95",              "object y=95"),
        ("r3_len58",              "length 58"),
    ]),
    ("4   Free-topology Fin Ray scan", [
        ("f2_default",   "topo\ndefault"),
        ("f2_ribrev",    "topo\nrib-rev"),
        ("f2_ribsteep",  "topo\nrib 65°"),
        ("f2_symmetric", "topo\nsymmetric"),
    ]),
    ("5   Wrap-optimization  —  compliant contact beam", [
        ("w0_base",         "w0 base"),
        ("w1_contactgrad15","w1 cgrad"),
        ("w2_ribs16",       "w2 16 ribs"),
        ("w3_ribs16_cgrad", "w3 16r+cg"),
        ("w4_csoft15",      "w4 csoft1.5"),
        ("w5_csoft12",      "w5 csoft1.2"),
        ("w6_csoft_grad10", "w6 grad1.0"),
        ("w7_balanced",     "w7  ★ SHIPPED"),
    ]),
]
WINNER = "w7_balanced"
NCOLS = 8                       # widest band drives the grid

# --- load every panel --------------------------------------------------------
print("Loading FEA solutions...")
panels = []   # list of (band_idx, dir, label, S)
pooled = []
for bi, (_, items) in enumerate(BANDS):
    for d, lab in items:
        path = os.path.join(ITER_ROOT, d)
        if not os.path.exists(os.path.join(path, "fea3d_solution.npz")):
            print(f"  !! missing {d} — skipped"); continue
        S = load2d(path)
        panels.append((bi, d, lab, S))
        pooled.append(S["vms"][S["op"]][S["l0"]])
        print(f"  + {d}")

# shared, honest stress scale: 98th pct of pooled op-frame von Mises
VMAX = float(np.percentile(np.concatenate(pooled), 98))
print(f"shared vmax = {VMAX:.2f} MPa over {len(panels)} panels")

# --- layout (inches), bands stacked, partial rows centred --------------------
# --- light presentation theme ------------------------------------------------
BG       = "#f6f6f8"           # figure / panel background
C_TITLE  = "#141414"
C_SUB    = "#444"
C_HDR    = "#15506e"           # band headers (deep teal)
C_CAP    = "#666"
C_LABEL  = "#222"             # panel labels
C_GRIP   = "#1763a6"          # live grip readout
C_GOLD   = "#b8860b"          # winner text
C_GOLDBR = "#e6a700"          # winner border
C_GOLDBG = "#fff5d6"          # winner tint

PW, PH = 1.55, 2.26            # panel w/h
GX, GY = 0.10, 0.10            # gaps between panels
HDR = 0.34                     # band header strip
BANDGAP = 0.16
LM, RM = 0.18, 0.18
TOP = 0.78                     # suptitle
BOT = 0.72                     # colorbar + caption

GRIDW = NCOLS * PW + (NCOLS - 1) * GX
W = LM + GRIDW + RM
bandH = HDR + PH                # one panel row per band
H = TOP + len(BANDS) * bandH + (len(BANDS) - 1) * BANDGAP + BOT

fig = plt.figure(figsize=(W, H), dpi=100, facecolor=BG)

def ax_at(x_in, y_in, w_in, h_in):
    """y measured from TOP; convert to a matplotlib bottom-left fig-fraction axes."""
    return fig.add_axes([x_in / W, 1 - (y_in + h_in) / H, w_in / W, h_in / H])

# build per-panel axes + per-band header text
panel_axes = {}     # dir -> ax
for bi, (title, items) in enumerate(BANDS):
    band_y = TOP + bi * (bandH + BANDGAP)
    # header
    fig.text(LM / W, 1 - (band_y + 0.06) / H, title, ha="left", va="top",
             fontsize=11, color=C_HDR, fontweight="bold")
    n = len(items)
    row_w = n * PW + (n - 1) * GX
    x0 = LM + (GRIDW - row_w) / 2.0           # centre partial rows
    py = band_y + HDR
    for ci, (d, lab) in enumerate(items):
        if d not in [p[1] for p in panels]:
            continue
        px = x0 + ci * (PW + GX)
        ax = ax_at(px, py, PW, PH)
        ax.set_facecolor(BG)
        panel_axes[d] = ax

# colorbar axis (bottom, horizontal, centred)
cbw = 4.2
cax = fig.add_axes([(W / 2 - cbw / 2) / W, (BOT - 0.42) / H, cbw / W, 0.16 / H])
sm = plt.cm.ScalarMappable(cmap="inferno", norm=plt.Normalize(0, VMAX))
cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
cb.set_label("von Mises stress (MPa) — shared scale", color=C_CAP, fontsize=9)
cb.ax.tick_params(colors=C_CAP, labelsize=8)
cb.outline.set_edgecolor("#999")

# titles + captions
fig.text(0.5, 1 - 0.33 / H, "Fin-Ray finger — every design iteration & its FEA",
         ha="center", va="center", fontsize=19, color=C_TITLE, fontweight="bold")
sub_t = fig.text(0.5, 1 - 0.60 / H, "", ha="center", va="center",
                 fontsize=10.5, color=C_SUB)
fig.text(0.5, 0.012, MATERIAL + "    |    "
         "3D corotational contact FEA, base-pin clamp, R=22 mm cylinder, equal-closure sweep",
         ha="center", va="bottom", fontsize=7.5, color=C_CAP)

# --- animation: every panel closes to its own grasp in sync ------------------
RAMP = 22
HOLD = 7
fracs = [i / (RAMP - 1) for i in range(RAMP)] + [1.0] * HOLD

def draw_frame(k):
    f = fracs[k]
    for bi, d, lab, S in panels:
        ax = panel_axes[d]
        j = int(round(f * S["op"]))
        is_win = (d == WINNER)
        if is_win:                            # gold tint behind the shipped finger
            ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes, fill=True,
                                    facecolor=C_GOLDBG, edgecolor="none",
                                    zorder=-5, clip_on=False))
        _draw(ax, S, j, None, VMAX)          # mesh + object, no title
        # panel label
        ax.set_title(lab, fontsize=8.0, color=(C_GOLD if is_win else C_LABEL),
                     fontweight=("bold" if is_win else "normal"), pad=2)
        # live grip readout
        ax.text(0.5, 0.012, f"{S['grip'][j]:.0f} N", transform=ax.transAxes,
                ha="center", va="bottom", fontsize=7.5,
                color=(C_GOLD if is_win else C_GRIP), fontweight="bold")
        if is_win:
            ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes, fill=False,
                                    edgecolor=C_GOLDBR, lw=2.6, zorder=20, clip_on=False))
    sub_t.set_text(f"closure {f * 8.0:4.1f} mm   →   each finger pressed onto the same object, "
                   f"coloured by stress, on one shared scale")

print(f"Rendering {len(fracs)} frames × {len(panels)} panels...")
anim = FuncAnimation(fig, draw_frame, frames=len(fracs), blit=False)
anim.save(OUT, writer=PillowWriter(fps=9), savefig_kwargs={"facecolor": fig.get_facecolor()})
plt.close(fig)
print(f"\nWROTE  {OUT}  ({os.path.getsize(OUT)/1e6:.1f} MB)")

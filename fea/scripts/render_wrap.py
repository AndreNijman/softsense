"""Render FEA wrap results: filled finger mesh coloured by von Mises, conforming
to a SOLID object (the amphora-neck cylinder it actually touches), as a still at
the grasp + a closing animation. Plus a side-by-side comparison of iterations
(still + animation). Reads fea3d_solution.npz (3D tets) and rebuilds the mid-plane
2D mesh for a clean filled view.

Usage:
  python render_wrap.py one   <iter_dir>                 -> still + anim.gif
  python render_wrap.py compare <out_dir> <dir1> <dir2>... -> compare.png + compare.gif
"""
import sys, os, json, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from matplotlib.patches import Circle
from matplotlib.animation import FuncAnimation, PillowWriter

R_NECK, YC, GAP = 22.0, 80.0, 0.5
OBJ_COLOR = "#5a7d99"
PRESS_AT = 8.0


def load2d(d):
    z = np.load(os.path.join(d, "fea3d_solution.npz"))
    rest, frames, vms, press, grip = z["rest"], z["frames"], z["vms"], z["press"], z["grip"]
    yc = float(z["yc"]) if "yc" in z else YC
    rneck = float(z["R_neck"]) if "R_neck" in z else R_NECK
    z0 = rest[:, 2].min()
    l0 = np.where(np.abs(rest[:, 2] - z0) < 1e-6)[0]           # bottom-layer nodes
    g2l = {int(g): i for i, g in enumerate(l0)}
    tets = z["tets"]
    tris = []
    for t in tets:
        base = [int(n) for n in t if int(n) in g2l]
        if len(base) == 3:
            tris.append(sorted(base))
    tris = np.unique(np.array(tris), axis=0)
    tris_local = np.array([[g2l[n] for n in tri] for tri in tris])
    xc0 = rest[:, 0].min() - rneck - GAP
    # operating frame = closest to PRESS_AT
    op = int(np.argmin(np.abs(press - PRESS_AT)))
    return dict(l0=l0, tris=tris_local, frames=frames, vms=vms, press=press,
                grip=grip, xc0=xc0, yc=yc, rneck=rneck, op=op,
                vmax=float(np.percentile(vms[op][l0], 99)) + 1e-6)


def _draw(ax, S, i, title=None, vmax=None):
    ax.clear()
    P = S["frames"][i][S["l0"]]; vm = S["vms"][i][S["l0"]]
    cx = S["xc0"] + S["press"][i]
    ax.add_patch(Circle((cx, S["yc"]), S["rneck"], color=OBJ_COLOR, alpha=0.95, zorder=0))
    tri = Triangulation(P[:, 0], P[:, 1], S["tris"])
    ax.tripcolor(tri, vm, shading="gouraud", cmap="inferno",
                 vmin=0, vmax=vmax or S["vmax"], zorder=2)
    ax.triplot(tri, color="k", lw=0.15, alpha=0.25, zorder=3)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-38, 36); ax.set_ylim(22, 130)
    if title:
        ax.set_title(title, fontsize=8)


def render_one(d):
    S = load2d(d)
    name = os.path.basename(d)
    sm = plt.cm.ScalarMappable(cmap="inferno", norm=plt.Normalize(0, S["vmax"]))
    # still at grasp
    fig, ax = plt.subplots(figsize=(4.2, 7.0), dpi=140)
    i = S["op"]
    _draw(ax, S, i, f"{name}\nclosure {S['press'][i]:.1f}mm  grip {S['grip'][i]:.0f}N", S["vmax"])
    cb = fig.colorbar(sm, ax=ax, fraction=0.045, pad=0.02); cb.set_label("von Mises (MPa)", fontsize=7)
    cb.ax.tick_params(labelsize=6)
    fig.savefig(os.path.join(d, "wrap_render.png"), bbox_inches="tight"); plt.close(fig)
    # closing animation
    fig, ax = plt.subplots(figsize=(4.2, 7.0), dpi=110)
    order = list(range(len(S["press"]))) + [len(S["press"]) - 1] * 4
    def upd(k):
        i = order[k]
        _draw(ax, S, i, f"{name}\nclosure {S['press'][i]:.1f}mm  grip {S['grip'][i]:.0f}N", S["vmax"])
    anim = FuncAnimation(fig, upd, frames=len(order), blit=False)
    anim.save(os.path.join(d, "wrap_anim.gif"), writer=PillowWriter(fps=8)); plt.close(fig)
    print(f"  {name}: wrap_render.png + wrap_anim.gif")


def render_compare(outdir, dirs):
    Ss = [(os.path.basename(d), load2d(d)) for d in dirs]
    n = len(Ss); vmax = max(s["vmax"] for _, s in Ss)
    sm = plt.cm.ScalarMappable(cmap="inferno", norm=plt.Normalize(0, vmax))
    # still: all at grasp
    fig, axs = plt.subplots(1, n, figsize=(3.0 * n, 6.5), dpi=130)
    if n == 1: axs = [axs]
    for ax, (nm, S) in zip(axs, Ss):
        i = S["op"]; _draw(ax, S, i, f"{nm}\n{S['press'][i]:.1f}mm {S['grip'][i]:.0f}N", vmax)
    fig.colorbar(sm, ax=axs, fraction=0.012, pad=0.01, label="von Mises (MPa)")
    fig.savefig(os.path.join(outdir, "compare.png"), bbox_inches="tight"); plt.close(fig)
    # animation: all close together
    nf = min(len(S["press"]) for _, S in Ss)
    fig, axs = plt.subplots(1, n, figsize=(3.0 * n, 6.5), dpi=100)
    if n == 1: axs = [axs]
    order = list(range(nf)) + [nf - 1] * 4
    def upd(k):
        i = order[k]
        for ax, (nm, S) in zip(axs, Ss):
            j = min(i, len(S["press"]) - 1)
            _draw(ax, S, j, f"{nm}\n{S['press'][j]:.1f}mm {S['grip'][j]:.0f}N", vmax)
    anim = FuncAnimation(fig, upd, frames=len(order), blit=False)
    anim.save(os.path.join(outdir, "compare.gif"), writer=PillowWriter(fps=8)); plt.close(fig)
    print(f"  compare.png + compare.gif ({n} iterations) -> {outdir}")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "one":
        render_one(sys.argv[2])
    elif mode == "compare":
        render_compare(sys.argv[2], sys.argv[3:])

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
from matplotlib.patches import Circle, Rectangle
from matplotlib.animation import FuncAnimation, PillowWriter

R_NECK, YC, GAP = 22.0, 80.0, 0.5
OBJ_COLOR = "#5a7d99"
MATERIAL = "Material: Bambu TPU 95A HF   FEA E≈9.8 MPa (X-Y), σ≈27.3 MPa, ν=0.42"
PRESS_AT = 8.0
GRIP_TARGET = 12.0   # render the grasp at EQUAL grip force (fair across stiff/soft
                     # fingers) -- a soft finger needs more closure to reach it.


def contact_stats(S, i=None):
    """Contact arc / evenness / span computed AT the rendered frame (default the
    equal-grip op frame), from the deformed mid-plane nodes + the rigid object."""
    if i is None:
        i = S["op"]
    P = S["frames"][i][S["l0"]]
    cx = S["xc0"] + S["press"][i]; cy = S["yc"]; R = S["rneck"]
    dx = P[:, 0] - cx; dy = P[:, 1] - cy
    if S.get("shape") == "box":            # signed: +inside, -outside (box SDF)
        qx = np.abs(dx) - R; qy = np.abs(dy) - R
        out = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0))
        pen = -(out + np.minimum(np.maximum(qx, qy), 0.0))
    else:
        pen = R - np.hypot(dx, dy)         # +inside, -outside
    c = np.where(pen > -0.4)[0]            # nodes touching / within 0.4 mm of surface
    span = float(P[c, 1].max() - P[c, 1].min()) if len(c) >= 1 else 0.0
    return dict(n=int(len(c)), span=span,
                grip=float(S["grip"][i]), closure=float(S["press"][i]))


def statline(S):
    s = contact_stats(S)
    return ("contact spans %.0f mm of finger\ngrip %.0f N  @ %.1f mm closure"
            % (s["span"], s["grip"], s["closure"]))


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
    xc0 = float(z["xc0"]) if "xc0" in z else rest[:, 0].min() - rneck - GAP
    shape = str(z["obj_shape"]) if "obj_shape" in z else "circle"
    # operating frame = first closure reaching the target grip force (fair across
    # stiff/soft fingers); fall back to peak grip if never reached.
    _hit = np.where(grip >= GRIP_TARGET)[0]
    op = int(_hit[0]) if len(_hit) else int(np.argmax(grip))
    return dict(l0=l0, tris=tris_local, frames=frames, vms=vms, press=press,
                grip=grip, xc0=xc0, yc=yc, rneck=rneck, op=op, shape=shape,
                vmax=float(np.percentile(vms[op][l0], 99)) + 1e-6)


def _draw(ax, S, i, title=None, vmax=None):
    ax.clear()
    P = S["frames"][i][S["l0"]]; vm = S["vms"][i][S["l0"]]
    cx = S["xc0"] + S["press"][i]
    if S.get("shape") == "box":
        H = S["rneck"]
        ax.add_patch(Rectangle((cx - H, S["yc"] - H), 2 * H, 2 * H,
                               color=OBJ_COLOR, alpha=0.95, zorder=0))
    else:
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
    _draw(ax, S, i, f"{name}\n{statline(S)}", S["vmax"])
    cb = fig.colorbar(sm, ax=ax, fraction=0.045, pad=0.02); cb.set_label("von Mises (MPa)", fontsize=7)
    cb.ax.tick_params(labelsize=6)
    fig.text(0.5, 0.005, MATERIAL, ha="center", fontsize=6, color="#555")
    fig.savefig(os.path.join(d, "wrap_render.png"), bbox_inches="tight"); plt.close(fig)
    # closing animation
    fig, ax = plt.subplots(figsize=(4.2, 7.0), dpi=110)
    order = list(range(S["op"] + 1)) + [S["op"]] * 5     # close to the grasp, hold
    def upd(k):
        i = order[k]
        _draw(ax, S, i, f"{name}\nclosure {S['press'][i]:.1f}mm  grip {S['grip'][i]:.0f}N", S["vmax"])
    anim = FuncAnimation(fig, upd, frames=len(order), blit=False)
    anim.save(os.path.join(d, "wrap_anim.gif"), writer=PillowWriter(fps=8)); plt.close(fig)
    print(f"  {name}: wrap_render.png + wrap_anim.gif (op frame {S['op']}, grip {S['grip'][S['op']]:.0f}N)")


def render_compare(outdir, dirs):
    Ss = [(os.path.basename(d), load2d(d)) for d in dirs]
    n = len(Ss); vmax = max(s["vmax"] for _, s in Ss)
    sm = plt.cm.ScalarMappable(cmap="inferno", norm=plt.Normalize(0, vmax))
    # still: all at grasp
    fig, axs = plt.subplots(1, n, figsize=(3.0 * n, 6.8), dpi=130)
    if n == 1: axs = [axs]
    for ax, d, (nm, S) in zip(axs, dirs, Ss):
        i = S["op"]; _draw(ax, S, i, f"{nm}\n{statline(S)}", vmax)
    fig.colorbar(sm, ax=axs, fraction=0.012, pad=0.01, label="von Mises (MPa)")
    fig.text(0.5, 0.01, MATERIAL, ha="center", fontsize=7, color="#555")
    fig.savefig(os.path.join(outdir, "compare.png"), bbox_inches="tight"); plt.close(fig)
    # animation: all close together
    fig, axs = plt.subplots(1, n, figsize=(3.0 * n, 6.5), dpi=100)
    if n == 1: axs = [axs]
    nf = 26
    fracs = [i / (nf - 1) for i in range(nf)] + [1.0] * 5   # each finger -> its grasp
    def upd(k):
        f = fracs[k]
        for ax, (nm, S) in zip(axs, Ss):
            j = int(round(f * S["op"]))
            _draw(ax, S, j, f"{nm}\n{S['press'][j]:.1f}mm {S['grip'][j]:.0f}N", vmax)
    anim = FuncAnimation(fig, upd, frames=len(fracs), blit=False)
    anim.save(os.path.join(outdir, "compare.gif"), writer=PillowWriter(fps=8)); plt.close(fig)
    print(f"  compare.png + compare.gif ({n} iterations) -> {outdir}")


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "one":
        render_one(sys.argv[2])
    elif mode == "compare":
        render_compare(sys.argv[2], sys.argv[3:])

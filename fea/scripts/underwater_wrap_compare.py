"""Side-by-side dry vs wet wrap-stages comparison render for the underwater FEA.

Reads the fea3d_solution.npz files from the wet-modulus sweep and renders a
single 4-row × 4-col figure (one row per E_TPU level, 4 wrap stages each)
with the SAME vM color scale across cases for direct visual comparison.

Run:  python fea/scripts/underwater_wrap_compare.py
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ITER = os.path.join(ROOT, "fea", "iterations")
PICS = os.path.join(ROOT, "fea", "pictures")

CASES = [
    ("under_E40_dry", 40.0, "dry  (E = 40 MPa)"),
    ("under_E32_wet20", 32.0, "wet ~20%  (E = 32 MPa)"),
    ("under_E28_wet30", 28.0, "wet ~30%  (E = 28 MPa)"),
    ("under_E20_wet50", 20.0, "wet ~50%  (E = 20 MPa)"),
]


def load_case(name):
    fp = os.path.join(ITER, name, "fea3d_solution.npz")
    if not os.path.exists(fp):
        return None
    d = np.load(fp)
    return d


def main():
    cases = []
    for name, E, label in CASES:
        d = load_case(name)
        if d is None:
            print(f"missing {name}"); continue
        m = json.load(open(os.path.join(ITER, name, "metrics.json")))
        cases.append(dict(name=name, E=E, label=label, npz=d, m=m))
    if len(cases) < 2:
        print(f"only {len(cases)} cases — skip"); return

    # mid-plane z layer (matches iter_harness.plot_all)
    sample = cases[0]["npz"]
    rest = sample["rest"]
    midz = (rest[:, 2].min() + rest[:, 2].max()) / 2.0
    zlevels = np.unique(rest[:, 2])
    zlayer = zlevels[np.argmin(np.abs(zlevels - midz))]

    # SAME vmax across all cases — 99th percentile of the dry-case target frame
    target_idx_dry = int(cases[0]["m"].get("target_idx", -1))
    # safer: find target_idx using press ~ PRESS_AT_REPORT
    press_dry = cases[0]["npz"]["press"]
    tgt_dry = int(np.argmin(np.abs(np.array(press_dry) - 8.0)))
    sel_dry = np.abs(rest[:, 2] - zlayer) < 1e-6
    vmax = float(np.percentile(cases[0]["npz"]["vms"][tgt_dry][sel_dry], 99))

    nrows, ncols = len(cases), 4
    fig, axs = plt.subplots(nrows, ncols, figsize=(3.6 * ncols, 3.2 * nrows))
    if nrows == 1:
        axs = axs[None, :]
    for ri, c in enumerate(cases):
        rest_c = c["npz"]["rest"]
        sel = np.abs(rest_c[:, 2] - zlayer) < 1e-6
        F = c["npz"]["frames"]
        V = c["npz"]["vms"]
        pr = c["npz"]["press"]
        gr = c["npz"]["grip"]
        xc0 = float(c["npz"]["xc0"])
        yc = float(c["npz"]["yc"])
        Rn = float(c["npz"]["R_neck"])
        tgt = int(np.argmin(np.abs(np.array(pr) - 8.0)))
        idxs = [0, max(1, tgt // 2), tgt, len(F) - 1]
        for ci, fi in enumerate(idxs):
            ax = axs[ri, ci]
            P = F[fi][sel]
            sc = ax.scatter(P[:, 0], P[:, 1], c=V[fi][sel], s=4,
                            cmap="inferno", vmin=0, vmax=vmax)
            cx = xc0 + pr[fi]
            th = np.linspace(0, 2 * np.pi, 80)
            ax.plot(cx + Rn * np.cos(th), yc + Rn * np.sin(th), c="c", lw=1.5)
            ax.set_aspect("equal")
            ax.set_xlim(-30, 35); ax.set_ylim(20, 130)
            tag = " (report)" if fi == tgt else ""
            ax.set_title(f"press={pr[fi]:.1f}mm  grip={gr[fi]:.1f}N{tag}",
                         fontsize=8)
            ax.set_xticks([]); ax.set_yticks([])
        axs[ri, 0].set_ylabel(c["label"], fontsize=10)
    fig.suptitle("Wrap stages: dry → saturated soft TPU (same vM color scale)",
                 fontsize=12)
    fig.subplots_adjust(left=0.07, right=0.92, top=0.93, bottom=0.04,
                         wspace=0.08, hspace=0.18)
    # one colorbar on the right
    cbar_ax = fig.add_axes([0.93, 0.08, 0.015, 0.83])
    fig.colorbar(sc, cax=cbar_ax, label="von Mises (MPa)")
    fp = os.path.join(PICS, "underwater_wrap_compare.png")
    os.makedirs(PICS, exist_ok=True)
    fig.savefig(fp, dpi=120)
    print(f"wrote {fp}")


if __name__ == "__main__":
    main()

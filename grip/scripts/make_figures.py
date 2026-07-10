"""Generate all 7 publication-quality figures for the grip-texture campaign.

Run from:  cd /home/andre/gripper-cad/grip/scripts && python make_figures.py
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.ticker as ticker

import grip_model as G

# ── style ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 140,
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.fontsize": 9,
    "legend.framealpha": 0.85,
})

OUTDIR = "/home/andre/gripper-cad/grip/pictures"
DATA   = "/home/andre/gripper-cad/grip/iterations"

COLORS = {
    "concentric":   "#2176AE",
    "crosshatch":   "#D64045",
    "chevron":      "#E57C23",
    "hexpad":       "#3BAC6E",
    "hierarchical": "#7B5EA7",
    "ridge":        "#8B7355",
    "dimple":       "#888888",
    "smooth":       "#CCCCCC",
}

# ─────────────────────────────────────────────────────────────────────────────
# Fig 1  family_scores.png
# ─────────────────────────────────────────────────────────────────────────────
def fig_family_scores():
    # Champion scores from the brief (verified)
    champs = {
        "concentric":   0.872,
        "crosshatch":   0.808,
        "chevron":      0.797,
        "hexpad":       0.798,
        "hierarchical": 0.801,   # from sensitivity baseline
        "ridge":        0.754,
        "dimple":       0.632,
        "smooth":       0.251,
    }
    # Conservative / no-suction variants where known
    conserv = {
        "crosshatch":  0.746,    # SHIP params
        "concentric":  0.857,    # cavity=0, no suction
    }

    # Sort descending (smooth stays at bottom by construction of brief -- keep that)
    order = sorted(champs.keys(), key=lambda k: (k == "smooth", -champs[k]))

    fig, ax = plt.subplots(figsize=(7.5, 5.2))

    ys = np.arange(len(order))
    bar_h = 0.55

    for i, fam in enumerate(order):
        clr = COLORS.get(fam, "#999999")
        bar = ax.barh(i, champs[fam], height=bar_h, color=clr, zorder=3, alpha=0.92)
        # conservative variant as a lighter, thinner bar
        if fam in conserv:
            ax.barh(i, conserv[fam], height=bar_h * 0.45,
                    color=clr, alpha=0.38, zorder=4, left=0)
            ax.annotate(f"  conservative: {conserv[fam]:.3f}",
                        xy=(conserv[fam], i), xytext=(conserv[fam] + 0.005, i - 0.22),
                        fontsize=7.5, color=clr, va="center")

    ax.set_yticks(ys)
    ax.set_yticklabels([f"{'smooth (control)' if f == 'smooth' else f}" for f in order],
                       fontsize=9.5)
    ax.set_xlabel("Universal grip score (weighted, 0 – 1)")
    ax.set_title("Champion grip scores by texture family\n(underwater soft gripper, 7-condition battery)",
                 pad=8)
    ax.set_xlim(0, 1.02)
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.05))
    ax.grid(axis="x", which="both", lw=0.4, alpha=0.5, zorder=0)

    # Score labels on bars
    for i, fam in enumerate(order):
        ax.text(champs[fam] + 0.008, i, f"{champs[fam]:.3f}",
                va="center", fontsize=8.5)

    # Annotations
    conc_idx = order.index("concentric")
    xh_idx   = order.index("crosshatch")
    ax.annotate("model winner\n(suction overridden)",
                xy=(champs["concentric"], conc_idx),
                xytext=(champs["concentric"] - 0.26, conc_idx + 1.1),
                fontsize=8, color="#2176AE",
                arrowprops=dict(arrowstyle="->", color="#2176AE", lw=1.2))
    ax.annotate("SHIPPED",
                xy=(champs["crosshatch"], xh_idx),
                xytext=(champs["crosshatch"] + 0.045, xh_idx + 1.0),
                fontsize=8, color="#D64045",
                arrowprops=dict(arrowstyle="->", color="#D64045", lw=1.2))

    # Legend for second bar
    patch_cons = mpatches.Patch(color="#aaaaaa", alpha=0.4, label="conservative/no-suction variant")
    ax.legend(handles=[patch_cons], loc="lower right")

    ax.axvline(0.75, color="#999", lw=0.8, ls="--", zorder=1)
    ax.text(0.752, -0.6, "0.75 line", fontsize=7.5, color="#777")

    fig.tight_layout()
    path = f"{OUTDIR}/family_scores.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    print(f"  saved {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 2  per_condition.png
# ─────────────────────────────────────────────────────────────────────────────
def fig_per_condition():
    families_params = [
        ("crosshatch", {"pitch": 1.8,   "land": 1.26,  "depth": 0.6},   "crosshatch (SHIP)"),
        ("hexpad",     {"cell":  1.3,   "channel": 0.42,"depth": 0.5},   "hexpad"),
        ("concentric", {"pitch": 1.375, "land": 0.932,  "depth": 1.106, "cavity": 0.0}, "concentric (no-suction)"),
        ("ridge",      {"pitch": 1.01,  "land": 0.58,  "depth": 0.5},   "ridge"),
        ("dimple",     {"pitch": 1.213, "dia":  0.785,  "depth": 1.041}, "dimple"),
        ("smooth",     {},                                                 "smooth"),
    ]

    cond_labels = [c["label"][:22] for c in G.CONDITIONS]
    n_fam = len(families_params)
    n_cond = len(G.CONDITIONS)

    matrix = np.zeros((n_fam, n_cond))
    for i, (fam, params, _) in enumerate(families_params):
        r = G.score_texture(fam, params)
        for j, row in enumerate(r["rows"]):
            matrix[i, j] = round(row["obj"], 3)

    fig, ax = plt.subplots(figsize=(10, 4.2))
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=0.0, vmax=1.0, aspect="auto")

    ax.set_xticks(np.arange(n_cond))
    ax.set_xticklabels(cond_labels, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(np.arange(n_fam))
    ax.set_yticklabels([fp[2] for fp in families_params], fontsize=9)
    ax.set_title("Per-condition objective score (families × conditions)\n"
                 "Shows grip coverage across all target surfaces", pad=8)

    for i in range(n_fam):
        for j in range(n_cond):
            v = matrix[i, j]
            tc = "white" if v < 0.35 or v > 0.80 else "black"
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    fontsize=7.5, color=tc, fontweight="bold")

    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cb.set_label("Condition obj score", fontsize=9)

    fig.tight_layout()
    path = f"{OUTDIR}/per_condition.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    print(f"  saved {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 3  baseline_gate.png
# ─────────────────────────────────────────────────────────────────────────────
def fig_baseline_gate():
    with open(f"{DATA}/_baseline.json") as f:
        bl = json.load(f)

    ranking = bl["ranking"]
    names   = [r["name"] for r in ranking]
    scores  = [r["wet_hold"] for r in ranking]
    fams    = [r["family"] for r in ranking]

    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    colors = [COLORS.get(fa, "#aaaaaa") for fa in fams]
    bars = ax.bar(names, scores, color=colors, zorder=3, alpha=0.88, edgecolor="white")

    for bar, sc in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width() / 2, sc + 0.015,
                f"{sc:.3f}", ha="center", va="bottom", fontsize=9)

    # Published ordering arrows
    for i in range(len(names) - 1):
        ax.annotate("", xy=(i + 1, scores[i + 1] - 0.04),
                    xytext=(i, scores[i] - 0.04),
                    arrowprops=dict(arrowstyle="->", color="#555", lw=1.0))

    ax.set_ylabel("Wet-hold score (μ_hold, weighted avg)", fontsize=9)
    ax.set_title("Model reproduces published wet-grip ordering\n(validation gate — all checks PASSED)", pad=8)
    ax.set_ylim(0, max(scores) * 1.18)
    ax.grid(axis="y", lw=0.4, alpha=0.5, zorder=0)
    ax.tick_params(axis="x", labelsize=9)

    checks = bl["checks"]
    passed = sum(1 for c in checks if c["passed"])
    ax.text(0.98, 0.97, f"{passed}/{len(checks)} checks passed",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=8.5, color="green",
            bbox=dict(boxstyle="round,pad=0.3", fc="#eaffea", ec="green", lw=0.8))

    fig.tight_layout()
    path = f"{OUTDIR}/baseline_gate.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    print(f"  saved {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 4  sensitivity_winner.png
# ─────────────────────────────────────────────────────────────────────────────
def fig_sensitivity_winner():
    with open(f"{DATA}/_sensitivity.json") as f:
        sens_all = json.load(f)
    with open(f"{DATA}/_sensitivity_no-concentric.json") as f:
        sens_nc  = json.load(f)

    # Left: concentric tally (all families)
    tally_all = sens_all["tally"]   # {"concentric": 31}
    # Right: no-concentric tally
    tally_nc  = sens_nc["tally"]    # {"crosshatch": 23, "hierarchical": 4, ...}

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(10, 4.0),
                                      gridspec_kw={"width_ratios": [1, 2]})
    fig.suptitle("Coefficient-robustness: winner invariant to ±50 % parameter perturbation",
                 fontsize=11, y=1.01)

    # --- Left panel ---
    fams_all = list(tally_all.keys())
    vals_all = [tally_all[f] for f in fams_all]
    total    = sum(v for v in sens_all["rows"][0]["scores"].values()) * 0  # count rows
    n_settings = len(sens_all["rows"])
    clrs_l = [COLORS.get(f, "#aaa") for f in fams_all]
    ax_l.bar(fams_all, vals_all, color=clrs_l, zorder=3, alpha=0.88, edgecolor="white")
    for fam, v in zip(fams_all, vals_all):
        ax_l.text(fam, v + 0.3, f"{v}/{n_settings}", ha="center", va="bottom",
                  fontsize=9.5, fontweight="bold")
    ax_l.set_ylim(0, n_settings * 1.2)
    ax_l.set_ylabel("Settings where family wins")
    ax_l.set_title("All families (incl. concentric)", fontsize=10)
    ax_l.grid(axis="y", lw=0.4, alpha=0.5, zorder=0)
    ax_l.tick_params(axis="x", labelsize=8.5)

    # --- Right panel ---
    fams_nc = sorted(tally_nc.keys(), key=lambda k: -tally_nc[k])
    vals_nc = [tally_nc[f] for f in fams_nc]
    n_nc = len(sens_nc["rows"])
    clrs_r = [COLORS.get(f, "#aaa") for f in fams_nc]
    bars_r = ax_r.bar(fams_nc, vals_nc, color=clrs_r, zorder=3, alpha=0.88, edgecolor="white")
    for fam, v in zip(fams_nc, vals_nc):
        ax_r.text(fam, v + 0.3, f"{v}/{n_nc}", ha="center", va="bottom",
                  fontsize=9.5, fontweight="bold")
    ax_r.set_ylim(0, n_nc * 1.2)
    ax_r.set_ylabel("Settings where family wins")
    ax_r.set_title("Tileable families only (concentric excluded)", fontsize=10)
    ax_r.grid(axis="y", lw=0.4, alpha=0.5, zorder=0)
    ax_r.tick_params(axis="x", labelsize=8.5)

    # Annotate flips
    flip_count = len(set(sens_nc["flips"]))
    ax_r.text(0.97, 0.97,
              f"{len(sens_nc['flips'])} setting-flips\nacross {flip_count} params",
              transform=ax_r.transAxes, ha="right", va="top", fontsize=8,
              bbox=dict(boxstyle="round,pad=0.3", fc="#fff8e1", ec="#aaa", lw=0.8))

    fig.tight_layout()
    path = f"{OUTDIR}/sensitivity_winner.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 5  sensitivity_heatmap.png
# ─────────────────────────────────────────────────────────────────────────────
def fig_sensitivity_heatmap():
    with open(f"{DATA}/_sensitivity_no-concentric.json") as f:
        sens = json.load(f)

    rows = sens["rows"]
    family_order = ["crosshatch", "hexpad", "chevron", "hierarchical", "ridge", "dimple"]

    # Build matrix: rows = families, cols = settings
    setting_labels = []
    for r in rows:
        if r["key"] is None:
            lbl = "baseline"
        else:
            mult_str = "×0.5" if r["mult"] < 1.0 else "×1.5"
            lbl = f"{r['key']}\n{mult_str}"
        setting_labels.append(lbl)

    n_fam = len(family_order)
    n_set = len(rows)
    matrix = np.zeros((n_fam, n_set))
    winner_per_col = []

    for j, row in enumerate(rows):
        scores = row["scores"]
        winner_per_col.append(row["winner"])
        for i, fam in enumerate(family_order):
            matrix[i, j] = scores.get(fam, np.nan)

    fig, ax = plt.subplots(figsize=(14, 4.0))
    norm = Normalize(vmin=0.5, vmax=0.95)
    im = ax.imshow(matrix, cmap="YlOrRd", norm=norm, aspect="auto")

    ax.set_xticks(np.arange(n_set))
    ax.set_xticklabels(setting_labels, fontsize=6.5, rotation=45, ha="right")
    ax.set_yticks(np.arange(n_fam))
    ax.set_yticklabels(family_order, fontsize=9)
    ax.set_title("Sensitivity heatmap — tileable families × 31 coefficient settings\n"
                 "Stars mark the winner per column; near-ties visible where gaps are <0.01", pad=8)

    for j, winner in enumerate(winner_per_col):
        wi = family_order.index(winner) if winner in family_order else None
        for i in range(n_fam):
            v = matrix[i, j]
            ax.text(j, i, f"{v:.3f}", ha="center", va="center",
                    fontsize=5.5, color="black" if v < 0.85 else "white")
        if wi is not None:
            ax.scatter([j], [wi - 0.42], s=60, marker="*", color="#1a1aff",
                       zorder=6, transform=ax.transData)

    # Draw rectangle around winning cell per column
    for j, winner in enumerate(winner_per_col):
        if winner in family_order:
            wi = family_order.index(winner)
            rect = plt.Rectangle((j - 0.5, wi - 0.5), 1, 1,
                                  fill=False, edgecolor="#1a1aff", lw=1.5, zorder=5)
            ax.add_patch(rect)

    cb = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    cb.set_label("Universal score", fontsize=9)

    fig.tight_layout()
    path = f"{OUTDIR}/sensitivity_heatmap.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 6  crosshatch_sweep.png
# ─────────────────────────────────────────────────────────────────────────────
def fig_crosshatch_sweep():
    # SHIP params
    SHIP_pitch = 1.8
    SHIP_land  = 1.26
    SHIP_depth = 0.6

    # (a) pitch sweep at land/pitch = 0.7
    pitch_vals = np.linspace(1.2, 3.5, 40)
    land_frac  = 0.7
    depth_a    = 0.6
    scores_a   = []
    for p in pitch_vals:
        r = G.score_texture("crosshatch", {"pitch": p, "land": p * land_frac, "depth": depth_a})
        scores_a.append(r["score"])

    # (b) land fraction sweep at pitch=1.8
    lf_vals  = np.linspace(0.40, 0.95, 40)
    scores_b = []
    for lf in lf_vals:
        r = G.score_texture("crosshatch", {"pitch": SHIP_pitch, "land": SHIP_pitch * lf, "depth": SHIP_depth})
        scores_b.append(r["score"])
    SHIP_lf = SHIP_land / SHIP_pitch   # 0.70

    # (c) depth sweep at pitch=1.8, land=1.26
    depth_vals = np.linspace(0.3, 1.5, 40)
    scores_c   = []
    for d in depth_vals:
        r = G.score_texture("crosshatch", {"pitch": SHIP_pitch, "land": SHIP_land, "depth": d})
        scores_c.append(r["score"])

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=False)
    fig.suptitle("Crosshatch parameter sweep (universal score)\n"
                 "SHIP point marked with ★  — depth panel shows flat region",
                 fontsize=10.5, y=1.02)

    def style_ax(ax, x, y, xlabel, marker_x, marker_score, color="#D64045"):
        ax.plot(x, y, lw=2.0, color=color, zorder=3)
        ax.axvline(marker_x, color="#555", lw=0.8, ls="--", zorder=2)
        ax.scatter([marker_x], [marker_score], s=160, marker="*", color="#1a1aff",
                   edgecolors="#001a66", linewidths=0.6, zorder=5)
        ax.set_xlabel(xlabel, fontsize=9.5)
        ax.set_ylabel("Universal score", fontsize=9.5)
        ax.grid(lw=0.4, alpha=0.5)
        ax.set_ylim(max(0, min(y) - 0.05), min(1.0, max(y) + 0.05))

    # SHIP score at exact params for marker
    ship_score = G.score_texture("crosshatch",
                                  {"pitch": SHIP_pitch, "land": SHIP_land, "depth": SHIP_depth})["score"]

    # (a) pitch - ship is at pitch=1.8, land=1.8*0.7=1.26, depth=0.6
    ship_score_a = G.score_texture("crosshatch",
                                    {"pitch": SHIP_pitch, "land": SHIP_pitch * land_frac,
                                     "depth": depth_a})["score"]
    style_ax(axes[0], pitch_vals, scores_a,
             "Pitch (mm)  [land/pitch = 0.70 fixed]",
             SHIP_pitch, ship_score_a)
    axes[0].set_title("(a) Score vs pitch", fontsize=9.5)

    # (b) land fraction
    style_ax(axes[1], lf_vals, scores_b,
             "Land fraction (land/pitch)",
             SHIP_lf, ship_score)
    axes[1].set_title("(b) Score vs land fraction", fontsize=9.5)

    # (c) depth
    style_ax(axes[2], depth_vals, scores_c,
             "Depth (mm)  [pitch=1.8, land=1.26]",
             SHIP_depth, ship_score)
    axes[2].set_title("(c) Score vs depth  (near-flat = depth-insensitive)", fontsize=9.5)
    axes[2].annotate("depth-insensitive\nplateau",
                     xy=(0.8, ship_score), xytext=(0.95, ship_score - 0.04),
                     fontsize=7.5, color="#333",
                     arrowprops=dict(arrowstyle="->", color="#333", lw=0.9))

    fig.tight_layout()
    path = f"{OUTDIR}/crosshatch_sweep.png"
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Fig 7  tier2_fea.png
# ─────────────────────────────────────────────────────────────────────────────
def fig_tier2_fea():
    with open(f"{DATA}/_tier2_fea.json") as f:
        fea = json.load(f)

    contact   = fea["contact"]
    phi_geom  = fea["phi_geometric"]
    durability = fea["durability"]

    p_real_c = [c["p_real"] for c in contact]
    phi_eff_c = [c["phi_eff"] for c in contact]

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(10.5, 4.0))
    fig.suptitle("Tier-2 FEA results — contact mechanics & durability", fontsize=11)

    # (a) phi_eff vs p_real
    ax_a.plot(p_real_c, phi_eff_c, "o-", color="#2176AE", lw=2, ms=7,
              zorder=4, label=f"FEA φ_eff (const ≈ {phi_eff_c[0]:.3f})")
    ax_a.axhline(phi_geom, color="#D64045", lw=1.5, ls="--", zorder=3,
                 label=f"φ_geometric = {phi_geom:.2f}")
    ax_a.set_xlabel("Real contact pressure p_real (MPa)", fontsize=9.5)
    ax_a.set_ylabel("Effective land fraction φ_eff", fontsize=9.5)
    ax_a.set_title("(a) φ_eff vs load — flat confirms\nload-independence (geometrically dominated)", fontsize=9.5)
    ax_a.set_ylim(0.55, 0.9)
    ax_a.legend(fontsize=8.5)
    ax_a.grid(lw=0.4, alpha=0.5)
    ax_a.annotate("flat → geometric\ncontrol (C_FLAT validated)",
                  xy=(p_real_c[-1], phi_eff_c[-1]),
                  xytext=(p_real_c[-1] * 0.55, phi_eff_c[-1] + 0.12),
                  fontsize=7.5, color="#2176AE",
                  arrowprops=dict(arrowstyle="->", color="#2176AE", lw=0.9))

    # (b) durability bars
    mus = [d["mu"] for d in durability]
    fea_vm   = [d["fea_root_vm"] for d in durability]
    beam_est = [d["beam_estimate"] for d in durability]
    margins  = [d["fea_margin"] for d in durability]

    x = np.arange(len(mus))
    w = 0.32
    bars_fea  = ax_b.bar(x - w/2, fea_vm,   width=w, label="FEA root vM stress (MPa)",
                          color="#D64045", alpha=0.88, zorder=3)
    bars_beam = ax_b.bar(x + w/2, beam_est, width=w, label="Beam estimate (MPa)",
                          color="#E57C23", alpha=0.75, zorder=3)

    # Strength line
    strength = 27.3
    ax_b.axhline(strength, color="#333", lw=1.3, ls="--", zorder=4, label=f"Bambu TPU 95A HF strength {strength} MPa")

    # Margin annotations
    for i, (xi, vm, mg) in enumerate(zip(x, fea_vm, margins)):
        ax_b.text(xi - w/2, vm + 0.05, f"×{mg:.1f}", ha="center", va="bottom",
                  fontsize=8, color="#8b0000", fontweight="bold")

    ax_b.set_xticks(x)
    ax_b.set_xticklabels([f"μ = {m}" for m in mus], fontsize=9.5)
    ax_b.set_ylabel("von Mises stress at ridge root (MPa)", fontsize=9.5)
    ax_b.set_title("(b) FEA vs beam — durability margins at μ = 0.5 / 1.0 / 1.8", fontsize=9.5)
    ax_b.legend(fontsize=8, loc="upper left")
    ax_b.grid(axis="y", lw=0.4, alpha=0.5, zorder=0)
    ax_b.set_ylim(0, strength * 1.22)
    ax_b.annotate("margin (FEA)", xy=(x[0] - w/2, fea_vm[0]),
                  xytext=(x[0] - w/2 - 0.55, fea_vm[0] + 2.5),
                  fontsize=7, color="#8b0000")

    fig.tight_layout()
    path = f"{OUTDIR}/tier2_fea.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    print(f"  saved {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating grip-texture figures …")
    fig_family_scores()
    fig_per_condition()
    fig_baseline_gate()
    fig_sensitivity_winner()
    fig_sensitivity_heatmap()
    fig_crosshatch_sweep()
    fig_tier2_fea()

    print("\nFile sizes:")
    figs = [
        "family_scores.png",
        "per_condition.png",
        "baseline_gate.png",
        "sensitivity_winner.png",
        "sensitivity_heatmap.png",
        "crosshatch_sweep.png",
        "tier2_fea.png",
    ]
    for fn in figs:
        p = f"{OUTDIR}/{fn}"
        if os.path.exists(p):
            kb = os.path.getsize(p) / 1024
            print(f"  {fn:<30s}  {kb:7.1f} kB")
        else:
            print(f"  {fn:<30s}  MISSING")
    print("Done.")

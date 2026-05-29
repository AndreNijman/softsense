"""Clean family-score bar chart (champion vs honest/conservative variant)."""
import os, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = os.path.join(os.path.dirname(__file__), "..", "pictures", "family_scores.png")

# (family, champion, conservative/honest-variant, note)
DATA = [
    ("smooth (control)", 0.251, None,  ""),
    ("dimple",           0.632, 0.554, "no-suction"),
    ("ridge",            0.754, 0.716, "1-axis only"),
    ("chevron",          0.797, 0.729, ""),
    ("hexpad",           0.798, 0.734, "robust runner-up"),
    ("hierarchical",     0.801, 0.789, "2-scale print risk"),
    ("crosshatch",       0.808, 0.746, "SHIPPED (>=0.5mm)"),
    ("concentric",       0.872, 0.851, "model winner - overridden"),
]
COL = dict(smooth="#bbbbbb", dimple="#888888", ridge="#8c7355", chevron="#e08a1e",
           hexpad="#3aa66f", hierarchical="#8a5fb0", crosshatch="#d1413c",
           concentric="#2f7fc0")

names = [d[0] for d in DATA]
champ = [d[1] for d in DATA]
cons = [d[2] for d in DATA]
y = np.arange(len(DATA))
fig, ax = plt.subplots(figsize=(10.5, 6.2))
for i, (nm, ch, co, note) in enumerate(DATA):
    base = nm.split()[0]
    c = COL.get(base, "#777")
    ax.barh(i + 0.16, ch, height=0.32, color=c, edgecolor="black", linewidth=0.5)
    ax.text(ch + 0.008, i + 0.16, f"{ch:.3f}", va="center", fontsize=9)
    if co is not None:
        ax.barh(i - 0.18, co, height=0.32, color=c, alpha=0.45,
                edgecolor="black", linewidth=0.4, hatch="//")
        ax.text(co + 0.008, i - 0.18, f"{co:.3f}", va="center", fontsize=8,
                color="#444")
    if note:
        ax.text(0.012, i + 0.16, note, va="center", ha="left", fontsize=8,
                color="white", fontweight="bold")

ax.axvline(0.75, color="grey", ls="--", lw=0.8, alpha=0.7)
ax.set_yticks(y); ax.set_yticklabels(names)
ax.set_xlim(0, 1.0); ax.set_xlabel("Universal grip score (weighted, 7-condition battery, 0-1)")
ax.set_title("Grip-texture families: champion (solid) vs honest/conservative variant (hatched)\n"
             "underwater soft gripper - Bambu TPU 95A HF, Bambu P1S 0.4mm")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(facecolor="#999", label="champion (model optimum)"),
                   Patch(facecolor="#999", alpha=0.45, hatch="//",
                         label="conservative / no-speculation variant")],
          loc="lower right", fontsize=9, framealpha=0.95)
plt.tight_layout()
plt.savefig(OUT, dpi=140)
print("wrote", OUT, os.path.getsize(OUT), "bytes")

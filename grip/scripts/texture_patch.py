"""Small flat texture patch for clear face-on renders (old ridges vs new crosshatch).
PATCH=crosshatch (default) or ridge. Built as gen_step() for the step+GLB pipeline."""
import os
from build123d import Box, Pos, Compound

SIZE = 13.0          # patch side (mm)
BASE = 1.4           # slab thickness


def gen_step():
    mode = os.environ.get("PATCH", "crosshatch")
    slab = Box(SIZE, SIZE, BASE)
    feats = []
    if mode == "ridge":                       # legacy single-axis ridges
        pitch, land, depth = 2.2, 1.8, 0.6
        n = int(SIZE / pitch)
        y0 = -(n - 1) * pitch / 2.0
        for i in range(n):
            y = y0 + i * pitch
            feats.append(Pos(0, y, BASE / 2 + depth / 2) * Box(SIZE, land, depth))
    else:                                      # crosshatch post grid
        pitch, land, depth = 1.8, 1.26, 0.6
        n = int(SIZE / pitch)
        c0 = -(n - 1) * pitch / 2.0
        for i in range(n):
            for j in range(n):
                x = c0 + i * pitch
                y = c0 + j * pitch
                feats.append(Pos(x, y, BASE / 2 + depth / 2) * Box(land, land, depth))
    part = slab
    for f in feats:
        part = part + f
    return part

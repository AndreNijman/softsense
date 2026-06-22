"""Shared grip-texture micro-relief height fields z(x,y) for each swept family.

Pure geometry, no side effects — safe to import. `relief(fam, params, X, Y)`
returns (Z mm, hmax mm) on the given meshgrid. Used by the 3D pattern render and
the 3D voxel-FEA render.
"""
import numpy as np

def band(coord, pitch, land):
    return ((coord % pitch) < land).astype(float)

def tri_wave(t, period):
    p = t % period
    return np.abs(p / period - 0.5) * 2.0

def hex_pads(X, Y, L, cell, channel, pointy=True):
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
            ax_, ay_ = np.abs(X - cx), np.abs(Y - cy)
            if pointy:
                inside = (ax_ <= ri) & (0.5 * ax_ + (np.sqrt(3) / 2) * ay_ <= ri)
            else:
                inside = (ay_ <= ri) & ((np.sqrt(3) / 2) * ax_ + 0.5 * ay_ <= ri)
            Z = np.where(inside, 1.0, Z)
    return Z

def dimples(X, Y, pitch, dia):
    r = dia / 2.0
    fx = (X % pitch) - pitch / 2.0
    fy = (Y % pitch) - pitch / 2.0
    return np.where((fx * fx + fy * fy) < r * r, 0.0, 1.0)

def relief(fam, p, X, Y, L):
    """Height field (mm) + max height for one family's champion geometry."""
    if fam == "ridge":
        h = p["depth"]; Z = band(X, p["pitch"], p["land"]) * h
    elif fam in ("crosshatch", "crosshatch_ship"):
        h = p["depth"]
        Z = band(X, p["pitch"], p["land"]) * band(Y, p["pitch"], p["land"]) * h
    elif fam == "chevron":
        h = p["depth"]
        xp = X + p["pitch"] * 0.9 * tri_wave(Y, 2.6)
        Z = band(xp, p["pitch"], p["land"]) * h
    elif fam == "hexpad":
        h = p["depth"]; Z = hex_pads(X, Y, L, p["cell"], p["channel"]) * h
    elif fam == "dimple":
        h = p["depth"]; Z = dimples(X, Y, p["pitch"], p["dia"]) * h
    elif fam == "concentric":
        h = p["depth"]; cx = cy = L / 2.0
        r = np.hypot(X - cx, Y - cy)
        Z = band(r, p["pitch"], p["land"]) * h
        Z = np.where(r < p.get("cavity", 0), 0.0, Z)
    elif fam == "hierarchical":
        Mh, mh = p["macro_depth"], p["micro_depth"]; h = Mh + mh
        Ml = p["macro_pitch"] - p["macro_channel"]
        macro = band(X, p["macro_pitch"], Ml) * band(Y, p["macro_pitch"], Ml)
        micro = band(X, p["micro_pitch"], p["micro_land"]) * \
                band(Y, p["micro_pitch"], p["micro_land"])
        Z = macro * (Mh + micro * mh)
    else:
        raise ValueError(fam)
    return Z, h

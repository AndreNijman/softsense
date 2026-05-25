"""Coefficient-sensitivity sweep -- the campaign's central honesty deliverable.

The Tier-1 model is a weighted sum of textbook terms; "family X wins" is partly a
consequence of the coefficients I chose. This perturbs every coefficient +-50%
(one at a time) and, AT EACH SETTING, RE-OPTIMISES every family (a fresh sweep)
and records the winner. A winner that holds across the whole perturbation set is
a real conclusion; one that flips is a coefficient-artifact and is reported as
such.

Re-optimising (not just re-scoring fixed champions) is the rigorous form: a
family may have a different optimum under different physics, so we give each
family its best shot under every coefficient setting before declaring a winner.

  python sensitivity.py [n_per_family]

Writes grip/iterations/_sensitivity.json and prints the winner table.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import grip_model as G
import sweep as S

OUT = os.path.join(os.path.dirname(__file__), "..", "iterations", "_sensitivity.json")
FAMILIES = ["ridge", "crosshatch", "chevron", "hexpad", "concentric", "dimple", "hierarchical"]

# coefficients to perturb, grouped by what they represent. Each is swept to
# 0.5x and 1.5x its baseline (some clamped to a sensible range).
PERTURB = [
    "TAU0", "ALPHA", "MU_FILM", "SKIN_SLICK", "EDGE_DEGLAZE", "CAP0",
    "EDGE_PIERCE", "LAND_CRIT", "ETA_FLOOR", "C_HYS", "C_EDGE", "C_FLAT",
    "SUCT_GAIN", "W_PRIMARY", "INCON_PEN",
]


def best_per_family(C, n, families=None):
    out = {}
    for fam in (families or FAMILIES):
        top, _ = S.sweep(fam, n_random=n, topk=1, C=C, write=False)
        out[fam] = top[0]["score"] if top else 0.0
    return out


def run(n=1500, exclude=()):
    fams = [f for f in FAMILIES if f not in exclude]
    settings = [("baseline", None, 1.0)]
    for k in PERTURB:
        settings.append((k, k, 0.5))
        settings.append((k, k, 1.5))

    rows = []
    base_factor = {"W_PRIMARY": (0.30, 0.90), "SKIN_SLICK": (0.27, 0.68),
                   "ETA_FLOOR": (0.27, 0.68)}  # keep these in [0,1]-ish bands
    for label, key, mult in settings:
        C = dict(G.COEFFS)
        if key is not None:
            base = G.COEFFS[key]
            if key in base_factor and mult != 1.0:
                C[key] = base_factor[key][0] if mult < 1 else base_factor[key][1]
            else:
                C[key] = base * mult
        scores = best_per_family(C, n, fams)
        winner = max(scores, key=scores.get)
        ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        rows.append(dict(setting=label, key=key, mult=mult,
                         value=(None if key is None else round(C[key], 4)),
                         winner=winner, scores={k: round(v, 4) for k, v in scores.items()},
                         top3=[(k, round(v, 4)) for k, v in ranked[:3]]))
        tag = "baseline" if key is None else f"{key} x{mult}"
        print(f"{tag:22s} -> winner={winner:11s} "
              + "  ".join(f"{k}={v:.3f}" for k, v in ranked[:3]))

    # invariance summary
    winners = [r["winner"] for r in rows]
    from collections import Counter
    tally = Counter(winners)
    print("\n=== winner tally across all settings ===")
    for fam, c in tally.most_common():
        print(f"  {fam:12s} wins {c}/{len(rows)} settings")
    flips = [r["setting"] for r in rows if r["winner"] != rows[0]["winner"]]
    print(f"\nbaseline winner: {rows[0]['winner']}")
    print(f"settings where winner changes: {flips if flips else 'NONE (invariant)'}")

    out_path = OUT if not exclude else OUT.replace(".json", "_no-" + "-".join(exclude) + ".json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(dict(baseline_winner=rows[0]["winner"], tally=dict(tally),
                   flips=flips, excluded=list(exclude), rows=rows),
              open(out_path, "w"), indent=2)
    return rows


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1500
    exclude = tuple(sys.argv[2].split(",")) if len(sys.argv) > 2 else ()
    run(n, exclude)

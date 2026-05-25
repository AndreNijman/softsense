"""Parameter-space sweep for ONE texture family (the swarm's workhorse).

Each family has a different parametrisation, so each gets its own bounded grid +
random refinement here. A swarm agent owns a family and runs:

  python sweep.py <family> [n_random] [topk]

It prints the top-K printable candidates by universal grip score and writes every
evaluated candidate to grip/iterations/_sweep_<family>.json. With a microsecond
model this evaluates 10^3-10^4 candidates per family in well under a second, so
"lots of sims" is literal -- the agent fan-out buys per-family narrative
ownership and bespoke parameter ranges, not raw compute.

All ranges are clipped to the printable envelope (Bambu P1S 0.4 nozzle / 0.16
layer): min feature/gap >= 0.42 mm.
"""
import sys, os, json, itertools, random
sys.path.insert(0, os.path.dirname(__file__))
import grip_model as G

ITER = os.path.join(os.path.dirname(__file__), "..", "iterations")
MINF = 0.42

# (param ranges per family) -- grid points; random fills the gaps
GRIDS = {
    "ridge":      dict(pitch=[1.0, 1.4, 1.8, 2.2, 2.6, 3.2, 4.0],
                       land=[0.45, 0.6, 0.8, 1.0, 1.3, 1.7],
                       depth=[0.3, 0.5, 0.7, 0.9, 1.2, 1.5]),
    "crosshatch": dict(pitch=[1.2, 1.6, 2.0, 2.6, 3.2, 4.0],
                       land=[0.45, 0.6, 0.8, 1.0, 1.3, 1.7],
                       depth=[0.3, 0.5, 0.7, 0.9, 1.2, 1.5]),
    "chevron":    dict(pitch=[1.2, 1.6, 2.0, 2.6, 3.2],
                       land=[0.45, 0.6, 0.8, 1.0, 1.3],
                       depth=[0.4, 0.6, 0.8, 1.0, 1.3],
                       angle=[25, 35, 45, 55, 65]),
    "hexpad":     dict(cell=[0.6, 0.8, 1.0, 1.3, 1.6, 2.0, 2.5],
                       channel=[0.42, 0.5, 0.6, 0.8, 1.0, 1.2],
                       depth=[0.3, 0.4, 0.5, 0.7, 0.9, 1.2]),
    "concentric": dict(pitch=[1.0, 1.3, 1.6, 2.0, 2.6, 3.0],
                       land=[0.45, 0.6, 0.8, 1.0, 1.3],
                       depth=[0.3, 0.5, 0.7, 0.9, 1.2],
                       cavity=[0.0, 0.2, 0.4, 0.6]),
    "dimple":     dict(pitch=[1.2, 1.6, 2.0, 2.6, 3.2, 4.0],
                       dia=[0.45, 0.6, 0.8, 1.0, 1.3, 1.7],
                       depth=[0.3, 0.5, 0.7, 0.9, 1.2]),
    "hierarchical": dict(macro_pitch=[3.0, 4.0, 5.0, 6.0],
                         macro_channel=[0.5, 0.7, 0.9, 1.2, 1.5],
                         macro_depth=[0.6, 0.9, 1.2, 1.5],
                         micro_pitch=[0.85, 1.0, 1.2, 1.5],
                         micro_land=[0.42, 0.5, 0.6, 0.8],
                         micro_depth=[0.16, 0.25, 0.35, 0.5]),
}
RANGES = {  # (lo, hi) continuous bounds for random sampling
    "ridge":      dict(pitch=(1.0, 4.2), land=(0.45, 2.0), depth=(0.3, 1.6)),
    "crosshatch": dict(pitch=(1.2, 4.2), land=(0.45, 2.0), depth=(0.3, 1.6)),
    "chevron":    dict(pitch=(1.2, 3.6), land=(0.45, 1.6), depth=(0.4, 1.4), angle=(20, 70)),
    "hexpad":     dict(cell=(0.6, 2.6), channel=(0.42, 1.3), depth=(0.3, 1.3)),
    "concentric": dict(pitch=(1.0, 3.2), land=(0.45, 1.6), depth=(0.3, 1.3), cavity=(0.0, 0.6)),
    "dimple":     dict(pitch=(1.2, 4.2), dia=(0.45, 2.0), depth=(0.3, 1.3)),
    "hierarchical": dict(macro_pitch=(3.0, 6.5), macro_channel=(0.5, 1.6), macro_depth=(0.6, 1.6),
                         micro_pitch=(0.85, 1.6), micro_land=(0.42, 0.9), micro_depth=(0.16, 0.5)),
}


def _grid_candidates(family):
    g = GRIDS[family]
    keys = list(g.keys())
    for combo in itertools.product(*(g[k] for k in keys)):
        yield dict(zip(keys, combo))


def _rand_candidates(family, n, seed=0):
    r = random.Random(seed)
    rg = RANGES[family]
    for _ in range(n):
        yield {k: round(r.uniform(lo, hi), 3) for k, (lo, hi) in rg.items()}


def sweep(family, n_random=4000, topk=12, seed=0, C=None, write=True):
    seen = set(); evals = []
    cands = list(_grid_candidates(family)) + list(_rand_candidates(family, n_random, seed))
    for p in cands:
        key = tuple(sorted((k, round(v, 2)) for k, v in p.items()))
        if key in seen:
            continue
        seen.add(key)
        r = G.score_texture(family, p, C)
        evals.append(r)
    evals.sort(key=lambda r: r["score"], reverse=True)
    printable = [e for e in evals if e["printable"]]
    if write:
        os.makedirs(ITER, exist_ok=True)
        json.dump(dict(family=family, n=len(evals),
                       top=[{k: e[k] for k in ("params", "score", "base", "incon", "label")}
                            for e in printable[:50]]),
                  open(os.path.join(ITER, f"_sweep_{family}.json"), "w"), indent=2)
    return printable[:topk], len(evals)


if __name__ == "__main__":
    family = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 4000
    topk = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    top, total = sweep(family, n, topk)
    print(f"=== {family}: {total} printable-or-not candidates evaluated, top {topk} ===")
    for e in top:
        print(f"  score={e['score']:.4f} base={e['base']:.4f} incon={e['incon']:.3f}  "
              f"{e['label']}   {e['params']}")

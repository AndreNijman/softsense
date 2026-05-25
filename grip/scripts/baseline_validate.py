"""GATE: does the Tier-1 model reproduce the PUBLISHED wet-grip ordering?

The model is a hypothesis. Before trusting it to rank thousands of textures, it
must rank five well-studied real patterns the way the wet-adhesion / wet-friction
literature does. If it doesn't, the model is wrong and the swarm is meaningless.

Expected ordering of WET grip (holding capacity on wet surfaces), worst -> best:

  smooth  <  parallel ridges  <  tire-tread (deep channels)  <  { tree-frog hex,
                                                                   octopus sucker }

Sources for the ordering:
  * Smooth elastomer hydroplanes on wet smooth surfaces; channels recover grip
    -- tire wet-skid engineering (Persson 2001; pneumatic-tyre tread design).
  * Tree-frog toe pads: hexagonal epithelial cells + drainage channel network
    give high WET friction/adhesion; the channels are the mechanism
    (Barnes 2007; Federle et al. 2006; Drotlef et al. 2013 bio-inspired pads).
  * Octopus suckers: structured concentric/grooved contact + micro-cavity
    suction give strong WET attachment (Tramacere et al. 2013;
    bio-inspired sucker adhesives, Baik et al. 2017 Nature).

We rank by mean holding-mu over the WET conditions (pure grip, no
printability/durability weighting -- those are engineering filters, not what the
wet-adhesion literature measures).

Exit 0 + write report if the ordering holds; exit 1 (and print the violation) if
not. The swarm runner imports `passes()` and refuses to run on a failed gate.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import grip_model as G

OUT = os.path.join(os.path.dirname(__file__), "..", "iterations", "_baseline.json")

# representative real-world geometries (mm), within the printable envelope
PATTERNS = [
    ("smooth",   "smooth",     {}),
    ("ridges",   "ridge",      dict(pitch=2.5, land=1.2, depth=0.6)),
    ("tread",    "crosshatch", dict(pitch=3.0, land=1.2, depth=1.0)),  # deep grooved blocks
    ("treefrog", "hexpad",     dict(cell=1.0, channel=0.5, depth=0.4)),
    ("sucker",   "concentric", dict(pitch=1.6, land=0.7, depth=0.6, cavity=0.4)),
]


def wet_hold(family, params, C=None):
    """Mean holding-mu over the wet conditions = the literature 'wet grip' proxy."""
    C = G.COEFFS if C is None else C
    geom = G.P.resolve(family, params)
    rows = [G.grip_in_condition(geom, c, C) for c in G.CONDITIONS if c["wet"]]
    return sum(r["mu_hold"] for r in rows) / len(rows)


def evaluate(C=None):
    res = [(name, fam, p, wet_hold(fam, p, C)) for (name, fam, p) in PATTERNS]
    res.sort(key=lambda r: r[3])                      # ascending wet grip
    order = [r[0] for r in res]
    return res, order


def passes(C=None, verbose=False):
    res, order = evaluate(C)
    h = {name: v for (name, _, _, v) in res}
    checks = [
        ("smooth is worst",        order[0] == "smooth"),
        ("ridges beat smooth",     h["ridges"] > h["smooth"]),
        ("tread beats ridges",     h["tread"] > h["ridges"]),
        ("treefrog beats tread",   h["treefrog"] > h["tread"]),
        ("sucker beats tread",     h["sucker"] > h["tread"]),
        ("bio pair on top",        set(order[-2:]) == {"treefrog", "sucker"}),
    ]
    ok = all(c[1] for c in checks)
    if verbose:
        print("wet-grip ranking (worst -> best):")
        for name, fam, p, v in res:
            print(f"  {name:9s} mu_hold={v:.3f}   [{fam}]")
        print("checks:")
        for label, c in checks:
            print(f"  [{'PASS' if c else 'FAIL'}] {label}")
        print(f"\nGATE: {'PASS' if ok else 'FAIL'}")
    return ok, res, checks


if __name__ == "__main__":
    ok, res, checks = passes(verbose=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(dict(passed=ok,
                   ranking=[dict(name=n, family=f, params=p, wet_hold=round(v, 4))
                            for (n, f, p, v) in res],
                   checks=[dict(check=l, passed=c) for (l, c) in checks]),
              open(OUT, "w"), indent=2)
    sys.exit(0 if ok else 1)

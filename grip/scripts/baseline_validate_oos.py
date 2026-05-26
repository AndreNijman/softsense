"""Out-of-sample test of the grip-model's literature gate.

The original ``baseline_validate.py`` tests the model against 5 reference
patterns (smooth, ridges, tread, treefrog, sucker). The [PLACEHOLDER] /
[ESTIMATE] coefficients in ``grip_model.COEFFS`` were chosen so the model
reproduces the published ordering of those 5; "the gate passes" is therefore
a sufficient-condition test (the model CAN be fit), not a true out-of-sample
test (the model GENERALISES).

This script adds 3 new reference patterns the model was NOT tuned on, each
testing a specific PHYSICAL PREDICTION of the model:

  1. ``hexpad_nochannel`` — hexpad with the drainage channel collapsed to the
     minimum-printable width (0.05 mm). Physically: a smooth post grid with
     no open channels cannot drain. The model's Reynolds-drainage term
     should drop wet grip back toward the smooth-control level.
     LITERATURE EXPECTATION (Drotlef et al. 2013, Federle et al. 2006): wet
     adhesion of biological pads collapses when the channel network is
     suppressed; tread that "fills in" with debris also loses wet skid.

  2. ``crosshatch_fine`` — crosshatch at a finer pitch (1.0 mm vs the
     reference 3.0 mm). Physically: finer pitch -> shorter drain path
     (half-land-width) -> faster Reynolds squeeze-film clearance -> higher
     wet grip up to the printability floor.
     LITERATURE EXPECTATION (Persson 2007, tyre-tread engineering): fine
     siping at the 0.5-1 mm scale beats coarse blocks on wet for short
     contact times.

  3. ``hexpad_coarse`` — hexpad at large cell (3.0 mm vs the reference
     1.0 mm). Physically: coarser cells -> longer drain path -> the
     squeeze-film term doesn't clear in T_GRASP -> wet grip drops back
     toward the smooth-control level.
     LITERATURE EXPECTATION (Barnes 2007, Federle et al. 2006): tree-frog
     pads at the optimal scale (~1 mm) outperform both finer and coarser
     versions.

If the model gets all three orderings right, that's some real out-of-sample
evidence. If not, that's an honest miss and the appropriate place to start
calibrating against a wider experimental dataset.

Numbers reported are ``mu_hold`` averaged over the wet conditions in
``grip_model.CONDITIONS`` (the same proxy as the in-sample gate).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import baseline_validate as BV
import grip_model as G


OOS_PATTERNS = [
    # name, family, params, literature-expected ordering vs anchor pattern
    dict(name="hexpad_nochannel",
         family="hexpad",
         params=dict(cell=1.0, channel=0.05, depth=0.4),
         anchor=("treefrog", "lower"),
         physical_prediction="no open channels -> no drainage -> wet grip "
                             "should drop toward smooth-control level"),
    dict(name="crosshatch_fine",
         family="crosshatch",
         params=dict(pitch=1.0, land=0.5, depth=0.6),
         anchor=("tread", "higher"),
         physical_prediction="finer pitch -> shorter drain path -> faster "
                             "squeeze-film clearance -> higher wet grip"),
    dict(name="hexpad_coarse",
         family="hexpad",
         params=dict(cell=3.0, channel=0.5, depth=0.4),
         anchor=("treefrog", "lower"),
         physical_prediction="coarser cells -> longer drain path -> Reynolds "
                             "squeeze-film doesn't clear in T_GRASP -> wet "
                             "grip drops toward smooth-control level"),
]


def wet_hold(family, params, C=None):
    return BV.wet_hold(family, params, C)


def run():
    C = G.COEFFS
    # in-sample baseline
    in_sample = []
    for (name, fam, p) in BV.PATTERNS:
        in_sample.append(dict(name=name, family=fam, params=p,
                              wet_hold=round(wet_hold(fam, p, C), 4)))
    in_sample.sort(key=lambda r: r["wet_hold"])
    anchors = {r["name"]: r["wet_hold"] for r in in_sample}

    # out-of-sample
    oos_results = []
    checks = []
    for spec in OOS_PATTERNS:
        mu_pred = wet_hold(spec["family"], spec["params"], C)
        anchor_name, expected_dir = spec["anchor"]
        anchor_mu = anchors[anchor_name]
        # "lower" means the new pattern should grip LESS than the anchor;
        # "higher" means the new pattern should grip MORE.
        if expected_dir == "lower":
            ok = mu_pred < anchor_mu
        else:
            ok = mu_pred > anchor_mu
        oos_results.append(dict(
            name=spec["name"], family=spec["family"], params=spec["params"],
            mu_hold_pred=round(mu_pred, 4),
            anchor=anchor_name, anchor_mu_hold=round(anchor_mu, 4),
            expected_direction=expected_dir, passes=bool(ok),
            physical_prediction=spec["physical_prediction"]))
        checks.append(bool(ok))

    summary = dict(
        in_sample_ordering=in_sample,
        out_of_sample_patterns=oos_results,
        n_passed=int(sum(checks)),
        n_total=len(checks),
        pass_fraction=round(sum(checks) / max(len(checks), 1), 3),
        notes=[
            "These OOS patterns are NEW parametric points that the [PLACEHOLDER] "
            "coefficients were NOT tuned on. Each tests one specific physical "
            "prediction of the model (no drainage, finer/coarser scale).",
            "A pass here is genuine generalisation evidence; a failure is a "
            "natural place to start calibrating against a wider experimental "
            "dataset. Either result is informative.",
            "The literature expectations are based on Persson (rubber friction & "
            "wet skid 2001, 2007), Barnes (tree-frog wet adhesion 2007), Federle "
            "et al. (tree-frog pad mechanics 2006), Drotlef et al. (bio-inspired "
            "wet adhesion 2013, 2019), and standard tyre-tread engineering. "
            "Absolute mu values are still rank-only.",
        ],
    )
    return summary


if __name__ == "__main__":
    out = run()
    print("=" * 64)
    print("In-sample ordering (the original 5 patterns):")
    for r in out["in_sample_ordering"]:
        print(f"  {r['name']:14s} mu_hold = {r['wet_hold']:.3f}   [{r['family']}]")
    print()
    print("Out-of-sample test patterns:")
    for r in out["out_of_sample_patterns"]:
        tag = "PASS" if r["passes"] else "FAIL"
        print(f"  [{tag}] {r['name']:18s} mu_hold = {r['mu_hold_pred']:.3f}   "
              f"vs {r['anchor']:9s} ({r['anchor_mu_hold']:.3f})   "
              f"expected {r['expected_direction']}")
        print(f"        prediction: {r['physical_prediction']}")
    print()
    print(f"OOS GATE: {out['n_passed']}/{out['n_total']} "
          f"({out['pass_fraction']:.0%})")
    print()
    for note in out["notes"]:
        print(f"  - {note}")

    outpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "iterations", "_baseline_validate_oos.json")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    json.dump(out, open(outpath, "w"), indent=2)
    print(f"\nwrote {outpath}")

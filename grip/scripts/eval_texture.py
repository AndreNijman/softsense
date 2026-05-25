"""Single-candidate grip-texture evaluator (verification + agent hand-off).

  python eval_texture.py <name> <family> '<params_json>'

Writes grip/iterations/<name>.json (full per-condition breakdown) and prints the
universal grip score. Used to VERIFY a swarm agent's claimed champion -- agents
report a champion, the orchestrator re-runs it here to confirm the number.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import grip_model as G

ITER = os.path.join(os.path.dirname(__file__), "..", "iterations")


def run(name, family, params):
    r = G.score_texture(family, params)
    os.makedirs(ITER, exist_ok=True)
    json.dump(r, open(os.path.join(ITER, f"{name}.json"), "w"), indent=2)
    return r


if __name__ == "__main__":
    name = sys.argv[1]; family = sys.argv[2]
    params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else G.P.DEFAULTS.get(family, {})
    r = run(name, family, params)
    print(f"[{name}] {family} score={r['score']:.4f} base={r['base']:.4f} "
          f"incon={r['incon']:.3f} printable={r['printable']}  | {r['label']}")
    print("  per-condition:")
    for row, cond in zip(r["rows"], G.CONDITIONS):
        print(f"    {cond['name']:13s} mu_hold={row['mu_hold']:.3f} psi={row['psi']:.2f} "
              f"phi={row['phi_eff']:.2f} margin={row['margin']:.1f} obj={row['obj']:.3f}")

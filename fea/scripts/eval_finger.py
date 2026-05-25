"""UNIVERSAL finger scorer.

A gripper finger is only good if it conforms to MANY shapes and sizes, not one.
This evaluates a candidate finger (production / finray2 / flexure generator + a
param set) across a BATTERY of rigid objects (circles + squares, several sizes,
a couple of heights) and reduces it to a single universality score that the agent
swarm maximises. The finger is meshed ONCE and reused for every object (only the
rigid object changes), so a full battery is a handful of cheap FEA solves.

Score per object (0..~1):
  wrap  = contact_arc_deg / 80           (how far around the object it conforms)
  even  = 1.2 - pressure_cov             (how evenly the contact pressure spreads)
  grip  = plateau in [12 .. 35] N        (firm but not crushing)
  safe  = (margin_x - 1.5) / 1.5         (von-Mises safety vs TPU strength)
  obj   = 0.35 wrap + 0.30 even + 0.20 grip + 0.15 safe   (hard-failed if unsafe)
Universal = mean(obj over battery) - 0.5 * grip_inconsistency   (penalise 7x swings)

Usage:
  python eval_finger.py <name> <gen> '<params_json>' [screen|full]
    gen = production | finray2 | flexure
  writes fea/iterations/<name>/eval.json and prints the score.
"""
import sys, os, json, time, traceback, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import iter_harness as H

ITER = H.ITERDIR

# battery: (shape, R/half-size, object-centre-y)
SCREEN = [("circle", 12, 80), ("circle", 30, 80), ("box", 20, 80)]  # small+large round + corner
FULL = [("circle", 12, 80), ("circle", 22, 80), ("circle", 35, 80),
        ("box", 22, 80), ("box", 14, 80), ("circle", 22, 64), ("circle", 22, 94)]


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _grip_term(g):
    if g < 5: return _clamp(g / 7.0, 0, 1) * 0.5     # too weak
    if g <= 12: return 0.5 + 0.5 * (g - 5) / 7.0
    if g <= 35: return 1.0                            # firm plateau
    if g <= 70: return _clamp(1.0 - (g - 35) / 35.0, 0, 1)  # crushing
    return 0.0


def obj_score(m):
    if m is None: return 0.0
    nodes = m.get("contact_nodes", 0) or 0
    margin = m.get("margin_x", 0) or 0
    grip = m.get("grip_at_press_N", 0) or 0
    cov = m.get("pressure_cov", 2.0)
    arc = m.get("contact_arc_deg", 0) or 0
    wrap = _clamp(arc / 80.0, 0, 1.25)
    even = _clamp(1.2 - cov, 0, 1)
    grp = _grip_term(grip)
    safe = _clamp((margin - 1.5) / 1.5, 0, 1)
    s = 0.35 * wrap + 0.30 * even + 0.20 * grp + 0.15 * safe
    if margin < 1.3 or grip < 2 or nodes < 3:     # unsafe / no-grip -> heavy penalty
        s *= 0.2
    if m.get("locked"):                           # rigid jaw that crushes, not a gripper
        s *= 0.15
    return s


def universal(results):
    scores = [obj_score(m) for (_, _, _, m) in results]
    grips = [(m.get("grip_at_press_N", 0) or 0) for (_, _, _, m) in results if m]
    base = float(np.mean(scores)) if scores else 0.0
    incon = 0.0
    if len(grips) >= 2 and np.mean(grips) > 1e-6:
        incon = float(np.std(grips) / np.mean(grips))
    return base - 0.5 * _clamp(incon - 0.4, 0, 1.0), base, incon


def evaluate(name, gen, params, mode="screen"):
    battery = SCREEN if mode == "screen" else FULL
    outdir = os.path.join(ITER, name); os.makedirs(outdir, exist_ok=True)
    H.REPORT_MODE = "grip"                         # fair: compare wrap at equal grip
    if mode == "screen":
        H.NSTEPS, H.MESH_MAX, H.MESH_MIN = 12, 2.4, 1.1
    else:
        H.NSTEPS, H.MESH_MAX, H.MESH_MIN = 24, 1.3, 0.5
    p = dict(params)
    if gen != "production":
        p["_gen"] = gen
    # mesh once (object-independent)
    p2d, tris, lm = H.regen_section(p, outdir)
    results = []
    for shape, R, yc in battery:
        H.OBJ_SHAPE = shape; H.R_NECK = float(R); H.YC = float(yc)
        try:
            sol = H.run_fea(p2d, tris, lm, verbose=False)
            m = H.metrics(sol)
        except Exception as e:
            m = None; print(f"  [{shape} R{R} y{yc}] FEA FAIL: {e}")
        results.append((shape, R, yc, m))
        if m:
            print(f"  {shape:6s} R{R:>2} y{yc:>2}: arc={m['contact_arc_deg']:5.1f} "
                  f"cov={m['pressure_cov']:.2f} grip={m['grip_at_press_N']:5.1f}N "
                  f"margin={m['margin_x']:.1f} -> obj={obj_score(m):.3f}")
    score, base, incon = universal(results)
    out = dict(name=name, gen=gen, mode=mode, params=params,
               score=round(score, 4), base=round(base, 4), grip_incon=round(incon, 3),
               n_nodes=int(p2d.shape[0]),
               objects=[dict(shape=s, R=R, yc=yc, metrics=m) for (s, R, yc, m) in results])
    json.dump(out, open(os.path.join(outdir, "eval.json"), "w"), indent=2)
    return score, out


if __name__ == "__main__":
    name = sys.argv[1]; gen = sys.argv[2]
    params = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    mode = sys.argv[4] if len(sys.argv) > 4 else "screen"
    t0 = time.time()
    try:
        score, out = evaluate(name, gen, params, mode)
        print(f"[{name}] gen={gen} mode={mode} SCORE={score:.4f} "
              f"(base={out['base']:.3f} grip_incon={out['grip_incon']:.2f}) "
              f"in {time.time()-t0:.0f}s")
    except Exception:
        traceback.print_exc()
        print(f"[{name}] FAILED")
        sys.exit(1)

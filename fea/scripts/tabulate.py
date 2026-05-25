"""Tabulate metrics.json across iteration dirs for cross-shape/size comparison.
Usage: python tabulate.py <dir1> <dir2> ...   (names or full paths)"""
import sys, os, json

ITER = os.path.join(os.path.dirname(__file__), "..", "iterations")
cols = [("contact_nodes", "nodes", "%4d"), ("contact_arc_deg", "arc°", "%5.1f"),
        ("pressure_cov", "p_cov", "%5.2f"), ("contact_y_min", "y_lo", "%5.1f"),
        ("contact_y_max", "y_hi", "%5.1f"), ("mid_third_force_frac", "mid", "%4.2f"),
        ("top_third_force_frac", "top", "%4.2f"), ("grip_at_press_N", "grip_N", "%6.1f"),
        ("margin_x", "margin", "%5.1f"), ("max_von_mises_MPa", "vm_max", "%5.2f")]
print(f"{'iteration':<16}" + "".join(f"{c[1]:>7}" for c in cols))
print("-" * (16 + 7 * len(cols)))
for d in sys.argv[1:]:
    p = d if os.path.isdir(d) else os.path.join(ITER, d)
    try:
        m = json.load(open(os.path.join(p, "metrics.json")))
    except Exception as e:
        print(f"{os.path.basename(d):<16}  (no metrics: {e})"); continue
    row = f"{os.path.basename(d):<16}"
    for key, _, fmt in cols:
        v = m.get(key)
        row += (f"{fmt % v:>7}" if isinstance(v, (int, float)) else f"{'--':>7}")
    print(row)

"""Copy clip_stats into the bundle and write a human-readable STATS.md."""
import json, os, shutil

HERE = os.path.dirname(__file__)
FEA = os.path.normpath(os.path.join(HERE, "..", "render_bundle", "fea"))
shutil.copy2(os.path.join(HERE, "clip_stats.json"),
             os.path.join(FEA, "clip_stats.json"))

fr = json.load(open(os.path.join(FEA, "stats_finray.json")))
cl = json.load(open(os.path.join(FEA, "clip_stats.json")))
r = cl["results"]

md = f"""# Gripper FEA stats

## Fin Ray finger — nonlinear FEA (the centrepiece)
- Model: {fr['model']}
- Material: {fr['material']['name']}, E = {fr['material']['E_MPa']} MPa, ν = {fr['material']['nu']}
  ({fr['material']['note']})
- Mesh: {fr['mesh']['nodes']} nodes / {fr['mesh']['tris']} triangles, {fr['load_steps']} load steps
- **Peak grip load: {fr['grip_load_N']['max']:.2f} N** (applied contact-patch load = grip force)
- **Tip inward wrap: {fr['tip_wrap_mm']['inward_dx']:.1f} mm** (the Fin Ray conform)
- **Max von Mises: {fr['von_mises_MPa']['max']:.2f} MPa** → vs ~25–40 MPa TPU strength = **~10× margin** (gentle grip)
- Load-control limit point: {fr['limit_point_N']}

## Cover snap-clip — linear FEA corroboration
- Model: {cl['model']}, material {cl['material']['name']} (E {cl['material']['E_MPa']} MPa)
- Inputs: free length {cl['inputs']['free_len_mm']} mm, thickness {cl['inputs']['thickness_mm']} mm, tip deflection {cl['inputs']['tip_defl_mm']} mm
- **Nominal bending strain: {r['nominal_bending_strain']*100:.2f}%** (analytic {r['analytic_strain']*100:.2f}%, gate 1.5%) → margin {r['nominal_strain_margin']:.2f}×
- Sharp-clamp corner peak strain {r['sharp_corner_peak_strain']*100:.2f}% (SCF {r['stress_concentration_factor']:.2f}, mesh-singularity, mitigated by root fillet)
- Verdict: **{cl['verdict']}**

See FEA_NOTES.md for the exact-vs-approximated breakdown.
"""
open(os.path.join(FEA, "STATS.md"), "w").write(md)
print(md)

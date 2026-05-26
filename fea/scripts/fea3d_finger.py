"""DEPRECATED — use ``iter_harness.py`` instead.

This script was an earlier 3D corotational finger FEA, run on the MSI laptop
against a pre-meshed npz cross-section (``BUNDLE/fea/finray_morph.npz``). It
diverged from the production solver (``iter_harness.py``) in several ways
that mattered for reproducibility:

  =======================  fea3d_finger.py (old)   iter_harness.py (canonical)
  Material nu              0.45                    0.42
  Contact penalty K_PEN    1500 N/mm               2000 N/mm
  Press max                15 mm                   10 mm
  Newton max iters         14                      16
  Press steps              26                      24
  Source geometry          pre-meshed npz on MSI   gmsh-mesh from live CAD
  Path to bundle           hardcoded Windows path  GRIPPER_REPO env var

The Windows-hardcoded ``BUNDLE = r"C:\\Users\\andre\\gripper_render\\render_bundle"``
made the script unrunnable outside the original MSI laptop, and the parameter
drift made its results not directly comparable to the production harness.

The canonical 3D finger FEA is now ``fea/scripts/iter_harness.py``, which:

  * Meshes from the live ``gripper.py`` cross-section (no stale npz file
    dependency).
  * Discovers the repo root via the ``GRIPPER_REPO`` env var with a sensible
    file-relative fallback (portable across machines).
  * Records per-step Newton convergence telemetry (did_converge, max iters,
    final residual) in the metrics.json output.
  * Has the same corotational/penalty-contact formulation; only the
    parameters were drift-aligned.

If you need the old behaviour (nu=0.45 / K_PEN=1500 / press_max=15 / etc.) for
a one-off re-check, set the ``GRIPPER_NU`` env var and run iter_harness.py;
the other constants are exposed in ``iter_harness.py`` near the FROZEN scenario
block.

See ``docs/TESTING_AND_SIMULATION.md`` A.5 / A.11 for the methodology and
``docs/MSI_REMOTE.md`` for how the MSI was used for high-resolution runs.
"""
import sys
import os

print(
    "fea3d_finger.py is deprecated. Use:\n"
    "    python fea/scripts/iter_harness.py <name> '<params_json>'\n"
    "See the module docstring for the parameter mapping.",
    file=sys.stderr,
)
sys.exit(64)

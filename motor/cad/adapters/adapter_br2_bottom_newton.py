"""adapter_br2_bottom_newton.py — BlueROV2 bottom-panel Newton-footprint adapter.

Drops the gripper into the canonical Newton mounting slot on the underside of
the BlueROV2's 1/2" HDPE bottom panel. The mating geometry is taken verbatim
from BR drilling-template R1 (BR document
`NEWTON-GRIPPER-W-MOUNTHOLE-DRILLING-TEMPLATE-R1`, 2018-05-31), as catalogued in
`motor/interfaces/fixed-rov-chassis.md §3c`:

- 2× Ø5.5 mm M5 clearance holes drilled straight through the HDPE bottom panel.
- **100 mm pitch** between hole centres.
- **16/31 mm offsets** from the side edges.
- **16° angle** between the hole-pair line and the side edge.

> *The 16° tilt is the design insight.* Newton's bottom-panel mount is not
> orthogonal to the keel — the hole-pair line is canted ~16° so the gripper
> jaws clear the bottom panel and aim into the BR2's front-camera frustum.
> Any third-party gripper dropping into the Newton slot **must inherit this
> rotation**, or it points the wrong way. This adapter bakes the 16° as a
> geometric rotation (loft from a gripper-aligned bottom face to a 16°-canted
> top plate), not a comment, so the tilt is structural.

Orientation convention (adapter local frame, see `_base.py`):

- Origin: gripper-side bolt-pattern centroid on the mating face.
- +Z = away from gripper = toward BR2 belly. Top face (Z = ADAPTER_T)
  is the BR2-chassis-side; bottom face (Z = 0) is the gripper-side.
- +X = gripper jaw open/close axis. The M5 hole pair is rotated +16° from this
  axis in the XY plane so that, once bolted to the bottom panel, the gripper
  jaws point **down through the BR2 open frame into the camera FOV**.
- Bottom face: 96 × 28 mm enclosure footprint (4× M4 + shaft bore via `_base`).
- Top face: long thin plate aligned with the canted 100 mm M5 pitch line.

Fasteners (informational, not modelled): 2× M5×16 button-head socket cap,
316 SS, per BR Newton install guide.
"""
from __future__ import annotations

import math

from build123d import (
    Axis,
    Box,
    Color,
    Compound,
    Cylinder,
    Location,
    Part,
    Plane,
    Rectangle,
    Rot,
    extrude,
    fillet,
    loft,
)

from motor.cad.adapters import _base
from motor.cad.adapters._base import (
    GRIPPER_FLANGE_FOOTPRINT_X,
    GRIPPER_FLANGE_FOOTPRINT_Y,
    finalize,
    gripper_bolt_holes,
    m_clearance_radius,
    shaft_clearance_bore,
)

# ---------------------------------------------------------------------------
# Constants — dossier §3c
# ---------------------------------------------------------------------------

BR2_PITCH = 100.0           # mm, Newton hole pitch (dossier §3c table)
BR2_TILT_DEG = 16.0         # deg, hole-line angle to BR2 side edge (dossier §3c)
BR2_M5_R = m_clearance_radius(5)    # 2.75 mm; Ø5.5 matches BR template
ADAPTER_T = 10.0            # mm, adapter thickness (target ~8–12 mm)

# Top plate sizing — long thin strip running along the canted axis.
# Length must comfortably enclose the 100 mm pitch + bolt-head/wall margin.
TOP_PLATE_L = 116.0         # mm, along canted axis (±58 from origin → ≥8 mm past hole)
TOP_PLATE_W = 18.0          # mm, across canted axis (≥4 mm wall around Ø5.5 holes)
TOP_PLATE_FILLET = 4.0      # mm, vertical corner radius on the top plate ends

# ---------------------------------------------------------------------------


def build() -> Compound:
    """Build the BR2 bottom-panel Newton-footprint adapter.

    The body is a `loft` from the 96 × 28 gripper-side bottom rectangle
    (aligned with gripper +X) up to a long thin top plate that is rotated
    `BR2_TILT_DEG` about Z. The 16° appears as the rotation operator that
    builds the top sketch — the tilt is in the geometry, not a comment.
    """
    rad = math.radians(BR2_TILT_DEG)

    # --- Bottom (gripper-side) sketch: 96 × 28, gripper-aligned, Z = 0 ---
    bottom_sk = Plane.XY * Rectangle(
        GRIPPER_FLANGE_FOOTPRINT_X, GRIPPER_FLANGE_FOOTPRINT_Y
    )

    # --- Top (BR2-chassis-side) sketch: long thin plate at +16°, Z = T ---
    # The rotation is applied as a Plane transform: this is what makes the
    # 16° structural rather than cosmetic.
    top_plane = Plane.XY.offset(ADAPTER_T) * Rot(0, 0, BR2_TILT_DEG)
    top_sk = top_plane * Rectangle(TOP_PLATE_L, TOP_PLATE_W)

    # --- Loft the transition body between them ---
    body: Part = loft([bottom_sk, top_sk])

    # --- Subtract gripper-side features (bolts + shaft bore) via _base ---
    for hole in gripper_bolt_holes(ADAPTER_T):
        body -= hole
    body -= shaft_clearance_bore(ADAPTER_T)

    # --- BR2-side M5 clearance holes on the canted 100 mm pitch line ---
    # Positions follow from the 16° rotation: hole_k = R_z(16°) · (±50, 0, T).
    half = BR2_PITCH / 2.0
    for sign in (+1, -1):
        x = sign * half * math.cos(rad)
        y = sign * half * math.sin(rad)
        bore = Cylinder(radius=BR2_M5_R, height=ADAPTER_T + 2.0).moved(
            Location((x, y, ADAPTER_T / 2))
        )
        body -= bore

    # Light fillet on the top-plate vertical edges (cosmetic; safe because
    # those edges survive the loft as the four short corners of the top face).
    try:
        top_edges = (
            body.faces().sort_by(Axis.Z)[-1].edges()
        )
        body = fillet(top_edges, radius=1.5)
    except Exception:
        # Fillet is decorative; never block STEP export.
        pass

    return finalize(body, label="adapter_br2_bottom_newton")


def gen_step() -> Compound:
    """STEP CLI entry point."""
    return build()


if __name__ == "__main__":
    gen_step()

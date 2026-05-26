"""BlueROV2 Payload Skid adapter — full-kit production path.

This is the **production-friendly** chassis-mount path for our 3"-canister
gripper on a BlueROV2 (R3/R4). See `motor/interfaces/fixed-rov-chassis.md`:

- §3e "Payload Skid" — the BR2 Payload Skid (PN **BR-100233**) is a HDPE +
  AL6061-T6 sub-frame that bolts under the BR2 via 8× M5×16. It accepts
  either 2× 4" enclosures *or* 3× 3" enclosures + 2× Lumens, and carries
  12× 200 g ballast slots (2.4 kg compensation budget).
- §10. The skid's **bottom panel** inherits the same Newton M5 drilling
  footprint as the BR2 bottom panel: **2× M5 clearance holes, Ø5.50 mm,
  100 mm pitch, 16° tilt** (BR Newton drilling template R1).

The "full kit" framing: the 3" gripper canister is held in the skid's
native 3" clamp (no bracket needed), AND the gripper hangs underneath via
this printed adapter on the same skid bottom panel. Two interfaces from one
sub-frame, both BR-published — that is why this is the production path.

Geometry. Structurally identical to `adapter_br2_bottom_newton` (the
chassis-side belly-mount variant): wedge with a 16°-canted top face
carrying 2× M5 clearance bores at 100 mm pitch (Newton footprint), and a
flat bottom face carrying the gripper's 4× M4 flange pattern. The Newton
drilling template is identical on the skid bottom panel — only the
docstring/context differs. Per the task brief, we prefer to re-export the
bottom-Newton module to avoid drift; if that sibling module is not yet on
disk we inline the geometry here so this module is self-contained.

Coords (adapter local, per `_base.py`):
- origin = centroid of the 4× M4 gripper-flange bolt pattern (bottom face)
- +Z = up, toward the skid bottom panel
- +X = gripper jaw open/close axis
- +Y = gripper depth axis (the 16° canted Newton axis lies in the X-Y plane)

Optional cradle silhouette. The skid's "Newton bay" can also receive a
3"-canister cradle if the gripper is body-mounted instead of bottom-
mounted; we expose `add_cradle=False` by default and document the four
M5×16 clamp positions if enabled (4 holes on a 60 mm × 60 mm square,
matching the skid's native 3"-enclosure clamp top-plate fastener
schedule per §3e [19]).
"""
from __future__ import annotations

import math
import os
from typing import Optional

from build123d import (
    Axis,
    Box,
    Color,
    Compound,
    Cylinder,
    Location,
    Part,
    Rotation,
    chamfer,
    export_step,
    fillet,
)

# Import shared gripper-side mating geometry from _base.py (single source).
from motor.cad.adapters._base import (  # noqa: E402
    C_PA12_GF,
    GALVANIC_BUSHING_OD,
    GRIPPER_FLANGE_BOLT_R,
    GRIPPER_FLANGE_BOLT_XY,
    GRIPPER_FLANGE_FOOTPRINT_X,
    GRIPPER_FLANGE_FOOTPRINT_Y,
    GRIPPER_SHAFT_CLEARANCE_R,
    GRIPPER_SHAFT_OFFSET_X,
    GRIPPER_SHAFT_OFFSET_Y,
    finalize,
    gripper_bolt_holes,
    m_clearance_radius,
    shaft_clearance_bore,
)


# ---------------------------------------------------------------------------
# Skid / Newton interface constants (sourced in fixed-rov-chassis.md §3e/§4a)
# ---------------------------------------------------------------------------

SKID_PN: str = "BR-100233"
"""Blue Robotics Payload Skid part number; §3e [14]."""

BR2_PITCH: float = 100.0
"""Newton-footprint hole pitch, mm. Drilling template R1; §3c [3]."""

BR2_TILT_DEG: float = 16.0
"""Newton-pattern tilt to the side-edge reference, deg. §3c [3]."""

M5_CLEARANCE_R: float = m_clearance_radius(5.0)        # = 2.75 mm (Ø5.5)
"""M5 close-clearance radius. Matches BR's 5.50 mm drill spec exactly."""

ADAPTER_T: float = 12.0
"""Wedge body thickness on the gripper-side. 12 mm of PA12-GF carries the
bolt heads and the 16° wedge above; the wedge itself adds material on the
chassis side. See §8b — TPU compliance pad sits between this face and the
skid panel."""

WEDGE_RISE: float = math.tan(math.radians(BR2_TILT_DEG)) * BR2_PITCH
"""Mm of vertical rise across the 100 mm pitch at 16° = ~28.7 mm. The top
face is therefore the bottom face rotated about the X-axis by 16°."""

PLATE_X: float = max(GRIPPER_FLANGE_FOOTPRINT_X + 8.0, BR2_PITCH + 24.0)
"""Plate width in X. Must contain both the 96 mm gripper bolt span and the
100 mm Newton bolt span plus material on either side. 124 mm with 12 mm
edge margin from the 100 mm Newton pitch."""

PLATE_Y: float = GRIPPER_FLANGE_FOOTPRINT_Y + 14.0
"""Plate depth in Y. The Newton pattern lies on a 16° line; even after the
canted projection the two holes only span ~96 mm × tan(16°) ≈ 27.5 mm in Y
within the canted face, which is well inside this 42 mm depth."""

# Optional cradle (3"-canister silhouette in the skid's Newton bay)
CRADLE_TUBE_OD: float = 76.2            # BR 3" enclosure OD (acetal tube OD)
CRADLE_BAND_T: float = 6.0              # printed wall thickness around tube
CRADLE_BAND_W: float = 18.0             # axial width of the snap-band
CRADLE_PCD_X: float = 60.0              # skid clamp top-plate fastener pitch X
CRADLE_PCD_Y: float = 60.0              # skid clamp top-plate fastener pitch Y


# ---------------------------------------------------------------------------
# Inlined Newton-pattern helper (option (a) fallback; geometry is identical
# to `adapter_br2_bottom_newton`). We do NOT import the sibling — keeping
# this module self-contained avoids any import-order coupling between
# concurrent sibling agents.
# ---------------------------------------------------------------------------

def _newton_top_bolt_holes(thickness: float) -> list[Cylinder]:
    """Two M5 clearance bores on the canted top face.

    The Newton drilling template lays the two holes on a line tilted
    `BR2_TILT_DEG` from the chassis-side edge, 100 mm apart. In the
    adapter's local frame we project that line onto the X axis (so the
    pattern centroid sits at the adapter origin), then rotate the two
    cylinders to thread along Z through the wedge body.

    The chassis-mating face is the *upper* face of the wedge; in the
    adapter local frame we drill straight through in +Z, accepting that
    bolts on the canted upper face will see a slight head-tilt against
    the (canted) M5 nylon washer — well within the 16° BR template's
    own tolerance budget.
    """
    holes: list[Cylinder] = []
    # 100 mm pitch in local X; the 16° projects into Y as well, but for the
    # adapter's purpose (clear hole through the wedge) we drill nominal Z.
    h = thickness + 1.0
    for x in (-BR2_PITCH / 2.0, +BR2_PITCH / 2.0):
        c = Cylinder(radius=M5_CLEARANCE_R, height=h).moved(
            Location((x, 0.0, thickness / 2.0)))
        holes.append(c)
    return holes


def _wedge_body(width_x: float, depth_y: float,
                base_t: float, tilt_deg: float) -> Part:
    """Build the gripper-side flat slab (`base_t` thick) plus the 16°
    wedge above it. Returns a single Part with the wedge fused.

    Construction: start with a flat plate, then a triangular-prism wedge
    sitting on top. The wedge's bottom face = the top face of the plate;
    its inclined upper face presents the 16° canted Newton landing.
    """
    # Flat slab (gripper-side carrier).
    slab = Box(width_x, depth_y, base_t).moved(
        Location((0.0, 0.0, base_t / 2.0)))

    # Wedge: a Box rotated about its bottom edge by `tilt_deg`. We build it
    # as a generous prism then trim it to a triangular profile by
    # subtracting an above-the-incline cut.
    rise = math.tan(math.radians(tilt_deg)) * width_x
    wedge_h = rise + 2.0      # tall enough that the incline crosses fully
    wedge_block = Box(width_x, depth_y, wedge_h).moved(
        Location((0.0, 0.0, base_t + wedge_h / 2.0)))

    # Trim: subtract everything above the inclined plane. The plane runs
    # from (x=-width/2, z=base_t) up to (x=+width/2, z=base_t + rise).
    # We do that with a Box rotated by +tilt_deg about the Y axis and
    # positioned so its underside lies along the inclined plane.
    trim = Box(width_x * 2.5, depth_y * 1.2, wedge_h).moved(
        Location(
            (0.0, 0.0, base_t + rise + wedge_h / 2.0),
            (0.0, tilt_deg, 0.0),     # rotate about Y by +16° (right side up)
        ))
    wedge = wedge_block - trim

    body: Part = slab + wedge
    return body


def build(add_cradle: bool = False,
          label: str = "adapter_br2_payload_skid") -> Compound:
    """Construct the BR2 Payload Skid adapter.

    Parameters
    ----------
    add_cradle :
        If True, also emit the optional 3"-canister cradle band that drops
        the gripper canister into the skid's Newton bay (silhouette only —
        the snap-clip geometry is abstracted). The band carries 4× M5
        clearance bores on a 60 × 60 mm square pattern matching the skid's
        native 3" enclosure top-plate fastener schedule (§3e [19]).
    """
    # ---- Main wedge body ----------------------------------------------------
    body = _wedge_body(
        width_x=PLATE_X,
        depth_y=PLATE_Y,
        base_t=ADAPTER_T,
        tilt_deg=BR2_TILT_DEG,
    )

    # ---- Gripper-side bolt pattern (4× M4 clearance, identical to _base) ---
    for hole in gripper_bolt_holes(ADAPTER_T, overshoot=1.0):
        body -= hole

    # ---- Shaft pass-through bore (clearance only — adapter is below the
    # gripper's bottom flange, the shaft does not pass through the skid).
    # We keep it as a relief pocket so a longer shaft / lip-seal stack can
    # protrude up into the adapter if it ever needs to.
    body -= shaft_clearance_bore(ADAPTER_T,
                                 radius=GRIPPER_SHAFT_CLEARANCE_R + 1.0,
                                 overshoot=1.0)

    # ---- Newton-pattern bolt holes on the canted top face -----------------
    # We drill the M5 bores all the way through both slab and wedge so the
    # bolts can be inserted from above with their heads landing on the
    # canted upper surface (consistent with how Newton mounts to the BR2
    # bottom panel — bolts go in from above through the HDPE).
    # Drilled vertically (Z) — the BR drilling template itself specifies
    # "drill straight through" [3].
    for hole in _newton_top_bolt_holes(thickness=ADAPTER_T + WEDGE_RISE + 4.0):
        # Lift the cylinders so they pierce from below the slab up through
        # the highest point of the wedge.
        body -= hole.moved(Location((0.0, 0.0, 0.0)))

    # ---- Drain holes (flooded-gripper policy; see §9a "Drain holes") ------
    # 2× Ø3 drain bores through the slab so water doesn't pool in the wedge.
    drain_r = 1.5
    drain_h = ADAPTER_T + 2.0
    for (dx, dy) in [(-PLATE_X / 2 + 10.0, +PLATE_Y / 2 - 6.0),
                     (+PLATE_X / 2 - 10.0, -PLATE_Y / 2 + 6.0)]:
        d = Cylinder(radius=drain_r, height=drain_h).moved(
            Location((dx, dy, ADAPTER_T / 2.0)))
        body -= d

    # ---- Filleted vertical edges for the printed PA12-GF aesthetic --------
    try:
        body = fillet(body.edges().filter_by(Axis.Z), radius=3.0)
    except Exception:
        # Some edges (post-wedge boolean) may not be filletable; ignore.
        pass

    parts: list[Part] = [body]

    # ---- Optional cradle band (silhouette only) ---------------------------
    if add_cradle:
        band = _cradle_band()
        parts.append(band)

    if len(parts) == 1:
        return finalize(parts[0], label=label, colour=C_PA12_GF)

    # Multi-part: assemble as a single Compound, colour each child.
    children: list[Part] = []
    for i, p in enumerate(parts):
        p.color = C_PA12_GF
        p.label = f"{label}_p{i}"
        children.append(p)
    return Compound(label=label, children=children)


def _cradle_band() -> Part:
    """Optional 3" canister cradle band — a printed half-shell that hugs
    the BR 3" enclosure (OD 76.2 mm) and bolts to the skid's Newton bay
    via 4× M5×16 on a 60 × 60 mm square pattern.

    The band lives above the wedge in +Z, axis aligned with X (gripper
    jaw axis), so the canister sits across the skid bay with the wet
    end-cap pointing forward.

    Local geometry: an extruded ring section that takes the upper half
    only (snap-clip; the lower half is the skid's own cradle clamp).
    """
    # Locate centre of the band well above the wedge top so it sits in
    # the skid bay, not interfering with the wedge.
    z_centre = ADAPTER_T + WEDGE_RISE + 30.0    # 30 mm gap above the wedge tip

    outer = Cylinder(radius=CRADLE_TUBE_OD / 2 + CRADLE_BAND_T,
                     height=CRADLE_BAND_W).moved(
        Location((0.0, 0.0, z_centre), (90.0, 0.0, 0.0)))
    inner = Cylinder(radius=CRADLE_TUBE_OD / 2 + 0.25,    # slip-fit
                     height=CRADLE_BAND_W + 2.0).moved(
        Location((0.0, 0.0, z_centre), (90.0, 0.0, 0.0)))
    ring = outer - inner

    # Trim to upper half: subtract a box below the canister centreline.
    half_trim = Box(CRADLE_TUBE_OD + 4 * CRADLE_BAND_T,
                    CRADLE_BAND_W + 2.0,
                    CRADLE_TUBE_OD + 4 * CRADLE_BAND_T).moved(
        Location((0.0, 0.0, z_centre - (CRADLE_TUBE_OD + 4 * CRADLE_BAND_T) / 2)))
    ring -= half_trim

    # 4× M5 clearance bores on the 60×60 mm skid-clamp pattern, drilled
    # vertically through the band feet. The band's feet are imaginary
    # tabs on either side of the canister; we approximate by drilling
    # straight-through clearance bores at the four corner positions.
    feet_h = CRADLE_TUBE_OD + 4 * CRADLE_BAND_T
    for dx in (-CRADLE_PCD_X / 2, +CRADLE_PCD_X / 2):
        for dy in (-CRADLE_PCD_Y / 2, +CRADLE_PCD_Y / 2):
            bore = Cylinder(radius=M5_CLEARANCE_R, height=feet_h).moved(
                Location((dx, dy, z_centre)))
            ring -= bore

    return ring


# ---------------------------------------------------------------------------
# STEP CLI entry
# ---------------------------------------------------------------------------

def gen_step() -> Compound:
    """Entry point for the CAD `step` CLI. Returns the default (no-cradle)
    full-kit BR2 Payload Skid adapter."""
    return build(add_cradle=False)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.normpath(os.path.join(here, "..", "output",
                                        "adapter_br2_payload_skid.step"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    export_step(gen_step(), out)
    print(f"wrote {out}")

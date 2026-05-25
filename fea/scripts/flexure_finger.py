"""Monolithic compliant FLEXURE finger generator (universal-adaptive R&D).

A single TPU print: a tapered strip whose bending is localised at thin FLEXURE
NECKS (living hinges) between stiffer pads, optionally PRE-CURVED so it wants to
curl inward. One actuator input (the four-bar pushing the base in) distributes
across the flexures so each segment settles on the local object shape -> wrap +
even pressure on ANY shape, with no tendons/springs/pins (underwater + no
maintenance). Mount bores stay at the four-bar pivots C, D.

Frame (model XY, like finray2): CONTACT face at small x (toward the object on -X),
SPINE at large x, interior +X. Notches on the SPINE side open under contact load
-> promote inward curl; on the CONTACT side -> the opposite; "both" -> a central
neck. The FEA swarm searches which (with pre-curve, neck thickness, count, taper).
"""
import math
import gripper
from build123d import Cylinder, Location

_poly_solid = gripper._poly_solid


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


DEFAULTS = dict(
    base_width=22.0, tip_width=7.0,      # strip width (contact->spine), tapering
    precurve=0.0,                        # inward (-X) tip offset, parabolic (mm)
    n_flex=4,                            # number of flexure necks
    flex_t=1.4,                          # neck thickness left at a flexure (mm)
    flex_h=3.0,                          # notch height along Y (mm)
    flex_side="spine",                   # "spine" | "contact" | "both"
    inset_base=7.0, inset_tip=4.0,       # keep flexures off the bracket / apex
    bracket_w=13.0, contact_x0=1.0,
    taper_pow=1.0,                       # width taper exponent (1=linear)
)


def build(C, D, z0, thickness, P=None):
    p = dict(DEFAULTS); p.update(P or {})
    base_y = max(C[1], D[1]) - gripper.FR_BASE_DROP
    L = gripper.FR_BLADE_LEN * gripper.FINGER_SCALE
    tip_y = base_y + L
    cx0 = p["contact_x0"]; bw, tw = p["base_width"], p["tip_width"]
    side = p["flex_side"]

    def frac(y):
        return _clamp((y - base_y) / L, 0.0, 1.0)

    def width(y):
        return bw + (tw - bw) * (frac(y) ** p["taper_pow"])

    def xcurve(y):
        return -p["precurve"] * frac(y) ** 2          # curl toward the object (-X)

    def cx(y):
        return cx0 + xcurve(y)

    def sx(y):
        return cx0 + width(y) + xcurve(y)

    ns = 48
    ys = [base_y + L * i / ns for i in range(ns + 1)]
    contact_edge = [(cx(y), y) for y in ys]
    spine_edge = [(sx(y), y) for y in ys]
    strip = _poly_solid(contact_edge + list(reversed(spine_edge)), z0, thickness)
    finger = strip + gripper.link_bar(C, D, p["bracket_w"], z0, thickness, "br", gripper.TPU)

    # flexure notches
    y_lo = base_y + p["inset_base"]; y_hi = tip_y - p["inset_tip"]
    n = max(0, int(p["n_flex"]))
    h = p["flex_h"] / 2.0; ft = p["flex_t"]
    if n >= 1 and y_hi > y_lo:
        pitch = (y_hi - y_lo) / n
        for i in range(n):
            yc = y_lo + (i + 0.5) * pitch
            w = width(yc)
            if w - ft < 0.6:                          # neck would be wider than strip
                continue
            cuts = []
            if side in ("spine", "both"):
                x0n = (cx(yc) + ft) if side == "spine" else ((cx(yc) + sx(yc)) / 2 + ft / 2)
                cuts.append([(x0n, yc - h), (sx(yc) + 1.0, yc - h),
                             (sx(yc) + 1.0, yc + h), (x0n, yc + h)])
            if side in ("contact", "both"):
                x1n = (sx(yc) - ft) if side == "contact" else ((cx(yc) + sx(yc)) / 2 - ft / 2)
                cuts.append([(cx(yc) - 1.0, yc - h), (x1n, yc - h),
                             (x1n, yc + h), (cx(yc) - 1.0, yc + h)])
            for q in cuts:
                try:
                    finger -= _poly_solid(q, z0 - 1.0, thickness + 2.0)
                except Exception:
                    pass

    for hp in (C, D):
        try:
            finger -= Cylinder(radius=gripper.MOUNT_HOLE_R, height=thickness * 3).moved(
                Location((hp[0], hp[1], z0 + thickness / 2.0)))
        except Exception:
            pass

    finger.label = "flexure_finger"
    lm = dict(C=list(C), D=list(D), r_bore=gripper.MOUNT_HOLE_R,
              base_y=base_y, tip_y=tip_y)
    return finger, lm

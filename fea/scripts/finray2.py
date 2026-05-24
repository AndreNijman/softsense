"""Fully-parametric Fin Ray finger section generator for topology R&D.

Independent of gripper.py's production finger so topology (beam angles, rib
direction/angle, aspect ratio, wall split) can be explored freely. Produces a
build123d solid (the section extruded over the finger thickness) that the FEA
harness sections + meshes exactly like the production finger. Once a topology is
found that genuinely WRAPS (tip curls toward the object, contact patch grows), the
winning shape is ported back into gripper.py's finray_finger_closed.

Mount bores stay at the real four-bar pivots C, D (the finger must bolt to the
coupler). Everything else is free.

Geometry (model XY, contact face faces -X toward the object):
  contact beam : line (contact_x_base, base_y) -> (contact_x_tip, tip_y)
  spine  beam : line (spine_x_base,  base_y) -> (spine_x_tip,  tip_y)
  ribs        : n_ribs cross-members, slant set by rib_dir * cot(rib_angle)
"""
import math
import gripper
from build123d import Cylinder, Location, Axis

_poly_solid = gripper._poly_solid

DEFAULTS = dict(
    contact_x_base=1.0, contact_x_tip=1.0,     # vertical contact face (= production)
    spine_x_base=23.0, spine_x_tip=6.0,        # spine converges to tip
    inset_base=4.0, inset_tip=3.0,
    t_contact=2.8, t_spine=2.8, t_rib=2.8,
    n_ribs=10, rib_angle_deg=38.0, rib_dir=+1, # +1 = slant up toward spine
    bracket_w=13.0,
)


def build(C, D, z0, thickness, P=None):
    p = dict(DEFAULTS); p.update(P or {})
    base_y = max(C[1], D[1]) - gripper.FR_BASE_DROP
    tip_y = base_y + gripper.FR_BLADE_LEN * gripper.FINGER_SCALE
    cxb, cxt = p["contact_x_base"], p["contact_x_tip"]
    sxb, sxt = p["spine_x_base"], p["spine_x_tip"]

    def cx(y):
        f = (y - base_y) / (tip_y - base_y); return cxb + (cxt - cxb) * f

    def sx(y):
        f = (y - base_y) / (tip_y - base_y); return sxb + (sxt - sxb) * f

    # outer frame (quad: contact-base, spine-base, spine-tip, contact-tip)
    outer = _poly_solid([(cxb, base_y), (sxb, base_y), (sxt, tip_y), (cxt, tip_y)],
                        z0, thickness)
    # mounting bracket: a bar linking the C and D eyes, fused to the frame base
    bracket = gripper.link_bar(C, D, p["bracket_w"], z0, thickness, "br", gripper.TPU)
    finger = outer + bracket

    # hollow: leave contact + spine beam walls
    y_lo = base_y + p["inset_base"]
    y_hi = tip_y - p["inset_tip"]

    def cav_c(y):
        return cx(y) + p["t_contact"]

    def cav_s(y):
        return sx(y) - p["t_spine"]

    while y_hi > y_lo and (cav_s(y_hi) - cav_c(y_hi)) < 2.0:
        y_hi -= 0.5
    nseg = 12
    ys = [y_lo + (y_hi - y_lo) * i / nseg for i in range(nseg + 1)]
    cav = [(cav_c(y), y) for y in ys] + [(cav_s(y), y) for y in reversed(ys)]
    finger = finger - _poly_solid(cav, z0 - 2.0, thickness + 4.0)

    # ribs
    ang = math.radians(p["rib_angle_deg"])
    shear = p["rib_dir"] * (math.cos(ang) / math.sin(ang))
    half = p["t_rib"] / 2.0
    pitch = (y_hi - y_lo) / p["n_ribs"]
    ribs = []
    for i in range(p["n_ribs"] + 1):
        yc = y_lo + i * pitch
        xa = cx(yc) + 0.3
        xb = sx(yc) - p["t_rib"] * 0.4
        if xb - xa <= 2.0:
            continue
        quad = [(xa, yc - half), (xb, yc - half),
                (xb + shear * p["t_rib"], yc + half), (xa + shear * p["t_rib"], yc + half)]
        try:
            ribs.append(_poly_solid(quad, z0, thickness) & outer)
        except Exception:
            pass
    for r in ribs:
        finger = finger + r

    # centreline trim (keep fingers from crossing x=0 at closed) + mount bores
    for hp in (C, D):
        finger -= Cylinder(radius=gripper.MOUNT_HOLE_R, height=thickness * 3).moved(
            Location((hp[0], hp[1], z0 + thickness / 2.0)))

    finger.label = "finger2"
    lm = dict(C=list(C), D=list(D), r_bore=gripper.MOUNT_HOLE_R,
              base_y=base_y, tip_y=tip_y)
    return finger, lm

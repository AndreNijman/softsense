"""Texture-family geometry -> physical descriptors for the grip model.

A grip texture is a surface relief on the finger contact face. Each *family* has a
fundamentally different parametrisation (ridge pitch != hex cell size != chevron
angle), so each is resolved here into the same neutral descriptor set that
`grip_model.py` consumes. Keeping geometry separate from physics means the swarm
agents can each own one family's parameter space without touching the physics.

Descriptor set (all lengths in mm, in the contact plane unless noted):
  phi        land fraction  = solid-contact area / nominal area, unloaded (geometric)
  w          characteristic LAND width (the contact island between channels)
  g          characteristic CHANNEL (gap) width
  lam        pitch = w + g
  h          channel / feature depth (how proud the lands stand)
  aspect     protruding-feature aspect ratio h / w_feat   (durability + printability)
  w_feat     width of the load-bearing protruding feature at its root (mm)
  min_feat   smallest printed dimension (mm)            (printability gate)
  drain_path characteristic water-escape path = half-distance land-centre->channel
  chan_cap   channel cross-section area available to carry squeezed water (mm^2/mm)
  n_drain    number of distinct channel directions (drainage isotropy: 1..~6)
  edge_dens  contact-edge length per unit area (1/mm)    (film piercing + hysteresis)
  land_char  characteristic land size (mm) for partial-slip edge efficiency
  M_primary  directional grip factor for the PRIMARY slip axis (pull-out), 0..1
  M_worst    directional grip factor for the WORST slip direction, 0..1
  suction    micro-suction potential 0..1 (speculative; dimple/sucker only)
  family, label, notes

Directional factors (M_*) rationale: slip resistance of a 1-D ridge ~ |sin(angle
between ridge and slip)|; mean over directions = 2/pi ~= 0.64, worst (along the
ridge) ~= base friction only. 2-D / iso patterns approach 1 in every direction.
These are family constants modulated by the geometry; see each branch.
"""
import math


def _post_phi(w, lam):
    """Area fraction of square posts on pitch lam with land width w (2-D grid)."""
    return (w / lam) ** 2


def resolve(family, p):
    """family: str; p: dict of params. Returns a descriptor dict."""
    g = dict(family=family, suction=0.0, notes="")
    f = family

    if f == "smooth":
        g.update(phi=1.0, w=10.0, g=0.0, lam=10.0, h=0.0, w_feat=10.0,
                 aspect=0.0, min_feat=10.0, drain_path=5.0, chan_cap=0.0,
                 n_drain=0, edge_dens=0.0, land_char=10.0,
                 M_primary=1.0, M_worst=1.0, label="smooth (control)")

    elif f == "ridge":
        # parallel ridges transverse to the primary (pull-out) slip axis.
        lam = float(p.get("pitch", 2.0)); w = float(p.get("land", 0.9))
        h = float(p.get("depth", 0.6))
        w = min(w, lam - 0.2)  # keep a channel
        gw = lam - w
        g.update(phi=w / lam, w=w, g=gw, lam=lam, h=h, w_feat=w,
                 aspect=h / max(w, 1e-3), min_feat=min(w, gw),
                 drain_path=w / 2.0, chan_cap=gw * h, n_drain=1,
                 edge_dens=2.0 / lam,                       # 2 edges per pitch, 1 axis
                 land_char=w,
                 M_primary=1.0,                              # full bite vs pull-out
                 M_worst=0.18,                               # slides along ridge axis
                 label=f"ridge p{lam:.1f}/w{w:.1f}/h{h:.1f}")

    elif f == "crosshatch":
        # two ridge sets -> square posts; drainage + edges in two axes.
        lam = float(p.get("pitch", 2.0)); w = float(p.get("land", 0.9))
        h = float(p.get("depth", 0.6))
        w = min(w, lam - 0.2); gw = lam - w
        phi = _post_phi(w, lam)
        g.update(phi=phi, w=w, g=gw, lam=lam, h=h, w_feat=w,
                 aspect=h / max(w, 1e-3), min_feat=min(w, gw),
                 drain_path=w / 2.0, chan_cap=gw * h, n_drain=2,
                 edge_dens=4.0 / lam, land_char=w,
                 M_primary=1.0, M_worst=0.72,                # 45 deg still bites
                 label=f"xhatch p{lam:.1f}/w{w:.1f}/h{h:.1f}")

    elif f == "chevron":
        # herringbone V: directional drainage + 2-direction grip.
        lam = float(p.get("pitch", 2.0)); w = float(p.get("land", 0.9))
        h = float(p.get("depth", 0.6)); ang = float(p.get("angle", 45.0))
        w = min(w, lam - 0.2); gw = lam - w
        iso = math.sin(math.radians(ang))                   # 0 (axial) .. 1 (transverse)
        g.update(phi=w / lam, w=w, g=gw, lam=lam, h=h, w_feat=w,
                 aspect=h / max(w, 1e-3), min_feat=min(w, gw),
                 drain_path=w / 2.0, chan_cap=gw * h, n_drain=2,
                 edge_dens=2.0 / lam, land_char=w,
                 M_primary=0.90 + 0.10 * iso,
                 M_worst=0.35 + 0.30 * iso,
                 label=f"chevron p{lam:.1f}/w{w:.1f}/{ang:.0f}deg")

    elif f == "hexpad":
        # tree-frog: flat-topped hex pads separated by a continuous channel network
        # in three directions. Best wet drainage per unit land area (Barnes/Federle).
        cell = float(p.get("cell", 1.2)); gw = float(p.get("channel", 0.5))
        h = float(p.get("depth", 0.5))
        lam = cell + gw
        # hex area fraction of pads on a hex lattice
        phi = (cell / lam) ** 2
        g.update(phi=phi, w=cell, g=gw, lam=lam, h=h, w_feat=cell,
                 aspect=h / max(cell, 1e-3), min_feat=min(cell, gw),
                 drain_path=cell / 3.0,                      # channel on ~3 sides
                 chan_cap=gw * h, n_drain=3,
                 edge_dens=6.0 / (lam * math.sqrt(3)),       # hex perimeter density
                 land_char=cell,
                 M_primary=0.97, M_worst=0.85,               # near isotropic
                 label=f"hexpad c{cell:.1f}/g{gw:.1f}/h{h:.1f}")

    elif f == "concentric":
        # octopus-inspired: concentric rings + radial bleed channels -> isotropic
        # edges, plus a shallow central cavity (micro-suction, speculative).
        lam = float(p.get("pitch", 1.6)); w = float(p.get("land", 0.7))
        h = float(p.get("depth", 0.6)); cav = float(p.get("cavity", 0.3))
        w = min(w, lam - 0.2); gw = lam - w
        g.update(phi=w / lam, w=w, g=gw, lam=lam, h=h, w_feat=w,
                 aspect=h / max(w, 1e-3), min_feat=min(w, gw),
                 drain_path=w / 2.0, chan_cap=gw * h, n_drain=4,
                 edge_dens=3.0 / lam, land_char=w,
                 M_primary=0.95, M_worst=0.80,
                 suction=min(0.6, cav),                      # flagged speculative
                 label=f"concentric p{lam:.1f}/w{w:.1f}/cav{cav:.1f}")

    elif f == "dimple":
        # holes in an otherwise smooth land: high phi (adhesion) + some suction, but
        # POOR open drainage (holes are closed pockets unless interconnected).
        lam = float(p.get("pitch", 2.0)); d = float(p.get("dia", 0.9))
        h = float(p.get("depth", 0.6))
        d = min(d, lam - 0.2)
        hole_frac = (math.pi / 4.0) * (d / lam) ** 2
        phi = 1.0 - hole_frac
        g.update(phi=phi, w=lam - d, g=d, lam=lam, h=h, w_feat=lam - d,
                 aspect=h / max(lam - d, 1e-3), min_feat=min(d, lam - d),
                 drain_path=(lam - d),                       # long: must reach a hole
                 chan_cap=0.25 * hole_frac * lam * h,        # closed pockets: weak
                 n_drain=0,                                  # not an open network
                 edge_dens=math.pi * d / (lam * lam), land_char=lam,
                 M_primary=0.72, M_worst=0.62,
                 suction=min(0.7, 0.5 + 0.5 * hole_frac),
                 label=f"dimple p{lam:.1f}/d{d:.1f}/h{h:.1f}")

    elif f == "hierarchical":
        # coarse drainage channels (macro) + fine micro-texture on the pad tops.
        # Drainage from the macro channels; edges + edge-efficiency from the micro.
        mlam = float(p.get("macro_pitch", 4.0)); mgap = float(p.get("macro_channel", 0.8))
        mh = float(p.get("macro_depth", 1.0))
        flam = float(p.get("micro_pitch", 0.8)); fw = float(p.get("micro_land", 0.45))
        fh = float(p.get("micro_depth", 0.25))
        pad = mlam - mgap
        phi_pad = pad / mlam
        phi_micro = fw / flam
        phi = phi_pad * phi_micro
        g.update(phi=phi, w=fw, g=mgap, lam=mlam, h=mh, w_feat=fw,
                 aspect=mh / max(pad, 1e-3),                 # macro pad stability
                 min_feat=min(fw, flam - fw, mgap, fh),
                 drain_path=fw / 2.0,                        # micro lands drain locally
                 chan_cap=mgap * mh, n_drain=3,
                 edge_dens=2.0 / flam + 2.0 / mlam, land_char=fw,
                 M_primary=0.97, M_worst=0.80,
                 label=f"hier M{mlam:.0f}/{mgap:.1f} m{flam:.1f}/{fw:.2f}")

    else:
        raise ValueError(f"unknown family {family!r}")

    g["lam"] = g.get("lam", g["w"] + g["g"])
    return g


FAMILIES = ["smooth", "ridge", "crosshatch", "chevron", "hexpad",
            "concentric", "dimple", "hierarchical"]

# default param sets (mid of each family's printable range) for quick reference
DEFAULTS = {
    "smooth": {},
    "ridge": dict(pitch=2.0, land=0.9, depth=0.6),
    "crosshatch": dict(pitch=2.0, land=0.9, depth=0.6),
    "chevron": dict(pitch=2.0, land=0.9, depth=0.6, angle=45),
    "hexpad": dict(cell=1.2, channel=0.5, depth=0.5),
    "concentric": dict(pitch=1.6, land=0.7, depth=0.6, cavity=0.3),
    "dimple": dict(pitch=2.0, dia=0.9, depth=0.6),
    "hierarchical": dict(macro_pitch=4.0, macro_channel=0.8, macro_depth=1.0,
                         micro_pitch=0.8, micro_land=0.45, micro_depth=0.25),
}


if __name__ == "__main__":
    for fam in FAMILIES:
        d = resolve(fam, DEFAULTS[fam])
        print(f"{fam:13s} phi={d['phi']:.2f} w={d['w']:.2f} g={d['g']:.2f} "
              f"h={d['h']:.2f} AR={d['aspect']:.2f} edge={d['edge_dens']:.2f} "
              f"Mp={d['M_primary']:.2f} Mw={d['M_worst']:.2f} | {d['label']}")

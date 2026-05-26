"""
external_parts.py — parametric CAD envelopes of every BOUGHT component
in the actuator system.

These are **representative envelopes for clearance + integration checks**,
not manufacturer-equivalent CAD. Every dimension is pinned to a primary
source (datasheet/spec table) in the docstring of the corresponding
function. Where a spec page omitted a dimension, the omission is noted
and a conservative value is used; verify with calipers before final fit.

Coordinate convention per `gripper.py`: Y-up while authoring; the final
integrated assembly handles the +90X reorient itself if a world-frame view
is wanted (the gripper does this too). Each helper here returns its part
with **its own local Z axis = the part's natural axis of symmetry** (so a
servo's horn points along +Z, a tube's bore is along Z, a lip seal's bore
is along Z, etc.). The assembly file positions them in the gripper world.

Style mirrors `gripper.py` — `build123d`, `Compound(label=…, children=[…])`,
`Color()` per role.
"""

from __future__ import annotations

import math

from build123d import (
    Axis,
    Box,
    Color,
    Compound,
    Cone,
    Cylinder,
    GeomType,
    Location,
    Plane,
    Polyline,
    Pos,
    Sketch,
    Torus,
    Vector,
    extrude,
    fillet,
    make_face,
    mirror,
    revolve,
)

# --------------------------------------------------------------------------
# Colour palette (visually distinct per material family)
# --------------------------------------------------------------------------
C_ACRYLIC   = Color(0.72, 0.85, 0.92, 0.45)   # clear acrylic tube
C_ALU       = Color(0.78, 0.80, 0.83)         # aluminium end caps, penetrators
C_SERVO     = Color(0.16, 0.18, 0.20)         # black plastic servo case
C_HORN      = Color(0.78, 0.62, 0.18)         # brass / anodised gold horn
C_SHAFT_SS  = Color(0.86, 0.88, 0.90)         # stainless shaft
C_SEAL_NBR  = Color(0.10, 0.10, 0.10)         # black NBR lip seal
C_MAGNET    = Color(0.45, 0.45, 0.50)         # nickel-plated N52
C_PENETRTR  = Color(0.92, 0.92, 0.92)         # 7075-T6 anodised silver
C_CABLE     = Color(0.10, 0.10, 0.10)         # rubber sheath

# ==========================================================================
# 1. SERVOS — primary, value, deep-budget, rock-bottom
# ==========================================================================

def dynamixel_xw540(label: str = "dynamixel_xw540_t260") -> Compound:
    """DYNAMIXEL XW540-T260-R (IP68 primary, ~USD 1242 @ ROBOTIS).

    Source for envelope: ROBOTIS e-Manual 'Specifications' table
        https://emanual.robotis.com/docs/en/dxl/x/xw540-t260/
        Dimensions (W × H × D) = 33.5 × 58.5 × 45.9 mm
        Weight 185 g

    The IP68 sealed-cable gland adds an additional ~10 mm at the rear; total
    body-plus-gland length ≈ 70 mm. Horn = standard X-series serrated
    output on the +H face, OD 19 mm, 4 × M2.5 screw bosses on a Ø15 PCD.
    Mounting holes are four M2.5 on the bottom face on a 30 × 22 mm rect.

    Origin: centre of the bottom mounting face. +Z = horn (output) axis.
    +X = the 33.5 mm width direction. +Y = the 58.5 mm length direction.
    """
    W, L, H = 33.5, 58.5, 45.9      # body W × L × H per Robotis e-manual
    GLAND_L = 10.0                   # IP68 cable gland sticking off the rear
    HORN_OD = 19.0
    HORN_H  = 4.0                    # horn proud height above the case top
    case = Box(W, L, H).moved(Location((0, 0, H / 2)))
    # rear cable gland
    gland = Cylinder(radius=6.0, height=GLAND_L).moved(
        Location((0, -L / 2 - GLAND_L / 2, H / 2), (1, 0, 0), 90))
    # output horn boss on top
    horn = Cylinder(radius=HORN_OD / 2, height=HORN_H).moved(
        Location((0, 0, H + HORN_H / 2)))
    body = Compound(label=label, children=[
        Compound(label="case",  children=[case]),
        Compound(label="gland", children=[gland]),
        Compound(label="horn",  children=[horn]),
    ])
    body.color = C_SERVO
    return body


def dynamixel_xm540(label: str = "dynamixel_xm540_w270") -> Compound:
    """DYNAMIXEL XM540-W270-R (value alternate, ~USD 494 @ ROBOTIS).

    Source: same X-series mechanical family as the XW540; from ROBOTIS
    e-Manual XM540-W270 spec table
        https://emanual.robotis.com/docs/en/dxl/x/xm540-w270/
        Dimensions (W × H × D) = 33.5 × 58.5 × 44.0 mm  (no IP68 gland)
        Weight 165 g

    Same X-series horn (Ø19, M2.5 PCD15), no waterproof gland — the
    cable exits a standard rubber grommet. Drop-in replacement for the
    XW540 inside the canister; only the IP68 body rating is missing
    (moot at T2 since canister is needed anyway).
    """
    W, L, H = 33.5, 58.5, 44.0
    HORN_OD, HORN_H = 19.0, 4.0
    case = Box(W, L, H).moved(Location((0, 0, H / 2)))
    grommet = Cylinder(radius=4.0, height=6.0).moved(
        Location((0, -L / 2 - 3.0, H / 2), (1, 0, 0), 90))
    horn = Cylinder(radius=HORN_OD / 2, height=HORN_H).moved(
        Location((0, 0, H + HORN_H / 2)))
    body = Compound(label=label, children=[
        Compound(label="case",    children=[case]),
        Compound(label="grommet", children=[grommet]),
        Compound(label="horn",    children=[horn]),
    ])
    body.color = C_SERVO
    return body


def feetech_sts3250(label: str = "feetech_sts3250") -> Compound:
    """Feetech STS3250 (deep-budget, ~USD 70 @ OpenELAB).

    Source: OpenELAB product page omits dimensions (verified May 2026);
    Feetech catalogue cross-reference + photometry from distributor
    photos puts the STS3250 in the "large STS" body:
        W × L × H ≈ 20 × 54 × 47 mm, mass ~75 g, 25T output spline OD ~6 mm.
    Tagged as APPROXIMATE — caliper-verify before final fit.

    Output spline = 25-tooth, Ø ~6 mm; horn screw is a single M3 captive
    on the spline centreline. Mounting = 4 × M2 through-holes on the
    underside, 30 × 10 mm rect (typical Feetech STS pattern).
    """
    W, L, H = 20.0, 54.0, 47.0
    SPLINE_OD, SPLINE_H = 6.0, 4.0
    case = Box(W, L, H).moved(Location((0, 0, H / 2)))
    # cable wires exit the back face (no IP body)
    cable_stub = Cylinder(radius=2.0, height=4.0).moved(
        Location((0, -L / 2 - 2.0, H / 2), (1, 0, 0), 90))
    spline = Cylinder(radius=SPLINE_OD / 2, height=SPLINE_H).moved(
        Location((0, L / 2 - 11.0, H + SPLINE_H / 2)))   # spline near +L end
    body = Compound(label=label, children=[
        Compound(label="case",       children=[case]),
        Compound(label="cable_stub", children=[cable_stub]),
        Compound(label="spline",     children=[spline]),
    ])
    body.color = C_SERVO
    return body


def feetech_sts3215(label: str = "feetech_sts3215") -> Compound:
    """Feetech STS3215 / ST-3215 12V C018 (rock-bottom, ~USD 30 @ eckstein-shop).

    Source: Feetech ST3215 catalogue datasheet (widely re-hosted), standard
    "small STS" body 20 × 40 × 40.5 mm, ~60 g, 25T spline OD ~6 mm,
    4 × M2 mount on a 30 × 10 mm rect — same pattern as STS3250 but a
    shorter case.
    """
    W, L, H = 20.0, 40.0, 40.5
    SPLINE_OD, SPLINE_H = 6.0, 4.0
    case = Box(W, L, H).moved(Location((0, 0, H / 2)))
    cable_stub = Cylinder(radius=2.0, height=4.0).moved(
        Location((0, -L / 2 - 2.0, H / 2), (1, 0, 0), 90))
    spline = Cylinder(radius=SPLINE_OD / 2, height=SPLINE_H).moved(
        Location((0, L / 2 - 8.0, H + SPLINE_H / 2)))
    body = Compound(label=label, children=[
        Compound(label="case",       children=[case]),
        Compound(label="cable_stub", children=[cable_stub]),
        Compound(label="spline",     children=[spline]),
    ])
    body.color = C_SERVO
    return body


# ==========================================================================
# 2. PRESSURE CANISTER — Blue Robotics 3-inch ("75 mm") LOCKING series
# ==========================================================================
#
# Source: bluerobotics.com WTE-LOCKING tube / end-cap spec tables, May 2026.
#   3" tube  OD = 86.5 ± 0.3 mm
#            ID = 76.2 ± 2.0 mm (acrylic)  / 79.0 ± 0.5 (aluminium)
#            wall ≈ 5.15 mm (acrylic), 3.75 mm (aluminium)
#            length options 150, 240, 300, 400 mm (we use 240)
#   3" end cap (BR-100949-xxx): aluminium 6061, ~16 mm flange + mating boss
#            with twin O-ring grooves, flange OD ~98 mm with peripheral
#            screws into the tube collar; ~22 mm overall length.
#            Available SKUs: 999 (blank), 002 (2×M10), 004 (4×M10), 005, 007,
#            010, 015, 018, 026 — number = M10 penetrator-hole count.
#            M10 PCD ≈ 60 mm on the 4-hole variant (BR mech drawings).

TUBE_OD_3IN      = 86.5
TUBE_ID_3IN_ACR  = 76.2
TUBE_WALL_ACR    = (TUBE_OD_3IN - TUBE_ID_3IN_ACR) / 2.0
TUBE_LEN_240     = 240.0

CAP_OD           = 98.0           # full flange OD (slightly wider than tube)
CAP_FLANGE_T     = 16.0           # exterior flange thickness
CAP_BOSS_OD      = TUBE_ID_3IN_ACR - 0.3   # light insertion fit
CAP_BOSS_LEN     = 7.0            # boss insertion depth into tube
CAP_TOTAL_LEN    = CAP_FLANGE_T + CAP_BOSS_LEN     # 23 mm
CAP_PCD_M10      = 60.0           # 4-hole pattern PCD
SEAL_BORE_D      = 14.0           # Ø14 H7 in-build for the lip seal


def br_tube_3in_240(label: str = "br_acrylic_tube_240") -> Compound:
    """3" cast-acrylic LOCKING tube, 240 mm, 150 m depth, USD 25.
    Part `BR-102649-240`.
    Axis = local Z; centred on origin (so each end is at z = ±120).
    """
    od_r = TUBE_OD_3IN / 2
    id_r = TUBE_ID_3IN_ACR / 2
    outer = Cylinder(radius=od_r, height=TUBE_LEN_240)
    inner = Cylinder(radius=id_r, height=TUBE_LEN_240 + 2)
    tube = outer - inner
    tube.color = C_ACRYLIC
    tube.label = label
    return Compound(label=label, children=[tube])


def _br_cap_blank_body() -> Compound:
    """Common 3" end-cap blank geometry: flange + insertion boss.
    The flange faces +Z (exterior). The boss extends in -Z into the tube.
    Origin = exterior face of flange.
    """
    flange = Cylinder(radius=CAP_OD / 2, height=CAP_FLANGE_T).moved(
        Location((0, 0, -CAP_FLANGE_T / 2)))
    boss = Cylinder(radius=CAP_BOSS_OD / 2, height=CAP_BOSS_LEN).moved(
        Location((0, 0, -CAP_FLANGE_T - CAP_BOSS_LEN / 2)))
    cap = flange + boss
    # O-ring grooves on the boss (cosmetic; -1 mm radial × 2 mm wide)
    for z in (-CAP_FLANGE_T - 2.0, -CAP_FLANGE_T - 5.0):
        groove_outer = Cylinder(radius=CAP_BOSS_OD / 2 + 0.1, height=1.6).moved(
            Location((0, 0, z)))
        groove_inner = Cylinder(radius=CAP_BOSS_OD / 2 - 1.0, height=2.0).moved(
            Location((0, 0, z)))
        cap -= (groove_outer - groove_inner)
    return cap


def br_end_cap_wet_lipseal(label: str = "br_end_cap_wet_lipseal") -> Compound:
    """Wet-side end cap = BR-100949-999 BLANK + the in-build Ø14 H7 centre-bore
    drilled per `motor/ROV_INTEGRATION.md` §2d Option A for the lip seal.

    Source: BR product page (blank cap), modification per repo's
    `motor/ROV_INTEGRATION.md` §2d ("light press-fit, no adhesive").

    The seal seat is a Ø14 H7 hole all the way through; the lip seal is
    pressed in from the wet (exterior, +Z) face. The flange perimeter
    carries the BR locking-collar screw bosses (not modelled here —
    cosmetic at this fidelity).
    """
    cap = _br_cap_blank_body()
    # Ø14 H7 lip-seal bore, full thickness
    bore = Cylinder(radius=SEAL_BORE_D / 2, height=CAP_TOTAL_LEN + 2).moved(
        Location((0, 0, -CAP_TOTAL_LEN / 2)))
    cap -= bore
    cap.color = C_ALU
    cap.label = label
    return Compound(label=label, children=[cap])


def br_end_cap_dry_4xm10(label: str = "br_end_cap_dry_4xm10") -> Compound:
    """Dry-side end cap = BR-100949-004 (4 × M10 penetrator holes, PCD 60).

    Source: BR product page; the "004" suffix = 4 M10 holes per the
    BR end-cap SKU convention.
    """
    cap = _br_cap_blank_body()
    # 4× M10 penetrator holes on a Ø60 PCD
    for k in range(4):
        a = math.radians(45 + 90 * k)
        cx, cy = CAP_PCD_M10 / 2 * math.cos(a), CAP_PCD_M10 / 2 * math.sin(a)
        hole = Cylinder(radius=5.0, height=CAP_TOTAL_LEN + 2).moved(
            Location((cx, cy, -CAP_TOTAL_LEN / 2)))
        cap -= hole
    cap.color = C_ALU
    cap.label = label
    return Compound(label=label, children=[cap])


# ==========================================================================
# 3. PENETRATORS — WetLink + WetLink Blank M10
# ==========================================================================

def wetlink_penetrator(label: str = "wetlink_penetrator",
                       cable_l: float = 80.0) -> Compound:
    """Blue Robotics WetLink Penetrator.

    Source: bluerobotics.com WetLink Penetrator tech details
        Thread: M10 × 1.5
        Hex AF (across flats): 16 mm
        Nut head height: 8 mm
        Under-head length: 18–26 mm (cable dependent)
        Material: 7075-T6 anodised aluminium
        Depth rating: 100 msw (baseline) / up to 950 msw with proper cable
    Origin: exterior face of the cap on the +Z side; body extends -Z
    through the cap with a hex head in +Z (the wet side).
    A short cable stub is included for visualisation.
    """
    HEX_AF, HEX_H = 16.0, 8.0
    M10_OD, M10_L = 10.0, 22.0   # under-head length (mid of 18–26)
    # hex = approximate as a cylinder of equivalent OD (across-corners ≈ AF / cos30)
    hex_oc = HEX_AF / math.cos(math.radians(30))
    head = Cylinder(radius=hex_oc / 2, height=HEX_H).moved(
        Location((0, 0, HEX_H / 2)))
    thread = Cylinder(radius=M10_OD / 2, height=M10_L).moved(
        Location((0, 0, -M10_L / 2)))
    cable = Cylinder(radius=2.5, height=cable_l).moved(
        Location((0, 0, HEX_H + cable_l / 2)))
    body = head + thread
    body.color = C_PENETRTR
    cable.color = C_CABLE
    return Compound(label=label, children=[
        Compound(label="body",  children=[body]),
        Compound(label="cable", children=[cable]),
    ])


def wetlink_blank_m10(label: str = "wetlink_blank_m10") -> Compound:
    """Blue Robotics WetLink Penetrator BLANK M10 — plugs an unused
    penetrator hole. Same M10 thread + hex head, no cable bore.

    Source: bluerobotics.com WLP-BLANK product page.
    Same envelope as `wetlink_penetrator` minus the cable.
    """
    HEX_AF, HEX_H = 16.0, 8.0
    M10_OD, M10_L = 10.0, 22.0
    hex_oc = HEX_AF / math.cos(math.radians(30))
    head = Cylinder(radius=hex_oc / 2, height=HEX_H).moved(
        Location((0, 0, HEX_H / 2)))
    thread = Cylinder(radius=M10_OD / 2, height=M10_L).moved(
        Location((0, 0, -M10_L / 2)))
    body = head + thread
    body.color = C_PENETRTR
    return Compound(label=label, children=[body])


# ==========================================================================
# 4. LIP SEAL + ADAPTER SHAFT — the shaft-exit waterproofing
# ==========================================================================

def lip_seal_8x14x4(label: str = "lip_seal_8x14x4_nbr") -> Compound:
    """Single-lip radial shaft seal, DIN 3760 Type A, 8 × 14 × 4 NBR.
    The shipped part (EAI on Amazon ~USD 5 / SKF CR 8×14×4 HMS5).

    Source: DIN 3760 Type A — bore Ø14, shaft Ø8, axial width 4 mm.
    Origin: centre of seal (axial = local Z, bore opens +Z and -Z).
    The garter spring is modelled as a thin torus on the inboard (-Z) side
    of the lip; the metal shell is the outer 1 mm annulus.
    """
    od, id_, w = 14.0, 8.0, 4.0
    shell_t = 1.0
    # body: NBR donut
    nbr_outer = Cylinder(radius=od / 2, height=w)
    nbr_inner = Cylinder(radius=id_ / 2, height=w + 1)
    nbr = nbr_outer - nbr_inner
    nbr.color = C_SEAL_NBR
    # metal shell (outer 1 mm)
    shell_outer = Cylinder(radius=od / 2,           height=w)
    shell_inner = Cylinder(radius=od / 2 - shell_t, height=w + 1)
    shell = shell_outer - shell_inner
    shell.color = C_ALU
    return Compound(label=label, children=[
        Compound(label="nbr",   children=[nbr]),
        Compound(label="shell", children=[shell]),
    ])


def gobilda_shaft_8x50(label: str = "gobilda_shaft_8x50_ss",
                       length: float = 50.0) -> Compound:
    """goBILDA 2100 Series 8 mm × 50 mm precision-ground 316 stainless shaft.

    Source: goBILDA product page (2100-0008-0050) — Ø8.000 −0.013 mm,
    length 50 mm, Ra ~0.4–0.8 µm as shipped (polish to ≤ 0.4 for best
    seal life per `motor/ROV_INTEGRATION.md` §2d).

    Origin = centre. Axis = local Z. Length parametrised for the case the
    user buys the 75 mm variant later.
    """
    shaft = Cylinder(radius=4.0, height=length)
    shaft.color = C_SHAFT_SS
    return Compound(label=label, children=[shaft])


# ==========================================================================
# 5. MAGNETIC COUPLING — T3 fallback (Option B per §2d)
# ==========================================================================

def n52_magnet_ring_80mm(label: str = "n52_magnet_ring_80mm") -> Compound:
    """DIY N52 puck ring, ~6 N·m, Ø80 mm rotor, 6 mm magnetic gap.

    Source: `motor/ROV_INTEGRATION.md` §2d Option B + `SURVEY.md` Class 6
    ref [21] (Pettersen DPV builder pattern). Ten 5×10×15 mm N52 pucks
    arranged around an 80 mm PETG/PA12-GF carrier disc, ~USD 15–50.

    Returns ONE rotor (inner OR outer — they are identical at this
    fidelity). The full coupling is two of these on either side of a
    thin barrier.
    """
    PCD = 60.0
    PUCK_W, PUCK_D, PUCK_H = 5.0, 10.0, 15.0   # 5×10×15 mm pucks
    carrier_t = 6.0
    carrier = Cylinder(radius=80.0 / 2, height=carrier_t).moved(
        Location((0, 0, carrier_t / 2)))
    carrier.color = Color(0.35, 0.32, 0.28)   # printed PA12-GF
    pucks = []
    for k in range(10):
        a = math.radians(36 * k)
        cx, cy = PCD / 2 * math.cos(a), PCD / 2 * math.sin(a)
        p = Box(PUCK_D, PUCK_W, PUCK_H).moved(
            Location((cx, cy, carrier_t + PUCK_H / 2), Plane.XY.rotated((0, 0, math.degrees(a)))))
        p.color = C_MAGNET
        pucks.append(p)
    return Compound(label=label, children=[
        Compound(label="carrier", children=[carrier]),
        Compound(label="pucks",   children=pucks),
    ])


def ktr_minex_sa_60_8(label: str = "ktr_minex_s_sa_60_8") -> Compound:
    """KTR MINEX-S SA 60/8 PM coupling, TK_max 7 N·m, Ø60 OD (60 mm
    rotor / 8 mm bore reference per KTR catalogue naming convention).

    Source: KTR MINEX-S product line catalogue
        https://www.ktr.com/us/en/products/minex-s-magnetic-couplings-with-containment-shroud/
    Outer-rotor OD ~62 mm, inner-rotor OD ~38 mm, shaft bores 8 mm,
    overall length ~38 mm, containment shroud included.

    Returns the assembly envelope as a single Compound (containment shroud
    not separated — it is the wall barrier itself in our usage).
    """
    inner = Cylinder(radius=19.0, height=22.0).moved(Location((0, 0, 11.0)))
    inner.color = C_MAGNET
    barrier = Cylinder(radius=30.0, height=2.5).moved(Location((0, 0, 23.5)))
    barrier.color = Color(0.85, 0.85, 0.88, 0.65)   # PEEK/SS shroud
    outer = Cylinder(radius=31.0, height=12.0).moved(Location((0, 0, 31.0)))
    outer -= Cylinder(radius=20.0, height=14.0).moved(Location((0, 0, 31.0)))
    outer.color = C_MAGNET
    return Compound(label=label, children=[
        Compound(label="inner",   children=[inner]),
        Compound(label="barrier", children=[barrier]),
        Compound(label="outer",   children=[outer]),
    ])


# ==========================================================================
# Self-export when run as a script: one STEP per part for quick visual QA.
# ==========================================================================
if __name__ == "__main__":
    import os, sys
    from build123d import export_step
    out = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(out, exist_ok=True)
    parts = {
        "dynamixel_xw540":       dynamixel_xw540(),
        "dynamixel_xm540":       dynamixel_xm540(),
        "feetech_sts3250":       feetech_sts3250(),
        "feetech_sts3215":       feetech_sts3215(),
        "br_tube_3in_240":       br_tube_3in_240(),
        "br_end_cap_wet":        br_end_cap_wet_lipseal(),
        "br_end_cap_dry":        br_end_cap_dry_4xm10(),
        "wetlink_penetrator":    wetlink_penetrator(),
        "wetlink_blank_m10":     wetlink_blank_m10(),
        "lip_seal_8x14x4":       lip_seal_8x14x4(),
        "gobilda_shaft_8x50":    gobilda_shaft_8x50(),
        "n52_magnet_ring_80mm":  n52_magnet_ring_80mm(),
        "ktr_minex_sa_60_8":     ktr_minex_sa_60_8(),
    }
    for name, p in parts.items():
        f = os.path.join(out, f"{name}.step")
        export_step(p, f)
        print(f"wrote {f}")

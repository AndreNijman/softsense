"""Tier-1 mechanistic grip-texture model (fast surrogate, ~microseconds/eval).

This is NOT a first-principles simulator. It is a composition of textbook
relations whose coefficients are literature-anchored where a source exists and
flagged otherwise. The model is a *hypothesis about what matters* for underwater
grip; its job is to RANK textures, not to predict an absolute holding force. Two
guards on that honesty live alongside it:
  * baseline_validate.py  -- must reproduce the published wet-grip ordering, else
    the model is wrong and the swarm is meaningless (gate before any search).
  * sensitivity.py        -- perturbs every coefficient +-50% and reports which
    winners are invariant. The deliverable is "X wins for any reasonable
    weighting", not "X wins at my exact numbers".

Physics terms (each tagged with its source in COEFFS):
  1. Soft-land flattening      phi_eff(p, E)        [CALIBRATE vs Tier-2 FEA]
  2. Elastomer friction        tau = tau0 + alpha p [Briscoe & Tabor 1978]
  3. Hysteresis/deformation    f(object roughness)  [Persson 2001]
  4. Wet squeeze-film drainage Reynolds + channel   [tire-tread / tree-frog lit]
  5. Partial-slip edge effic.  discrete-contact surrogate (monotone Hill in
                                land size) -- the DIRECTION is supported by tyre-
                                tread / tree-frog literature; the functional form
                                is engineering convenience. NOT Cattaneo-Mindlin
                                (which is (1-(T/muN)^(2/3)) for Hertzian spheres)
                                and NOT gecko adhesion (van-der-Waals on
                                hierarchical fibrils). [ESTIMATE]
  6. Directional coverage      M(slip direction)    [geometry]
  7. Durability                root bending stress  [beam theory; FEA-checked]
  8. Micro-suction             (dimple/sucker)      [SPECULATIVE, low weight]

Units: lengths mm; pressure/stress MPa; force N; viscosity SI internally.
"""
import math
import patterns as P

# --------------------------------------------------------------------------
# COEFFICIENTS  -- source tag in the comment. [cited] real source; [ESTIMATE]
# physically-bounded guess; [PLACEHOLDER] tuned to the baseline gate;
# [CALIBRATE] fitted against Tier-2 FEA; [SPECULATIVE] low-confidence effect.
# --------------------------------------------------------------------------
COEFFS = dict(
    # --- elastomer interfacial friction: tau = tau0 + alpha*p  (Briscoe&Tabor) ---
    TAU0=0.18,        # MPa interfacial shear strength, TPU-class [cited ~0.1-0.3]
    ALPHA=0.22,       # pressure coeff (load-controlled term)     [cited ~0.1-0.3]
    MU_FILM=0.08,     # wet smooth hydroplaning floor             [cited tire 0.05-0.15]
    MU_CAP=2.5,       # physical max effective friction           [cited clean rubber]
    MU_GOOD=0.60,     # reference "good grip" for normalising      [ESTIMATE]
    # --- as-printed eSUN eTPU-95A is SLICK: FDM TPU contact faces come out glossy
    #     with a low-friction skin (real grip << ideal/lab TPU). A flat printed
    #     land keeps only SKIN_SLICK of the ideal adhesion; edges & channel
    #     side-walls (rough layer lines, fresh-cut geometry) break that skin and
    #     restore grip -> texture is needed to overcome the slickness itself. ---
    SKIN_SLICK=0.45,  # adhesion fraction kept by a FLAT printed TPU face [ESTIMATE]
    EDGE_DEGLAZE=2.0, # edge density (1/mm) that fully deglazes the skin   [PLACEHOLDER]
    # --- wet drainage (Reynolds squeeze film + channel capacity) ---
    ETA_WATER=1.0e-3, # Pa.s seawater ~20C                        [cited physical]
    T_GRASP=2.0,      # s available to squeeze the film           [ESTIMATE]
    H0_FILM=50e-6,    # m initial trapped film                    [ESTIMATE]
    CAP0=0.5,         # channel-capacity reference (dimensionless) [PLACEHOLDER]
    EDGE_PIERCE=0.10, # film-piercing gain per (1/mm * MPa)        [PLACEHOLDER]
    # --- partial-slip edge efficiency (discrete-contact benefit) ---
    LAND_CRIT=2.0,    # mm; land smaller than this -> efficiency~1 [ESTIMATE]
    ETA_FLOOR=0.45,   # efficiency of one big monolithic pad       [ESTIMATE]
    # --- hysteresis / deformation friction (Persson) ---
    C_HYS=0.25,       # hysteresis gain                            [ESTIMATE]
    C_EDGE=0.6,       # edge contribution to hysteresis per 1/mm   [PLACEHOLDER]
    # --- soft-land flattening (Tier-2 FEA calibrates C_FLAT) ---
    C_FLAT=0.8,       # phi grows with p_real/E'                   [CALIBRATE vs FEA]
    E_TPU=40.0,       # MPa eSUN eTPU-95A estimate (finger study)  [project]
    NU=0.42, STRENGTH=25.0,  # MPa printed strength (finger study) [project]
    # --- micro-suction (speculative, dimple/sucker only) ---
    SUCT_GAIN=0.25,   # mu boost from suction (wet smooth only)    [SPECULATIVE]
    # --- score weights ---
    W_PRIMARY=0.60,   # primary pull-out axis vs worst direction   [design choice]
    W_HOLD=0.72, W_SAFE=0.16, W_DAMAGE=0.35,  #                     [design choice]
    INCON_PEN=0.80,   # grip-inconsistency (CoV) penalty across conditions [design choice]
    # --- printability (Bambu P1S 0.4 nozzle / 0.16 layer) ---
    MIN_PRINT=0.42, ASPECT_MAX=3.0, ASPECT_HARD=5.0,  #            [DFM]
)

# --------------------------------------------------------------------------
# CONDITION BATTERY  -- objects/surfaces the gripper must hold underwater.
# Span demanded by the design brief (must work on ALL object surfaces, not one):
# smooth-wet (hydroplaning), rough-wet (asperity interlock), ridged/corrugated
# (macro relief -- the gripper texture must mesh, not bridge), slimy/biofouled
# (boundary film kills adhesion), soft compliant (must not damage), small-curved
# (conformance + high pressure), and one dry-clean case (where adhesion/smooth
# is meant to win -- proves texture has a real cost, for honesty).
# Ra in metres; p_nom in MPa (0.03-0.15 band from the finger's 8-44mm x 10mm
# contact patches at the 12 N grip target).
# --------------------------------------------------------------------------
CONDITIONS = [
    dict(name="smooth_wet",  label="smooth hard, wet (acrylic)", wet=True,
         Ra=0.2e-6, slime=0.00, soft=False, dmg=9.9, p_nom=0.10, weight=1.0),
    dict(name="rough_wet",   label="rough hard, wet (rock)",     wet=True,
         Ra=30e-6,  slime=0.10, soft=False, dmg=9.9, p_nom=0.10, weight=0.8),
    dict(name="ridged_wet",  label="ridged/corrugated, wet",     wet=True,
         Ra=80e-6,  slime=0.10, soft=False, dmg=9.9, p_nom=0.10, weight=0.8),
    dict(name="slimy",       label="biofouled / slimy",          wet=True,
         Ra=5e-6,   slime=0.85, soft=False, dmg=9.9, p_nom=0.10, weight=1.0),
    dict(name="soft_wet",    label="soft compliant, wet (kelp)", wet=True,
         Ra=5e-6,   slime=0.30, soft=True,  dmg=0.05, p_nom=0.08, weight=0.7),
    dict(name="small_curved",label="small cylinder, wet",        wet=True,
         Ra=1e-6,   slime=0.05, soft=False, dmg=9.9, p_nom=0.15, weight=0.9),
    dict(name="dry_smooth",  label="smooth hard, dry-clean",     wet=False,
         Ra=0.5e-6, slime=0.00, soft=False, dmg=9.9, p_nom=0.10, weight=0.3),
]


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def phi_eff(geom, p_nom, C):
    """Load-flattened land fraction. Soft lands spread under pressure, raising
    real contact area toward 1. C_FLAT is calibrated against Tier-2 FEA."""
    phi0 = geom["phi"]
    if phi0 >= 0.999:
        return 1.0
    Eprime = C["E_TPU"] / (1.0 - C["NU"] ** 2)          # plane-strain-ish modulus
    p_real0 = p_nom / phi0
    flat = C["C_FLAT"] * (p_real0 / Eprime)             # fractional widening
    return _clamp(phi0 * (1.0 + flat), phi0, 1.0)


def psi_dewet(geom, cond, p_real, C):
    """Dewetted fraction (0..1): how much of the land achieves solid/boundary
    contact rather than riding a water film. Reynolds squeeze-film over the
    drain path, gated by channel capacity, boosted by edge film-piercing."""
    if not cond["wet"]:
        return 1.0
    if geom["n_drain"] <= 0:
        # no OPEN channel network (smooth land, or closed dimple pockets): the
        # film cannot escape laterally -> it persists and the pad hydroplanes.
        # Closed pockets give only a small benefit (trap a little displaced water).
        base = 0.05 + 0.10 * min(geom["chan_cap"], 1.0)
    else:
        a = geom["drain_path"] * 1e-3                    # mm -> m
        p_pa = max(p_real, 1e-3) * 1e6                   # MPa -> Pa
        h_t = max(cond["Ra"], 0.3e-6)                    # boundary gap ~ roughness
        # squeeze time to thin the film to boundary contact (parallel-plate Reynolds)
        t_drain = 3.0 * C["ETA_WATER"] * a * a / (2.0 * p_pa * h_t * h_t)
        psi_time = 1.0 / (1.0 + t_drain / C["T_GRASP"])
        # channel must hold the squeezed water: vol/land ~ w*H0 ; channel ~ g*h
        cap_ratio = geom["chan_cap"] / max(geom["w"] * C["H0_FILM"] * 1e3, 1e-6)
        gate = _clamp(cap_ratio / C["CAP0"], 0.0, 1.0)
        base = psi_time * gate
    # sharp/dense edges pierce the boundary film locally
    pierce = _clamp(C["EDGE_PIERCE"] * geom["edge_dens"] * p_real * 30.0, 0.0, 0.6)
    return _clamp(base + pierce * (1.0 - base), 0.0, 1.0)


def eta_edge(geom, C):
    """Partial-slip edge efficiency surrogate [ESTIMATE]. One big compliant pad
    peels from its edge (low efficiency); subdividing into many small lands resets
    the edge stress at each land (efficiency -> 1). The DIRECTION of this effect
    is supported by tyre-tread + tree-frog wet-grip literature; the FUNCTIONAL
    FORM here is a monotone Hill curve chosen for convenience, NOT Cattaneo-Mindlin
    (Hertzian sphere) and NOT gecko adhesion (vdW on hierarchical fibrils)."""
    lc = geom["land_char"]
    return C["ETA_FLOOR"] + (1.0 - C["ETA_FLOOR"]) * C["LAND_CRIT"] / (C["LAND_CRIT"] + lc)


def grip_in_condition(geom, cond, C):
    """Full evaluation of one texture against one object condition."""
    p_nom = cond["p_nom"]
    phi_e = phi_eff(geom, p_nom, C)
    p_real = p_nom / max(phi_e, 1e-3)                    # MPa on the lands
    psi = psi_dewet(geom, cond, p_real, C)

    # as-printed TPU skin is slick; edges/side-walls deglaze it back toward ideal
    deglaze = _clamp(geom["edge_dens"] / C["EDGE_DEGLAZE"], 0.0, 1.0)
    skin = C["SKIN_SLICK"] + (1.0 - C["SKIN_SLICK"]) * deglaze

    # friction available WHERE there is solid contact
    mu_adh = (C["TAU0"] * phi_e / p_nom) * (1.0 - cond["slime"]) * skin  # adhesion (real area)
    mu_load = C["ALPHA"]                                 # load-controlled term
    rough_n = _clamp(cond["Ra"] / 10e-6, 0.0, 4.0)       # normalised roughness
    mu_hys = C["C_HYS"] * rough_n * (1.0 + C["C_EDGE"] * geom["edge_dens"])
    mu_solid = mu_adh + mu_load + mu_hys

    mu_eff = psi * mu_solid + (1.0 - psi) * C["MU_FILM"]
    # micro-suction bonus: only wet + smooth object (needs a sealing surface)
    if geom["suction"] > 0 and cond["wet"] and cond["Ra"] < 2e-6:
        mu_eff += geom["suction"] * C["SUCT_GAIN"]
    mu_eff = _clamp(mu_eff, 0.0, C["MU_CAP"])

    # directional: blend primary pull-out axis with worst direction
    mu_dir = C["W_PRIMARY"] * mu_eff * geom["M_primary"] + \
             (1.0 - C["W_PRIMARY"]) * mu_eff * geom["M_worst"]
    eta = eta_edge(geom, C)
    mu_hold = mu_dir * eta                               # effective holding mu

    # --- sub-scores ---
    hold = _clamp(mu_hold / C["MU_GOOD"], 0.0, 1.15)     # plateau at "good grip"
    tau_shear = mu_dir * p_real                          # MPa shear on land root
    sigma_root = 6.0 * tau_shear * geom["aspect"]        # cantilever root bending
    margin = C["STRENGTH"] / max(sigma_root, 1e-6)
    safe = _clamp((margin - 1.5) / 3.0, 0.0, 1.0)
    damage = 0.0
    if cond["soft"]:
        damage = _clamp((p_real - cond["dmg"]) / cond["dmg"], 0.0, 1.0)

    obj = C["W_HOLD"] * hold + C["W_SAFE"] * safe - C["W_DAMAGE"] * damage
    if margin < 1.2:                                     # durability hard fail
        obj *= 0.2
    return dict(cond=cond["name"], mu_eff=mu_eff, mu_hold=mu_hold, psi=psi,
                phi_eff=phi_e, p_real=p_real, eta=eta, margin=margin,
                hold=hold, safe=safe, damage=damage, obj=max(obj, 0.0))


def printable(geom, C):
    """Hard printability gate (Bambu P1S 0.4 nozzle / 0.16 layer)."""
    ok = geom["min_feat"] >= C["MIN_PRINT"] and geom["aspect"] <= C["ASPECT_HARD"]
    pen = 1.0
    if geom["aspect"] > C["ASPECT_MAX"]:
        pen = _clamp(1.0 - (geom["aspect"] - C["ASPECT_MAX"]) /
                     (C["ASPECT_HARD"] - C["ASPECT_MAX"]) * 0.5, 0.5, 1.0)
    return ok, pen


def score_texture(family, params, C=None, conditions=None):
    """Universal grip score across the condition battery. Returns full breakdown."""
    C = dict(COEFFS if C is None else C)
    conds = CONDITIONS if conditions is None else conditions
    geom = P.resolve(family, params)
    ok, pgate = printable(geom, C)
    rows = [grip_in_condition(geom, c, C) for c in conds]
    ws = [c["weight"] for c in conds]
    base = sum(r["obj"] * w for r, w in zip(rows, ws)) / sum(ws)
    # inconsistency is judged over the WET operating envelope only (the dry-clean
    # case is a deliberate contrast and would otherwise swamp the spread).
    wet_holds = [r["mu_hold"] for r, c in zip(rows, conds) if c["wet"]]
    holds = wet_holds if wet_holds else [r["mu_hold"] for r in rows]
    mean_h = sum(holds) / len(holds)
    var = sum((x - mean_h) ** 2 for x in holds) / len(holds)
    incon = (var ** 0.5) / mean_h if mean_h > 1e-6 else 0.0   # coeff. of variation
    score = base - C["INCON_PEN"] * _clamp(incon - 0.35, 0.0, 1.0)
    score *= pgate
    if not ok:
        score *= 0.15                                    # unprintable -> dead
    return dict(family=family, params=params, label=geom["label"],
                score=round(score, 4), base=round(base, 4),
                incon=round(incon, 3), printable=ok, pgate=round(pgate, 3),
                geom={k: geom[k] for k in ("phi", "w", "g", "h", "aspect",
                      "min_feat", "edge_dens", "M_primary", "M_worst",
                      "land_char", "drain_path", "chan_cap", "suction")},
                rows=rows)


if __name__ == "__main__":
    for fam in P.FAMILIES:
        r = score_texture(fam, P.DEFAULTS[fam])
        flag = "" if r["printable"] else "  [UNPRINTABLE]"
        print(f"{fam:13s} score={r['score']:.3f} base={r['base']:.3f} "
              f"incon={r['incon']:.2f}{flag}  | {r['label']}")

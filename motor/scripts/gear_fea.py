"""Phase-4 gear-tooth FEA: the max-safe input-shaft torque T_safe.

The drivetrain is current-FORCE-controlled (the sensing pivot), so grip force is
*commanded* and the motor never runs to mechanical stall in normal use. But a
firmware/limit FAULT could drive the chosen servo to its stall torque (XW540-T260
stall 9.5 N.m; STS3215 stall 2.94 N.m). This study answers: at what input-shaft
torque does the weakest printed tooth reach the PA12-GF root-bending allowable?
That number, T_safe, is the gear-protection CEILING the firmware current limit
must stay below (see SENSING.md / ELECTRICAL.md) and the margin SELECTION.md cites.

Method (headline = 2D FEA; Lewis = sanity check):
  The gears are REPRESENTATIVE straight-flank teeth (gripper.py:132-148), NOT 20deg
  involute, so the standard Lewis form factor Y is misleading -> a 2D plane-stress
  Q4 FEA of the actual trapezoidal tooth is the headline. We port the grip Tier-2
  machinery (grip/scripts/texture_fea.py). A worst-case TIP tangential load bends a
  cantilever tooth of root thickness s_root, height h, loaded face width b_eff
  (= min of the two mating face widths). Peak von-Mises is sampled in the root band
  (sharp shoulder -> conservative; a real fillet lowers it). Stress is linear in
  load, so we solve once at a reference force and scale to the allowable.

  Tooth tangential force vs input torque T_in:
    pinion mesh contact force  F_t = T_in / PINION_RP   (pinion AND crown see this)
    sector mesh force          F_s = T_in * i_g / R_GEAR (left gear carries both fingers)
  -> T_safe(gear) = F_allow * lever, where F_allow = sigma_allow/sigma_ref * F_ref.

Allowable: PA12-GF (drive arms + pinion shaft, per BOM). Polymaker Fiberon
PA6-GF25 tensile = 84.5 MPa (ISO 527); PA12-GF base is weaker than PA6, and FDM
100%-infill knocks bulk down ~30-40% (layer adhesion), so bulk ~50-65 MPa. With a
wet/creep/cyclic safety factor we use a conservative ROOT-BENDING ALLOWABLE of
30 MPa (cf. grip campaign STRENGTH=25 for eTPU-95A).
"""
import math
import os
import sys
import json
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import gripper as g  # noqa: E402

E_GF = 3500.0     # PA12-GF Young's modulus ~3.5 GPa (FDM est.); cancels (linear, stress-scaled)
NU = 0.40
SIGMA_ALLOW = 30.0  # MPa, PA12-GF FDM root-bending allowable (conservative, see header)
ITER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "iterations")


def plane_stress_D(E, nu):
    c = E / (1 - nu * nu)
    return c * np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1 - nu) / 2]])


def q4_ke(xy, D):
    ke = np.zeros((8, 8)); gp = 1 / np.sqrt(3)
    for xi in (-gp, gp):
        for et in (-gp, gp):
            dN = 0.25 * np.array([[-(1 - et), (1 - et), (1 + et), -(1 + et)],
                                  [-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)]])
            J = dN @ xy
            dNxy = np.linalg.solve(J, dN)
            B = np.zeros((3, 8))
            B[0, 0::2] = dNxy[0]; B[1, 1::2] = dNxy[1]
            B[2, 0::2] = dNxy[1]; B[2, 1::2] = dNxy[0]
            ke += B.T @ D @ B * abs(np.linalg.det(J))
    return ke


def assemble(nodes, elems, D):
    ndof = 2 * len(nodes); rows, cols, vals = [], [], []
    for el in elems:
        ke = q4_ke(nodes[el], D)
        dofs = np.array([[2 * n, 2 * n + 1] for n in el]).ravel()
        for a in range(8):
            for b in range(8):
                rows.append(dofs[a]); cols.append(dofs[b]); vals.append(ke[a, b])
    return sp.csr_matrix((vals, (rows, cols)), shape=(ndof, ndof))


def vm_nodes(nodes, elems, U, D):
    sig = np.zeros(len(nodes)); cnt = np.zeros(len(nodes))
    for el in elems:
        xy = nodes[el]
        dN = 0.25 * np.array([[-1, 1, 1, -1], [-1, -1, 1, 1]])
        J = dN @ xy; dNxy = np.linalg.solve(J, dN)
        B = np.zeros((3, 8))
        B[0, 0::2] = dNxy[0]; B[1, 1::2] = dNxy[1]
        B[2, 0::2] = dNxy[1]; B[2, 1::2] = dNxy[0]
        dofs = np.array([[2 * n, 2 * n + 1] for n in el]).ravel()
        sxx, syy, sxy = D @ (B @ U[dofs])
        vm = math.sqrt(sxx * sxx - sxx * syy + syy * syy + 3 * sxy * sxy)
        for n in el:
            sig[n] += vm; cnt[n] += 1
    cnt[cnt == 0] = 1
    return sig / cnt


def tooth_root_stress(s_root, h, b_eff, F_ref=1.0, ex=None):
    """Centered constant-width (=s_root, conservative) cantilever tooth on a base
    slab; tip tangential line load F_ref/b_eff. Returns peak root von-Mises [MPa]."""
    ex = ex or s_root / 12.0
    Wb = 3.0 * s_root
    hb = 1.2 * s_root
    nx = max(6, int(round(Wb / ex)))
    nyb = max(3, int(round(hb / ex)))
    nyp = max(6, int(round(h / ex)))
    xs = np.linspace(0, Wb, nx + 1)
    yb = np.linspace(0, hb, nyb + 1)
    yp = np.linspace(hb, hb + h, nyp + 1)[1:]
    ys = np.concatenate([yb, yp])
    nodes = np.array([(x, y) for y in ys for x in xs]); ncols = nx + 1

    def nid(ix, iy): return iy * ncols + ix
    x0, x1 = Wb / 2 - s_root / 2, Wb / 2 + s_root / 2
    post_col = np.array([x0 - 1e-9 <= 0.5 * (xs[i] + xs[i + 1]) <= x1 + 1e-9 for i in range(nx)])
    nrows_b = len(yb)
    elems = []
    for iy in range(len(ys) - 1):
        for ix in range(nx):
            if iy >= nrows_b - 1 and not post_col[ix]:
                continue
            elems.append([nid(ix, iy), nid(ix + 1, iy), nid(ix + 1, iy + 1), nid(ix, iy + 1)])
    elems = np.array(elems)
    D = plane_stress_D(E_GF, NU)
    K = assemble(nodes, elems, D)
    ndof = 2 * len(nodes)
    ref = np.unique(elems.ravel())
    orph = np.setdiff1d(np.arange(len(nodes)), ref)
    base = np.where(nodes[:, 1] < 1e-6)[0]
    fixed = np.concatenate([2 * base, 2 * base + 1, 2 * orph, 2 * orph + 1]).astype(int)
    top_y = hb + h
    tip = np.where((np.abs(nodes[:, 1] - top_y) < 1e-6) &
                   (nodes[:, 0] >= x0 - 1e-9) & (nodes[:, 0] <= x1 + 1e-9))[0]
    F = np.zeros(ndof)
    line = F_ref / b_eff                       # N/mm (plane-stress per-thickness load)
    for n in tip:
        F[2 * n] += line / len(tip)            # tangential +x -> bending
    free = np.setdiff1d(np.arange(ndof), fixed)
    U = np.zeros(ndof)
    U[free] = spla.spsolve(K[free][:, free], F[free])
    vm = vm_nodes(nodes, elems, U, D)
    root_band = (np.abs(nodes[:, 1] - hb) < 0.18 * h) & (nodes[:, 0] >= x0 - 1e-9) & (nodes[:, 0] <= x1 + 1e-9)
    return float(vm[root_band].max() if root_band.any() else vm.max())


def tooth_dims():
    """Tooth root thickness s_root, height h, and pitch radius for each gear,
    derived from gripper.py's straight-flank profile (frac +/-0.30 root span)."""
    # pinion (straight-flank, fracs -0.30..0.30 at root)
    p_step = 2 * math.pi / g.PINION_TEETH
    p_root_r = g.PINION_RP - 0.55 * g.PINION_TOOTH_H
    pin = dict(s_root=0.60 * p_step * p_root_r, h=g.PINION_TOOTH_H, R=g.PINION_RP)
    # sector gear
    s_step = 2 * math.pi / g.GEAR_TEETH
    s_root_r = g.R_GEAR - 0.55 * g.GEAR_TOOTH_H
    sec = dict(s_root=0.60 * s_step * s_root_r, h=g.GEAR_TOOTH_H, R=g.R_GEAR)
    # crown face tooth: bends about its base; thickness ~ half circular pitch at RC,
    # height = axial proud CROWN_FACE_H, loaded over the radial band 2*CROWN_TOOTH_H
    c_step = 2 * math.pi / g.CROWN_TEETH
    crown = dict(s_root=0.5 * c_step * g.CROWN_RC, h=g.CROWN_FACE_H, R=g.CROWN_RC)
    return pin, sec, crown


def face_widths():
    """Loaded face width b_eff per gear = min of the two mating faces."""
    pin_face = g.PINION_T
    crown_band = 2.0 * g.CROWN_TOOTH_H
    mesh_b = min(pin_face, crown_band)        # pinion<->crown contact patch
    sector_b = g.T_CRANK                       # sector<->sector (both on the crank layer)
    return dict(pinion=mesh_b, crown=mesh_b, sector=sector_b)


def run():
    pin, sec, crown = tooth_dims()
    fb = face_widths()
    i_g = g.CROWN_TEETH / g.PINION_TEETH
    F_REF = 10.0  # N reference tooth force
    out = {"sigma_allow": SIGMA_ALLOW, "i_g": i_g,
           "geometry": {"PINION_T": g.PINION_T, "CROWN_TOOTH_H": g.CROWN_TOOTH_H,
                        "T_CRANK": g.T_CRANK}, "gears": {}}
    res = {}
    for name, d, b, lever in (
            ("pinion", pin, fb["pinion"], g.PINION_RP),       # F_t = T_in/PINION_RP
            ("crown", crown, fb["crown"], g.PINION_RP),       # same contact force
            ("sector", sec, fb["sector"], g.R_GEAR / i_g)):   # F_s = T_in*i_g/R_GEAR -> lever=R_GEAR/i_g
        sref = tooth_root_stress(d["s_root"], d["h"], b, F_REF)
        F_allow = SIGMA_ALLOW / sref * F_REF                  # N tooth force at allowable
        T_safe = F_allow * lever / 1000.0                     # N.m input-shaft torque
        res[name] = T_safe
        out["gears"][name] = dict(
            s_root=round(d["s_root"], 3), h=round(d["h"], 3), b_eff=round(b, 3),
            sigma_ref_at_10N=round(sref, 4), F_tooth_allow_N=round(F_allow, 1),
            T_safe_input_Nm=round(T_safe, 3), lever_mm=round(lever, 3))
    out["T_safe_input_Nm"] = round(min(res.values()), 3)
    out["binding_gear"] = min(res, key=res.get)
    return out


def proposed_resize():
    """T_safe for the PROPOSED full module/radius re-size (engineered target, NOT
    implemented in gripper.py -- needs CAD-render clearance validation, see
    DRIVETRAIN.md / DECISION_LOG). CROWN_RC 8->11, module 0.67->1.83, teeth 24/9->12/6,
    i_g 2.667->2.0, pinion face 8. F_contact = T_left/CROWN_RC, so the bigger crown
    radius + bigger module is what buys the strength the housing envelope allows."""
    CRC, CT, PT, face = 11.0, 12, 6, 8.0
    m = 2 * CRC / CT                 # module 1.83
    PRP = m * PT / 2                 # pinion pitch radius 5.5
    i_g = CT / PT                    # 2.0
    step = 2 * math.pi / PT
    s_root = 0.60 * step * (PRP - 0.55 * m)
    b_eff = min(face, 2 * m)         # crown band ~ 2*module
    sref = tooth_root_stress(s_root, m, b_eff, 10.0)
    F_allow = SIGMA_ALLOW / sref * 10.0
    T_safe = F_allow * PRP / 1000.0
    return dict(CROWN_RC=CRC, CROWN_TEETH=CT, PINION_TEETH=PT, module=round(m, 3),
                PINION_RP=round(PRP, 2), i_g=i_g, PINION_T=face,
                T_safe_input_Nm_conservative=round(T_safe, 3),
                T_safe_input_Nm_realistic_2x=round(2 * T_safe, 3),
                note="proposed/not-implemented; tip-load+sharp-shoulder+30MPa are ~2-3x "
                     "conservative, so realistic T_safe ~2x; needs CAD clearance validation")


if __name__ == "__main__":
    o = run()
    o["proposed_resize"] = proposed_resize()
    print(f"=== Gear-tooth FEA  (allowable {SIGMA_ALLOW} MPa, i_g={o['i_g']:.3f}) ===")
    print(f"geometry: PINION_T={o['geometry']['PINION_T']}  "
          f"CROWN_TOOTH_H={o['geometry']['CROWN_TOOTH_H']}  T_CRANK={o['geometry']['T_CRANK']}")
    for name, d in o["gears"].items():
        print(f"  {name:7s} s_root={d['s_root']:.2f} h={d['h']:.2f} b_eff={d['b_eff']:.2f}  "
              f"sigma@10N={d['sigma_ref_at_10N']:.2f}MPa  F_allow={d['F_tooth_allow_N']:.0f}N  "
              f"T_safe={d['T_safe_input_Nm']:.2f} N.m")
    print(f"  -> BINDING: {o['binding_gear']}  T_safe(input shaft) = {o['T_safe_input_Nm']:.2f} N.m")
    os.makedirs(ITER, exist_ok=True)
    json.dump(o, open(os.path.join(ITER, "_gear_fea.json"), "w"), indent=2)
    print(f"wrote {os.path.join(ITER,'_gear_fea.json')}")

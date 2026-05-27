"""Render underwater FEA summary figures.

Two panels:
  1. fea/pictures/underwater_pressure.png — analytical/FEA hydrostatic
     compression vs depth (ε_lin, peak vM, peak displacement) for ν=0.42/0.45/0.48
     against the TPU 25 MPa yield reference. Reads
     fea/iterations/_underwater_pressure/results.json.

  2. fea/pictures/underwater_wet_modulus.png — wet-modulus sweep:
     peak vM and grip force at closure vs E_TPU (dry → saturated).
     Reads fea/iterations/under_E{40,32,28,20}*/metrics.json.

Run:  python fea/scripts/underwater_figures.py
"""
import json
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ITER = os.path.join(ROOT, "fea", "iterations")
PICS = os.path.join(ROOT, "fea", "pictures")
TPU_YIELD = 25.0   # MPa, conservative


def crush_panel():
    """Worst-case trapped-air vs flooded — peak vM and contact-wall deflection."""
    src_fl = os.path.join(ITER, "_underwater_pressure", "results.json")
    src_cr = os.path.join(ITER, "_underwater_crush", "results.json")
    if not (os.path.exists(src_fl) and os.path.exists(src_cr)):
        print("missing flooded or crush results"); return False
    fl = json.load(open(src_fl))["runs"]
    cr = json.load(open(src_cr))["runs"]
    by_nu_fl, by_nu_cr = {}, {}
    for r in fl: by_nu_fl.setdefault(r["nu"], []).append(r)
    for r in cr: by_nu_cr.setdefault(r["nu"], []).append(r)
    nu_target = 0.45
    fl_rs = sorted(by_nu_fl[nu_target], key=lambda x: x["depth_m"])
    cr_rs = sorted(by_nu_cr[nu_target], key=lambda x: x["depth_m"])
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.6))
    d = [r["depth_m"] for r in fl_rs]
    # (a) peak vM vs depth: flooded vs trapped-air, with yield
    axs[0].plot(d, [r["peak_vM_MPa"] for r in fl_rs], "o-",
                color="#1f77b4", lw=2, label="FLOODED (design intent)")
    axs[0].plot(d, [r["peak_vM_MPa"] for r in cr_rs], "s-",
                color="#d62728", lw=2, label="TRAPPED AIR (worst case)")
    axs[0].axhline(TPU_YIELD, ls="--", c="k", lw=1, alpha=0.6)
    axs[0].text(5, TPU_YIELD * 1.1, f"TPU yield ≈ {TPU_YIELD} MPa",
                fontsize=8, alpha=0.7)
    axs[0].set_yscale("log")
    axs[0].set_xlabel("depth (m)")
    axs[0].set_ylabel("peak von Mises (MPa)")
    axs[0].set_title("Pressure-induced stress: flooded vs trapped-air\n"
                     f"(ν = {nu_target}, plane-strain 2D)")
    axs[0].grid(alpha=0.3, which="both"); axs[0].legend(fontsize=9)
    # (b) contact-wall deflection vs depth (trapped-air only)
    cw = [r["contact_wall_disp_um"] for r in cr_rs]
    axs[1].plot(d, cw, "s-", color="#d62728", lw=2)
    axs[1].axhline(300.0, ls="--", c="grey", lw=1, alpha=0.6)
    axs[1].text(5, 350, "PRINT_CLEAR = 300 μm", fontsize=8, alpha=0.7)
    axs[1].axhline(2000.0, ls=":", c="darkorange", lw=1, alpha=0.6)
    axs[1].text(5, 2200, "rib spacing ~2 mm", fontsize=8, alpha=0.7)
    axs[1].set_xlabel("depth (m)")
    axs[1].set_ylabel("contact-wall inward deflection (μm)")
    axs[1].set_title("Trapped-air contact-wall collapse\n(0 in flooded case)")
    axs[1].grid(alpha=0.3)
    # (c) survival margin vs depth (trapped-air only) on log
    mg = [r["margin_to_yield"] for r in cr_rs[1:]]   # drop d=0 inf
    axs[2].plot(d[1:], mg, "s-", color="#d62728", lw=2, label="trapped-air margin")
    axs[2].axhline(1.0, ls="--", c="k", lw=1, alpha=0.6)
    axs[2].text(5, 1.2, "yield (margin = 1)", fontsize=8, alpha=0.7)
    axs[2].axhline(3.0, ls=":", c="grey", lw=1, alpha=0.5)
    axs[2].text(5, 3.3, "common design margin (3×)", fontsize=8, alpha=0.5)
    axs[2].set_yscale("log")
    axs[2].set_xlabel("depth (m)")
    axs[2].set_ylabel("margin = TPU_yield / peak vM  (×)")
    axs[2].set_title("Trapped-air yield margin vs depth")
    axs[2].grid(alpha=0.3, which="both"); axs[2].legend(fontsize=9)
    fig.suptitle("Underwater pressure-crush check — Fin Ray cells flooded "
                 "(design) vs trapped air (worst case)", fontsize=11)
    fig.tight_layout()
    fp = os.path.join(PICS, "underwater_crush.png")
    fig.savefig(fp, dpi=120)
    print(f"wrote {fp}")
    return True


def pressure_panel():
    src = os.path.join(ITER, "_underwater_pressure", "results.json")
    if not os.path.exists(src):
        print(f"missing {src}"); return False
    data = json.load(open(src))
    runs = data["runs"]
    by_nu = {}
    for r in runs:
        by_nu.setdefault(r["nu"], []).append(r)
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.4))
    colors = {0.42: "#1f77b4", 0.45: "#2ca02c", 0.48: "#d62728"}
    # (a) linear strain vs depth (analytical)
    for nu, rs in sorted(by_nu.items()):
        rs.sort(key=lambda x: x["depth_m"])
        d = [r["depth_m"] for r in rs]
        e = [r["eps_lin_analytical_pct"] for r in rs]
        axs[0].plot(d, e, "o-", color=colors[nu], label=f"ν = {nu}")
    axs[0].set_xlabel("depth (m)")
    axs[0].set_ylabel("linear strain ε (%)  (analytical −P/3K)")
    axs[0].set_title("Bulk linear contraction vs depth")
    axs[0].grid(alpha=0.3); axs[0].legend(fontsize=9)
    # (b) peak vM at clamp vs depth, with TPU yield reference
    for nu, rs in sorted(by_nu.items()):
        d = [r["depth_m"] for r in rs]
        v = [r["peak_vM_MPa"] for r in rs]
        axs[1].plot(d, v, "o-", color=colors[nu], label=f"ν = {nu}")
    axs[1].axhline(TPU_YIELD, ls="--", c="k", lw=1, alpha=0.6)
    axs[1].text(5, TPU_YIELD * 0.55, f"TPU yield ≈ {TPU_YIELD} MPa",
                fontsize=8, alpha=0.7)
    axs[1].set_yscale("log")
    axs[1].set_xlabel("depth (m)")
    axs[1].set_ylabel("peak von Mises (MPa) — at clamp")
    axs[1].set_title("Pressure-induced deviatoric stress\n"
                     "(plane-strain UPPER bound)")
    axs[1].grid(alpha=0.3, which="both"); axs[1].legend(fontsize=9)
    # (c) peak displacement vs depth (μm)
    for nu, rs in sorted(by_nu.items()):
        d = [r["depth_m"] for r in rs]
        u = [r["peak_disp_um"] for r in rs]
        axs[2].plot(d, u, "o-", color=colors[nu], label=f"ν = {nu}")
    axs[2].axhline(300.0, ls="--", c="grey", lw=1, alpha=0.6)
    axs[2].text(5, 320, "PRINT_CLEAR = 300 μm", fontsize=8, alpha=0.7)
    axs[2].set_xlabel("depth (m)")
    axs[2].set_ylabel("peak displacement |u| (μm)")
    axs[2].set_title("Pressure-induced contraction")
    axs[2].grid(alpha=0.3); axs[2].legend(fontsize=9)
    fig.suptitle("Hydrostatic compression of the flooded TPU finger — "
                 "plane-strain CONSERVATIVE upper bound", fontsize=11)
    fig.tight_layout()
    os.makedirs(PICS, exist_ok=True)
    fp = os.path.join(PICS, "underwater_pressure.png")
    fig.savefig(fp, dpi=120)
    print(f"wrote {fp}")
    return True


def wet_modulus_panel():
    cases = [("under_E40_dry", 40.0, "dry"),
             ("under_E32_wet20", 32.0, "wet 20%"),
             ("under_E28_wet30", 28.0, "wet 30%"),
             ("under_E20_wet50", 20.0, "wet 50%")]
    data = []
    for name, E, label in cases:
        fp = os.path.join(ITER, name, "metrics.json")
        if not os.path.exists(fp):
            print(f"missing {fp} (run not done yet)"); continue
        m = json.load(open(fp))
        data.append(dict(name=name, E=E, label=label, m=m))
    if len(data) < 2:
        print(f"only {len(data)} runs ready — skipping wet-modulus panel"); return False
    fig, axs = plt.subplots(1, 3, figsize=(14, 4.4))
    E = np.array([d["E"] for d in data])
    vM = np.array([d["m"]["max_von_mises_MPa"] for d in data])
    grip = np.array([d["m"]["grip_at_press_N"] for d in data])
    tip = np.array([d["m"]["tip_inward_mm"] for d in data])
    arc = np.array([d["m"].get("contact_arc_deg", np.nan) for d in data])
    margin = np.array([d["m"].get("margin_x", np.nan) for d in data])
    # (a) peak vM vs E
    axs[0].plot(E, vM, "o-", color="#d62728")
    axs[0].set_xlabel("E_TPU (MPa)")
    axs[0].set_ylabel("peak von Mises (MPa) — at PRESS_AT_REPORT")
    axs[0].set_title("Stress at the same closure (8 mm)")
    axs[0].grid(alpha=0.3); axs[0].invert_xaxis()
    for d, vm_ in zip(data, vM):
        axs[0].annotate(d["label"], (d["E"], vm_), textcoords="offset points",
                        xytext=(6, 4), fontsize=8)
    # (b) grip force at closure vs E
    axs[1].plot(E, grip, "o-", color="#1f77b4")
    axs[1].set_xlabel("E_TPU (MPa)")
    axs[1].set_ylabel("grip force at closure (N)")
    axs[1].set_title("Grip force at the same actuator stroke")
    axs[1].grid(alpha=0.3); axs[1].invert_xaxis()
    # (c) wrap quality (contact arc + tip inward)
    ax2 = axs[2]
    ln1, = ax2.plot(E, arc, "o-", color="#2ca02c", label="contact arc (°)")
    ax2.set_xlabel("E_TPU (MPa)")
    ax2.set_ylabel("contact arc (deg)", color="#2ca02c")
    ax2.tick_params(axis="y", labelcolor="#2ca02c")
    ax2.invert_xaxis()
    ax3 = ax2.twinx()
    ln2, = ax3.plot(E, -tip, "s--", color="#9467bd", label="tip inward (mm)")
    ax3.set_ylabel("tip inward travel (mm)", color="#9467bd")
    ax3.tick_params(axis="y", labelcolor="#9467bd")
    ax2.set_title("Wrap quality vs softening")
    ax2.grid(alpha=0.3)
    fig.suptitle("Wet-modulus sweep: dry TPU → saturated soft TPU "
                 "(reported at PRESS_AT_REPORT = 8 mm closure, R=22 mm cylinder)",
                 fontsize=11)
    fig.tight_layout()
    os.makedirs(PICS, exist_ok=True)
    fp = os.path.join(PICS, "underwater_wet_modulus.png")
    fig.savefig(fp, dpi=120)
    print(f"wrote {fp}")
    # also dump aggregated json
    out = [dict(E=float(d["E"]), label=d["label"], **d["m"]) for d in data]
    aggp = os.path.join(ITER, "_underwater_wet_modulus.json")
    json.dump(out, open(aggp, "w"), indent=2)
    print(f"wrote {aggp}")
    return True


def main():
    pressure_panel()
    crush_panel()
    wet_modulus_panel()


if __name__ == "__main__":
    main()

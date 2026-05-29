"""Post-process the Fin Ray FEA: stress/deformation animation, force-closure
curve, Blender-ready morph npz, and stats."""
import os, json, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.tri import Triangulation
from matplotlib.collections import LineCollection

HERE = os.path.dirname(__file__)
OUT = os.path.normpath(os.path.join(HERE, "..", "render_bundle", "fea"))
os.makedirs(OUT, exist_ok=True)

R = np.load(os.path.join(HERE, "results.npz"))
frames = R["frames"]          # (F, 2, N)
vms = R["vms"]                # (F, N)
tris = R["tris"].T            # (M, 3)
curve = R["curve"]            # (F, 3): load, tip_dx, tip_dy
E, nu, Ft = float(R["E"]), float(R["nu"]), float(R["F_target"])
lm = json.load(open(os.path.join(HERE, "finger_landmarks.json")))

F = frames.shape[0]
vmax = float(np.percentile(vms, 99.5))
p0 = frames[0]

# artifact arc (context): R=22 mm cylinder tangent to the contact face mid-patch
Rart = 22.0
yc = lm["base_y"] + 0.52 * lm["blade_len"]
cx, cy = lm["contact_x"] - Rart, yc
th = np.linspace(np.deg2rad(-55), np.deg2rad(55), 80)
arc = np.vstack([cx + Rart * np.cos(th), cy + Rart * np.sin(th)])

# ---------- stress / deformation animation ----------
fig, ax = plt.subplots(figsize=(4.2, 7.2), dpi=150)
ax.set_aspect("equal"); ax.axis("off")
xpad = (p0[0].max() - p0[0].min()) * 0.25
ax.set_xlim(p0[0].min() - Rart - 4, p0[0].max() + xpad)
ax.set_ylim(p0[1].min() - 3, p0[1].max() + 6)

def draw(i):
    ax.clear(); ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(p0[0].min() - Rart - 4, p0[0].max() + xpad)
    ax.set_ylim(p0[1].min() - 3, p0[1].max() + 6)
    P = frames[i]
    tri = Triangulation(P[0], P[1], tris)
    tpc = ax.tripcolor(tri, vms[i], shading="gouraud", cmap="inferno",
                       vmin=0, vmax=vmax)
    ax.triplot(tri, color="k", lw=0.12, alpha=0.25)
    ax.plot(arc[0], arc[1], color="#39c", lw=3, alpha=0.75)
    ax.fill_between(arc[0], arc[1], cy - Rart, color="#39c", alpha=0.10)
    ld, dx, dy = curve[i]
    ax.set_title(f"Fin Ray finger FEA (TPU 95A, E={E:.0f} MPa, plane strain)\n"
                 f"grip load {ld:4.2f} N   tip wrap {dx:+.1f} mm",
                 fontsize=8)
    return tpc,

draw(0)
sm = plt.cm.ScalarMappable(cmap="inferno",
                           norm=plt.Normalize(vmin=0, vmax=vmax))
cb = fig.colorbar(sm, ax=ax, fraction=0.04, pad=0.02)
cb.set_label("von Mises stress (MPa)", fontsize=7)
cb.ax.tick_params(labelsize=6)

# ping-pong (close then release) for a nicer loop
order = list(range(F)) + list(range(F - 2, 0, -1))
anim = FuncAnimation(fig, draw, frames=order, blit=False)
mp4 = os.path.join(OUT, "stress_animation.mp4")
anim.save(mp4, writer=FFMpegWriter(fps=12, bitrate=2400))
plt.close(fig)
print("wrote", mp4)

# ---------- force / closure curve ----------
fig2, ax2 = plt.subplots(figsize=(5, 3.4), dpi=150)
ax2.plot(curve[:, 1], curve[:, 0], "-o", ms=3, color="#c33")
ax2.set_xlabel("tip inward wrap (mm)"); ax2.set_ylabel("grip load (N)")
ax2.set_title("Fin Ray grip load vs tip wrap (FEA)")
ax2.grid(alpha=0.3)
fig2.tight_layout()
png = os.path.join(OUT, "force_curve.png")
fig2.savefig(png); plt.close(fig2)
print("wrote", png)

# ---------- Blender-ready morph ----------
morph = os.path.join(OUT, "finray_morph.npz")
np.savez_compressed(
    morph,
    rest=p0.astype(np.float32),          # (2, N) reference XY (mm)
    frames=frames.astype(np.float32),    # (F, 2, N) deformed XY per step
    tris=tris.astype(np.int32),          # (M, 3)
    vms=vms.astype(np.float32),          # (F, N) von Mises (MPa)
    curve=curve.astype(np.float32),      # (F, 3) load, tip_dx, tip_dy
    z_extrude=np.float32(lm["thickness"]),   # 10 mm depth
    E_MPa=np.float32(E), nu=np.float32(nu))
print("wrote", morph)

# ---------- stats ----------
stats = dict(
    model="Fin Ray finger, plane-strain, St.-Venant-Kirchhoff, total Lagrangian",
    material=dict(name="Bambu TPU 95A HF", E_MPa=E, nu=nu,
                  note="E = ISO 527 in-plane (X-Y) printed-specimen modulus 9.8 MPa "
                       "(Bambu TDS); nu literature estimate (Bambu publishes none)"),
    mesh=dict(nodes=int(p0.shape[1]), tris=int(tris.shape[0])),
    load_steps=int(F - 1),
    grip_load_N=dict(max=float(curve[:, 0].max()),
                     note="applied horizontal contact-patch load = grip force"),
    tip_wrap_mm=dict(inward_dx=float(curve[:, 1].max()),
                     axial_dy=float(curve[-1, 2])),
    von_mises_MPa=dict(max=float(vms.max()), p99_5=vmax),
    limit_point_N="~5.7 (load-control snap-through; solve capped at 5.4 N)",
)
with open(os.path.join(OUT, "stats_finray.json"), "w") as fh:
    json.dump(stats, fh, indent=2)
print(json.dumps(stats, indent=2))

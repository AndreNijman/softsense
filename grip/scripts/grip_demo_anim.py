"""Grip-demo animation — *why the crosshatch grips underwater*, for a lay audience.

Two faces, side by side, in motion:
  LEFT  — a flat / smooth face (the old single-axis ridge face behaves the same on
          wet cross-slip): a water film stays trapped, the object hydroplanes and
          SLIDES OFF when pulled.
  RIGHT — the shipped crosshatch micro-posts (pitch 1.8, post 1.26, channel 0.54,
          height 0.9 mm): the water is squeezed out through the crossing channels,
          the posts bite, and the object is HELD when pulled.

Story loop:  1 press · 2 drain · 3 pull sideways · 4 verdict.  The wet object is
rendered translucent so you can watch the water drain and the posts make contact
underneath.  Geometry is the real shipped relief; this is a *mechanism* render, not
an FEA solve (the stress/durability montage is montage_grip_fea_hq.py).

Usage:
  python grip/scripts/grip_demo_anim.py                 # -> renders/grip_demo.gif (+ .png money shot)
  python grip/scripts/grip_demo_anim.py --still 32      # one frame -> /tmp peek
  python grip/scripts/grip_demo_anim.py --fast          # fewer frames / smaller (draft)
"""
import os, sys
import numpy as np
import vtk
from vtk.util import numpy_support as ns
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "renders", "grip_demo.gif")

# ---- geometry (the shipped crosshatch, real dimensions) --------------------
L       = 5.0          # patch (mm)
BASE_H  = 0.7          # TPU base slab below the posts
PITCH   = 1.8          # crosshatch pitch
LAND    = 1.26         # post width
GAP     = PITCH - LAND  # 0.54 channel
POST_H  = 0.9          # post height
FILM_TH = 0.22         # trapped water-film thickness on the smooth face

TOP_X   = BASE_H + POST_H            # crosshatch post-top contact height (1.6)
TOP_S   = BASE_H + FILM_TH           # smooth face: object rides on the film (0.92)
OBJ_TH  = 1.25                       # object slab thickness
OBJ_W   = 3.4                        # object footprint (centred, < L so posts show around it)
OBJ_CX  = L / 2.0                    # object centre
OBJ_HI  = 2.95                       # object bottom start height (lowered in)
SLIDE   = 2.7                        # how far the object skates off the smooth film

# ---- palette ---------------------------------------------------------------
TPU_BASE = (0.16, 0.29, 0.33)   # dark wet TPU
TPU_POST = (0.22, 0.40, 0.45)
GOLD     = (0.95, 0.72, 0.18)   # contact "bite" glow
WATER    = (0.16, 0.55, 0.95)
OBJ_COL  = (0.62, 0.85, 0.90)   # translucent wet object (glassy)
OBJ_EDGE = (0.08, 0.27, 0.32)   # dark silhouette so it reads when transparent
FIXED_BOUNDS = (-0.8, L + SLIDE + 0.9, -0.8, L + 0.8, 0.0, OBJ_HI + OBJ_TH + 0.25)


# ---- VTK helpers -----------------------------------------------------------
def _finish(actor, color, opacity, spec, specpow, ambient=0.32, edge=None):
    pr = actor.GetProperty()
    pr.SetColor(*color); pr.SetOpacity(opacity)
    pr.SetInterpolationToPhong()
    pr.SetAmbient(ambient); pr.SetDiffuse(0.85)
    pr.SetSpecular(spec); pr.SetSpecularPower(specpow)
    if edge is not None:
        pr.EdgeVisibilityOn(); pr.SetEdgeColor(*edge); pr.SetLineWidth(edge_w)
    return actor

edge_w = 1.4

def box(b, color, opacity=1.0, spec=0.25, specpow=24, edge=None):
    s = vtk.vtkCubeSource(); s.SetBounds(*b)
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(s.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m)
    return _finish(a, color, opacity, spec, specpow, edge=edge)

def sphere(c, r, color, opacity=1.0):
    s = vtk.vtkSphereSource(); s.SetCenter(*c); s.SetRadius(r)
    s.SetThetaResolution(18); s.SetPhiResolution(18)
    m = vtk.vtkPolyDataMapper(); m.SetInputConnection(s.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(m)
    return _finish(a, color, opacity, 0.5, 40)


def _post_starts():
    k = 0; out = []
    while k * PITCH < L:
        x0 = k * PITCH
        out.append((x0, min(x0 + LAND, L)))
        k += 1
    return out

def _gap_starts():
    k = 0; out = []
    while k * PITCH + LAND < L:
        g0 = k * PITCH + LAND
        out.append((g0, min(g0 + GAP, L)))
        k += 1
    return out


def build_scene(kind, st):
    """kind in {'smooth','cross'}; st = animation state dict -> list of actors."""
    acts = []
    # --- TPU base slab ---
    acts.append(box((0, L, 0, L, 0, BASE_H), TPU_BASE, spec=0.18, specpow=16))

    if kind == "cross":
        glow = st["glow"]
        pcol = tuple(np.array(TPU_POST) * (1 - glow) + np.array(GOLD) * glow)
        for (xa, xb) in _post_starts():
            for (ya, yb) in _post_starts():
                acts.append(box((xa, xb, ya, yb, BASE_H, TOP_X), pcol,
                                spec=0.30 + 0.4 * glow, specpow=30))
        # water in the channel network (vertical x-gaps + horizontal y-gaps)
        wl = st["water"]                       # 0..1 fill of channel depth
        if wl > 0.02:
            wtop = BASE_H + wl * POST_H
            for (ga, gb) in _gap_starts():     # x-gaps, full y
                acts.append(box((ga, gb, 0, L, BASE_H, wtop), WATER,
                                opacity=0.62, spec=0.6, specpow=60))
            for (ga, gb) in _gap_starts():     # y-gaps, full x
                acts.append(box((0, L, ga, gb, BASE_H, wtop), WATER,
                                opacity=0.62, spec=0.6, specpow=60))
        # droplets jetting out the +x and +y edges while draining
        for (px, py, pz) in st.get("drops", []):
            acts.append(sphere((px, py, pz), 0.22, WATER, opacity=0.85))
    else:
        # smooth: a persistent trapped water film across the whole face
        acts.append(box((0, L, 0, L, BASE_H, BASE_H + FILM_TH), WATER,
                        opacity=0.72, spec=0.7, specpow=60))

    # --- the wet object (translucent + dark edges so it reads through) ---
    dx = st["dx"]; bz = st["bz"]; ox0 = OBJ_CX - OBJ_W / 2; ox1 = OBJ_CX + OBJ_W / 2
    acts.append(box((ox0 + dx, ox1 + dx, ox0, ox1, bz, bz + OBJ_TH),
                    OBJ_COL, opacity=0.56, spec=0.8, specpow=80, edge=OBJ_EDGE))
    return acts


def render(kind, st, size, bg):
    ren = vtk.vtkRenderer(); ren.SetBackground(*bg)
    # NOTE: depth peeling silently drops translucent actors in this offscreen Mesa
    # context, so we use plain alpha blending. Actors are added opaque-first,
    # translucent-last (build_scene order) which keeps blending order sane.
    for a in build_scene(kind, st):
        ren.AddActor(a)
    ren.AutomaticLightCreationOff()
    for pos, inten, col in (((-0.6, 1.0, 1.0), 0.95, (1.0, 0.97, 0.92)),
                            ((0.9, -0.2, 0.5), 0.45, (0.9, 0.95, 1.0)),
                            ((0.0, 0.3, -1.0), 0.30, (1, 1, 1))):
        lt = vtk.vtkLight(); lt.SetLightTypeToCameraLight(); lt.SetPosition(*pos)
        lt.SetFocalPoint(0, 0, 0); lt.SetIntensity(inten); lt.SetColor(*col)
        ren.AddLight(lt)

    rw = vtk.vtkRenderWindow(); rw.SetOffScreenRendering(1); rw.AddRenderer(ren)
    rw.SetSize(*size); rw.SetMultiSamples(8); rw.SetAlphaBitPlanes(1)

    u = np.array((0.46, -0.80, 0.46)); u /= np.linalg.norm(u)
    xb = FIXED_BOUNDS
    fx, fy, fz = (xb[0] + xb[1]) / 2, (xb[2] + xb[3]) / 2, TOP_X * 0.9
    cam = ren.GetActiveCamera(); cam.SetViewUp(0, 0, 1)
    cam.SetFocalPoint(fx, fy, fz)
    cam.SetPosition(fx + 10 * u[0], fy + 10 * u[1], fz + 10 * u[2])
    ren.ResetCamera(*xb); ren.ResetCameraClippingRange(); cam.Zoom(1.65)
    rw.Render()

    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(rw)
    w2i.SetInputBufferTypeToRGB(); w2i.ReadFrontBufferOff(); w2i.Update()
    im = w2i.GetOutput(); W, H, _ = im.GetDimensions()
    arr = ns.vtk_to_numpy(im.GetPointData().GetScalars()).reshape(H, W, -1)[::-1].copy()
    rw.Finalize()
    return arr


# ---- animation timeline ----------------------------------------------------
def ss(t):                      # smoothstep ease
    t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)

def lerp(a, b, t): return a + (b - a) * t

def timeline(fast=False):
    """Returns a list of frames; each = (phase_caption, smooth_state, cross_state,
    pull, vs, vc)."""
    n = (6, 5, 8, 5) if fast else (10, 8, 12, 8)
    n_app, n_drn, n_pul, n_ver = n
    frames = []

    def push(cap, smooth, cross, pull, vs, vc):
        frames.append((cap, smooth, cross, pull, vs, vc))

    # 1 — press: object lowered onto both faces
    for i in range(n_app):
        t = ss(i / (n_app - 1))
        smooth = dict(bz=lerp(OBJ_HI, TOP_S, t), dx=0, water=1, glow=0, drops=[])
        cross  = dict(bz=lerp(OBJ_HI, TOP_X, t), dx=0, water=1, glow=0, drops=[])
        push("1 · a wet object is pressed onto the surface", smooth, cross, False, "", "")

    # 2 — drain: smooth keeps the film; crosshatch squeezes water out the channels
    for i in range(n_drn):
        t = ss(i / (n_drn - 1))
        drops = []
        for gy in (1.0, 2.8, 4.0):                 # jets off the +x edge
            drops.append((L + lerp(0.1, 1.7, t), gy, BASE_H + 0.25 + 0.4 * np.sin(3 * t)))
        for gx in (1.4, 3.2):                       # jets off the +y edge
            drops.append((gx, L + lerp(0.1, 1.5, t), BASE_H + 0.25 + 0.4 * np.sin(3 * t)))
        smooth = dict(bz=TOP_S, dx=0, water=1, glow=0, drops=[])
        cross  = dict(bz=TOP_X, dx=0, water=lerp(1.0, 0.22, t), glow=t,
                      drops=drops if t < 0.92 else [])
        push("2 · water is squeezed out — smooth traps a film, crosshatch drains it away",
             smooth, cross, False, "", "")

    # 3 — pull sideways: smooth skates off, crosshatch holds
    for i in range(n_pul):
        t = ss(i / (n_pul - 1))
        smooth = dict(bz=TOP_S, dx=lerp(0, SLIDE, t), water=1, glow=0, drops=[])
        cross  = dict(bz=TOP_X, dx=lerp(0, 0.06, ss(min(1, 2 * t))), water=0.22, glow=1, drops=[])
        push("3 · now pull the object sideways", smooth, cross, True, "", "")

    # 4 — verdict hold
    for i in range(n_ver):
        smooth = dict(bz=TOP_S, dx=SLIDE, water=1, glow=0, drops=[])
        cross  = dict(bz=TOP_X, dx=0.06, water=0.22, glow=1, drops=[])
        push("the smooth face hydroplanes · the crosshatch bites and holds",
             smooth, cross, True, "SLIPS  ✗", "HOLDS  ✓")
    return frames


# ---- compose two panels + captions ----------------------------------------
def compose(fig, axL, axR, imL, imR, frame, txt):
    cap, _, _, pull, vs, vc = frame
    imL_im, imR_im = txt["imL"], txt["imR"]
    imL_im.set_data(imL); imR_im.set_data(imR)
    txt["cap"].set_text(cap)
    # pull arrows
    for ar, show in ((txt["arrL"], pull), (txt["arrR"], pull)):
        ar.set_visible(show)
    txt["vsL"].set_text(vs); txt["vsR"].set_text(vc)
    txt["vsL"].set_color("#c0392b"); txt["vsR"].set_color("#1f8a4c")


def build_figure(W, H, frames):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor="#f4f4f7")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.86, bottom=0.075, wspace=0.02)
    axL = fig.add_subplot(1, 2, 1); axR = fig.add_subplot(1, 2, 2)
    for ax in (axL, axR): ax.set_xticks([]); ax.set_yticks([])
    for sp in axR.spines.values(): sp.set_color("#e6a700"); sp.set_linewidth(3)
    for sp in axL.spines.values(): sp.set_color("#cccccc"); sp.set_linewidth(1.2)

    blankL = np.zeros_like(frames[0][1]) if False else None
    txt = {}
    txt["imL"] = axL.imshow(np.zeros((10, 10, 3), np.uint8))
    txt["imR"] = axR.imshow(np.zeros((10, 10, 3), np.uint8))

    axL.set_title("SMOOTH face  (no texture)", fontsize=13, color="#444", fontweight="bold", pad=6)
    axR.set_title("★ CROSSHATCH micro-posts  (shipped)", fontsize=13,
                  color="#b8860b", fontweight="bold", pad=6)

    fig.text(0.5, 0.965, "Why the crosshatch grips underwater — smooth slips, crosshatch holds",
             ha="center", fontsize=19, fontweight="bold", color="#141414")
    fig.text(0.5, 0.915,
             "same wet object, same squeeze · left: flat face traps a water film · "
             "right: 1.8 mm posts with 0.54 mm drainage channels",
             ha="center", fontsize=10.5, color="#15506e")
    txt["cap"] = fig.text(0.5, 0.038, "", ha="center", fontsize=12.5,
                          fontweight="bold", color="#15506e")

    # pull arrows (figure coords), one over each panel
    txt["arrL"] = fig.text(0.27, 0.50, "pull →", ha="center", fontsize=15,
                           fontweight="bold", color="#c0392b", visible=False,
                           bbox=dict(boxstyle="rarrow,pad=0.3", fc="#ffe2dc", ec="#c0392b", lw=2))
    txt["arrR"] = fig.text(0.77, 0.50, "pull →", ha="center", fontsize=15,
                           fontweight="bold", color="#1f8a4c", visible=False,
                           bbox=dict(boxstyle="rarrow,pad=0.3", fc="#e0f3e6", ec="#1f8a4c", lw=2))
    txt["vsL"] = fig.text(0.27, 0.14, "", ha="center", fontsize=17, fontweight="bold")
    txt["vsR"] = fig.text(0.77, 0.14, "", ha="center", fontsize=17, fontweight="bold")
    return fig, axL, axR, txt


def main():
    fast = "--fast" in sys.argv
    still = None
    if "--still" in sys.argv:
        still = int(sys.argv[sys.argv.index("--still") + 1])
    psize = (620, 560) if fast else (840, 760)
    bgL, bgR = (0.955, 0.955, 0.962), (0.999, 0.972, 0.90)

    frames = timeline(fast=fast)
    print(f"{len(frames)} frames, panel {psize}")

    if still is not None:
        cap, sm, cr, pull, vs, vc = frames[still]
        imL = render("smooth", sm, psize, bgL)
        imR = render("cross",  cr, psize, bgR)
        W, H = psize[0] * 2 + 30, psize[1] + 230
        fig, axL, axR, txt = build_figure(W, H, [(cap, imL, imR)])
        compose(fig, axL, axR, imL, imR, frames[still], txt)
        p = "/tmp/claude-1000/-home-andre-Projects-softsense/" \
            "37b8a3e8-aa39-49e8-8a81-780f6a85a4d1/scratchpad/grip_demo_still.png"
        fig.savefig(p, dpi=100, facecolor="#f4f4f7")
        print("WROTE", p); return

    # render all VTK frames once
    print("rendering VTK frames...")
    rendered = []
    for k, (cap, sm, cr, pull, vs, vc) in enumerate(frames):
        rendered.append((render("smooth", sm, psize, bgL),
                         render("cross",  cr, psize, bgR)))
        print(f"  frame {k+1}/{len(frames)}")

    from matplotlib.animation import FuncAnimation, PillowWriter
    W, H = psize[0] * 2 + 30, psize[1] + 230
    fig, axL, axR, txt = build_figure(W, H, frames)

    # hold the last frame a beat, then loop
    order = list(range(len(frames))) + [len(frames) - 1] * (3 if fast else 5)

    def upd(idx):
        k = order[idx]
        imL, imR = rendered[k]
        compose(fig, axL, axR, imL, imR, frames[k], txt)
        return []

    # money-shot PNG = the verdict frame
    vk = len(frames) - 1
    compose(fig, axL, axR, rendered[vk][0], rendered[vk][1], frames[vk], txt)
    png = OUT.replace(".gif", ".png")
    fig.savefig(png, dpi=110, facecolor="#f4f4f7")
    print("WROTE", png, f"({os.path.getsize(png)/1e6:.1f} MB)")

    an = FuncAnimation(fig, upd, frames=len(order), blit=False)
    an.save(OUT, writer=PillowWriter(fps=12), dpi=90,
            savefig_kwargs={"facecolor": "#f4f4f7"})
    print("WROTE", OUT, f"({os.path.getsize(OUT)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()

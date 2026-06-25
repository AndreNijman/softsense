#!/usr/bin/env python3
"""assembly_video.py -- high-quality, readable step-by-step assembly animation of
the gripper, INCLUDING the heat-stake caps being melted on with a soldering iron.

Headless GPU (pyrender + EGL). Builds gripper.gen_step() ONCE, tessellates each
part, then animates the build in order. Qualities (the old version was a flat
grey blob that orbited past the action):

  * high-contrast legibility palette (parts separate by value AND hue)
  * EDGE OUTLINES -- a per-part id pass + a depth pass are Sobel'd and composited
    as dark lines, so every part has a crisp silhouette + crease outline
  * a ground plane + a painted contact shadow ground the object
  * the camera FRAMES EACH STEP -- dollies/pans to the parts being added and
    swings around to the -Z back face + zooms IN for the heat-stake close-up
  * correct insertion axes (pins/caps run along Z); a soldering-iron prop dabs
    each cap as it mushrooms + glows into a rivet head
  * 2x supersampled then downscaled for clean anti-aliased edges

PARALLELISM: rendering is single-threaded per frame but every frame is
independent, so by default we fan the frames out across all CPU cores as worker
subprocesses. gen_step() is built ONCE in the orchestrator and the tessellated
meshes are cached to disk; each worker loads the cache (no rebuild) and renders
its slice. ~Ncores faster.

  python scripts/assembly_video.py                  # full render, all cores
  python scripts/assembly_video.py --workers 1      # force single process
  python scripts/assembly_video.py --frame 210      # one frame -> /tmp (tuning)
  # (internal) worker mode:
  python scripts/assembly_video.py --range 0:30 --cache C.pkl --outdir D
"""
import os, sys, math, argparse, pickle
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import numpy as np

POSE = 0.14                 # slightly open so the mechanism reads
OUTW, OUTH = 1600, 1200     # final output resolution
SS = 2                      # supersample factor (render at SSx, downscale)
W, H = OUTW * SS, OUTH * SS
FPS = 30
BG = (0.92, 0.94, 0.965)
TESS = 0.25

# ------------------------------------------------------------ legibility palette
# key = label.split('_')[0]
PALETTE = {
    "enclosure": (0.50, 0.55, 0.62, 1.0),
    "front":     (0.64, 0.68, 0.74, 1.0),   # front_cover
    "drive":     (0.38, 0.62, 0.58, 1.0),   # drive_arm_* (teal)
    "follower":  (0.76, 0.63, 0.40, 1.0),   # amber
    "finger":    (0.42, 0.46, 0.53, 1.0),   # blue-grey (was near-black -> blob)
    "input":     (0.64, 0.50, 0.34, 1.0),   # input_pinion_shaft (bronze)
    "pin":       (0.82, 0.84, 0.88, 1.0),   # steel
    "cap":       (0.95, 0.56, 0.20, 1.0),   # orange
}
GROUND_RGBA = (0.80, 0.82, 0.85, 1.0)
IRON_STEEL  = (0.66, 0.69, 0.73, 1.0)
IRON_HANDLE = (0.13, 0.14, 0.16, 1.0)


def pal(lbl):
    return PALETTE.get(lbl.split("_")[0], (0.6, 0.62, 0.66, 1.0))


# ------------------------------------------------------------------ timeline
def spec(lbl):
    """per-part: phase, slide-in unit vector, slide distance. CORRECT axes:
    pins run along Z and insert from +Z; caps seat onto the -Z stud face."""
    if lbl == "enclosure":            return 0, (0, 1, 0), 34
    if lbl == "input_pinion_shaft":   return 0, (0, -1, 0), 52
    if lbl.startswith("drive_arm"):   return 1, (0, 0, 1), 48
    if lbl.startswith("follower"):    return 1, (0, 0, 1), 40
    if lbl.startswith("finger"):      return 2, (0, 1, 0), 88
    if lbl.startswith("pin_"):        return 3, (0, 0, 1), 50
    if lbl.startswith("cap_"):        return 4, (0, 0, -1), 22
    if lbl == "front_cover":          return 5, (0, 0, 1), 55
    return 1, (0, 0, 1), 40

PHASE = {0: (6, 30), 1: (38, 68), 2: (76, 104), 3: (112, 142), 4: (158, 184), 5: (264, 292)}
MELT = (192, 260)
HOLD_END = 326
NFRAMES = HOLD_END

CAPTIONS = [
    (0,   "Flooded enclosure + input drive shaft"),
    (38,  "Crown / gear arms + coupler followers"),
    (76,  "Fin-Ray compliant fingers"),
    (112, "Heat-stake journal pins slide in (along their axis)"),
    (158, "Retaining caps drop onto the pin studs"),
    (192, "Heat-stake: a soldering iron melts each cap into a rivet head"),
    (264, "Snap-on front cover"),
    (296, "Assembled — all-printed, zero metal fasteners"),
]

# camera keyframes: (frame, target xyz, azim deg, elev deg, distance)
# azim 0 = +Z front; azim ~195 = -Z back (the cap / heat-stake face).
CAMKEYS = [
    (0,   (0, -4,  8),   28, 15, 235),
    (38,  (0, 16,  7),   33, 18, 205),
    (76,  (0, 48, 13),   30, 12, 315),
    (112, (0, 20,  8),   38, 20, 178),
    (158, (0, 18, -2),  118, 16, 165),
    (196, (0, 16, -3),  198, 12, 112),
    (250, (0, 16, -3),  198, 12, 112),
    (266, (0,  2, 12),   40, 18, 258),
    (300, (0, 28,  9),   22, 16, 292),
    (NFRAMES - 1, (0, 28, 9), 22, 16, 292),
]


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def caption_for(f):
    out = CAPTIONS[0][1]
    for sf, txt in CAPTIONS:
        if f >= sf:
            out = txt
    return out


def cam_at(f):
    ks = CAMKEYS
    a, b = ks[0], ks[-1]
    for i in range(len(ks) - 1):
        if ks[i][0] <= f <= ks[i + 1][0]:
            a, b = ks[i], ks[i + 1]; break
    if f <= ks[0][0]:  a = b = ks[0]
    if f >= ks[-1][0]: a = b = ks[-1]
    span = max(1, b[0] - a[0]); t = smooth((f - a[0]) / span)
    tgt = np.array(a[1], float) * (1 - t) + np.array(b[1], float) * t
    azim = a[2] * (1 - t) + b[2] * t
    elev = a[3] * (1 - t) + b[3] * t
    dist = a[4] * (1 - t) + b[4] * t
    A = math.radians(azim); E = math.radians(elev)
    d = np.array([math.cos(E) * math.sin(A), math.sin(E), math.cos(E) * math.cos(A)])
    return tgt + d * dist, tgt


def look_pose(eye, tgt, up=np.array([0, 1, 0.])):
    f = tgt - eye; f /= (np.linalg.norm(f) + 1e-9)
    s = np.cross(f, up); s /= (np.linalg.norm(s) + 1e-9)
    u = np.cross(s, f)
    M = np.eye(4); M[:3, 0] = s; M[:3, 1] = u; M[:3, 2] = -f; M[:3, 3] = eye
    return M


# ------------------------------------------------------------------ parts (build / cache)
def build_parts_from_model():
    """Run gen_step() at POSE and tessellate -> [(label, verts, faces)]. EXPENSIVE."""
    os.environ["GRIPPER_OPEN"] = str(POSE)
    import gripper
    print("[build] gen_step ...", flush=True)
    asm = gripper.gen_step()
    parts = []
    for leaf in asm.children:
        lbl = getattr(leaf, "label", "") or ""
        try:
            V, Tr = leaf.tessellate(tolerance=TESS)
        except Exception:
            continue
        if not Tr:
            continue
        verts = np.array([(v.X, v.Y, v.Z) for v in V], np.float32)
        faces = np.array(Tr, np.int64)
        parts.append((lbl, verts, faces))
    print(f"[build] {len(parts)} parts", flush=True)
    return parts


def save_cache(parts, path):
    with open(path, "wb") as fh:
        pickle.dump(parts, fh, protocol=pickle.HIGHEST_PROTOCOL)


def load_cache(path):
    with open(path, "rb") as fh:
        return pickle.load(fh)


def smooth_with_crease(tm, deg=35.0):
    """Return a copy of tm with vertices split along sharp (>deg) edges so that
    trimesh's per-vertex normals smooth ONLY within each crease group. This gives
    a CAD-like look: curved surfaces (gear teeth roots, cylinders, fillets,
    rounded knuckles) shade smoothly, while plate/tooth edges stay crisp."""
    import trimesh
    try:
        from scipy.sparse import coo_matrix
        from scipy.sparse.csgraph import connected_components
        faces = tm.faces
        fa = tm.face_adjacency
        ang = tm.face_adjacency_angles
        nf = len(faces)
        m = ang < math.radians(deg)
        r = fa[m, 0]; c = fa[m, 1]
        g = coo_matrix((np.ones(2 * len(r)),
                        (np.concatenate([r, c]), np.concatenate([c, r]))), shape=(nf, nf))
        _, comp = connected_components(g, directed=False)          # comp[f] = smoothing group
        ov = faces.reshape(-1)                                     # original vertex per face-vert
        gid = comp[np.repeat(np.arange(nf), 3)]
        keys = ov.astype(np.int64) * (int(comp.max()) + 1) + gid
        uniq, first, inv = np.unique(keys, return_index=True, return_inverse=True)
        new_faces = inv.reshape(-1, 3).astype(np.int64)
        new_verts = tm.vertices[ov[first]]
        return trimesh.Trimesh(new_verts, new_faces, process=False)
    except Exception:
        return tm


# ------------------------------------------------------------------ scene (per process)
# build_scene() populates these module globals, then frame() uses them.
scene = renderer = cam_node = None
REG = []
IRON_TIP = IRON_NODES = None
CAP_C = {}; CAP_ORDER = []; CENTER = None; GROUND_Y = 0.0
HIDE = np.eye(4); HIDE[:3, 3] = [0, 0, 1e5]
FONT = FONT_S = None
USE_SHADOW = False


def _idcol(i):
    return (np.array([(i * 53 + 40) % 215 + 25,
                      (i * 97 + 30) % 215 + 25,
                      (i * 29 + 70) % 215 + 25]) / 255.0).tolist()


def build_scene(parts):
    """Build the pyrender scene/lights/camera/iron + the offscreen renderer from
    the cached part meshes. Sets the module globals used by frame()."""
    global scene, renderer, cam_node, REG, IRON_TIP, IRON_NODES
    global CAP_C, CAP_ORDER, CENTER, GROUND_Y, FONT, FONT_S
    import trimesh, pyrender
    from PIL import ImageFont

    tms = [(lbl, trimesh.Trimesh(v.astype(np.float64), f, process=False)) for lbl, v, f in parts]
    mins = np.array([t.bounds[0] for _, t in tms]).min(0)
    maxs = np.array([t.bounds[1] for _, t in tms]).max(0)
    CENTER = (mins + maxs) / 2.0
    GROUND_Y = float(mins[1]) - 2.0
    CAP_C = {lbl: ((t.bounds[0] + t.bounds[1]) / 2.0) for lbl, t in tms if lbl.startswith("cap_")}
    CAP_ORDER = [c for c in ("cap_A_L", "cap_A_R", "cap_B_L", "cap_B_R",
                             "cap_C_L", "cap_C_R", "cap_D_L", "cap_D_R") if c in CAP_C]

    scene = pyrender.Scene(bg_color=(*BG, 1.0), ambient_light=(0.50, 0.50, 0.53))
    REG = []

    def add_mesh(tm, rgba, kind, lbl="", ph=None, uv=(0, 0, 1), dist=0.0):
        matte = kind in ("ground", "shadow")
        blend = rgba[3] < 0.999
        cen = (tm.bounds[0] + tm.bounds[1]) / 2.0
        mat = pyrender.MetallicRoughnessMaterial(
            baseColorFactor=list(rgba),
            metallicFactor=0.0 if matte else (0.55 if kind == "iron" else 0.12),
            roughnessFactor=1.0 if matte else (0.32 if kind == "iron" else 0.46),
            emissiveFactor=[0, 0, 0], alphaMode="BLEND" if blend else "OPAQUE")
        if matte:
            pm = pyrender.Mesh.from_trimesh(tm, material=mat, smooth=False)
        else:
            pm = pyrender.Mesh.from_trimesh(smooth_with_crease(tm), material=mat, smooth=True)
        node = pyrender.Node(mesh=pm, matrix=np.eye(4)); scene.add_node(node)
        REG.append(dict(node=node, prims=pm.primitives, rgba=list(rgba),
                        idcol=_idcol(len(REG)), kind=kind, lbl=lbl, cen=cen,
                        ph=ph, uv=np.array(uv, float), dist=float(dist), shell=False))
        return REG[-1]

    # ground + painted contact shadow
    ground = trimesh.creation.box(extents=[680, 2, 680]); ground.apply_translation([0, GROUND_Y, 40])
    G = add_mesh(ground, GROUND_RGBA, "ground")
    shadow = trimesh.creation.cylinder(radius=1.0, height=1.0, sections=56)
    shadow.apply_scale([60, 0.5, 42]); shadow.apply_translation([0, GROUND_Y + 1.3, 8])
    SH = add_mesh(shadow, (0.52, 0.55, 0.60, 1.0), "shadow"); SH["idcol"] = G["idcol"]

    # only the enclosure (body) is GHOSTED so you can watch the mechanism go in;
    # the snap-on front cover is left SOLID (it's the lid that closes it up).
    SHELL_ALPHA = {"enclosure": 0.30}
    for lbl, tm in tms:
        ph, uv, dist = spec(lbl)
        rgba = list(pal(lbl))
        if lbl in SHELL_ALPHA:
            rgba[3] = SHELL_ALPHA[lbl]
        r = add_mesh(tm, rgba, "part", lbl=lbl, ph=ph, uv=uv, dist=dist)
        r["shell"] = lbl in SHELL_ALPHA

    # soldering iron, pointing +Z
    _tip = trimesh.creation.cone(radius=2.4, height=9, sections=28); _tip.apply_translation([0, 0, -9])
    _shaft = trimesh.creation.cylinder(radius=2.0, height=34, sections=28); _shaft.apply_translation([0, 0, -26])
    _handle = trimesh.creation.cylinder(radius=3.3, height=20, sections=28); _handle.apply_translation([0, 0, -53])
    IRON_TIP = add_mesh(_tip, IRON_STEEL, "iron")
    _sh = add_mesh(_shaft, IRON_STEEL, "iron"); _hd = add_mesh(_handle, IRON_HANDLE, "iron")
    IRON_NODES = [IRON_TIP, _sh, _hd]

    cam = pyrender.PerspectiveCamera(yfov=math.radians(34), aspectRatio=W / H)
    cam_node = scene.add(cam, pose=np.eye(4))
    # directional key + fills + a soft down-fill to lift undersides (no distance
    # falloff -> no ground hotspot). Even, bright studio-ish lighting.
    for off, inten in (((0.5, 1.1, 0.85), 3.1), ((-1.3, 0.7, 0.6), 2.0),
                       ((0.4, -0.5, -1.2), 1.3), ((-0.3, -1.0, 0.25), 0.85)):
        d = np.array(off, float)
        scene.add(pyrender.DirectionalLight(color=[1, 1, 1], intensity=inten),
                  pose=look_pose(CENTER + d / np.linalg.norm(d) * 400, CENTER))
    renderer = pyrender.OffscreenRenderer(W, H)

    for fp in ("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
               "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
               "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if os.path.exists(fp):
            FONT = ImageFont.truetype(fp, 40 * SS); FONT_S = ImageFont.truetype(fp, 26 * SS); break
    if FONT is None:
        try:
            import matplotlib
            mp = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data/fonts/ttf/DejaVuSans-Bold.ttf")
            FONT = ImageFont.truetype(mp, 40 * SS); FONT_S = ImageFont.truetype(mp, 26 * SS)
        except Exception:
            FONT = ImageFont.load_default(); FONT_S = FONT


# ------------------------------------------------------------------ iron + caps
def iron_pose(f):
    m0, m1 = MELT; n = len(CAP_ORDER)
    if not (m0 - 6 <= f <= m1 + 6) or n == 0:
        return None, 0.0
    seg = (m1 - m0) / n
    k = min(n - 1, max(0, int((f - m0) / seg)))
    frac = (f - m0 - k * seg) / max(1e-6, seg)
    cur = CAP_C[CAP_ORDER[k]]
    prev = CAP_C[CAP_ORDER[k - 1]] if k > 0 else cur + np.array([0, -10, -40.])
    w = smooth(min(1, frac * 1.6))
    p = cur * w + prev * (1 - w)
    dab = math.sin(min(1.0, frac) * math.pi)
    approach = 16 * (1 - dab)
    pos = np.array([p[0], p[1], p[2] - 2 - approach])
    M = np.eye(4); M[:3, 3] = pos
    glow = 0.5 + 0.5 * dab
    if f < m0:
        glow *= smooth((f - (m0 - 6)) / 6)
    return M, glow


def cap_progress(lbl, f):
    m0, m1 = MELT; n = len(CAP_ORDER)
    if lbl not in CAP_ORDER or f < m0:
        return 0.0, 0.0
    i = CAP_ORDER.index(lbl); seg = (m1 - m0) / n
    ts = m0 + i * seg; te = ts + seg * 1.5
    pr = smooth((f - ts) / max(1e-6, (te - ts)))
    glow = math.sin(min(1.0, max(0.0, (f - ts) / max(1e-6, te - ts))) * math.pi)
    return pr, glow


# ------------------------------------------------------------------ outlines + render
def _id_edges(idimg):
    idint = (idimg[..., 0].astype(np.int64) * 65536 +
             idimg[..., 1].astype(np.int64) * 256 + idimg[..., 2].astype(np.int64))
    e = np.zeros(idint.shape, bool)
    for sh in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        e |= idint != np.roll(idint, sh, (0, 1))
    return e


def edges_from_passes(color, idA, idB, depthB):
    # idA = shells opaque (outer silhouette); idB = shells hidden (inner mechanism)
    edge = _id_edges(idA) | _id_edges(idB)
    valid = depthB > 0
    dmax = depthB[valid].max() if valid.any() else 1.0
    dn = np.where(valid, depthB, dmax)
    gx = np.abs(dn - np.roll(dn, 1, 1)); gy = np.abs(dn - np.roll(dn, 1, 0))
    edge |= ((gx + gy) > 0.012 * dmax) & valid
    edge[0, :] = edge[-1, :] = edge[:, 0] = edge[:, -1] = False
    out = color.astype(np.float32).copy()
    out[edge] = out[edge] * 0.12 + np.array([26, 28, 34], np.float32) * 0.88
    return np.clip(out, 0, 255).astype(np.uint8)


def render_passes():
    import pyrender
    color, _ = renderer.render(scene, flags=pyrender.RenderFlags.NONE)   # lit, shells ghosted
    snap = []
    for r in REG:
        for pm in r["prims"]:
            m = pm.material
            snap.append((m, list(m.baseColorFactor), list(m.emissiveFactor), m.alphaMode))
            m.baseColorFactor = [*r["idcol"], 1.0]; m.emissiveFactor = [0, 0, 0]; m.alphaMode = "OPAQUE"
    old_bg = scene.bg_color.copy(); scene.bg_color = np.array([0, 0, 0, 1.0])
    idA, _ = renderer.render(scene, flags=pyrender.RenderFlags.FLAT)      # shells opaque
    shells = [(r["node"], r["node"].matrix.copy()) for r in REG if r.get("shell")]
    for node, _m in shells:
        scene.set_pose(node, HIDE)
    idB, depthB = renderer.render(scene, flags=pyrender.RenderFlags.FLAT)  # shells hidden
    for node, m in shells:
        scene.set_pose(node, m)
    scene.bg_color = old_bg
    for m, b, e, a in snap:
        m.baseColorFactor = b; m.emissiveFactor = e; m.alphaMode = a
    return color[..., :3], idA[..., :3], idB[..., :3], depthB


def overlay(arr, f):
    from PIL import Image, ImageDraw
    im = Image.fromarray(arr).convert("RGB"); d = ImageDraw.Draw(im)
    d.text((40 * SS, 26 * SS), "Underwater gripper — assembly", font=FONT_S, fill=(64, 68, 78))
    txt = caption_for(f); melt = MELT[0] <= f < MELT[1] + 6
    col = (196, 84, 16) if melt else (34, 38, 48)
    d.text((40 * SS + 2, H - 70 * SS + 2), txt, font=FONT, fill=(235, 237, 240))
    d.text((40 * SS, H - 70 * SS), txt, font=FONT, fill=col)
    p = f / (NFRAMES - 1)
    d.rectangle([40 * SS, H - 14 * SS, W - 40 * SS, H - 8 * SS], fill=(206, 210, 216))
    d.rectangle([40 * SS, H - 14 * SS, 40 * SS + int((W - 80 * SS) * p), H - 8 * SS], fill=(86, 116, 198))
    return np.array(im)


def frame(f):
    from PIL import Image
    eye, tgt = cam_at(f); scene.set_pose(cam_node, look_pose(eye, tgt))
    M_iron, iglow = iron_pose(f)
    for r in IRON_NODES:
        scene.set_pose(r["node"], HIDE if M_iron is None else M_iron)
    if M_iron is not None:
        IRON_TIP["prims"][0].material.emissiveFactor = [1.0 * iglow, 0.45 * iglow, 0.10 * iglow]
    for r in REG:
        if r["kind"] != "part":
            continue
        lbl, node, ph, uv, dist, cen = r["lbl"], r["node"], r["ph"], r["uv"], r["dist"], r["cen"]
        t0, t1 = PHASE[ph]
        if f < t0:
            scene.set_pose(node, HIDE); continue
        s = smooth((f - t0) / max(1, (t1 - t0)))
        M = np.eye(4); M[:3, 3] = uv * dist * (1.0 - s)
        if lbl.startswith("cap_"):
            r["prims"][0].material.baseColorFactor = list(r["rgba"])
            r["prims"][0].material.emissiveFactor = [0, 0, 0]
            pr, glow = cap_progress(lbl, f)
            if pr > 0:
                sz = 1.0 - 0.55 * pr; sxy = 1.0 + 0.5 * pr
                S = np.diag([sxy, sxy, sz, 1.0])
                T1 = np.eye(4); T1[:3, 3] = cen; T0 = np.eye(4); T0[:3, 3] = -cen
                M = M @ T1 @ S @ T0
                r["prims"][0].material.emissiveFactor = [0.95 * glow, 0.4 * glow, 0.06 * glow]
        scene.set_pose(node, M)
    color, idA, idB, depthB = render_passes()
    out = overlay(edges_from_passes(color, idA, idB, depthB), f)
    if SS != 1:
        out = np.array(Image.fromarray(out).resize((OUTW, OUTH), Image.LANCZOS))
    return out


def render_range(a, b, outdir):
    import imageio.v2 as imageio
    os.makedirs(outdir, exist_ok=True)
    for f in range(a, b):
        imageio.imwrite(os.path.join(outdir, f"f_{f:04d}.png"), frame(f))
        if (f - a) % 10 == 0:
            print(f"  [{a}:{b}] frame {f}", flush=True)


# ------------------------------------------------------------------ orchestration
def _split(n, k):
    base, rem, s, out = n // k, n % k, 0, []
    for i in range(k):
        cnt = base + (1 if i < rem else 0)
        if cnt:
            out.append((s, s + cnt)); s += cnt
    return out


def encode(outdir):
    import subprocess
    out = os.path.join(ROOT, "renders")
    mp4 = os.path.join(out, "gripper_assembly.mp4"); gif = os.path.join(out, "gripper_assembly.gif")
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{outdir}/f_%04d.png",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16",
                    "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", mp4], check=True, capture_output=True)
    print("  wrote", mp4, flush=True)
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{outdir}/f_%04d.png",
                    "-vf", "fps=18,scale=860:-1:flags=lanczos,split[a][b];"
                           "[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=4",
                    "-loop", "0", gif], check=True, capture_output=True)
    print("  wrote", gif, flush=True)


def orchestrate(workers):
    import tempfile, shutil, subprocess
    fdir = tempfile.mkdtemp(prefix="asmvid_")
    cache = os.path.join(fdir, "parts.pkl")
    parts = build_parts_from_model()
    save_cache(parts, cache)
    ranges = _split(NFRAMES, workers)
    if workers == 1:
        print(f"[render] {NFRAMES} frames @ {W}x{H} (SS{SS}) single process", flush=True)
        build_scene(parts); render_range(0, NFRAMES, fdir)
    else:
        print(f"[render] {NFRAMES} frames @ {W}x{H} (SS{SS}) across {len(ranges)} workers", flush=True)
        env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                   MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1", PYOPENGL_PLATFORM="egl")
        procs = []
        for (a, b) in ranges:
            p = subprocess.Popen([sys.executable, os.path.abspath(__file__),
                                  "--range", f"{a}:{b}", "--cache", cache, "--outdir", fdir],
                                 env=env)
            procs.append((p, a, b))
        fail = False
        for p, a, b in procs:
            rc = p.wait()
            if rc != 0:
                print(f"  WORKER FAILED range {a}:{b} rc={rc}", flush=True); fail = True
        if fail:
            print("ASSEMBLY_VIDEO_FAILED", flush=True); shutil.rmtree(fdir, ignore_errors=True); return
    have = len([f for f in os.listdir(fdir) if f.startswith("f_") and f.endswith(".png")])
    if have != NFRAMES:
        print(f"  EXPECTED {NFRAMES} frames, found {have} -- aborting encode", flush=True)
        print("ASSEMBLY_VIDEO_FAILED", flush=True); shutil.rmtree(fdir, ignore_errors=True); return
    encode(fdir)
    shutil.rmtree(fdir, ignore_errors=True)
    print("ASSEMBLY_VIDEO_DONE", flush=True)


def main():
    global USE_SHADOW
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", default="", help="comma list of frames -> /tmp (tuning)")
    ap.add_argument("--workers", type=int, default=0, help="0 = auto (all cores, capped)")
    ap.add_argument("--range", default="", help="(worker) A:B frame range")
    ap.add_argument("--cache", default="", help="(worker) cached parts.pkl")
    ap.add_argument("--outdir", default="", help="(worker) PNG output dir")
    ap.add_argument("--shadow", action="store_true", help="(broken under headless EGL)")
    a = ap.parse_args()
    USE_SHADOW = a.shadow

    if a.range:                       # worker mode
        x, y = a.range.split(":")
        parts = load_cache(a.cache) if a.cache else build_parts_from_model()
        build_scene(parts)
        render_range(int(x), int(y), a.outdir)
        if renderer is not None:
            renderer.delete()
        return

    if a.frame:                       # single-frame tuning
        import imageio.v2 as imageio
        build_scene(build_parts_from_model())
        for fs in a.frame.split(","):
            fn = int(fs); p = f"/tmp/asm_f{fn:03d}.png"; imageio.imwrite(p, frame(fn))
            print("wrote", p, flush=True)
        renderer.delete(); return

    workers = a.workers if a.workers > 0 else max(1, min(os.cpu_count() or 4, 12))
    orchestrate(workers)


if __name__ == "__main__":
    main()

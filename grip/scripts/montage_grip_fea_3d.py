"""3D FEA of every grip-texture family — the real pattern AND its stress in one array.

For each swept family's champion geometry this runs a genuine 3D voxel finite-element
solve on the actual micro-relief: a brick (hex) mesh of the textured patch, base
clamped, a rigid object pressing + shearing across the post tops (normal pressure +
tangential traction). It then renders each pattern's deformed surface coloured by
von Mises stress — so you see the pattern's shape AND where it is stressed, in 3D,
for all of them at once. Shared stress scale; shipped crosshatch highlighted.

Common grip load (fair across geometries): p = 0.20 MPa normal + μ = 1.0 shear.
Linear-elastic small-strain voxel FEM, 8-node trilinear bricks, scipy sparse direct.

Usage:  python grip/scripts/montage_grip_fea_3d.py [out.png] [--anim]
"""
import os, sys, json, time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from texture_relief import relief

ITER = os.path.join(HERE, "..", "iterations")
ANIM = "--anim" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT_PNG = args[0] if args else os.path.join(HERE, "..", "..", "renders", "grip_fea_3d_array.png")
OUT_GIF = OUT_PNG.rsplit(".", 1)[0] + ".gif"

E, NU = 9.8, 0.42         # Bambu TPU 95A HF, ISO 527 in-plane
P_NORM, MU = 0.20, 1.0    # common grip load
L, BASE_H = 5.0, 0.7      # patch side + substrate slab (mm)
A = 0.15                  # voxel size (mm)

FAMILIES = [
    ("crosshatch_champ.json", "crosshatch",      "crosshatch",           False),
    ("conc_champ.json",       "concentric",      "concentric",           False),
    ("hexpad_champ.json",     "hexpad",          "hexpad",               False),
    ("chevron_champ.json",    "chevron",         "chevron",              False),
    ("dimple_champ.json",     "dimple",          "dimple",               False),
    ("ridge_champ.json",      "ridge",           "ridge",                False),
    ("hier_champ.json",       "hierarchical",    "hierarchical",         False),
    ("SHIP_crosshatch.json",  "crosshatch_ship", "crosshatch (shipped)", True),
]
NROWS, NCOLS = 2, 4

# --- voxel FEM kernel -------------------------------------------------------
LN = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]], float)
# exposed-face local node quads (CCW) per direction
FACE = {"-x":[0,4,7,3], "+x":[1,2,6,5], "-y":[0,1,5,4],
        "+y":[3,7,6,2], "-z":[0,3,2,1], "+z":[4,5,6,7]}

def D3(E, nu):
    lam = E*nu/((1+nu)*(1-2*nu)); mu = E/(2*(1+nu))
    D = np.zeros((6,6)); D[:3,:3]=lam
    D[0,0]=D[1,1]=D[2,2]=lam+2*mu; D[3,3]=D[4,4]=D[5,5]=mu
    return D

def _B(xi, et, ze, a):
    dN=np.zeros((3,8))
    for n,(Xn,Yn,Zn) in enumerate(LN):
        sx,sy,sz=2*Xn-1,2*Yn-1,2*Zn-1
        dN[0,n]=0.125*sx*(1+sy*et)*(1+sz*ze)
        dN[1,n]=0.125*(1+sx*xi)*sy*(1+sz*ze)
        dN[2,n]=0.125*(1+sx*xi)*(1+sy*et)*sz
    J=dN@(LN*a); dNx=np.linalg.solve(J,dN)
    B=np.zeros((6,24))
    B[0,0::3]=dNx[0]; B[1,1::3]=dNx[1]; B[2,2::3]=dNx[2]
    B[3,0::3]=dNx[1]; B[3,1::3]=dNx[0]
    B[4,1::3]=dNx[2]; B[4,2::3]=dNx[1]
    B[5,0::3]=dNx[2]; B[5,2::3]=dNx[0]
    return B, abs(np.linalg.det(J))

def hex_ke(a, D):
    ke=np.zeros((24,24)); g=1/np.sqrt(3)
    for xi in (-g,g):
        for et in (-g,g):
            for ze in (-g,g):
                B,dJ=_B(xi,et,ze,a); ke+=B.T@D@B*dJ
    return ke

def solve_texture(fam, params, a=A):
    """3D voxel FEA. Returns deformed-render data + von Mises per cell."""
    D = D3(E, NU); ke = hex_ke(a, D); Bc,_ = _B(0,0,0,a)
    nx = int(round(L/a)); ny = nx
    xs = (np.arange(nx)+0.5)*a
    Xc, Yc = np.meshgrid(xs, xs)                 # [yi,xi]
    Z, h = relief(fam, params, Xc, Yc, L)
    Htot = (BASE_H + Z).T                         # [xi,yi]
    nz = int(np.ceil((BASE_H + h)/a))
    zc = (np.arange(nz)+0.5)*a
    solid = zc[None,None,:] <= Htot[:,:,None]    # [xi,yi,k]
    ii,jj,kk = np.where(solid)
    nxp,nyp = nx+1, ny+1
    def NID(i,j,k): return i + nxp*(j + nyp*k)
    en = np.stack([NID(ii,jj,kk),NID(ii+1,jj,kk),NID(ii+1,jj+1,kk),NID(ii,jj+1,kk),
                   NID(ii,jj,kk+1),NID(ii+1,jj,kk+1),NID(ii+1,jj+1,kk+1),NID(ii,jj+1,kk+1)],axis=1)
    edof = np.empty((len(en),24),int)
    edof[:,0::3]=3*en; edof[:,1::3]=3*en+1; edof[:,2::3]=3*en+2
    nn = nxp*nyp*(nz+1); ndof = 3*nn
    rows=np.repeat(edof,24,axis=1).ravel(); cols=np.tile(edof,(1,24)).ravel()
    K=sp.csr_matrix((np.tile(ke.ravel(),len(en)),(rows,cols)),shape=(ndof,ndof))
    ref=np.unique(en)
    bi,bj=np.meshgrid(np.arange(nxp),np.arange(nyp))
    base_nodes=(bi+nxp*bj).ravel()
    orph=np.setdiff1d(np.arange(nn),ref)
    fixed=np.unique(np.concatenate([3*base_nodes,3*base_nodes+1,3*base_nodes+2,
                                    3*orph,3*orph+1,3*orph+2]))
    free=np.setdiff1d(np.arange(ndof),fixed)
    # load: rigid object on the exposed top (+z) faces -> normal + shear
    above=np.zeros_like(solid); above[:,:,:-1]=solid[:,:,1:]
    ti,tj,tk=np.where(solid & ~above)
    tn=np.stack([NID(ti,tj,tk+1),NID(ti+1,tj,tk+1),NID(ti+1,tj+1,tk+1),NID(ti,tj+1,tk+1)],axis=1)
    F=np.zeros(ndof); tau=MU*P_NORM; fa=a*a/4
    np.add.at(F,3*tn.ravel(),tau*fa); np.add.at(F,3*tn.ravel()+2,-P_NORM*fa)
    U=np.zeros(ndof)
    U[free]=spla.spsolve(K[free][:,free].tocsc(),F[free])
    # von Mises per cell (centre)
    ue=U[edof]                                    # (Ncell,24)
    eps=ue@Bc.T                                   # (Ncell,6)
    sig=eps@D.T
    sxx,syy,szz,sxy,syz,szx=sig.T
    vm=np.sqrt(0.5*((sxx-syy)**2+(syy-szz)**2+(szz-sxx)**2)+3*(sxy**2+syz**2+szx**2))
    # exposed faces (any direction) for rendering
    pad=np.zeros((nx+2,ny+2,nz+2),bool); pad[1:-1,1:-1,1:-1]=solid
    cidx=np.stack([ii,jj,kk],1)
    faces=[]; fcell=[]
    shift={"-x":(-1,0,0),"+x":(1,0,0),"-y":(0,-1,0),"+y":(0,1,0),"-z":(0,0,-1),"+z":(0,0,1)}
    for dname,(di,dj,dk) in shift.items():
        nb=pad[1+ii+di,1+jj+dj,1+kk+dk]
        exp=~nb
        loc=FACE[dname]
        faces.append(en[exp][:,loc]); fcell.append(np.where(exp)[0])
    fnodes=np.concatenate(faces); fcell=np.concatenate(fcell)
    coords=np.zeros((nn,3))                        # rest node coords
    alln=np.arange(nn); ai=alln%nxp; aj=(alln//nxp)%nyp; ak=alln//(nxp*nyp)
    coords[:,0]=ai*a; coords[:,1]=aj*a; coords[:,2]=ak*a
    return dict(coords=coords, U=U.reshape(-1,3), fnodes=fnodes, fvm=vm[fcell],
                vm=vm, h=h, root_vm=float(np.percentile(vm,99.5)))

# --- solve all --------------------------------------------------------------
print(f"3D voxel FEA per family (a={A} mm)...")
panels=[]
for fn,fam,title,ship in FAMILIES:
    d=json.load(open(os.path.join(ITER,fn))); t=time.time()
    S=solve_texture(fam,d["params"])
    S.update(title=title,ship=ship,score=d.get("score"),
             label=d["label"].replace("xhatch","crosshatch"))
    panels.append(S)
    print(f"  + {title:22s} faces={len(S['fnodes']):6d}  peak vM={S['vm'].max():.2f} "
          f"root~{S['root_vm']:.2f} MPa  ({time.time()-t:.1f}s)")

VMAX=float(np.percentile(np.concatenate([p["vm"] for p in panels]),98))
gmax=max(np.abs(p["U"]).max() for p in panels)
DEF=0.45/gmax                                     # global max disp -> 0.45 mm on screen
print(f"shared vmax={VMAX:.2f} MPa   true max disp {gmax:.2f} mm  (shown ×{DEF:.2f})")

# --- render -----------------------------------------------------------------
BG,C_TITLE,C_HDR,C_CAP="#f6f6f8","#141414","#15506e","#666"
C_LABEL,C_GOLD,C_GOLDBR,C_GOLDBG="#222","#b8860b","#e6a700","#fff5d6"
LIGHT=np.array([0.4,0.5,0.75]); LIGHT=LIGHT/np.linalg.norm(LIGHT)
cmap=plt.cm.turbo          # blue(low)->red(high): classic, legible FEA stress field
ZMAX=max(BASE_H+p["h"] for p in panels)

fig=plt.figure(figsize=(15.4,8.7),dpi=100,facecolor=BG)
fig.subplots_adjust(left=0.004,right=0.996,top=0.85,bottom=0.06,wspace=0.02,hspace=0.10)

def build(ax,S,s):
    """Draw one panel at load fraction s in [0,1]: deform ×(DEF·s), colour by s·vM."""
    P=S["coords"]+DEF*s*S["U"]
    verts=P[S["fnodes"]]                            # (Nf,4,3)
    base=cmap(np.clip(s*S["fvm"]/VMAX,0,1))[:,:3]
    # fake lambert shading from face normals for 3D form
    n=np.cross(verts[:,1]-verts[:,0],verts[:,2]-verts[:,0])
    ln=np.linalg.norm(n,axis=1,keepdims=True); ln[ln==0]=1; n=n/ln
    sh=0.70+0.30*np.clip(n@LIGHT,0,1)[:,None]
    pc=Poly3DCollection(verts,facecolors=np.clip(base*sh,0,1),
                        edgecolors=(0,0,0,0.06),linewidths=0.05)
    ax.add_collection3d(pc)
    ax.set_xlim(0,L); ax.set_ylim(0,L); ax.set_zlim(0,ZMAX)
    ax.set_box_aspect((1,1,0.42)); ax.set_axis_off()
    ax.view_init(elev=42,azim=-62)

def set_panel_title(ax,S):
    win=S["ship"]
    ttl=("★ SHIPPED — " if win else "")+S["title"]
    ax.set_title(f"{ttl}\n{S['label']} · score {S['score']:.3f}\npeak root ≈ {S['root_vm']:.2f} MPa",
                 fontsize=8.8,color=(C_GOLD if win else C_LABEL),
                 fontweight=("bold" if win else "normal"),pad=-4,linespacing=1.25)

axes=[]
for k,S in enumerate(panels):
    ax=fig.add_subplot(NROWS,NCOLS,k+1,projection="3d")
    build(ax,S,1.0)
    if S["ship"]:
        bb=ax.get_position()
        fig.add_artist(Rectangle((bb.x0-0.004,bb.y0-0.005),bb.width+0.008,bb.height+0.055,
                       transform=fig.transFigure,facecolor=C_GOLDBG,edgecolor=C_GOLDBR,
                       lw=2.6,zorder=-10,clip_on=False))
    set_panel_title(ax,S)
    axes.append((ax,S))

sm=plt.cm.ScalarMappable(cmap=cmap,norm=plt.Normalize(0,VMAX))
cax=fig.add_axes([0.30,0.055,0.40,0.016])
cb=fig.colorbar(sm,cax=cax,orientation="horizontal")
cb.set_label("von Mises stress (MPa) — shared scale",color=C_CAP,fontsize=9)
cb.ax.tick_params(colors=C_CAP,labelsize=8); cb.outline.set_edgecolor("#999")

fig.text(0.5,0.965,"Grip textures in 3D — real pattern + its FEA stress",
         ha="center",va="center",fontsize=20,color=C_TITLE,fontweight="bold")
fig.text(0.5,0.925,
         f"genuine 3D voxel finite-element solve on each champion relief · {L:.0f}×{L:.0f} mm "
         f"patch to scale · object presses + shears the tops (p=0.20 MPa, μ=1.0) · von Mises, "
         f"deformation ×{DEF:.1f}",
         ha="center",va="center",fontsize=10.5,color=C_HDR)
fig.text(0.5,0.018,"Bambu TPU 95A HF  E≈9.8 MPa, σ≈27.3 MPa, ν=0.42 · 8-node brick FEM, "
         "base clamped · stress concentrates at the post roots (the durability limit)",
         ha="center",va="center",fontsize=8.5,color=C_CAP)

fig.savefig(OUT_PNG,dpi=185,facecolor=BG)
print(f"WROTE  {OUT_PNG}")

if ANIM:
    from matplotlib.animation import FuncAnimation, PillowWriter
    ramp=list(np.linspace(0,1,16))+[1.0]*5
    sub=fig.text(0.5,0.895,"",ha="center",va="center",fontsize=10,color=C_CAP)
    def upd(kf):
        s=ramp[kf]
        for ax,S in axes:
            ax.clear(); build(ax,S,s); set_panel_title(ax,S)
        sub.set_text(f"grip load {s*100:3.0f}%  —  stress builds at the post roots "
                     f"as the object presses + shears")
    print(f"Rendering {len(ramp)}-frame load ramp...")
    an=FuncAnimation(fig,upd,frames=len(ramp),blit=False)
    an.save(OUT_GIF,writer=PillowWriter(fps=8),savefig_kwargs={"facecolor":BG})
    print(f"WROTE  {OUT_GIF}  ({os.path.getsize(OUT_GIF)/1e6:.1f} MB)")
plt.close(fig)

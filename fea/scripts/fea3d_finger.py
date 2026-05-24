"""Full 3D corotational FEA of the Fin Ray finger wrapping a rigid neck cylinder.

Genuine 3D finite-element solve (not the bundled 2D plane-strain):
  * Geometry: the real finger cross-section (fea/finray_morph.npz: 1655 nodes,
    2791 tris) extruded over the 10 mm finger thickness into linear tetrahedra.
  * Constitutive: corotational linear elasticity (polar-decomposition "warped
    stiffness"), which is accurate for this large-rotation / small-strain regime
    (TPU 95A, E=40 MPa, nu=0.45 from the npz). Handles the big bending rotations
    of the wrap correctly while keeping a symmetric tangent -> robust Newton.
  * Contact: penalty contact against an analytic rigid cylinder = the amphora
    NECK (radius 22 mm) at its real grasp position relative to the finger. The
    neck is displacement-stepped into the toothed contact face; the Fin Ray truss
    converts the push into the tip curling AROUND the neck (emergent, physical).
  * Drive: base (mount) clamped; neck pressed in over load steps. Grip force =
    integrated contact reaction. Frictionless (noted).

Outputs (fea3d/): per-step deformed 3D field + von Mises (npz), force/wrap curves,
stats json. A separate script renders the stress field and maps the wrap onto the
Blender finger meshes.
"""
import numpy as np, json, os, time
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

BUNDLE = r"C:\Users\andre\gripper_render\render_bundle"
OUT = os.path.join(BUNDLE, "fea3d")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- material
E = 40.0          # MPa  (N/mm^2)  TPU ~95A, from npz
NU = 0.45
LAM = E*NU/((1+NU)*(1-2*NU))
MU  = E/(2*(1+NU))

def Dmat():
    D = np.zeros((6,6))
    D[:3,:3] = LAM
    D[0,0]=D[1,1]=D[2,2]=LAM+2*MU
    D[3,3]=D[4,4]=D[5,5]=MU
    return D
D6 = Dmat()

# ---------------------------------------------------------------- mesh build
def build_mesh(nlayers=3, z0=13.0, z1=23.0):
    z = np.load(os.path.join(BUNDLE,"fea","finray_morph.npz"))
    rest2d = z['rest'].T.astype(np.float64)      # (N2,2)  mm
    tris   = z['tris'].astype(np.int64)          # (M,3)
    N2 = rest2d.shape[0]
    zs = np.linspace(z0, z1, nlayers+1)
    # node planes
    nodes = np.zeros((N2*(nlayers+1), 3))
    for k,zc in enumerate(zs):
        nodes[k*N2:(k+1)*N2,0:2] = rest2d
        nodes[k*N2:(k+1)*N2,2]   = zc
    # prisms -> 3 tets each (consistent split)
    tets=[]
    for k in range(nlayers):
        b = k*N2; t = (k+1)*N2
        for (a,bb,c) in tris:
            # bottom a,bb,c  top a',bb',c'
            a0,b0,c0 = b+a, b+bb, b+c
            a1,b1,c1 = t+a, t+bb, t+c
            tets.append((a0,b0,c0,a1))
            tets.append((b0,c0,a1,b1))
            tets.append((c0,a1,b1,c1))
    tets=np.array(tets,dtype=np.int64)
    # ensure positive volume (swap two nodes if negative)
    X = nodes[tets]                              # (Ntet,4,3)
    Jm = np.stack([X[:,1]-X[:,0], X[:,2]-X[:,0], X[:,3]-X[:,0]],axis=2)  # (Ntet,3,3)
    vol6 = np.linalg.det(Jm)
    neg = vol6<0
    tets[neg] = tets[neg][:,[0,2,1,3]]
    return nodes, tets, N2, nlayers

# ---------------------------------------------------------------- precompute
def precompute(nodes, tets):
    X = nodes[tets]                               # (Ntet,4,3)
    e1=X[:,1]-X[:,0]; e2=X[:,2]-X[:,0]; e3=X[:,3]-X[:,0]
    Jm = np.stack([e1,e2,e3],axis=2)              # cols = edges
    invJm = np.linalg.inv(Jm)
    V = np.abs(np.linalg.det(Jm))/6.0
    # shape gradients dN/dx : (Ntet,4,3)
    dNref = np.array([[-1,-1,-1],[1,0,0],[0,1,0],[0,0,1]],dtype=np.float64)  # (4,3)
    dNdx = np.einsum('ij,njk->nik', dNref, invJm)  # (Ntet,4,3)
    Ntet = tets.shape[0]
    # B (Ntet,6,12)
    B = np.zeros((Ntet,6,12))
    for i in range(4):
        gx=dNdx[:,i,0]; gy=dNdx[:,i,1]; gz=dNdx[:,i,2]
        c=3*i
        B[:,0,c]=gx; B[:,1,c+1]=gy; B[:,2,c+2]=gz
        B[:,3,c]=gy; B[:,3,c+1]=gx
        B[:,4,c+1]=gz; B[:,4,c+2]=gy
        B[:,5,c]=gz;  B[:,5,c+2]=gx
    Ke0 = np.einsum('nki,kl,nlj->nij', B, D6, B) * V[:,None,None]   # (Ntet,12,12)
    edof = (tets[:,:,None]*3 + np.arange(3)[None,None,:]).reshape(Ntet,12)  # (Ntet,12)
    I = np.repeat(edof,12,axis=1).reshape(-1)
    Jc= np.tile(edof,(1,12)).reshape(-1)
    return dict(X=X, Xvec=X.reshape(Ntet,12), invJm=invJm, V=V, B=B, D=D6,
                Ke0=Ke0, edof=edof, I=I, J=Jc, Ntet=Ntet)

def apply_blockR(R, Vvec):
    # R:(Ntet,3,3)  Vvec:(Ntet,12) -> (Ntet,12), node-wise R@v
    Vr = Vvec.reshape(-1,4,3)
    return np.einsum('nij,nkj->nki', R, Vr).reshape(-1,12)

def polar_R(F):
    U,S,Vt = np.linalg.svd(F)
    R = np.einsum('nij,njk->nik', U, Vt)
    det = np.linalg.det(R)
    flip = det<0
    if np.any(flip):
        U2=U.copy(); U2[flip,:,2]*=-1
        R[flip]=np.einsum('nij,njk->nik', U2[flip], Vt[flip])
    return R, S

# ---------------------------------------------------------------- solve
def solve(nlayers=3, nsteps=24, press_max=15.0, kpen=1500.0,
          yc=88.0, x_gap=0.5, R_neck=22.0, clamp_y=32.5, newton_tol=2e-3,
          max_newton=14, nu_override=None, verbose=True):
    global LAM, MU, D6, NU
    if nu_override is not None:
        NU=nu_override
        LAM=E*NU/((1+NU)*(1-2*NU)); MU=E/(2*(1+NU)); D6=Dmat()
    nodes, tets, N2, nl = build_mesh(nlayers)
    P = precompute(nodes, tets)
    nn = nodes.shape[0]; ndof=nn*3
    Xrest = nodes.copy()
    u = np.zeros(ndof)
    # contact face start x (near y=yc) to seat the cylinder
    xc0 = (Xrest[:,0].min()) - R_neck - x_gap   # ~ -21.x
    # clamp base nodes
    clamp = Xrest[:,1] < clamp_y
    fixed = np.zeros(ndof,bool)
    for d in range(3): fixed[3*np.where(clamp)[0]+d]=True
    free = ~fixed
    freeidx = np.where(free)[0]

    Ntet=P['Ntet']; Ke0=P['Ke0']; invJm=P['invJm']; edof=P['edof']
    Iidx=P['I']; Jidx=P['J']; Xvec=P['Xvec']

    frames=[]; vms_frames=[]; grip=[]; tipwrap=[]; press_hist=[]
    tip_node = np.argmax(Xrest[:,1])   # global tip (any layer, max y)
    # use a tip near mid-z
    tipcands = np.where(Xrest[:,1] > Xrest[:,1].max()-1.0)[0]
    tip_node = tipcands[np.argmin(np.abs(Xrest[tipcands,2]-18.0))]

    t0=time.time()
    for s in range(1,nsteps+1):
        press = press_max*s/nsteps
        cx = xc0 + press; cy = yc
        # Newton
        for it in range(max_newton):
            x = (Xrest.reshape(-1)+u).reshape(nn,3)
            xe = x[tets]                           # (Ntet,4,3)
            Js = np.stack([xe[:,1]-xe[:,0], xe[:,2]-xe[:,0], xe[:,3]-xe[:,0]],axis=2)
            F = np.einsum('nij,njk->nik', Js, invJm)
            R,Ssv = polar_R(F)
            # corotational internal force
            xev = xe.reshape(Ntet,12)
            RtX = apply_blockR(np.transpose(R,(0,2,1)), xev) - Xvec
            f_loc = np.einsum('nij,nj->ni', Ke0, RtX)
            f_e = apply_blockR(R, f_loc)           # (Ntet,12)
            f_int = np.zeros(ndof); np.add.at(f_int, edof.reshape(-1), f_e.reshape(-1))
            # tangent Ke = Rb Ke0 Rb^T
            Rb = np.zeros((Ntet,12,12))
            for k in range(4): Rb[:,3*k:3*k+3,3*k:3*k+3]=R
            Ke = np.einsum('nij,njk,nlk->nil', Rb, Ke0, Rb)
            # contact (penalty) vs cylinder axis along z at (cx,cy)
            dx = x[:,0]-cx; dy=x[:,1]-cy
            rr = np.sqrt(dx*dx+dy*dy)+1e-9
            pen = R_neck-rr
            inside = pen>0
            f_ext = np.zeros(ndof);
            Kc_diag = np.zeros((nn,3,3))
            if np.any(inside):
                nrm = np.zeros((nn,3)); nrm[:,0]=dx/rr; nrm[:,1]=dy/rr
                fc = (kpen*pen)[:,None]*nrm        # outward push
                fc[~inside]=0
                f_ext[0::3]+=fc[:,0]; f_ext[1::3]+=fc[:,1]; f_ext[2::3]+=fc[:,2]
                # tangent: kpen * n n^T for inside nodes
                nn_out = np.einsum('ni,nj->nij',nrm,nrm)*kpen
                nn_out[~inside]=0
                Kc_diag=nn_out
            # assemble global K
            data=Ke.reshape(-1)
            K=coo_matrix((data,(Iidx,Jidx)),shape=(ndof,ndof)).tocsr()
            # add contact diagonal blocks
            if np.any(inside):
                rows=[]; cols=[]; vals=[]
                ii=np.where(inside)[0]
                for a in range(3):
                    for b in range(3):
                        rows.append(3*ii+a); cols.append(3*ii+b); vals.append(Kc_diag[ii,a,b])
                Kc=coo_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),
                              shape=(ndof,ndof)).tocsr()
                K=K+Kc
            r = f_int - f_ext
            rn=np.linalg.norm(r[freeidx])
            if it>0 and rn<newton_tol*(1+np.linalg.norm(f_ext[freeidx])):
                break
            Kff=K[freeidx][:,freeidx]
            du=spsolve(Kff.tocsc(), -r[freeidx])
            # damped update for robustness on first iters
            relax = 1.0 if it>1 else 0.7
            u[freeidx]+=relax*du
        # record
        x = (Xrest.reshape(-1)+u).reshape(nn,3)
        # von Mises per tet -> nodal
        xe=x[tets]; Js=np.stack([xe[:,1]-xe[:,0],xe[:,2]-xe[:,0],xe[:,3]-xe[:,0]],axis=2)
        F=np.einsum('nij,njk->nik',Js,invJm); R,_=polar_R(F)
        # corotated small strain: eps = sym(R^T F - I)
        RtF=np.einsum('nij,njk->nik',np.transpose(R,(0,2,1)),F)
        eps=0.5*(RtF+np.transpose(RtF,(0,2,1)))-np.eye(3)[None]
        ev=np.stack([eps[:,0,0],eps[:,1,1],eps[:,2,2],
                     2*eps[:,0,1],2*eps[:,1,2],2*eps[:,2,0]],axis=1)
        sig=ev@D6.T   # (Ntet,6) voigt stress
        sxx,syy,szz,sxy,syz,szx=sig.T
        vm=np.sqrt(0.5*((sxx-syy)**2+(syy-szz)**2+(szz-sxx)**2)+3*(sxy**2+syz**2+szx**2))
        # scatter tet vm to nodes (avg)
        nodal=np.zeros(nn); cnt=np.zeros(nn)
        np.add.at(nodal,tets.reshape(-1),np.repeat(vm,4)); np.add.at(cnt,tets.reshape(-1),1)
        nodal/=np.maximum(cnt,1)
        # grip force = total outward contact reaction magnitude (x-dominant)
        dx=x[:,0]-cx; dy=x[:,1]-cy; rr=np.sqrt(dx*dx+dy*dy)+1e-9; pen=R_neck-rr; inside=pen>0
        gf=float(np.sum((kpen*pen[inside])))  # sum of normal penalty force magnitudes
        gfx=float(np.sum((kpen*pen[inside])*(dx[inside]/rr[inside])))
        disp_tip=x[tip_node]-Xrest[tip_node]
        frames.append(x.astype(np.float32))
        vms_frames.append(nodal.astype(np.float32))
        grip.append(abs(gfx)); tipwrap.append(float(np.hypot(disp_tip[0],disp_tip[1])))
        press_hist.append(press)
        if verbose:
            print(f"step {s:2d}/{nsteps} press={press:5.2f}mm  newton_it={it+1} "
                  f"res={rn:.2e}  grip_x={abs(gfx):6.2f}N  vmmax={nodal.max():.2f}MPa "
                  f"tip|d|={np.hypot(disp_tip[0],disp_tip[1]):5.2f}mm  pen={pen[inside].max() if inside.any() else 0:.3f}",flush=True)
    dt=time.time()-t0
    print(f"solved in {dt:.1f}s  Ntet={Ntet} ndof={ndof}")
    np.savez_compressed(os.path.join(OUT,"fea3d_solution.npz"),
        rest=Xrest.astype(np.float32), tets=tets.astype(np.int32),
        frames=np.array(frames), vms=np.array(vms_frames),
        grip=np.array(grip), tipwrap=np.array(tipwrap), press=np.array(press_hist),
        N2=N2, nlayers=nl, yc=yc, R_neck=R_neck, xc0=xc0,
        E=E, nu=NU, clamp_y=clamp_y, kpen=kpen)
    return dict(rest=Xrest,tets=tets,frames=frames,vms=vms_frames,grip=grip,
                tipwrap=tipwrap,press=press_hist,Ntet=Ntet,ndof=ndof,
                yc=yc,R_neck=R_neck,xc0=xc0,N2=N2,nlayers=nl)

if __name__=="__main__":
    import sys
    test = "--test" in sys.argv
    if test:
        solve(nlayers=2, nsteps=6, press_max=10.0, kpen=1200.0)
    else:
        solve(nlayers=3, nsteps=26, press_max=16.0, kpen=1500.0)

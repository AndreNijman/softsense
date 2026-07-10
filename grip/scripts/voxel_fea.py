"""3D voxel finite-element solver for a grip-texture relief patch (shared).

solve_texture(fam, params, ...) builds a brick (hex) mesh of the textured patch
from texture_relief.relief(), clamps the base, presses + shears a rigid object
across the post tops, solves linear elasticity, and returns the deformed exposed
surface + per-cell von Mises for rendering. Pure compute, safe to import.
"""
import os, sys
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from texture_relief import relief

E, NU = 9.8, 0.42           # Bambu TPU 95A HF, ISO 527 in-plane
P_NORM, MU = 0.20, 1.0      # common grip load: normal pressure + shear coeff

LN = np.array([[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]], float)
FACE = {"-x":[0,4,7,3], "+x":[1,2,6,5], "-y":[0,1,5,4],
        "+y":[3,7,6,2], "-z":[0,3,2,1], "+z":[4,5,6,7]}
_SHIFT = {"-x":(-1,0,0),"+x":(1,0,0),"-y":(0,-1,0),"+y":(0,1,0),"-z":(0,0,-1),"+z":(0,0,1)}

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

def solve_texture(fam, params, L=5.0, base_h=0.7, a=0.13):
    D = D3(E, NU); ke = hex_ke(a, D); Bc,_ = _B(0,0,0,a)
    nx = int(round(L/a)); ny = nx
    xs = (np.arange(nx)+0.5)*a
    Xc, Yc = np.meshgrid(xs, xs)
    Z, h = relief(fam, params, Xc, Yc, L)
    Htot = (base_h + Z).T
    nz = int(np.ceil((base_h + h)/a))
    zc = (np.arange(nz)+0.5)*a
    solid = zc[None,None,:] <= Htot[:,:,None]
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
    above=np.zeros_like(solid); above[:,:,:-1]=solid[:,:,1:]
    ti,tj,tk=np.where(solid & ~above)
    tn=np.stack([NID(ti,tj,tk+1),NID(ti+1,tj,tk+1),NID(ti+1,tj+1,tk+1),NID(ti,tj+1,tk+1)],axis=1)
    F=np.zeros(ndof); tau=MU*P_NORM; fa=a*a/4
    np.add.at(F,3*tn.ravel(),tau*fa); np.add.at(F,3*tn.ravel()+2,-P_NORM*fa)
    U=np.zeros(ndof)
    U[free]=spla.spsolve(K[free][:,free].tocsc(),F[free])
    ue=U[edof]; eps=ue@Bc.T; sig=eps@D.T
    sxx,syy,szz,sxy,syz,szx=sig.T
    vm=np.sqrt(0.5*((sxx-syy)**2+(syy-szz)**2+(szz-sxx)**2)+3*(sxy**2+syz**2+szx**2))
    # exposed faces for rendering
    pad=np.zeros((nx+2,ny+2,nz+2),bool); pad[1:-1,1:-1,1:-1]=solid
    faces=[]; fcell=[]
    for dname,(di,dj,dk) in _SHIFT.items():
        exp=~pad[1+ii+di,1+jj+dj,1+kk+dk]
        faces.append(en[exp][:,FACE[dname]]); fcell.append(np.where(exp)[0])
    fnodes=np.concatenate(faces); fcell=np.concatenate(fcell)
    coords=np.zeros((nn,3))
    alln=np.arange(nn); ai=alln%nxp; aj=(alln//nxp)%nyp; ak=alln//(nxp*nyp)
    coords[:,0]=ai*a; coords[:,1]=aj*a; coords[:,2]=ak*a
    return dict(coords=coords, U=U.reshape(-1,3), fnodes=fnodes, fvm=vm[fcell],
                vm=vm, h=h, L=L, base_h=base_h,
                root_vm=float(np.percentile(vm,99.5)), peak_vm=float(vm.max()))

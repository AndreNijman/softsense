"""Map the 3D FEA displacement field onto the Blender finger OBJ meshes to make
an accurate 'wrap' shape key. Runs in system Python (has scipy); writes an npz of
per-OBJ-vertex deformed coordinates + von Mises that Blender then loads by index.

finger_R: FEA was solved on the finger_R cross-section -> direct map.
finger_L: x-mirror of the finger_R field (geometry + displacement) -> map to finger_L OBJ.
"""
import numpy as np, os, sys
from scipy.spatial import cKDTree

BUNDLE=os.environ.get("GRIPPER_RENDER_BUNDLE", "render_bundle")  # render-bundle root
GEO=os.path.join(BUNDLE,"geometry"); OUT=os.path.join(BUNDLE,"fea3d")

def read_obj_verts(path):
    vs=[]
    with open(path) as f:
        for ln in f:
            if ln.startswith('v '):
                _,x,y,z=ln.split()[:4]; vs.append((float(x),float(y),float(z)))
    return np.array(vs)

def idw_map(src_pts, src_val, dst_pts, k=6, power=2.0):
    tree=cKDTree(src_pts)
    d,idx=tree.query(dst_pts,k=k)
    d=np.maximum(d,1e-6)
    w=1.0/d**power
    w/=w.sum(axis=1,keepdims=True)
    out=np.einsum('nk,nkd->nd', w, src_val[idx]) if src_val.ndim==2 else np.einsum('nk,nk->n', w, src_val[idx])
    return out

def build(frame_index=None):
    sol=np.load(os.path.join(OUT,"fea3d_solution.npz"))
    rest=sol['rest'].astype(np.float64)      # (Nf,3) finger-local mm
    frames=sol['frames']; vms=sol['vms']
    if frame_index is None: frame_index=len(frames)-1
    defo=frames[frame_index].astype(np.float64)
    disp=defo-rest
    vm=vms[frame_index].astype(np.float64)

    res={}
    # ---- finger_R ----
    objR=read_obj_verts(os.path.join(GEO,"finger_R_base.obj"))
    dispR=idw_map(rest, disp, objR)
    vmR=idw_map(rest, vm, objR)
    res['R_def']=(objR+dispR).astype(np.float32)
    res['R_vm']=vmR.astype(np.float32)
    res['R_n']=len(objR)
    # ---- finger_L (mirror x) ----
    restL=rest.copy(); restL[:,0]*=-1
    dispL=disp.copy(); dispL[:,0]*=-1
    objL=read_obj_verts(os.path.join(GEO,"finger_L_base.obj"))
    dL=idw_map(restL, dispL, objL)
    vmL=idw_map(restL, vm, objL)
    res['L_def']=(objL+dL).astype(np.float32)
    res['L_vm']=vmL.astype(np.float32)
    res['L_n']=len(objL)
    res['frame_index']=frame_index
    res['vm_max']=float(vm.max())
    np.savez_compressed(os.path.join(OUT,"shapekey_map.npz"), **res)
    print(f"frame {frame_index}: R verts {len(objR)} L verts {len(objL)}  "
          f"max|dispR|={np.linalg.norm(dispR,axis=1).max():.2f}mm vm_max={vm.max():.2f}MPa")
    return res

if __name__=="__main__":
    fi=int(sys.argv[1]) if len(sys.argv)>1 else None
    build(fi)

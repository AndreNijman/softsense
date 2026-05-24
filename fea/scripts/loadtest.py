"""DECISIVE FEA-validity check: does the 3D corotational solver reproduce the Fin
Ray effect at all? Apply a pure +X patch force on the contact face mid-band (no
contact search, no cylinder), clamp the two bores, and report which way the apex
moves. Fin Ray effect => apex curls toward the object side (-X) => tip_inward > 0.
If the apex moves +X (with the load), the structure has no Fin Ray coupling under
this BC/loading and the earlier "won't wrap" results are about the mechanism, not
a contact-modelling artifact.

Usage: python loadtest.py <name> '<params_json>'  (params -> regen_section)
"""
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import iter_harness as H
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

name = sys.argv[1]
params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {"_gen": "finray2"}
FTOT = 6.0            # N total +X patch force (ramped)
NSTEP = 16
BASECLAMP = bool(params.pop("_baseclamp", False))   # clamp the bottom base edge
                                                    # (textbook Fin Ray) vs the 2 bores

p2d, tris, lm = H.regen_section(params, "/tmp")
nodes, tets, N2 = H.build_tets(p2d, tris)
P = H.precompute(nodes, tets)
nn = nodes.shape[0]; ndof = nn * 3; Xrest = nodes.copy(); u = np.zeros(ndof)
Ke0 = P['Ke0']; invJm = P['invJm']; edof = P['edof']; Iidx = P['I']; Jidx = P['J']
Xvec = P['Xvec']; Ntet = P['Ntet']

C, D = np.array(lm['C']), np.array(lm['D']); rb = lm['r_bore']
if BASECLAMP:                       # textbook Fin Ray: clamp the whole bottom base edge
    clamp = Xrest[:, 1] < lm['base_y'] + 1.0
else:                               # real mount: the two coupler pin bores
    dC = np.hypot(Xrest[:, 0] - C[0], Xrest[:, 1] - C[1])
    dD = np.hypot(Xrest[:, 0] - D[0], Xrest[:, 1] - D[1])
    clamp = (dC < rb + 0.4) | (dD < rb + 0.4)
fixed = np.zeros(ndof, bool)
for d in range(3): fixed[3 * np.where(clamp)[0] + d] = True
free = np.where(~fixed)[0]

# contact-face mid-band nodes: lowest-x quartile, mid third in y
base_y, tip_y = lm['base_y'], lm['tip_y']; Lf = tip_y - base_y
xthr = np.percentile(Xrest[:, 0], 20)
band = (Xrest[:, 0] < xthr) & (Xrest[:, 1] > base_y + 0.40 * Lf) & (Xrest[:, 1] < base_y + 0.60 * Lf)
load_nodes = np.where(band)[0]
print(f"[{name}] clamp={clamp.sum()} load_nodes={len(load_nodes)} (+X patch) ndof={ndof}")

tipc = np.where(Xrest[:, 1] > Xrest[:, 1].max() - 1.0)[0]
tn = tipc[np.argmin(np.abs(Xrest[tipc, 2] - (H.Z0 + H.Z1) / 2))]

for s in range(1, NSTEP + 1):
    f = FTOT * s / NSTEP
    fext = np.zeros(ndof); fext[3 * load_nodes] = f / len(load_nodes)   # +X
    for it in range(16):
        x = (Xrest.reshape(-1) + u).reshape(nn, 3); xe = x[tets]
        Js = np.stack([xe[:, 1] - xe[:, 0], xe[:, 2] - xe[:, 0], xe[:, 3] - xe[:, 0]], axis=2)
        F = np.einsum('nij,njk->nik', Js, invJm); R = H.polar_R(F)
        RtX = H.apply_blockR(np.transpose(R, (0, 2, 1)), xe.reshape(Ntet, 12)) - Xvec
        f_e = H.apply_blockR(R, np.einsum('nij,nj->ni', Ke0, RtX))
        f_int = np.zeros(ndof); np.add.at(f_int, edof.reshape(-1), f_e.reshape(-1))
        Rb = np.zeros((Ntet, 12, 12))
        for k in range(4): Rb[:, 3 * k:3 * k + 3, 3 * k:3 * k + 3] = R
        Ke = np.einsum('nij,njk,nlk->nil', Rb, Ke0, Rb)
        K = coo_matrix((Ke.reshape(-1), (Iidx, Jidx)), shape=(ndof, ndof)).tocsr()
        r = f_int - fext; rn = np.linalg.norm(r[free])
        if it > 0 and rn < 2e-3 * (1 + np.linalg.norm(fext[free])): break
        du = spsolve(K[free][:, free].tocsc(), -r[free])
        u[free] += (1.0 if it > 1 else 0.7) * du
    x = (Xrest.reshape(-1) + u).reshape(nn, 3)
    tip_inward = float(Xrest[tn, 0] - x[tn, 0])    # +ve = apex moved -X (toward object)
    print(f"  step {s:2d} F={f:4.2f}N  apex dx={x[tn,0]-Xrest[tn,0]:+.2f}mm  tip_inward={tip_inward:+.2f}  (>0 = Fin Ray wrap toward object)", flush=True)
print(f"[{name}] VERDICT: {'WRAPS (Fin Ray effect present)' if tip_inward > 0.5 else 'NO WRAP (apex follows the load, away from object)'}")

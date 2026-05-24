"""Re-evaluate saved FEA solutions at a FIXED CLOSURE (press depth), the fair
operating point for the wrap comparison (grip force is a reported result, not the
control). No re-solving: reads fea3d_solution.npz (per-step frames, nodal vM,
press, grip) and recomputes the contact/wrap metrics at the step closest to
PRESS_AT_REPORT. Usage: python reeval_npz.py <iter_dir> [<iter_dir> ...]"""
import numpy as np, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import iter_harness as H            # R_NECK, YC, GAP, KPEN, TPU_STRENGTH
os.environ["GRIPPER_OPEN"] = "0"; os.environ["GRIPPER_FINGER_SCALE"] = "1.0"
import gripper

PRESS_AT_REPORT = 8.0
refR = gripper.solve_side_right(0.0); C, D = refR["C"], refR["D"]
BASE_Y = max(C[1], D[1]) - gripper.FR_BASE_DROP
TIP_Y = BASE_Y + gripper.FR_BLADE_LEN * gripper.FINGER_SCALE
L = TIP_Y - BASE_Y


def reeval(d, press_at=PRESS_AT_REPORT):
    z = np.load(os.path.join(d, "fea3d_solution.npz"))
    rest, frames, vms, press, grip = z["rest"], z["frames"], z["vms"], z["press"], z["grip"]
    xc0 = rest[:, 0].min() - H.R_NECK - H.GAP
    idx = int(np.argmin(np.abs(press - press_at)))
    x = frames[idx]; cx = xc0 + press[idx]
    dx = x[:, 0] - cx; dy = x[:, 1] - H.YC; rr = np.hypot(dx, dy) + 1e-9
    pen = H.R_NECK - rr; inside = pen > 0
    cf = np.where(inside, H.KPEN * pen, 0.0)
    yk = rest[inside, 1]; fk = cf[inside]
    engage = (yk.max() - yk.min()) / L if inside.any() else 0.0
    tot = fk.sum() + 1e-12
    top = fk[yk >= BASE_Y + 2 / 3 * L].sum() / tot
    mid = fk[(yk >= BASE_Y + 1 / 3 * L) & (yk < BASE_Y + 2 / 3 * L)].sum() / tot
    tipc = np.where(rest[:, 1] > rest[:, 1].max() - 1.0)[0]
    tn = tipc[np.argmin(np.abs(rest[tipc, 2] - 18.0))]
    tip_in = float(rest[tn, 0] - x[tn, 0])
    vm = vms[idx]; maxvm = float(vm.max())
    spread = float((vm > 0.3 * maxvm).mean())
    return dict(press_mm=round(float(press[idx]), 2),
                grip_at_press_N=round(float(grip[idx]), 2),
                contact_nodes=int(inside.sum()),
                engage_y_frac=round(engage, 3),
                top_third_force_frac=round(float(top), 3),
                mid_third_force_frac=round(float(mid), 3),
                tip_inward_mm=round(tip_in, 2),
                stress_spread_frac=round(spread, 3),
                max_von_mises_MPa=round(maxvm, 3),
                margin_x=round(H.TPU_STRENGTH / maxvm, 2))


if __name__ == "__main__":
    for d in sys.argv[1:]:
        print(os.path.basename(d), json.dumps(reeval(d)))

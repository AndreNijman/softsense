// Interactive motion sidecar for gripper_interactive.step (baked at CLOSED).
//
// One slider, "open", drives the whole single-DOF mechanism live:
//   open = 0  -> closed (jaws together)   open = 1 -> fully open (V splay)
//
// Physically this is the angle you turn the input SHAFT (coaxial with the
// left crank pivot). The meshing gear pair makes both fingers mirror.
// The four-bar solver below is the same one used by the Python generator,
// so the live motion matches the baked STEP geometry exactly.
//
// Part occurrence ids (by assembly order in gripper.py):
//   o1.1 enclosure  o1.2 shaft  o1.3 gearR  o1.4 gearL  o1.5 crankR  o1.6 crankL
//   o1.7 followerR  o1.8 followerL  o1.9 fingerR  o1.10 fingerL
//   o1.11 pinA_R o1.12 pinB_R o1.13 pinC_R o1.14 pinD_R
//   o1.15 pinA_L o1.16 pinB_L o1.17 pinC_L o1.18 pinD_L

// ---- locked kinematic constants (mm, deg) -- mirror of gripper.py ----
const A_R = [12.0, 0.0];
const B_R = [26.0, 10.0];
const R_CRANK = 34.0, R_FOLLOW = 32.0, R_COUPLER = 20.0;
const THETA_CLOSED = 104.0, OPEN_TRAVEL = 46.0;

const d2r = (d) => (d * Math.PI) / 180;
const r2d = (r) => (r * 180) / Math.PI;

function crankPoint(open) {
  const th = d2r(THETA_CLOSED - OPEN_TRAVEL * open);
  return [A_R[0] + R_CRANK * Math.cos(th), A_R[1] + R_CRANK * Math.sin(th)];
}

function circleBoth(c0, r0, c1, r1) {
  const dx = c1[0] - c0[0], dy = c1[1] - c0[1];
  const d = Math.hypot(dx, dy);
  const a = (r0 * r0 - r1 * r1 + d * d) / (2 * d);
  const h = Math.sqrt(Math.max(0, r0 * r0 - a * a));
  const xm = c0[0] + (a * dx) / d, ym = c0[1] + (a * dy) / d;
  const px = -dy / d, py = dx / d;
  return [[xm + h * px, ym + h * py], [xm - h * px, ym - h * py]];
}

// Right-side solution with continuity tracking from the closed pose.
function solveRight(open) {
  const C0 = crankPoint(0);
  const dPar = [
    B_R[0] + (C0[0] - A_R[0]) * (R_FOLLOW / R_CRANK),
    B_R[1] + (C0[1] - A_R[1]) * (R_FOLLOW / R_CRANK),
  ];
  let cand = circleBoth(C0, R_COUPLER, B_R, R_FOLLOW);
  let D = cand[0], best = Infinity;
  for (const p of cand) {
    const e = (p[0] - dPar[0]) ** 2 + (p[1] - dPar[1]) ** 2;
    if (e < best) { best = e; D = p; }
  }
  let C = C0;
  if (open > 0) {
    const n = Math.max(1, Math.ceil(open / 0.02));
    for (let i = 1; i <= n; i++) {
      C = crankPoint((open * i) / n);
      cand = circleBoth(C, R_COUPLER, B_R, R_FOLLOW);
      let nb = Infinity, nd = D;
      for (const p of cand) {
        const e = (p[0] - D[0]) ** 2 + (p[1] - D[1]) ** 2;
        if (e < nb) { nb = e; nd = p; }
      }
      D = nd;
    }
  }
  const couplerAng = r2d(Math.atan2(D[1] - C[1], D[0] - C[0]));
  const followAng = r2d(Math.atan2(D[1] - B_R[1], D[0] - B_R[0]));
  const crankAng = THETA_CLOSED - OPEN_TRAVEL * open;
  return { C, D, couplerAng, followAng, crankAng };
}

export default {
  manifest: {
    schemaVersion: 1,
    parameters: {
      open: {
        type: "number", label: "Open  (rotate shaft)", unit: "",
        min: 0, max: 1, step: 0.01, default: 0,
        description: "0 = closed jaws, 1 = fully open. Drives the single DOF; both fingers mirror via the gear mesh.",
      },
    },
  },

  update(ctx) {
    const open = Math.max(0, Math.min(1, Number(ctx.params.open) || 0));
    const r = solveRight(open);
    const r0 = solveRight(0);

    const dCrank = r.crankAng - r0.crankAng;          // right crank rotation (deg)
    const dFollow = r.followAng - r0.followAng;        // right follower rotation
    const dCoupler = r.couplerAng - r0.couplerAng;     // right finger rotation
    const dCx = r.C[0] - r0.C[0], dCy = r.C[1] - r0.C[1];
    const dDx = r.D[0] - r0.D[0], dDy = r.D[1] - r0.D[1];

    const Z = [0, 0, 1];
    const rot = (id, origin, ang) =>
      ctx.effects.transform(id, { rotate: { axis: Z, origin: [origin[0], origin[1], 0], angleDeg: ang } });
    const fingerMove = (id, C0, dAng, dx, dy) =>
      ctx.effects.transform(id, { transforms: [
        { rotate: { axis: Z, origin: [C0[0], C0[1], 0], angleDeg: dAng } },
        { translate: [dx, dy, 0] },
      ] });
    const tr = (id, dx, dy) => ctx.effects.transform(id, { translate: [dx, dy, 0] });

    const A_L = [-A_R[0], A_R[1]];
    const B_L = [-B_R[0], B_R[1]];
    const C0_L = [-r0.C[0], r0.C[1]];

    // ---- RIGHT side ----
    rot("o1.3", A_R, dCrank);                 // gear_R
    rot("o1.5", A_R, dCrank);                 // crank_R
    rot("o1.7", B_R, dFollow);                // follower_R
    fingerMove("o1.9", r0.C, dCoupler, dCx, dCy);     // finger_R
    tr("o1.13", dCx, dCy);                    // pin_C_R
    tr("o1.14", dDx, dDy);                    // pin_D_R

    // ---- LEFT side (mirror: negate angles, mirror translations in X) ----
    rot("o1.2", A_L, -dCrank);                // drive_shaft turns with left crank
    rot("o1.4", A_L, -dCrank);                // gear_L
    rot("o1.6", A_L, -dCrank);                // crank_L
    rot("o1.8", B_L, -dFollow);               // follower_L
    fingerMove("o1.10", C0_L, -dCoupler, -dCx, dCy);  // finger_L
    tr("o1.17", -dCx, dCy);                   // pin_C_L
    tr("o1.18", -dDx, dDy);                   // pin_D_L

    ctx.requestRender?.();
  },
};

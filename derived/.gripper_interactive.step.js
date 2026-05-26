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
// Part occurrence ids (assembly order in gripper.py; model is reoriented Z-up,
// so the hinge axis is world +Y and translations map (dx,dy)->(dx,0,dy)):
//   o1.1 enclosure   o1.2 drive_arm_R   o1.3 drive_arm_L
//   o1.4 follower_R  o1.5 follower_L    o1.6 finger_R   o1.7 finger_L
//   o1.8 pin_A_R  o1.9 pin_B_R  o1.10 pin_C_R  o1.11 pin_D_R
//   o1.12 pin_A_L  o1.13 pin_B_L  o1.14 pin_C_L  o1.15 pin_D_L
//   o1.16 front_cover   o1.17 input_pinion_shaft (bottom drive; shown static)

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

    // Model is reoriented Z-up (rotate +90 deg about X at export). The 2D
    // solver works in the authored frame; map into the world frame here:
    //   hinge axis  +Z(model) -> -Y(world)  => rotate about +Y by -modelAngle
    //   point   (x, y)(model) -> (x, 0, y)(world)
    //   vector  (dx, dy)(model) -> (dx, 0, dy)(world)
    const Y = [0, 1, 0];
    const rot = (id, mx, my, modelAng) =>
      ctx.effects.transform(id, { rotate: { axis: Y, origin: [mx, 0, my], angleDeg: -modelAng } });
    const tr = (id, mdx, mdy) =>
      ctx.effects.transform(id, { translate: [mdx, 0, mdy] });
    const fingerMove = (id, c0x, c0y, modelAng, mdx, mdy) =>
      ctx.effects.transform(id, { transforms: [
        { rotate: { axis: Y, origin: [c0x, 0, c0y], angleDeg: -modelAng } },
        { translate: [mdx, 0, mdy] },
      ] });

    const A_L = [-A_R[0], A_R[1]];
    const B_L = [-B_R[0], B_R[1]];
    const C0_L = [-r0.C[0], r0.C[1]];

    // ---- RIGHT side ----
    rot("o1.2", A_R[0], A_R[1], dCrank);              // drive_arm_R (gear+crank)
    rot("o1.4", B_R[0], B_R[1], dFollow);             // follower_R
    fingerMove("o1.6", r0.C[0], r0.C[1], dCoupler, dCx, dCy);  // finger_R
    tr("o1.10", dCx, dCy);                            // pin_C_R
    tr("o1.11", dDx, dDy);                            // pin_D_R

    // ---- LEFT side (mirror) ----
    rot("o1.3", A_L[0], A_L[1], -dCrank);             // drive_arm_L (turns the shaft)
    rot("o1.5", B_L[0], B_L[1], -dFollow);            // follower_L
    fingerMove("o1.7", C0_L[0], C0_L[1], -dCoupler, -dCx, dCy);  // finger_L
    tr("o1.14", -dCx, dCy);                           // pin_C_L
    tr("o1.15", -dDx, dDy);                           // pin_D_L

    // ---- input pinion+shaft: spins about its own VERTICAL axis (world Z) at the
    // gear ratio CROWN_RC/PINION_RP. crank A_L turns -dCrank; the crown rides it;
    // the pinion turns that * ratio. (Drive geometry: axis at world x=DRIVE_X,
    // y=-DRIVE_Z; this is the one part whose axis is vertical, not the world-Y hinge.)
    const CROWN_RC = 8.0, PINION_RP = 3.0, DRIVE_X = -12.0, DRIVE_Z = 10.52;
    const pinionSpin = dCrank * (CROWN_RC / PINION_RP);   // matches _pinion_spin_deg in gripper.py
    ctx.effects.transform("o1.17", { rotate: {
      axis: [0, 0, 1], origin: [DRIVE_X, -DRIVE_Z, 0], angleDeg: pinionSpin } });

    ctx.requestRender?.();
  },
};

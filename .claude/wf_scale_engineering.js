export const meta = {
  name: 'scale-engineering-reruns',
  description: 'Re-run finger FEA, gear/motor, underwater, grip at 1.5x & 2.0x self-similar',
  phases: [
    { title: 'Finger-FEA' },
    { title: 'Drivetrain' },
    { title: 'Underwater' },
    { title: 'Grip' },
  ],
}

// Each domain agent: sets GRIPPER_SCALE env for the scaled self-similar geometry,
// runs the existing scripts at 1.5x AND 2.0x (and 1.0x where a self-similar baseline
// is needed), writes result artifacts into variants/scale_<k>x/fea, updates its domain
// doc with a both-scale table + honest framing, and RETURNS structured headline numbers.
// Agents MUST NOT git commit (the parent commits per-phase). Compute is LOCAL (MSI down)
// -> screen/coarse modes; flag hi-fidelity for an MSI re-run.

const REPO = '/home/andre/gripper-cad'
const VENV = '/home/andre/.cad-venv/bin/python'

const NUM = { type: 'number' }
const SCALE_RESULT = {
  type: 'object',
  properties: {
    summary: { type: 'string' },
    per_scale: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          scale: NUM, headline: { type: 'string' },
          metrics: { type: 'object', additionalProperties: true },
        },
        required: ['scale', 'headline'],
      },
    },
    files_written: { type: 'array', items: { type: 'string' } },
    docs_updated: { type: 'array', items: { type: 'string' } },
    caveats: { type: 'string' },
  },
  required: ['summary', 'per_scale', 'files_written', 'docs_updated'],
}

const common = `Repo: ${REPO}. Python venv: ${VENV}. Always run with PYTHONPATH=${REPO}.
The model now has a global self-similar scale: set env GRIPPER_SCALE=1.5 or 2.0 and the
gripper geometry (and anything that imports gripper.py for dimensions) scales self-similarly
(walls included). The 1x baseline is GRIPPER_SCALE=1.0 (== unset). MSI is DOWN, so run LOCALLY
in screen/coarse mode; note where a high-fidelity MSI re-run is warranted. Do NOT git commit.
Do NOT modify gripper.py. Keep edits to your own domain's docs + result files.`

const fingerPrompt = `${common}

YOU OWN: the headline self-similar finger-grasp FEA. The OLD fea/SCALABILITY.md found that
scaling the BLADE ONLY (walls fixed) made the finger floppy above ~1.1x (score 0.645 at 1x ->
0.441 at 1.5x -> 0.368 at 2.0x). The new GRIPPER_SCALE scales walls too, so the wall/blade ratio
is constant and the bigger finger should KEEP the ~0.645 score. PROVE it.

RUN (each ~1-3 min; finger meshed once, then 3 objects):
  cd ${REPO}
  GRIPPER_SCALE=1.0 PYTHONPATH=${REPO} ${VENV} fea/scripts/eval_finger.py selfsim_1p0 production '{}' screen
  GRIPPER_SCALE=1.5 PYTHONPATH=${REPO} ${VENV} fea/scripts/eval_finger.py selfsim_1p5 production '{}' screen
  GRIPPER_SCALE=2.0 PYTHONPATH=${REPO} ${VENV} fea/scripts/eval_finger.py selfsim_2p0 production '{}' screen
Each writes fea/iterations/selfsim_<k>/eval.json (fields: score, base, grip_incon, eff_scale,
per-object metrics: contact_arc_deg, pressure_cov, grip_at_press_N, margin_x). Console prints SCORE=.
eval_finger.py already scales objects/press/mesh by the EFFECTIVE factor (gripper.SCALE * _scale),
so leaving params '{}' is a fair self-similar comparison.

THEN:
- Copy each eval.json + wrap_stages.png into variants/scale_1.5x/fea and variants/scale_2.0x/fea
  (keep the 1.0 one in fea/iterations as the reference).
- Add a clearly-titled "Self-similar scale-up (GRIPPER_SCALE)" section/table to fea/SCALABILITY.md
  contrasting the NEW self-similar scores (1.0/1.5/2.0) with the OLD blade-only numbers
  (0.645/0.441/0.368), plus one honest paragraph: self-similar scaling keeps the score because the
  wall/blade ratio is fixed; force at a given grip scales ~k^2 but stays gear-limited (no absolute-
  newton overclaim -- the repo posture is rank/size). If a solve cannot reach the 12 N probe at a
  scale, say so explicitly.
RETURN per-scale score/base/grip_incon and the headline (did the bigger finger KEEP its grip?).`

const drivetrainPrompt = `${common}

YOU OWN: gear structural limit (T_safe) + tip-force envelope + motor re-check at 1.5x and 2.0x.
Self-similar scaling: tooth bending capacity (T_safe) scales ~k^3, deliverable tip force ~k^2.
Read motor/scripts/ (gear_fea.py, gear_fea_radial.py -> T_safe; drivetrain_force_envelope.py;
kinematics_chain.py / torque_chain.py). For each, determine whether it imports gripper.py for gear
dims (then GRIPPER_SCALE=k propagates) or takes its own params (then pass the scaled module/radius).
RUN each at GRIPPER_SCALE=1.0, 1.5, 2.0 (cd ${REPO}; PYTHONPATH=${REPO}; ${VENV} ...).
Confirm the power laws (T_safe ~k^3, force ~k^2) and that the SELECTED servos still clear the load
with large headroom (XW540 9.5 N.m / STS3250 4.9 N.m stall vs the new T_safe). Copy result JSONs into
variants/scale_<k>x/fea. Update motor/DRIVETRAIN.md and motor/SELECTION.md with a both-scale table
(T_safe, per-finger force band, servo headroom ratio) + honest framing (force grows but is STILL
gear-limited; current-limit is the protection). RETURN per-scale T_safe, force band, headroom.`

const underwaterPrompt = `${common}

YOU OWN: underwater crush / external-pressure FEA at 1.5x and 2.0x. EXPECTATION (state it, then
verify -- do NOT present it as a new discovery): self-similar scaling preserves wall-thickness/radius
ratio, so thin-wall hoop stress sigma ~ p*r/t is SCALE-INVARIANT -> von-Mises field and material-yield
depth UNCHANGED vs 1x; only absolute displacement scales ~k. Flooded stays vM~0. Run
fea/scripts/underwater_crush_3d.py (and underwater_pressure_probe.py) at GRIPPER_SCALE=1.0, 1.5, 2.0
(screen/coarse; cd ${REPO}; PYTHONPATH=${REPO}). Confirm vM field + yield-depth reproduce the 1x
values (within solver tolerance) and report displacement scaling. Copy result JSONs/figures into
variants/scale_<k>x/fea. Add a short "scale-invariance confirmed" subsection to fea/UNDERWATER_FEA.md
(do NOT headline as improved). RETURN per-scale peak vM, yield depth, max displacement.`

const gripPrompt = `${common}

YOU OWN: wet-grip texture re-evaluation at 1.5x and 2.0x. KEY FACT: the grip MICRO-TEXTURE
(FR_GRIP_* in gripper.py) now SCALES self-similarly with the gripper (each FR_GRIP_* has *SCALE). The
crosshatch channel width goes 0.54 -> 0.81 -> 1.08 mm at 1.0/1.5/2.0x. The grip-texture campaign found
grip is grip-NEUTRAL above a ~0.3 mm channel (drainage saturates) -- and EVERY scaled channel stays
well above 0.3 mm -- so the wet-grip coefficient/score from grip/scripts (grip_model.py,
baseline_validate.py) is ~SCALE-INVARIANT (still in the saturated-drainage plateau; coarser channels
drain at least as well). VERIFY: confirm FR_GRIP_* now carry *SCALE and that 0.54*1.5 and 0.54*2.0
both exceed the ~0.3 mm saturation threshold; run grip/scripts/grip_model.py (+ baseline_validate.py)
once to record the current score; ARGUE scale-invariance from the drainage-saturation plateau rather
than re-running a full sweep per scale. Add a one-paragraph "behaviour under GRIPPER_SCALE" note to
grip/GRIP_TEXTURE.md (texture scales; stays in the saturated-drainage band; grip score holds).
RETURN the grip score and the scale-invariance argument.`

const results = await parallel([
  () => agent(fingerPrompt, { label: 'finger-fea', phase: 'Finger-FEA', schema: SCALE_RESULT }),
  () => agent(drivetrainPrompt, { label: 'drivetrain-motor', phase: 'Drivetrain', schema: SCALE_RESULT }),
  () => agent(underwaterPrompt, { label: 'underwater', phase: 'Underwater', schema: SCALE_RESULT }),
  () => agent(gripPrompt, { label: 'grip', phase: 'Grip', schema: SCALE_RESULT }),
])

return {
  finger: results[0],
  drivetrain: results[1],
  underwater: results[2],
  grip: results[3],
}

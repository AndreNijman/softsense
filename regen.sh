#!/usr/bin/env bash
# Regenerate every deliverable from gripper.py + motor/cad/system_assembly.py:
#   poses          -> derived/gripper_{closed,mid,open,interactive,scale16}.step
#   parts          -> parts/*.{step,stl}
#   print plates   -> print_plates/*.stl
#   print set      -> output/*.stl  (descriptively named)
#   system STEPs   -> motor/cad/output/system_assembly_*.step (T2 ladder + T3)
#   heroes / gif   -> renders/  (now the FULL system: gripper + canister + STS3250)
set -e
cd /home/andre/gripper-cad
source /home/andre/.cad-venv/bin/activate 2>/dev/null || true
STEP="python /home/andre/.claude/skills/cad/scripts/step"
SNAP="python3 /home/andre/.claude/skills/render/scripts/snapshot"
SYSGEN="python motor/cad/system_assembly.py"
export PYTHONPATH=/home/andre/gripper-cad

echo "[poses]"
GRIPPER_OPEN=0   $STEP gripper.py -o derived/gripper_closed.step       >/dev/null 2>&1 && echo "  closed"
GRIPPER_OPEN=0.5 $STEP gripper.py -o derived/gripper_mid.step          >/dev/null 2>&1 && echo "  mid"
GRIPPER_OPEN=1   $STEP gripper.py -o derived/gripper_open.step         >/dev/null 2>&1 && echo "  open"
GRIPPER_OPEN=0   $STEP gripper.py -o derived/gripper_interactive.step  >/dev/null 2>&1 && echo "  interactive"
GRIPPER_OPEN=0 GRIPPER_FINGER_SCALE=1.6 $STEP gripper.py -o derived/gripper_scale16_interactive.step >/dev/null 2>&1 && echo "  scale16"

echo "[parts]";  python scripts/export_parts.py     >/dev/null 2>&1 && echo "  export OK"
echo "[plates]"; python scripts/make_print_plates.py >/dev/null 2>&1 && echo "  plates OK"

echo "[system assembly STEPs]"
GRIPPER_CANISTER_VARIANT=T2 GRIPPER_CANISTER_SERVO=STS3250 \
  $STEP motor/cad/system_assembly.py -o motor/cad/output/system_assembly_T2_STS3250.step >/dev/null 2>&1 && echo "  T2 STS3250"
for s in XW540 XM540 STS3215; do
  GRIPPER_CANISTER_SERVO=$s $SYSGEN >/dev/null 2>&1 && echo "  T2 $s"
done
GRIPPER_CANISTER_VARIANT=T3 GRIPPER_CANISTER_SERVO=STS3250 $SYSGEN >/dev/null 2>&1 && echo "  T3 STS3250 (mag coupling)"

echo "[full-system renders]";  bash scripts/render_full_system.sh && echo "  renders OK"
echo "REGEN_DONE"

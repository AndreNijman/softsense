#!/usr/bin/env bash
# Regenerate every deliverable from gripper.py (poses, parts, plates, heroes, gif).
set -e
cd /home/andre/gripper-cad
source /home/andre/.cad-venv/bin/activate 2>/dev/null || true
STEP="python /home/andre/.claude/skills/cad/scripts/step gripper.py -o"
SNAP="python3 /home/andre/.claude/skills/render/scripts/snapshot"
export PYTHONPATH=/home/andre/gripper-cad

echo "[poses]"
GRIPPER_OPEN=0   $STEP gripper_closed.step       >/dev/null 2>&1 && echo "  closed"
GRIPPER_OPEN=0.5 $STEP gripper_mid.step          >/dev/null 2>&1 && echo "  mid"
GRIPPER_OPEN=1   $STEP gripper_open.step         >/dev/null 2>&1 && echo "  open"
GRIPPER_OPEN=0   $STEP gripper_interactive.step  >/dev/null 2>&1 && echo "  interactive"
GRIPPER_OPEN=0 GRIPPER_FINGER_SCALE=1.6 $STEP gripper_scale16_interactive.step >/dev/null 2>&1 && echo "  scale16"

echo "[parts]";  python export_parts.py     >/dev/null 2>&1 && echo "  export OK"
echo "[plates]"; python make_print_plates.py >/dev/null 2>&1 && echo "  plates OK"

echo "[heroes]"
$SNAP --input gripper_open.step   --output /home/andre/gripper-cad/gripper_hero_open.png   --mode view --camera iso --theme technical --width 1800 --height 1350 >/dev/null 2>&1 && echo "  hero_open"
$SNAP --input gripper_closed.step --output /home/andre/gripper-cad/gripper_hero_closed.png --mode view --camera iso --theme technical --width 1800 --height 1350 >/dev/null 2>&1 && echo "  hero_closed"

echo "[gif]"
$SNAP --input gripper_interactive.step --output /home/andre/gripper-cad/gripper_motion.gif \
  --params '{"values":{},"animate":{"open":{"from":0,"to":1}},"durationSeconds":2.2,"fps":8,"loop":true}' >/dev/null 2>&1 && echo "  gif OK"
echo "REGEN_DONE"

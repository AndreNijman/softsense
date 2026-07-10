#!/usr/bin/env bash
# Regenerate all derived poses CONCURRENTLY (one process per pose). Each STEP gen is
# single-threaded OCCT (~3 min); running the 5 independent poses in parallel on a
# multicore box gives wall-time ~= one gen instead of 5x serial. (regen.sh does these
# serially; use this for the heavy STEP step.)
set -u
cd /home/andre/Projects/softsense
source /home/andre/.cad-venv/bin/activate 2>/dev/null || true
STEP="python /home/andre/.claude/skills/cad/scripts/step"
LOG=/tmp/claude-1000/-home-andre-Projects-softsense/a3c1cfc8-9fc0-4b7e-9ff1-a293bcece136/scratchpad
mkdir -p "$LOG"

echo "[parallel poses] launching 5 concurrent STEP gens..."
GRIPPER_OPEN=0   $STEP gripper.py -o derived/gripper_closed.step      >"$LOG/pose_closed.log" 2>&1 &
GRIPPER_OPEN=0.5 $STEP gripper.py -o derived/gripper_mid.step         >"$LOG/pose_mid.log" 2>&1 &
GRIPPER_OPEN=1   $STEP gripper.py -o derived/gripper_open.step        >"$LOG/pose_open.log" 2>&1 &
GRIPPER_OPEN=0   $STEP gripper.py -o derived/gripper_interactive.step >"$LOG/pose_interactive.log" 2>&1 &
GRIPPER_OPEN=0 GRIPPER_FINGER_SCALE=1.6 $STEP gripper.py -o derived/gripper_scale16_interactive.step >"$LOG/pose_scale16.log" 2>&1 &
wait
echo "[parallel poses] all done. Exit codes captured in logs."
ls -la derived/*.step | awk '{print "  "$5"  "$9}'

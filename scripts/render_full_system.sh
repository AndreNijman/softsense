#!/usr/bin/env bash
# Render the full SYSTEM (gripper + canister + STS3250 servo + shaft + lip seal +
# end caps + penetrators) into renders/ at the root.
#
# Worked-example servo is the STS3250 (~USD 130 total system cost).
# Outputs in /renders/:
#   gripper_hero_open.png      open-pose still
#   gripper_hero_closed.png    closed-pose still
#   gripper_motion.gif         3-keyframe ping-pong (0 → 0.5 → 1 → 0.5 → 0)
#   gripper_xray.png           cutaway showing servo + shaft + lip seal
#   gripper_xray.gif           same as motion but cutaway
#
# Strategy: gripper.gen_step() is ~3.5 min per pose (Fin Ray + gears = heavy CSG).
# We build the THREE keyframe STEPs in parallel (one core each, ~3.5 min wall),
# then render PNGs from them (cheap), and ffmpeg-assemble the GIF locally.
set -e
cd /home/andre/Projects/softsense
source /home/andre/.cad-venv/bin/activate 2>/dev/null || true

STEPCLI="python /home/andre/.claude/skills/cad/scripts/step"
SNAP="python3 /home/andre/.claude/skills/render/scripts/snapshot"
SYS=motor/cad/system_assembly.py
SERVO=STS3250
MESHTOL=0.3            # coarser than the default 0.05 → faster GLB tessellation
RENDER_VIEWER_ROOT=/home/andre/.claude/skills/render/scripts/viewer
mkdir -p renders motor/cad/output

FRAMES_DIR=$(mktemp -d)
trap "rm -rf $FRAMES_DIR" EXIT

build_step() {  # $1 = "VARIANT,OPEN" (e.g. "T2_UNIBODY,0.5" or "T2_XRAY,0")
    local VAR=${1%,*}
    local OPEN=${1#*,}
    local TAG=$(printf "frame_%s_open%s" "$VAR" "$OPEN")
    GRIPPER_CANISTER_VARIANT=$VAR GRIPPER_CANISTER_SERVO=$SERVO GRIPPER_OPEN=$OPEN \
        $STEPCLI $SYS -o motor/cad/output/${TAG}.step --mesh-tolerance $MESHTOL >/dev/null 2>&1
    echo "  built $TAG"
}
export -f build_step
export STEPCLI SYS SERVO MESHTOL

# Three poses × two variants (unibody + xray) = 6 STEPs, 3 cores -> ~7 min wall.
echo "[building 6 keyframe STEPs in parallel — ~7 min wall]"
printf "T2_UNIBODY,0\nT2_UNIBODY,0.5\nT2_UNIBODY,1\nT2_XRAY,0\nT2_XRAY,0.5\nT2_XRAY,1\n" | xargs -P 3 -I{} bash -c 'build_step "$@"' _ {}

echo "[heroes]"
$SNAP --input motor/cad/output/frame_T2_UNIBODY_open1.step   --output renders/gripper_hero_open.png   --mode view --camera iso --theme technical --size-profile assembly-large >/dev/null
$SNAP --input motor/cad/output/frame_T2_UNIBODY_open0.step   --output renders/gripper_hero_closed.png --mode view --camera iso --theme technical --size-profile assembly-large >/dev/null
cp -f "$RENDER_VIEWER_ROOT/renders/gripper_hero_open.png"   renders/ 2>/dev/null || true
cp -f "$RENDER_VIEWER_ROOT/renders/gripper_hero_closed.png" renders/ 2>/dev/null || true
echo "  hero_open + hero_closed"

# Ping-pong frame schedule for the GIF: 0 → 0.5 → 1 → 0.5 → 0
GIF_FRAMES="0 0.5 1 0.5 0"

# ---- motion GIF (T2, opaque canister) ----------------------------------
echo "[motion gif frames]"
n=0
for OPEN in $GIF_FRAMES; do
    OUT=$(printf "f_%03d.png" $n)
    $SNAP --input motor/cad/output/frame_T2_UNIBODY_open${OPEN}.step --output "$OUT" --mode view --camera iso --theme technical --width 1000 --height 750 >/dev/null
    cp -f "$RENDER_VIEWER_ROOT/$OUT" "$FRAMES_DIR/$OUT"
    n=$((n+1))
done
ffmpeg -y -framerate 4 -i "$FRAMES_DIR/f_%03d.png" \
    -vf "split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=5" \
    -loop 0 renders/gripper_motion.gif >/dev/null 2>&1
echo "  motion.gif ($n frames @ 4fps)"

# ---- xray PNG + GIF (T2_XRAY: same assembly but acrylic tube OMITTED) --
echo "[xray PNG]"
$SNAP --input motor/cad/output/frame_T2_XRAY_open0.5.step --output renders/gripper_xray.png \
      --mode view --camera iso --theme technical --size-profile assembly-large >/dev/null
cp -f "$RENDER_VIEWER_ROOT/renders/gripper_xray.png" renders/ 2>/dev/null || true
echo "  xray.png"

echo "[xray gif frames]"
n=0
for OPEN in $GIF_FRAMES; do
    OUT_PNG=$(printf "x_%03d.png" $n)
    $SNAP --input motor/cad/output/frame_T2_XRAY_open${OPEN}.step --output "$OUT_PNG" \
          --mode view --camera iso --theme technical --width 1000 --height 750 >/dev/null
    cp -f "$RENDER_VIEWER_ROOT/$OUT_PNG" "$FRAMES_DIR/$OUT_PNG" 2>/dev/null
    n=$((n+1))
done
ffmpeg -y -framerate 4 -i "$FRAMES_DIR/x_%03d.png" \
    -vf "split[a][b];[a]palettegen=stats_mode=full[p];[b][p]paletteuse=dither=bayer:bayer_scale=5" \
    -loop 0 renders/gripper_xray.gif >/dev/null 2>&1
echo "  xray.gif"
echo "RENDER_DONE"

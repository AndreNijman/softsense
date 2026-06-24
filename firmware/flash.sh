#!/usr/bin/env bash
# Build + flash the gripper firmware to the Waveshare General Driver board.
# Plug the board into this laptop via the ESP32 USB-C port, then:  ./flash.sh
#
# Needs PlatformIO core. If `pio` isn't found this installs it with pipx.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

if ! command -v pio >/dev/null 2>&1; then
  echo ">> PlatformIO not found — installing with pipx"
  pipx install platformio
  export PATH="$HOME/.local/bin:$PATH"
fi

PORT="${1:-}"
ARGS=()
if [ -n "$PORT" ]; then ARGS+=(--upload-port "$PORT"); fi

echo ">> building + uploading (general_driver / esp32dev)"
pio run -t upload "${ARGS[@]}"

echo
echo ">> done. The board reboots into Wi-Fi 'Gripper' (pass gripper1234)."
echo ">> Join it and open http://192.168.4.1/  —  serial log: pio device monitor"

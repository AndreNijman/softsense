#!/usr/bin/env bash
# Serve the DualSense control page from localhost. localhost is a "secure
# context", so the browser Gamepad API works here -- it is BLOCKED on the
# board's plain-http IP (http://192.168.4.1), which is why this exists.
#
# Steps:
#   1. Join the board's Wi-Fi 'Gripper' (so the page can reach the board).
#   2. Plug the DualSense into THIS laptop (USB-C) or pair it over the laptop's
#      Bluetooth.  (It does NOT plug into the driver board.)
#   3. ./serve.sh   then open the printed URL and press a controller button.
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT="${1:-8080}"
echo ">> Gripper DualSense page:  http://localhost:$PORT/"
echo ">> (default board URL http://192.168.4.1 for the ESP32; use http://192.168.7.2 for the Orange Pi)"
exec python3 -m http.server "$PORT" --directory "$HERE"

#!/usr/bin/env bash
# Push new web-app code to the Orange Pi over the wired link and restart it.
#
# Plug the OPi into this laptop with an Ethernet cable, then run:  ./deploy.sh
# The OPi is 192.168.7.2; this brings the laptop's NIC up as 192.168.7.1,
# rsyncs opi/app/ -> /opt/gripper, and restarts the service. The device's
# calibrated config.json is preserved (never overwritten by a deploy).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
OPI_IP=192.168.7.2
LAPTOP_IP=192.168.7.1
SSH="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"

IFACE="${ETH_IFACE:-$(ip -o link show 2>/dev/null | awk -F': ' '$2 ~ /^(en|eth)/ {print $2; exit}')}"
[ -n "$IFACE" ] || { echo "No ethernet interface found; set ETH_IFACE=..."; exit 1; }
echo ">> using laptop interface: $IFACE"

if ! ip -4 addr show "$IFACE" | grep -q "$LAPTOP_IP"; then
  echo ">> assigning $LAPTOP_IP/24 to $IFACE (sudo)"
  sudo ip addr add "$LAPTOP_IP/24" dev "$IFACE" 2>/dev/null || true
fi
sudo ip link set "$IFACE" up

echo ">> waiting for $OPI_IP ..."
for _ in $(seq 1 60); do
  ping -c1 -W1 "$OPI_IP" >/dev/null 2>&1 && break; sleep 1
done
ping -c1 -W1 "$OPI_IP" >/dev/null 2>&1 || { echo "OPi not reachable at $OPI_IP"; exit 1; }

echo ">> syncing app/ -> root@$OPI_IP:/opt/gripper"
rsync -az --delete --exclude='config.json' --exclude='__pycache__' \
      -e "$SSH" "$HERE/app/" "root@$OPI_IP:/opt/gripper/"

echo ">> restarting gripper-web"
$SSH "root@$OPI_IP" 'systemctl restart gripper-web && systemctl is-active gripper-web'
echo ">> done. Control UI: http://10.42.0.1/ (Wi-Fi 'Gripper')"

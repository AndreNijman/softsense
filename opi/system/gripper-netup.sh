#!/bin/sh
# Bring the wired deploy/control link up with a fixed static IP, independent of
# NetworkManager / systemd-networkd. Idempotent (ip addr replace). The Gripper
# appliance is reached at http://192.168.7.2/ over this cable; the laptop side
# is 192.168.7.1 (deploy.sh sets that automatically).
#
# Auto-detects the first wired interface (eth0 on the Orange Pi PC's H3 EMAC,
# but tolerant of en*/end* naming on other boards).
set -e

IFACE=""
for d in /sys/class/net/*; do
  n=$(basename "$d")
  case "$n" in
    eth*|en*|end*) IFACE="$n"; break;;
  esac
done
[ -n "$IFACE" ] || IFACE=eth0

ip link set "$IFACE" up || true
ip addr replace 192.168.7.2/24 dev "$IFACE"

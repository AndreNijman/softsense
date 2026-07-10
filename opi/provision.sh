#!/usr/bin/env bash
# Provision (overwrite) an already-Armbian SD card into the Gripper appliance:
# Wi-Fi AP + captive web control for the Feetech servo, plus a wired deploy
# link. Run on the laptop with the card's rootfs mounted. Uses qemu-user +
# chroot to apt-install hostapd/dnsmasq into the arm64 rootfs offline-for-later.
#
#   sudo-capable user, card mounted at /run/media/$USER/armbi_root
#   ./provision.sh [ROOTFS_MOUNT]
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
R="${1:-/run/media/$USER/armbi_root}"
SSH_PUBKEY="${SSH_PUBKEY:-$HOME/.ssh/id_ed25519.pub}"
QEMU=/usr/bin/qemu-aarch64-static

red(){ printf '\033[31m%s\033[0m\n' "$*"; }
say(){ printf '\033[36m>> %s\033[0m\n' "$*"; }

# --- sanity ------------------------------------------------------------------
[ -d "$R" ]                     || { red "rootfs not mounted at $R"; exit 1; }
sudo test -f "$R/etc/armbian-release" || { red "$R is not an Armbian rootfs"; exit 1; }
[ -f "$QEMU" ]                  || { red "missing $QEMU (qemu-user-static)"; exit 1; }
[ -f "$SSH_PUBKEY" ]            || { red "missing ssh pubkey $SSH_PUBKEY"; exit 1; }
[ -d "$HERE/app/vendor/serial" ]|| { red "pyserial not vendored (opi/app/vendor/serial)"; exit 1; }
say "target rootfs: $R"

# --- cleanup trap ------------------------------------------------------------
cleanup(){
  set +e
  for m in dev/pts dev proc sys; do sudo umount -l "$R/$m" 2>/dev/null; done
  sudo rm -f "$R/usr/sbin/policy-rc.d" "$R/usr/bin/qemu-aarch64-static"
  if [ -e "$R/etc/resolv.conf.provbak" ] || [ -L "$R/etc/resolv.conf.provbak" ]; then
    sudo rm -f "$R/etc/resolv.conf"
    sudo mv "$R/etc/resolv.conf.provbak" "$R/etc/resolv.conf"
  fi
}
trap cleanup EXIT

# --- qemu binfmt -------------------------------------------------------------
if [ ! -e /proc/sys/fs/binfmt_misc/qemu-aarch64 ]; then
  say "registering qemu-aarch64 binfmt"
  sudo sh -c 'echo ":qemu-aarch64:M::\x7f\x45\x4c\x46\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\xb7\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:/usr/bin/qemu-aarch64-static:OCF" > /proc/sys/fs/binfmt_misc/register'
fi

# --- chroot prep -------------------------------------------------------------
say "preparing chroot"
sudo cp "$QEMU" "$R/usr/bin/"
if [ -e "$R/etc/resolv.conf" ] || [ -L "$R/etc/resolv.conf" ]; then
  sudo mv "$R/etc/resolv.conf" "$R/etc/resolv.conf.provbak"
fi
printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' | sudo tee "$R/etc/resolv.conf" >/dev/null
for m in proc sys dev dev/pts; do sudo mount --bind "/$m" "$R/$m"; done
printf '#!/bin/sh\nexit 101\n' | sudo tee "$R/usr/sbin/policy-rc.d" >/dev/null
sudo chmod +x "$R/usr/sbin/policy-rc.d"

# --- install AP packages -----------------------------------------------------
say "apt-get install hostapd dnsmasq (emulated; takes a minute)"
sudo chroot "$R" /bin/bash -c '
  set -e
  export DEBIAN_FRONTEND=noninteractive
  apt-get update
  apt-get install -y --no-install-recommends hostapd dnsmasq
'

# --- lay down config + app ---------------------------------------------------
say "installing appliance config + app"
sudo install -Dm644 "$HERE/system/hostapd.conf"                    "$R/etc/hostapd/hostapd.conf"
sudo install -Dm644 "$HERE/system/default-hostapd"                 "$R/etc/default/hostapd"
sudo install -Dm644 "$HERE/system/dnsmasq-gripper.conf"           "$R/etc/dnsmasq.d/gripper.conf"
sudo install -Dm644 "$HERE/system/systemd-networkd/08-wlan-ap.network" "$R/etc/systemd/network/08-wlan-ap.network"
sudo install -Dm644 "$HERE/system/systemd-networkd/10-eth.network"     "$R/etc/systemd/network/10-eth.network"
sudo install -Dm644 "$HERE/system/gripper-web.service"            "$R/etc/systemd/system/gripper-web.service"
sudo install -Dm644 "$HERE/system/99-feetech.rules"              "$R/etc/udev/rules.d/99-feetech.rules"

sudo rm -rf "$R/opt/gripper"
sudo mkdir -p "$R/opt/gripper"
sudo cp -r "$HERE/app/." "$R/opt/gripper/"
sudo find "$R/opt/gripper" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true

# ssh key for passwordless deploy from this laptop
say "installing ssh deploy key"
sudo mkdir -p "$R/root/.ssh"
sudo cp "$SSH_PUBKEY" "$R/root/.ssh/authorized_keys"
sudo chmod 700 "$R/root/.ssh"; sudo chmod 600 "$R/root/.ssh/authorized_keys"
sudo chown -R 0:0 "$R/root/.ssh"

# --- wipe the donor image's leftovers -----------------------------------------
# PRIOR_USER: the first-boot user account that exists on the donor Armbian image.
PRIOR_USER="${PRIOR_USER:-andre}"
say "removing prior config (saved Wi-Fi profiles / firstboot / $PRIOR_USER)"
sudo rm -f  "$R/etc/NetworkManager/system-connections/"*.nmconnection
sudo rm -f  "$R/root/firstboot.sh" "$R/root/authorized_keys"
sudo rm -f  "$R/etc/systemd/system/firstboot.service" "$R/var/lib/firstboot.done"
sudo rm -f  "$R/etc/sudoers.d/"*-nopasswd

# --- system identity + services (in chroot) ----------------------------------
say "setting hostname/password, removing $PRIOR_USER, enabling services"
sudo chroot "$R" /bin/bash -c '
  set -e
  export DEBIAN_FRONTEND=noninteractive
  echo gripper > /etc/hostname
  sed -i "/127.0.1.1/d" /etc/hosts
  echo "127.0.1.1 gripper" >> /etc/hosts
  echo "root:gripper" | chpasswd
  userdel -rf '"$PRIOR_USER"' 2>/dev/null || true
  systemctl unmask hostapd 2>/dev/null || true
  systemctl enable hostapd dnsmasq gripper-web systemd-networkd ssh 2>/dev/null || true
  systemctl mask wpa_supplicant systemd-networkd-wait-online 2>/dev/null || true
'
sudo rm -rf "$R/home/$PRIOR_USER"

# --- verify/repair the enable symlinks (chroot systemctl can be flaky) -------
say "verifying service enablement"
WANTS="$R/etc/systemd/system/multi-user.target.wants"
sudo mkdir -p "$WANTS"
ensure_enabled(){
  local unit="$1"
  [ -e "$WANTS/$unit" ] && return 0
  local src
  src=$(sudo find "$R/usr/lib/systemd/system" "$R/lib/systemd/system" "$R/etc/systemd/system" \
        -maxdepth 1 -name "$unit" 2>/dev/null | head -1)
  if [ -n "$src" ]; then
    sudo ln -sf "${src#$R}" "$WANTS/$unit"
    echo "   linked $unit"
  else
    red "   WARN: unit $unit not found to enable"
  fi
}
# hostapd ships masked (symlink to /dev/null in /etc) -> drop that first
if [ -L "$R/etc/systemd/system/hostapd.service" ] && \
   [ "$(readlink "$R/etc/systemd/system/hostapd.service")" = "/dev/null" ]; then
  sudo rm -f "$R/etc/systemd/system/hostapd.service"
fi
for u in hostapd.service dnsmasq.service gripper-web.service; do ensure_enabled "$u"; done

say "syncing to card"
sync
say "DONE. Eject the card and boot the Orange Pi."

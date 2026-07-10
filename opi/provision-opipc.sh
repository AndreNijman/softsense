#!/usr/bin/env bash
# Provision (overwrite) an already-Armbian Orange Pi PC (Allwinner H3, 32-bit
# armhf) SD card into the Gripper appliance in ETHERNET-ONLY mode.
#
# The OPi PC has NO onboard Wi-Fi, so unlike the OPi 3 LTS build (provision.sh)
# this does NOT bring up a Wi-Fi AP. Instead the web UI is served over the wired
# port at a fixed static IP (192.168.7.2) -- the same link used to deploy code.
# Browse http://192.168.7.2/ from the laptop (which deploy.sh puts on .1).
#
# When a USB Wi-Fi dongle arrives, the AP config files are staged on the card
# already -- see opi/ENABLE_AP_LATER.md.
#
# Run on the laptop with the card's rootfs mounted (read-write):
#   sudo mount /dev/sdX1 /mnt/opicard
#   ./provision-opipc.sh /mnt/opicard
#
# Uses qemu-arm-static (armhf) ONLY for the two identity ops (chpasswd, userdel);
# everything else is plain file/symlink manipulation. No apt, no network needed.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
R="${1:-/mnt/opicard}"
SSH_PUBKEY="${SSH_PUBKEY:-$HOME/.ssh/id_ed25519.pub}"
QEMU=/usr/bin/qemu-arm-static

red(){ printf '\033[31m%s\033[0m\n' "$*"; }
say(){ printf '\033[36m>> %s\033[0m\n' "$*"; }

# --- sanity ------------------------------------------------------------------
[ -d "$R" ]                          || { red "rootfs not mounted at $R"; exit 1; }
sudo test -f "$R/etc/armbian-release"|| { red "$R is not an Armbian rootfs"; exit 1; }
BOARD=$(sudo sed -n 's/^BOARD=//p' "$R/etc/armbian-release")
ARCH=$(sudo sed -n 's/^ARCH=//p'   "$R/etc/armbian-release")
say "card board=$BOARD arch=$ARCH"
[ "$ARCH" = "arm" ] || red "WARNING: expected 32-bit arm, got '$ARCH' -- check the board"
[ -f "$QEMU" ]                       || { red "missing $QEMU (qemu-user-static armhf)"; exit 1; }
[ -f "$SSH_PUBKEY" ]                 || { red "missing ssh pubkey $SSH_PUBKEY"; exit 1; }
[ -d "$HERE/app/vendor/serial" ]     || { red "pyserial not vendored (opi/app/vendor/serial)"; exit 1; }
sudo test -w "$R" || { red "$R is mounted read-only -- remount rw"; exit 1; }

# --- cleanup trap (qemu chroot binds) ----------------------------------------
cleanup(){
  set +e
  for m in dev/pts dev proc sys; do sudo umount -l "$R/$m" 2>/dev/null; done
  sudo rm -f "$R/usr/bin/qemu-arm-static"
}
trap cleanup EXIT

# --- app ---------------------------------------------------------------------
say "installing app -> /opt/gripper"
sudo rm -rf "$R/opt/gripper"
sudo mkdir -p "$R/opt/gripper"
sudo cp -r "$HERE/app/." "$R/opt/gripper/"
sudo find "$R/opt/gripper" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
# staged AP-enabler doc + script for dongle-day
sudo install -Dm644 "$HERE/ENABLE_AP_LATER.md" "$R/opt/gripper/ENABLE_AP_LATER.md" 2>/dev/null || true

# --- units + udev + wired-link script ----------------------------------------
say "installing services, udev rule, wired-link bringup"
sudo install -Dm644 "$HERE/system/gripper-web.service" "$R/etc/systemd/system/gripper-web.service"
sudo install -Dm644 "$HERE/system/gripper-net.service" "$R/etc/systemd/system/gripper-net.service"
sudo install -Dm755 "$HERE/system/gripper-netup.sh"    "$R/usr/local/sbin/gripper-netup.sh"
sudo install -Dm644 "$HERE/system/99-feetech.rules"    "$R/etc/udev/rules.d/99-feetech.rules"

# stage (DISABLED) AP config for when a USB Wi-Fi dongle is added later
say "staging (disabled) AP config for dongle-day"
sudo install -Dm644 "$HERE/system/hostapd.conf"        "$R/etc/hostapd/hostapd.conf"
sudo install -Dm644 "$HERE/system/default-hostapd"     "$R/etc/default/hostapd"
sudo install -Dm644 "$HERE/system/dnsmasq-gripper.conf" "$R/etc/dnsmasq.d/gripper.conf"

# --- ssh deploy key ----------------------------------------------------------
say "installing ssh deploy key + enabling root key login"
sudo mkdir -p "$R/root/.ssh"
sudo cp "$SSH_PUBKEY" "$R/root/.ssh/authorized_keys"
sudo chmod 700 "$R/root/.ssh"; sudo chmod 600 "$R/root/.ssh/authorized_keys"
sudo chown -R 0:0 "$R/root/.ssh"
sudo mkdir -p "$R/etc/ssh/sshd_config.d"
sudo tee "$R/etc/ssh/sshd_config.d/gripper.conf" >/dev/null <<'EOF'
# Gripper appliance: allow key-only root login for deploy.sh over the wired link
PermitRootLogin prohibit-password
PubkeyAuthentication yes
EOF
sudo chmod 644 "$R/etc/ssh/sshd_config.d/gripper.conf"
# Focal's sshd may not Include sshd_config.d -> also set it directly, idempotently
if ! sudo grep -q '^Include /etc/ssh/sshd_config.d' "$R/etc/ssh/sshd_config" 2>/dev/null; then
  sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin prohibit-password/' "$R/etc/ssh/sshd_config"
  sudo grep -q '^PermitRootLogin' "$R/etc/ssh/sshd_config" || \
    echo 'PermitRootLogin prohibit-password' | sudo tee -a "$R/etc/ssh/sshd_config" >/dev/null
fi

# --- identity (hostname) -----------------------------------------------------
say "hostname -> gripper"
echo gripper | sudo tee "$R/etc/hostname" >/dev/null
sudo sed -i '/127.0.1.1/d' "$R/etc/hosts"
echo "127.0.1.1 gripper" | sudo tee -a "$R/etc/hosts" >/dev/null

# --- enable our services, disable/mask the rest (symlinks, robust) -----------
say "enabling gripper services; masking Wi-Fi/NM/octoprint/openvpn"
WANTS="$R/etc/systemd/system/multi-user.target.wants"
sudo mkdir -p "$WANTS"
enable_unit(){ # unit lives in /etc/systemd/system here
  sudo ln -sf "/etc/systemd/system/$1" "$WANTS/$1"; echo "   enabled $1"
}
enable_unit gripper-web.service
enable_unit gripper-net.service
# ssh stays enabled (already is). Mask things that fight us or waste the 1GB box.
for u in NetworkManager.service NetworkManager-wait-online.service \
         wpa_supplicant.service octoprint.service openvpn.service \
         systemd-networkd-wait-online.service; do
  sudo ln -sf /dev/null "$R/etc/systemd/system/$u"
  sudo rm -f "$WANTS/$u"
  echo "   masked $u"
done
# networking.service (ifupdown) is harmless (only lo) -- leave it.

# --- qemu chroot: password + remove prior owner ------------------------------
if [ ! -e /proc/sys/fs/binfmt_misc/qemu-arm ]; then
  say "registering qemu-arm binfmt"
  sudo sh -c 'echo ":qemu-arm:M::\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00:\xff\xff\xff\xff\xff\xff\xff\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff:/usr/bin/qemu-arm-static:OCF" > /proc/sys/fs/binfmt_misc/register' \
    || red "binfmt register failed (continuing; identity ops may be skipped)"
fi
sudo cp "$QEMU" "$R/usr/bin/"
for m in proc sys dev dev/pts; do sudo mount --bind "/$m" "$R/$m"; done
say "setting root password + removing prior owner 'marco' (chroot)"
sudo chroot "$R" /bin/bash -c '
  set -e
  echo "root:gripper" | chpasswd
  userdel -rf marco 2>/dev/null || true
  groupdel marco    2>/dev/null || true
' || red "chroot identity step failed -- root pw / marco removal may be incomplete"
sudo rm -rf "$R/home/marco"

# --- remove octoprint/openvpn leftover bulk (optional tidy) ------------------
say "tidying prior-owner data"
sudo rm -rf "$R/home/marco" "$R/root/.octoprint" 2>/dev/null || true

say "syncing"
sync
say "DONE. Eject, put the card in the Orange Pi PC, plug Ethernet into the laptop, boot."
say "Then on the laptop:  cd opi && ./deploy.sh   (or just browse http://192.168.7.2/ )"

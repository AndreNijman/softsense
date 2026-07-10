# Gripper controller — Orange Pi 3 LTS appliance

A self-contained, **offline** controller for the gripper's Feetech servo. The
Orange Pi boots straight into a Wi-Fi access point; you join it from your phone,
open a web page, and get OPEN / CLOSE buttons (plus manual positioning and
calibration). The Pi is **never on a real network** — the only time it changes
is when you plug it into the dev laptop over Ethernet and push new code.

## How you use it

1. Power the Pi. After ~30 s it broadcasts Wi-Fi **`Gripper`** (password
   **`gripper1234`**).
2. Join that Wi-Fi on your phone. A "sign in to network" page should pop up
   automatically (captive portal). If not, open **http://10.42.0.1/**.
3. Tap **OPEN** / **CLOSE**. Live position / load / voltage / temperature show
   under the buttons.

### Calibrating open & close
The shipped open/close positions (1024 / 3072 of 0–4095) are placeholders.
To set them to your gripper's real endpoints:
1. Toggle **Torque** off, hand-move the gripper (or use the slider with torque on).
2. Drive it to the fully-open pose, tap **Set current as OPEN**.
3. Drive it to the fully-closed pose, tap **Set current as CLOSE**.
Saved to `config.json` on the Pi; survives reboots and future deploys.

## Hardware

- **Board:** Orange Pi 3 LTS (Allwinner H6), Armbian (Debian trixie).
- **Servo:** Feetech **STS3250** (STS3215 also works) on the SCS-TTL bus.
- **Adapter:** Feetech **FE-URT-1** (CH340 USB-serial) → the Pi's USB port,
  enumerates as `/dev/ttyUSB0` (also symlinked `/dev/feetech`), 1,000,000 baud.
- **Power:** 12 V to the URT-1 screw terminal / servo rail (separate from the
  Pi's 5 V supply). The servo ID is **1** (Feetech factory default).

## Networking (fixed by design)

| Interface | Role | Address |
|-----------|------|---------|
| `wlan0`   | Wi-Fi AP (hostapd + dnsmasq) | `10.42.0.1/24`, DHCP `.10–.200` |
| `eth0`/`end0` | Wired deploy link to laptop | `192.168.7.2/24` |

No internet, no routing, no upstream DNS — all DNS resolves to the Pi so the
captive portal works.

## Deploying new app code

Edit anything under `opi/app/`, then plug the Pi into this laptop with an
Ethernet cable and run:

```bash
opi/deploy.sh
```

It sets the laptop NIC to `192.168.7.1`, rsyncs `app/` → `/opt/gripper`, and
restarts `gripper-web`. Your on-device `config.json` (calibration) is preserved.
SSH is `root@192.168.7.2`, key-only from this laptop (console password `gripper`).

## (Re)flashing the whole appliance

With a card that already has Armbian for this board, mounted at
`/run/media/$USER/armbi_root`:

```bash
opi/provision.sh
```

This wipes the prior owner's config, installs hostapd/dnsmasq (via qemu-chroot),
lays down the AP + web app + deploy link + this laptop's SSH key, sets the
hostname to `gripper`, and enables everything. Eject and boot.

## Layout

```
opi/
  app/                 # what runs on the Pi, lives in /opt/gripper
    server.py          # stdlib HTTP control server on :80
    servo.py           # Feetech STS protocol driver (pure Python)
    index.html         # mobile control UI
    config.json        # port/baud/id + open/close/speed/acc (calibratable)
    vendor/serial/     # vendored pyserial (no pip on the offline Pi)
  system/              # OS config installed into the rootfs
    hostapd.conf  dnsmasq-gripper.conf  default-hostapd
    systemd-networkd/  gripper-web.service  99-feetech.rules
  provision.sh         # one-shot: turn an Armbian card into this appliance
  deploy.sh            # push app code over the wired link
```

## Troubleshooting

- **No `/dev/ttyUSB0`:** the CH340 can be grabbed by `brltty` (not installed
  here) or ModemManager. The udev rule sets `ID_MM_DEVICE_IGNORE`. Re-plug the
  URT-1 and check `dmesg | tail`.
- **UI loads but "servo not found":** the web app runs fine without the servo.
  Check 12 V power, the 3-pin lead, and that the servo ID is 1
  (`/api/status` reports `connected:false` until it answers).
- **Wi-Fi doesn't appear:** `systemctl status hostapd` over the wired link.
- **STS vs SCS:** this driver speaks the little-endian STS/SMS protocol
  (STS3215/3250). SCS-series servos use big-endian and need a tweak.

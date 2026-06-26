# Enabling the Wi-Fi AP later (Orange Pi PC + USB Wi-Fi dongle)

The Orange Pi PC (Allwinner H3) has **no onboard Wi-Fi**, so the appliance was
provisioned in **Ethernet-only** mode (`provision-opipc.sh`): the web UI is served
over the wired port at `http://192.168.7.2/`.

When you get a USB Wi-Fi dongle that supports **AP mode** (nl80211 / `iw` shows
`AP` under "Supported interface modes" -- e.g. RTL8188EUS, RT5370, MT7601U), the
AP config files are already on the card (staged, disabled):

- `/etc/hostapd/hostapd.conf`        -- SSID `Gripper`, WPA2 `gripper1234`, ch6 2.4GHz
- `/etc/default/hostapd`             -- points at the conf
- `/etc/dnsmasq.d/gripper.conf`      -- captive-portal DHCP/DNS on `wlan0` (10.42.0.1)

`hostapd` is already installed; **`dnsmasq` is not** (not needed for wired).

## Dongle-day steps (over the wired deploy link, with internet shared from laptop)

1. Plug the dongle in; confirm it enumerates and supports AP:
   ```sh
   ip link            # note the new wlanN name
   iw list | grep -A8 "Supported interface modes"   # must list "* AP"
   ```
2. Install dnsmasq (needs internet -- share the laptop's connection over the
   wired link, or temporarily put the Pi on a network):
   ```sh
   apt-get update && apt-get install -y --no-install-recommends dnsmasq
   ```
3. Give `wlan0` its AP address + enable the services:
   ```sh
   ip addr replace 10.42.0.1/24 dev wlan0
   systemctl unmask hostapd 2>/dev/null || true
   systemctl enable --now hostapd dnsmasq
   ```
   (If the dongle came up as `wlan1`, edit the `interface=` line in
   `hostapd.conf` and `dnsmasq.d/gripper.conf` first.)
4. Join Wi-Fi `Gripper` / `gripper1234` from a phone; the captive portal pops the
   control UI. The wired link keeps working in parallel for deploys.

The full AP-native build (for the OPi 3 LTS, which *does* have onboard Wi-Fi) is
`provision.sh` in this directory -- use that as the reference for the AP path.

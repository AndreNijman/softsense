# DualSense control for the gripper

Control the gripper with a PlayStation DualSense (or DualShock 4). The controller
connects to **your laptop** — a laptop-side bridge reads it and sends commands to
the board over Wi-Fi.

## Why it can't plug into the board

- **The driver board's USB-C port can't read a controller.** It's an ESP32-WROOM-32
  (no USB-host hardware at all) and that port is just a **CP2102 UART bridge** for
  flashing. A gamepad is a USB *host* job the board can't do.
- **A page served *from* the board can't read the gamepad either.** Browsers gate the
  Gamepad API behind a **secure context**; on the board's plain-http IP
  `navigator.getGamepads()` returns nothing. It only works from **`http://localhost`**
  (or https).

So the controller plugs into the **laptop** (USB-C cable, or the laptop's Bluetooth),
and the laptop relays to the board. Two ways to do that:

## Option A — browser page (recommended)

```bash
./serve.sh                 # serves the page from http://localhost:8080
```
1. Join the board's Wi-Fi **`Gripper`** (so the page can reach `192.168.4.1`).
2. Plug the DualSense into the laptop (USB) or pair it over the laptop's Bluetooth.
3. Open **http://localhost:8080/**, set the Board URL (`192.168.4.1` ESP32 /
   `192.168.7.2` Orange Pi), and **press any controller button** to activate it
   (browsers require one button press first).

Uses the browser's normalized "standard" gamepad mapping, so it's consistent across
USB and Bluetooth. Shows live position/load and a debug readout.

## Option B — native bridge (no browser)

```bash
python3 bridge.py                    # ESP32 (192.168.4.1)
python3 bridge.py --host 192.168.7.2 # Orange Pi over Ethernet
python3 bridge.py --debug            # print raw button/axis numbers to remap
```
Pure standard library (reads `/dev/input/js0`). Fewer steps, but the raw
button/axis numbers vary by USB vs Bluetooth and kernel — run `--debug` once, press
each control, and if they don't match, edit the `BTN_*` / `AXIS_*` constants at the
top of `bridge.py`.

## Controls

| Input | Action |
|-------|--------|
| **R2** (right trigger) | proportional grip — release = open, squeeze = close |
| **Left stick ↕** | fine jog (when R2 released) |
| **✕ Cross** | Open |
| **◯ Circle** | Close (uses stop-on-load if enabled) |
| **L1** | STOP — brake & hold |
| **□ Square** | Torque on (bridge) / toggle Torque (web) |
| **△ Triangle** | Stop-on-load on (bridge) / toggle (web) |

Live trigger control uses **`/api/jog`** (a raw, non-blocking move) so streaming stays
responsive even with stop-on-load enabled; the **Circle** button uses the guarded
`/api/close` so a deliberate grip still contact-stops.

## Firmware requirement

Needs the board firmware with the `/api/jog` endpoint and the `Access-Control-Allow-Origin`
header (added alongside this). Reflash with `firmware/flash.sh`. Without it, live jog and
the browser page's live readout won't work (buttons still would, via no-CORS).

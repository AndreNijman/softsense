# Gripper controller — ESP32 firmware

Firmware for the **Waveshare General Driver for Robots** (ESP32-WROOM-32,
Core Electronics WS-23730). The board boots into its own Wi-Fi access point;
you join it from your phone, open a web page, and get OPEN / CLOSE buttons for
the Feetech servo. **Fully offline** — no router, no internet.

This replaces the fried Orange Pi controller: the ESP32 *is* the AP, the web
server, and the servo bus master, all in one board.

## How you use it

1. Power the board from **~12 V (3S)** via the XH2.54 DC input (the bus servo
   power comes from this rail — a 12 V STS3250 wants ~12 V).
2. It broadcasts Wi-Fi **`Gripper`** / password **`gripper1234`** (published
   defaults — change `AP_SSID`/`AP_PASS` in `src/main.cpp` before flashing if
   that matters for your build).
3. Join it on your phone → a captive "sign in" page pops up (or open
   **http://192.168.4.1/**).
4. Tap **OPEN** / **CLOSE**. Live position / load / voltage / temp show below;
   a 0.91" OLED on the board mirrors the SSID, IP, and position.

### Calibrate open & close
The shipped open/close positions (1024 / 3072 of 0–4095) are placeholders.
1. Turn **Torque** off (or use the slider with torque on) and move the gripper.
2. At the fully-open pose tap **Set current as OPEN**; at fully-closed tap
   **Set current as CLOSE**. Saved to the ESP32's flash (NVS); survives reboots.

## Wiring the servo

The Feetech **STS3250** (or STS3215) plugs **straight into the board's ST3215
bus servo port** with a 3-pin cable — no FE-URT-1 adapter. The board provides
both the half-duplex data line and servo power from the DC input.

- Bus servo UART: **GPIO18 (RXD) / GPIO19 (TXD)**, **1,000,000 baud**, servo
  **ID 1** (Feetech factory default).
- ⚠️ Before powering up, check the 3-pin connector orientation
  (**GND / VCC / signal**) matches between the servo cable and the board port —
  reversed power can damage the servo.
- ⚠️ Match the supply voltage to the servo (12 V servo → ~12 V / 3S; a 7.4 V
  STS3215 variant → ~7.4 V, **not** 3S).

## Flashing (do this when the board arrives)

Connect the board to this laptop with **USB-C** (the ESP32 port — the one wired
to the CP2102 that talks to the ESP32), then:

```bash
firmware/flash.sh            # auto-installs PlatformIO via pipx if missing
# or, manually:
cd firmware && pio run -t upload
pio device monitor           # 115200 — see the boot log
```

`board = esp32dev` (ESP32-WROOM-32) is already set in `platformio.ini`. If
upload fails to auto-reset, hold **BOOT**, tap **EN/RST**, release **BOOT**, and
re-run. Pass an explicit port with `firmware/flash.sh /dev/ttyUSB0`.

### Arduino IDE alternative
1. Install the **esp32** boards package (Boards Manager).
2. Copy `firmware/lib/SCServo` into your Arduino `libraries/` folder; install
   **Adafruit SSD1306** + **Adafruit GFX** from Library Manager.
3. Open `firmware/src/main.cpp` as a sketch (rename to `Gripper.ino` in a
   `Gripper/` folder), select **ESP32 Dev Module**, and Upload.

## What's here

```
firmware/
  platformio.ini        # build config (board, libs)
  flash.sh              # build + upload wrapper
  src/
    main.cpp            # AP + captive web server + servo control + OLED
    index_html.h        # mobile UI, embedded in flash (served at /)
  lib/SCServo/          # Feetech bus-servo library (bundled, from Waveshare)
```

## HTTP API (same shape as the old OPi controller)

| Method | Path | Action |
|--------|------|--------|
| GET  | `/api/status` | JSON: connected, position, load, voltage, temp, open/close/speed/acc |
| POST | `/api/open` · `/api/close` | move to the calibrated endpoint |
| POST | `/api/goto?pos=N` | move to raw position 0–4095 |
| POST | `/api/torque?on=0\|1` | enable/disable holding torque |
| POST | `/api/calibrate?which=open\|close` | save current position as that endpoint |
| POST | `/api/config?speed=&acc=&open=&close=` | set + persist params |

## Notes / untested until hardware boots

- Bus pins, baud, and the `SMS_STS` protocol are from Waveshare's own firmware
  for this exact board, so they should be correct out of the box.
- Open/close **directions and positions are placeholders** — calibrate on first
  run.
- The OLED is assumed 128×32 @ I²C `0x3C` on GPIO32/33. If your board's panel
  differs it just stays blank (non-fatal); set `USE_OLED 0` in `main.cpp` to drop
  the dependency entirely.
- To change the Wi-Fi name/password, edit `AP_SSID` / `AP_PASS` in `main.cpp`
  and re-flash.

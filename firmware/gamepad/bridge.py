#!/usr/bin/env python3
"""Native DualSense -> gripper bridge (Linux, pure standard library).

Reads a PlayStation controller from /dev/input/jsN and drives the gripper board
over HTTP. No browser, no pip installs -- an alternative to the localhost web
page for when you'd rather just run one command.

    join the board's Wi-Fi 'Gripper' first, plug the DualSense into THIS laptop
    (USB) or pair it over the laptop's Bluetooth, then:

        python3 bridge.py                       # ESP32 board (192.168.4.1)
        python3 bridge.py --host 192.168.7.2    # Orange Pi over Ethernet
        python3 bridge.py --debug               # print raw button/axis numbers

Controller button/axis numbers vary between USB and Bluetooth and across kernels
-- run with --debug first, press each control, and if the numbers below don't
match, edit the BTN_* / AXIS_* constants.
"""
import argparse, os, select, struct, sys, time, urllib.request

# ---- DualSense mapping via /dev/input/jsN (hid-playstation, USB defaults) -----
BTN_CROSS, BTN_CIRCLE, BTN_TRIANGLE, BTN_SQUARE, BTN_L1 = 0, 1, 2, 3, 4
AXIS_LY, AXIS_R2 = 1, 5            # left-stick Y, right trigger (analog)

JS_EVENT = struct.Struct("IhBB")  # time(u32), value(s16), type(u8), number(u8)
JS_BUTTON, JS_AXIS, JS_INIT = 0x01, 0x02, 0x80

def norm_trigger(v):  # joydev scales the trigger to -32767(released)..32767(pressed)
    return max(0.0, min(1.0, (v + 32767) / 65534.0))
def norm_stick(v):
    return max(-1.0, min(1.0, v / 32767.0))

class Board:
    def __init__(self, host):
        self.base = "http://%s" % host
        self.busy_until = 0.0
    def post(self, path):
        try:
            urllib.request.urlopen(self.base + path, data=b"", timeout=0.6).read()
        except Exception:
            pass
    def jog(self, target):                        # throttled + deadband happens in caller
        self.post("/api/jog?pos=%d" % target)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="192.168.4.1")
    ap.add_argument("--dev", default="/dev/input/js0")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--open", type=int, default=None, help="open position (else read from board)")
    ap.add_argument("--close", type=int, default=None, help="close position")
    a = ap.parse_args()

    try:
        fd = os.open(a.dev, os.O_RDONLY | os.O_NONBLOCK)
    except OSError as e:
        sys.exit("cannot open %s (%s). Plug in / pair the controller; check /dev/input/js*." % (a.dev, e))

    board = Board(a.host)
    open_p, close_p = a.open, a.close
    if open_p is None or close_p is None:         # try to read calibration from the board
        try:
            import json
            s = json.load(urllib.request.urlopen("http://%s/api/status" % a.host, timeout=1))
            open_p = open_p if open_p is not None else s.get("open_pos", 1024)
            close_p = close_p if close_p is not None else s.get("close_pos", 3072)
        except Exception:
            open_p, close_p = open_p or 1024, close_p or 3072
    print("bridge: %s  ->  %s   open=%d close=%d%s"
          % (a.dev, a.host, open_p, close_p, "   [DEBUG]" if a.debug else ""))

    axes = {}
    grip = 0.0
    last_send, last_target = 0.0, -1
    THROTTLE, DEADBAND = 0.09, 18

    while True:
        select.select([fd], [], [], 0.02)
        # drain all pending events
        while True:
            try:
                buf = os.read(fd, 8)
            except BlockingIOError:
                break
            if not buf or len(buf) < 8:
                break
            _, value, etype, number = JS_EVENT.unpack(buf)
            if etype & JS_INIT:                   # synthetic startup events
                continue
            if a.debug:
                print("%-6s num=%-2d val=%d" % ("BTN" if etype & JS_BUTTON else "AXIS", number, value))
            if etype & JS_BUTTON:
                if value != 1:                    # act on press only
                    continue
                if number == BTN_CROSS:    grip = 0.0; board.post("/api/open")
                elif number == BTN_CIRCLE: grip = 1.0; board.post("/api/close")
                elif number == BTN_L1:     board.post("/api/stop")
                elif number == BTN_SQUARE: board.post("/api/torque?on=1")   # simple: press = torque on
                elif number == BTN_TRIANGLE: board.post("/api/stop_on_load?on=1")
            elif etype & JS_AXIS:
                axes[number] = value

        # control tick (continuous while a stick/trigger is held)
        r2 = norm_trigger(axes.get(AXIS_R2, -32767))
        ly = norm_stick(axes.get(AXIS_LY, 0))
        if r2 > 0.04:
            grip = r2
        elif abs(ly) > 0.15:
            grip = min(1.0, max(0.0, grip + ly * 0.02))
        target = int(round(open_p + grip * (close_p - open_p)))
        now = time.time()
        if (r2 > 0.04 or abs(ly) > 0.15) and now - last_send >= THROTTLE and abs(target - last_target) >= DEADBAND:
            board.jog(target); last_send, last_target = now, target

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

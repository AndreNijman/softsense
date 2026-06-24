#!/usr/bin/env python3
"""Gripper web control -- minimal stdlib HTTP server for the Orange Pi appliance.

Serves a single mobile control page and a tiny JSON API that drives the Feetech
servo. No web framework: only the Python 3 standard library plus the local
servo driver (which uses vendored pyserial). Binds 0.0.0.0:80 so a phone on the
'Gripper' Wi-Fi AP can just open http://10.42.0.1/.

Any non-/api GET returns the control page -- this doubles as the captive-portal
landing page (phones probing for connectivity get the UI and pop "Sign in").
"""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "vendor"))

from servo import Servo  # noqa: E402

CONFIG_PATH = os.path.join(HERE, "config.json")
INDEX_PATH = os.path.join(HERE, "index.html")

DEFAULT_CONFIG = {
    "port": "/dev/ttyUSB0",
    "baud": 1000000,
    "servo_id": 1,
    "open_pos": 1024,
    "close_pos": 3072,
    "speed": 1500,
    "acc": 50,
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH) as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg):
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(cfg, f, indent=2)
    os.replace(tmp, CONFIG_PATH)


CFG = load_config()
SERVO = Servo(port=CFG["port"], baud=CFG["baud"], servo_id=CFG["servo_id"])


class Handler(BaseHTTPRequestHandler):
    server_version = "GripperCtl/1.0"

    # -- helpers ---------------------------------------------------------------
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _page(self):
        try:
            with open(INDEX_PATH, "rb") as f:
                body = f.read()
        except OSError:
            body = b"<h1>Gripper</h1><p>index.html missing</p>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _status(self):
        pos = SERVO.present_position()
        return {
            "connected": pos is not None,
            "position": pos,
            "load": SERVO.present_load(),
            "voltage": (SERVO.present_voltage() or 0) / 10.0,
            "temp": SERVO.present_temp(),
            "open_pos": CFG["open_pos"],
            "close_pos": CFG["close_pos"],
            "speed": CFG["speed"],
            "acc": CFG["acc"],
        }

    # -- routing ---------------------------------------------------------------
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/status":
            self._json(self._status())
        elif path.startswith("/api/"):
            self._json({"error": "use POST"}, 405)
        else:
            self._page()  # control page == captive portal landing

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        q = parse_qs(parsed.query)

        def arg(name, default=None):
            return q.get(name, [default])[0]

        if path == "/api/open":
            ok = SERVO.move(CFG["open_pos"], CFG["speed"], CFG["acc"])
            self._json({"ok": ok, "target": CFG["open_pos"]})
        elif path == "/api/close":
            ok = SERVO.move(CFG["close_pos"], CFG["speed"], CFG["acc"])
            self._json({"ok": ok, "target": CFG["close_pos"]})
        elif path == "/api/goto":
            try:
                pos = int(arg("pos"))
            except (TypeError, ValueError):
                return self._json({"error": "pos required"}, 400)
            ok = SERVO.move(pos, CFG["speed"], CFG["acc"])
            self._json({"ok": ok, "target": pos})
        elif path == "/api/torque":
            on = arg("on", "1") in ("1", "true", "on", "yes")
            self._json({"ok": SERVO.torque(on), "torque": on})
        elif path == "/api/calibrate":
            # save the servo's current position as the open or close endpoint
            which = arg("which")
            pos = SERVO.present_position()
            if which not in ("open", "close"):
                return self._json({"error": "which=open|close"}, 400)
            if pos is None:
                return self._json({"error": "servo not connected"}, 503)
            CFG[which + "_pos"] = pos
            save_config(CFG)
            self._json({"ok": True, which + "_pos": pos})
        elif path == "/api/config":
            length = int(self.headers.get("Content-Length", 0) or 0)
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
            except ValueError:
                return self._json({"error": "bad json"}, 400)
            for k in ("open_pos", "close_pos", "speed", "acc"):
                if k in data:
                    CFG[k] = int(data[k])
            save_config(CFG)
            self._json({"ok": True, "config": {k: CFG[k] for k in
                       ("open_pos", "close_pos", "speed", "acc")}})
        else:
            self._json({"error": "not found"}, 404)

    def log_message(self, *a):  # quiet
        pass


def main():
    port = int(os.environ.get("GRIPPER_HTTP_PORT", "80"))
    httpd = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"gripper web control on :{port}  (servo port {CFG['port']})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

"""Minimal, self-contained Feetech STS/SMS serial-bus servo driver.

Targets the gripper actuator: Feetech STS3250 (also works with STS3215) on the
SCS-TTL half-duplex bus, driven through an FE-URT-1 (CH340) USB adapter at
1,000,000 baud. Pure Python on top of the vendored pyserial -- no external SDK,
so it runs on the offline Orange Pi with only the system Python 3.

Protocol (Feetech "SMS/STS" series, little-endian 16-bit values):
    packet = [0xFF, 0xFF, ID, LEN, INST, *PARAMS, CHECKSUM]
    LEN      = len(PARAMS) + 2
    CHECKSUM = ~(ID + LEN + INST + sum(PARAMS)) & 0xFF
"""

import os
import glob
import threading
import time

import serial  # vendored in ./vendor

# --- SMS/STS RAM register map -------------------------------------------------
ADDR_TORQUE_ENABLE = 40
ADDR_ACC = 41
ADDR_GOAL_POSITION = 42
ADDR_GOAL_TIME = 44
ADDR_GOAL_SPEED = 46
ADDR_PRESENT_POSITION = 56
ADDR_PRESENT_SPEED = 58
ADDR_PRESENT_LOAD = 60
ADDR_PRESENT_VOLTAGE = 62
ADDR_PRESENT_TEMP = 63
ADDR_MOVING = 66
ADDR_PRESENT_CURRENT = 69

# --- instructions -------------------------------------------------------------
INST_PING = 0x01
INST_READ = 0x02
INST_WRITE = 0x03


def _decode_signed(value, sign_bit):
    """STS encodes some fields as magnitude + a direction bit (not two's comp)."""
    if value & sign_bit:
        return -(value & (sign_bit - 1))
    return value & (sign_bit - 1)


class Servo:
    """Thread-safe driver for a single Feetech STS servo on a shared bus.

    Resilient by design: if the adapter is unplugged the calls return None /
    False and the next call transparently tries to reopen the port, so the web
    UI keeps working with the servo physically absent.
    """

    def __init__(self, port="/dev/ttyUSB0", baud=1000000, servo_id=1, timeout=0.05):
        self.port = port
        self.baud = baud
        self.servo_id = servo_id
        self.timeout = timeout
        self._ser = None
        self._lock = threading.RLock()

    # -- connection ------------------------------------------------------------
    def _candidate_ports(self):
        order = []
        for p in (self.port, "/dev/feetech"):
            if p and p not in order:
                order.append(p)
        for p in sorted(glob.glob("/dev/ttyUSB*")) + sorted(glob.glob("/dev/ttyACM*")):
            if p not in order:
                order.append(p)
        return order

    def _ensure_open(self):
        if self._ser is not None and self._ser.is_open:
            return True
        for p in self._candidate_ports():
            if not os.path.exists(p):
                continue
            try:
                self._ser = serial.Serial(p, self.baud, timeout=self.timeout,
                                          write_timeout=0.2)
                self.port = p
                # let the CH340 settle
                time.sleep(0.05)
                self._ser.reset_input_buffer()
                return True
            except (serial.SerialException, OSError):
                self._ser = None
        return False

    def _close(self):
        try:
            if self._ser:
                self._ser.close()
        except Exception:
            pass
        self._ser = None

    @property
    def connected(self):
        with self._lock:
            return self.ping()

    # -- raw packet I/O --------------------------------------------------------
    def _send(self, inst, params):
        sid = self.servo_id
        length = len(params) + 2
        checksum = (~(sid + length + inst + sum(params))) & 0xFF
        pkt = bytes([0xFF, 0xFF, sid, length, inst, *params, checksum])
        self._ser.reset_input_buffer()
        self._ser.write(pkt)
        self._ser.flush()

    def _read_status(self, n_data):
        """Read a status packet, returning n_data payload bytes (or None)."""
        deadline = time.time() + 0.15
        buf = bytearray()
        want = 2 + 1 + 1 + 1 + n_data + 1  # FF FF ID LEN ERR data... CHK
        while time.time() < deadline:
            chunk = self._ser.read(want - len(buf) if want > len(buf) else 1)
            if chunk:
                buf.extend(chunk)
            # find a frame header (skip any half-duplex echo)
            i = buf.find(b"\xff\xff")
            if i >= 0 and len(buf) - i >= want:
                frame = buf[i:i + want]
                if frame[2] != self.servo_id:
                    del buf[:i + 2]
                    continue
                data = frame[5:5 + n_data]
                return bytes(data)
        return None

    # -- register access -------------------------------------------------------
    def write_reg(self, addr, data):
        with self._lock:
            if not self._ensure_open():
                return False
            try:
                self._send(INST_WRITE, [addr, *data])
                return True
            except (serial.SerialException, OSError):
                self._close()
                return False

    def read_reg(self, addr, length):
        with self._lock:
            if not self._ensure_open():
                return None
            try:
                self._send(INST_READ, [addr, length])
                return self._read_status(length)
            except (serial.SerialException, OSError):
                self._close()
                return None

    def _read_u16(self, addr):
        d = self.read_reg(addr, 2)
        if not d or len(d) < 2:
            return None
        return d[0] | (d[1] << 8)  # little-endian (STS series)

    # -- high-level API --------------------------------------------------------
    def ping(self):
        with self._lock:
            if not self._ensure_open():
                return False
            try:
                self._send(INST_PING, [])
                return self._read_status(0) is not None
            except (serial.SerialException, OSError):
                self._close()
                return False

    def torque(self, on):
        return self.write_reg(ADDR_TORQUE_ENABLE, [1 if on else 0])

    def move(self, position, speed=1500, acc=50):
        """Move to an absolute position (0-4095) with the given speed/acc.

        Writes ACC, GOAL_POSITION, GOAL_TIME(=0), GOAL_SPEED in one frame
        starting at ADDR_ACC (Feetech "WritePosEx").
        """
        position = max(0, min(4095, int(position)))
        speed = max(0, min(0x7FFF, int(speed)))
        acc = max(0, min(255, int(acc)))
        with self._lock:
            self.torque(True)
            params = [
                acc,
                position & 0xFF, (position >> 8) & 0xFF,
                0, 0,                                   # goal time
                speed & 0xFF, (speed >> 8) & 0xFF,
            ]
            return self.write_reg(ADDR_ACC, params)

    def present_position(self):
        v = self._read_u16(ADDR_PRESENT_POSITION)
        return None if v is None else (v & 0x7FFF)

    def present_load(self):
        v = self._read_u16(ADDR_PRESENT_LOAD)
        return None if v is None else _decode_signed(v, 0x400)

    def present_current(self):
        v = self._read_u16(ADDR_PRESENT_CURRENT)
        return None if v is None else _decode_signed(v, 0x8000)

    def present_voltage(self):
        d = self.read_reg(ADDR_PRESENT_VOLTAGE, 1)
        return None if not d else d[0]  # 0.1 V units

    def present_temp(self):
        d = self.read_reg(ADDR_PRESENT_TEMP, 1)
        return None if not d else d[0]  # deg C

    def is_moving(self):
        d = self.read_reg(ADDR_MOVING, 1)
        return None if not d else bool(d[0])

    def stop(self):
        """Halt motion immediately: command the present position as the goal so
        the servo brakes and holds where it is (torque stays on)."""
        with self._lock:
            pos = self.present_position()
            if pos is None:
                return False
            return self.move(pos, speed=600, acc=0)

    def guarded_move(self, position, speed=1500, acc=50, load_limit=200,
                     timeout=5.0, grace=0.15, poll=0.025, confirm=2):
        """Move toward `position` but stop the moment the load magnitude stays
        at/above `load_limit` -- a gentle 'stop on contact'. A short grace plus
        `confirm` consecutive over-limit samples reject the acceleration inrush.

        Returns an outcome dict with reason in {load, reached, timeout, no_servo}.
        Does not hold the bus lock across the loop, so /api/status keeps polling.
        """
        position = max(0, min(4095, int(position)))
        if not self.move(position, speed, acc):
            return {"ok": False, "stopped": False, "reason": "no_servo",
                    "target": position}
        t0 = time.time()
        time.sleep(grace)                       # ignore acceleration inrush
        hits = 0
        last_pos = None
        while time.time() - t0 < timeout:
            load = self.present_load()
            pos = self.present_position()
            if pos is not None:
                last_pos = pos
            if load is not None and abs(load) >= load_limit:
                hits += 1
                if hits >= confirm:
                    self.stop()
                    return {"ok": True, "stopped": True, "reason": "load",
                            "position": self.present_position(),
                            "load": load, "target": position}
            else:
                hits = 0
            if pos is not None and abs(pos - position) <= 10:
                return {"ok": True, "stopped": False, "reason": "reached",
                        "position": pos, "load": load, "target": position}
            time.sleep(poll)
        return {"ok": True, "stopped": False, "reason": "timeout",
                "position": last_pos, "target": position}

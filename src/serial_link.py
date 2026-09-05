"""Auto-detect com0com ports and open the Python (MCU) side."""

from __future__ import annotations

import time
from dataclasses import dataclass

import serial
from serial.tools import list_ports

from .com0com_setup import PREFERRED_DGUS, PREFERRED_PYTHON, PortPair

COM0COM_MARKERS = ("COM0COM", "CNCA", "CNCB", "COM0COM")
SKIP_MARKERS = ("BLUETOOTH", "BTHENUM", "STLINK", "DEBUG")


@dataclass
class PortInfo:
    device: str
    description: str
    hwid: str

    @property
    def is_com0com(self) -> bool:
        blob = f"{self.device} {self.description} {self.hwid}".upper()
        return any(m in blob for m in ("COM0COM", "CNCA", "CNCB"))

    @property
    def is_skipped(self) -> bool:
        blob = f"{self.device} {self.description} {self.hwid}".upper()
        return any(m in blob for m in SKIP_MARKERS)


def enumerate_ports() -> list[PortInfo]:
    found: list[PortInfo] = []
    seen: set[str] = set()
    for port in list_ports.comports():
        info = PortInfo(port.device, port.description or "", port.hwid or "")
        found.append(info)
        seen.add(info.device.upper())
    # com0com default names are often missing from Device Manager until renamed.
    for name in (PREFERRED_PYTHON, PREFERRED_DGUS, "CNCA0", "CNCB0"):
        if name.upper() in seen:
            continue
        if _port_exists(name):
            found.append(PortInfo(name, "detected by open-probe", "PROBE"))
    return found


def _port_exists(name: str) -> bool:
    try:
        with serial.Serial(name, baudrate=115200, timeout=0.05):
            return True
    except serial.SerialException as exc:
        text = str(exc).lower()
        if "file not found" in text or "could not open" in text or "cannot find" in text:
            # Access denied / permission / already open still means the port exists.
            if "access is denied" in text or "permission" in text or "busy" in text:
                return True
            return False
        return True


def choose_pair(ports: list[PortInfo] | None = None) -> PortPair:
    ports = ports if ports is not None else enumerate_ports()
    names = {p.device.upper(): p.device for p in ports}

    if PREFERRED_PYTHON.upper() in names and PREFERRED_DGUS.upper() in names:
        return PortPair(PREFERRED_PYTHON, PREFERRED_DGUS, "preferred COM10/COM11")

    com0 = [p for p in ports if p.is_com0com]
    if len(com0) >= 2:
        return PortPair(com0[0].device, com0[1].device, "com0com pair")
    if len(com0) == 1:
        other = next((p for p in ports if p.device != com0[0].device and not p.is_skipped), None)
        if other:
            return PortPair(com0[0].device, other.device, "com0com + other")

    usable = [p for p in ports if not p.is_skipped]
    if len(usable) >= 2:
        return PortPair(usable[0].device, usable[1].device, "first two non-Bluetooth ports")
    if len(usable) == 1:
        return PortPair(usable[0].device, usable[0].device, "single usable port")

    return PortPair(PREFERRED_PYTHON, PREFERRED_DGUS, "fallback names (pair may still be created)")


class DgusSerial:
    def __init__(self, port: str, baudrate: int = 115200) -> None:
        self.port = port
        self.baudrate = baudrate
        self._ser: serial.Serial | None = None

    @property
    def is_open(self) -> bool:
        return bool(self._ser and self._ser.is_open)

    def connect(self, retries: int = 8, delay: float = 0.4) -> None:
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                self._ser = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.05,
                    write_timeout=1,
                )
                self._ser.reset_input_buffer()
                self._ser.reset_output_buffer()
                return
            except serial.SerialException as exc:
                last_error = exc
                time.sleep(delay * attempt)
        raise ConnectionError(
            f"Could not open {self.port} at {self.baudrate} 8N1 after {retries} tries: {last_error}"
        )

    def send(self, frame: bytes) -> None:
        if not self._ser:
            raise ConnectionError("Serial port is not open.")
        self._ser.write(frame)
        self._ser.flush()

    def read(self, size: int = 256) -> bytes:
        if not self._ser:
            return b""
        waiting = self._ser.in_waiting
        if waiting:
            return self._ser.read(waiting)
        return self._ser.read(size)

    def close(self) -> None:
        if self._ser:
            try:
                self._ser.close()
            finally:
                self._ser = None

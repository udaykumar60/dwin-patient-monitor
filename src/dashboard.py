"""Live values and waveforms written to the DWIN / preview (MCU simulator)."""

from __future__ import annotations

import math
import time
from collections import deque
from dataclasses import dataclass, field

from . import dgus_protocol as proto
from .vp_map import CURVE, VP
from .waveforms import burst


SAMPLES_PER_TICK = 16
SAMPLE_DT = 0.008  # 125 Hz demo stream
TRACE_LEN = 280


@dataclass
class VitalState:
    heart_rate: int = 72
    spo2: int = 98
    temperature_x10: int = 365
    pressure: int = 118
    resp_rate: int = 16
    alarm: int = 0
    status: str = "SYSTEM READY"
    detail: str = "COM LINK IDLE"
    page: int = 0
    tick: float = 0.0
    frames_sent: int = 0
    last_hex: str = ""
    rx_hex: str = ""
    python_port: str = ""
    dgus_port: str = ""
    connected: bool = False
    log: list[str] = field(default_factory=list)
    ecg: deque[int] = field(default_factory=lambda: deque([128] * TRACE_LEN, maxlen=TRACE_LEN))
    resp_wave: deque[int] = field(default_factory=lambda: deque([128] * TRACE_LEN, maxlen=TRACE_LEN))
    spo2_wave: deque[int] = field(default_factory=lambda: deque([128] * TRACE_LEN, maxlen=TRACE_LEN))

    def snapshot(self) -> dict:
        return {
            "heart_rate": self.heart_rate,
            "spo2": self.spo2,
            "temperature": self.temperature_x10 / 10.0,
            "pressure": self.pressure,
            "resp_rate": self.resp_rate,
            "alarm": self.alarm,
            "status": self.status,
            "detail": self.detail,
            "page": self.page,
            "frames_sent": self.frames_sent,
            "last_hex": self.last_hex,
            "rx_hex": self.rx_hex,
            "python_port": self.python_port,
            "dgus_port": self.dgus_port,
            "connected": self.connected,
            "ecg": list(self.ecg),
            "resp_wave": list(self.resp_wave),
            "spo2_wave": list(self.spo2_wave),
        }


def next_vitals(state: VitalState, now: float | None = None) -> VitalState:
    t = now if now is not None else time.time()
    state.tick = t
    state.heart_rate = int(72 + 8 * math.sin(t / 1.6))
    state.spo2 = int(98 + 1.2 * math.sin(t / 2.4))
    state.temperature_x10 = int(365 + 6 * math.sin(t / 7.0))
    state.pressure = int(118 + 6 * math.sin(t / 3.1))
    state.resp_rate = int(16 + 2 * math.sin(t / 5.0))
    if state.heart_rate >= 78:
        state.alarm = 1
        state.status = "HR HIGH  —  MONITOR"
    else:
        state.alarm = 0
        state.status = "ALL VITALS NORMAL"
    state.detail = f"TX {state.frames_sent:05d}   PAGE {state.page}   {state.python_port}->{state.dgus_port}"
    return state


class DashboardEngine:
    def __init__(self, serial_link) -> None:
        self.link = serial_link
        self.state = VitalState()
        self._wave_t = 0.0

    def send_frame(self, frame: bytes, note: str = "") -> None:
        self.state.last_hex = proto.to_hex(frame)
        if self.link and self.link.is_open:
            self.link.send(frame)
            self.state.connected = True
        self.state.frames_sent += 1
        if note:
            self.state.log.append(note)
            self.state.log = self.state.log[-8:]

    def _push_wave(self, name: str, samples: list[int]) -> None:
        channel = CURVE[name]["channel"]
        target = {"ecg": self.state.ecg, "resp": self.state.resp_wave, "spo2": self.state.spo2_wave}[name]
        target.extend(samples)
        self.send_frame(proto.write_curve(channel, samples))

    def push_all(self) -> None:
        s = self.state
        self.send_frame(proto.write_words(VP["heart_rate"], s.heart_rate))
        self.send_frame(proto.write_words(VP["spo2"], s.spo2))
        self.send_frame(proto.write_words(VP["temperature"], s.temperature_x10))
        self.send_frame(proto.write_words(VP["pressure"], s.pressure))
        self.send_frame(proto.write_words(VP["resp_rate"], s.resp_rate))
        self.send_frame(proto.write_words(VP["alarm"], s.alarm))
        self.send_frame(proto.write_text(VP["status_text"], s.status))
        self.send_frame(proto.write_text(VP["detail_text"], s.detail))

        self._push_wave("ecg", burst("ecg", self._wave_t, SAMPLES_PER_TICK, SAMPLE_DT, s.heart_rate, s.resp_rate))
        self._push_wave("resp", burst("resp", self._wave_t, SAMPLES_PER_TICK, SAMPLE_DT, s.heart_rate, s.resp_rate))
        self._push_wave("spo2", burst("spo2", self._wave_t, SAMPLES_PER_TICK, SAMPLE_DT, s.heart_rate, s.resp_rate))
        self._wave_t += SAMPLES_PER_TICK * SAMPLE_DT

    def set_page(self, page_id: int) -> None:
        self.state.page = page_id
        self.send_frame(proto.set_page(page_id), note=f"page -> {page_id}")

    def step(self) -> VitalState:
        next_vitals(self.state)
        self.push_all()
        return self.state

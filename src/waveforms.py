"""Synthetic ECG / RESP / SpO2 traces. Replace with probe ADC on the real MCU."""

from __future__ import annotations

import math


def _gauss(x: float, center: float, width: float, height: float) -> float:
    return height * math.exp(-((x - center) ** 2) / (2.0 * width * width))


def ecg_sample(t: float, heart_rate: int) -> int:
    """One 0–255 sample of a PQRST beat. Baseline 128."""
    hr = max(40, min(180, heart_rate))
    period = 60.0 / hr
    x = (t % period) / period
    y = (
        _gauss(x, 0.18, 0.025, 12)
        - _gauss(x, 0.34, 0.012, 18)
        + _gauss(x, 0.40, 0.010, 95)
        - _gauss(x, 0.45, 0.014, 28)
        + _gauss(x, 0.62, 0.045, 22)
    )
    return max(0, min(255, int(128 + y)))


def resp_sample(t: float, resp_rate: int) -> int:
    rr = max(8, min(40, resp_rate))
    y = 40.0 * math.sin(2.0 * math.pi * t * rr / 60.0)
    return max(0, min(255, int(128 + y)))


def spo2_sample(t: float, heart_rate: int) -> int:
    """PPG-style pulse, same rate as ECG."""
    hr = max(40, min(180, heart_rate))
    period = 60.0 / hr
    x = (t % period) / period
    rise = math.exp(-((x - 0.22) ** 2) / 0.004) * 70
    notch = math.exp(-((x - 0.38) ** 2) / 0.003) * 18
    y = rise - notch
    return max(0, min(255, int(128 + y)))


def burst(kind: str, t0: float, count: int, dt: float, heart_rate: int, resp_rate: int) -> list[int]:
    fn = {"ecg": ecg_sample, "resp": resp_sample, "spo2": spo2_sample}[kind]
    out = []
    for i in range(count):
        t = t0 + i * dt
        if kind == "resp":
            out.append(fn(t, resp_rate))
        else:
            out.append(fn(t, heart_rate))
    return out

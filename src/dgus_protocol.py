"""DWIN DGUS II UART frames used by DGUS v7.650 virtual screen."""

from __future__ import annotations

from dataclasses import dataclass

HEADER = bytes((0x5A, 0xA5))
CMD_WRITE_VP = 0x82
CMD_READ_VP = 0x83
CMD_WRITE_CURVE = 0x84

# System variable: page switch. Write 0x5A01 + page id.
VP_PIC_SET = 0x0084


def _u16(value: int) -> bytes:
    return int(value).to_bytes(2, "big")


def build_frame(command: int, payload: bytes) -> bytes:
    """Frame = 5A A5 | length | command | payload. Length counts command+payload."""
    body = bytes((command & 0xFF,)) + payload
    return HEADER + bytes((len(body),)) + body


def write_vp(address: int, data: bytes) -> bytes:
    if len(data) % 2:
        data += b"\x00"
    return build_frame(CMD_WRITE_VP, _u16(address) + data)


def write_words(address: int, *values: int) -> bytes:
    payload = _u16(address) + b"".join(_u16(v & 0xFFFF) for v in values)
    return build_frame(CMD_WRITE_VP, payload)


def write_text(address: int, text: str, words: int = 16) -> bytes:
    """ASCII text for a DGUS Text Display control, padded and 0xFFFF terminated."""
    raw = text.encode("ascii", errors="replace")[: words * 2 - 2]
    if len(raw) % 2:
        raw += b"\x20"
    raw += b"\xFF\xFF"
    raw = raw.ljust(words * 2, b"\x00")
    return write_vp(address, raw)


def write_curve(channel: int, samples: list[int]) -> bytes:
    """DGUS II 0x84 real-time curve. channel 0–7, Y samples 0–65535 (we use 0–255)."""
    if not samples:
        raise ValueError("curve needs at least one sample")
    if len(samples) > 120:
        samples = samples[:120]
    ch_mode = 1 << (int(channel) & 7)
    payload = bytes((ch_mode,)) + b"".join(_u16(int(v) & 0xFFFF) for v in samples)
    return build_frame(CMD_WRITE_CURVE, payload)


def set_page(page_id: int) -> bytes:
    """Switch virtual-screen page (PIC_Set at 0x0084)."""
    return write_words(VP_PIC_SET, 0x5A01, page_id & 0xFFFF)


def read_vp(address: int, word_count: int = 1) -> bytes:
    return build_frame(CMD_READ_VP, _u16(address) + bytes((word_count & 0xFF,)))


def to_hex(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


@dataclass
class DgusFrame:
    command: int
    payload: bytes

    @property
    def address(self) -> int | None:
        if len(self.payload) >= 2:
            return int.from_bytes(self.payload[:2], "big")
        return None

    @property
    def words(self) -> list[int]:
        data = self.payload[2:]
        if self.command == CMD_READ_VP and data:
            data = data[1:]  # skip word-count on 0x83 replies
        out = []
        for i in range(0, len(data) - 1, 2):
            out.append(int.from_bytes(data[i : i + 2], "big"))
        return out


class FrameParser:
    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, chunk: bytes) -> list[DgusFrame]:
        self._buf.extend(chunk)
        frames: list[DgusFrame] = []
        while True:
            start = self._buf.find(HEADER)
            if start < 0:
                self._buf.clear()
                break
            if start:
                del self._buf[:start]
            if len(self._buf) < 4:
                break
            length = self._buf[2]
            total = 3 + length
            if len(self._buf) < total:
                break
            packet = bytes(self._buf[:total])
            del self._buf[:total]
            frames.append(DgusFrame(command=packet[3], payload=packet[4:]))
        return frames

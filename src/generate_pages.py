"""Create 1280x800 JPG pages for DGUS v7.650 (import into the HMI project)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .vp_map import VP

W, H = 1280, 800
BG = (8, 12, 20)
CARD = (16, 24, 40)
LINE = (32, 48, 72)
TEXT = (232, 238, 247)
MUTED = (138, 160, 191)
GREEN = (0, 220, 120)
RED = (255, 77, 109)
CYAN = (0, 210, 230)
AMBER = (255, 176, 32)
YELLOW = (240, 220, 80)
PURPLE = (167, 139, 250)


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = (
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "calibrib.ttf" if bold else "calibri.ttf",
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _round_rect(draw: ImageDraw.ImageDraw, box, fill, outline=None, radius=12) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2)


def _grid(draw: ImageDraw.ImageDraw, box, color) -> None:
    x0, y0, x1, y1 = box
    step = 28
    y = y0 + step
    while y < y1:
        draw.line((x0, y, x1, y), fill=color)
        y += step
    x = x0 + step
    while x < x1:
        draw.line((x, y0, x, y1), fill=color)
        x += step


def _wave_lane(draw, box, title, color, hint) -> None:
    _round_rect(draw, box, CARD, LINE, 10)
    _grid(draw, (box[0] + 8, box[1] + 28, box[2] - 8, box[3] - 8), (22, 34, 52))
    draw.text((box[0] + 16, box[1] + 6), title, font=_font(16, True), fill=color)
    draw.text((box[0] + 120, box[1] + 8), hint, font=_font(12), fill=MUTED)


def _value_panel(draw, box, title, unit, color, vp) -> None:
    _round_rect(draw, box, CARD, LINE, 10)
    draw.text((box[0] + 16, box[1] + 10), title, font=_font(14), fill=MUTED)
    draw.text((box[0] + 16, box[1] + 40), "---", font=_font(48, True), fill=color)
    draw.text((box[0] + 200, box[1] + 70), unit, font=_font(14), fill=MUTED)
    draw.text((box[0] + 16, box[3] - 28), vp, font=_font(12), fill=LINE)


def make_dashboard() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 80), fill=(6, 10, 18))
    draw.text((28, 16), "PATIENT MONITOR", font=_font(26, True), fill=GREEN)
    draw.text((28, 50), "DWIN DGUS  ·  ECG / RESP / SpO2  ·  UART 115200 8N1", font=_font(13), fill=MUTED)
    draw.text((980, 22), "DWIN PANEL", font=_font(13), fill=MUTED)
    draw.ellipse((1100, 20, 1128, 48), fill=GREEN)

    _wave_lane(draw, (20, 92, 888, 256), "ECG", GREEN, "Real-time curve CH0   0x84")
    _wave_lane(draw, (20, 276, 888, 440), "RESP", YELLOW, "Real-time curve CH1   0x84")
    _wave_lane(draw, (20, 460, 888, 624), "SpO2", CYAN, "Real-time curve CH2   0x84")

    _value_panel(draw, (908, 92, 1260, 256), "HEART RATE", "BPM", RED, f"VP 0x{VP['heart_rate']:04X}")
    _value_panel(draw, (908, 276, 1260, 440), "RESP", "/min", YELLOW, f"VP 0x{VP['resp_rate']:04X}")
    _value_panel(draw, (908, 460, 1260, 624), "SpO2", "%", CYAN, f"VP 0x{VP['spo2']:04X}")

    _round_rect(draw, (908, 640, 1080, 732), CARD, LINE, 10)
    draw.text((920, 650), "TEMP", font=_font(12), fill=MUTED)
    draw.text((920, 672), "--.-", font=_font(28, True), fill=AMBER)
    draw.text((920, 710), f"VP 0x{VP['temperature']:04X}", font=_font(11), fill=LINE)

    _round_rect(draw, (1092, 640, 1260, 732), CARD, LINE, 10)
    draw.text((1104, 650), "NIBP", font=_font(12), fill=MUTED)
    draw.text((1104, 672), "---", font=_font(28, True), fill=PURPLE)
    draw.text((1104, 710), f"VP 0x{VP['pressure']:04X}", font=_font(11), fill=LINE)

    _round_rect(draw, (20, 640, 888, 732), CARD, LINE, 10)
    draw.text((36, 652), "STATUS", font=_font(12), fill=MUTED)
    draw.text((36, 678), "Waiting for MCU / Python host…", font=_font(20, True), fill=GREEN)
    draw.text((36, 708), f"Text VP 0x{VP['status_text']:04X}   ·   Generate DWIN_SET to dump onto the panel", font=_font(12), fill=MUTED)

    draw.text((28, 752), "Place Real-time Curve controls on the 3 lanes and Data Variable Display on the number boxes.", font=_font(13), fill=LINE)
    return img


def make_status() -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 80), fill=(6, 10, 18))
    draw.text((28, 16), "SYSTEM / DUMP", font=_font(26, True), fill=GREEN)
    draw.text((28, 50), "Page 1  ·  how this project reaches a real DWIN screen", font=_font(13), fill=MUTED)
    _round_rect(draw, (28, 112, 1252, 760), CARD, LINE, 14)
    draw.text((56, 140), "DETAIL LINE", font=_font(13), fill=MUTED)
    draw.text((56, 176), "TX count and COM pair appear here", font=_font(22, True), fill=TEXT)
    draw.text((56, 220), f"Text VP 0x{VP['detail_text']:04X}", font=_font(14), fill=MUTED)
    lines = [
        "1. Same UART protocol on PC preview and on the purchased DWIN panel: 5A A5 82 / 84.",
        "2. In DGUS: File -> Generate. Copy the DWIN_SET folder to an SD card (root).",
        "3. Power off the DWIN, insert the card, power on. The screen loads this project.",
        "4. Wire the main MCU: TX -> DWIN RX, RX -> DWIN TX, GND. 115200 8N1.",
        "5. MCU writes VP 0x5000–0x5005 from probes, and 0x84 curve samples for ECG/RESP/SpO2.",
        "6. Python on this PC is only a stand-in MCU. Replace it with your patient-monitor firmware.",
    ]
    y = 300
    for line in lines:
        draw.text((56, y), line, font=_font(18), fill=TEXT)
        y += 44
    return img


def export_pages(folder: Path) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    dash = make_dashboard().convert("RGB")
    status = make_status().convert("RGB")
    paths = [
        folder / "00.jpg",
        folder / "01.jpg",
        folder / "00.bmp",
        folder / "01.bmp",
    ]
    dash.save(paths[0], quality=92)
    status.save(paths[1], quality=92)
    dash.save(paths[2])
    status.save(paths[3])
    return paths


if __name__ == "__main__":
    export_pages(Path(__file__).resolve().parents[1] / "dgus_hmi")

"""Variable map shared by Python, the Tk virtual screen, and the DWIN panel.

Vital VPs start at 0x5000 so they do not collide with DGUS curve buffers
(0x1000–0x4FFF, 2K words per real-time curve channel).
"""

from __future__ import annotations

PAGES = {
    0: "Dashboard",
    1: "Status",
}

VP = {
    "heart_rate": 0x5000,
    "spo2": 0x5001,
    "temperature": 0x5002,
    "pressure": 0x5003,
    "alarm": 0x5004,
    "resp_rate": 0x5005,
    "status_text": 0x5100,
    "detail_text": 0x5200,
}

# DGUS Display -> Real-time Curves  (command 0x84)
CURVE = {
    "ecg": {"channel": 0, "color": "0x07E0", "y_center": 128},
    "resp": {"channel": 1, "color": "0xFFE0", "y_center": 128},
    "spo2": {"channel": 2, "color": "0x07FF", "y_center": 128},
}

# 1280x800 placement for DGUS controls (page 0).
LAYOUT_1280X800 = {
    "ecg_curve": {"page": 0, "x": 24, "y": 96, "w": 860, "h": 168, "channel": 0},
    "resp_curve": {"page": 0, "x": 24, "y": 280, "w": 860, "h": 168, "channel": 1},
    "spo2_curve": {"page": 0, "x": 24, "y": 464, "w": 860, "h": 168, "channel": 2},
    "heart_rate": {"page": 0, "x": 920, "y": 120, "w": 320, "h": 72, "digits": 3, "decimals": 0},
    "resp_rate": {"page": 0, "x": 920, "y": 304, "w": 320, "h": 72, "digits": 2, "decimals": 0},
    "spo2": {"page": 0, "x": 920, "y": 488, "w": 160, "h": 64, "digits": 3, "decimals": 0},
    "temperature": {"page": 0, "x": 920, "y": 640, "w": 140, "h": 48, "digits": 2, "decimals": 1},
    "pressure": {"page": 0, "x": 1080, "y": 640, "w": 160, "h": 48, "digits": 3, "decimals": 0},
    "status_text": {"page": 0, "x": 32, "y": 748, "w": 860, "h": 36, "chars": 32},
    "detail_text": {"page": 1, "x": 80, "y": 220, "w": 1120, "h": 48, "chars": 32},
}

DGUS_CONTROL_STEPS = """
DGUS v7.650  —  software preview and hardware dump
--------------------------------------------------
1. Open DGUS_V7.650.exe
2. File -> Open -> dgus_hmi/DWprj.hmi
   (or New 1280x800, then add 00.jpg and 01.jpg from dgus_hmi/)
3. Numbers on page 0 (Display -> Data Variable Display):
     VP 0x5000  Heart Rate     3 digits, 0 decimal
     VP 0x5001  SpO2           3 digits, 0 decimal
     VP 0x5002  Temperature    2 digits, 1 decimal
     VP 0x5003  Pressure       3 digits, 0 decimal
     VP 0x5005  RESP rate      2 digits, 0 decimal
4. Text (Display -> Text Display):
     VP 0x5100  status bar     32 chars ASCII
     VP 0x5200  page 1 detail  32 chars ASCII
5. Graphs (Display -> Real-time Curves) on the three dark lanes:
     Channel 0  ECG    green    Y center 128   data 0-255
     Channel 1  RESP   yellow   Y center 128   data 0-255
     Channel 2  SpO2   cyan     Y center 128   data 0-255
6. File -> Save, then File -> Generate  (creates DWIN_SET)

PC preview: Common -> Preview from first page -> COM11, 115200, Open

Real DWIN panel:
  Copy the generated DWIN_SET folder to an SD card, insert it, power the screen.
  Wire MCU TX->DWIN RX, MCU RX->DWIN TX, GND. UART 115200 8N1.
  The MCU sends the same 0x82 VP writes and 0x84 curve frames as this Python host.
"""

# DWIN patient monitor (DGUS v7.650)

Python on this PC is a **stand-in MCU**. The same frames drive:

- the local preview window
- DGUS v7.650 virtual screen (when com0com works)
- a **real DWIN panel** after you dump `DWIN_SET`

When you buy the hardware, the main MCU reads ECG / RESP / SpO2 probes and sends those values and waveforms over UART. You do not rewrite the screen project.

```
Probes → Main MCU UART TX  →  DWIN RX   (115200 8N1)
                 UART RX  ←  DWIN TX
```

## What shows on the screen

| Item | How it is sent | Address / channel |
|---|---|---|
| Heart rate | Data variable | VP `0x5000` |
| SpO2 % | Data variable | VP `0x5001` |
| Temperature ×10 | Data variable | VP `0x5002` |
| NIBP | Data variable | VP `0x5003` |
| RESP rate | Data variable | VP `0x5005` |
| ECG graph | Real-time curve | CH0 command `0x84` |
| RESP graph | Real-time curve | CH1 command `0x84` |
| SpO2 graph | Real-time curve | CH2 command `0x84` |

Vitals start at `0x5000` so they do not sit on top of DWIN curve RAM (`0x1000–0x4FFF`).

## See it on this PC now

```text
cd C:\Users\udayk\OneDrive\Desktop\Project2
python run.py --no-dgus
```

The window **Patient monitor — DWIN / Python host** shows numbers plus ECG, RESP, and SpO2 traces.

## Dump onto a real DWIN panel

1. Open `dgus_hmi/DWprj.hmi` in **DGUS v7.650**.
2. Import `00.jpg` / `01.jpg` if the project is new.
3. Add the controls listed in `src/vp_map.py` (`DGUS_CONTROL_STEPS`).
4. **File → Generate**. This creates a `DWIN_SET` folder.
5. Copy **the whole `DWIN_SET` folder** to a FAT32 SD card (root).
6. Power the DWIN **off**, insert the card, power **on**. The panel programs itself.
7. Remove the card. Wire the MCU:

   - MCU TX → DWIN RX  
   - MCU RX → DWIN TX  
   - GND → GND  
   - Power as specified for that module (often 12 V or 5 V)

8. Port settings: **115200, 8 data, no parity, 1 stop**.
9. In your MCU firmware, send the same frames as `mcu/dwin_patient_monitor.c` (copy that file into your MCU project and fill `uart_write`).

After that, probe data from the MCU appears on the glass. No PC and no com0com are required.

## PC virtual screen (optional)

com0com on this Windows PC is blocked (`unsigned driver`), so COM10/COM11 may not exist. That only affects PC simulation. It does **not** affect a purchased DWIN panel.

If you later install a signed com0com build:

```text
python run.py
```

DGUS Preview → **COM11**, 115200 → **Open**.

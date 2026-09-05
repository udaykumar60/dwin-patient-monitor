"""
Auto-connect Python to a com0com port and stream live DGUS frames
to DGUS v7.650 virtual screen.
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.com0com_setup import UNSIGNED_HELP, driver_blocked, ensure_named_pair, open_setupg
from src.dashboard import DashboardEngine
from src.dgus_preview import find_dgus_exe, launch_dgus, remember_virtual_com
from src.dgus_protocol import FrameParser, to_hex
from src.generate_pages import export_pages
from src.serial_link import DgusSerial, choose_pair, enumerate_ports
from src.vp_map import DGUS_CONTROL_STEPS
from src.virtual_screen import VirtualScreen

HMI_DIR = ROOT / "dgus_hmi"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DGUS v7.650 virtual-screen Python host")
    parser.add_argument("--port", help="Force the Python-side COM port, e.g. COM10")
    parser.add_argument("--dgus-port", help="DGUS virtual-screen COM port, e.g. COM11")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--setup-ports", action="store_true", help="Create/rename com0com COM10<->COM11")
    parser.add_argument("--list-ports", action="store_true")
    parser.add_argument("--no-gui", action="store_true")
    parser.add_argument("--no-dgus", action="store_true", help="Do not launch DGUS_V7.650.exe")
    parser.add_argument("--interval", type=float, default=0.08, help="Seconds between VP / curve updates")
    return parser.parse_args()


def print_ports() -> None:
    if driver_blocked():
        print(UNSIGNED_HELP)
        print()
    ports = enumerate_ports()
    if not ports:
        print("No serial ports found.")
        return
    print("Serial ports:")
    for port in ports:
        mark = "  [com0com]" if port.is_com0com else ""
        skip = "  [skipped]" if port.is_skipped else ""
        print(f"  {port.device:10}  {port.description}{mark}{skip}")


def main() -> int:
    args = parse_args()
    export_pages(HMI_DIR)

    if args.list_ports:
        print_ports()
        return 0

    if args.setup_ports:
        print(ensure_named_pair())
        if not driver_blocked():
            open_setupg()
        print_ports()
        return 0

    print_ports()
    pair = choose_pair()
    python_port = args.port or pair.python_port
    dgus_port = args.dgus_port or pair.dgus_port
    print(f"\nAuto pair ({pair.source}):")
    print(f"  Python MCU ........ {python_port}")
    print(f"  DGUS virtual screen {dgus_port}  (115200 8N1)")
    print(DGUS_CONTROL_STEPS)

    remember_virtual_com(dgus_port, HMI_DIR / "DWprj.hmi")
    if not args.no_dgus:
        exe = launch_dgus(HMI_DIR / "DWprj.hmi")
        if exe:
            print(f"Launched {exe}")
        else:
            print("DGUS_V7.650.exe not found. Open it yourself, then Preview -> Open COM.")

    link = DgusSerial(python_port, args.baud)
    try:
        link.connect()
        print(f"Opened {python_port} automatically.")
    except ConnectionError as exc:
        print(exc)
        print("\nTrying to create COM10 <-> COM11 with com0com…")
        print(ensure_named_pair())
        try:
            link.connect()
            print(f"Opened {python_port} automatically.")
        except ConnectionError as exc2:
            print(exc2)
            if driver_blocked():
                print(UNSIGNED_HELP)
            else:
                print("Open com0com Setup (setupg.exe) as Administrator, add pair COM10 <-> COM11, then rerun.")
                open_setupg()
            if args.no_gui:
                return 1

    engine = DashboardEngine(link)
    engine.state.python_port = python_port
    engine.state.dgus_port = dgus_port
    engine.set_page(0)

    stop = threading.Event()
    parser = FrameParser()

    def worker() -> None:
        while not stop.is_set():
            try:
                if link.is_open:
                    incoming = link.read()
                    if incoming:
                        frames = parser.feed(incoming)
                        engine.state.rx_hex = to_hex(incoming)
                        for frame in frames:
                            engine.state.log.append(
                                f"RX cmd={frame.command:02X} addr={frame.address} words={frame.words}"
                            )
                else:
                    engine.state.connected = False
                engine.step()
            except Exception as exc:  # noqa: BLE001
                engine.state.connected = False
                engine.state.status = f"SERIAL ERROR: {exc}"
            stop.wait(args.interval)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    if args.no_gui:
        print("Streaming VPs. Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            stop.set()
            link.close()
        return 0

    app = VirtualScreen(on_page=engine.set_page, on_quit=stop.set)

    def pump() -> None:
        if stop.is_set():
            app.destroy()
            return
        app.update_state(engine.state.snapshot())
        app.after(200, pump)

    app.after(200, pump)
    app.mainloop()
    stop.set()
    link.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Launch DGUS v7.650 and remember the virtual-screen COM port."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

DGUS_EXE_CANDIDATES = (
    Path(r"C:\Users\udayk\OneDrive\Desktop\DGUS_V7650\DGUS_V7650\DGUS_V7.650.exe"),
    Path(r"C:\Users\udayk\Desktop\DGUS_V7650\DGUS_V7650\DGUS_V7.650.exe"),
)

TERMINAL_INI_CANDIDATES = (
    Path(r"C:\Users\udayk\OneDrive\Desktop\DGUS_V7650\DGUS_V7650\Config\Terminal.ini"),
    Path(r"C:\Users\udayk\Desktop\DGUS_V7650\DGUS_V7650\Config\Terminal.ini"),
)

# Index used by this DGUS build's UART tool. 115200 is the DWIN default.
BAUD_115200_INDEX = "6"


def find_dgus_exe() -> Path | None:
    for path in DGUS_EXE_CANDIDATES:
        if path.is_file():
            return path
    return None


def launch_dgus(project_hmi: Path | None = None) -> Path | None:
    exe = find_dgus_exe()
    if exe is None:
        return None
    args = [str(exe)]
    if project_hmi and project_hmi.is_file():
        args.append(str(project_hmi))
    subprocess.Popen(args, cwd=str(exe.parent))
    return exe


def remember_virtual_com(dgus_port: str, project_hmi: Path | None = None) -> None:
    """Write the DGUS-side COM into Terminal.ini so preview can pick it up."""
    for ini in TERMINAL_INI_CANDIDATES:
        if not ini.is_file():
            continue
        text = ini.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        out: list[str] = []
        in_download = False
        seen_com = seen_baud = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                in_download = stripped.lower() == "[download]"
            if in_download and stripped.lower().startswith("currcom"):
                out.append(f"CurrCom={dgus_port}")
                seen_com = True
                continue
            if in_download and stripped.lower().startswith("currbaudrate"):
                out.append(f"CurrBaudRate={BAUD_115200_INDEX}")
                seen_baud = True
                continue
            out.append(line)
        if not seen_com:
            out.append("[DOWNLOAD]")
            out.append(f"CurrCom={dgus_port}")
            out.append(f"CurrBaudRate={BAUD_115200_INDEX}")
        elif not seen_baud:
            out.append(f"CurrBaudRate={BAUD_115200_INDEX}")

        if project_hmi and project_hmi.is_file():
            patched = []
            written = False
            for line in out:
                if line.startswith("Prj1="):
                    patched.append(f"Prj1={project_hmi}")
                    written = True
                else:
                    patched.append(line)
            out = patched
            if not written:
                out.append("[TFTPRJ]")
                out.append(f"Prj1={project_hmi}")

        ini.write_text("\n".join(out) + "\n", encoding="utf-8")
        return


def open_folder(path: Path) -> None:
    os.startfile(str(path))  # noqa: S606

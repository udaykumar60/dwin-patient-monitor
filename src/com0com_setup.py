"""Detect and (when possible) create a com0com COM10 <-> COM11 pair."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

SETUPC_CANDIDATES = (
    Path(r"C:\Program Files (x86)\com0com\setupc.exe"),
    Path(r"C:\Program Files\com0com\setupc.exe"),
)

PREFERRED_PYTHON = "COM10"
PREFERRED_DGUS = "COM11"

UNSIGNED_HELP = """
com0com is installed but Windows blocked the driver (unsigned).
Until the driver starts, COM10/COM11 will not exist and DGUS cannot open a virtual port.

Fix (one of these), then reboot if asked:
  1. Install a signed com0com build for Windows 11, or
  2. In an Administrator Command Prompt:
       bcdedit /set testsigning on
     Reboot, then open setupg.exe and create pair COM10 <-> COM11.

After the pair exists, run:  python run.py
""".strip()


@dataclass
class PortPair:
    python_port: str
    dgus_port: str
    source: str


def find_setupc() -> Path | None:
    for path in SETUPC_CANDIDATES:
        if path.is_file():
            return path
    return None


def driver_blocked() -> bool:
    """True when Windows refused to load com0com (unsigned driver)."""
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-PnpDevice | Where-Object { $_.FriendlyName -like '*com0com*' } "
                "| Select-Object -ExpandProperty Problem",
            ],
            capture_output=True,
            text=True,
            timeout=12,
            check=False,
        )
    except Exception:  # noqa: BLE001
        return False
    return "CM_PROB_UNSIGNED_DRIVER" in (completed.stdout or "")


def run_setupc(*args: str, timeout: float = 8) -> str:
    setupc = find_setupc()
    if setupc is None:
        raise FileNotFoundError("com0com setupc.exe was not found.")
    # setupc is interactive if started with no real command; never call it that way.
    completed = subprocess.run(
        [str(setupc), *args],
        cwd=str(setupc.parent),
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    return (completed.stdout or "") + (completed.stderr or "")


def ensure_named_pair() -> str:
    """
    Ask com0com to expose COM10 <-> COM11.
    Needs Administrator if the pair has not been created yet.
    """
    if driver_blocked():
        return UNSIGNED_HELP

    setupc = find_setupc()
    if setupc is None:
        return "com0com is not installed. Install it, then run this again."

    notes: list[str] = []
    commands = [
        ("change", "CNCA0", f"PortName={PREFERRED_PYTHON}"),
        ("change", "CNCB0", f"PortName={PREFERRED_DGUS}"),
        ("install", f"PortName={PREFERRED_PYTHON}", f"PortName={PREFERRED_DGUS}"),
    ]
    for cmd in commands:
        try:
            out = run_setupc(*cmd)
            notes.append(f"$ setupc {' '.join(cmd)}\n{out.strip() or '(no output)'}")
        except subprocess.TimeoutExpired:
            notes.append(
                f"$ setupc {' '.join(cmd)}\nTimed out (setupc is an interactive tool). Use setupg.exe instead."
            )
        except Exception as exc:  # noqa: BLE001
            notes.append(f"$ setupc {' '.join(cmd)}\nERROR: {exc}")
    notes.append(
        "If Device Manager still shows 'COM# <-> COM#', open "
        f"{setupc.parent / 'setupg.exe'} as Administrator, add a pair, "
        f"and rename it to {PREFERRED_PYTHON} <-> {PREFERRED_DGUS}."
    )
    return "\n\n".join(notes)


def setupg_path() -> Path | None:
    setupc = find_setupc()
    if setupc is None:
        return None
    gui = setupc.with_name("setupg.exe")
    return gui if gui.is_file() else None


def open_setupg() -> bool:
    gui = setupg_path()
    if gui is None:
        return False
    os.startfile(str(gui))  # noqa: S606
    return True

"""Tk virtual screen that mirrors what the DWIN panel should show."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .vp_map import PAGES

BG = "#080C14"
CARD = "#101828"
LINE = "#203048"
TEXT = "#E8EEF7"
MUTED = "#8AA0BF"
GREEN = "#00DC78"
RED = "#FF4D6D"
CYAN = "#00D2E6"
AMBER = "#FFB020"
YELLOW = "#F0DC50"
PURPLE = "#A78BFA"


class VirtualScreen(tk.Tk):
    def __init__(self, on_page, on_quit) -> None:
        super().__init__()
        self.on_page = on_page
        self.on_quit = on_quit
        self.title("Patient monitor  —  DWIN / Python host")
        self.configure(bg=BG)
        self.geometry("1200x780")
        self.minsize(1040, 700)
        self.protocol("WM_DELETE_WINDOW", self._quit)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("Muted.TLabel", background=BG, foreground=MUTED)
        style.configure("Title.TLabel", background=BG, foreground=GREEN, font=("Segoe UI", 18, "bold"))
        style.configure("TButton", background=LINE, foreground=TEXT, padding=8)

        header = ttk.Frame(self)
        header.pack(fill="x", padx=16, pady=(12, 4))
        ttk.Label(header, text="PATIENT MONITOR", style="Title.TLabel").pack(side="left")
        self.link_label = ttk.Label(header, text="COM: searching…", style="Muted.TLabel")
        self.link_label.pack(side="right")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=6)
        waves = tk.Frame(body, bg=BG)
        waves.pack(side="left", fill="both", expand=True)
        nums = tk.Frame(body, bg=BG, width=280)
        nums.pack(side="right", fill="y", padx=(12, 0))
        nums.pack_propagate(False)

        self.canvases = {}
        self.canvases["ecg"] = self._wave(waves, "ECG", GREEN)
        self.canvases["resp"] = self._wave(waves, "RESP", YELLOW)
        self.canvases["spo2"] = self._wave(waves, "SpO2", CYAN)

        self.values = {}
        self.values["heart_rate"] = self._card(nums, "HEART RATE", "BPM", RED)
        self.values["resp_rate"] = self._card(nums, "RESP", "/min", YELLOW)
        self.values["spo2"] = self._card(nums, "SpO2", "%", CYAN)
        self.values["temperature"] = self._card(nums, "TEMP", "°C", AMBER)
        self.values["pressure"] = self._card(nums, "NIBP", "mmHg", PURPLE)

        self.status = tk.Label(
            self,
            text="Waiting for probes / MCU…",
            bg=CARD,
            fg=GREEN,
            font=("Consolas", 14),
            anchor="w",
            padx=16,
            pady=10,
        )
        self.status.pack(fill="x", padx=16, pady=(4, 8))

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=16, pady=(0, 12))
        ttk.Button(buttons, text="Page 0  Dashboard", command=lambda: self.on_page(0)).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Page 1  Status", command=lambda: self.on_page(1)).pack(side="left")
        self.page_label = ttk.Label(buttons, text="page 0", style="Muted.TLabel")
        self.page_label.pack(side="right")

    def _wave(self, parent, title: str, color: str) -> tk.Canvas:
        wrap = tk.Frame(parent, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        wrap.pack(fill="both", expand=True, pady=4)
        tk.Label(wrap, text=title, bg=CARD, fg=color, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(4, 0))
        canvas = tk.Canvas(wrap, bg="#060A10", highlightthickness=0, height=140)
        canvas.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        return canvas

    def _card(self, parent, title: str, unit: str, color: str) -> tk.Label:
        frame = tk.Frame(parent, bg=CARD, highlightbackground=LINE, highlightthickness=1)
        frame.pack(fill="x", pady=5)
        tk.Label(frame, text=title, bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(8, 0))
        value = tk.Label(frame, text="--", bg=CARD, fg=color, font=("Segoe UI", 28, "bold"))
        value.pack(anchor="w", padx=12)
        tk.Label(frame, text=unit, bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(0, 8))
        return value

    def _plot(self, canvas: tk.Canvas, samples: list[int], color: str) -> None:
        canvas.delete("all")
        w = max(canvas.winfo_width(), 10)
        h = max(canvas.winfo_height(), 10)
        if len(samples) < 2:
            return
        points = []
        last = len(samples) - 1
        for i, value in enumerate(samples):
            x = i * (w - 2) / last
            y = h - 4 - (max(0, min(255, value)) / 255.0) * (h - 8)
            points.extend((x, y))
        canvas.create_line(*points, fill=color, width=2, smooth=True)

    def update_state(self, snap: dict) -> None:
        self.values["heart_rate"].configure(text=str(snap["heart_rate"]))
        self.values["resp_rate"].configure(text=str(snap.get("resp_rate", "--")))
        self.values["spo2"].configure(text=str(snap["spo2"]))
        self.values["temperature"].configure(text=f"{snap['temperature']:.1f}")
        self.values["pressure"].configure(text=str(snap["pressure"]))
        self._plot(self.canvases["ecg"], snap.get("ecg") or [], GREEN)
        self._plot(self.canvases["resp"], snap.get("resp_wave") or [], YELLOW)
        self._plot(self.canvases["spo2"], snap.get("spo2_wave") or [], CYAN)
        self.status.configure(text=snap["status"], fg=RED if snap["alarm"] else GREEN)
        link = "CONNECTED" if snap["connected"] else "LOCAL PREVIEW (no DWIN COM yet)"
        self.link_label.configure(
            text=f"{link}   Python {snap['python_port'] or '-'}  →  DWIN {snap['dgus_port'] or '-'}"
        )
        self.page_label.configure(text=f"page {snap['page']}  {PAGES.get(snap['page'], '')}   TX {snap['frames_sent']}")

    def _quit(self) -> None:
        self.on_quit()
        self.destroy()

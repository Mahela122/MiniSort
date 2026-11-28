"""Compact startup loading splash screen for MiniSort."""

from __future__ import annotations

import tkinter as tk
import customtkinter as ctk

from ui.theme import ThemeManager
from utils.constants import APP_NAME, APP_TAGLINE, APP_VERSION


class SplashScreen(ctk.CTkToplevel):
    """Borderless centered loading screen displayed briefly while MiniSort initializes."""

    def __init__(self, parent: tk.Misc, theme: ThemeManager) -> None:
        super().__init__(parent)
        self._theme = theme
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=theme.color("border_strong"))

        width, height = 400, 260
        self.update_idletasks()
        scaling = 1.0
        try:
            scaling = float(self._get_window_scaling())
        except Exception:
            scaling = 1.0
        phys_w = int(width * scaling)
        phys_h = int(height * scaling)
        sx = max(20, (self.winfo_screenwidth() - phys_w) // 2)
        sy = max(20, (self.winfo_screenheight() - phys_h) // 2)
        self.geometry(f"{width}x{height}+{sx}+{sy}")

        # Outer 1px frame border with clean interior card
        card = ctk.CTkFrame(
            self,
            fg_color=theme.color("bg_app"),
            corner_radius=0,
        )
        card.pack(fill="both", expand=True, padx=1, pady=1)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        logo = theme.app_logo(74)
        if logo is not None:
            ctk.CTkLabel(inner, text="", image=logo).pack(pady=(0, 10))

        ctk.CTkLabel(
            inner,
            text=APP_NAME,
            font=theme.font(22, "bold"),
            text_color=theme.color("text_primary"),
        ).pack()

        ctk.CTkLabel(
            inner,
            text=APP_TAGLINE,
            font=theme.font(12, "normal"),
            text_color=theme.color("text_secondary"),
        ).pack(pady=(2, 16))

        self._bar = ctk.CTkProgressBar(
            inner,
            width=260,
            height=6,
            corner_radius=3,
            fg_color=theme.color("bg_hover"),
            progress_color=theme.color("btn_primary_bg"),
        )
        self._bar.set(0.15)
        self._bar.pack(pady=(0, 8))

        self._status = ctk.CTkLabel(
            inner,
            text="Starting MiniSort...",
            font=theme.font(11, "normal"),
            text_color=theme.color("text_muted"),
        )
        self._status.pack()

        ctk.CTkLabel(
            card,
            text=f"Version {APP_VERSION}",
            font=theme.font(10, "normal"),
            text_color=theme.color("text_muted"),
        ).place(relx=0.5, rely=0.93, anchor="center")

        self.update()

    def set_progress(self, value: float, status: str) -> None:
        if not self.winfo_exists():
            return
        self._bar.set(max(0.0, min(1.0, value)))
        self._status.configure(text=status)
        self.update()

    def close(self) -> None:
        if self.winfo_exists():
            try:
                self.destroy()
            except Exception:
                pass

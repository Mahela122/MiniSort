"""Left navigation sidebar for MiniSort with strict black-and-white active states."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from ui.theme import ThemeManager
from utils.constants import APP_NAME, APP_TAGLINE, APP_VERSION

NAV_ITEMS = [
    ("dashboard", "Dashboard", "dashboard"),
    ("sort", "Sort Data", "sort"),
    ("filter", "Filter Data", "filter"),
    ("clean", "Clean Data", "clean"),
    ("statistics", "Data Statistics", "stats"),
    ("recent", "Recent Files", "recent"),
    ("settings", "Settings", "settings"),
    ("about", "About", "about"),
]


class Sidebar(ctk.CTkFrame):
    """Minimalist left navigation sidebar with 8 sections and clear monochrome active state."""

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        theme: ThemeManager,
        on_navigate: Callable[[str], None],
    ) -> None:
        super().__init__(
            master,
            width=220,
            corner_radius=0,
            fg_color=theme.color("bg_sidebar"),
        )
        self.pack_propagate(False)
        self._theme = theme
        self._on_navigate = on_navigate
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._icon_map: dict[str, str] = {}
        self._active_key = "dashboard"

        self._build_ui()
        self.set_active("dashboard")

    def _build_ui(self) -> None:
        # Right border divider
        divider = ctk.CTkFrame(
            self,
            width=1,
            fg_color=self._theme.color("border"),
            corner_radius=0,
        )
        divider.pack(side="right", fill="y")

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(side="left", fill="both", expand=True)

        # Brand Header
        brand = ctk.CTkFrame(container, fg_color="transparent")
        brand.pack(fill="x", padx=18, pady=(20, 18))

        logo_img = self._theme.app_logo(36)
        if logo_img is not None:
            ctk.CTkLabel(brand, text="", image=logo_img).pack(side="left", padx=(0, 10))

        title_col = ctk.CTkFrame(brand, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_col,
            text=APP_NAME,
            font=self._theme.font(17, "bold"),
            text_color=self._theme.color("text_primary"),
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text=APP_TAGLINE,
            font=self._theme.font(10, "normal"),
            text_color=self._theme.color("text_muted"),
            anchor="w",
        ).pack(anchor="w")

        # Subtle horizontal divider
        ctk.CTkFrame(container, height=1, fg_color=self._theme.color("border")).pack(
            fill="x", padx=16, pady=(0, 14)
        )

        # Navigation buttons
        nav_frame = ctk.CTkFrame(container, fg_color="transparent")
        nav_frame.pack(fill="both", expand=True, padx=12)

        for key, label, icon_name in NAV_ITEMS:
            self._icon_map[key] = icon_name
            btn = ctk.CTkButton(
                nav_frame,
                text=f"  {label}",
                anchor="w",
                height=40,
                corner_radius=8,
                border_width=0,
                font=self._theme.font(13, "normal"),
                image=self._theme.icon(icon_name, "dark", 17),
                compound="left",
                command=lambda k=key: self._handle_click(k),
            )
            btn.pack(fill="x", pady=2)
            self._buttons[key] = btn

        # Footer offline indicator
        footer = ctk.CTkFrame(container, fg_color="transparent")
        footer.pack(fill="x", padx=16, pady=(8, 16))

        ctk.CTkFrame(footer, height=1, fg_color=self._theme.color("border")).pack(
            fill="x", pady=(0, 10)
        )

        ctk.CTkLabel(
            footer,
            text=f"Version {APP_VERSION}",
            font=self._theme.font(11, "normal"),
            text_color=self._theme.color("text_muted"),
            anchor="w",
        ).pack(anchor="w", padx=4)

    def _handle_click(self, key: str) -> None:
        self.set_active(key)
        self._on_navigate(key)

    def set_active(self, key: str) -> None:
        self._active_key = key
        for item_key, btn in self._buttons.items():
            icon_name = self._icon_map[item_key]
            if item_key == key:
                btn.configure(
                    fg_color=self._theme.color("btn_primary_bg"),
                    hover_color=self._theme.color("btn_primary_hover"),
                    text_color=self._theme.color("btn_primary_text"),
                    font=self._theme.font(13, "bold"),
                    image=self._theme.icon(icon_name, "light", 17),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    hover_color=self._theme.color("bg_hover"),
                    text_color=self._theme.color("text_primary"),
                    font=self._theme.font(13, "normal"),
                    image=self._theme.icon(icon_name, "dark", 17),
                )

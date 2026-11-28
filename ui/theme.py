"""Visual theme, background customization, typography scaling, icon cache, and Treeview styling."""

from __future__ import annotations

import re
from tkinter import ttk
import customtkinter as ctk
from PIL import Image

from utils.constants import (
    BACKGROUND_PRESETS,
    PALETTE_DARK_BASE,
    PALETTE_HIGH_CONTRAST,
    PALETTE_STANDARD,
    TABLE_DENSITY_ROWHEIGHT,
    TEXT_SIZE_OFFSETS,
)
from utils.helpers import get_asset_path

HEX_COLOR_RE = re.compile(r"^#([0-9a-fA-F]{6})$")


def _parse_hex(hex_color: str) -> tuple[int, int, int]:
    m = HEX_COLOR_RE.match(str(hex_color).strip())
    if not m:
        return (255, 255, 255)
    h = m.group(1)
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = (max(0, min(255, int(round(c)))) for c in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def _mix_hex(c1: str, c2: str, ratio: float) -> str:
    """Blend c1 toward c2 by ratio in [0.0, 1.0]."""
    r1, g1, b1 = _parse_hex(c1)
    r2, g2, b2 = _parse_hex(c2)
    return _to_hex(
        (
            r1 + (r2 - r1) * ratio,
            g1 + (g2 - g1) * ratio,
            b1 + (b2 - b1) * ratio,
        )
    )


def _is_dark_hex(hex_color: str) -> bool:
    r, g, b = _parse_hex(hex_color)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
    return luminance < 0.52


class ThemeManager:
    """Central source of truth for MiniSort's background theme, contrast, typography, and icons."""

    def __init__(
        self,
        variant: str = "Standard Monochrome",
        background_preset: str = "Pure White",
        custom_bg_color: str = "#FFFFFF",
        text_size: str = "Normal",
        table_density: str = "Comfortable",
    ) -> None:
        self._variant = variant
        self._background_preset = background_preset
        self._custom_bg_color = custom_bg_color if HEX_COLOR_RE.match(str(custom_bg_color)) else "#FFFFFF"
        self._text_size = text_size if text_size in TEXT_SIZE_OFFSETS else "Normal"
        self._table_density = table_density if table_density in TABLE_DENSITY_ROWHEIGHT else "Comfortable"
        self._is_dark = False
        self._palette: dict[str, str] = {}
        self._icon_cache: dict[tuple[str, str, int], ctk.CTkImage] = {}
        self._logo_cache: dict[int, ctk.CTkImage] = {}
        self._rebuild_palette()

    def _rebuild_palette(self) -> None:
        high_contrast = self._variant == "High-Contrast Monochrome"

        if self._background_preset == "Custom":
            bg = self._custom_bg_color
            self._is_dark = _is_dark_hex(bg)
            if self._is_dark:
                p = dict(PALETTE_DARK_BASE)
                p["bg_app"] = bg
                p["bg_sidebar"] = _mix_hex(bg, "#000000", 0.25)
                p["bg_surface"] = _mix_hex(bg, "#FFFFFF", 0.08)
                p["bg_subtle"] = _mix_hex(bg, "#FFFFFF", 0.13)
                p["bg_hover"] = _mix_hex(bg, "#FFFFFF", 0.19)
                p["bg_active_subtle"] = _mix_hex(bg, "#FFFFFF", 0.25)
                p["border"] = _mix_hex(bg, "#FFFFFF", 0.45 if high_contrast else 0.20)
                p["border_strong"] = _mix_hex(bg, "#FFFFFF", 0.70 if high_contrast else 0.35)
                p["table_header_bg"] = _mix_hex(bg, "#FFFFFF", 0.12)
                p["table_row_even"] = _mix_hex(bg, "#FFFFFF", 0.05)
                p["table_row_odd"] = _mix_hex(bg, "#FFFFFF", 0.09)
            else:
                p = dict(PALETTE_HIGH_CONTRAST if high_contrast else PALETTE_STANDARD)
                p["bg_app"] = bg
                p["bg_sidebar"] = _mix_hex(bg, "#000000", 0.04)
                p["bg_surface"] = _mix_hex(bg, "#FFFFFF", 0.70)
                p["bg_subtle"] = _mix_hex(bg, "#000000", 0.05)
                p["bg_hover"] = _mix_hex(bg, "#000000", 0.10)
                p["bg_active_subtle"] = _mix_hex(bg, "#000000", 0.16)
                p["table_header_bg"] = _mix_hex(bg, "#000000", 0.06)
                p["table_row_even"] = _mix_hex(bg, "#FFFFFF", 0.78)
                p["table_row_odd"] = _mix_hex(bg, "#000000", 0.03)
            self._palette = p
            return

        preset = BACKGROUND_PRESETS.get(self._background_preset, BACKGROUND_PRESETS["Pure White"])
        self._is_dark = bool(preset["is_dark"])

        if self._is_dark:
            p = dict(PALETTE_DARK_BASE)
            p["bg_app"] = str(preset["bg_app"])
            p["bg_sidebar"] = str(preset["bg_sidebar"])
            p["bg_surface"] = str(preset["bg_surface"])
            p["bg_subtle"] = str(preset["bg_subtle"])
            p["table_row_even"] = str(preset["bg_surface"])
            p["table_row_odd"] = str(preset["bg_subtle"])
            if high_contrast:
                p["border"] = "#A0A0AA"
                p["border_strong"] = "#FFFFFF"
                p["text_primary"] = "#FFFFFF"
                p["text_secondary"] = "#E2E2E8"
                p["text_muted"] = "#B8B8C2"
            self._palette = p
        else:
            p = dict(PALETTE_HIGH_CONTRAST if high_contrast else PALETTE_STANDARD)
            p["bg_app"] = str(preset["bg_app"])
            p["bg_sidebar"] = str(preset["bg_sidebar"])
            p["bg_surface"] = str(preset["bg_surface"])
            p["bg_subtle"] = str(preset["bg_subtle"])
            if self._background_preset != "Pure White":
                p["table_row_even"] = str(preset["bg_surface"])
                p["table_row_odd"] = str(preset["bg_subtle"])
                p["table_header_bg"] = str(preset["bg_sidebar"])
            self._palette = p

    @property
    def variant(self) -> str:
        return self._variant

    @property
    def background_preset(self) -> str:
        return self._background_preset

    @property
    def custom_bg_color(self) -> str:
        return self._custom_bg_color

    @property
    def text_size(self) -> str:
        return self._text_size

    @property
    def table_density(self) -> str:
        return self._table_density

    @property
    def is_dark(self) -> bool:
        return self._is_dark

    def configure(
        self,
        *,
        variant: str | None = None,
        background_preset: str | None = None,
        custom_bg_color: str | None = None,
        text_size: str | None = None,
        table_density: str | None = None,
    ) -> None:
        if variant is not None:
            self._variant = variant
        if background_preset is not None:
            self._background_preset = background_preset
        if custom_bg_color is not None and HEX_COLOR_RE.match(str(custom_bg_color)):
            self._custom_bg_color = str(custom_bg_color).upper()
        if text_size is not None and text_size in TEXT_SIZE_OFFSETS:
            self._text_size = text_size
        if table_density is not None and table_density in TABLE_DENSITY_ROWHEIGHT:
            self._table_density = table_density
        self._rebuild_palette()

    def set_variant(self, variant: str) -> None:
        self.configure(variant=variant)

    def color(self, token: str) -> str:
        return self._palette[token]

    @property
    def c(self) -> dict[str, str]:
        return self._palette

    def sync_ctk_appearance_mode(self) -> None:
        """Align CustomTkinter light/dark mode with the selected background preset."""
        ctk.set_appearance_mode("dark" if self._is_dark else "light")

    @staticmethod
    def apply_ctk_theme(is_dark: bool = False) -> None:
        """Apply custom monochrome CTk theme with both light and dark tokens."""
        ctk.set_appearance_mode("dark" if is_dark else "light")
        theme_file = get_asset_path("theme_bw.json")
        if theme_file.exists():
            ctk.set_default_color_theme(str(theme_file))

    def font(self, size: int = 13, weight: str = "normal") -> ctk.CTkFont:
        offset = TEXT_SIZE_OFFSETS.get(self._text_size, 0)
        return ctk.CTkFont(family="Segoe UI", size=max(9, size + offset), weight=weight)

    def mono_font(self, size: int = 12, weight: str = "normal") -> ctk.CTkFont:
        offset = TEXT_SIZE_OFFSETS.get(self._text_size, 0)
        return ctk.CTkFont(family="Consolas", size=max(9, size + offset), weight=weight)

    def icon(self, name: str, variant: str = "dark", size: int = 18) -> ctk.CTkImage | None:
        """Load and cache a crisp Lucide-style icon, automatically adapting polarity on dark themes."""
        effective_variant = variant
        if self._is_dark:
            if variant == "dark":
                effective_variant = "light"
            elif variant == "light":
                effective_variant = "dark"

        key = (name, effective_variant, size)
        if key in self._icon_cache:
            return self._icon_cache[key]
        path = get_asset_path("icons", f"{name}_{effective_variant}.png")
        if not path.exists():
            return None
        img = Image.open(path)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
        self._icon_cache[key] = ctk_img
        return ctk_img

    def app_logo(self, size: int = 28) -> ctk.CTkImage | None:
        if size in self._logo_cache:
            return self._logo_cache[size]
        path = get_asset_path("images", "minisort.png")
        if not path.exists():
            return None
        img = Image.open(path)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
        self._logo_cache[size] = ctk_img
        return ctk_img

    def configure_treeview_style(self, style: ttk.Style | None = None) -> ttk.Style:
        """Configure ttk.Treeview style matching current background, text size, and row density."""
        s = style or ttk.Style()
        try:
            s.theme_use("clam")
        except Exception:
            pass

        p = self._palette
        row_h = TABLE_DENSITY_ROWHEIGHT.get(self._table_density, 30)
        font_pt = max(9, 10 + TEXT_SIZE_OFFSETS.get(self._text_size, 0))

        s.configure(
            "MiniSort.Treeview",
            background=p["table_row_even"],
            fieldbackground=p["table_row_even"],
            foreground=p["text_primary"],
            rowheight=row_h,
            borderwidth=0,
            relief="flat",
            font=("Segoe UI", font_pt),
        )
        s.map(
            "MiniSort.Treeview",
            background=[("selected", p["table_select_bg"])],
            foreground=[("selected", p["table_select_fg"])],
        )

        s.configure(
            "MiniSort.Treeview.Heading",
            background=p["table_header_bg"],
            foreground=p["text_primary"],
            bordercolor=p["border"],
            lightcolor=p["table_header_bg"],
            darkcolor=p["border"],
            relief="flat",
            borderwidth=1,
            font=("Segoe UI", font_pt, "bold"),
            padding=(10, 7),
        )
        s.map(
            "MiniSort.Treeview.Heading",
            background=[("active", p["bg_hover"]), ("pressed", p["bg_active_subtle"])],
            foreground=[("active", p["text_primary"])],
        )

        s.layout(
            "MiniSort.Treeview",
            [("MiniSort.Treeview.treearea", {"sticky": "nswe"})],
        )
        return s

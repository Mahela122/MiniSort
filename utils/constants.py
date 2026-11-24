"""Application-wide constants, strict black-and-white palette, and default settings for MiniSort."""

from __future__ import annotations

APP_NAME = "MiniSort"
APP_TAGLINE = "Smart Spreadsheet Organizer"
APP_VERSION = "1.2.0"
APP_DESCRIPTION = (
    "MiniSort is a simple desktop application that helps everyone organize, "
    "sort, filter and clean CSV and Excel datasets without complicated "
    "spreadsheet operations."
)
APP_DEVELOPER = "Mahela122"
APP_GITHUB_URL = "https://github.com/Mahela122"
APP_WINDOW_TITLE = f"{APP_NAME} — {APP_TAGLINE}"

MIN_WINDOW_WIDTH = 1000
MIN_WINDOW_HEIGHT = 650
DEFAULT_WINDOW_WIDTH = 1260
DEFAULT_WINDOW_HEIGHT = 780

SUPPORTED_EXTENSIONS = (".csv", ".xlsx", ".xls")
EXPORT_EXTENSIONS = (".xlsx", ".csv")

# Practical safety limits so the application warns gracefully instead of crashing
MAX_FILE_SIZE_MB = 250
LARGE_DATASET_WARNING_ROWS = 100_000
MAX_UNDO_MEMORY_MB = 150
MAX_UNDO_STEPS = 20
MAX_RECENT_FILES = 20

# Strict Black-and-White Design System Tokens
# Zero blue, green, purple, orange, red, or decorative colors anywhere.
PALETTE_STANDARD = {
    "bg_app": "#FFFFFF",
    "bg_sidebar": "#FAFAFA",
    "bg_surface": "#FFFFFF",
    "bg_subtle": "#F5F5F5",
    "bg_hover": "#EBEBEB",
    "bg_active_subtle": "#E2E2E2",
    "border": "#DCDCDC",
    "border_strong": "#B8B8B8",
    "border_dark": "#111111",
    "text_primary": "#111111",
    "text_secondary": "#4D4D4D",
    "text_muted": "#737373",
    "text_inverse": "#FFFFFF",
    "btn_primary_bg": "#111111",
    "btn_primary_hover": "#2E2E2E",
    "btn_primary_text": "#FFFFFF",
    "btn_secondary_bg": "#F0F0F0",
    "btn_secondary_hover": "#E0E0E0",
    "btn_secondary_text": "#111111",
    "btn_ghost_bg": "transparent",
    "btn_ghost_hover": "#EFEFEF",
    "table_header_bg": "#F3F3F3",
    "table_row_even": "#FFFFFF",
    "table_row_odd": "#FAFAFA",
    "table_select_bg": "#1A1A1A",
    "table_select_fg": "#FFFFFF",
    "badge_bg": "#EFEFEF",
    "badge_fg": "#222222",
    "badge_dark_bg": "#111111",
    "badge_dark_fg": "#FFFFFF",
    "scrollbar_bg": "#F2F2F2",
    "scrollbar_thumb": "#BDBDBD",
    "scrollbar_thumb_hover": "#8C8C8C",
}

PALETTE_HIGH_CONTRAST = {
    "bg_app": "#FFFFFF",
    "bg_sidebar": "#FFFFFF",
    "bg_surface": "#FFFFFF",
    "bg_subtle": "#F2F2F2",
    "bg_hover": "#E0E0E0",
    "bg_active_subtle": "#D4D4D4",
    "border": "#222222",
    "border_strong": "#000000",
    "border_dark": "#000000",
    "text_primary": "#000000",
    "text_secondary": "#222222",
    "text_muted": "#444444",
    "text_inverse": "#FFFFFF",
    "btn_primary_bg": "#000000",
    "btn_primary_hover": "#262626",
    "btn_primary_text": "#FFFFFF",
    "btn_secondary_bg": "#E8E8E8",
    "btn_secondary_hover": "#D4D4D4",
    "btn_secondary_text": "#000000",
    "btn_ghost_bg": "transparent",
    "btn_ghost_hover": "#E6E6E6",
    "table_header_bg": "#E8E8E8",
    "table_row_even": "#FFFFFF",
    "table_row_odd": "#F6F6F6",
    "table_select_bg": "#000000",
    "table_select_fg": "#FFFFFF",
    "badge_bg": "#E6E6E6",
    "badge_fg": "#000000",
    "badge_dark_bg": "#000000",
    "badge_dark_fg": "#FFFFFF",
    "scrollbar_bg": "#E8E8E8",
    "scrollbar_thumb": "#555555",
    "scrollbar_thumb_hover": "#111111",
}

# Curated background presets selectable in Settings (with automatic contrast support)
BACKGROUND_PRESETS: dict[str, dict[str, str | bool]] = {
    "Pure White": {
        "swatch": "#FFFFFF",
        "bg_app": "#FFFFFF",
        "bg_sidebar": "#FAFAFA",
        "bg_surface": "#FFFFFF",
        "bg_subtle": "#F5F5F5",
        "is_dark": False,
    },
    "Soft Grey": {
        "swatch": "#F0F0F0",
        "bg_app": "#EFEFEF",
        "bg_sidebar": "#E6E6E6",
        "bg_surface": "#FFFFFF",
        "bg_subtle": "#F5F5F5",
        "is_dark": False,
    },
    "Warm Paper": {
        "swatch": "#F7F4EE",
        "bg_app": "#F6F3EC",
        "bg_sidebar": "#EEEAE0",
        "bg_surface": "#FDFBF7",
        "bg_subtle": "#F0ECE3",
        "is_dark": False,
    },
    "Dark Charcoal": {
        "swatch": "#1A1A1A",
        "bg_app": "#1A1A1A",
        "bg_sidebar": "#121212",
        "bg_surface": "#242424",
        "bg_subtle": "#2C2C2C",
        "is_dark": True,
    },
    "Pure Black": {
        "swatch": "#0A0A0A",
        "bg_app": "#0A0A0A",
        "bg_sidebar": "#000000",
        "bg_surface": "#151515",
        "bg_subtle": "#1E1E1E",
        "is_dark": True,
    },
}

PALETTE_DARK_BASE = {
    "bg_app": "#1A1A1A",
    "bg_sidebar": "#121212",
    "bg_surface": "#242424",
    "bg_subtle": "#2C2C2C",
    "bg_hover": "#363636",
    "bg_active_subtle": "#424242",
    "border": "#383838",
    "border_strong": "#5E5E5E",
    "border_dark": "#F5F5F5",
    "text_primary": "#F5F5F5",
    "text_secondary": "#C8C8C8",
    "text_muted": "#969696",
    "text_inverse": "#111111",
    "btn_primary_bg": "#F5F5F5",
    "btn_primary_hover": "#DCDCDC",
    "btn_primary_text": "#111111",
    "btn_secondary_bg": "#2D2D2D",
    "btn_secondary_hover": "#3A3A3A",
    "btn_secondary_text": "#F5F5F5",
    "btn_ghost_bg": "transparent",
    "btn_ghost_hover": "#303030",
    "table_header_bg": "#2A2A2A",
    "table_row_even": "#202020",
    "table_row_odd": "#262626",
    "table_select_bg": "#F5F5F5",
    "table_select_fg": "#111111",
    "badge_bg": "#303030",
    "badge_fg": "#F5F5F5",
    "badge_dark_bg": "#F5F5F5",
    "badge_dark_fg": "#111111",
    "scrollbar_bg": "#202020",
    "scrollbar_thumb": "#4D4D4D",
    "scrollbar_thumb_hover": "#6E6E6E",
}

TEXT_SIZE_OFFSETS = {
    "Small": -1,
    "Normal": 0,
    "Large": 2,
}

TABLE_DENSITY_ROWHEIGHT = {
    "Compact": 24,
    "Comfortable": 30,
    "Spacious": 38,
}

DEFAULT_SETTINGS = {
    "theme_variant": "Standard Monochrome",  # "Standard Monochrome" | "High-Contrast Monochrome"
    "background_preset": "Pure White",       # Preset key in BACKGROUND_PRESETS or "Custom"
    "custom_bg_color": "#FFFFFF",            # Used when background_preset == "Custom"
    "text_size": "Normal",                   # "Small" | "Normal" | "Large"
    "table_density": "Comfortable",          # "Compact" | "Comfortable" | "Spacious"
    "default_export_format": "xlsx",         # "xlsx" | "csv"
    "default_sort_order": "Ascending",       # "Ascending" | "Descending"
    "default_missing_position": "At the end",  # "At the end" | "At the beginning"
    "preview_page_size": 100,                # 50 | 100 | 250 | 500
    "max_recent_files": 15,                  # 5 | 10 | 15 | 20
    "last_seen_version": "",                 # Tracks first-launch / version upgrade welcome guide
}

# Column logical types
COL_TYPE_NUMERIC = "Numeric"
COL_TYPE_TEXT = "Text"
COL_TYPE_DATE = "Date"
COL_TYPE_EMPTY = "Empty"
VALID_COLUMN_TYPES = (COL_TYPE_NUMERIC, COL_TYPE_TEXT, COL_TYPE_DATE, COL_TYPE_EMPTY)

MISSING_DISPLAY_TEXT = "—"

"""General helper functions: PyInstaller-safe paths, number formatting, OS folder reveal."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Return the runtime root directory (supports both development and PyInstaller bundles)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def get_asset_path(*parts: str) -> Path:
    """Resolve a path inside the assets/ directory."""
    return get_project_root() / "assets" / Path(*parts)


def format_int(value: int) -> str:
    """Format an integer with thousands separators."""
    return f"{int(value):,}"


def format_number(value: float | int | None, decimals: int = 2) -> str:
    """Format a number cleanly without trailing .00 for whole numbers."""
    if value is None:
        return "—"
    try:
        fval = float(value)
    except (TypeError, ValueError):
        return str(value)
    if fval != fval:  # NaN
        return "—"
    if abs(fval - round(fval)) < 1e-9 and abs(fval) < 1e15:
        return f"{int(round(fval)):,}"
    return f"{fval:,.{decimals}f}"


def truncate_text(text: str, max_len: int = 48) -> str:
    """Truncate long labels neatly with an ellipsis."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def open_in_file_explorer(file_path: str | Path) -> bool:
    """Open Windows File Explorer highlighting the exported file, or its parent folder."""
    target = Path(file_path).resolve()
    try:
        if sys.platform == "win32":
            if target.exists() and target.is_file():
                subprocess.Popen(["explorer", "/select,", str(target)])
            else:
                os.startfile(str(target.parent if target.parent.exists() else target))  # type: ignore[attr-defined]
            return True
    except Exception:
        return False
    return False

"""User-friendly validation and error translation utilities for MiniSort."""

from __future__ import annotations

import os
from pathlib import Path

from utils.constants import MAX_FILE_SIZE_MB, SUPPORTED_EXTENSIONS


class MiniSortError(Exception):
    """Base user-facing exception with a clear, jargon-free message."""

    def __init__(self, user_message: str, technical_detail: str = "") -> None:
        super().__init__(user_message)
        self.user_message = user_message
        self.technical_detail = technical_detail


def validate_import_file(file_path: str | Path) -> Path:
    """Validate that a file exists, is readable, has a supported format, and is within size limits."""
    if not file_path or not str(file_path).strip():
        raise MiniSortError("Please select a spreadsheet file to import.")

    path = Path(file_path)
    if not path.exists():
        raise MiniSortError(
            f"The file '{path.name}' could not be found. It may have been moved, renamed, or deleted."
        )
    if not path.is_file():
        raise MiniSortError("The selected item is a folder, not a spreadsheet file.")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        supported_list = ", ".join(SUPPORTED_EXTENSIONS)
        raise MiniSortError(
            f"Unsupported file format '{ext or '(none)'}'. "
            f"MiniSort supports CSV and Excel files ({supported_list})."
        )

    try:
        size_bytes = path.stat().st_size
    except OSError as exc:
        raise MiniSortError(
            f"Could not read file information for '{path.name}'. Please check your permissions.",
            str(exc),
        ) from exc

    if size_bytes == 0:
        raise MiniSortError(
            f"The file '{path.name}' is completely empty. Please choose a file that contains data."
        )

    size_mb = size_bytes / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise MiniSortError(
            f"The file '{path.name}' is {size_mb:.1f} MB, which exceeds MiniSort's "
            f"recommended limit of {MAX_FILE_SIZE_MB} MB for smooth local processing. "
            "Try splitting the file into smaller parts first."
        )

    if not os.access(path, os.R_OK):
        raise MiniSortError(
            f"MiniSort does not have permission to read '{path.name}'. "
            "Check file permissions or copy the file to your Documents folder."
        )

    return path


def translate_exception(exc: Exception, context: str = "performing this action") -> str:
    """Convert any Python exception into a calm, beginner-friendly message."""
    if isinstance(exc, MiniSortError):
        return exc.user_message
    if isinstance(exc, PermissionError):
        return (
            f"Access was denied while {context}. "
            "If the file is open in Excel or another program, please close it and try again."
        )
    if isinstance(exc, FileNotFoundError):
        return f"A required file or folder could not be found while {context}."
    if isinstance(exc, MemoryError):
        return (
            "Your computer ran out of available memory while processing this dataset. "
            "Try closing other programs or working with a smaller spreadsheet."
        )
    if isinstance(exc, OSError):
        err_no = getattr(exc, "errno", None)
        if err_no == 28:  # ENOSPC
            return (
                "There is not enough free disk space to save the file. "
                "Please free up storage or choose a different drive."
            )
        return (
            f"A file system error occurred while {context}. "
            "Make sure the file is not locked by another application and that you have write permission."
        )
    if isinstance(exc, KeyError):
        return "We couldn't find the selected column. Please choose another column."
    if isinstance(exc, ValueError):
        return (
            f"Some values could not be processed while {context}. "
            "Please check your selections and try again."
        )
    return (
        f"Something unexpected happened while {context}. "
        "Your original file has not been modified. Technical details were saved to the local log."
    )


def sanitize_filename(name: str) -> str:
    """Remove characters that are invalid in Windows filenames."""
    invalid_chars = '<>:"/\\|?*'
    cleaned = "".join("_" if ch in invalid_chars else ch for ch in name).strip().strip(".")
    return cleaned or "MiniSort_Export"


def parse_number_input(raw: str, field_label: str = "value") -> float:
    """Parse user-entered numeric strings, allowing commas and whitespace."""
    if raw is None or not str(raw).strip():
        raise MiniSortError(f"Please enter a number for {field_label}.")
    cleaned = str(raw).strip().replace(",", "")
    try:
        return float(cleaned)
    except ValueError as exc:
        raise MiniSortError(
            f"'{raw}' is not a valid number for {field_label}. Please enter digits such as 500 or 12.5."
        ) from exc

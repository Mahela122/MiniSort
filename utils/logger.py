"""Privacy-safe local logging for MiniSort.

Logs technical diagnostics and error tracebacks to a local rotating log file
inside %APPDATA%/MiniSort/logs/ without ever recording spreadsheet cell contents.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from utils.constants import APP_NAME


def get_app_data_dir() -> Path:
    """Return a writable local application data directory on Windows."""
    appdata = os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
    if appdata:
        base = Path(appdata) / APP_NAME
    else:
        base = Path.home() / f".{APP_NAME.lower()}"
    try:
        base.mkdir(parents=True, exist_ok=True)
        return base
    except OSError:
        fallback = Path.cwd() / ".minisort_data"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def get_log_file_path() -> Path:
    """Return the path to the local rotating log file."""
    log_dir = get_app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "minisort.log"


def setup_logger(name: str = APP_NAME) -> logging.Logger:
    """Configure and return the application logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        handler = RotatingFileHandler(
            filename=str(get_log_file_path()),
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except OSError:
        # If filesystem logging is unavailable, attach a null handler so the app never fails.
        logger.addHandler(logging.NullHandler())

    return logger


def get_logger(module_name: str) -> logging.Logger:
    """Return a child logger under the MiniSort root logger."""
    setup_logger(APP_NAME)
    return logging.getLogger(f"{APP_NAME}.{module_name}")

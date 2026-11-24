"""Local JSON configuration and recent-files persistence for MiniSort."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from utils.constants import DEFAULT_SETTINGS, MAX_RECENT_FILES
from utils.logger import get_app_data_dir, get_logger

logger = get_logger("config")


class ConfigManager:
    """Manages local user preferences and recent files history in JSON."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or (get_app_data_dir() / "config.json")
        self._settings: dict[str, Any] = dict(DEFAULT_SETTINGS)
        self._recent_files: list[dict[str, str]] = []
        self.load()

    @property
    def config_path(self) -> Path:
        return self._config_path

    def load(self) -> None:
        """Load configuration from disk, falling back cleanly to defaults."""
        self._settings = dict(DEFAULT_SETTINGS)
        self._recent_files = []
        if not self._config_path.exists():
            return
        try:
            raw = json.loads(self._config_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                saved_settings = raw.get("settings", {})
                if isinstance(saved_settings, dict):
                    for key, default_val in DEFAULT_SETTINGS.items():
                        if key in saved_settings:
                            self._settings[key] = saved_settings[key]
                saved_recent = raw.get("recent_files", [])
                if isinstance(saved_recent, list):
                    self._recent_files = [
                        item for item in saved_recent
                        if isinstance(item, dict) and item.get("path")
                    ][:MAX_RECENT_FILES]
        except Exception as exc:
            logger.warning("Failed to read config file (%s); using defaults.", type(exc).__name__)

    def save(self) -> None:
        """Persist settings and recent files to disk atomically."""
        payload = {
            "settings": self._settings,
            "recent_files": self._recent_files,
        }
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self._config_path.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp_path.replace(self._config_path)
        except Exception as exc:
            logger.error("Failed to save config file: %s", type(exc).__name__)

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, DEFAULT_SETTINGS.get(key, default))

    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        self._settings[key] = value
        if key == "max_recent_files":
            limit = max(1, min(int(value), MAX_RECENT_FILES))
            self._recent_files = self._recent_files[:limit]
        if auto_save:
            self.save()

    def get_all_settings(self) -> dict[str, Any]:
        return dict(self._settings)

    def update_settings(self, updates: dict[str, Any]) -> None:
        for key, value in updates.items():
            if key in DEFAULT_SETTINGS:
                self._settings[key] = value
        limit = max(1, min(int(self._settings.get("max_recent_files", 15)), MAX_RECENT_FILES))
        self._recent_files = self._recent_files[:limit]
        self.save()

    def reset_settings(self) -> None:
        self._settings = dict(DEFAULT_SETTINGS)
        self.save()

    # Recent files management
    def get_recent_files(self) -> list[dict[str, str]]:
        return [dict(entry) for entry in self._recent_files]

    def add_recent_file(self, file_path: str, sheet_name: str | None = None) -> None:
        path_obj = Path(file_path).resolve()
        normalized = str(path_obj)
        file_type = path_obj.suffix.upper().lstrip(".") or "FILE"
        entry = {
            "name": path_obj.name,
            "path": normalized,
            "file_type": file_type,
            "sheet_name": sheet_name or "",
            "last_opened": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        # Remove existing entry for same path (case-insensitive on Windows)
        self._recent_files = [
            item for item in self._recent_files
            if item.get("path", "").lower() != normalized.lower()
        ]
        self._recent_files.insert(0, entry)
        limit = max(1, min(int(self._settings.get("max_recent_files", 15)), MAX_RECENT_FILES))
        self._recent_files = self._recent_files[:limit]
        self.save()

    def remove_recent_file(self, file_path: str) -> None:
        target = str(Path(file_path)).lower()
        self._recent_files = [
            item for item in self._recent_files
            if item.get("path", "").lower() != target
        ]
        self.save()

    def clear_recent_files(self) -> None:
        self._recent_files = []
        self.save()

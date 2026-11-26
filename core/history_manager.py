"""Memory-aware Undo/Redo history manager and original dataset preservation."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.models import OperationRecord
from utils.constants import MAX_UNDO_MEMORY_MB, MAX_UNDO_STEPS


@dataclass
class _HistorySnapshot:
    df: pd.DataFrame
    overrides: dict[str, str]
    record: OperationRecord
    approx_bytes: int


def _estimate_df_bytes(df: pd.DataFrame) -> int:
    try:
        return int(df.memory_usage(index=True, deep=False).sum())
    except Exception:
        return int(len(df) * max(1, len(df.columns)) * 16)


class HistoryManager:
    """Tracks dataset state snapshots with bounded RAM usage for Undo, Redo, and Comparison."""

    def __init__(
        self,
        max_steps: int = MAX_UNDO_STEPS,
        max_memory_mb: int = MAX_UNDO_MEMORY_MB,
    ) -> None:
        self._max_steps = max(2, int(max_steps))
        self._max_memory_bytes = max(16, int(max_memory_mb)) * 1024 * 1024
        self._original_df: pd.DataFrame | None = None
        self._original_overrides: dict[str, str] = {}
        self._undo_stack: list[_HistorySnapshot] = []
        self._redo_stack: list[_HistorySnapshot] = []
        self._current: _HistorySnapshot | None = None

    def reset_with_original(
        self,
        df: pd.DataFrame,
        overrides: dict[str, str] | None = None,
        description: str = "Imported dataset",
    ) -> None:
        """Initialize history with a newly imported dataset, keeping a safe copy as original."""
        clean_overrides = dict(overrides or {})
        self._original_df = df.copy(deep=True)
        self._original_overrides = dict(clean_overrides)
        record = OperationRecord(
            description=description,
            category="import",
            row_count_before=len(df),
            row_count_after=len(df),
            col_count_before=len(df.columns),
            col_count_after=len(df.columns),
        )
        self._current = _HistorySnapshot(
            df=df.copy(deep=True),
            overrides=dict(clean_overrides),
            record=record,
            approx_bytes=_estimate_df_bytes(df),
        )
        self._undo_stack.clear()
        self._redo_stack.clear()

    def clear(self) -> None:
        self._original_df = None
        self._original_overrides = {}
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._current = None

    @property
    def has_data(self) -> bool:
        return self._current is not None and self._original_df is not None

    @property
    def original_df(self) -> pd.DataFrame | None:
        return self._original_df

    @property
    def current_df(self) -> pd.DataFrame | None:
        return self._current.df if self._current is not None else None

    @property
    def current_overrides(self) -> dict[str, str]:
        return dict(self._current.overrides) if self._current is not None else {}

    @property
    def last_operation(self) -> OperationRecord | None:
        return self._current.record if self._current is not None else None

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def is_modified(self) -> bool:
        return self._current is not None and self._current.record.category != "import"

    def push(
        self,
        new_df: pd.DataFrame,
        description: str,
        category: str,
        overrides: dict[str, str] | None = None,
    ) -> OperationRecord:
        """Record a new dataset state, clearing redo history and respecting memory limits."""
        prev = self._current
        row_before = len(prev.df) if prev is not None else len(new_df)
        col_before = len(prev.df.columns) if prev is not None else len(new_df.columns)
        eff_overrides = dict(overrides) if overrides is not None else (
            dict(prev.overrides) if prev is not None else {}
        )

        if prev is not None:
            self._undo_stack.append(prev)

        record = OperationRecord(
            description=description,
            category=category,
            row_count_before=row_before,
            row_count_after=len(new_df),
            col_count_before=col_before,
            col_count_after=len(new_df.columns),
        )
        self._current = _HistorySnapshot(
            df=new_df.copy(deep=True),
            overrides=eff_overrides,
            record=record,
            approx_bytes=_estimate_df_bytes(new_df),
        )
        self._redo_stack.clear()
        self._enforce_limits()
        return record

    def _enforce_limits(self) -> None:
        """Keep undo stack within step count and RAM limits to avoid memory blowups."""
        while len(self._undo_stack) > self._max_steps:
            self._undo_stack.pop(0)

        total_bytes = sum(s.approx_bytes for s in self._undo_stack)
        # Always keep at least the single most recent undo snapshot if available
        while len(self._undo_stack) > 1 and total_bytes > self._max_memory_bytes:
            removed = self._undo_stack.pop(0)
            total_bytes -= removed.approx_bytes

    def undo(self) -> OperationRecord | None:
        """Restore the previous dataset state and return its OperationRecord."""
        if not self.can_undo or self._current is None:
            return None
        self._redo_stack.append(self._current)
        self._current = self._undo_stack.pop()
        return self._current.record

    def redo(self) -> OperationRecord | None:
        """Reapply the most recently undone state and return its OperationRecord."""
        if not self.can_redo or self._current is None:
            return None
        self._undo_stack.append(self._current)
        self._current = self._redo_stack.pop()
        self._enforce_limits()
        return self._current.record

    def restore_original(self) -> OperationRecord | None:
        """Reset working dataset back to the originally imported data (undoable!)."""
        if self._original_df is None:
            return None
        return self.push(
            new_df=self._original_df.copy(deep=True),
            description="Restored original imported dataset",
            category="import",
            overrides=dict(self._original_overrides),
        )

    def get_recent_operations(self) -> list[OperationRecord]:
        """Return chronological list of active operations from oldest to current."""
        records = [snap.record for snap in self._undo_stack]
        if self._current is not None:
            records.append(self._current.record)
        return records

    def get_undo_label(self) -> str:
        if not self.can_undo or self._current is None:
            return "Nothing to undo"
        return f"Undo: {self._current.record.description}"

    def get_redo_label(self) -> str:
        if not self.can_redo:
            return "Nothing to redo"
        return f"Redo: {self._redo_stack[-1].record.description}"

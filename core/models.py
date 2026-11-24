"""Data structures shared across MiniSort's core engines and UI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd


@dataclass
class ColumnInfo:
    """Metadata and detected logical type for a single dataset column."""

    name: str
    detected_type: str  # "Numeric" | "Text" | "Date" | "Empty"
    override_type: str | None = None
    missing_count: int = 0
    unique_count: int = 0
    sample_values: list[str] = field(default_factory=list)
    detection_note: str = ""

    @property
    def effective_type(self) -> str:
        return self.override_type or self.detected_type


@dataclass
class DatasetSummary:
    """High-level overview of the currently loaded dataset."""

    file_name: str
    file_path: str
    file_type: str
    sheet_name: str | None
    total_rows: int
    total_columns: int
    numeric_columns: int
    text_columns: int
    date_columns: int
    empty_columns: int
    missing_values: int
    duplicate_rows: int
    empty_rows: int
    column_infos: list[ColumnInfo] = field(default_factory=list)
    import_notices: list[str] = field(default_factory=list)


@dataclass
class SortCondition:
    """A single column sorting rule."""

    column: str
    ascending: bool = True


@dataclass
class FilterCondition:
    """A single column filter rule."""

    column: str
    operator: str
    value: str = ""
    value2: str = ""
    case_sensitive: bool = False


@dataclass
class OperationRecord:
    """One recorded state transition for Undo/Redo and Before/After comparison."""

    description: str
    category: str  # "import" | "sort" | "filter" | "clean" | "type"
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    row_count_before: int = 0
    row_count_after: int = 0
    col_count_before: int = 0
    col_count_after: int = 0


@dataclass
class LoadedDataset:
    """Result returned by the file handler after importing a CSV or Excel file."""

    df: pd.DataFrame
    file_path: str
    file_name: str
    file_type: str
    sheet_name: str | None = None
    available_sheets: list[str] = field(default_factory=list)
    encoding: str | None = None
    delimiter: str | None = None
    notices: list[str] = field(default_factory=list)


@dataclass
class ColumnStats:
    """Computed statistics for one column."""

    column: str
    column_type: str
    total_rows: int
    non_missing_count: int
    missing_count: int
    metrics: list[tuple[str, str]] = field(default_factory=list)
    top_values: list[tuple[str, int, float]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

"""Smart single-column & multi-column sorting engine with local sort suggestions."""

from __future__ import annotations

import re
import warnings
from typing import Any

import numpy as np
import pandas as pd

from core.data_detector import _try_parse_numeric_str
from core.models import ColumnInfo, SortCondition
from utils.constants import COL_TYPE_DATE, COL_TYPE_NUMERIC, COL_TYPE_TEXT
from utils.validators import MiniSortError


# Local rule-based suggestion patterns: (regex, priority_score, friendly_reason)
SUGGESTION_RULES: list[tuple[re.Pattern[str], int, str]] = [
    (re.compile(r"\b(employee|student|order|customer|product|invoice|item|record|user|member)[\s_-]*id\b", re.I), 100, "Record ID"),
    (re.compile(r"(^|[\s_-])id$", re.I), 92, "Identifier"),
    (re.compile(r"\b(employee|student|customer|client|full|first|last|product|item)[\s_-]*name\b", re.I), 95, "Name"),
    (re.compile(r"^name$", re.I), 90, "Name"),
    (re.compile(r"\b(department|dept|division|team|category|class|section|region|status)\b", re.I), 85, "Group / Category"),
    (re.compile(r"\b(salary|wage|pay|sales|revenue|amount|total|price|cost|profit|balance|budget)\b", re.I), 88, "Amount"),
    (re.compile(r"\b(marks|score|grade|gpa|points|rank|rating|percentage|percent)\b", re.I), 88, "Score / Grade"),
    (re.compile(r"\b(date|dob|joined|joining|created|updated|order[\s_-]*date|hire[\s_-]*date|deadline|timestamp)\b", re.I), 84, "Date"),
    (re.compile(r"\b(quantity|qty|count|units|stock|age|year)\b", re.I), 76, "Number"),
]


def suggest_sort_columns(
    column_infos: list[ColumnInfo],
    max_suggestions: int = 5,
) -> list[tuple[str, str]]:
    """Suggest useful sorting columns using local column-name and data-type heuristics.

    Returns a list of (column_name, short_reason) tuples sorted by usefulness.
    """
    scored: list[tuple[int, int, str, str]] = []

    for idx, info in enumerate(column_infos):
        if info.effective_type == "Empty":
            continue
        col_name = info.name
        best_score = 0
        reason = info.effective_type

        for pattern, score, label in SUGGESTION_RULES:
            if pattern.search(col_name):
                if score > best_score:
                    best_score = score
                    reason = label

        # Type-based boost when no specific name pattern matched
        if best_score == 0:
            if info.effective_type == COL_TYPE_DATE:
                best_score = 60
                reason = "Date"
            elif info.effective_type == COL_TYPE_NUMERIC:
                best_score = 55
                reason = "Numeric"
            elif info.effective_type == COL_TYPE_TEXT and info.unique_count > 1:
                best_score = 45
                reason = "Alphabetical"
            else:
                best_score = 20
                reason = info.effective_type

        # Slight penalty for columns that are mostly missing
        if info.unique_count <= 1 and best_score < 80:
            best_score -= 30

        scored.append((best_score, -idx, col_name, reason))

    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [(col, reason) for _score, _neg_idx, col, reason in scored[:max_suggestions]]


def _build_sort_key_series(
    series: pd.Series,
    col_type: str,
    case_insensitive: bool = True,
) -> pd.Series:
    """Build a temporary sort-key Series without mutating the original dataset values."""
    if col_type == COL_TYPE_NUMERIC:
        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
            return series.astype("float64")
        # Vectorized fast path first, then flexible fallback for currency/commas
        numeric = pd.to_numeric(series, errors="coerce")
        non_na_orig = series.notna()
        if non_na_orig.any() and numeric[non_na_orig].isna().any():
            parsed = series.map(
                lambda v: (
                    float(v)
                    if isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool)
                    else (_try_parse_numeric_str(str(v)) if pd.notna(v) else np.nan)
                )
            )
            return pd.Series(parsed, index=series.index, dtype="float64")
        return numeric.astype("float64")

    if col_type == COL_TYPE_DATE:
        if pd.api.types.is_datetime64_any_dtype(series):
            return series
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            try:
                return pd.to_datetime(series, format="mixed", errors="coerce")
            except TypeError:
                return pd.to_datetime(series, errors="coerce")

    # Default: Text / Alphabetical sorting
    is_missing = series.isna()
    text_vals = series.astype(str)
    if case_insensitive:
        text_vals = text_vals.str.strip().str.casefold()
    else:
        text_vals = text_vals.str.strip()
    # Treat blank strings as missing for consistent missing-value placement
    is_missing = is_missing | text_vals.eq("")
    return text_vals.mask(is_missing, np.nan)


def _stable_sort_indices(
    key_series: pd.Series,
    ascending: bool,
    na_position: str,
) -> np.ndarray:
    """Return a stable positional permutation for key_series honoring na_position ('last' or 'first')."""
    n = len(key_series)
    if n <= 1:
        return np.arange(n, dtype=np.int64)

    is_na = key_series.isna().to_numpy(dtype=bool)
    non_na_pos = np.flatnonzero(~is_na)
    na_pos = np.flatnonzero(is_na)

    if len(non_na_pos) > 1:
        non_na_vals = key_series.iloc[non_na_pos]
        temp = pd.Series(non_na_vals.to_numpy(), index=non_na_pos)
        sorted_non_na_pos = temp.sort_values(ascending=ascending, kind="mergesort").index.to_numpy(dtype=np.int64)
    else:
        sorted_non_na_pos = non_na_pos.astype(np.int64)

    if na_position == "first":
        return np.concatenate([na_pos.astype(np.int64), sorted_non_na_pos])
    return np.concatenate([sorted_non_na_pos, na_pos.astype(np.int64)])


def sort_dataframe(
    df: pd.DataFrame,
    conditions: list[SortCondition],
    column_types: dict[str, str] | None = None,
    na_position: str = "last",
    case_insensitive: bool = True,
) -> pd.DataFrame:
    """Sort complete rows by one or more SortConditions without mutating input DataFrame.

    Args:
        df: Input dataset.
        conditions: Ordered list of SortCondition (primary first, secondary next, ...).
        column_types: Map of column name -> effective type ("Numeric", "Text", "Date", "Empty").
        na_position: "last" (default) or "first".
        case_insensitive: Whether text sorting ignores uppercase/lowercase differences.
    """
    if df is None:
        raise MiniSortError("Please import a dataset before sorting.")
    if not conditions:
        raise MiniSortError("Please select at least one column to sort by.")

    seen_cols: set[str] = set()
    for cond in conditions:
        if cond.column not in df.columns:
            raise MiniSortError(
                f"We couldn't find the selected column '{cond.column}'. Please choose another column."
            )
        if cond.column in seen_cols:
            raise MiniSortError(
                f"The column '{cond.column}' is listed more than once. Please choose different columns for each sorting level."
            )
        seen_cols.add(cond.column)

    if na_position not in ("last", "first"):
        na_position = "last"

    if len(df) <= 1:
        return df.copy().reset_index(drop=True)

    col_types = column_types or {}
    order = np.arange(len(df), dtype=np.int64)

    # Apply stable mergesort from least-significant condition to most-significant condition
    for cond in reversed(conditions):
        col_type = col_types.get(cond.column, COL_TYPE_TEXT)
        current_series = df[cond.column].iloc[order].reset_index(drop=True)
        key_series = _build_sort_key_series(
            current_series,
            col_type=col_type,
            case_insensitive=case_insensitive,
        )
        perm = _stable_sort_indices(key_series, ascending=cond.ascending, na_position=na_position)
        order = order[perm]

    return df.iloc[order].reset_index(drop=True)


def describe_sort_conditions(conditions: list[SortCondition]) -> str:
    """Build a friendly human-readable summary like 'Sorted by Department (Asc), Employee ID (Asc)'."""
    parts = [
        f"{cond.column} ({'Ascending' if cond.ascending else 'Descending'})"
        for cond in conditions
    ]
    return "Sorted by " + ", then ".join(parts)

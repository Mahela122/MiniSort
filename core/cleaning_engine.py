"""Data cleaning engine for MiniSort.

Supports duplicate removal (full row or selected columns), empty row removal,
empty column removal, missing value replacement, whitespace trimming/normalization,
and text case formatting without mutating the source DataFrame.
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

from core.data_detector import get_empty_columns, get_empty_row_mask
from utils.validators import MiniSortError, parse_number_input


def count_duplicates(df: pd.DataFrame, subset: list[str] | None = None) -> int:
    """Return the number of duplicate rows (either across all columns or a subset)."""
    if df is None or df.empty:
        return 0
    if subset:
        missing_cols = [c for c in subset if c not in df.columns]
        if missing_cols:
            raise MiniSortError(f"We couldn't find column '{missing_cols[0]}'. Please select valid columns.")
    try:
        return int(df.duplicated(subset=subset or None, keep="first").sum())
    except TypeError:
        sub_df = df[subset] if subset else df
        return int(sub_df.astype(str).duplicated(keep="first").sum())


def remove_duplicates(
    df: pd.DataFrame,
    subset: list[str] | None = None,
) -> tuple[pd.DataFrame, int]:
    """Remove duplicate rows while keeping the first occurrence."""
    if df is None:
        raise MiniSortError("Please import a dataset before cleaning.")
    if subset:
        for col in subset:
            if col not in df.columns:
                raise MiniSortError(f"We couldn't find the selected column '{col}'. Please choose another column.")
    before = len(df)
    try:
        cleaned = df.drop_duplicates(subset=subset or None, keep="first").reset_index(drop=True)
    except TypeError:
        sub_df = df[subset] if subset else df
        keep_mask = ~sub_df.astype(str).duplicated(keep="first")
        cleaned = df.loc[keep_mask].copy().reset_index(drop=True)
    removed = before - len(cleaned)
    return cleaned, removed


def remove_empty_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove rows where every cell is missing or whitespace-only."""
    if df is None:
        raise MiniSortError("Please import a dataset before cleaning.")
    if df.empty:
        return df.copy(), 0
    empty_mask = get_empty_row_mask(df)
    removed = int(empty_mask.sum())
    cleaned = df.loc[~empty_mask].copy().reset_index(drop=True)
    return cleaned, removed


def remove_empty_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Remove columns where every cell is missing or whitespace-only."""
    if df is None:
        raise MiniSortError("Please import a dataset before cleaning.")
    empty_cols = get_empty_columns(df)
    if not empty_cols:
        return df.copy(), []
    cleaned = df.drop(columns=empty_cols).copy()
    return cleaned, empty_cols


def get_missing_counts_by_column(df: pd.DataFrame) -> list[tuple[str, int]]:
    """Return (column_name, missing_count) for every column with at least 1 missing cell."""
    if df is None or df.empty:
        return []
    counts: list[tuple[str, int]] = []
    for col in df.columns:
        cnt = int(df[col].isna().sum())
        if cnt > 0:
            counts.append((str(col), cnt))
    return counts


def replace_missing_values(
    df: pd.DataFrame,
    columns: list[str] | None,
    mode: str,
    custom_value: str = "",
) -> tuple[pd.DataFrame, int]:
    """Replace missing cells in selected columns (or all columns if None).

    Modes:
      - "empty_text": replace missing values with ""
      - "custom_text": replace missing values with custom_value string
      - "numeric_value": replace missing values with parsed float/int from custom_value
      - "column_mean": replace missing values in numeric columns with column mean
      - "column_median": replace missing values in numeric columns with column median
    """
    if df is None:
        raise MiniSortError("Please import a dataset before cleaning.")

    target_cols = list(columns) if columns else list(df.columns)
    for col in target_cols:
        if col not in df.columns:
            raise MiniSortError(f"We couldn't find the selected column '{col}'. Please choose another column.")

    cleaned = df.copy()
    replaced_total = 0

    parsed_num: float | int | None = None
    if mode == "numeric_value":
        val_f = parse_number_input(custom_value, "replacement number")
        parsed_num = int(val_f) if float(val_f).is_integer() else val_f

    for col in target_cols:
        series = cleaned[col]
        na_mask = series.isna()
        missing_count = int(na_mask.sum())
        if missing_count == 0:
            continue

        if mode == "empty_text":
            if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
                cleaned[col] = series.astype(object).where(~na_mask, "")
            else:
                cleaned[col] = series.fillna("")
            replaced_total += missing_count

        elif mode == "custom_text":
            if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
                cleaned[col] = series.astype(object).where(~na_mask, custom_value)
            else:
                cleaned[col] = series.fillna(custom_value)
            replaced_total += missing_count

        elif mode == "numeric_value":
            assert parsed_num is not None
            if pd.api.types.is_integer_dtype(series):
                if isinstance(parsed_num, int):
                    cleaned[col] = series.fillna(parsed_num)
                else:
                    cleaned[col] = series.astype("float64").fillna(parsed_num)
            elif pd.api.types.is_float_dtype(series):
                cleaned[col] = series.fillna(float(parsed_num))
            else:
                # Try numeric column conversion or fill as string/object safely
                if pd.api.types.is_string_dtype(series):
                    cleaned[col] = series.fillna(str(parsed_num))
                else:
                    cleaned[col] = series.astype(object).where(~na_mask, parsed_num)
            replaced_total += missing_count

        elif mode in ("column_mean", "column_median"):
            numeric_vals = pd.to_numeric(series, errors="coerce").dropna()
            if numeric_vals.empty:
                continue
            stat_val = float(numeric_vals.mean() if mode == "column_mean" else numeric_vals.median())
            stat_val = round(stat_val, 4)
            if pd.api.types.is_integer_dtype(series):
                cleaned[col] = series.astype("float64").fillna(stat_val)
            elif pd.api.types.is_float_dtype(series):
                cleaned[col] = series.fillna(stat_val)
            else:
                cleaned[col] = series.astype(object).where(~na_mask, stat_val)
            replaced_total += missing_count
        else:
            raise MiniSortError("Please choose a valid replacement option for missing values.")

    return cleaned, replaced_total


def remove_extra_spaces(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    normalize_internal: bool = True,
) -> tuple[pd.DataFrame, int]:
    """Trim leading and trailing spaces from text cells, optionally normalizing repeated internal spaces."""
    if df is None:
        raise MiniSortError("Please import a dataset before cleaning.")

    target_cols = list(columns) if columns else list(df.columns)
    for col in target_cols:
        if col not in df.columns:
            raise MiniSortError(f"We couldn't find the selected column '{col}'. Please choose another column.")

    cleaned = df.copy()
    modified_cells = 0
    multi_space_re = re.compile(r"[ \t]{2,}")

    for col in target_cols:
        series = cleaned[col]
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
            continue

        if pd.api.types.is_string_dtype(series):
            updated = series.str.strip()
            if normalize_internal:
                updated = updated.str.replace(r"[ \t]{2,}", " ", regex=True)
            changed = series.notna() & (updated != series)
            count = int(changed.sum())
            if count > 0:
                cleaned[col] = updated
                modified_cells += count
        elif series.dtype == object:
            new_vals: list[Any] = []
            col_changed = 0
            for val in series.tolist():
                if isinstance(val, str):
                    trimmed = val.strip()
                    if normalize_internal:
                        trimmed = multi_space_re.sub(" ", trimmed)
                    if trimmed != val:
                        col_changed += 1
                    new_vals.append(trimmed)
                else:
                    new_vals.append(val)
            if col_changed > 0:
                cleaned[col] = pd.Series(new_vals, index=series.index, dtype=object)
                modified_cells += col_changed

    return cleaned, modified_cells


def format_text_case(
    df: pd.DataFrame,
    columns: list[str],
    case_mode: str,
) -> tuple[pd.DataFrame, int]:
    """Convert text cells in selected columns to uppercase, lowercase, or title case."""
    if df is None:
        raise MiniSortError("Please import a dataset before cleaning.")
    if not columns:
        raise MiniSortError("Please select at least one text column to format.")
    if case_mode not in ("upper", "lower", "title"):
        raise MiniSortError("Please choose Uppercase, Lowercase, or Title Case.")

    for col in columns:
        if col not in df.columns:
            raise MiniSortError(f"We couldn't find the selected column '{col}'. Please choose another column.")

    cleaned = df.copy()
    modified_cells = 0

    for col in columns:
        series = cleaned[col]
        if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
            continue

        if pd.api.types.is_string_dtype(series):
            if case_mode == "upper":
                updated = series.str.upper()
            elif case_mode == "lower":
                updated = series.str.lower()
            else:
                updated = series.str.title()
            changed = series.notna() & (updated != series)
            count = int(changed.sum())
            if count > 0:
                cleaned[col] = updated
                modified_cells += count
        elif series.dtype == object:
            new_vals: list[Any] = []
            col_changed = 0
            for val in series.tolist():
                if isinstance(val, str):
                    if case_mode == "upper":
                        formatted = val.upper()
                    elif case_mode == "lower":
                        formatted = val.lower()
                    else:
                        formatted = val.title()
                    if formatted != val:
                        col_changed += 1
                    new_vals.append(formatted)
                else:
                    new_vals.append(val)
            if col_changed > 0:
                cleaned[col] = pd.Series(new_vals, index=series.index, dtype=object)
                modified_cells += col_changed

    return cleaned, modified_cells

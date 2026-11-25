"""Dataset filtering engine supporting text, numeric, date, and multi-condition filters."""

from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd

from core.data_detector import _try_parse_numeric_str
from core.models import FilterCondition
from utils.constants import COL_TYPE_DATE, COL_TYPE_NUMERIC, COL_TYPE_TEXT
from utils.validators import MiniSortError, parse_number_input

TEXT_OPERATORS = [
    "Contains",
    "Does not contain",
    "Equals",
    "Starts with",
    "Ends with",
]

NUMERIC_OPERATORS = [
    "Greater than",
    "Less than",
    "Equal to",
    "Between",
]

DATE_OPERATORS = [
    "Before",
    "After",
    "Between",
]


def get_operators_for_type(col_type: str) -> list[str]:
    if col_type == COL_TYPE_NUMERIC:
        return list(NUMERIC_OPERATORS)
    if col_type == COL_TYPE_DATE:
        return list(DATE_OPERATORS)
    return list(TEXT_OPERATORS)


def _to_numeric_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
        return series.astype("float64")
    numeric = pd.to_numeric(series, errors="coerce")
    non_na = series.notna()
    if non_na.any() and numeric[non_na].isna().any():
        parsed = series.map(
            lambda v: (
                float(v)
                if isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool)
                else (_try_parse_numeric_str(str(v)) if pd.notna(v) else np.nan)
            )
        )
        return pd.Series(parsed, index=series.index, dtype="float64")
    return numeric.astype("float64")


def _to_date_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        try:
            return pd.to_datetime(series, format="mixed", errors="coerce")
        except TypeError:
            return pd.to_datetime(series, errors="coerce")


def _parse_date_input(raw: str, label: str = "date") -> pd.Timestamp:
    if not raw or not raw.strip():
        raise MiniSortError(f"Please enter a {label} (for example, 2024-06-15).")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        ts = pd.to_datetime(raw.strip(), errors="coerce")
    if pd.isna(ts):
        raise MiniSortError(
            f"'{raw}' is not a valid date for {label}. Please use a format like YYYY-MM-DD (for example, 2024-06-15)."
        )
    return pd.Timestamp(ts)


def _evaluate_condition(
    df: pd.DataFrame,
    cond: FilterCondition,
    col_type: str,
) -> pd.Series:
    if cond.column not in df.columns:
        raise MiniSortError(
            f"We couldn't find the selected column '{cond.column}'. Please choose another column."
        )

    series = df[cond.column]
    op = cond.operator

    # Date operators (checked before numeric because "Between" applies to both dates and numbers)
    if (col_type == COL_TYPE_DATE and op in DATE_OPERATORS) or op in ("Before", "After"):
        date_series = _to_date_series(series)
        # Normalize to midnight when comparing pure dates so "Between" includes the entire end day
        norm_series = date_series.dt.normalize()
        d1 = _parse_date_input(cond.value, f"'{cond.column}'").normalize()
        if op == "Before":
            return (norm_series < d1).fillna(False)
        if op == "After":
            return (norm_series > d1).fillna(False)
        if op == "Between":
            d2 = _parse_date_input(cond.value2, f"'{cond.column}' (end date)").normalize()
            start, end = (d1, d2) if d1 <= d2 else (d2, d1)
            return ((norm_series >= start) & (norm_series <= end)).fillna(False)

    # Numeric operators
    if op in NUMERIC_OPERATORS:
        num_series = _to_numeric_series(series)
        val1 = parse_number_input(cond.value, f"'{cond.column}'")
        if op == "Greater than":
            return (num_series > val1).fillna(False)
        if op == "Less than":
            return (num_series < val1).fillna(False)
        if op == "Equal to":
            return (num_series == val1).fillna(False)
        if op == "Between":
            val2 = parse_number_input(cond.value2, f"'{cond.column}' (upper limit)")
            low, high = (val1, val2) if val1 <= val2 else (val2, val1)
            return ((num_series >= low) & (num_series <= high)).fillna(False)

    # Text operators
    if op in TEXT_OPERATORS:
        if cond.value == "":
            raise MiniSortError(f"Please enter text to filter '{cond.column}'.")
        is_na = series.isna()
        str_series = series.fillna("").astype(str)
        target = str(cond.value)
        if not cond.case_sensitive:
            str_series = str_series.str.casefold()
            target = target.casefold()

        if op == "Contains":
            return (~is_na) & str_series.str.contains(target, regex=False)
        if op == "Does not contain":
            return is_na | (~str_series.str.contains(target, regex=False))
        if op == "Equals":
            return (~is_na) & (str_series.str.strip() == target.strip())
        if op == "Starts with":
            return (~is_na) & str_series.str.startswith(target)
        if op == "Ends with":
            return (~is_na) & str_series.str.endswith(target)

    raise MiniSortError(f"Unsupported filter condition '{op}'. Please choose a valid filter option.")


def filter_dataframe(
    df: pd.DataFrame,
    conditions: list[FilterCondition],
    column_types: dict[str, str] | None = None,
    match_all: bool = True,
) -> pd.DataFrame:
    """Apply one or more filter conditions and return a new filtered DataFrame.

    Never modifies the input DataFrame.
    """
    if df is None:
        raise MiniSortError("Please import a dataset before filtering.")
    if not conditions:
        raise MiniSortError("Please add at least one filter condition before applying.")

    col_types = column_types or {}
    if len(df) == 0:
        return df.copy().reset_index(drop=True)

    combined: pd.Series | None = None
    for cond in conditions:
        col_type = col_types.get(cond.column, COL_TYPE_TEXT)
        mask = _evaluate_condition(df, cond, col_type)
        if combined is None:
            combined = mask
        else:
            combined = (combined & mask) if match_all else (combined | mask)

    assert combined is not None
    return df.loc[combined].copy().reset_index(drop=True)


def describe_filters(conditions: list[FilterCondition], match_all: bool = True) -> str:
    count = len(conditions)
    if count == 1:
        c = conditions[0]
        if c.operator == "Between":
            return f"Filtered: {c.column} {c.operator.lower()} {c.value} and {c.value2}"
        return f"Filtered: {c.column} {c.operator.lower()} '{c.value}'"
    joiner = "all" if match_all else "any"
    return f"Applied {count} filters (matching {joiner})"

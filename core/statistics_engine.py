"""Column-level statistical summary engine for numeric, text, date, and empty columns."""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from core.data_detector import _try_parse_numeric_str
from core.models import ColumnStats
from utils.constants import COL_TYPE_DATE, COL_TYPE_EMPTY, COL_TYPE_NUMERIC, COL_TYPE_TEXT
from utils.helpers import format_int, format_number
from utils.validators import MiniSortError


def compute_column_statistics(
    df: pd.DataFrame,
    column: str,
    col_type: str,
) -> ColumnStats:
    """Compute beginner-friendly statistics appropriate for a column's effective data type."""
    if df is None:
        raise MiniSortError("Please import a dataset to view statistics.")
    if column not in df.columns:
        raise MiniSortError(f"We couldn't find the selected column '{column}'. Please choose another column.")

    series = df[column]
    total_rows = int(len(series))
    missing_count = int(series.isna().sum())
    non_missing_count = total_rows - missing_count

    if col_type == COL_TYPE_EMPTY or non_missing_count == 0:
        return ColumnStats(
            column=column,
            column_type=COL_TYPE_EMPTY,
            total_rows=total_rows,
            non_missing_count=0,
            missing_count=missing_count,
            metrics=[
                ("Total Rows", format_int(total_rows)),
                ("Filled Values", "0"),
                ("Missing Values", format_int(missing_count)),
            ],
        )

    if col_type == COL_TYPE_NUMERIC:
        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
            num_series = series.astype("float64").dropna()
        else:
            parsed = pd.to_numeric(series, errors="coerce")
            non_na = series.notna()
            if non_na.any() and parsed[non_na].isna().any():
                parsed = series.map(
                    lambda v: (
                        float(v)
                        if isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool)
                        else (_try_parse_numeric_str(str(v)) if pd.notna(v) else np.nan)
                    )
                ).astype("float64")
            num_series = parsed.dropna()

        valid_count = int(len(num_series))
        if valid_count == 0:
            return ColumnStats(
                column=column,
                column_type=COL_TYPE_NUMERIC,
                total_rows=total_rows,
                non_missing_count=0,
                missing_count=missing_count,
                metrics=[
                    ("Count", "0"),
                    ("Missing Values", format_int(missing_count)),
                ],
            )

        total_sum = float(num_series.sum())
        avg_val = float(num_series.mean())
        min_val = float(num_series.min())
        max_val = float(num_series.max())
        median_val = float(num_series.median())

        return ColumnStats(
            column=column,
            column_type=COL_TYPE_NUMERIC,
            total_rows=total_rows,
            non_missing_count=valid_count,
            missing_count=missing_count,
            metrics=[
                ("Count", format_int(valid_count)),
                ("Sum", format_number(total_sum)),
                ("Average", format_number(avg_val)),
                ("Minimum", format_number(min_val)),
                ("Maximum", format_number(max_val)),
                ("Median", format_number(median_val)),
            ],
            extra={
                "count": valid_count,
                "sum": total_sum,
                "average": avg_val,
                "min": min_val,
                "max": max_val,
                "median": median_val,
            },
        )

    if col_type == COL_TYPE_DATE:
        if pd.api.types.is_datetime64_any_dtype(series):
            dt_series = series.dropna()
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                try:
                    dt_series = pd.to_datetime(series, format="mixed", errors="coerce").dropna()
                except TypeError:
                    dt_series = pd.to_datetime(series, errors="coerce").dropna()

        valid_count = int(len(dt_series))
        if valid_count == 0:
            return ColumnStats(
                column=column,
                column_type=COL_TYPE_DATE,
                total_rows=total_rows,
                non_missing_count=0,
                missing_count=missing_count,
                metrics=[
                    ("Valid Dates", "0"),
                    ("Missing Values", format_int(missing_count)),
                ],
            )

        earliest = pd.Timestamp(dt_series.min())
        latest = pd.Timestamp(dt_series.max())
        span_days = int((latest.normalize() - earliest.normalize()).days)

        return ColumnStats(
            column=column,
            column_type=COL_TYPE_DATE,
            total_rows=total_rows,
            non_missing_count=valid_count,
            missing_count=missing_count,
            metrics=[
                ("Earliest Date", earliest.strftime("%Y-%m-%d")),
                ("Latest Date", latest.strftime("%Y-%m-%d")),
                ("Valid Dates", format_int(valid_count)),
                ("Date Range", f"{format_int(span_days)} days"),
                ("Missing Values", format_int(missing_count)),
            ],
            extra={
                "earliest": earliest.strftime("%Y-%m-%d"),
                "latest": latest.strftime("%Y-%m-%d"),
                "span_days": span_days,
                "count": valid_count,
            },
        )

    # Text column statistics
    non_null_str = series.dropna().astype(str).str.strip()
    non_null_str = non_null_str[non_null_str != ""]
    total_vals = int(len(non_null_str))
    unique_vals = int(non_null_str.nunique()) if total_vals > 0 else 0

    top_values: list[tuple[str, int, float]] = []
    if total_vals > 0:
        vc = non_null_str.value_counts().head(5)
        for val_label, cnt in vc.items():
            pct = (int(cnt) / total_vals) * 100.0
            top_values.append((str(val_label), int(cnt), pct))

    most_common_label = top_values[0][0] if top_values else "—"
    return ColumnStats(
        column=column,
        column_type=COL_TYPE_TEXT,
        total_rows=total_rows,
        non_missing_count=total_vals,
        missing_count=missing_count,
        metrics=[
            ("Total Values", format_int(total_vals)),
            ("Unique Values", format_int(unique_vals)),
            ("Most Frequent", most_common_label if len(most_common_label) <= 22 else most_common_label[:21] + "…"),
            ("Missing Values", format_int(missing_count)),
        ],
        top_values=top_values,
        extra={
            "total_values": total_vals,
            "unique_values": unique_vals,
            "most_frequent": most_common_label,
        },
    )

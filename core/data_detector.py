"""Automatic dataset structure & column type detection with manual override support.

Protects number-like identifiers (postal codes, phone numbers, zero-padded IDs)
from being blindly converted to numbers, while cleanly recognizing true Numeric,
Date, Text, and Empty columns.
"""

from __future__ import annotations

import datetime as dt
import re
import warnings
from typing import Any

import numpy as np
import pandas as pd

from core.models import ColumnInfo, DatasetSummary
from utils.constants import (
    COL_TYPE_DATE,
    COL_TYPE_EMPTY,
    COL_TYPE_NUMERIC,
    COL_TYPE_TEXT,
    VALID_COLUMN_TYPES,
)

# Column header tokens that strongly indicate text identifiers even if all digits
TEXT_IDENTIFIER_TOKENS = {
    "phone",
    "telephone",
    "tel",
    "mobile",
    "cell",
    "fax",
    "zip",
    "zipcode",
    "postal",
    "postcode",
    "ssn",
    "sin",
    "isbn",
    "sku",
    "barcode",
    "upc",
    "ean",
    "iban",
    "swift",
    "passport",
    "cnic",
    "nic",
    "serial",
    "card",
    "account_no",
    "account_number",
    "emp_code",
    "code",
}

DATE_TOKEN_PATTERN = re.compile(
    r"(\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4})|"
    r"(\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b)",
    re.IGNORECASE,
)

NUMERIC_CLEAN_PATTERN = re.compile(r"^\s*[\$€£¥]?\s*([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*$")
LEADING_ZERO_ID_PATTERN = re.compile(r"^0\d+$")


def _header_tokens(col_name: str) -> set[str]:
    normalized = re.sub(r"[^a-zA-Z0-9]+", " ", str(col_name).lower()).strip()
    tokens = set(normalized.split())
    underscore = normalized.replace(" ", "_")
    tokens.add(underscore)
    return tokens


def _is_missing_value(val: Any) -> bool:
    if val is None:
        return True
    try:
        if pd.isna(val):
            return True
    except (TypeError, ValueError):
        pass
    if isinstance(val, str) and val == "":
        return True
    return False


def _try_parse_numeric_str(text: str) -> float | None:
    match = NUMERIC_CLEAN_PATTERN.match(text)
    if not match:
        return None
    raw_num = match.group(1).replace(",", "")
    try:
        val = float(raw_num)
        return val if np.isfinite(val) else None
    except ValueError:
        return None


def _parse_dates_safe(series: pd.Series) -> pd.Series:
    """Parse date-like strings safely without noisy pandas format warnings."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        try:
            return pd.to_datetime(series, format="mixed", errors="coerce")
        except TypeError:
            return pd.to_datetime(series, errors="coerce")


def detect_column_type(col_name: str, series: pd.Series) -> tuple[str, str]:
    """Detect the logical type of a single column and provide a short explanation note."""
    non_null = series.dropna()
    # Filter out empty strings if any remained
    if len(non_null) > 0:
        non_empty_mask = non_null.map(lambda v: not (isinstance(v, str) and v.strip() == ""))
        non_null = non_null[non_empty_mask]

    if len(non_null) == 0:
        return COL_TYPE_EMPTY, "All cells in this column are empty."

    # Sample up to 2,000 non-empty values for fast detection on large datasets
    sample = non_null.iloc[:2000] if len(non_null) > 2000 else non_null
    sample_list = sample.tolist()

    # 1. Native datetime / date column
    if pd.api.types.is_datetime64_any_dtype(series):
        return COL_TYPE_DATE, "Detected native date/time values."

    datetime_count = sum(
        1 for v in sample_list if isinstance(v, (dt.datetime, dt.date, pd.Timestamp))
    )
    if datetime_count / len(sample_list) >= 0.85:
        return COL_TYPE_DATE, "Detected Excel date values."

    # 2. Check header-based text identifier protection (phone, postal, zip, code, etc.)
    tokens = _header_tokens(col_name)
    if tokens & TEXT_IDENTIFIER_TOKENS:
        return COL_TYPE_TEXT, "Kept as Text (identifier pattern such as phone, postal code, or code)."

    # 3. Inspect raw string representations for leading zeros (e.g. '02108', '00123')
    str_values = [str(v).strip() for v in sample_list]
    has_leading_zero_codes = any(
        isinstance(raw, str) and LEADING_ZERO_ID_PATTERN.match(raw.strip())
        for raw in sample_list
    )
    if has_leading_zero_codes:
        return COL_TYPE_TEXT, "Kept as Text to preserve leading zeros."

    # 4. Native numeric dtype (excluding booleans)
    if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
        return COL_TYPE_NUMERIC, "Detected numeric values."

    # 5. Native Python int/float objects (e.g. from openpyxl object dtype)
    native_num_count = sum(
        1 for v in sample_list if isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool)
    )
    if native_num_count == len(sample_list):
        return COL_TYPE_NUMERIC, "Detected numeric values."

    # 6. Check string-based numeric values (allowing commas and currency symbols)
    parsed_num_count = sum(
        1
        for v, s in zip(sample_list, str_values)
        if (
            (isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool))
            or _try_parse_numeric_str(s) is not None
        )
    )
    if parsed_num_count / len(sample_list) >= 0.85:
        if "id" in tokens:
            return (
                COL_TYPE_NUMERIC,
                "Detected numeric IDs (change to Text if you want text-style sorting).",
            )
        return COL_TYPE_NUMERIC, "Detected numeric values."

    # 7. Check date strings (must contain date separators or month names so plain numbers aren't misread)
    date_like_count = sum(1 for s in str_values if DATE_TOKEN_PATTERN.search(s))
    if date_like_count / len(sample_list) >= 0.80:
        parsed_dates = _parse_dates_safe(pd.Series(str_values))
        if parsed_dates.notna().mean() >= 0.85:
            return COL_TYPE_DATE, "Detected date values."

    return COL_TYPE_TEXT, "Detected text values."


def coerce_dataframe_types(
    df: pd.DataFrame,
    column_infos: list[ColumnInfo],
) -> pd.DataFrame:
    """Safely convert clean Numeric/Date columns to proper types without losing mixed raw values."""
    result = df.copy()
    for info in column_infos:
        col = info.name
        if col not in result.columns:
            continue
        series = result[col]
        eff_type = info.effective_type

        if eff_type == COL_TYPE_NUMERIC:
            if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
                continue
            non_null_mask = series.notna()
            if not non_null_mask.any():
                continue
            # Try parsing cleanly without destroying any non-numeric text entries
            cleaned = series.map(
                lambda v: (
                    float(v)
                    if isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(v, bool)
                    else (_try_parse_numeric_str(str(v)) if pd.notna(v) else np.nan)
                )
            )
            # Only convert column dtype if ALL non-null values parsed cleanly (zero data loss)
            if cleaned[non_null_mask].notna().all():
                # Keep nullable Int64 if all values are whole integers
                non_na_vals = cleaned.dropna()
                if len(non_na_vals) > 0 and (non_na_vals % 1 == 0).all() and (non_na_vals.abs() < 1e15).all():
                    result[col] = cleaned.round().astype("Int64")
                else:
                    result[col] = cleaned.astype("float64")

        elif eff_type == COL_TYPE_DATE:
            if pd.api.types.is_datetime64_any_dtype(series):
                continue
            non_null_mask = series.notna()
            if not non_null_mask.any():
                continue
            parsed = _parse_dates_safe(series)
            if parsed[non_null_mask].notna().all():
                result[col] = parsed

        elif eff_type == COL_TYPE_TEXT:
            # Preserve exact text without turning NaN into "nan"
            if pd.api.types.is_numeric_dtype(series) or pd.api.types.is_datetime64_any_dtype(series):
                result[col] = series.map(
                    lambda v: np.nan
                    if _is_missing_value(v)
                    else (
                        v.strftime("%Y-%m-%d")
                        if isinstance(v, (pd.Timestamp, dt.datetime, dt.date))
                        else (
                            str(int(v))
                            if isinstance(v, (float, np.floating)) and float(v).is_integer()
                            else str(v)
                        )
                    )
                )

    return result


def analyze_dataset(
    df: pd.DataFrame,
    file_name: str,
    file_path: str,
    file_type: str,
    sheet_name: str | None = None,
    existing_overrides: dict[str, str] | None = None,
    import_notices: list[str] | None = None,
) -> DatasetSummary:
    """Analyze a DataFrame and build a complete DatasetSummary with column types and counts."""
    overrides = existing_overrides or {}
    col_infos: list[ColumnInfo] = []

    numeric_cols = 0
    text_cols = 0
    date_cols = 0
    empty_cols = 0

    for col in df.columns:
        series = df[col]
        detected, note = detect_column_type(str(col), series)
        override = overrides.get(str(col))
        if override not in VALID_COLUMN_TYPES:
            override = None

        missing_count = int(series.isna().sum())
        non_null = series.dropna()
        try:
            unique_count = int(non_null.nunique())
        except TypeError:
            unique_count = int(non_null.astype(str).nunique())

        samples = [str(v) for v in non_null.head(3).tolist()]
        info = ColumnInfo(
            name=str(col),
            detected_type=detected,
            override_type=override,
            missing_count=missing_count,
            unique_count=unique_count,
            sample_values=samples,
            detection_note=note,
        )
        col_infos.append(info)

        eff = info.effective_type
        if eff == COL_TYPE_NUMERIC:
            numeric_cols += 1
        elif eff == COL_TYPE_TEXT:
            text_cols += 1
        elif eff == COL_TYPE_DATE:
            date_cols += 1
        else:
            empty_cols += 1

    total_rows = int(len(df))
    total_cols = int(len(df.columns))
    missing_values = int(df.isna().sum().sum()) if total_rows > 0 and total_cols > 0 else 0

    try:
        duplicate_rows = int(df.duplicated().sum()) if total_rows > 0 else 0
    except TypeError:
        duplicate_rows = int(df.astype(str).duplicated().sum()) if total_rows > 0 else 0

    # Completely empty rows (all cells missing or blank strings) — vectorized for performance
    empty_rows = int(get_empty_row_mask(df).sum()) if (total_rows > 0 and total_cols > 0) else 0

    return DatasetSummary(
        file_name=file_name,
        file_path=file_path,
        file_type=file_type,
        sheet_name=sheet_name,
        total_rows=total_rows,
        total_columns=total_cols,
        numeric_columns=numeric_cols,
        text_columns=text_cols,
        date_columns=date_cols,
        empty_columns=empty_cols,
        missing_values=missing_values,
        duplicate_rows=duplicate_rows,
        empty_rows=empty_rows,
        column_infos=col_infos,
        import_notices=list(import_notices or []),
    )


def get_empty_row_mask(df: pd.DataFrame) -> pd.Series:
    """Return a boolean mask indicating completely empty (NaN or whitespace-only) rows."""
    if df.empty or len(df.columns) == 0:
        return pd.Series(dtype=bool, index=df.index)

    all_blank = pd.Series(True, index=df.index)
    for col in df.columns:
        series = df[col]
        col_blank = series.isna()
        if pd.api.types.is_string_dtype(series):
            col_blank = col_blank | series.str.strip().eq("").fillna(False)
        elif series.dtype == object:
            non_na = ~col_blank
            if non_na.any():
                # Fast check on string cells in object columns
                str_empty = series[non_na].map(lambda v: isinstance(v, str) and v.strip() == "")
                col_blank = col_blank.copy()
                col_blank.loc[non_na] = str_empty
        all_blank &= col_blank
        if not all_blank.any():
            break
    return all_blank


def get_empty_columns(df: pd.DataFrame) -> list[str]:
    """Return names of columns where every cell is missing or whitespace-only."""
    empty_cols: list[str] = []
    for col in df.columns:
        series = df[col]
        col_blank = series.isna()
        if pd.api.types.is_string_dtype(series):
            col_blank = col_blank | series.str.strip().eq("").fillna(False)
        elif series.dtype == object:
            non_na = ~col_blank
            if non_na.any():
                str_empty = series[non_na].map(lambda v: isinstance(v, str) and v.strip() == "")
                col_blank = col_blank.copy()
                col_blank.loc[non_na] = str_empty
        if col_blank.all():
            empty_cols.append(str(col))
    return empty_cols


def get_column_type_map(summary: DatasetSummary | None) -> dict[str, str]:
    """Return a dict mapping each column name to its effective logical type."""
    if summary is None:
        return {}
    return {info.name: info.effective_type for info in summary.column_infos}

"""Safe local CSV and Excel (.xlsx, .xls) file importing for MiniSort.

Preserves original source files (read-only access), preserves leading zeros
in text identifiers, auto-detects CSV encoding and delimiter, lists Excel
worksheets, and normalizes missing or duplicate column headings cleanly.
"""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import openpyxl
from openpyxl.utils.exceptions import InvalidFileException
import pandas as pd

from core.models import LoadedDataset
from utils.logger import get_logger
from utils.validators import MiniSortError, validate_import_file

logger = get_logger("file_handler")

CANDIDATE_DELIMITERS = [",", ";", "\t", "|"]


def get_excel_sheet_names(file_path: str | Path) -> list[str]:
    """Return all worksheet names in an .xlsx or .xls file without loading full data."""
    path = validate_import_file(file_path)
    ext = path.suffix.lower()

    if ext == ".xlsx":
        wb = None
        try:
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            sheets = list(wb.sheetnames)
            if not sheets:
                raise MiniSortError(f"The Excel file '{path.name}' does not contain any worksheets.")
            return sheets
        except MiniSortError:
            raise
        except PermissionError as exc:
            raise MiniSortError(
                f"Cannot open '{path.name}' because it is locked or open in another program. "
                "Please close it in Excel and try again.",
                str(exc),
            ) from exc
        except (zipfile.BadZipFile, InvalidFileException, KeyError, ValueError, EOFError) as exc:
            logger.warning("Corrupted or invalid .xlsx file (%s)", type(exc).__name__)
            raise MiniSortError(
                f"The file '{path.name}' appears to be corrupted or is not a valid Excel (.xlsx) file.",
                str(exc),
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected error inspecting .xlsx sheets")
            raise MiniSortError(
                f"MiniSort could not read the worksheets in '{path.name}'. "
                "Please verify the file is a valid, unencrypted Excel spreadsheet.",
                str(exc),
            ) from exc
        finally:
            if wb is not None:
                try:
                    wb.close()
                except Exception:
                    pass

    if ext == ".xls":
        try:
            import xlrd

            wb = xlrd.open_workbook(str(path), on_demand=True)
            try:
                sheets = list(wb.sheet_names())
            finally:
                wb.release_resources()
            if not sheets:
                raise MiniSortError(f"The Excel file '{path.name}' does not contain any worksheets.")
            return sheets
        except MiniSortError:
            raise
        except PermissionError as exc:
            raise MiniSortError(
                f"Cannot open '{path.name}' because it is locked or open in another program.",
                str(exc),
            ) from exc
        except Exception as exc:
            logger.warning("Failed to inspect .xls file (%s)", type(exc).__name__)
            raise MiniSortError(
                f"MiniSort could not open '{path.name}'. Make sure it is a valid Excel 97–2003 (.xls) file "
                "and is not password-protected or corrupted.",
                str(exc),
            ) from exc

    return []


def detect_csv_encoding(file_path: Path) -> str:
    """Detect encoding for a CSV file, handling UTF-8, UTF-8 BOM, UTF-16, and Windows fallbacks."""
    try:
        with open(file_path, "rb") as fh:
            sample = fh.read(65536)
    except PermissionError as exc:
        raise MiniSortError(
            f"Cannot open '{file_path.name}' because it is locked or open in another program.",
            str(exc),
        ) from exc

    if not sample:
        raise MiniSortError(f"The file '{file_path.name}' is completely empty.")

    if sample.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if sample.startswith((b"\xff\xfe", b"\xfe\xff")):
        return "utf-16"

    # Check if file looks like UTF-16 without BOM (lots of null bytes)
    if b"\x00" in sample[:2048]:
        for enc in ("utf-16", "utf-16-le", "utf-16-be"):
            try:
                sample.decode(enc)
                return enc
            except UnicodeDecodeError:
                continue

    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            sample.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue

    return "latin-1"


def detect_csv_delimiter(sample_text: str) -> str:
    """Detect the most likely CSV delimiter using Python's csv.Sniffer with a safe fallback."""
    lines = [line for line in sample_text.splitlines() if line.strip()][:20]
    if not lines:
        return ","

    snippet = "\n".join(lines)
    try:
        dialect = csv.Sniffer().sniff(snippet, delimiters="".join(CANDIDATE_DELIMITERS))
        if dialect.delimiter in CANDIDATE_DELIMITERS:
            return dialect.delimiter
    except csv.Error:
        pass

    # Consistency fallback: pick delimiter that yields the most consistent >1 column split
    best_delim = ","
    best_score = -1.0
    for delim in CANDIDATE_DELIMITERS:
        counts = [len(next(csv.reader([line], delimiter=delim))) for line in lines[:10]]
        if max(counts) <= 1:
            continue
        avg = sum(counts) / len(counts)
        variance = sum((c - avg) ** 2 for c in counts) / len(counts)
        score = avg - variance
        if score > best_score:
            best_score = score
            best_delim = delim
    return best_delim


def normalize_column_headers(raw_headers: list[Any]) -> tuple[list[str], list[str]]:
    """Clean column headers: fill missing headings and disambiguate duplicates."""
    notices: list[str] = []
    cleaned: list[str] = []
    seen_counts: dict[str, int] = {}
    had_missing = False
    had_duplicates = False

    for idx, raw in enumerate(raw_headers):
        if raw is None or (isinstance(raw, float) and np.isnan(raw)):
            base = ""
        else:
            base = str(raw).strip()
        if not base:
            had_missing = True
            base = f"Column {idx + 1}"

        key = base.lower()
        if key in seen_counts:
            had_duplicates = True
            seen_counts[key] += 1
            candidate = f"{base} ({seen_counts[key]})"
            while candidate.lower() in seen_counts:
                seen_counts[key] += 1
                candidate = f"{base} ({seen_counts[key]})"
            seen_counts[candidate.lower()] = 1
            cleaned.append(candidate)
        else:
            seen_counts[key] = 1
            cleaned.append(base)

    if had_missing:
        notices.append("Some missing column headings were named automatically (e.g., Column 1).")
    if had_duplicates:
        notices.append("Duplicate column headings were renamed so every column stays unique.")

    return cleaned, notices


def _load_csv(path: Path) -> LoadedDataset:
    encoding = detect_csv_encoding(path)
    try:
        with open(path, "r", encoding=encoding, errors="replace", newline="") as fh:
            sample_text = fh.read(32768)
    except PermissionError as exc:
        raise MiniSortError(
            f"Cannot open '{path.name}' because it is locked or open in another program.",
            str(exc),
        ) from exc

    if not sample_text.strip():
        raise MiniSortError(f"The file '{path.name}' contains no readable data.")

    delimiter = detect_csv_delimiter(sample_text)
    notices: list[str] = []

    # Fast path: pandas read_csv preserving raw strings so leading zeros are never stripped
    raw_df: pd.DataFrame | None = None
    try:
        raw_df = pd.read_csv(
            path,
            sep=delimiter,
            header=None,
            dtype=str,
            keep_default_na=False,
            encoding=encoding,
            encoding_errors="replace",
            skip_blank_lines=False,
        )
    except Exception:
        # Fallback to Python's standard csv module to handle ragged rows cleanly
        rows: list[list[str]] = []
        max_len = 0
        try:
            with open(path, "r", encoding=encoding, errors="replace", newline="") as fh:
                reader = csv.reader(fh, delimiter=delimiter)
                for row in reader:
                    rows.append(row)
                    if len(row) > max_len:
                        max_len = len(row)
        except Exception as exc:
            logger.exception("CSV fallback reader failed")
            raise MiniSortError(
                f"MiniSort could not read '{path.name}'. Please check that it is a valid CSV file.",
                str(exc),
            ) from exc

        if not rows or max_len == 0:
            raise MiniSortError(f"The file '{path.name}' contains no readable rows.")
        padded = [r + [""] * (max_len - len(r)) for r in rows]
        raw_df = pd.DataFrame(padded, dtype=str)
        notices.append("Rows with uneven column counts were adjusted automatically during import.")

    if raw_df is None or raw_df.empty:
        raise MiniSortError(f"The file '{path.name}' contains no data.")

    # Drop leading completely blank lines before header if any
    first_non_empty = None
    for r_idx in range(len(raw_df)):
        row_vals = raw_df.iloc[r_idx].tolist()
        if any(str(v).strip() != "" for v in row_vals):
            first_non_empty = r_idx
            break

    if first_non_empty is None:
        raise MiniSortError(f"The file '{path.name}' only contains blank lines.")

    raw_headers = raw_df.iloc[first_non_empty].tolist()
    headers, header_notices = normalize_column_headers(raw_headers)
    notices.extend(header_notices)

    data_df = raw_df.iloc[first_non_empty + 1 :].copy()
    data_df.columns = headers
    data_df = data_df.reset_index(drop=True)

    # Convert strictly empty strings "" to NaN so missing cells are properly recognized
    data_df = data_df.replace("", np.nan)

    if delimiter != ",":
        delim_names = {";": "semicolon", "\t": "tab", "|": "pipe"}
        notices.append(f"Detected {delim_names.get(delimiter, delimiter)}-separated values.")

    return LoadedDataset(
        df=data_df,
        file_path=str(path.resolve()),
        file_name=path.name,
        file_type="CSV",
        sheet_name=None,
        available_sheets=[],
        encoding=encoding,
        delimiter=delimiter,
        notices=notices,
    )


def _load_xlsx(path: Path, sheet_name: str | None = None) -> LoadedDataset:
    sheets = get_excel_sheet_names(path)
    chosen_sheet = sheet_name if (sheet_name and sheet_name in sheets) else sheets[0]

    wb = None
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb[chosen_sheet]
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
    except PermissionError as exc:
        raise MiniSortError(
            f"Cannot open '{path.name}' because it is locked or open in another program. "
            "Please close it in Excel and try again.",
            str(exc),
        ) from exc
    except (zipfile.BadZipFile, InvalidFileException, KeyError, EOFError) as exc:
        raise MiniSortError(
            f"The file '{path.name}' appears to be corrupted or is not a valid Excel (.xlsx) file.",
            str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Error reading .xlsx worksheet")
        raise MiniSortError(
            f"MiniSort could not read worksheet '{chosen_sheet}' in '{path.name}'.",
            str(exc),
        ) from exc
    finally:
        if wb is not None:
            try:
                wb.close()
            except Exception:
                pass

    if not rows:
        raise MiniSortError(f"The worksheet '{chosen_sheet}' in '{path.name}' is completely empty.")

    # Find first non-empty row to treat as header
    first_non_empty = None
    for idx, row in enumerate(rows):
        if any(cell is not None and str(cell).strip() != "" for cell in row):
            first_non_empty = idx
            break

    if first_non_empty is None:
        raise MiniSortError(f"The worksheet '{chosen_sheet}' in '{path.name}' has no data.")

    max_cols = max(len(r) for r in rows[first_non_empty:])
    if max_cols == 0:
        raise MiniSortError(f"The worksheet '{chosen_sheet}' in '{path.name}' has no columns.")

    raw_headers = list(rows[first_non_empty]) + [None] * (max_cols - len(rows[first_non_empty]))
    headers, notices = normalize_column_headers(raw_headers)

    body_rows = [
        list(r) + [None] * (max_cols - len(r))
        for r in rows[first_non_empty + 1 :]
    ]

    data_df = pd.DataFrame(body_rows, columns=headers, dtype=object)
    # Normalize empty strings to NaN while preserving native numbers/dates/leading-zero strings
    data_df = data_df.replace("", np.nan)
    data_df = data_df.reset_index(drop=True)

    return LoadedDataset(
        df=data_df,
        file_path=str(path.resolve()),
        file_name=path.name,
        file_type="XLSX",
        sheet_name=chosen_sheet,
        available_sheets=sheets,
        notices=notices,
    )


def _load_xls(path: Path, sheet_name: str | None = None) -> LoadedDataset:
    sheets = get_excel_sheet_names(path)
    chosen_sheet = sheet_name if (sheet_name and sheet_name in sheets) else sheets[0]

    try:
        raw_df = pd.read_excel(
            path,
            sheet_name=chosen_sheet,
            header=None,
            engine="xlrd",
            dtype=object,
        )
    except PermissionError as exc:
        raise MiniSortError(
            f"Cannot open '{path.name}' because it is locked or open in another program.",
            str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Error reading .xls worksheet")
        raise MiniSortError(
            f"MiniSort could not read '{path.name}'. Make sure it is a valid Excel 97–2003 (.xls) file.",
            str(exc),
        ) from exc

    if raw_df is None or raw_df.empty:
        raise MiniSortError(f"The worksheet '{chosen_sheet}' in '{path.name}' is completely empty.")

    first_non_empty = None
    for idx in range(len(raw_df)):
        vals = raw_df.iloc[idx].tolist()
        if any(pd.notna(v) and str(v).strip() != "" for v in vals):
            first_non_empty = idx
            break

    if first_non_empty is None:
        raise MiniSortError(f"The worksheet '{chosen_sheet}' in '{path.name}' has no data.")

    raw_headers = raw_df.iloc[first_non_empty].tolist()
    headers, notices = normalize_column_headers(raw_headers)

    data_df = raw_df.iloc[first_non_empty + 1 :].copy()
    data_df.columns = headers
    data_df = data_df.replace("", np.nan)
    data_df = data_df.reset_index(drop=True)

    return LoadedDataset(
        df=data_df,
        file_path=str(path.resolve()),
        file_name=path.name,
        file_type="XLS",
        sheet_name=chosen_sheet,
        available_sheets=sheets,
        notices=notices,
    )


def load_spreadsheet(file_path: str | Path, sheet_name: str | None = None) -> LoadedDataset:
    """Import a CSV, XLSX, or XLS spreadsheet safely without modifying the original file."""
    path = validate_import_file(file_path)
    ext = path.suffix.lower()

    logger.info("Importing %s file (%s)", ext, path.name)
    if ext == ".csv":
        return _load_csv(path)
    if ext == ".xlsx":
        return _load_xlsx(path, sheet_name=sheet_name)
    if ext == ".xls":
        return _load_xls(path, sheet_name=sheet_name)

    raise MiniSortError(f"Unsupported file format '{ext}'. Please choose a .csv, .xlsx, or .xls file.")

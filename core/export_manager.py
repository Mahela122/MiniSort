"""Excel (.xlsx) and CSV (.csv) export manager with monochrome styling and overwrite protection."""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd

from utils.logger import get_logger
from utils.validators import MiniSortError, sanitize_filename

logger = get_logger("export_manager")


def suggest_export_filename(
    source_file_name: str,
    operation_category: str = "processed",
    export_format: str = "xlsx",
) -> str:
    """Create a clear, descriptive default filename like Employee_Data_Sorted.xlsx."""
    stem = Path(source_file_name).stem if source_file_name else "Dataset"
    suffix_map = {
        "sort": "Sorted",
        "filter": "Filtered",
        "clean": "Cleaned",
        "import": "Export",
        "type": "Processed",
        "all": "All_Records",
    }
    tag = suffix_map.get(operation_category, "Processed")
    clean_stem = sanitize_filename(f"{stem}_{tag}")
    ext = "csv" if str(export_format).lower().lstrip(".") == "csv" else "xlsx"
    return f"{clean_stem}.{ext}"


def is_same_as_original(export_path: str | Path, original_path: str | Path | None) -> bool:
    """Return True if the chosen destination path points to the original imported file."""
    if not original_path:
        return False
    try:
        return Path(export_path).resolve() == Path(original_path).resolve()
    except OSError:
        return str(export_path).strip().lower() == str(original_path).strip().lower()


def _normalize_excel_cell(val: Any) -> Any:
    """Convert pandas/numpy scalars cleanly to native Python types for OpenPyXL."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(val, pd.Timestamp):
        if val.hour == 0 and val.minute == 0 and val.second == 0:
            return val.date()
        return val.to_pydatetime()
    if hasattr(val, "item") and callable(val.item):
        try:
            return val.item()
        except Exception:
            pass
    return val


def export_to_csv(df: pd.DataFrame, destination: str | Path) -> Path:
    """Export DataFrame to a UTF-8 CSV file (with UTF-8 BOM for clean Windows Excel opening)."""
    if df is None:
        raise MiniSortError("There is no data to export.")
    dest = Path(destination)
    if dest.suffix.lower() != ".csv":
        dest = dest.with_suffix(".csv")

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        # Format datetime columns nicely as YYYY-MM-DD when time component is midnight
        out_df = df.copy()
        for col in out_df.columns:
            if pd.api.types.is_datetime64_any_dtype(out_df[col]):
                s = out_df[col]
                has_time = ((s.dt.hour != 0) | (s.dt.minute != 0) | (s.dt.second != 0)).any()
                fmt = "%Y-%m-%d %H:%M:%S" if has_time else "%Y-%m-%d"
                out_df[col] = s.dt.strftime(fmt)

        out_df.to_csv(dest, index=False, encoding="utf-8-sig")
        logger.info("Exported CSV (%d rows, %d cols)", len(df), len(df.columns))
        return dest
    except PermissionError as exc:
        raise MiniSortError(
            f"Cannot save '{dest.name}' because the file is open in another program or access was denied. "
            "Close the file or choose a different filename.",
            str(exc),
        ) from exc
    except OSError as exc:
        if getattr(exc, "errno", None) == 28:
            raise MiniSortError(
                "There is not enough free storage space to save this file. Please choose another folder or drive.",
                str(exc),
            ) from exc
        raise MiniSortError(
            f"Could not save '{dest.name}'. Please verify the destination folder exists and is writable.",
            str(exc),
        ) from exc


def export_to_excel(
    df: pd.DataFrame,
    destination: str | Path,
    sheet_name: str = "Data",
) -> Path:
    """Export DataFrame to a formatted .xlsx workbook with clean black-and-white header styling."""
    if df is None:
        raise MiniSortError("There is no data to export.")
    dest = Path(destination)
    if dest.suffix.lower() != ".xlsx":
        dest = dest.with_suffix(".xlsx")

    # Sanitize worksheet name to Excel's 31-character limit
    safe_sheet = "".join(ch for ch in (sheet_name or "Data") if ch not in r"[]:*?/\\")[:31].strip() or "Data"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = safe_sheet

    # Monochrome header styling (clean light grey fill, bold black text, crisp thin border)
    header_font = Font(name="Calibri", size=11, bold=True, color="111111")
    header_fill = PatternFill(start_color="F0F0F0", end_color="F0F0F0", fill_type="solid")
    header_align = Alignment(horizontal="left", vertical="center")
    thin_side = Side(style="thin", color="CCCCCC")
    header_border = Border(bottom=Side(style="medium", color="333333"), left=thin_side, right=thin_side, top=thin_side)

    body_font = Font(name="Calibri", size=11, color="111111")
    col_widths: list[int] = []

    headers = [str(c) for c in df.columns]
    ws.append(headers)
    for col_idx, header_text in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = header_border
        col_widths.append(min(max(len(header_text) + 4, 12), 45))

    ws.row_dimensions[1].height = 24
    ws.freeze_panes = "A2"

    # Write rows efficiently while computing sensible column widths from a sample
    sample_limit = 250
    for row_idx, row_tuple in enumerate(df.itertuples(index=False, name=None), start=2):
        excel_row = [_normalize_excel_cell(val) for val in row_tuple]
        ws.append(excel_row)
        if row_idx <= sample_limit + 1:
            for c_idx, val in enumerate(excel_row):
                if val is not None:
                    text_len = len(val.strftime("%Y-%m-%d")) if isinstance(val, (dt.date, dt.datetime)) else len(str(val))
                    col_widths[c_idx] = min(max(col_widths[c_idx], text_len + 3), 48)

    # Apply readable date format & font cleanly (avoid excessive per-cell styling overhead on huge files)
    style_row_limit = min(len(df) + 1, 15_000)
    for col_idx in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = col_widths[col_idx - 1]
        is_date_col = pd.api.types.is_datetime64_any_dtype(df.iloc[:, col_idx - 1])
        for row_idx in range(2, style_row_limit + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = body_font
            if is_date_col and isinstance(cell.value, (dt.date, dt.datetime)):
                cell.number_format = "yyyy-mm-dd"

    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        wb.save(dest)
        logger.info("Exported XLSX (%d rows, %d cols)", len(df), len(df.columns))
        return dest
    except PermissionError as exc:
        raise MiniSortError(
            f"Cannot save '{dest.name}' because the file is currently open in Excel or another program. "
            "Please close it or choose a different filename.",
            str(exc),
        ) from exc
    except OSError as exc:
        if getattr(exc, "errno", None) == 28:
            raise MiniSortError(
                "There is not enough free storage space to save this file. Please choose another folder or drive.",
                str(exc),
            ) from exc
        raise MiniSortError(
            f"Could not save '{dest.name}'. Please check folder permissions and try again.",
            str(exc),
        ) from exc
    finally:
        try:
            wb.close()
        except Exception:
            pass


def export_dataset(
    df: pd.DataFrame,
    destination: str | Path,
    export_format: str | None = None,
    sheet_name: str = "Data",
) -> Path:
    """Export DataFrame as Excel (.xlsx) or CSV (.csv) based on format or extension."""
    dest = Path(destination)
    fmt = (export_format or dest.suffix).lower().lstrip(".")
    if fmt == "csv":
        return export_to_csv(df, dest)
    if fmt in ("xlsx", "excel", ""):
        return export_to_excel(df, dest, sheet_name=sheet_name)
    raise MiniSortError(f"Unsupported export format '.{fmt}'. Please choose Excel (.xlsx) or CSV (.csv).")

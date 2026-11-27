"""Tests for Excel/CSV exporting, data roundtrip fidelity, overwrite guard, and large dataset performance."""

from __future__ import annotations

import hashlib
from pathlib import Path
import time

import numpy as np
import openpyxl
import pandas as pd

from core.data_detector import analyze_dataset, coerce_dataframe_types, get_column_type_map
from core.export_manager import (
    export_dataset,
    is_same_as_original,
    suggest_export_filename,
)
from core.file_handler import load_spreadsheet
from core.models import SortCondition
from core.sorting_engine import sort_dataframe


def test_export_xlsx_and_csv_match_processed_data(sample_employee_df: pd.DataFrame, tmp_path: Path) -> None:
    summary = analyze_dataset(sample_employee_df, "emp.xlsx", "emp.xlsx", "XLSX")
    tmap = get_column_type_map(summary)
    sorted_df = sort_dataframe(sample_employee_df, [SortCondition("Employee ID", True)], tmap)

    # Export Excel
    xlsx_out = export_dataset(sorted_df, tmp_path / "Employee_Data_Sorted.xlsx", export_format="xlsx")
    assert xlsx_out.exists()

    # Check OpenPyXL header formatting & column widths
    wb = openpyxl.load_workbook(xlsx_out)
    ws = wb.active
    assert ws.cell(1, 1).font.bold is True
    assert ws.freeze_panes == "A2"
    wb.close()

    # Re-import Excel and verify rows & leading zeros match exactly
    re_xlsx = load_spreadsheet(xlsx_out)
    assert re_xlsx.df["Employee ID"].tolist() == [1, 2, 3, 4, 5, 10]
    assert re_xlsx.df["Postal Code"].tolist() == ["10001", "02108", "60601", "02109", "94107", "01001"]

    # Export CSV
    csv_out = export_dataset(sorted_df, tmp_path / "Employee_Data_Sorted.csv", export_format="csv")
    assert csv_out.exists()
    re_csv = load_spreadsheet(csv_out)
    assert re_csv.df["Employee Name"].tolist() == ["Zara", "Peter", "bob", "Maria", "John", "alex"]
    assert re_csv.df["Postal Code"].tolist() == ["10001", "02108", "60601", "02109", "94107", "01001"]


def test_original_file_protection_and_filename_suggestions(multi_sheet_xlsx: Path) -> None:
    assert is_same_as_original(multi_sheet_xlsx, multi_sheet_xlsx) is True
    assert is_same_as_original(multi_sheet_xlsx.with_name("other.xlsx"), multi_sheet_xlsx) is False

    assert suggest_export_filename("Employee_Data.xlsx", "sort", "xlsx") == "Employee_Data_Sorted.xlsx"
    assert suggest_export_filename("Student_Data.csv", "clean", "csv") == "Student_Data_Cleaned.csv"
    assert suggest_export_filename("Sales.xlsx", "filter", "xlsx") == "Sales_Filtered.xlsx"

    # Full pipeline never touches source file bytes
    before_hash = hashlib.sha256(multi_sheet_xlsx.read_bytes()).hexdigest()
    loaded = load_spreadsheet(multi_sheet_xlsx, sheet_name="Employees")
    summary = analyze_dataset(loaded.df, loaded.file_name, loaded.file_path, loaded.file_type)
    typed_df = coerce_dataframe_types(loaded.df, summary.column_infos)
    sorted_df = sort_dataframe(typed_df, [SortCondition("Employee ID", True)], get_column_type_map(summary))
    export_dataset(sorted_df, multi_sheet_xlsx.with_name("Employee_Data_Sorted.xlsx"))
    assert hashlib.sha256(multi_sheet_xlsx.read_bytes()).hexdigest() == before_hash


def test_large_dataset_performance(tmp_path: Path) -> None:
    """Verify 50,000-row CSV imports, detects, sorts, and exports smoothly within seconds."""
    n = 50_000
    rng = np.random.default_rng(42)
    df = pd.DataFrame(
        {
            "Record ID": rng.permutation(np.arange(1, n + 1)),
            "Category": rng.choice(["Alpha", "Beta", "Gamma", "Delta"], size=n),
            "Amount": rng.uniform(10.0, 50000.0, size=n).round(2),
            "Postal Code": ["02108" if i % 2 == 0 else "90210" for i in range(n)],
        }
    )
    csv_in = tmp_path / "large_50k.csv"
    df.to_csv(csv_in, index=False)

    t0 = time.perf_counter()
    loaded = load_spreadsheet(csv_in)
    summary = analyze_dataset(loaded.df, loaded.file_name, loaded.file_path, loaded.file_type)
    typed = coerce_dataframe_types(loaded.df, summary.column_infos)
    sorted_df = sort_dataframe(
        typed,
        conditions=[SortCondition("Record ID", True)],
        column_types=get_column_type_map(summary),
    )
    csv_out = export_dataset(sorted_df, tmp_path / "large_50k_sorted.csv", export_format="csv")
    elapsed = time.perf_counter() - t0

    assert len(sorted_df) == n
    assert int(sorted_df["Record ID"].iloc[0]) == 1
    assert int(sorted_df["Record ID"].iloc[-1]) == n
    assert sorted_df["Postal Code"].iloc[0] in ("02108", "90210")
    assert csv_out.exists()
    assert elapsed < 15.0, f"50k pipeline took too long: {elapsed:.2f}s"

"""Tests for CSV/Excel file importing, worksheet selection, auto detection, and invalid file handling."""

from __future__ import annotations

import hashlib
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

from core.data_detector import analyze_dataset, coerce_dataframe_types, get_column_type_map
from core.file_handler import get_excel_sheet_names, load_spreadsheet
from utils.constants import COL_TYPE_DATE, COL_TYPE_EMPTY, COL_TYPE_NUMERIC, COL_TYPE_TEXT
from utils.validators import MiniSortError


def test_csv_utf8_bom_and_leading_zeros(tmp_path: Path) -> None:
    csv_path = tmp_path / "contacts.csv"
    csv_path.write_text(
        "Employee ID,Name,Postal Code,Phone,Salary,Joining Date,Unused\n"
        "001,Alice,02108,0771234567,50000,2023-01-15,\n"
        "002,\"Bob, Jr.\",01001,0771234568,70000,2022-12-01,\n",
        encoding="utf-8-sig",
    )

    loaded = load_spreadsheet(csv_path)
    assert loaded.file_type == "CSV"
    assert len(loaded.df) == 2
    assert loaded.df.loc[1, "Name"] == "Bob, Jr."
    # Leading zeros preserved before and after detection/coercion!
    summary = analyze_dataset(
        loaded.df, loaded.file_name, loaded.file_path, loaded.file_type
    )
    tmap = get_column_type_map(summary)
    assert tmap["Employee ID"] == COL_TYPE_TEXT  # Leading zero '001' protected!
    assert tmap["Postal Code"] == COL_TYPE_TEXT
    assert tmap["Phone"] == COL_TYPE_TEXT
    assert tmap["Salary"] == COL_TYPE_NUMERIC
    assert tmap["Joining Date"] == COL_TYPE_DATE
    assert tmap["Unused"] == COL_TYPE_EMPTY

    coerced = coerce_dataframe_types(loaded.df, summary.column_infos)
    assert coerced.loc[0, "Employee ID"] == "001"
    assert coerced.loc[0, "Postal Code"] == "02108"
    assert coerced.loc[0, "Phone"] == "0771234567"
    assert int(coerced.loc[0, "Salary"]) == 50000


def test_csv_semicolon_delimiter_and_cp1252_encoding(tmp_path: Path) -> None:
    csv_path = tmp_path / "euro.csv"
    content = "Name;City;Amount\nCafé Owner;München;1200\nJosé;São Paulo;3500\n"
    csv_path.write_bytes(content.encode("cp1252"))

    loaded = load_spreadsheet(csv_path)
    assert loaded.delimiter == ";"
    assert list(loaded.df.columns) == ["Name", "City", "Amount"]
    assert loaded.df.loc[0, "Name"] == "Café Owner"
    assert loaded.df.loc[1, "City"] == "São Paulo"


def test_csv_missing_and_duplicate_headers(tmp_path: Path) -> None:
    csv_path = tmp_path / "headers.csv"
    csv_path.write_text("Name,,Name\nAlice,10,Sales\nBob,20,HR\n", encoding="utf-8")

    loaded = load_spreadsheet(csv_path)
    assert list(loaded.df.columns) == ["Name", "Column 2", "Name (2)"]
    assert len(loaded.notices) >= 2


def test_excel_multisheet_listing_and_selection(multi_sheet_xlsx: Path) -> None:
    original_hash = hashlib.sha256(multi_sheet_xlsx.read_bytes()).hexdigest()

    sheets = get_excel_sheet_names(multi_sheet_xlsx)
    assert sheets == ["Employees", "Departments"]

    loaded_emp = load_spreadsheet(multi_sheet_xlsx, sheet_name="Employees")
    assert loaded_emp.sheet_name == "Employees"
    assert len(loaded_emp.df) == 3
    assert loaded_emp.df.loc[0, "Postal Code"] == "02108"

    loaded_dept = load_spreadsheet(multi_sheet_xlsx, sheet_name="Departments")
    assert loaded_dept.sheet_name == "Departments"
    assert list(loaded_dept.df.columns) == ["Department", "Budget"]
    assert len(loaded_dept.df) == 2

    # Original Excel file untouched
    assert hashlib.sha256(multi_sheet_xlsx.read_bytes()).hexdigest() == original_hash


def test_manual_column_type_override(tmp_path: Path) -> None:
    csv_path = tmp_path / "ids.csv"
    csv_path.write_text("Employee ID,Score\n101,85\n102,90\n", encoding="utf-8")
    loaded = load_spreadsheet(csv_path)

    s1 = analyze_dataset(loaded.df, loaded.file_name, loaded.file_path, loaded.file_type)
    assert get_column_type_map(s1)["Employee ID"] == COL_TYPE_NUMERIC

    # Override Employee ID to Text
    s2 = analyze_dataset(
        loaded.df,
        loaded.file_name,
        loaded.file_path,
        loaded.file_type,
        existing_overrides={"Employee ID": COL_TYPE_TEXT},
    )
    assert get_column_type_map(s2)["Employee ID"] == COL_TYPE_TEXT


def test_invalid_and_corrupted_files_raise_friendly_errors(tmp_path: Path) -> None:
    # Missing file
    with pytest.raises(MiniSortError, match="could not be found"):
        load_spreadsheet(tmp_path / "does_not_exist.csv")

    # Unsupported extension
    bad_ext = tmp_path / "notes.txt"
    bad_ext.write_text("hello", encoding="utf-8")
    with pytest.raises(MiniSortError, match="Unsupported file format"):
        load_spreadsheet(bad_ext)

    # 0-byte empty file
    empty_file = tmp_path / "empty.csv"
    empty_file.write_bytes(b"")
    with pytest.raises(MiniSortError, match="completely empty"):
        load_spreadsheet(empty_file)

    # Corrupted .xlsx file
    corrupt_xlsx = tmp_path / "corrupt.xlsx"
    corrupt_xlsx.write_bytes(b"NOT A REAL ZIP OR EXCEL FILE")
    with pytest.raises(MiniSortError, match="corrupted"):
        load_spreadsheet(corrupt_xlsx)

    # Corrupted .xls file
    corrupt_xls = tmp_path / "corrupt.xls"
    corrupt_xls.write_bytes(b"GARBAGE BYTES FOR XLS")
    with pytest.raises(MiniSortError):
        load_spreadsheet(corrupt_xls)

    # Empty worksheet inside valid .xlsx
    blank_xlsx = tmp_path / "blank.xlsx"
    wb = openpyxl.Workbook()
    wb.save(blank_xlsx)
    wb.close()
    with pytest.raises(MiniSortError, match="empty|no data"):
        load_spreadsheet(blank_xlsx)

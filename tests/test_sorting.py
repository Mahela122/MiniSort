"""Tests for smart sorting, row integrity, multi-column sorting, missing values, and suggestions."""

from __future__ import annotations

import pandas as pd
import pytest

from core.data_detector import analyze_dataset, get_column_type_map
from core.models import SortCondition
from core.sorting_engine import sort_dataframe, suggest_sort_columns
from utils.validators import MiniSortError


def test_numeric_sorting_keeps_complete_rows_together(sample_employee_df: pd.DataFrame) -> None:
    summary = analyze_dataset(sample_employee_df, "emp.xlsx", "emp.xlsx", "XLSX")
    tmap = get_column_type_map(summary)

    # Employee ID has 2, 10, 5, 4, 1, 3 -> numeric sort must put 10 AFTER 5, not after 1!
    sorted_df = sort_dataframe(
        sample_employee_df,
        conditions=[SortCondition("Employee ID", ascending=True)],
        column_types=tmap,
    )
    assert sorted_df["Employee ID"].tolist() == [1, 2, 3, 4, 5, 10]
    # Verify complete rows stayed glued together
    assert sorted_df.loc[sorted_df["Employee ID"] == 10, "Employee Name"].iloc[0] == "alex"
    assert sorted_df.loc[sorted_df["Employee ID"] == 10, "Salary"].iloc[0] == 70000
    assert sorted_df.loc[sorted_df["Employee ID"] == 1, "Employee Name"].iloc[0] == "Zara"
    assert sorted_df.loc[sorted_df["Employee ID"] == 2, "Postal Code"].iloc[0] == "02108"


def test_salary_sorting_ascending_and_descending_with_missing_values(sample_employee_df: pd.DataFrame) -> None:
    summary = analyze_dataset(sample_employee_df, "emp.xlsx", "emp.xlsx", "XLSX")
    tmap = get_column_type_map(summary)

    # Ascending, missing at end (default)
    asc_df = sort_dataframe(
        sample_employee_df,
        conditions=[SortCondition("Salary", ascending=True)],
        column_types=tmap,
        na_position="last",
    )
    assert asc_df["Salary"].iloc[:5].tolist() == [30000.0, 45000.0, 50000.0, 60000.0, 70000.0]
    assert pd.isna(asc_df["Salary"].iloc[5])
    assert asc_df["Employee Name"].iloc[5] == "Maria"

    # Descending, missing STILL at end
    desc_df = sort_dataframe(
        sample_employee_df,
        conditions=[SortCondition("Salary", ascending=False)],
        column_types=tmap,
        na_position="last",
    )
    assert desc_df["Salary"].iloc[:5].tolist() == [70000.0, 60000.0, 50000.0, 45000.0, 30000.0]
    assert pd.isna(desc_df["Salary"].iloc[5])

    # Missing at beginning
    na_first_df = sort_dataframe(
        sample_employee_df,
        conditions=[SortCondition("Salary", ascending=True)],
        column_types=tmap,
        na_position="first",
    )
    assert pd.isna(na_first_df["Salary"].iloc[0])
    assert na_first_df["Salary"].iloc[1:].tolist() == [30000.0, 45000.0, 50000.0, 60000.0, 70000.0]


def test_alphabetical_case_insensitive_sorting(sample_employee_df: pd.DataFrame) -> None:
    summary = analyze_dataset(sample_employee_df, "emp.xlsx", "emp.xlsx", "XLSX")
    tmap = get_column_type_map(summary)

    sorted_df = sort_dataframe(
        sample_employee_df,
        conditions=[SortCondition("Employee Name", ascending=True)],
        column_types=tmap,
        case_insensitive=True,
    )
    assert sorted_df["Employee Name"].tolist() == ["alex", "bob", "John", "Maria", "Peter", "Zara"]


def test_date_chronological_sorting() -> None:
    df = pd.DataFrame(
        {
            "Event": ["B", "A", "D", "C"],
            "Date": ["Feb 1, 2024", "Jan 15, 2024", "Dec 31, 2023", None],
        }
    )
    summary = analyze_dataset(df, "events.csv", "events.csv", "CSV")
    tmap = get_column_type_map(summary)

    sorted_df = sort_dataframe(
        df,
        conditions=[SortCondition("Date", ascending=True)],
        column_types=tmap,
        na_position="last",
    )
    # Chronological: Dec 2023 -> Jan 2024 -> Feb 2024 -> None (NOT alphabetical!)
    assert sorted_df["Event"].tolist() == ["D", "A", "B", "C"]


def test_multi_column_sorting(sample_employee_df: pd.DataFrame) -> None:
    summary = analyze_dataset(sample_employee_df, "emp.xlsx", "emp.xlsx", "XLSX")
    tmap = get_column_type_map(summary)

    # Primary: Department Asc, Secondary: Employee ID Asc
    sorted_df = sort_dataframe(
        sample_employee_df,
        conditions=[
            SortCondition("Department", ascending=True),
            SortCondition("Employee ID", ascending=True),
        ],
        column_types=tmap,
    )
    pairs = list(zip(sorted_df["Department"].tolist(), sorted_df["Employee ID"].tolist()))
    assert pairs == [
        ("Engineering", 3),
        ("Engineering", 5),
        ("Engineering", 10),
        ("HR", 1),
        ("Sales", 2),
        ("Sales", 4),
    ]


def test_duplicate_sort_column_rejected(sample_employee_df: pd.DataFrame) -> None:
    with pytest.raises(MiniSortError, match="listed more than once"):
        sort_dataframe(
            sample_employee_df,
            conditions=[SortCondition("Salary", True), SortCondition("Salary", False)],
        )


def test_missing_sort_column_friendly_error(sample_employee_df: pd.DataFrame) -> None:
    with pytest.raises(MiniSortError, match="couldn't find the selected column"):
        sort_dataframe(sample_employee_df, conditions=[SortCondition("NonExistent", True)])


def test_smart_sort_suggestions_local_heuristics(sample_employee_df: pd.DataFrame) -> None:
    summary = analyze_dataset(sample_employee_df, "emp.xlsx", "emp.xlsx", "XLSX")
    suggestions = suggest_sort_columns(summary.column_infos, max_suggestions=4)
    suggested_names = [col for col, _reason in suggestions]
    assert "Employee ID" in suggested_names
    assert "Employee Name" in suggested_names
    assert "Salary" in suggested_names

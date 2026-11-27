"""Tests for text, numeric, date, and multi-condition filtering."""

from __future__ import annotations

import pandas as pd
import pytest

from core.data_detector import analyze_dataset, get_column_type_map
from core.filter_engine import filter_dataframe
from core.models import FilterCondition
from utils.validators import MiniSortError


def test_text_filters(sample_employee_df: pd.DataFrame) -> None:
    tmap = get_column_type_map(analyze_dataset(sample_employee_df, "e.xlsx", "e.xlsx", "XLSX"))

    res_contains = filter_dataframe(
        sample_employee_df,
        [FilterCondition("Department", "Contains", "eng")],
        tmap,
    )
    assert len(res_contains) == 3

    res_not = filter_dataframe(
        sample_employee_df,
        [FilterCondition("Department", "Does not contain", "eng")],
        tmap,
    )
    assert len(res_not) == 3

    res_eq = filter_dataframe(
        sample_employee_df,
        [FilterCondition("Department", "Equals", "sales")],
        tmap,
    )
    assert len(res_eq) == 2

    res_starts = filter_dataframe(
        sample_employee_df,
        [FilterCondition("Employee Name", "Starts with", "m")],
        tmap,
    )
    assert res_starts["Employee Name"].tolist() == ["Maria"]

    res_ends = filter_dataframe(
        sample_employee_df,
        [FilterCondition("Employee Name", "Ends with", "ra")],
        tmap,
    )
    assert res_ends["Employee Name"].tolist() == ["Zara"]


def test_numeric_filters(sample_employee_df: pd.DataFrame) -> None:
    tmap = get_column_type_map(analyze_dataset(sample_employee_df, "e.xlsx", "e.xlsx", "XLSX"))

    gt = filter_dataframe(
        sample_employee_df,
        [FilterCondition("Salary", "Greater than", "50000")],
        tmap,
    )
    assert sorted(gt["Salary"].tolist()) == [60000.0, 70000.0]

    lt = filter_dataframe(
        sample_employee_df,
        [FilterCondition("Salary", "Less than", "50000")],
        tmap,
    )
    assert sorted(lt["Salary"].tolist()) == [30000.0, 45000.0]

    eq = filter_dataframe(
        sample_employee_df,
        [FilterCondition("Salary", "Equal to", "50,000")],
        tmap,
    )
    assert eq["Employee Name"].tolist() == ["Peter"]

    btw = filter_dataframe(
        sample_employee_df,
        [FilterCondition("Salary", "Between", "45000", "60000")],
        tmap,
    )
    assert sorted(btw["Salary"].tolist()) == [45000.0, 50000.0, 60000.0]


def test_date_filters(sample_employee_df: pd.DataFrame) -> None:
    tmap = get_column_type_map(analyze_dataset(sample_employee_df, "e.xlsx", "e.xlsx", "XLSX"))

    after = filter_dataframe(
        sample_employee_df,
        [FilterCondition("Joining Date", "After", "2023-01-01")],
        tmap,
    )
    assert sorted(after["Employee Name"].tolist()) == ["John", "Peter"]

    before = filter_dataframe(
        sample_employee_df,
        [FilterCondition("Joining Date", "Before", "2022-01-01")],
        tmap,
    )
    assert sorted(before["Employee Name"].tolist()) == ["Maria", "alex"]

    between = filter_dataframe(
        sample_employee_df,
        [FilterCondition("Joining Date", "Between", "2022-01-01", "2023-12-31")],
        tmap,
    )
    assert sorted(between["Employee Name"].tolist()) == ["Peter", "bob"]


def test_multi_filter_and_original_preserved(sample_employee_df: pd.DataFrame) -> None:
    tmap = get_column_type_map(analyze_dataset(sample_employee_df, "e.xlsx", "e.xlsx", "XLSX"))
    original_len = len(sample_employee_df)

    # Engineering AND Salary > 40000
    res = filter_dataframe(
        sample_employee_df,
        [
            FilterCondition("Department", "Equals", "Engineering"),
            FilterCondition("Salary", "Greater than", "40000"),
        ],
        tmap,
        match_all=True,
    )
    assert sorted(res["Employee Name"].tolist()) == ["alex", "bob"]
    assert len(sample_employee_df) == original_len


def test_invalid_filter_inputs_raise_friendly_errors(sample_employee_df: pd.DataFrame) -> None:
    tmap = get_column_type_map(analyze_dataset(sample_employee_df, "e.xlsx", "e.xlsx", "XLSX"))

    with pytest.raises(MiniSortError, match="not a valid number"):
        filter_dataframe(sample_employee_df, [FilterCondition("Salary", "Greater than", "abc")], tmap)

    with pytest.raises(MiniSortError, match="not a valid date"):
        filter_dataframe(sample_employee_df, [FilterCondition("Joining Date", "After", "not-a-date")], tmap)

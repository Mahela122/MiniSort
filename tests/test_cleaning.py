"""Tests for all 6 data cleaning operations: duplicates, empty rows/cols, missing values, spaces, case."""

from __future__ import annotations

import numpy as np
import pandas as pd

from core.cleaning_engine import (
    count_duplicates,
    format_text_case,
    remove_duplicates,
    remove_empty_columns,
    remove_empty_rows,
    remove_extra_spaces,
    replace_missing_values,
)


def test_remove_duplicates_all_and_subset() -> None:
    df = pd.DataFrame(
        {
            "ID": [1, 2, 1, 3, 2],
            "Name": ["Alice", "Bob", "Alice", "Cara", "Robert"],
        }
    )
    assert count_duplicates(df) == 1
    cleaned_all, removed_all = remove_duplicates(df)
    assert removed_all == 1
    assert len(cleaned_all) == 4

    # Duplicate check on subset ["ID"] removes both duplicate ID=1 and ID=2
    assert count_duplicates(df, subset=["ID"]) == 2
    cleaned_sub, removed_sub = remove_duplicates(df, subset=["ID"])
    assert removed_sub == 2
    assert cleaned_sub["ID"].tolist() == [1, 2, 3]
    assert cleaned_sub["Name"].tolist() == ["Alice", "Bob", "Cara"]


def test_remove_empty_rows_and_empty_columns() -> None:
    df = pd.DataFrame(
        {
            "Name": ["Alice", None, "   ", "Bob"],
            "Age": [30, np.nan, np.nan, 25],
            "EmptyCol": [np.nan, np.nan, np.nan, np.nan],
        }
    )
    no_empty_rows, removed_rows = remove_empty_rows(df)
    assert removed_rows == 2
    assert no_empty_rows["Name"].tolist() == ["Alice", "Bob"]

    no_empty_cols, removed_cols = remove_empty_columns(no_empty_rows)
    assert removed_cols == ["EmptyCol"]
    assert list(no_empty_cols.columns) == ["Name", "Age"]


def test_replace_missing_values_modes() -> None:
    df = pd.DataFrame(
        {
            "Name": ["Alice", None, "Cara"],
            "Score": [10.0, np.nan, 30.0],
        }
    )

    c1, n1 = replace_missing_values(df, ["Name"], mode="custom_text", custom_value="Unknown")
    assert n1 == 1
    assert c1["Name"].tolist() == ["Alice", "Unknown", "Cara"]

    c2, n2 = replace_missing_values(df, ["Name"], mode="empty_text")
    assert n2 == 1
    assert c2["Name"].tolist() == ["Alice", "", "Cara"]

    c3, n3 = replace_missing_values(df, ["Score"], mode="numeric_value", custom_value="0")
    assert n3 == 1
    assert c3["Score"].tolist() == [10.0, 0.0, 30.0]

    c4, n4 = replace_missing_values(df, ["Score"], mode="column_mean")
    assert n4 == 1
    assert c4["Score"].tolist() == [10.0, 20.0, 30.0]


def test_remove_extra_spaces_and_text_formatting() -> None:
    df = pd.DataFrame(
        {
            "Name": ["  alice   smith ", "BOB  JONES", None],
            "City": [" new   york ", "boston", "  chicago  "],
            "Salary": [50000, 60000, 70000],
        }
    )

    trimmed, count = remove_extra_spaces(df, normalize_internal=True)
    assert count == 4
    assert trimmed["Name"].iloc[0] == "alice smith"
    assert trimmed["Name"].iloc[1] == "BOB JONES"
    assert pd.isna(trimmed["Name"].iloc[2])
    assert trimmed["City"].iloc[0] == "new york"

    upper_df, u_cnt = format_text_case(trimmed, ["City"], "upper")
    assert u_cnt == 3
    assert upper_df["City"].tolist() == ["NEW YORK", "BOSTON", "CHICAGO"]

    title_df, _ = format_text_case(trimmed, ["Name"], "title")
    assert title_df["Name"].iloc[0] == "Alice Smith"
    assert title_df["Name"].iloc[1] == "Bob Jones"
    assert pd.isna(title_df["Name"].iloc[2])

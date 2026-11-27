"""Tests for column statistics engine and memory-capped Undo/Redo history manager."""

from __future__ import annotations

import pandas as pd

from core.history_manager import HistoryManager
from core.statistics_engine import compute_column_statistics
from utils.constants import COL_TYPE_DATE, COL_TYPE_NUMERIC, COL_TYPE_TEXT


def test_numeric_text_and_date_statistics(sample_employee_df: pd.DataFrame) -> None:
    num_stats = compute_column_statistics(sample_employee_df, "Salary", COL_TYPE_NUMERIC)
    assert num_stats.extra["count"] == 5
    assert num_stats.extra["sum"] == 255000.0
    assert num_stats.extra["average"] == 51000.0
    assert num_stats.extra["min"] == 30000.0
    assert num_stats.extra["max"] == 70000.0
    assert num_stats.extra["median"] == 50000.0
    assert num_stats.missing_count == 1

    txt_stats = compute_column_statistics(sample_employee_df, "Department", COL_TYPE_TEXT)
    assert txt_stats.extra["total_values"] == 6
    assert txt_stats.extra["unique_values"] == 3
    assert txt_stats.extra["most_frequent"] == "Engineering"
    assert txt_stats.top_values[0][0] == "Engineering"
    assert txt_stats.top_values[0][1] == 3

    dt_stats = compute_column_statistics(sample_employee_df, "Joining Date", COL_TYPE_DATE)
    assert dt_stats.extra["earliest"] == "2020-02-28"
    assert dt_stats.extra["latest"] == "2024-01-15"
    assert dt_stats.missing_count == 1


def test_undo_redo_restore_and_limits() -> None:
    hm = HistoryManager(max_steps=3, max_memory_mb=10)
    df0 = pd.DataFrame({"A": [3, 1, 2]})
    hm.reset_with_original(df0, description="Imported")
    assert not hm.can_undo
    assert not hm.can_redo

    df1 = pd.DataFrame({"A": [1, 2, 3]})
    hm.push(df1, "Sorted A", "sort")
    assert hm.can_undo
    assert hm.current_df["A"].tolist() == [1, 2, 3]

    df2 = pd.DataFrame({"A": [1, 2]})
    hm.push(df2, "Filtered A", "filter")
    assert hm.current_df["A"].tolist() == [1, 2]

    # Undo back to sorted
    hm.undo()
    assert hm.current_df["A"].tolist() == [1, 2, 3]
    assert hm.can_redo

    # Redo back to filtered
    hm.redo()
    assert hm.current_df["A"].tolist() == [1, 2]

    # Undo twice back to original
    hm.undo()
    hm.undo()
    assert hm.current_df["A"].tolist() == [3, 1, 2]
    assert not hm.can_undo

    # Push clears redo stack
    hm.push(pd.DataFrame({"A": [9]}), "Cleaned", "clean")
    assert not hm.can_redo

    # Restore original preserves exact imported baseline
    hm.restore_original()
    assert hm.current_df["A"].tolist() == [3, 1, 2]
    assert hm.original_df["A"].tolist() == [3, 1, 2]

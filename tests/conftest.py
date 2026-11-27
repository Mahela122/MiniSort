"""Shared pytest fixtures for MiniSort test suite."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import openpyxl
import pandas as pd
import pytest


@pytest.fixture
def sample_employee_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Employee ID": [2, 10, 5, 4, 1, 3],
            "Employee Name": ["Peter", "alex", "John", "Maria", "Zara", "bob"],
            "Department": ["Sales", "Engineering", "Engineering", "Sales", "HR", "Engineering"],
            "Salary": [50000, 70000, 30000, None, 60000, 45000],
            "Joining Date": pd.to_datetime(
                ["2023-05-10", "2021-11-01", "2024-01-15", "2020-02-28", None, "2022-07-04"]
            ),
            "Postal Code": ["02108", "01001", "94107", "02109", "10001", "60601"],
            "Phone": ["0771234561", "0771234562", "0771234563", "0771234564", "0771234565", "0771234566"],
        }
    )


@pytest.fixture
def multi_sheet_xlsx(tmp_path: Path) -> Path:
    path = tmp_path / "company.xlsx"
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Employees"
    ws1.append(["Employee ID", "Employee Name", "Salary", "Joining Date", "Postal Code"])
    ws1.append([2, "Peter", 50000, dt.date(2023, 5, 10), "02108"])
    ws1.append([1, "Alex", 70000, dt.date(2021, 11, 1), "01001"])
    ws1.append([3, "John", None, dt.date(2022, 3, 15), "94107"])

    ws2 = wb.create_sheet("Departments")
    ws2.append(["Department", "Budget"])
    ws2.append(["Engineering", 500000])
    ws2.append(["Sales", 300000])

    wb.save(path)
    wb.close()
    return path

"""Generate realistic sample CSV and Excel datasets for MiniSort users and testing."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import openpyxl
from openpyxl.styles import Font
import pandas as pd

SAMPLE_DIR = Path(__file__).resolve().parent


def create_employee_workbook() -> Path:
    """Multi-sheet Excel workbook with Employee data and Department reference sheet."""
    path = SAMPLE_DIR / "Employee_Data.xlsx"
    wb = openpyxl.Workbook()

    # Sheet 1: Employees
    ws = wb.active
    ws.title = "Employees"
    headers = [
        "Employee ID",
        "Employee Name",
        "Department",
        "Salary",
        "Joining Date",
        "Phone",
        "Postal Code",
    ]
    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        ws.cell(1, col_idx).font = Font(bold=True)

    rows = [
        [105, "Peter Collins", "Engineering", 72000, dt.date(2022, 5, 14), "0771234561", "02108"],
        [102, "Alex Morgan", "Marketing", 54000, dt.date(2023, 1, 20), "0771234562", "01001"],
        [110, "John Carter", "Engineering", 85000, dt.date(2021, 9, 3), "0771234563", "94107"],
        [101, "Maria Garcia", "Finance", 68000, dt.date(2020, 11, 18), "0771234564", "10001"],
        [108, "Priya Nair", "Engineering", 79000, dt.date(2023, 6, 1), "0771234565", "02115"],
        [103, "David Kim", "Sales", 61000, dt.date(2022, 2, 28), "0771234566", "60601"],
        [107, "Hannah Brooks", "Marketing", 58000, dt.date(2024, 3, 11), "0771234567", "30301"],
        [104, "Omar Hassan", "Finance", None, dt.date(2021, 7, 19), "0771234568", "02109"],
        [109, "Sophia Patel", "Sales", 64500, dt.date(2022, 10, 5), "0771234569", "75201"],
        [106, "Liam O'Connor", "Engineering", 72000, dt.date(2023, 8, 22), None, "02110"],
        [112, "Elena Rossi", "HR", 52000, dt.date(2020, 4, 9), "0771234571", "98101"],
        [111, "Noah Bennett", "Sales", 59000, dt.date(2024, 1, 15), "0771234572", "33101"],
    ]
    for r in rows:
        ws.append(r)

    # Sheet 2: Departments
    ws2 = wb.create_sheet(title="Departments")
    ws2.append(["Department", "Location", "Headcount Budget", "Manager"])
    for r in [
        ["Engineering", "Building A", 450000, "John Carter"],
        ["Marketing", "Building B", 210000, "Alex Morgan"],
        ["Finance", "Building A", 280000, "Maria Garcia"],
        ["Sales", "Building C", 320000, "Sophia Patel"],
        ["HR", "Building B", 150000, "Elena Rossi"],
    ]:
        ws2.append(r)

    wb.save(path)
    wb.close()
    return path


def create_student_csv() -> Path:
    path = SAMPLE_DIR / "Student_Records.csv"
    df = pd.DataFrame(
        [
            {"Student ID": 14, "Student Name": "Zara Ali", "Class": "Grade 10", "Marks": 88, "Grade": "A", "Exam Date": "2025-03-15"},
            {"Student ID": 3, "Student Name": "Ben Thomas", "Class": "Grade 10", "Marks": 64, "Grade": "C", "Exam Date": "2025-03-14"},
            {"Student ID": 9, "Student Name": "Chloe Wang", "Class": "Grade 11", "Marks": 95, "Grade": "A+", "Exam Date": "2025-03-16"},
            {"Student ID": 1, "Student Name": "Daniel Reed", "Class": "Grade 10", "Marks": 72, "Grade": "B", "Exam Date": "2025-03-15"},
            {"Student ID": 11, "Student Name": "Amara Okafor", "Class": "Grade 11", "Marks": 81, "Grade": "A", "Exam Date": "2025-03-14"},
            {"Student ID": 5, "Student Name": "Lucas Silva", "Class": "Grade 10", "Marks": 53, "Grade": "D", "Exam Date": "2025-03-16"},
            {"Student ID": 2, "Student Name": "Maya Sharma", "Class": "Grade 11", "Marks": 91, "Grade": "A+", "Exam Date": "2025-03-15"},
            {"Student ID": 7, "Student Name": "Ethan Brooks", "Class": "Grade 10", "Marks": None, "Grade": None, "Exam Date": "2025-03-15"},
            {"Student ID": 10, "Student Name": "Grace Kim", "Class": "Grade 11", "Marks": 78, "Grade": "B+", "Exam Date": "2025-03-14"},
            {"Student ID": 4, "Student Name": "Oliver Grant", "Class": "Grade 10", "Marks": 67, "Grade": "C+", "Exam Date": "2025-03-16"},
        ]
    )
    df.to_csv(path, index=False, encoding="utf-8")
    return path


def create_sales_workbook() -> Path:
    path = SAMPLE_DIR / "Sales_Orders.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Orders"
    ws.append(["Order ID", "Customer Name", "Region", "Sales Amount", "Order Date", "Status"])
    rows = [
        [2004, "Northstar Co", "West", 1240.50, dt.date(2025, 2, 18), "Completed"],
        [2001, "Brightline LLC", "East", 890.00, dt.date(2025, 1, 5), "Completed"],
        [2008, "Summit Retail", "North", 3420.75, dt.date(2025, 4, 2), "Pending"],
        [2002, "Harbor Goods", "South", 450.25, dt.date(2025, 1, 22), "Completed"],
        [2005, "Apex Supply", "West", 2150.00, dt.date(2025, 3, 10), "Shipped"],
        [2003, "Crestview Inc", "East", 1780.00, dt.date(2025, 2, 3), "Cancelled"],
        [2007, "Pinecrest Mart", "North", 995.40, dt.date(2025, 3, 27), "Completed"],
        [2006, "Valley Foods", "South", 3100.00, dt.date(2025, 3, 19), "Shipped"],
    ]
    for r in rows:
        ws.append(r)
    wb.save(path)
    wb.close()
    return path


def create_messy_csv() -> Path:
    """Messy CSV with UTF-8 BOM, duplicates, empty rows, empty column, extra spaces, mixed casing, leading zeros."""
    path = SAMPLE_DIR / "Messy_Contacts.csv"
    lines = [
        "Contact ID,Full Name,City,Postal Code,Phone Number,Notes",
        "001,  alice   smith , new york ,02108,0712345678,",
        "002,BOB  JONES,boston,01001,0712345679,",
        "001,  alice   smith , new york ,02108,0712345678,",
        ",,,,,",
        "003,charlie brown,  chicago  ,60601,,",
        "004,Diana   Prince,seattle,98101,0712345681,",
        "   ,   ,   ,   ,   ,",
        "002,BOB  JONES,boston,01001,0712345679,",
        "005,  evan wright  ,,02115,0712345682,",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    return path


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    files = [
        create_employee_workbook(),
        create_student_csv(),
        create_sales_workbook(),
        create_messy_csv(),
    ]
    for f in files:
        print(f"Created sample: {f.name}")


if __name__ == "__main__":
    main()

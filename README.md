# MiniSort — Smart Spreadsheet Organizer for Windows

**Make spreadsheet organization simple for everyone.**

MiniSort is a 100% offline, minimalist black-and-white Windows desktop application that helps ordinary users organize, sort, filter, clean and export CSV and Excel spreadsheets — without requiring Excel expertise, internet connectivity, accounts or cloud services.

---

## Key Features

- **Simple File Importing**: Supports `.csv`, `.xlsx` and `.xls` files via file browser or drag-and-drop. Automatically detects CSV encodings (UTF-8, UTF-8 BOM, UTF-16, CP1252/Latin-1) and delimiters (`,`, `;`, tab, `|`). Multi-sheet Excel workbooks prompt you to choose a worksheet.
- **Automatic Dataset Detection**: Detects column names, row/column counts, missing values, duplicates and logical data types (`Numeric`, `Text`, `Date`, `Empty`). Protects number-like identifiers (postal codes, phone numbers, zero-padded IDs) from losing leading zeros and lets you manually override any column's type.
- **Paginated Data Preview**: Fast spreadsheet-style preview with horizontal/vertical scrolling, row numbering, clear missing-value indicators (`—`) and configurable page size (`50`–`500` rows) while preserving the full dataset underneath.
- **Smart Sorting & Multi-Column Sorting**:
  - Local rule-based **Smart Sort Suggestions** highlight the most useful columns automatically.
  - Complete rows always stay together.
  - Proper numeric sorting (`1, 2, 3, ..., 10` — never sorted as strings), case-insensitive alphabetical sorting, chronological date sorting and configurable missing-value placement.
  - Multi-column sorting with reordering (`↑`/`↓`) and independent Ascending/Descending order per level.
- **Data Filtering**: Text (`Contains`, `Does not contain`, `Equals`, `Starts with`, `Ends with`), Numeric (`Greater than`, `Less than`, `Equal to`, `Between`), and Date (`Before`, `After`, `Between`) multi-condition filters (`Match All` or `Match Any`), completely non-destructive to your original dataset.
- **Data Cleaning**:
  - Remove duplicate rows (all columns or selected columns)
  - Remove completely empty rows and empty columns
  - Replace missing values (empty text, custom value, numeric value, column average or column median)
  - Trim leading/trailing spaces and normalize repeated internal spaces
  - Format text to `UPPERCASE`, `lowercase` or `Title Case`
  - Confirmation prompts before destructive operations and full Undo support
- **Data Statistics**: Clean monochrome statistic cards for Numeric (`Count`, `Sum`, `Average`, `Minimum`, `Maximum`, `Median`), Text (`Total`, `Unique`, `Top 5 Most Frequent`) and Date (`Earliest`, `Latest`, `Span`) columns.
- **Before & After Comparison + Undo / Redo**: Side-by-side comparison of Original vs. Processed data with memory-bounded Undo/Redo history (`Ctrl+Z` / `Ctrl+Y`) and one-click Restore Original.
- **Safe Exporting**: Export to formatted Excel (`.xlsx` with styled headers, frozen header row, and auto-fitted column widths) or UTF-8 CSV (`.csv`). Descriptive default filenames, overwrite protection against modifying your original source file and one-click "Open Destination Folder".
- **Recent Files & Local Settings**: Stored locally in `%APPDATA%\MiniSort\config.json`. Technical diagnostics are logged locally to `%APPDATA%\MiniSort\logs\minisort.log` without ever logging spreadsheet cell contents.

---

## Quick Start (End-User Journey)

1. **Open MiniSort**
2. **Import File** — Drag and drop a `.csv`, `.xlsx` or `.xls` file onto the window, or click **Import File** (`Ctrl+O`).
3. **Select Column** — Go to **Sort Data**, click a smart suggestion or pick any column under *"What would you like to sort by?"*.
4. **Choose Sorting Order** — Pick **Ascending** or **Descending** (and optionally add secondary sort levels).
5. **Sort Data** — Click **Sort Data** to organize complete rows safely.
6. **Preview Results** — Inspect the preview or open **Compare** to view Before & After side-by-side.
7. **Export File** — Click **Export** (`Ctrl+E`) to save your organized `.xlsx` or `.csv` file.

---

## Running in Development Mode

### Requirements
- Windows 10 or Windows 11
- Python 3.10+ (tested on Python 3.13)

### Setup & Launch

```powershell
# 1. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Regenerate icons or sample datasets
python assets\generate_assets.py
python sample_data\generate_samples.py

# 4. Run MiniSort
python main.py
```

Sample CSV and Excel spreadsheets are available in `sample_data/`:
- `Employee_Data.xlsx` (multi-sheet Excel workbook with Employees & Departments)
- `Student_Records.csv`
- `Sales_Orders.xlsx`
- `Messy_Contacts.csv` (duplicates, empty rows, empty column, extra spaces, leading-zero postal codes & phone numbers)

---

## Running Automated Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

The test suite verifies CSV/Excel import, worksheet selection, auto column detection, leading-zero preservation, numeric/alphabetical/date/multi-column sorting, missing-value handling, filtering, all 6 cleaning operations, statistics, undo/redo, export round-trip accuracy, original file protection, invalid/corrupted file handling, 50,000-row dataset performance, end-to-end UI navigation, and strict black-and-white color compliance.

---

## Packaging & Creating the Windows Installer

### 1. Build Standalone Windows Executable (PyInstaller)

```powershell
.\.venv\Scripts\pyinstaller.exe --clean --noconfirm MiniSort.spec
```

This creates a standalone application bundle in `dist\MiniSort\MiniSort.exe` containing Python, all dependencies, icons, theme files and drag-and-drop runtime libraries.

### 2. Build Windows Installer (`MiniSort_Setup.exe`) with Inno Setup

1. Install [Inno Setup 6](https://jrsoftware.org/isinfo.php).
2. Compile `installer\MiniSort_Setup.iss`:

```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\MiniSort_Setup.iss
```

The installer executable is generated at:
```
installer\Output\MiniSort_Setup.exe
```

It supports custom install directory selection, Start Menu shortcut, optional Desktop shortcut, application icon and standard Windows uninstallation.

---

## Project Structure

```
MiniSort/
├── main.py                     # Desktop application entry point
├── requirements.txt            # Python package dependencies
├── MiniSort.spec               # PyInstaller packaging configuration
├── README.md
├── core/                       # Pure data-processing engines (UI-independent)
│   ├── models.py
│   ├── file_handler.py
│   ├── data_detector.py
│   ├── sorting_engine.py
│   ├── filter_engine.py
│   ├── cleaning_engine.py
│   ├── statistics_engine.py
│   ├── history_manager.py
│   └── export_manager.py
├── ui/                         # Strict black-and-white CustomTkinter UI
│   ├── theme.py
│   ├── components.py
│   ├── dialogs.py
│   ├── main_window.py
│   ├── sidebar.py
│   ├── dashboard.py
│   ├── upload_page.py
│   ├── preview_page.py
│   ├── sorting_page.py
│   ├── filtering_page.py
│   ├── cleaning_page.py
│   ├── statistics_page.py
│   ├── recent_files_page.py
│   ├── settings_page.py
│   └── about_page.py
├── utils/                      # Constants, logging, settings, validation, helpers
├── assets/                     # Monochrome Lucide-style icons, theme_bw.json, minisort.ico
├── sample_data/                # Ready-to-use CSV and Excel sample spreadsheets
├── tests/                      # Comprehensive automated pytest suite
└── installer/
    └── MiniSort_Setup.iss      # Inno Setup Windows installer script
```

---

## Offline & Privacy Guarantee

MiniSort operates **100% locally** on your Windows computer. It makes zero network requests, collects no analytics, requires no login or account and never modifies your original spreadsheet files without your explicit permission.

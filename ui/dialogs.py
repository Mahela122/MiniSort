"""Modal black-and-white dialogs for MiniSort: worksheet picker, column type inspector, export, and history."""

from __future__ import annotations

import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk
import pandas as pd

from core.export_manager import is_same_as_original, suggest_export_filename
from core.models import ColumnInfo, OperationRecord
from ui.components import (
    BaseModalDialog,
    Card,
    PrimaryButton,
    SecondaryButton,
    SegmentedToggle,
    show_alert_dialog,
    show_confirm_dialog,
)
from ui.theme import ThemeManager
from utils.constants import APP_NAME, APP_TAGLINE, APP_VERSION, VALID_COLUMN_TYPES
from utils.helpers import format_int, open_in_file_explorer, truncate_text
from utils.validators import sanitize_filename


def show_sheet_selector_dialog(
    parent: tk.Misc,
    theme: ThemeManager,
    file_name: str,
    sheet_names: list[str],
) -> str | None:
    """Ask the user which Excel worksheet to import when multiple sheets exist."""
    result: dict[str, str | None] = {"sheet": None}
    height = min(460, max(280, 190 + len(sheet_names) * 42))
    dlg = BaseModalDialog(parent, theme, title="Select Worksheet — MiniSort", width=460, height=height)

    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=20)

    ctk.CTkLabel(
        body,
        text="Choose a worksheet to import",
        font=theme.font(16, "bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).pack(anchor="w")

    ctk.CTkLabel(
        body,
        text=f"'{truncate_text(file_name, 42)}' contains {len(sheet_names)} worksheets. Select one below:",
        font=theme.font(12, "normal"),
        text_color=theme.color("text_secondary"),
        anchor="w",
        wraplength=410,
    ).pack(anchor="w", pady=(4, 14))

    selected_var = tk.StringVar(value=sheet_names[0])

    scroll = ctk.CTkScrollableFrame(
        body,
        fg_color=theme.color("bg_subtle"),
        border_color=theme.color("border"),
        border_width=1,
        corner_radius=8,
    )
    scroll.pack(fill="both", expand=True, pady=(0, 14))

    for name in sheet_names:
        row = ctk.CTkFrame(scroll, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=4)
        ctk.CTkRadioButton(
            row,
            text=name,
            variable=selected_var,
            value=name,
            font=theme.font(13, "normal"),
            text_color=theme.color("text_primary"),
            fg_color=theme.color("btn_primary_bg"),
            border_color=theme.color("border_strong"),
            hover_color=theme.color("btn_primary_hover"),
        ).pack(anchor="w", padx=4, pady=2)

    footer = ctk.CTkFrame(body, fg_color="transparent")
    footer.pack(fill="x")

    def _confirm() -> None:
        result["sheet"] = selected_var.get()
        dlg.destroy()

    PrimaryButton(footer, theme, text="Import Worksheet", command=_confirm, width=150, height=36).pack(side="right")
    SecondaryButton(footer, theme, text="Cancel", command=dlg.destroy, width=96, height=36).pack(
        side="right", padx=(0, 10)
    )
    dlg.finalize_layout()
    dlg.bind("<Escape>", lambda _e: dlg.destroy())
    parent.wait_window(dlg)

    return result["sheet"]


def show_column_type_inspector_dialog(
    parent: tk.Misc,
    theme: ThemeManager,
    column_infos: list[ColumnInfo],
) -> dict[str, str] | None:
    """Allow users to inspect detected column types and manually override any type."""
    result: dict[str, dict[str, str] | None] = {"overrides": None}
    dlg = BaseModalDialog(parent, theme, title="Inspect & Adjust Column Types", width=760, height=540)

    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=20)

    ctk.CTkLabel(
        body,
        text="Inspect & Adjust Column Data Types",
        font=theme.font(17, "bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).pack(anchor="w")

    ctk.CTkLabel(
        body,
        text=(
            "MiniSort detects each column type automatically. If a number-like column "
            "(such as Employee ID, postal code, or phone number) should stay as Text, "
            "or if a date/number column needs correction, change it below."
        ),
        font=theme.font(12, "normal"),
        text_color=theme.color("text_secondary"),
        wraplength=700,
        justify="left",
        anchor="w",
    ).pack(anchor="w", pady=(4, 14))

    # Header bar
    insp_weights = (3, 2, 3, 2)
    hdr = ctk.CTkFrame(body, fg_color=theme.color("bg_subtle"), corner_radius=6)
    hdr.pack(fill="x", pady=(0, 6))
    for col_idx, (w, label) in enumerate(zip(insp_weights, ("Column Name", "Detected", "Sample / Note", "Use Type"))):
        hdr.grid_columnconfigure(col_idx, weight=w, uniform="insp_cols")
        ctk.CTkLabel(
            hdr,
            text=label,
            width=10,
            font=theme.font(12, "bold"),
            text_color=theme.color("text_primary"),
            anchor="w",
        ).grid(row=0, column=col_idx, sticky="ew", padx=10, pady=8)

    scroll = ctk.CTkScrollableFrame(
        body,
        fg_color=theme.color("bg_surface"),
        border_width=1,
        border_color=theme.color("border"),
        corner_radius=8,
    )
    scroll.pack(fill="both", expand=True, pady=(0, 14))

    vars_by_col: dict[str, tk.StringVar] = {}
    detected_by_col: dict[str, str] = {}

    for idx, info in enumerate(column_infos):
        detected_by_col[info.name] = info.detected_type
        var = tk.StringVar(value=info.effective_type)
        vars_by_col[info.name] = var

        row = ctk.CTkFrame(
            scroll,
            fg_color=theme.color("bg_subtle") if idx % 2 == 0 else "transparent",
            corner_radius=6,
        )
        row.pack(fill="x", padx=6, pady=2)
        for col_idx, w in enumerate(insp_weights):
            row.grid_columnconfigure(col_idx, weight=w, uniform="insp_cols")

        ctk.CTkLabel(
            row,
            text=truncate_text(info.name, 26),
            width=10,
            font=theme.font(12, "bold"),
            text_color=theme.color("text_primary"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=10, pady=8)

        ctk.CTkLabel(
            row,
            text=info.detected_type,
            width=10,
            font=theme.font(12, "normal"),
            text_color=theme.color("text_secondary"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=10, pady=8)

        sample_preview = ", ".join(info.sample_values[:2]) if info.sample_values else "(empty)"
        note_text = truncate_text(sample_preview, 32)
        ctk.CTkLabel(
            row,
            text=note_text,
            width=10,
            font=theme.font(11, "normal"),
            text_color=theme.color("text_muted"),
            anchor="w",
        ).grid(row=0, column=2, sticky="ew", padx=10, pady=8)

        menu = ctk.CTkOptionMenu(
            row,
            values=list(VALID_COLUMN_TYPES),
            variable=var,
            width=120,
            height=30,
            font=theme.font(12, "normal"),
            fg_color=theme.color("bg_surface"),
            button_color=theme.color("bg_hover"),
            button_hover_color=theme.color("bg_active_subtle"),
            text_color=theme.color("text_primary"),
            dropdown_fg_color=theme.color("bg_surface"),
            dropdown_hover_color=theme.color("bg_hover"),
            dropdown_text_color=theme.color("text_primary"),
        )
        menu.grid(row=0, column=3, sticky="e", padx=10, pady=6)

    footer = ctk.CTkFrame(body, fg_color="transparent")
    footer.pack(fill="x")

    def _reset_auto() -> None:
        for col_name, var in vars_by_col.items():
            var.set(detected_by_col[col_name])

    def _apply() -> None:
        overrides: dict[str, str] = {}
        for col_name, var in vars_by_col.items():
            chosen = var.get()
            if chosen != detected_by_col[col_name]:
                overrides[col_name] = chosen
        result["overrides"] = overrides
        dlg.destroy()

    SecondaryButton(footer, theme, text="Reset to Automatic", command=_reset_auto, width=150, height=36).pack(
        side="left"
    )
    PrimaryButton(footer, theme, text="Apply Column Types", command=_apply, width=165, height=36).pack(side="right")
    SecondaryButton(footer, theme, text="Cancel", command=dlg.destroy, width=96, height=36).pack(
        side="right", padx=(0, 10)
    )

    dlg.finalize_layout()
    dlg.bind("<Escape>", lambda _e: dlg.destroy())
    parent.wait_window(dlg)

    return result["overrides"]


def show_export_dialog(
    parent: tk.Misc,
    theme: ThemeManager,
    source_file_path: str,
    source_file_name: str,
    current_df: pd.DataFrame,
    original_df: pd.DataFrame,
    operation_category: str,
    default_format: str,
    on_confirm_export: Callable[[pd.DataFrame, Path, str], None],
) -> None:
    """Open the monochrome Export dialog with scope, format, folder, filename, and overwrite safety."""
    dlg = BaseModalDialog(parent, theme, title="Export Dataset — MiniSort", width=560, height=530)

    # Anchor footer at bottom FIRST so Export File & Cancel buttons are never clipped at any DPI
    footer_wrap = ctk.CTkFrame(dlg, fg_color=theme.color("bg_surface"), corner_radius=0)
    footer_wrap.pack(side="bottom", fill="x")

    ctk.CTkFrame(footer_wrap, height=1, fg_color=theme.color("border"), corner_radius=0).pack(fill="x")
    footer = ctk.CTkFrame(footer_wrap, fg_color="transparent")
    footer.pack(fill="x", padx=24, pady=14)

    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=(20, 12))

    ctk.CTkLabel(
        body,
        text="Export Your Spreadsheet",
        font=theme.font(17, "bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).pack(anchor="w")

    ctk.CTkLabel(
        body,
        text="Save a new Excel or CSV file without modifying your original spreadsheet.",
        font=theme.font(12, "normal"),
        text_color=theme.color("text_secondary"),
        anchor="w",
    ).pack(anchor="w", pady=(2, 14))

    # Scope selection (always defaults to current Sorted / Filtered / Cleaned Records)
    scope_labels = {
        "sort": f"Sorted Records ({format_int(len(current_df))} rows)",
        "filter": f"Filtered Records ({format_int(len(current_df))} rows)",
        "clean": f"Cleaned Records ({format_int(len(current_df))} rows)",
        "type": f"Processed Records ({format_int(len(current_df))} rows)",
        "import": f"Current Dataset ({format_int(len(current_df))} rows)",
    }
    current_scope_label = scope_labels.get(operation_category, f"Current Records ({format_int(len(current_df))} rows)")
    all_scope_label = f"All Original Records — Unmodified ({format_int(len(original_df))} rows)"

    ctk.CTkLabel(
        body,
        text="What to export",
        font=theme.font(12, "bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).pack(anchor="w", pady=(0, 6))

    scope_options = [current_scope_label]
    if len(current_df) != len(original_df) or operation_category != "import":
        scope_options.append(all_scope_label)

    scope_var = tk.StringVar(master=dlg, value=current_scope_label)
    scope_menu = ctk.CTkOptionMenu(
        body,
        values=scope_options,
        variable=scope_var,
        height=36,
        font=theme.font(13, "normal"),
        fg_color=theme.color("bg_subtle"),
        button_color=theme.color("bg_hover"),
        button_hover_color=theme.color("bg_active_subtle"),
        text_color=theme.color("text_primary"),
        dropdown_fg_color=theme.color("bg_surface"),
        dropdown_hover_color=theme.color("bg_hover"),
        dropdown_text_color=theme.color("text_primary"),
    )
    scope_menu.set(current_scope_label)
    scope_menu.pack(fill="x", pady=(0, 12))

    # Format selection
    ctk.CTkLabel(
        body,
        text="File format",
        font=theme.font(12, "bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).pack(anchor="w", pady=(0, 6))

    initial_fmt_label = "CSV (.csv)" if str(default_format).lower() == "csv" else "Excel (.xlsx)"

    default_dir = str(Path(source_file_path).parent) if source_file_path else os.path.expanduser("~")
    if not os.path.isdir(default_dir):
        default_dir = os.path.expanduser("~")

    dir_var = tk.StringVar(master=dlg, value=default_dir)
    name_var = tk.StringVar(
        master=dlg,
        value=Path(
            suggest_export_filename(source_file_name, operation_category, default_format)
        ).stem,
    )
    # Keep strong references on the dialog so Tkinter StringVars cannot be garbage-collected
    dlg._export_vars = (scope_var, dir_var, name_var)  # type: ignore[attr-defined]

    def _on_fmt_change(_val: str) -> None:
        pass

    fmt_toggle = SegmentedToggle(
        body,
        theme,
        options=["Excel (.xlsx)", "CSV (.csv)"],
        initial=initial_fmt_label,
        command=_on_fmt_change,
        height=36,
    )
    fmt_toggle.pack(fill="x", pady=(0, 12))

    def _on_scope_change(selected: str) -> None:
        cat = "all" if selected == all_scope_label else operation_category
        fmt = "csv" if "CSV" in fmt_toggle.get() else "xlsx"
        name_var.set(Path(suggest_export_filename(source_file_name, cat, fmt)).stem)

    scope_menu.configure(command=_on_scope_change)

    # Filename input
    ctk.CTkLabel(
        body,
        text="File name (extension is added automatically)",
        font=theme.font(12, "bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).pack(anchor="w", pady=(0, 6))

    name_entry = ctk.CTkEntry(
        body,
        textvariable=name_var,
        height=36,
        font=theme.font(13, "normal"),
    )
    name_entry.pack(fill="x", pady=(0, 12))

    # Destination folder picker
    ctk.CTkLabel(
        body,
        text="Destination folder",
        font=theme.font(12, "bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).pack(anchor="w", pady=(0, 6))

    dir_row = ctk.CTkFrame(body, fg_color="transparent")
    dir_row.pack(fill="x", pady=(0, 4))

    dir_entry = ctk.CTkEntry(
        dir_row,
        textvariable=dir_var,
        height=36,
        font=theme.font(12, "normal"),
    )
    dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

    def _choose_folder() -> None:
        chosen = filedialog.askdirectory(
            title="Choose Export Destination Folder",
            initialdir=dir_var.get() if os.path.isdir(dir_var.get()) else os.path.expanduser("~"),
            parent=dlg,
        )
        if chosen:
            dir_var.set(chosen)

    SecondaryButton(dir_row, theme, text="Browse", command=_choose_folder, width=96, height=36).pack(side="right")

    def _export() -> None:
        raw_name = name_var.get().strip()
        if not raw_name:
            show_alert_dialog(dlg, theme, "Missing File Name", "Please enter a name for the exported file.")
            return
        folder = Path(dir_var.get().strip())
        if not folder.exists() or not folder.is_dir():
            show_alert_dialog(
                dlg,
                theme,
                "Invalid Folder",
                "The chosen destination folder does not exist. Please browse and select a valid folder.",
            )
            return

        fmt = "csv" if "CSV" in fmt_toggle.get() else "xlsx"
        clean_stem = sanitize_filename(Path(raw_name).stem if raw_name.lower().endswith((".xlsx", ".csv")) else raw_name)
        dest_path = folder / f"{clean_stem}.{fmt}"

        # Strict original file overwrite protection
        if is_same_as_original(dest_path, source_file_path):
            confirmed = show_confirm_dialog(
                dlg,
                theme,
                title="Overwrite Original File?",
                message=(
                    f"'{dest_path.name}' is your original imported file.\n\n"
                    "MiniSort recommends saving to a new filename so your original data stays untouched. "
                    "Do you really want to overwrite the original file?"
                ),
                confirm_text="Yes, Overwrite",
                cancel_text="Choose Another Name",
            )
            if not confirmed:
                return
        elif dest_path.exists():
            confirmed = show_confirm_dialog(
                dlg,
                theme,
                title="Replace Existing File?",
                message=f"A file named '{dest_path.name}' already exists in this folder. Replace it?",
                confirm_text="Replace File",
                cancel_text="Cancel",
            )
            if not confirmed:
                return

        target_df = original_df if scope_var.get() == all_scope_label else current_df
        dlg.destroy()
        on_confirm_export(target_df, dest_path, fmt)

    PrimaryButton(footer, theme, text="Export File", icon_name="export", command=_export, width=148, height=38).pack(
        side="right"
    )
    SecondaryButton(footer, theme, text="Cancel", command=dlg.destroy, width=96, height=38).pack(
        side="right", padx=(0, 10)
    )

    dlg.finalize_layout()
    dlg.bind("<Return>", lambda _e: _export())
    dlg.bind("<Escape>", lambda _e: dlg.destroy())


def show_export_success_dialog(
    parent: tk.Misc,
    theme: ThemeManager,
    saved_path: Path,
    row_count: int,
) -> None:
    """Display export confirmation with a one-click button to open the destination folder."""
    dlg = BaseModalDialog(parent, theme, title="Export Complete — MiniSort", width=480, height=250)

    def _open_folder() -> None:
        open_in_file_explorer(saved_path)
        dlg.destroy()

    footer = ctk.CTkFrame(dlg, fg_color="transparent")
    footer.pack(side="bottom", fill="x", padx=24, pady=(0, 18))
    PrimaryButton(footer, theme, text="Open Destination Folder", icon_name="folder", command=_open_folder, height=36).pack(
        side="right"
    )
    SecondaryButton(footer, theme, text="Close", command=dlg.destroy, width=86, height=36).pack(
        side="right", padx=(0, 10)
    )

    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=(20, 12))

    title_row = ctk.CTkFrame(body, fg_color="transparent")
    title_row.pack(fill="x", pady=(0, 10))
    ctk.CTkLabel(title_row, text="", image=theme.icon("check", "dark", 20)).pack(side="left", padx=(0, 8))
    ctk.CTkLabel(
        title_row,
        text="File exported successfully",
        font=theme.font(16, "bold"),
        text_color=theme.color("text_primary"),
    ).pack(side="left")

    ctk.CTkLabel(
        body,
        text=(
            f"Saved {format_int(row_count)} rows to:\n"
            f"{saved_path}\n\n"
            "Your original source file was not modified."
        ),
        font=theme.font(12, "normal"),
        text_color=theme.color("text_secondary"),
        wraplength=425,
        justify="left",
        anchor="w",
    ).pack(anchor="w", fill="x", expand=True)

    dlg.finalize_layout()
    dlg.bind("<Escape>", lambda _e: dlg.destroy())
    parent.wait_window(dlg)



def show_history_dialog(
    parent: tk.Misc,
    theme: ThemeManager,
    operations: list[OperationRecord],
    can_undo: bool,
    can_redo: bool,
    on_undo: Callable[[], None],
    on_redo: Callable[[], None],
    on_restore_original: Callable[[], None],
) -> None:
    """Display the recent operations timeline with Undo, Redo, and Restore Original controls."""
    dlg = BaseModalDialog(parent, theme, title="Operation History — MiniSort", width=560, height=430)

    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=20)

    ctk.CTkLabel(
        body,
        text="Recent Operations",
        font=theme.font(17, "bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).pack(anchor="w")

    ctk.CTkLabel(
        body,
        text="Review changes made to your dataset in this session. You can undo, redo, or restore the original data.",
        font=theme.font(12, "normal"),
        text_color=theme.color("text_secondary"),
        wraplength=500,
        justify="left",
        anchor="w",
    ).pack(anchor="w", pady=(2, 12))

    scroll = ctk.CTkScrollableFrame(
        body,
        fg_color=theme.color("bg_subtle"),
        border_width=1,
        border_color=theme.color("border"),
        corner_radius=8,
    )
    scroll.pack(fill="both", expand=True, pady=(0, 14))

    for idx, rec in enumerate(reversed(operations)):
        is_latest = idx == 0
        item = Card(scroll, theme, subtle=False, corner_radius=8)
        item.pack(fill="x", padx=6, pady=4)
        if is_latest:
            item.configure(border_color=theme.color("border_dark"), border_width=1)

        top = ctk.CTkFrame(item, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(8, 2))
        badge_text = "CURRENT  •  " if is_latest else ""
        ctk.CTkLabel(
            top,
            text=f"{badge_text}{rec.description}",
            font=theme.font(12, "bold"),
            text_color=theme.color("text_primary"),
            anchor="w",
        ).pack(side="left")
        ctk.CTkLabel(
            top,
            text=rec.timestamp,
            font=theme.font(11, "normal"),
            text_color=theme.color("text_muted"),
        ).pack(side="right")

        ctk.CTkLabel(
            item,
            text=(
                f"Rows: {format_int(rec.row_count_before)} → {format_int(rec.row_count_after)}   •   "
                f"Columns: {format_int(rec.col_count_before)} → {format_int(rec.col_count_after)}"
            ),
            font=theme.font(11, "normal"),
            text_color=theme.color("text_secondary"),
            anchor="w",
        ).pack(anchor="w", padx=12, pady=(0, 8))

    footer = ctk.CTkFrame(body, fg_color="transparent")
    footer.pack(fill="x")

    def _run_and_close(fn: Callable[[], None]) -> None:
        dlg.destroy()
        fn()

    SecondaryButton(
        footer,
        theme,
        text="Restore Original",
        command=lambda: _run_and_close(on_restore_original),
        height=34,
    ).pack(side="left")

    PrimaryButton(footer, theme, text="Close", command=dlg.destroy, width=88, height=34).pack(side="right")

    redo_btn = SecondaryButton(
        footer,
        theme,
        text="Redo",
        icon_name="redo",
        command=lambda: _run_and_close(on_redo),
        width=84,
        height=34,
    )
    redo_btn.configure(state="normal" if can_redo else "disabled")
    redo_btn.pack(side="right", padx=(0, 8))

    undo_btn = SecondaryButton(
        footer,
        theme,
        text="Undo",
        icon_name="undo",
        command=lambda: _run_and_close(on_undo),
        width=84,
        height=34,
    )
    undo_btn.configure(state="normal" if can_undo else "disabled")
    undo_btn.pack(side="right", padx=(0, 8))

    dlg.finalize_layout()
    dlg.bind("<Escape>", lambda _e: dlg.destroy())
    parent.wait_window(dlg)


def show_welcome_guide_dialog(
    parent: tk.Misc,
    theme: ThemeManager,
    is_first_install: bool = True,
    on_dismiss: Callable[[bool], None] | None = None,
) -> None:
    """Show the first-time / new-version Welcome, How to Use and What's New dialog."""
    dlg = BaseModalDialog(parent, theme, title=f"Welcome to {APP_NAME} — Version {APP_VERSION}", width=640, height=580)

    dont_show_var = tk.BooleanVar(master=dlg, value=True)
    dlg._welcome_var = dont_show_var  # type: ignore[attr-defined]

    def _finish() -> None:
        remember = bool(dont_show_var.get())
        dlg.destroy()
        if on_dismiss is not None:
            on_dismiss(remember)

    # Bottom footer anchored first so Get Started is always visible at every DPI
    footer_wrap = ctk.CTkFrame(dlg, fg_color=theme.color("bg_surface"), corner_radius=0)
    footer_wrap.pack(side="bottom", fill="x")
    ctk.CTkFrame(footer_wrap, height=1, fg_color=theme.color("border"), corner_radius=0).pack(fill="x")

    footer = ctk.CTkFrame(footer_wrap, fg_color="transparent")
    footer.pack(fill="x", padx=24, pady=14)

    ctk.CTkCheckBox(
        footer,
        text=f"Don't show automatically again for Version {APP_VERSION}",
        variable=dont_show_var,
        font=theme.font(12, "normal"),
        text_color=theme.color("text_secondary"),
    ).pack(side="left")

    PrimaryButton(
        footer,
        theme,
        text="Get Started",
        icon_name="check",
        command=_finish,
        width=142,
        height=38,
    ).pack(side="right")

    # Main content area
    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=(20, 12))

    # Hero header with custom MiniSort logo
    hero = ctk.CTkFrame(body, fg_color="transparent")
    hero.pack(fill="x", pady=(0, 14))

    logo = theme.app_logo(48)
    if logo is not None:
        ctk.CTkLabel(hero, text="", image=logo).pack(side="left", padx=(0, 14))

    hero_text = ctk.CTkFrame(hero, fg_color="transparent")
    hero_text.pack(side="left", fill="x", expand=True)

    headline = f"Welcome to {APP_NAME}" if is_first_install else f"Updated to {APP_NAME} Version {APP_VERSION}"
    ctk.CTkLabel(
        hero_text,
        text=headline,
        font=theme.font(19, "bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).pack(anchor="w")

    ctk.CTkLabel(
        hero_text,
        text=f"{APP_TAGLINE}  •  Version {APP_VERSION}  •  100% Offline",
        font=theme.font(12, "normal"),
        text_color=theme.color("text_muted"),
        anchor="w",
    ).pack(anchor="w", pady=(2, 0))

    # Tab switcher: How to Use | What's New
    content_holder = ctk.CTkScrollableFrame(
        body,
        fg_color=theme.color("bg_subtle"),
        border_width=1,
        border_color=theme.color("border"),
        corner_radius=10,
    )

    def _render_tab(tab_name: str) -> None:
        for child in content_holder.winfo_children():
            child.destroy()

        if tab_name == "How to Use":
            steps = [
                (
                    "1",
                    "Import Your Spreadsheet",
                    "Click Import File (or drag and drop any .csv, .xlsx or .xls file anywhere in the window). For multi-sheet Excel files, pick the worksheet you want.",
                ),
                (
                    "2",
                    "Sort, Filter or Clean",
                    "Open Sort Data and pick a column or Smart Sort Suggestion, choose Ascending or Descending or add multiple sort levels. Use Filter Data and Clean Data to remove duplicates, blanks or extra spaces.",
                ),
                (
                    "3",
                    "Preview, Check Statistics & Compare",
                    "Inspect your data in the paginated table, view column totals and averages in Data Statistics or click Compare to review Before and After side by side.",
                ),
                (
                    "4",
                    "Export Safely Without Touching Originals",
                    "Click Export to save a brand-new .xlsx or .csv file. Your original file is never overwritten without permission and every edit supports Undo and Redo.",
                ),
            ]
            for num, title, desc in steps:
                item = Card(content_holder, theme, subtle=False, corner_radius=8)
                item.pack(fill="x", padx=10, pady=5)

                row = ctk.CTkFrame(item, fg_color="transparent")
                row.pack(fill="x", padx=12, pady=10)

                badge = ctk.CTkLabel(
                    row,
                    text=num,
                    width=26,
                    height=26,
                    corner_radius=13,
                    fg_color=theme.color("btn_primary_bg"),
                    text_color=theme.color("btn_primary_text"),
                    font=theme.font(12, "bold"),
                )
                badge.pack(side="left", anchor="n", padx=(0, 12), pady=(2, 0))

                txt = ctk.CTkFrame(row, fg_color="transparent")
                txt.pack(side="left", fill="x", expand=True)

                ctk.CTkLabel(
                    txt,
                    text=title,
                    font=theme.font(13, "bold"),
                    text_color=theme.color("text_primary"),
                    anchor="w",
                ).pack(anchor="w")

                ctk.CTkLabel(
                    txt,
                    text=desc,
                    font=theme.font(12, "normal"),
                    text_color=theme.color("text_secondary"),
                    wraplength=490,
                    justify="left",
                    anchor="w",
                ).pack(anchor="w", pady=(2, 0))

            # Handy shortcuts strip
            shortcuts = Card(content_holder, theme, subtle=False, corner_radius=8)
            shortcuts.pack(fill="x", padx=10, pady=(6, 10))
            ctk.CTkLabel(
                shortcuts,
                text="Keyboard Shortcuts:   Ctrl+O Import   •   Ctrl+Z Undo   •   Ctrl+Y Redo   •   Ctrl+E Export",
                font=theme.font(11, "bold"),
                text_color=theme.color("text_secondary"),
            ).pack(padx=12, pady=10)
        else:
            whats_new = [
                (
                    "New Custom MiniSort Logo & Loading Screen",
                    "Refreshed brand identity across the app header, startup loading screen, taskbar and Windows installer.",
                ),
                (
                    "Background Colors & Display Settings",
                    "Open Settings to pick from 5 background themes (Pure White, Soft Grey, Warm Paper, Dark Charcoal or Pure Black), pick any Custom Color or adjust Text Size and Table Row Density.",
                ),
                (
                    "Smarter Export Workflow",
                    "Exports default directly to your Sorted, Filtered or Cleaned records with descriptive filenames and automatic overwrite protection.",
                ),
                (
                    "Polished Statistics & Sorting Layouts",
                    "Pixel-aligned All Columns Overview table in Data Statistics and compact single-level and multi-level sorting controls.",
                ),
                (
                    "100% Offline Standalone Experience",
                    "Runs completely locally on Windows with zero internet connection, zero accounts and zero separate Python installation.",
                ),
            ]
            for title, desc in whats_new:
                item = Card(content_holder, theme, subtle=False, corner_radius=8)
                item.pack(fill="x", padx=10, pady=5)

                ctk.CTkLabel(
                    item,
                    text=f"•  {title}",
                    font=theme.font(13, "bold"),
                    text_color=theme.color("text_primary"),
                    anchor="w",
                ).pack(anchor="w", padx=14, pady=(10, 2))

                ctk.CTkLabel(
                    item,
                    text=desc,
                    font=theme.font(12, "normal"),
                    text_color=theme.color("text_secondary"),
                    wraplength=510,
                    justify="left",
                    anchor="w",
                ).pack(anchor="w", padx=24, pady=(0, 10))

    initial_tab = "How to Use" if is_first_install else "What's New"
    tabs = SegmentedToggle(
        body,
        theme,
        options=["How to Use", "What's New"],
        initial=initial_tab,
        command=_render_tab,
        height=36,
    )
    tabs.pack(fill="x", pady=(0, 12))
    content_holder.pack(fill="both", expand=True)

    _render_tab(initial_tab)
    dlg.finalize_layout()
    dlg.protocol("WM_DELETE_WINDOW", _finish)
    dlg.bind("<Return>", lambda _e: _finish())
    dlg.bind("<Escape>", lambda _e: _finish())
    parent.wait_window(dlg)

"""Reusable minimalist black-and-white UI components for MiniSort."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable

import customtkinter as ctk
import pandas as pd

from ui.theme import ThemeManager
from utils.constants import MISSING_DISPLAY_TEXT
from utils.helpers import format_int, get_asset_path


class Card(ctk.CTkFrame):
    """Minimalist white surface card with crisp grey border."""

    def __init__(
        self,
        master: Any,
        theme: ThemeManager,
        subtle: bool = False,
        corner_radius: int = 10,
        **kwargs: Any,
    ) -> None:
        bg = theme.color("bg_subtle") if subtle else theme.color("bg_surface")
        kwargs.setdefault("fg_color", bg)
        kwargs.setdefault("border_color", theme.color("border"))
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("corner_radius", corner_radius)
        super().__init__(master, **kwargs)


class PrimaryButton(ctk.CTkButton):
    """Primary black action button with white text."""

    def __init__(
        self,
        master: Any,
        theme: ThemeManager,
        text: str,
        command: Callable[[], Any] | None = None,
        icon_name: str | None = None,
        height: int = 38,
        **kwargs: Any,
    ) -> None:
        img = theme.icon(icon_name, "light", 16) if icon_name else None
        kwargs.setdefault("fg_color", theme.color("btn_primary_bg"))
        kwargs.setdefault("hover_color", theme.color("btn_primary_hover"))
        kwargs.setdefault("text_color", theme.color("btn_primary_text"))
        kwargs.setdefault("font", theme.font(13, "bold"))
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("height", height)
        if img is not None:
            kwargs.setdefault("image", img)
            kwargs.setdefault("compound", "left")
        super().__init__(master, text=text, command=command, **kwargs)


class SecondaryButton(ctk.CTkButton):
    """Secondary light-grey button with crisp border and dark text."""

    def __init__(
        self,
        master: Any,
        theme: ThemeManager,
        text: str,
        command: Callable[[], Any] | None = None,
        icon_name: str | None = None,
        height: int = 38,
        **kwargs: Any,
    ) -> None:
        img = theme.icon(icon_name, "dark", 16) if icon_name else None
        kwargs.setdefault("fg_color", theme.color("btn_secondary_bg"))
        kwargs.setdefault("hover_color", theme.color("btn_secondary_hover"))
        kwargs.setdefault("text_color", theme.color("btn_secondary_text"))
        kwargs.setdefault("border_color", theme.color("border"))
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("font", theme.font(13, "normal"))
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("height", height)
        if img is not None:
            kwargs.setdefault("image", img)
            kwargs.setdefault("compound", "left")
        super().__init__(master, text=text, command=command, **kwargs)


class GhostButton(ctk.CTkButton):
    """Subtle borderless monochrome button."""

    def __init__(
        self,
        master: Any,
        theme: ThemeManager,
        text: str,
        command: Callable[[], Any] | None = None,
        icon_name: str | None = None,
        height: int = 34,
        **kwargs: Any,
    ) -> None:
        img = theme.icon(icon_name, "dark", 15) if icon_name else None
        kwargs.setdefault("fg_color", "transparent")
        kwargs.setdefault("hover_color", theme.color("btn_ghost_hover"))
        kwargs.setdefault("text_color", theme.color("text_primary"))
        kwargs.setdefault("font", theme.font(13, "normal"))
        kwargs.setdefault("corner_radius", 7)
        kwargs.setdefault("height", height)
        if img is not None:
            kwargs.setdefault("image", img)
            kwargs.setdefault("compound", "left")
        super().__init__(master, text=text, command=command, **kwargs)


class SegmentedToggle(ctk.CTkFrame):
    """Strict black-and-white segmented toggle with black active pill and white active text."""

    def __init__(
        self,
        master: Any,
        theme: ThemeManager,
        options: list[str],
        initial: str | None = None,
        command: Callable[[str], Any] | None = None,
        height: int = 36,
    ) -> None:
        super().__init__(
            master,
            fg_color=theme.color("bg_subtle"),
            border_color=theme.color("border"),
            border_width=1,
            corner_radius=8,
        )
        self._theme = theme
        self._items = list(options)
        self._command = command
        self._value = initial if initial in self._items else (self._items[0] if self._items else "")
        self._buttons: dict[str, ctk.CTkButton] = {}

        for idx, opt in enumerate(self._items):
            btn = ctk.CTkButton(
                self,
                text=opt,
                height=height - 6,
                corner_radius=6,
                border_width=0,
                font=theme.font(12, "bold"),
                command=lambda o=opt: self._select(o, notify=True),
            )
            btn.grid(row=0, column=idx, padx=3, pady=3, sticky="ew")
            self.grid_columnconfigure(idx, weight=1)
            self._buttons[opt] = btn

        self._render()

    def _select(self, option: str, notify: bool = False) -> None:
        if option not in self._buttons:
            return
        self._value = option
        self._render()
        if notify and self._command:
            self._command(option)

    def _render(self) -> None:
        for opt, btn in self._buttons.items():
            if opt == self._value:
                btn.configure(
                    fg_color=self._theme.color("btn_primary_bg"),
                    hover_color=self._theme.color("btn_primary_hover"),
                    text_color=self._theme.color("btn_primary_text"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    hover_color=self._theme.color("bg_hover"),
                    text_color=self._theme.color("text_primary"),
                )

    def get(self) -> str:
        return self._value

    def set(self, value: str, notify: bool = False) -> None:
        self._select(value, notify=notify)


class SectionHeader(ctk.CTkFrame):
    """Consistent page or section title block with subtitle and optional right-side controls."""

    def __init__(
        self,
        master: Any,
        theme: ThemeManager,
        title: str,
        subtitle: str = "",
        title_size: int = 22,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")

        self.title_label = ctk.CTkLabel(
            left,
            text=title,
            font=theme.font(title_size, "bold"),
            text_color=theme.color("text_primary"),
            anchor="w",
        )
        self.title_label.pack(anchor="w")

        if subtitle:
            self.subtitle_label = ctk.CTkLabel(
                left,
                text=subtitle,
                font=theme.font(13, "normal"),
                text_color=theme.color("text_secondary"),
                anchor="w",
                justify="left",
            )
            self.subtitle_label.pack(anchor="w", pady=(2, 0))

        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent", width=0, height=0)
        self.actions_frame.grid(row=0, column=1, sticky="e")


class StatTile(Card):
    """Minimalist monochrome metric card."""

    def __init__(
        self,
        master: Any,
        theme: ThemeManager,
        label: str,
        value: str,
        note: str = "",
        subtle: bool = False,
    ) -> None:
        super().__init__(master, theme, subtle=subtle, corner_radius=10)
        self._label_lbl = ctk.CTkLabel(
            self,
            text=label,
            font=theme.font(12, "normal"),
            text_color=theme.color("text_muted"),
            anchor="w",
        )
        self._label_lbl.pack(anchor="w", padx=16, pady=(12, 2))

        self._value_lbl = ctk.CTkLabel(
            self,
            text=value,
            font=theme.font(22, "bold"),
            text_color=theme.color("text_primary"),
            anchor="w",
        )
        self._value_lbl.pack(anchor="w", padx=16, pady=(0, 4 if note else 12))

        self._note_lbl: ctk.CTkLabel | None = None
        if note:
            self._note_lbl = ctk.CTkLabel(
                self,
                text=note,
                font=theme.font(11, "normal"),
                text_color=theme.color("text_secondary"),
                anchor="w",
            )
            self._note_lbl.pack(anchor="w", padx=16, pady=(0, 12))

    def set_value(self, value: str, note: str | None = None) -> None:
        self._value_lbl.configure(text=value)
        if note is not None and self._note_lbl is not None:
            self._note_lbl.configure(text=note)


class EmptyState(Card):
    """Clean centered empty state shown when no dataset is loaded yet."""

    def __init__(
        self,
        master: Any,
        theme: ThemeManager,
        title: str,
        description: str,
        button_text: str = "Import Spreadsheet",
        on_action: Callable[[], Any] | None = None,
        icon_name: str = "upload",
    ) -> None:
        super().__init__(master, theme, subtle=True, corner_radius=12)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        icon_box = ctk.CTkFrame(
            inner,
            width=56,
            height=56,
            corner_radius=28,
            fg_color=theme.color("bg_surface"),
            border_width=1,
            border_color=theme.color("border"),
        )
        icon_box.pack(pady=(0, 14))
        icon_box.pack_propagate(False)

        icon_img = theme.icon(icon_name, "dark", 24)
        ctk.CTkLabel(icon_box, text="", image=icon_img).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner,
            text=title,
            font=theme.font(17, "bold"),
            text_color=theme.color("text_primary"),
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            inner,
            text=description,
            font=theme.font(13, "normal"),
            text_color=theme.color("text_secondary"),
            wraplength=460,
            justify="center",
        ).pack(pady=(0, 18))

        if on_action is not None:
            PrimaryButton(
                inner,
                theme,
                text=button_text,
                icon_name="upload",
                command=on_action,
                width=200,
                height=40,
            ).pack()


class LoadingOverlay(ctk.CTkFrame):
    """Non-intrusive monochrome loading overlay during background file processing."""

    def __init__(self, master: Any, theme: ThemeManager) -> None:
        super().__init__(
            master,
            fg_color=theme.color("bg_app"),
            corner_radius=0,
        )
        self._card = Card(self, theme, subtle=False, corner_radius=12)
        self._card.place(relx=0.5, rely=0.5, anchor="center")

        self._title = ctk.CTkLabel(
            self._card,
            text="Processing your data...",
            font=theme.font(15, "bold"),
            text_color=theme.color("text_primary"),
        )
        self._title.pack(padx=36, pady=(24, 6))

        self._detail = ctk.CTkLabel(
            self._card,
            text="Please wait a moment.",
            font=theme.font(12, "normal"),
            text_color=theme.color("text_secondary"),
        )
        self._detail.pack(padx=36, pady=(0, 14))

        self._bar = ctk.CTkProgressBar(
            self._card,
            width=260,
            height=6,
            mode="indeterminate",
            fg_color=theme.color("bg_hover"),
            progress_color=theme.color("btn_primary_bg"),
        )
        self._bar.pack(padx=36, pady=(0, 24))

    def show(self, title: str = "Processing your data...", detail: str = "Please wait a moment.") -> None:
        self._title.configure(text=title)
        self._detail.configure(text=detail)
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.lift()
        self._bar.start()

    def hide(self) -> None:
        self._bar.stop()
        self.place_forget()


class BaseModalDialog(ctk.CTkToplevel):
    """Base strictly black-and-white modal dialog centered on the parent window.

    Automatically expands to fit all content at any Windows DPI scaling so
    action buttons are never clipped off the bottom, and applies MiniSort's
    monochrome icon to the title bar.
    """

    def __init__(
        self,
        parent: tk.Misc,
        theme: ThemeManager,
        title: str,
        width: int = 440,
        height: int = 230,
    ) -> None:
        super().__init__(parent)
        self._parent_window = parent
        self._theme = theme
        self._base_width = width
        self._base_height = height
        self.title(title)
        self.configure(fg_color=theme.color("bg_app"))
        self.resizable(False, False)
        self.transient(parent)
        self._apply_geometry(width, height)
        self._apply_monochrome_icon()
        self.grab_set()
        self.focus_set()

    def _apply_monochrome_icon(self) -> None:
        ico_path = get_asset_path("images", "minisort.ico")
        if not ico_path.exists():
            return

        def _set_ico() -> None:
            try:
                if self.winfo_exists():
                    self.iconbitmap(str(ico_path))
            except Exception:
                pass

        _set_ico()
        # Override CustomTkinter's delayed default CTkToplevel icon (set at 200ms)
        self.after(250, _set_ico)

    def _apply_geometry(self, logical_w: int, logical_h: int) -> None:
        self.update_idletasks()
        scaling = 1.0
        try:
            scaling = float(self._get_window_scaling())
        except Exception:
            scaling = 1.0

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        phys_w = int(logical_w * scaling)
        phys_h = int(logical_h * scaling)
        try:
            px = self._parent_window.winfo_rootx() + (self._parent_window.winfo_width() - phys_w) // 2
            py = self._parent_window.winfo_rooty() + (self._parent_window.winfo_height() - phys_h) // 2
        except Exception:
            px, py = (screen_w - phys_w) // 2, (screen_h - phys_h) // 2

        px = max(20, min(px, max(20, screen_w - phys_w - 20)))
        py = max(20, min(py, max(20, screen_h - phys_h - 40)))
        self.geometry(f"{logical_w}x{logical_h}+{px}+{py}")

    def finalize_layout(self) -> None:
        """Ensure the dialog is tall/wide enough for all packed widgets at current DPI."""
        self.update_idletasks()
        scaling = 1.0
        try:
            scaling = float(self._get_window_scaling())
        except Exception:
            scaling = 1.0

        req_logical_w = int((self.winfo_reqwidth() / max(scaling, 0.5)) + 0.99)
        req_logical_h = int((self.winfo_reqheight() / max(scaling, 0.5)) + 0.99)
        max_logical_h = int((self.winfo_screenheight() - 90) / max(scaling, 0.5))

        final_w = max(self._base_width, req_logical_w)
        final_h = min(max_logical_h, max(self._base_height, req_logical_h + 8))
        self._apply_geometry(final_w, final_h)


def show_alert_dialog(
    parent: tk.Misc,
    theme: ThemeManager,
    title: str,
    message: str,
    button_text: str = "OK",
) -> None:
    """Display a monochrome modal notification dialog."""
    dlg = BaseModalDialog(parent, theme, title=title, width=440, height=220)

    footer = ctk.CTkFrame(dlg, fg_color="transparent")
    footer.pack(side="bottom", fill="x", padx=24, pady=(0, 18))
    PrimaryButton(footer, theme, text=button_text, command=dlg.destroy, width=100, height=36).pack(side="right")

    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=(20, 12))

    ctk.CTkLabel(
        body,
        text=title,
        font=theme.font(16, "bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).pack(anchor="w", pady=(0, 8))

    ctk.CTkLabel(
        body,
        text=message,
        font=theme.font(13, "normal"),
        text_color=theme.color("text_secondary"),
        wraplength=390,
        justify="left",
        anchor="w",
    ).pack(anchor="w", fill="x", expand=True)

    dlg.finalize_layout()
    dlg.bind("<Return>", lambda _e: dlg.destroy())
    dlg.bind("<Escape>", lambda _e: dlg.destroy())
    parent.wait_window(dlg)


def show_confirm_dialog(
    parent: tk.Misc,
    theme: ThemeManager,
    title: str,
    message: str,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
) -> bool:
    """Display a monochrome modal confirmation dialog and return True if confirmed."""
    result = {"confirmed": False}
    dlg = BaseModalDialog(parent, theme, title=title, width=460, height=235)

    def _confirm() -> None:
        result["confirmed"] = True
        dlg.destroy()

    footer = ctk.CTkFrame(dlg, fg_color="transparent")
    footer.pack(side="bottom", fill="x", padx=24, pady=(0, 18))
    PrimaryButton(footer, theme, text=confirm_text, command=_confirm, width=130, height=36).pack(side="right")
    SecondaryButton(footer, theme, text=cancel_text, command=dlg.destroy, width=100, height=36).pack(
        side="right", padx=(0, 10)
    )

    body = ctk.CTkFrame(dlg, fg_color="transparent")
    body.pack(fill="both", expand=True, padx=24, pady=(20, 12))

    ctk.CTkLabel(
        body,
        text=title,
        font=theme.font(16, "bold"),
        text_color=theme.color("text_primary"),
        anchor="w",
    ).pack(anchor="w", pady=(0, 8))

    ctk.CTkLabel(
        body,
        text=message,
        font=theme.font(13, "normal"),
        text_color=theme.color("text_secondary"),
        wraplength=410,
        justify="left",
        anchor="w",
    ).pack(anchor="w", fill="x", expand=True)

    dlg.finalize_layout()
    dlg.bind("<Escape>", lambda _e: dlg.destroy())
    parent.wait_window(dlg)
    return result["confirmed"]


class DataTable(Card):
    """Paginated spreadsheet-style table preview built on monochrome ttk.Treeview.

    Never renders unbounded rows at once; displays one configurable page at a time
    while preserving complete access to the full underlying DataFrame.
    """

    def __init__(
        self,
        master: Any,
        theme: ThemeManager,
        page_size: int = 100,
        title: str = "Data Preview",
        compact: bool = False,
    ) -> None:
        super().__init__(master, theme, subtle=False, corner_radius=10)
        self._theme = theme
        self._page_size = max(10, int(page_size))
        self._df: pd.DataFrame | None = None
        self._current_page = 1
        self._total_pages = 1
        self._compact = compact
        self._title = title

        theme.configure_treeview_style()

        # Header strip
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(10, 6))

        self._title_lbl = ctk.CTkLabel(
            header,
            text=title,
            font=theme.font(14 if not compact else 13, "bold"),
            text_color=theme.color("text_primary"),
        )
        self._title_lbl.pack(side="left")

        self._count_lbl = ctk.CTkLabel(
            header,
            text="",
            font=theme.font(12, "normal"),
            text_color=theme.color("text_muted"),
        )
        self._count_lbl.pack(side="right")

        # Notice bar shown when dataset exceeds a single preview page
        self._notice_bar = ctk.CTkFrame(
            self,
            fg_color=theme.color("bg_subtle"),
            corner_radius=6,
            border_width=1,
            border_color=theme.color("border"),
        )
        self._notice_lbl = ctk.CTkLabel(
            self._notice_bar,
            text="",
            font=theme.font(11, "normal"),
            text_color=theme.color("text_secondary"),
            anchor="w",
        )
        self._notice_lbl.pack(fill="x", padx=10, pady=5)

        # Treeview container
        tree_wrap = ctk.CTkFrame(
            self,
            fg_color=theme.color("bg_surface"),
            border_width=1,
            border_color=theme.color("border"),
            corner_radius=6,
        )
        tree_wrap.pack(fill="both", expand=True, padx=14, pady=(2, 8))
        tree_wrap.grid_rowconfigure(0, weight=1)
        tree_wrap.grid_columnconfigure(0, weight=1)

        self._tree = ttk.Treeview(
            tree_wrap,
            style="MiniSort.Treeview",
            show="headings",
            selectmode="browse",
        )
        self._tree.grid(row=0, column=0, sticky="nsew", padx=(1, 0), pady=(1, 0))

        self._vscroll = ctk.CTkScrollbar(tree_wrap, orientation="vertical", command=self._tree.yview)
        self._vscroll.grid(row=0, column=1, sticky="ns", padx=2, pady=2)

        self._hscroll = ctk.CTkScrollbar(tree_wrap, orientation="horizontal", command=self._tree.xview)
        self._hscroll.grid(row=1, column=0, sticky="ew", padx=2, pady=2)

        self._tree.configure(yscrollcommand=self._vscroll.set, xscrollcommand=self._hscroll.set)

        self._tree.tag_configure("even", background=theme.color("table_row_even"))
        self._tree.tag_configure("odd", background=theme.color("table_row_odd"))

        # Pagination footer
        self._pager = ctk.CTkFrame(self, fg_color="transparent")
        self._pager.pack(fill="x", padx=14, pady=(0, 10))

        self._range_lbl = ctk.CTkLabel(
            self._pager,
            text="No data loaded",
            font=theme.font(12, "normal"),
            text_color=theme.color("text_muted"),
        )
        self._range_lbl.pack(side="left")

        nav = ctk.CTkFrame(self._pager, fg_color="transparent")
        nav.pack(side="right")

        self._btn_first = SecondaryButton(nav, theme, text="«", command=self._go_first, width=32, height=28)
        self._btn_prev = SecondaryButton(nav, theme, text="Prev", command=self._go_prev, width=54, height=28)
        self._page_lbl = ctk.CTkLabel(
            nav,
            text="Page 1 / 1",
            font=theme.font(12, "normal"),
            text_color=theme.color("text_primary"),
            width=96,
        )
        self._btn_next = SecondaryButton(nav, theme, text="Next", command=self._go_next, width=54, height=28)
        self._btn_last = SecondaryButton(nav, theme, text="»", command=self._go_last, width=32, height=28)

        self._btn_first.pack(side="left", padx=2)
        self._btn_prev.pack(side="left", padx=2)
        self._page_lbl.pack(side="left", padx=6)
        self._btn_next.pack(side="left", padx=2)
        self._btn_last.pack(side="left", padx=2)

    def set_title(self, title: str) -> None:
        self._title = title
        self._title_lbl.configure(text=title)

    def set_page_size(self, page_size: int) -> None:
        self._page_size = max(10, int(page_size))
        if self._df is not None:
            self._current_page = 1
            self._render_page()

    def set_dataframe(self, df: pd.DataFrame | None, reset_page: bool = True) -> None:
        self._df = df
        if reset_page:
            self._current_page = 1
        self._rebuild_columns()
        self._render_page()

    def _rebuild_columns(self) -> None:
        self._tree.delete(*self._tree.get_children())
        if self._df is None or len(self._df.columns) == 0:
            self._tree["columns"] = ()
            return

        col_ids = ["#row"] + [f"c_{i}" for i in range(len(self._df.columns))]
        self._tree["columns"] = col_ids

        self._tree.heading("#row", text="#", anchor="center")
        self._tree.column("#row", width=56, minwidth=46, stretch=False, anchor="center")

        sample_df = self._df.head(40)
        for i, col_name in enumerate(self._df.columns):
            cid = f"c_{i}"
            header_text = str(col_name)
            self._tree.heading(cid, text=header_text, anchor="w")

            # Compute readable column width from header + sample cells
            max_chars = len(header_text)
            try:
                for val in sample_df.iloc[:, i].tolist():
                    if pd.notna(val):
                        max_chars = max(max_chars, min(len(str(val)), 36))
            except Exception:
                pass
            px_width = max(110, min(280, max_chars * 9 + 34))
            self._tree.column(cid, width=px_width, minwidth=85, stretch=False, anchor="w")

    def _render_page(self) -> None:
        self._tree.delete(*self._tree.get_children())

        if self._df is None:
            self._count_lbl.configure(text="")
            self._range_lbl.configure(text="No dataset loaded")
            self._page_lbl.configure(text="Page 0 / 0")
            self._notice_bar.pack_forget()
            self._set_nav_state(False, False)
            return

        total_rows = len(self._df)
        total_cols = len(self._df.columns)
        self._count_lbl.configure(
            text=f"{format_int(total_rows)} rows  •  {format_int(total_cols)} columns"
        )

        if total_rows == 0:
            self._range_lbl.configure(text="0 rows to display")
            self._page_lbl.configure(text="Page 1 / 1")
            self._notice_bar.pack_forget()
            self._set_nav_state(False, False)
            return

        self._total_pages = max(1, math.ceil(total_rows / self._page_size))
        self._current_page = max(1, min(self._current_page, self._total_pages))

        start_idx = (self._current_page - 1) * self._page_size
        end_idx = min(start_idx + self._page_size, total_rows)

        # Show helpful banner whenever dataset spans multiple preview pages
        if total_rows > self._page_size and not self._compact:
            self._notice_lbl.configure(
                text=(
                    f"Previewing {format_int(self._page_size)} rows per page for fast performance. "
                    f"All {format_int(total_rows)} rows remain intact for sorting, filtering, cleaning and exporting."
                )
            )
            if not self._notice_bar.winfo_ismapped():
                self._notice_bar.pack(fill="x", padx=14, pady=(0, 6), before=self._pager)
        else:
            self._notice_bar.pack_forget()

        page_slice = self._df.iloc[start_idx:end_idx]
        for offset, row_tuple in enumerate(page_slice.itertuples(index=False, name=None)):
            row_num = start_idx + offset + 1
            formatted_cells = [str(row_num)]
            for val in row_tuple:
                formatted_cells.append(self._format_cell(val))
            tag = "even" if offset % 2 == 0 else "odd"
            self._tree.insert("", "end", values=formatted_cells, tags=(tag,))

        self._range_lbl.configure(
            text=f"Showing rows {format_int(start_idx + 1)}–{format_int(end_idx)} of {format_int(total_rows)}"
        )
        self._page_lbl.configure(text=f"Page {self._current_page} / {self._total_pages}")
        self._set_nav_state(self._current_page > 1, self._current_page < self._total_pages)

    @staticmethod
    def _format_cell(val: Any) -> str:
        if val is None:
            return MISSING_DISPLAY_TEXT
        try:
            if pd.isna(val):
                return MISSING_DISPLAY_TEXT
        except (TypeError, ValueError):
            pass
        if isinstance(val, pd.Timestamp):
            if val.hour == 0 and val.minute == 0 and val.second == 0:
                return val.strftime("%Y-%m-%d")
            return val.strftime("%Y-%m-%d %H:%M")
        text = str(val)
        if text == "":
            return MISSING_DISPLAY_TEXT
        if len(text) > 120:
            return text[:119] + "…"
        return text

    def _set_nav_state(self, can_prev: bool, can_next: bool) -> None:
        prev_state = "normal" if can_prev else "disabled"
        next_state = "normal" if can_next else "disabled"
        self._btn_first.configure(state=prev_state)
        self._btn_prev.configure(state=prev_state)
        self._btn_next.configure(state=next_state)
        self._btn_last.configure(state=next_state)

    def _go_first(self) -> None:
        self._current_page = 1
        self._render_page()

    def _go_prev(self) -> None:
        if self._current_page > 1:
            self._current_page -= 1
            self._render_page()

    def _go_next(self) -> None:
        if self._current_page < self._total_pages:
            self._current_page += 1
            self._render_page()

    def _go_last(self) -> None:
        self._current_page = self._total_pages
        self._render_page()

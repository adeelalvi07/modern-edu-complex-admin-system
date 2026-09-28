"""
Responsive Styled Data Table Component for CustomTkinter.
Uses themed ttk.Treeview embedded within a CTkFrame with scrollbars.
"""
import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from config.theme_config import ThemeConfig
from typing import List, Tuple, Optional, Callable, Dict, Any

class DataTable(ctk.CTkFrame):
    def __init__(
        self,
        master,
        columns: List[Tuple[str, str, int]], # (col_id, col_text, width)
        on_select: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_double_click: Optional[Callable[[Dict[str, Any]], None]] = None,
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=10,
            fg_color=ThemeConfig.BG_CARD,
            border_width=1,
            border_color=ThemeConfig.BORDER,
            **kwargs
        )
        self.columns_def = columns
        self.on_select = on_select
        self.on_double_click = on_double_click
        self.col_ids = [c[0] for c in columns]

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._setup_style()
        self._create_tree()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_header = "#1E293B" if is_dark else "#F1F5F9"
        fg_header = "#F8FAFC" if is_dark else "#0F172A"
        bg_row = "#0F172A" if is_dark else "#FFFFFF"
        fg_row = "#F8FAFC" if is_dark else "#0F172A"
        bg_alt = "#162032" if is_dark else "#F8FAFC"
        bg_selected = "#2563EB"

        style.configure(
            "Custom.Treeview.Heading",
            background=bg_header,
            foreground=fg_header,
            font=("Segoe UI", 10, "bold"),
            borderwidth=0,
            relief="flat",
            padding=8
        )
        style.map(
            "Custom.Treeview.Heading",
            background=[("active", "#334155" if is_dark else "#E2E8F0")]
        )

        style.configure(
            "Custom.Treeview",
            background=bg_row,
            foreground=fg_row,
            fieldbackground=bg_row,
            font=("Segoe UI", 10),
            rowheight=32,
            borderwidth=0,
            relief="flat"
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", bg_selected)],
            foreground=[("selected", "#FFFFFF")]
        )

    def _create_tree(self):
        self.tree = ttk.Treeview(
            self,
            columns=self.col_ids,
            show="headings",
            style="Custom.Treeview",
            selectmode="browse"
        )

        for col_id, text, width in self.columns_def:
            self.tree.heading(col_id, text=text, anchor="w")
            self.tree.column(col_id, width=width, minwidth=60, anchor="w")

        # Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(2, 0), pady=2)
        self.scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 2), pady=2)

        self.tree.bind("<<TreeviewSelect>>", self._handle_select)
        self.tree.bind("<Double-1>", self._handle_double_click)

    def populate(self, rows_data: List[Dict[str, Any]]):
        """Clears and re-populates table rows with semantic status colors."""
        self.clear()
        is_dark = ctk.get_appearance_mode() == "Dark"
        self.raw_data = rows_data

        # Configure base striping tags
        bg_row = "#0F172A" if is_dark else "#FFFFFF"
        bg_alt = "#162032" if is_dark else "#F8FAFC"
        fg_default = "#F8FAFC" if is_dark else "#0F172A"

        self.tree.tag_configure("even", background=bg_row, foreground=fg_default)
        self.tree.tag_configure("odd", background=bg_alt, foreground=fg_default)

        # 🟢 Present: Vivid High-Contrast Green with soft tinted background
        self.tree.tag_configure(
            "status_present",
            foreground="#22C55E" if is_dark else "#15803D",
            background="#0A241A" if is_dark else "#ECFDF5",
            font=("Segoe UI", 10, "bold")
        )

        # 🔴 Absent: Vivid High-Contrast Red with soft tinted background
        self.tree.tag_configure(
            "status_absent",
            foreground="#EF4444" if is_dark else "#DC2626",
            background="#2A0F12" if is_dark else "#FEF2F2",
            font=("Segoe UI", 10, "bold")
        )

        # ⏱ Late: Warm Gold/Amber with soft tinted background
        self.tree.tag_configure(
            "status_late",
            foreground="#F59E0B" if is_dark else "#B45309",
            background="#261A0A" if is_dark else "#FFFBEB",
            font=("Segoe UI", 10, "bold")
        )

        # ℹ Excused: Soft Sky Blue with soft tinted background
        self.tree.tag_configure(
            "status_excused",
            foreground="#38BDF8" if is_dark else "#0284C7",
            background="#0C202F" if is_dark else "#F0F9FF",
            font=("Segoe UI", 10, "bold")
        )

        # Financial Status Tags
        self.tree.tag_configure(
            "status_paid",
            foreground="#22C55E" if is_dark else "#15803D",
            background="#0A241A" if is_dark else "#ECFDF5"
        )
        self.tree.tag_configure(
            "status_unpaid",
            foreground="#EF4444" if is_dark else "#DC2626",
            background="#2A0F12" if is_dark else "#FEF2F2"
        )
        self.tree.tag_configure(
            "status_partial",
            foreground="#F59E0B" if is_dark else "#B45309",
            background="#261A0A" if is_dark else "#FFFBEB"
        )

        for i, row in enumerate(rows_data):
            values = [row.get(cid, "") for cid in self.col_ids]

            # Semantic tag matching
            status_text = str(row.get("raw_status") or row.get("status") or row.get("alert") or "").strip().lower()
            if "present" in status_text:
                tag = "status_present"
            elif "absent" in status_text or "deficit" in status_text:
                tag = "status_absent"
            elif "late" in status_text:
                tag = "status_late"
            elif "excused" in status_text:
                tag = "status_excused"
            elif status_text == "paid":
                tag = "status_paid"
            elif status_text == "unpaid":
                tag = "status_unpaid"
            elif "partial" in status_text:
                tag = "status_partial"
            else:
                tag = "even" if i % 2 == 0 else "odd"

            self.tree.insert("", "end", iid=str(i), values=values, tags=(tag,))

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.raw_data = []

    def get_selected_item(self) -> Optional[Dict[str, Any]]:
        selected = self.tree.selection()
        if not selected:
            return None
        idx = int(selected[0])
        if 0 <= idx < len(self.raw_data):
            return self.raw_data[idx]
        return None

    def _handle_select(self, event):
        if self.on_select:
            item = self.get_selected_item()
            if item:
                self.on_select(item)

    def _handle_double_click(self, event):
        if self.on_double_click:
            item = self.get_selected_item()
            if item:
                self.on_double_click(item)

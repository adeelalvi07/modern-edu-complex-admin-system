"""
Fee & Financial Management Module View.
Features:
- Live Invoice Directory & Fast Payment Processing POS
- Batch Monthly Voucher / Challan Generator
- Official 3-Part PDF Challan Printing
- Defaulters Register with One-Click Excel Export
- Centered, Straight, Low-Opacity Campus Watermark Background
"""
import os
import customtkinter as ctk
from datetime import date
from config.theme_config import ThemeConfig
from src.views.components.data_table import DataTable
from src.views.components.watermark import WatermarkManager
from src.controllers.fee_controller import FeeController
from src.repositories.fee_repository import FeeRepository
from src.repositories.student_repository import StudentRepository
from src.services.pdf_generator import PDFGenerator
from src.services.excel_service import ExcelService

class FeeView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=ThemeConfig.BG_MAIN, **kwargs)
        self.controller = FeeController()
        self.repo = FeeRepository()
        self.student_repo = StudentRepository()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Apply centered, straight watermark in background
        WatermarkManager.apply(self, width=820, height=560)

        self._build_tabs()

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=ThemeConfig.BG_MAIN,
            segmented_button_selected_color=ThemeConfig.SECONDARY[1],
            segmented_button_selected_hover_color=ThemeConfig.SECONDARY_HOVER[1]
        )
        self.tabview.grid(row=0, column=0, padx=20, pady=16, sticky="nsew")

        self.tab_invoices = self.tabview.add("💳 Invoices & Payments")
        self.tab_generate = self.tabview.add("⚡ Generate Monthly Vouchers")
        self.tab_defaulters = self.tabview.add("⚠️ Defaulters Register")
        self.tab_structures = self.tabview.add("⚙️ Fee Structures")

        self._init_invoices_tab()
        self._init_generate_tab()
        self._init_defaulters_tab()
        self._init_structures_tab()

    # -------------------------------------------------------------------------
    # TAB 1: INVOICES & PAYMENTS POS
    # -------------------------------------------------------------------------
    def _init_invoices_tab(self):
        tab = self.tab_invoices
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        bar.grid(row=0, column=0, padx=4, pady=(4, 12), sticky="ew")

        self.classes_cache = self.student_repo.get_all_classes()
        class_options = ["All Classes"] + [c["name"] for c in self.classes_cache]

        self.inv_search = ctk.CTkEntry(
            bar,
            placeholder_text="🔍 Search invoice #, student name, or admission #...",
            width=260,
            height=36
        )
        self.inv_search.pack(side="left", padx=(12, 6), pady=10)
        self.inv_search.bind("<KeyRelease>", lambda e: self._refresh_invoices())
        self.inv_search.bind("<Return>", lambda e: self._refresh_invoices())

        ctk.CTkLabel(bar, text="Class:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(6, 4), pady=10)
        self.inv_class_filter = ctk.CTkComboBox(
            bar,
            values=class_options,
            command=lambda v: self._refresh_invoices(),
            width=120,
            height=36
        )
        self.inv_class_filter.set("All Classes")
        self.inv_class_filter.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(bar, text="Status:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(6, 4), pady=10)
        self.inv_status_filter = ctk.CTkComboBox(
            bar,
            values=["All", "Unpaid", "Partially Paid", "Paid"],
            command=lambda v: self._refresh_invoices(),
            width=120,
            height=36
        )
        self.inv_status_filter.set("All")
        self.inv_status_filter.pack(side="left", padx=4, pady=10)

        pay_btn = ctk.CTkButton(
            bar,
            text="💵 Record Payment",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.SUCCESS,
            height=36,
            command=self._open_payment_dialog
        )
        pay_btn.pack(side="right", padx=12, pady=10)

        print_btn = ctk.CTkButton(
            bar,
            text="🖨️ Print 3-Part Challan PDF",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.PRIMARY,
            height=36,
            command=self._print_selected_challan
        )
        print_btn.pack(side="right", padx=6, pady=10)

        cols = [
            ("invoice_number", "Invoice #", 130),
            ("admission_number", "Adm #", 100),
            ("student_name", "Student Name", 160),
            ("class_name", "Class", 90),
            ("billing_cycle", "Billing Month", 100),
            ("net_payable", "Net Payable", 100),
            ("paid_amount", "Paid", 90),
            ("balance_amount", "Balance", 100),
            ("status", "Status", 100)
        ]
        self.inv_table = DataTable(tab, columns=cols)
        self.inv_table.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="nsew")

        self.inv_feedback = ctk.CTkLabel(tab, text="", font=ThemeConfig.get_font(11, "bold"))
        self.inv_feedback.grid(row=2, column=0, sticky="w", padx=10, pady=4)

        self._refresh_invoices()

    def _refresh_invoices(self):
        term = self.inv_search.get().strip()
        st = self.inv_status_filter.get()
        selected_class = self.inv_class_filter.get() if hasattr(self, "inv_class_filter") else "All Classes"
        class_id = None
        if selected_class and selected_class != "All Classes":
            c_obj = next((c for c in self.classes_cache if c["name"] == selected_class), None)
            if c_obj:
                class_id = c_obj["id"]

        invoices = self.repo.search_invoices(class_id=class_id, status=st, search_term=term)
        formatted = []
        for inv in invoices:
            formatted.append({
                "id": inv["id"],
                "invoice_number": inv["invoice_number"],
                "admission_number": inv.get("admission_number", "-"),
                "student_name": f"{inv.get('first_name', '')} {inv.get('last_name', '')}",
                "class_name": f"{inv.get('class_name', '')} - {inv.get('section_name', '')}",
                "billing_cycle": f"{inv.get('billing_month')}/{inv.get('billing_year')}",
                "net_payable": f"PKR {float(inv.get('net_payable', 0)):,.0f}",
                "paid_amount": f"PKR {float(inv.get('paid_amount', 0)):,.0f}",
                "balance_amount": f"PKR {float(inv.get('balance_amount', 0)):,.0f}",
                "status": inv.get("status", "Unpaid"),
                "raw_balance": float(inv.get("balance_amount", 0)),
                "raw_invoice": inv
            })
        self.inv_table.populate(formatted)
        cls_info = f" ({selected_class})" if selected_class != "All Classes" else ""
        self.inv_feedback.configure(text=f"Total: {len(formatted)} Invoices{cls_info}", text_color=ThemeConfig.TEXT_MUTED)

    def _open_payment_dialog(self):
        item = self.inv_table.get_selected_item()
        if not item:
            self.inv_feedback.configure(text="Please select an invoice from the table first.", text_color=ThemeConfig.WARNING[1])
            return

        bal = item.get("raw_balance", 0.0)
        if bal <= 0:
            self.inv_feedback.configure(text="This invoice is already fully paid.", text_color=ThemeConfig.INFO[1])
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Receive Fee Payment")
        dialog.geometry("380x380")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"Record Payment: {item['invoice_number']}", font=ThemeConfig.get_font(13, "bold")).pack(pady=(16, 4))
        ctk.CTkLabel(dialog, text=f"Student: {item['student_name']} | Balance: PKR {bal:,.0f}", font=ThemeConfig.get_font(11), text_color=ThemeConfig.TEXT_MUTED).pack(pady=(0, 10))

        ctk.CTkLabel(dialog, text="Payment Date (YYYY-MM-DD):", font=ThemeConfig.get_font(11, "bold")).pack(anchor="w", padx=30, pady=(4, 2))
        pay_date_entry = ctk.CTkEntry(dialog, font=ThemeConfig.get_font(12))
        pay_date_entry.insert(0, date.today().isoformat())
        pay_date_entry.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkLabel(dialog, text="Amount Received (PKR):", font=ThemeConfig.get_font(11, "bold")).pack(anchor="w", padx=30, pady=(4, 2))
        amt_entry = ctk.CTkEntry(dialog, font=ThemeConfig.get_font(12))
        amt_entry.insert(0, str(int(bal)))
        amt_entry.pack(fill="x", padx=30, pady=(0, 10))

        ctk.CTkLabel(dialog, text="Payment Mode:", font=ThemeConfig.get_font(11, "bold")).pack(anchor="w", padx=30, pady=(4, 2))
        mode_cb = ctk.CTkComboBox(dialog, values=["Cash", "Bank Slip", "Online Transfer"])
        mode_cb.set("Cash")
        mode_cb.pack(fill="x", padx=30, pady=(0, 16))

        def confirm_pay():
            try:
                amt = float(amt_entry.get().strip())
            except ValueError:
                return

            pay_dt = pay_date_entry.get().strip() or date.today().isoformat()
            success, msg, rec = self.controller.record_fee_payment(
                invoice_id=item["id"],
                amount=amt,
                payment_mode=mode_cb.get(),
                ref_number="",
                user_id=1,
                remarks="Office counter payment",
                payment_date=pay_dt
            )
            if success:
                self.inv_feedback.configure(text=f"✔ {msg}", text_color=ThemeConfig.SUCCESS[1])
                dialog.destroy()
                self._refresh_invoices()

        ctk.CTkButton(dialog, text="✔ Confirm Payment", font=ThemeConfig.get_font(12, "bold"), fg_color=ThemeConfig.SECONDARY, height=38, command=confirm_pay).pack(fill="x", padx=30)

    def _print_selected_challan(self):
        item = self.inv_table.get_selected_item()
        if not item:
            self.inv_feedback.configure(text="Select an invoice from the table to print.", text_color=ThemeConfig.WARNING[1])
            return

        inv_raw = item["raw_invoice"]
        items = self.repo.db.fetch_all(
            """SELECT fii.*, fh.name as fee_head_name 
               FROM fee_invoice_items fii 
               JOIN fee_heads fh ON fii.fee_head_id = fh.id
               WHERE fii.invoice_id = :id""",
            {"id": item["id"]}
        )
        if not items:
            items = [{"fee_head_name": "Tuition Fee", "amount": float(inv_raw.get("net_payable", 0))}]

        pdf_path = PDFGenerator.generate_fee_voucher(inv_raw, items)
        self.inv_feedback.configure(text=f"✔ PDF Challan Generated: {os.path.basename(pdf_path)}", text_color=ThemeConfig.SUCCESS[1])
        try:
            os.startfile(pdf_path)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # TAB 2: GENERATE MONTHLY VOUCHERS
    # -------------------------------------------------------------------------
    def _init_generate_tab(self):
        tab = self.tab_generate
        tab.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=12, border_width=1, border_color=ThemeConfig.BORDER)
        card.pack(fill="x", padx=10, pady=16)

        ctk.CTkLabel(card, text="BATCH MONTHLY FEE VOUCHER GENERATOR", font=ThemeConfig.get_font(13, "bold"), text_color=ThemeConfig.PRIMARY[1]).pack(anchor="w", padx=20, pady=(16, 6))
        ctk.CTkLabel(card, text="Generates fee challans for all enrolled students in the selected class based on configured fee heads.", font=ThemeConfig.get_font(11), text_color=ThemeConfig.TEXT_MUTED).pack(anchor="w", padx=20, pady=(0, 16))

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 16))
        grid.grid_columnconfigure((1, 3), weight=1)

        # Class
        ctk.CTkLabel(grid, text="Select Class:", font=ThemeConfig.get_font(11, "bold")).grid(row=0, column=0, sticky="w", pady=8)
        classes = self.student_repo.get_all_classes()
        c_names = [c["name"] for c in classes]
        self.gen_class = ctk.CTkComboBox(grid, values=c_names)
        if c_names:
            self.gen_class.set(c_names[0])
        self.gen_class.grid(row=0, column=1, sticky="ew", padx=(10, 24), pady=8)

        # Month
        ctk.CTkLabel(grid, text="Billing Month:", font=ThemeConfig.get_font(11, "bold")).grid(row=0, column=2, sticky="w", pady=8)
        self.gen_month = ctk.CTkComboBox(grid, values=[str(m) for m in range(1, 13)])
        self.gen_month.set(str(date.today().month))
        self.gen_month.grid(row=0, column=3, sticky="ew", padx=(10, 0), pady=8)

        # Year
        ctk.CTkLabel(grid, text="Billing Year:", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=0, sticky="w", pady=8)
        self.gen_year = ctk.CTkComboBox(grid, values=["2025", "2026", "2027"])
        self.gen_year.set(str(date.today().year))
        self.gen_year.grid(row=1, column=1, sticky="ew", padx=(10, 24), pady=8)

        # Due Date
        ctk.CTkLabel(grid, text="Due Date:", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=2, sticky="w", pady=8)
        self.gen_due = ctk.CTkEntry(grid)
        self.gen_due.insert(0, f"{date.today().year}-{date.today().month:02d}-10")
        self.gen_due.grid(row=1, column=3, sticky="ew", padx=(10, 0), pady=8)

        # Generate Button & Status
        btn_bar = ctk.CTkFrame(card, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 20))

        self.gen_status_lbl = ctk.CTkLabel(btn_bar, text="", font=ThemeConfig.get_font(12, "bold"))
        self.gen_status_lbl.pack(side="left")

        do_gen_btn = ctk.CTkButton(
            btn_bar,
            text="⚡ Generate Class Vouchers",
            font=ThemeConfig.get_font(12, "bold"),
            fg_color=ThemeConfig.PRIMARY,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            height=40,
            command=self._do_generate_vouchers
        )
        do_gen_btn.pack(side="right")

    def _do_generate_vouchers(self):
        c_name = self.gen_class.get()
        classes = self.student_repo.get_all_classes()
        c_obj = next((c for c in classes if c["name"] == c_name), None)
        if not c_obj:
            return

        session = self.student_repo.get_current_session()
        session_id = session["id"] if session else 1

        structures = self.repo.get_fee_structure(c_obj["id"], session_id)
        if not structures:
            self.repo.set_fee_structure(session_id, c_obj["id"], fee_head_id=1, amount=3500.0)

        success, msg, count = self.controller.generate_monthly_bills(
            class_id=c_obj["id"],
            session_id=session_id,
            month=int(self.gen_month.get()),
            year=int(self.gen_year.get()),
            due_date_str=self.gen_due.get().strip()
        )
        if success:
            self.gen_status_lbl.configure(text=f"✔ {msg}", text_color=ThemeConfig.SUCCESS[1])
            self._refresh_invoices()
        else:
            self.gen_status_lbl.configure(text=f"✖ {msg}", text_color=ThemeConfig.DANGER[1])

    # -------------------------------------------------------------------------
    # TAB 3: DEFAULTERS REGISTER
    # -------------------------------------------------------------------------
    def _init_defaulters_tab(self):
        tab = self.tab_defaulters
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        bar.grid(row=0, column=0, padx=4, pady=(4, 12), sticky="ew")

        # Search & Class Filters
        self.def_search = ctk.CTkEntry(
            bar,
            placeholder_text="🔍 Search student or adm #...",
            width=210,
            height=36
        )
        self.def_search.pack(side="left", padx=(12, 6), pady=8)
        self.def_search.bind("<KeyRelease>", lambda e: self._refresh_defaulters())
        self.def_search.bind("<Return>", lambda e: self._refresh_defaulters())

        ctk.CTkLabel(bar, text="Class:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(6, 4), pady=8)
        class_options = ["All Classes"] + [c["name"] for c in self.classes_cache]
        self.def_class_filter = ctk.CTkComboBox(
            bar,
            values=class_options,
            command=lambda v: self._refresh_defaulters(),
            width=120,
            height=36
        )
        self.def_class_filter.set("All Classes")
        self.def_class_filter.pack(side="left", padx=4, pady=8)

        export_btn = ctk.CTkButton(
            bar,
            text="📊 Export to Excel (.xlsx)",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.SUCCESS,
            height=36,
            command=self._export_defaulters_excel
        )
        export_btn.pack(side="right", padx=12, pady=8)

        self.defaulters_status = ctk.CTkLabel(bar, text="", font=ThemeConfig.get_font(11, "bold"))
        self.defaulters_status.pack(side="right", padx=12)

        cols = [
            ("invoice_number", "Invoice #", 120),
            ("admission_number", "Adm #", 100),
            ("student_name", "Student Name", 180),
            ("class_name", "Class", 100),
            ("father_phone", "Parent Contact", 120),
            ("due_date", "Due Date", 100),
            ("balance_amount", "Overdue Balance", 120)
        ]
        self.def_table = DataTable(tab, columns=cols)
        self.def_table.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="nsew")

        self.current_defaulters = []
        self._refresh_defaulters()

    def _refresh_defaulters(self):
        term = self.def_search.get().strip().lower() if hasattr(self, "def_search") else ""
        selected_class = self.def_class_filter.get() if hasattr(self, "def_class_filter") else "All Classes"
        class_id = None
        if selected_class and selected_class != "All Classes":
            c_obj = next((c for c in self.classes_cache if c["name"] == selected_class), None)
            if c_obj:
                class_id = c_obj["id"]

        defs = self.controller.get_defaulter_summary(class_id=class_id)
        if term:
            defs = [
                d for d in defs
                if term in str(d.get("first_name", "")).lower()
                or term in str(d.get("last_name", "")).lower()
                or term in str(d.get("admission_number", "")).lower()
                or term in str(d.get("invoice_number", "")).lower()
                or term in str(d.get("father_name", "")).lower()
            ]

        self.current_defaulters = defs
        formatted = []
        tot_bal = 0.0
        for d in defs:
            bal = float(d.get("balance_amount", 0))
            tot_bal += bal
            formatted.append({
                "invoice_number": d.get("invoice_number"),
                "admission_number": d.get("admission_number"),
                "student_name": f"{d.get('first_name')} {d.get('last_name')}",
                "class_name": f"{d.get('class_name')} - {d.get('section_name')}",
                "father_phone": d.get("father_phone", "-"),
                "due_date": str(d.get("due_date")),
                "balance_amount": f"PKR {bal:,.0f}"
            })
        self.def_table.populate(formatted)
        cls_info = f" ({selected_class})" if selected_class != "All Classes" else ""
        self.defaulters_status.configure(text=f"Total: {len(defs)} Defaulters{cls_info} (PKR {tot_bal:,.0f})")

    def _export_defaulters_excel(self):
        if not self.current_defaulters:
            self.defaulters_status.configure(text="No defaulter records to export.")
            return

        file_path = ExcelService.export_defaulter_list(self.current_defaulters)
        self.defaulters_status.configure(text=f"✔ Exported to {os.path.basename(file_path)}", text_color=ThemeConfig.SUCCESS[1])
        try:
            os.startfile(file_path)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # TAB 4: FEE STRUCTURES CONFIGURATION
    # -------------------------------------------------------------------------
    def _init_structures_tab(self):
        tab = self.tab_structures
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        card = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=12, border_width=1, border_color=ThemeConfig.BORDER)
        card.grid(row=0, column=0, padx=4, pady=(4, 12), sticky="ew")

        ctk.CTkLabel(card, text="Fee Structures Configuration", font=ThemeConfig.get_font(12, "bold"), text_color=ThemeConfig.TEXT_MAIN).pack(side="left", padx=16, pady=12)

        classes = self.student_repo.get_all_classes()
        c_names = [c["name"] for c in classes]
        self.struct_class = ctk.CTkComboBox(card, values=c_names, command=lambda v: self._refresh_structures())
        if c_names:
            self.struct_class.set(c_names[0])
        self.struct_class.pack(side="left", padx=8, pady=12)

        cols = [
            ("fee_head_name", "Fee Head", 220),
            ("frequency", "Frequency", 140),
            ("amount", "Amount (PKR)", 160)
        ]
        self.struct_table = DataTable(tab, columns=cols)
        self.struct_table.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="nsew")

        self._refresh_structures()

    def _refresh_structures(self):
        c_name = self.struct_class.get()
        classes = self.student_repo.get_all_classes()
        c_obj = next((c for c in classes if c["name"] == c_name), None)
        if not c_obj:
            return

        session = self.student_repo.get_current_session()
        session_id = session["id"] if session else 1

        structs = self.repo.get_fee_structure(c_obj["id"], session_id)
        formatted = []
        for s in structs:
            formatted.append({
                "fee_head_name": s.get("fee_head_name", ""),
                "frequency": s.get("frequency", "Monthly"),
                "amount": f"PKR {float(s.get('amount', 0)):,.0f}"
            })
        self.struct_table.populate(formatted)

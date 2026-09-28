"""
Teacher & Staff Management Module View.
Features:
- Staff Directory
- Add Staff & Faculty Profile Wizard
- Monthly Salary & Payroll Generator
- Centered, Straight, Low-Opacity Campus Watermark Background
"""
import customtkinter as ctk
from datetime import date
from config.theme_config import ThemeConfig
from src.views.components.data_table import DataTable
from src.views.components.watermark import WatermarkManager
from src.repositories.staff_repository import StaffRepository

class StaffView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=ThemeConfig.BG_MAIN, **kwargs)
        self.repo = StaffRepository()

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

        self.tab_dir = self.tabview.add("👨‍🏫 Staff Directory")
        self.tab_add = self.tabview.add("➕ Add Staff Member")
        self.tab_payroll = self.tabview.add("💵 Monthly Payroll")

        self._init_dir_tab()
        self._init_add_tab()
        self._init_payroll_tab()

    def _init_dir_tab(self):
        tab = self.tab_dir
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        filter_bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        filter_bar.grid(row=0, column=0, padx=4, pady=(4, 12), sticky="ew")

        self.depts_cache = self.repo.get_all_departments()
        dept_options = ["All Departments"] + [d["name"] for d in self.depts_cache]

        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="🔍 Search staff code, name, designation, or phone...",
            font=ThemeConfig.get_font(12),
            width=220,
            height=36
        )
        self.search_entry.pack(side="left", padx=(10, 4), pady=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_dir())
        self.search_entry.bind("<Return>", lambda e: self._refresh_dir())

        ctk.CTkLabel(filter_bar, text="Dept:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(4, 2), pady=10)
        self.dept_filter = ctk.CTkComboBox(
            filter_bar,
            values=dept_options,
            command=lambda v: self._refresh_dir(),
            width=120,
            height=36
        )
        self.dept_filter.set("All Departments")
        self.dept_filter.pack(side="left", padx=2, pady=10)

        # Status Filter (Active, Inactive/Relieved, All)
        ctk.CTkLabel(filter_bar, text="Status:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(4, 2), pady=10)
        self.staff_status_filter = ctk.CTkComboBox(
            filter_bar,
            values=["Active", "Inactive / Relieved", "All"],
            command=lambda v: self._refresh_dir(),
            width=100,
            height=36
        )
        self.staff_status_filter.set("Active")
        self.staff_status_filter.pack(side="left", padx=(2, 6), pady=10)

        # Refresh Button
        refresh_btn = ctk.CTkButton(
            filter_bar,
            text="🔄 Refresh",
            width=75,
            height=36,
            fg_color=ThemeConfig.BG_CARD_ALT,
            text_color=ThemeConfig.TEXT_MAIN,
            border_width=1,
            border_color=ThemeConfig.BORDER,
            command=self._refresh_dir
        )
        refresh_btn.pack(side="right", padx=(4, 10), pady=10)

        # Delete Staff Button (Double Confirmation)
        delete_btn = ctk.CTkButton(
            filter_bar,
            text="🗑️ Delete",
            width=80,
            height=36,
            fg_color=ThemeConfig.DANGER,
            hover_color="#991B1B",
            command=self._open_delete_staff_dialog
        )
        delete_btn.pack(side="right", padx=3, pady=10)

        # Relieve / Resign Button
        relieve_btn = ctk.CTkButton(
            filter_bar,
            text="🚪 Relieve / Resign",
            width=135,
            height=36,
            fg_color=ThemeConfig.WARNING,
            hover_color="#B45309",
            command=self._open_staff_status_dialog
        )
        relieve_btn.pack(side="right", padx=3, pady=10)

        # Edit Staff Button
        edit_btn = ctk.CTkButton(
            filter_bar,
            text="✏️ Edit Profile",
            width=110,
            height=36,
            fg_color=ThemeConfig.PRIMARY,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            command=self._open_edit_staff_dialog
        )
        edit_btn.pack(side="right", padx=3, pady=10)

        self.staff_count_lbl = ctk.CTkLabel(
            filter_bar,
            text="",
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.TEXT_MUTED
        )
        self.staff_count_lbl.pack(side="right", padx=6)

        cols = [
            ("employee_code", "Code", 85),
            ("full_name", "Full Name", 160),
            ("designation", "Designation", 140),
            ("department_name", "Department", 120),
            ("qualification", "Qualification", 130),
            ("contact_phone", "Phone", 110),
            ("basic_salary", "Basic Salary", 100),
            ("status_label", "Status", 95)
        ]
        self.staff_table = DataTable(tab, columns=cols, on_double_click=self._open_edit_staff_dialog)
        self.staff_table.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="nsew")

        self._refresh_dir()

    def _refresh_dir(self):
        term = self.search_entry.get().strip()
        selected_dept = self.dept_filter.get() if hasattr(self, "dept_filter") else "All Departments"
        dept_id = None
        if selected_dept and selected_dept != "All Departments":
            d_obj = next((d for d in self.depts_cache if d["name"] == selected_dept), None)
            if d_obj:
                dept_id = d_obj["id"]

        st_filter = self.staff_status_filter.get() if hasattr(self, "staff_status_filter") else "Active"
        staff_list = self.repo.get_all_staff(department_id=dept_id, search_term=term, status_filter=st_filter)
        formatted = []
        for s in staff_list:
            is_act = bool(s.get("is_active", 1))
            formatted.append({
                "id": s["id"],
                "employee_code": s.get("employee_code", ""),
                "full_name": f"{s.get('first_name', '')} {s.get('last_name', '')}",
                "designation": s.get("designation", "-"),
                "department_name": s.get("department_name", "-"),
                "qualification": s.get("qualification", "-"),
                "contact_phone": s.get("contact_phone", "-"),
                "basic_salary": f"PKR {float(s.get('basic_salary', 0)):,.0f}",
                "status_label": "🟢 Active" if is_act else "🔴 Relieved"
            })
        self.staff_table.populate(formatted)
        cls_info = f" ({selected_dept})" if selected_dept != "All Departments" else ""
        self.staff_count_lbl.configure(text=f"Total: {len(formatted)} Staff{cls_info}", text_color=ThemeConfig.TEXT_MUTED)

    def _open_edit_staff_dialog(self, item=None):
        if not item:
            item = self.staff_table.get_selected_item()

        if not item or not item.get("id"):
            self.staff_count_lbl.configure(
                text="⚠ Select a staff member from the table to edit.",
                text_color=ThemeConfig.WARNING[1]
            )
            return

        staff_id = item["id"]
        staff_data = self.repo.get_staff_by_id(staff_id)
        if not staff_data:
            self.staff_count_lbl.configure(text="⚠ Staff record not found.", text_color=ThemeConfig.DANGER[1])
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"✏️ Edit Staff Member - {staff_data['employee_code']}")
        dialog.geometry("640x700")
        dialog.grab_set()

        # Dialog Header
        top_bar = ctk.CTkFrame(dialog, fg_color=ThemeConfig.BG_CARD_ALT, corner_radius=0)
        top_bar.pack(fill="x", padx=0, pady=0)
        ctk.CTkLabel(
            top_bar,
            text=f"EDIT PROFILE: {staff_data['first_name']} {staff_data['last_name']} ({staff_data['employee_code']})",
            font=ThemeConfig.get_font(13, "bold"),
            text_color=ThemeConfig.PRIMARY[1]
        ).pack(side="left", padx=20, pady=12)

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)
        scroll.grid_columnconfigure((1, 3), weight=1)

        # 1. First & Last Name
        ctk.CTkLabel(scroll, text="First Name *", font=ThemeConfig.get_font(11, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=6)
        e_fn = ctk.CTkEntry(scroll)
        e_fn.insert(0, staff_data.get("first_name", ""))
        e_fn.grid(row=0, column=1, sticky="ew", padx=10, pady=6)

        ctk.CTkLabel(scroll, text="Last Name *", font=ThemeConfig.get_font(11, "bold")).grid(row=0, column=2, sticky="w", padx=10, pady=6)
        e_ln = ctk.CTkEntry(scroll)
        e_ln.insert(0, staff_data.get("last_name", ""))
        e_ln.grid(row=0, column=3, sticky="ew", padx=10, pady=6)

        # 2. Designation & Department
        ctk.CTkLabel(scroll, text="Designation *", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=0, sticky="w", padx=10, pady=6)
        e_desig = ctk.CTkEntry(scroll)
        e_desig.insert(0, staff_data.get("designation", ""))
        e_desig.grid(row=1, column=1, sticky="ew", padx=10, pady=6)

        ctk.CTkLabel(scroll, text="Department *", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=2, sticky="w", padx=10, pady=6)
        dept_names = [d["name"] for d in self.depts_cache]
        e_dept = ctk.CTkComboBox(scroll, values=dept_names)
        curr_dept = staff_data.get("department_name", dept_names[0] if dept_names else "")
        e_dept.set(curr_dept)
        e_dept.grid(row=1, column=3, sticky="ew", padx=10, pady=6)

        # 3. Gender & Date of Birth
        ctk.CTkLabel(scroll, text="Gender", font=ThemeConfig.get_font(11, "bold")).grid(row=2, column=0, sticky="w", padx=10, pady=6)
        e_gender = ctk.CTkComboBox(scroll, values=["Male", "Female", "Other"])
        e_gender.set(staff_data.get("gender", "Male"))
        e_gender.grid(row=2, column=1, sticky="ew", padx=10, pady=6)

        ctk.CTkLabel(scroll, text="Date of Birth", font=ThemeConfig.get_font(11, "bold")).grid(row=2, column=2, sticky="w", padx=10, pady=6)
        e_dob = ctk.CTkEntry(scroll)
        e_dob.insert(0, str(staff_data.get("date_of_birth", "1990-01-01")))
        e_dob.grid(row=2, column=3, sticky="ew", padx=10, pady=6)

        # 4. CNIC & Qualification
        ctk.CTkLabel(scroll, text="CNIC / NID", font=ThemeConfig.get_font(11, "bold")).grid(row=3, column=0, sticky="w", padx=10, pady=6)
        e_cnic = ctk.CTkEntry(scroll)
        e_cnic.insert(0, staff_data.get("cnic_nid", "") or "")
        e_cnic.grid(row=3, column=1, sticky="ew", padx=10, pady=6)

        ctk.CTkLabel(scroll, text="Qualification", font=ThemeConfig.get_font(11, "bold")).grid(row=3, column=2, sticky="w", padx=10, pady=6)
        e_qual = ctk.CTkEntry(scroll)
        e_qual.insert(0, staff_data.get("qualification", "") or "")
        e_qual.grid(row=3, column=3, sticky="ew", padx=10, pady=6)

        # 5. Phone & Email
        ctk.CTkLabel(scroll, text="Phone *", font=ThemeConfig.get_font(11, "bold")).grid(row=4, column=0, sticky="w", padx=10, pady=6)
        e_phone = ctk.CTkEntry(scroll)
        e_phone.insert(0, staff_data.get("contact_phone", ""))
        e_phone.grid(row=4, column=1, sticky="ew", padx=10, pady=6)

        ctk.CTkLabel(scroll, text="Email", font=ThemeConfig.get_font(11, "bold")).grid(row=4, column=2, sticky="w", padx=10, pady=6)
        e_email = ctk.CTkEntry(scroll)
        e_email.insert(0, staff_data.get("email", "") or "")
        e_email.grid(row=4, column=3, sticky="ew", padx=10, pady=6)

        # 6. Basic Salary & Status
        ctk.CTkLabel(scroll, text="Basic Salary (PKR)", font=ThemeConfig.get_font(11, "bold")).grid(row=5, column=0, sticky="w", padx=10, pady=6)
        e_salary = ctk.CTkEntry(scroll)
        e_salary.insert(0, str(staff_data.get("basic_salary", "0")))
        e_salary.grid(row=5, column=1, sticky="ew", padx=10, pady=6)

        ctk.CTkLabel(scroll, text="Status", font=ThemeConfig.get_font(11, "bold")).grid(row=5, column=2, sticky="w", padx=10, pady=6)
        e_status = ctk.CTkComboBox(scroll, values=["Active", "Inactive"])
        e_status.set("Active" if staff_data.get("is_active", 1) else "Inactive")
        e_status.grid(row=5, column=3, sticky="ew", padx=10, pady=6)

        # 7. Bank Details
        ctk.CTkLabel(scroll, text="Bank Info", font=ThemeConfig.get_font(11, "bold")).grid(row=6, column=0, sticky="w", padx=10, pady=6)
        e_bank = ctk.CTkEntry(scroll)
        e_bank.insert(0, staff_data.get("bank_account_info", "") or "")
        e_bank.grid(row=6, column=1, columnspan=3, sticky="ew", padx=10, pady=6)

        # 8. Address
        ctk.CTkLabel(scroll, text="Address", font=ThemeConfig.get_font(11, "bold")).grid(row=7, column=0, sticky="w", padx=10, pady=6)
        e_addr = ctk.CTkEntry(scroll)
        e_addr.insert(0, staff_data.get("address", "") or "")
        e_addr.grid(row=7, column=1, columnspan=3, sticky="ew", padx=10, pady=6)

        dialog_status = ctk.CTkLabel(dialog, text="", font=ThemeConfig.get_font(11, "bold"))
        dialog_status.pack(pady=4)

        # Action Buttons
        btn_bar = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 16))

        def save_edits():
            fn = e_fn.get().strip()
            ln = e_ln.get().strip()
            desig = e_desig.get().strip()
            phone = e_phone.get().strip()

            if not fn or not desig or not phone:
                dialog_status.configure(text="Please fill in all mandatory fields (*).", text_color=ThemeConfig.DANGER[1])
                return

            try:
                sal = float(e_salary.get().strip() or "0")
            except ValueError:
                sal = 0.0

            d_obj = next((d for d in self.depts_cache if d["name"] == e_dept.get()), None)
            dept_id = d_obj["id"] if d_obj else 1

            payload = {
                "department_id": dept_id,
                "first_name": fn,
                "last_name": ln,
                "gender": e_gender.get(),
                "cnic_nid": e_cnic.get().strip(),
                "date_of_birth": e_dob.get().strip() or "1990-01-01",
                "qualification": e_qual.get().strip(),
                "designation": desig,
                "contact_phone": phone,
                "email": e_email.get().strip(),
                "address": e_addr.get().strip(),
                "basic_salary": sal,
                "bank_account_info": e_bank.get().strip(),
                "is_active": (e_status.get() == "Active")
            }

            try:
                success = self.repo.update_staff(staff_id, payload)
                if success:
                    self._refresh_dir()
                    self.staff_count_lbl.configure(text=f"✔ Updated {fn} {ln} successfully!", text_color=ThemeConfig.SUCCESS[1])
                    dialog.destroy()
                else:
                    dialog_status.configure(text="Failed to update staff record.", text_color=ThemeConfig.DANGER[1])
            except Exception as e:
                dialog_status.configure(text=f"Error: {str(e)}", text_color=ThemeConfig.DANGER[1])

        ctk.CTkButton(btn_bar, text="Cancel", width=90, fg_color=ThemeConfig.BG_CARD_ALT, text_color=ThemeConfig.TEXT_MAIN, command=dialog.destroy).pack(side="left")
        ctk.CTkButton(btn_bar, text="💾 Save Changes", font=ThemeConfig.get_font(12, "bold"), fg_color=ThemeConfig.PRIMARY, hover_color=ThemeConfig.PRIMARY_HOVER, command=save_edits).pack(side="right")

    def _open_staff_status_dialog(self):
        """Allows marking staff as Resigned, Retired, Terminated, On Leave, or Active."""
        item = self.staff_table.get_selected_item()
        if not item or not item.get("id"):
            self.staff_count_lbl.configure(text="⚠ Select a staff member from the table first.", text_color=ThemeConfig.WARNING[1])
            return

        staff_id = item["id"]
        staff_data = self.repo.get_staff_by_id(staff_id)
        if not staff_data:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"🚪 Relieve / Resign Staff - {staff_data['employee_code']}")
        dialog.geometry("450x390")
        dialog.grab_set()

        top_bar = ctk.CTkFrame(dialog, fg_color=ThemeConfig.BG_CARD_ALT, corner_radius=0)
        top_bar.pack(fill="x")
        ctk.CTkLabel(
            top_bar,
            text="STAFF RELIEVING & LIFECYCLE",
            font=ThemeConfig.get_font(13, "bold"),
            text_color=ThemeConfig.GOLD_ACCENT[1]
        ).pack(side="left", padx=20, pady=12)

        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=12)

        info_box = ctk.CTkFrame(content, fg_color=ThemeConfig.BG_CARD, corner_radius=8, border_width=1, border_color=ThemeConfig.BORDER)
        info_box.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            info_box,
            text=f"Faculty: {staff_data['first_name']} {staff_data['last_name']} ({staff_data['employee_code']})",
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.TEXT_MAIN
        ).pack(anchor="w", padx=12, pady=(8, 2))
        cur_st_text = "Active" if staff_data.get("is_active", 1) else "Relieved / Inactive"
        ctk.CTkLabel(
            info_box,
            text=f"Dept: {staff_data.get('department_name', '')}  •  Designation: {staff_data.get('designation', '')}  •  Status: {cur_st_text}",
            font=ThemeConfig.get_font(10),
            text_color=ThemeConfig.TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkLabel(content, text="Relieving / Status Action:", font=ThemeConfig.get_font(11, "bold")).pack(anchor="w", pady=(4, 2))
        status_cb = ctk.CTkComboBox(content, values=["Resigned", "Retired", "Terminated", "On Leave", "Active"], height=34)
        status_cb.set("Resigned" if staff_data.get("is_active", 1) else "Active")
        status_cb.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(content, text="Relieving Reason / Official Remarks:", font=ThemeConfig.get_font(11, "bold")).pack(anchor="w", pady=(4, 2))
        remarks_entry = ctk.CTkEntry(content, height=34, placeholder_text="e.g., Submitted formal resignation letter / Relieved on 2026-09-18")
        remarks_entry.pack(fill="x", pady=(0, 16))

        def save_status():
            st_val = status_cb.get().strip()
            rem = remarks_entry.get().strip()
            is_active = (st_val == "Active")
            ok = self.repo.update_staff_status(staff_id, is_active, status_label=st_val, remarks=rem)
            if ok:
                self.staff_count_lbl.configure(text=f"✔ Updated status to '{st_val}' successfully!", text_color=ThemeConfig.SUCCESS[1])
                dialog.destroy()
                self._refresh_dir()
            else:
                self.staff_count_lbl.configure(text="✖ Failed to update staff status.", text_color=ThemeConfig.DANGER[1])

        btn_bar = ctk.CTkFrame(content, fg_color="transparent")
        btn_bar.pack(fill="x", pady=4)
        ctk.CTkButton(btn_bar, text="Cancel", font=ThemeConfig.get_font(11), fg_color=ThemeConfig.BG_CARD_ALT, hover_color=ThemeConfig.BG_HOVER, width=100, command=dialog.destroy).pack(side="left")
        ctk.CTkButton(btn_bar, text="✔ Confirm Update", font=ThemeConfig.get_font(11, "bold"), fg_color=ThemeConfig.PRIMARY, hover_color=ThemeConfig.PRIMARY_HOVER, width=140, command=save_status).pack(side="right")

    def _open_delete_staff_dialog(self):
        """STEP 1 OF 2: Warning details + choice between Relieve/Archive vs Permanent Deletion."""
        item = self.staff_table.get_selected_item()
        if not item or not item.get("id"):
            self.staff_count_lbl.configure(text="⚠ Select a staff member from the table to delete.", text_color=ThemeConfig.WARNING[1])
            return

        staff_id = item["id"]
        staff_data = self.repo.get_staff_by_id(staff_id)
        if not staff_data:
            return

        d1 = ctk.CTkToplevel(self)
        d1.title("⚠️ Confirm Staff Deletion / Relieving (Step 1 of 2)")
        d1.geometry("520x430")
        d1.grab_set()

        top_bar = ctk.CTkFrame(d1, fg_color=ThemeConfig.DANGER[1], corner_radius=0)
        top_bar.pack(fill="x")
        ctk.CTkLabel(
            top_bar,
            text="⚠️ CONFIRM RECORD DELETION - STEP 1 OF 2",
            font=ThemeConfig.get_font(12, "bold"),
            text_color="#FFFFFF"
        ).pack(side="left", padx=16, pady=10)

        body = ctk.CTkFrame(d1, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=16)

        card = ctk.CTkFrame(body, fg_color=ThemeConfig.BG_CARD, corner_radius=8, border_width=1, border_color=ThemeConfig.BORDER)
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card, text="TARGET FACULTY / STAFF MEMBER:", font=ThemeConfig.get_font(10, "bold"), text_color=ThemeConfig.TEXT_MUTED).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(
            card,
            text=f"👨‍🏫 {staff_data['first_name']} {staff_data['last_name']} ({staff_data['employee_code']})",
            font=ThemeConfig.get_font(13, "bold"),
            text_color=ThemeConfig.TEXT_MAIN
        ).pack(anchor="w", padx=12, pady=1)
        ctk.CTkLabel(
            card,
            text=f"Dept: {staff_data.get('department_name', '')}  •  Designation: {staff_data.get('designation', '')}",
            font=ThemeConfig.get_font(11),
            text_color=ThemeConfig.GOLD_ACCENT[1]
        ).pack(anchor="w", padx=12, pady=1)
        ctk.CTkLabel(
            card,
            text=f"Contact Phone: {staff_data.get('contact_phone', '-')}  •  Salary: PKR {float(staff_data.get('basic_salary', 0)):,.0f}",
            font=ThemeConfig.get_font(10),
            text_color=ThemeConfig.TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(1, 8))

        notice = ctk.CTkFrame(body, fg_color=ThemeConfig.BG_CARD_ALT, corner_radius=6)
        notice.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            notice,
            text="ℹ️ In school administration, teachers who leave should normally\n"
                 "be marked as 'Resigned' or 'Relieved' to preserve past subject\n"
                 "teaching history, payroll records, and attendance logs.",
            font=ThemeConfig.get_font(10),
            text_color=ThemeConfig.TEXT_MAIN,
            justify="left"
        ).pack(padx=10, pady=8)

        def proceed_to_step2():
            d1.destroy()
            self._open_permanent_delete_staff_step2(staff_data)

        def proceed_to_status():
            d1.destroy()
            self._open_staff_status_dialog()

        ctk.CTkButton(
            body,
            text="🚪 Relieve / Resign Staff (Archive - Recommended)",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.WARNING,
            hover_color="#B45309",
            height=36,
            command=proceed_to_status
        ).pack(fill="x", pady=(0, 8))

        ctk.CTkButton(
            body,
            text="🚨 Proceed to Permanent Deletion (Step 2/2)",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.DANGER,
            hover_color="#991B1B",
            height=36,
            command=proceed_to_step2
        ).pack(fill="x", pady=(0, 6))

        ctk.CTkButton(
            body,
            text="Cancel",
            font=ThemeConfig.get_font(11),
            fg_color="transparent",
            hover_color=ThemeConfig.BG_HOVER,
            height=30,
            command=d1.destroy
        ).pack(fill="x")

    def _open_permanent_delete_staff_step2(self, staff_data: dict):
        """STEP 2 OF 2: Strict Double Confirmation requiring typing DELETE."""
        d2 = ctk.CTkToplevel(self)
        d2.title("🚨 CRITICAL: Permanent Staff Deletion (Step 2 of 2)")
        d2.geometry("480x370")
        d2.grab_set()

        top_bar = ctk.CTkFrame(d2, fg_color="#991B1B", corner_radius=0)
        top_bar.pack(fill="x")
        ctk.CTkLabel(
            top_bar,
            text="🚨 FINAL CONFIRMATION - STEP 2 OF 2",
            font=ThemeConfig.get_font(12, "bold"),
            text_color="#FFFFFF"
        ).pack(side="left", padx=16, pady=10)

        body = ctk.CTkFrame(d2, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=20, pady=16)

        st_name = f"{staff_data['first_name']} {staff_data['last_name']} ({staff_data['employee_code']})"
        ctk.CTkLabel(
            body,
            text=f"You are about to PERMANENTLY ERASE:\n{st_name}",
            font=ThemeConfig.get_font(12, "bold"),
            text_color=ThemeConfig.DANGER[1],
            justify="center"
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            body,
            text="This action CANNOT BE UNDONE. All payroll history, teacher\n"
                 "assignments, and staff attendance logs will be permanently\n"
                 "erased from the database.",
            font=ThemeConfig.get_font(10),
            text_color=ThemeConfig.TEXT_MUTED,
            justify="center"
        ).pack(pady=(0, 14))

        ctk.CTkLabel(
            body,
            text="Type the word DELETE in capital letters to unlock:",
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.TEXT_MAIN
        ).pack(anchor="w", pady=(0, 4))

        entry_confirm = ctk.CTkEntry(body, font=ThemeConfig.get_font(12, "bold"), height=36, placeholder_text="Type DELETE here...")
        entry_confirm.pack(fill="x", pady=(0, 16))

        def execute_purge():
            if entry_confirm.get().strip() != "DELETE":
                return
            ok, msg = self.repo.delete_staff_permanently(staff_data["id"])
            if ok:
                self.staff_count_lbl.configure(text=f"✔ {msg}", text_color=ThemeConfig.SUCCESS[1])
                d2.destroy()
                self._refresh_dir()
            else:
                self.staff_count_lbl.configure(text=f"✖ {msg}", text_color=ThemeConfig.DANGER[1])

        btn_purge = ctk.CTkButton(
            body,
            text="🚨 Permanently Delete Staff Record",
            font=ThemeConfig.get_font(12, "bold"),
            fg_color="#64748B",
            state="disabled",
            height=38,
            command=execute_purge
        )
        btn_purge.pack(fill="x", pady=(0, 8))

        def on_text_change(e=None):
            if entry_confirm.get().strip() == "DELETE":
                btn_purge.configure(state="normal", fg_color=ThemeConfig.DANGER, hover_color="#991B1B")
            else:
                btn_purge.configure(state="disabled", fg_color="#64748B")

        entry_confirm.bind("<KeyRelease>", on_text_change)

        ctk.CTkButton(
            body,
            text="Cancel & Keep Record",
            font=ThemeConfig.get_font(11),
            fg_color="transparent",
            hover_color=ThemeConfig.BG_HOVER,
            height=30,
            command=d2.destroy
        ).pack(fill="x")

    def _init_add_tab(self):
        tab = self.tab_add
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        card = ctk.CTkFrame(scroll, fg_color=ThemeConfig.BG_CARD, corner_radius=12, border_width=1, border_color=ThemeConfig.BORDER)
        card.grid(row=0, column=0, columnspan=2, padx=4, pady=4, sticky="ew")
        card.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(card, text="REGISTER NEW STAFF MEMBER", font=ThemeConfig.get_font(12, "bold"), text_color=ThemeConfig.SECONDARY[1]).grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(16, 12))

        # First Name
        ctk.CTkLabel(card, text="First Name *", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=0, sticky="w", padx=16, pady=6)
        self.add_fn = ctk.CTkEntry(card, placeholder_text="First name")
        self.add_fn.grid(row=1, column=1, sticky="ew", padx=16, pady=6)

        # Last Name
        ctk.CTkLabel(card, text="Last Name *", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=2, sticky="w", padx=16, pady=6)
        self.add_ln = ctk.CTkEntry(card, placeholder_text="Last name")
        self.add_ln.grid(row=1, column=3, sticky="ew", padx=16, pady=6)

        # Designation
        ctk.CTkLabel(card, text="Designation *", font=ThemeConfig.get_font(11, "bold")).grid(row=2, column=0, sticky="w", padx=16, pady=6)
        self.add_desig = ctk.CTkEntry(card, placeholder_text="e.g. Senior Math Teacher / Accountant")
        self.add_desig.grid(row=2, column=1, sticky="ew", padx=16, pady=6)

        # Department
        ctk.CTkLabel(card, text="Department *", font=ThemeConfig.get_font(11, "bold")).grid(row=2, column=2, sticky="w", padx=16, pady=6)
        self.depts_cache = self.repo.get_all_departments()
        dept_names = [d["name"] for d in self.depts_cache] or ["Teaching Faculty", "Administration"]
        self.add_dept = ctk.CTkComboBox(card, values=dept_names)
        self.add_dept.set(dept_names[0])
        self.add_dept.grid(row=2, column=3, sticky="ew", padx=16, pady=6)

        # Phone
        ctk.CTkLabel(card, text="Phone Number *", font=ThemeConfig.get_font(11, "bold")).grid(row=3, column=0, sticky="w", padx=16, pady=6)
        self.add_phone = ctk.CTkEntry(card, placeholder_text="0300-XXXXXXX")
        self.add_phone.grid(row=3, column=1, sticky="ew", padx=16, pady=6)

        # CNIC
        ctk.CTkLabel(card, text="CNIC / NID", font=ThemeConfig.get_font(11)).grid(row=3, column=2, sticky="w", padx=16, pady=6)
        self.add_cnic = ctk.CTkEntry(card, placeholder_text="XXXXX-XXXXXXX-X")
        self.add_cnic.grid(row=3, column=3, sticky="ew", padx=16, pady=6)

        # Qualification
        ctk.CTkLabel(card, text="Qualification", font=ThemeConfig.get_font(11)).grid(row=4, column=0, sticky="w", padx=16, pady=6)
        self.add_qual = ctk.CTkEntry(card, placeholder_text="e.g. M.Sc Mathematics, B.Ed")
        self.add_qual.grid(row=4, column=1, sticky="ew", padx=16, pady=6)

        # Basic Salary
        ctk.CTkLabel(card, text="Basic Salary (PKR) *", font=ThemeConfig.get_font(11, "bold")).grid(row=4, column=2, sticky="w", padx=16, pady=6)
        self.add_salary = ctk.CTkEntry(card, placeholder_text="e.g. 45000")
        self.add_salary.insert(0, "40000")
        self.add_salary.grid(row=4, column=3, sticky="ew", padx=16, pady=6)

        # Save Button
        btn_bar = ctk.CTkFrame(card, fg_color="transparent")
        btn_bar.grid(row=5, column=0, columnspan=4, padx=16, pady=(16, 20), sticky="ew")

        self.add_status_lbl = ctk.CTkLabel(btn_bar, text="", font=ThemeConfig.get_font(12, "bold"))
        self.add_status_lbl.pack(side="left")

        save_btn = ctk.CTkButton(
            btn_bar,
            text="✔ Save Staff Profile",
            font=ThemeConfig.get_font(12, "bold"),
            fg_color=ThemeConfig.SECONDARY,
            hover_color=ThemeConfig.SECONDARY_HOVER,
            height=40,
            command=self._do_add_staff
        )
        save_btn.pack(side="right")

    def _do_add_staff(self):
        fn = self.add_fn.get().strip()
        ln = self.add_ln.get().strip()
        desig = self.add_desig.get().strip()
        phone = self.add_phone.get().strip()

        if not fn or not desig or not phone:
            self.add_status_lbl.configure(text="Please fill in all mandatory fields (*).", text_color=ThemeConfig.DANGER[1])
            return

        try:
            sal = float(self.add_salary.get().strip() or "0")
        except ValueError:
            sal = 0.0

        dept_obj = next((d for d in self.depts_cache if d["name"] == self.add_dept.get()), None)
        dept_id = dept_obj["id"] if dept_obj else 1
        emp_code = self.repo.generate_employee_code()

        payload = {
            "emp_code": emp_code,
            "dept_id": dept_id,
            "fn": fn,
            "ln": ln,
            "gen": "Male",
            "cnic": self.add_cnic.get().strip() or f"35201-9999999-{date.today().day}",
            "dob": "1990-01-01",
            "qual": self.add_qual.get().strip(),
            "desig": desig,
            "join_date": date.today().isoformat(),
            "phone": phone,
            "email": "",
            "addr": "",
            "salary": sal,
            "bank": ""
        }

        try:
            self.repo.add_staff(payload)
            self.add_status_lbl.configure(text=f"✔ Staff added with Employee Code: {emp_code}", text_color=ThemeConfig.SUCCESS[1])
            self.add_fn.delete(0, "end")
            self.add_ln.delete(0, "end")
            self.add_desig.delete(0, "end")
            self.add_phone.delete(0, "end")
            self._refresh_dir()
        except Exception as e:
            self.add_status_lbl.configure(text=f"✖ Error: {str(e)}", text_color=ThemeConfig.DANGER[1])

    def _init_payroll_tab(self):
        tab = self.tab_payroll
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        bar.grid(row=0, column=0, padx=4, pady=(4, 12), sticky="ew")

        ctk.CTkLabel(bar, text="Payroll Month:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=12, pady=10)
        self.payroll_month = ctk.CTkComboBox(bar, values=[str(m) for m in range(1, 13)], width=70)
        self.payroll_month.set(str(date.today().month))
        self.payroll_month.pack(side="left", padx=4, pady=10)

        ctk.CTkLabel(bar, text="Year:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=8, pady=10)
        self.payroll_year = ctk.CTkComboBox(bar, values=["2025", "2026", "2027"], width=80)
        self.payroll_year.set(str(date.today().year))
        self.payroll_year.pack(side="left", padx=4, pady=10)

        gen_btn = ctk.CTkButton(
            bar,
            text="⚡ Generate Monthly Payroll",
            font=ThemeConfig.get_font(12, "bold"),
            fg_color=ThemeConfig.PRIMARY,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            command=self._do_gen_payroll
        )
        gen_btn.pack(side="left", padx=16, pady=10)

        self.payroll_msg = ctk.CTkLabel(bar, text="", font=ThemeConfig.get_font(11, "bold"))
        self.payroll_msg.pack(side="left", padx=8)

        cols = [
            ("employee_code", "Emp Code", 90),
            ("full_name", "Staff Name", 180),
            ("designation", "Designation", 140),
            ("basic_salary", "Basic", 100),
            ("net_salary", "Net Payable", 110),
            ("payment_status", "Status", 100)
        ]
        self.payroll_table = DataTable(tab, columns=cols)
        self.payroll_table.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="nsew")

        self._refresh_payroll()

    def _do_gen_payroll(self):
        m = int(self.payroll_month.get())
        y = int(self.payroll_year.get())
        created = self.repo.generate_monthly_payroll(m, y)
        self.payroll_msg.configure(text=f"✔ Processed {created} staff records.", text_color=ThemeConfig.SUCCESS[1])
        self._refresh_payroll()

    def _refresh_payroll(self):
        m = int(self.payroll_month.get())
        y = int(self.payroll_year.get())
        records = self.repo.get_payroll_records(m, y)
        formatted = []
        for r in records:
            formatted.append({
                "employee_code": r.get("employee_code", ""),
                "full_name": f"{r.get('first_name', '')} {r.get('last_name', '')}",
                "designation": r.get("designation", ""),
                "basic_salary": f"PKR {float(r.get('basic_salary', 0)):,.0f}",
                "net_salary": f"PKR {float(r.get('net_salary', 0)):,.0f}",
                "payment_status": r.get("payment_status", "Pending")
            })
        self.payroll_table.populate(formatted)

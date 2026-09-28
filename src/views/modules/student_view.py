"""
Student Management Module View.
Features:
- Live Search & Directory with Responsive Data Table
- Structured Registration Form with Parent Details & Class Assignment
- Annual Academic Promotion Engine
- Centered, Straight, Low-Opacity Campus Watermark Background
"""
import customtkinter as ctk
from datetime import date
from config.theme_config import ThemeConfig
from src.views.components.data_table import DataTable
from src.views.components.watermark import WatermarkManager
from src.controllers.student_controller import StudentController
from src.repositories.student_repository import StudentRepository
from typing import Dict, Any, List

class StudentView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=ThemeConfig.BG_MAIN, **kwargs)
        self.controller = StudentController()
        self.repo = StudentRepository()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Apply centered, straight watermark in background
        WatermarkManager.apply(self, width=820, height=560)

        self._build_tabs()

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=ThemeConfig.BG_MAIN,
            segmented_button_selected_color=ThemeConfig.PRIMARY[1],
            segmented_button_selected_hover_color=ThemeConfig.PRIMARY_HOVER[1]
        )
        self.tabview.grid(row=0, column=0, padx=20, pady=16, sticky="nsew")

        self.tab_directory = self.tabview.add("👨‍🎓 Student Directory")
        self.tab_register = self.tabview.add("➕ Register New Student")
        self.tab_promote = self.tabview.add("🚀 End-of-Year Promotion")

        self._init_directory_tab()
        self._init_register_tab()
        self._init_promote_tab()

    # -------------------------------------------------------------------------
    # TAB 1: STUDENT DIRECTORY & LIVE SEARCH
    # -------------------------------------------------------------------------
    def _init_directory_tab(self):
        tab = self.tab_directory
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Filters Bar
        filter_bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        filter_bar.grid(row=0, column=0, padx=4, pady=(4, 12), sticky="ew")

        # Search Entry
        self.search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text="🔍 Search student name, adm #, father name, or phone...",
            font=ThemeConfig.get_font(12),
            width=230,
            height=36,
            corner_radius=8
        )
        self.search_entry.pack(side="left", padx=(10, 4), pady=10)
        self.search_entry.bind("<KeyRelease>", lambda e: self._refresh_directory())

        # Class Filter
        self.classes_cache = self.repo.get_all_classes()
        class_options = ["All Classes"] + [c["name"] for c in self.classes_cache]
        self.class_filter = ctk.CTkComboBox(
            filter_bar,
            values=class_options,
            command=self._on_dir_class_change,
            width=110,
            height=36
        )
        self.class_filter.set("All Classes")
        self.class_filter.pack(side="left", padx=3, pady=10)

        # Section Filter
        ctk.CTkLabel(filter_bar, text="Sec:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(4, 2), pady=10)
        self.section_filter = ctk.CTkComboBox(
            filter_bar,
            values=["All"],
            command=lambda v: self._refresh_directory(),
            width=65,
            height=36
        )
        self.section_filter.set("All")
        self.section_filter.pack(side="left", padx=(2, 4), pady=10)

        # Status Filter (Active, Passed Out, Left, etc.)
        ctk.CTkLabel(filter_bar, text="Status:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(4, 2), pady=10)
        self.status_filter = ctk.CTkComboBox(
            filter_bar,
            values=["Active", "Passed Out", "Left", "Transferred", "Inactive", "All"],
            command=lambda v: self._refresh_directory(),
            width=100,
            height=36
        )
        self.status_filter.set("Active")
        self.status_filter.pack(side="left", padx=(2, 6), pady=10)

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
            hover_color=ThemeConfig.BG_HOVER,
            command=self._refresh_directory
        )
        refresh_btn.pack(side="right", padx=(4, 10), pady=10)

        # Delete Student Button (Double Confirmation)
        delete_btn = ctk.CTkButton(
            filter_bar,
            text="🗑️ Delete",
            width=80,
            height=36,
            fg_color=ThemeConfig.DANGER,
            hover_color="#991B1B",
            command=self._open_delete_student_dialog
        )
        delete_btn.pack(side="right", padx=3, pady=10)

        # Mark Left / Passed Out Button
        status_btn = ctk.CTkButton(
            filter_bar,
            text="🚪 Mark Left / Passed",
            width=140,
            height=36,
            fg_color=ThemeConfig.WARNING,
            hover_color="#B45309",
            command=self._open_student_status_dialog
        )
        status_btn.pack(side="right", padx=3, pady=10)

        # Edit Student Button
        edit_btn = ctk.CTkButton(
            filter_bar,
            text="✏️ Edit Profile",
            width=115,
            height=36,
            fg_color=ThemeConfig.PRIMARY,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            command=self._open_edit_student_dialog
        )
        edit_btn.pack(side="right", padx=3, pady=10)

        # Results Count Label
        self.dir_count_lbl = ctk.CTkLabel(
            filter_bar,
            text="Loading students...",
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.TEXT_MUTED
        )
        self.dir_count_lbl.pack(side="right", padx=6, pady=10)

        # Table
        cols = [
            ("admission_number", "Adm No", 110),
            ("full_name", "Student Name", 160),
            ("class_name", "Class", 90),
            ("section_name", "Sec", 60),
            ("roll_number", "Roll #", 60),
            ("father_name", "Father Name", 150),
            ("father_phone", "Father Phone", 120),
            ("status", "Status", 100)
        ]
        self.dir_table = DataTable(tab, columns=cols, on_double_click=self._open_edit_student_dialog)
        self.dir_table.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="nsew")

        self._refresh_directory()

    def _on_dir_class_change(self, selected_class: str):
        if selected_class and selected_class != "All Classes":
            c_obj = next((c for c in self.classes_cache if c["name"] == selected_class), None)
            if c_obj:
                secs = self.repo.get_sections_by_class(c_obj["id"])
                sec_names = ["All"] + [s["name"] for s in secs]
                self.section_filter.configure(values=sec_names)
                self.section_filter.set("All")
        else:
            self.section_filter.configure(values=["All"])
            self.section_filter.set("All")
        self._refresh_directory()

    def _refresh_directory(self):
        term = self.search_entry.get().strip()
        selected_class = self.class_filter.get()
        class_id = None
        if selected_class and selected_class != "All Classes":
            for c in self.classes_cache:
                if c["name"] == selected_class:
                    class_id = c["id"]
                    break

        section_id = None
        selected_sec = self.section_filter.get() if hasattr(self, "section_filter") else "All"
        if class_id and selected_sec and selected_sec != "All":
            secs = self.repo.get_sections_by_class(class_id)
            sec_obj = next((s for s in secs if s["name"] == selected_sec), None)
            if sec_obj:
                section_id = sec_obj["id"]

        status_val = self.status_filter.get() if hasattr(self, "status_filter") else "Active"
        students = self.repo.search_students(search_term=term if term else None, class_id=class_id, section_id=section_id, status=status_val)
        formatted = []
        for s in students:
            formatted.append({
                "id": s["id"],
                "admission_number": s.get("admission_number", ""),
                "full_name": f"{s.get('first_name', '')} {s.get('last_name', '')}",
                "class_name": s.get("class_name", "-"),
                "section_name": s.get("section_name", "-"),
                "roll_number": s.get("roll_number", "-"),
                "father_name": s.get("father_name", "-"),
                "father_phone": s.get("father_phone", "-"),
                "status": s.get("status", "Active")
            })

        self.dir_table.populate(formatted)
        cls_info = f" ({selected_class})" if selected_class != "All Classes" else ""
        self.dir_count_lbl.configure(text=f"Total: {len(formatted)} Students{cls_info}", text_color=ThemeConfig.TEXT_MUTED)

    def _open_edit_student_dialog(self, item=None):
        if not item:
            item = self.dir_table.get_selected_item()

        if not item or not item.get("id"):
            self.dir_count_lbl.configure(
                text="⚠ Select a student from the table to edit.",
                text_color=ThemeConfig.WARNING[1]
            )
            return

        student_id = item["id"]
        student_data = self.repo.get_student_by_id(student_id)
        if not student_data:
            self.dir_count_lbl.configure(text="⚠ Student record not found.", text_color=ThemeConfig.DANGER[1])
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"✏️ Edit Student Profile - {student_data['admission_number']}")
        dialog.geometry("680x740")
        dialog.grab_set()

        # Dialog Header
        top_bar = ctk.CTkFrame(dialog, fg_color=ThemeConfig.BG_CARD_ALT, corner_radius=0)
        top_bar.pack(fill="x", padx=0, pady=0)
        ctk.CTkLabel(
            top_bar,
            text=f"EDIT PROFILE: {student_data['first_name']} {student_data['last_name']} ({student_data['admission_number']})",
            font=ThemeConfig.get_font(13, "bold"),
            text_color=ThemeConfig.PRIMARY[1]
        ).pack(side="left", padx=20, pady=12)

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=12)
        scroll.grid_columnconfigure((1, 3), weight=1)

        # Section 1 Header
        ctk.CTkLabel(scroll, text="1. STUDENT ACADEMIC & PERSONAL DETAILS", font=ThemeConfig.get_font(11, "bold"), text_color=ThemeConfig.SECONDARY[1]).grid(row=0, column=0, columnspan=4, sticky="w", padx=10, pady=(4, 8))

        # First Name & Last Name
        ctk.CTkLabel(scroll, text="First Name *", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        e_fn = ctk.CTkEntry(scroll)
        e_fn.insert(0, student_data.get("first_name", ""))
        e_fn.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(scroll, text="Last Name *", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=2, sticky="w", padx=10, pady=5)
        e_ln = ctk.CTkEntry(scroll)
        e_ln.insert(0, student_data.get("last_name", ""))
        e_ln.grid(row=1, column=3, sticky="ew", padx=10, pady=5)

        # Gender & Date of Birth
        ctk.CTkLabel(scroll, text="Gender", font=ThemeConfig.get_font(11, "bold")).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        e_gender = ctk.CTkComboBox(scroll, values=["Male", "Female", "Other"])
        e_gender.set(student_data.get("gender", "Male"))
        e_gender.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(scroll, text="Date of Birth", font=ThemeConfig.get_font(11, "bold")).grid(row=2, column=2, sticky="w", padx=10, pady=5)
        e_dob = ctk.CTkEntry(scroll)
        e_dob.insert(0, str(student_data.get("date_of_birth", "2015-01-01")))
        e_dob.grid(row=2, column=3, sticky="ew", padx=10, pady=5)

        # Class & Section
        ctk.CTkLabel(scroll, text="Class *", font=ThemeConfig.get_font(11, "bold")).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        class_names = [c["name"] for c in self.classes_cache]
        e_class = ctk.CTkComboBox(scroll, values=class_names)
        curr_class = student_data.get("class_name", class_names[0] if class_names else "")
        e_class.set(curr_class)
        e_class.grid(row=3, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(scroll, text="Section *", font=ThemeConfig.get_font(11, "bold")).grid(row=3, column=2, sticky="w", padx=10, pady=5)
        e_sec = ctk.CTkComboBox(scroll, values=["A", "B"])
        curr_sec = student_data.get("section_name", "A")
        e_sec.set(curr_sec)
        e_sec.grid(row=3, column=3, sticky="ew", padx=10, pady=5)

        def on_edit_class_change(cls_name):
            c_obj = next((c for c in self.classes_cache if c["name"] == cls_name), None)
            if c_obj:
                secs = self.repo.get_sections_by_class(c_obj["id"])
                s_names = [s["name"] for s in secs] or ["A", "B"]
                e_sec.configure(values=s_names)
                if s_names:
                    e_sec.set(s_names[0])

        e_class.configure(command=on_edit_class_change)

        # Roll Number & Status
        ctk.CTkLabel(scroll, text="Roll Number", font=ThemeConfig.get_font(11, "bold")).grid(row=4, column=0, sticky="w", padx=10, pady=5)
        e_roll = ctk.CTkEntry(scroll)
        e_roll.insert(0, str(student_data.get("roll_number", "1")))
        e_roll.grid(row=4, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(scroll, text="Status", font=ThemeConfig.get_font(11, "bold")).grid(row=4, column=2, sticky="w", padx=10, pady=5)
        e_status = ctk.CTkComboBox(scroll, values=["Active", "Inactive", "Graduated"])
        e_status.set(student_data.get("status", "Active"))
        e_status.grid(row=4, column=3, sticky="ew", padx=10, pady=5)

        # Blood Group & Religion
        ctk.CTkLabel(scroll, text="Blood Group", font=ThemeConfig.get_font(11, "bold")).grid(row=5, column=0, sticky="w", padx=10, pady=5)
        e_bg = ctk.CTkComboBox(scroll, values=["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "Unknown"])
        e_bg.set(student_data.get("blood_group") or "Unknown")
        e_bg.grid(row=5, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(scroll, text="Religion", font=ThemeConfig.get_font(11, "bold")).grid(row=5, column=2, sticky="w", padx=10, pady=5)
        e_rel = ctk.CTkEntry(scroll)
        e_rel.insert(0, student_data.get("religion", "Islam"))
        e_rel.grid(row=5, column=3, sticky="ew", padx=10, pady=5)

        # Section 2 Header
        ctk.CTkLabel(scroll, text="2. PARENT & GUARDIAN DETAILS", font=ThemeConfig.get_font(11, "bold"), text_color=ThemeConfig.SECONDARY[1]).grid(row=6, column=0, columnspan=4, sticky="w", padx=10, pady=(16, 8))

        # Father Name & Phone
        ctk.CTkLabel(scroll, text="Father Name *", font=ThemeConfig.get_font(11, "bold")).grid(row=7, column=0, sticky="w", padx=10, pady=5)
        e_father = ctk.CTkEntry(scroll)
        e_father.insert(0, student_data.get("father_name", ""))
        e_father.grid(row=7, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(scroll, text="Father Phone *", font=ThemeConfig.get_font(11, "bold")).grid(row=7, column=2, sticky="w", padx=10, pady=5)
        e_fphone = ctk.CTkEntry(scroll)
        e_fphone.insert(0, student_data.get("father_phone", ""))
        e_fphone.grid(row=7, column=3, sticky="ew", padx=10, pady=5)

        # Father CNIC & Occupation
        ctk.CTkLabel(scroll, text="Father CNIC", font=ThemeConfig.get_font(11, "bold")).grid(row=8, column=0, sticky="w", padx=10, pady=5)
        e_fcnic = ctk.CTkEntry(scroll)
        e_fcnic.insert(0, student_data.get("father_cnic_nid", "") or "")
        e_fcnic.grid(row=8, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(scroll, text="Father Occupation", font=ThemeConfig.get_font(11, "bold")).grid(row=8, column=2, sticky="w", padx=10, pady=5)
        e_focc = ctk.CTkEntry(scroll)
        e_focc.insert(0, student_data.get("father_occupation", "") or "")
        e_focc.grid(row=8, column=3, sticky="ew", padx=10, pady=5)

        # Mother Name & Emergency Contact
        ctk.CTkLabel(scroll, text="Mother Name", font=ThemeConfig.get_font(11, "bold")).grid(row=9, column=0, sticky="w", padx=10, pady=5)
        e_mother = ctk.CTkEntry(scroll)
        e_mother.insert(0, student_data.get("mother_name", "") or "")
        e_mother.grid(row=9, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(scroll, text="Emergency Phone", font=ThemeConfig.get_font(11, "bold")).grid(row=9, column=2, sticky="w", padx=10, pady=5)
        e_emphone = ctk.CTkEntry(scroll)
        e_emphone.insert(0, student_data.get("emergency_contact", "") or "")
        e_emphone.grid(row=9, column=3, sticky="ew", padx=10, pady=5)

        # Address
        ctk.CTkLabel(scroll, text="Residential Address", font=ThemeConfig.get_font(11, "bold")).grid(row=10, column=0, sticky="w", padx=10, pady=5)
        e_addr = ctk.CTkEntry(scroll)
        e_addr.insert(0, student_data.get("residential_address", "") or "")
        e_addr.grid(row=10, column=1, columnspan=3, sticky="ew", padx=10, pady=5)

        dialog_status = ctk.CTkLabel(dialog, text="", font=ThemeConfig.get_font(11, "bold"))
        dialog_status.pack(pady=4)

        # Action Buttons
        btn_bar = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 16))

        def save_student_edits():
            fn = e_fn.get().strip()
            ln = e_ln.get().strip()
            father = e_father.get().strip()
            fphone = e_fphone.get().strip()

            if not fn or not ln or not father or not fphone:
                dialog_status.configure(text="Please fill in all mandatory fields (*).", text_color=ThemeConfig.DANGER[1])
                return

            c_obj = next((c for c in self.classes_cache if c["name"] == e_class.get()), None)
            cid = c_obj["id"] if c_obj else 1
            secs = self.repo.get_sections_by_class(cid)
            sec_obj = next((s for s in secs if s["name"] == e_sec.get()), None)
            secid = sec_obj["id"] if sec_obj else (secs[0]["id"] if secs else 1)

            try:
                roll_val = int(e_roll.get().strip() or "1")
            except ValueError:
                roll_val = 1

            student_payload = {
                "first_name": fn,
                "last_name": ln,
                "gender": e_gender.get(),
                "date_of_birth": e_dob.get().strip() or "2015-01-01",
                "blood_group": e_bg.get(),
                "religion": e_rel.get().strip(),
                "status": e_status.get()
            }

            parent_payload = {
                "father_name": father,
                "father_phone": fphone,
                "father_occupation": e_focc.get().strip(),
                "father_cnic_nid": e_fcnic.get().strip(),
                "father_email": "",
                "mother_name": e_mother.get().strip(),
                "emergency_contact": e_emphone.get().strip() or fphone,
                "residential_address": e_addr.get().strip()
            }

            enrollment_payload = {
                "academic_session_id": student_data.get("academic_session_id", 1),
                "class_id": cid,
                "section_id": secid,
                "roll_number": roll_val
            }

            try:
                success = self.repo.update_student(student_id, student_payload, parent_payload, enrollment_payload)
                if success:
                    self._refresh_directory()
                    self.dir_count_lbl.configure(text=f"✔ Updated {fn} {ln} successfully!", text_color=ThemeConfig.SUCCESS[1])
                    dialog.destroy()
                else:
                    dialog_status.configure(text="Failed to update student record.", text_color=ThemeConfig.DANGER[1])
            except Exception as e:
                dialog_status.configure(text=f"Error: {str(e)}", text_color=ThemeConfig.DANGER[1])

        ctk.CTkButton(btn_bar, text="Cancel", width=90, fg_color=ThemeConfig.BG_CARD_ALT, text_color=ThemeConfig.TEXT_MAIN, command=dialog.destroy).pack(side="left")
        ctk.CTkButton(btn_bar, text="💾 Save Changes", font=ThemeConfig.get_font(12, "bold"), fg_color=ThemeConfig.PRIMARY, hover_color=ThemeConfig.PRIMARY_HOVER, command=save_student_edits).pack(side="right")

    def _open_student_status_dialog(self):
        """Allows marking student as Passed Out, Left, Transferred, or Active."""
        item = self.dir_table.get_selected_item()
        if not item or not item.get("id"):
            self.dir_count_lbl.configure(text="⚠ Select a student from the table first.", text_color=ThemeConfig.WARNING[1])
            return

        student_id = item["id"]
        student_data = self.repo.get_student_by_id(student_id)
        if not student_data:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"🚪 Update Student Status - {student_data['admission_number']}")
        dialog.geometry("450x390")
        dialog.grab_set()

        top_bar = ctk.CTkFrame(dialog, fg_color=ThemeConfig.BG_CARD_ALT, corner_radius=0)
        top_bar.pack(fill="x", padx=0, pady=0)
        ctk.CTkLabel(
            top_bar,
            text="STUDENT STATUS LIFECYCLE",
            font=ThemeConfig.get_font(13, "bold"),
            text_color=ThemeConfig.GOLD_ACCENT[1]
        ).pack(side="left", padx=20, pady=12)

        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=12)

        # Student info card
        info_box = ctk.CTkFrame(content, fg_color=ThemeConfig.BG_CARD, corner_radius=8, border_width=1, border_color=ThemeConfig.BORDER)
        info_box.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            info_box,
            text=f"Student: {student_data['first_name']} {student_data['last_name']}  •  Adm: {student_data['admission_number']}",
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.TEXT_MAIN
        ).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(
            info_box,
            text=f"Class: {student_data.get('class_name', '')}-{student_data.get('section_name', '')}  •  Current Status: {student_data.get('status', 'Active')}",
            font=ThemeConfig.get_font(10),
            text_color=ThemeConfig.TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkLabel(content, text="New Student Status:", font=ThemeConfig.get_font(11, "bold")).pack(anchor="w", pady=(4, 2))
        status_cb = ctk.CTkComboBox(content, values=["Passed Out", "Left / Struck Off", "Transferred", "Inactive", "Active"], height=34)
        status_cb.set("Passed Out" if student_data.get("status") == "Active" else student_data.get("status", "Passed Out"))
        status_cb.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(content, text="Leaving Certificate # / Reason / Remarks:", font=ThemeConfig.get_font(11, "bold")).pack(anchor="w", pady=(4, 2))
        remarks_entry = ctk.CTkEntry(content, height=34, placeholder_text="e.g., Passed Class 10 Matric Board / SLC #10492 issued")
        remarks_entry.pack(fill="x", pady=(0, 16))

        def save_status():
            new_st = status_cb.get().strip()
            rem = remarks_entry.get().strip()
            ok, msg = self.controller.change_student_status(student_id, new_st, rem)
            if ok:
                self.dir_count_lbl.configure(text=f"✔ {msg}", text_color=ThemeConfig.SUCCESS[1])
                dialog.destroy()
                self._refresh_directory()
            else:
                self.dir_count_lbl.configure(text=f"✖ {msg}", text_color=ThemeConfig.DANGER[1])

        btn_bar = ctk.CTkFrame(content, fg_color="transparent")
        btn_bar.pack(fill="x", pady=4)
        ctk.CTkButton(btn_bar, text="Cancel", font=ThemeConfig.get_font(11), fg_color=ThemeConfig.BG_CARD_ALT, hover_color=ThemeConfig.BG_HOVER, width=100, command=dialog.destroy).pack(side="left")
        ctk.CTkButton(btn_bar, text="✔ Update Status", font=ThemeConfig.get_font(11, "bold"), fg_color=ThemeConfig.PRIMARY, hover_color=ThemeConfig.PRIMARY_HOVER, width=140, command=save_status).pack(side="right")

    def _open_delete_student_dialog(self):
        """STEP 1 OF 2: Displays warning details and offers Left/Passed Out archival vs Permanent Deletion."""
        item = self.dir_table.get_selected_item()
        if not item or not item.get("id"):
            self.dir_count_lbl.configure(text="⚠ Select a student from the table to delete.", text_color=ThemeConfig.WARNING[1])
            return

        student_id = item["id"]
        student_data = self.repo.get_student_by_id(student_id)
        if not student_data:
            return

        d1 = ctk.CTkToplevel(self)
        d1.title("⚠️ Confirm Deletion / Withdrawal (Step 1 of 2)")
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

        # Target student details card
        card = ctk.CTkFrame(body, fg_color=ThemeConfig.BG_CARD, corner_radius=8, border_width=1, border_color=ThemeConfig.BORDER)
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card, text="TARGET STUDENT DETAILS:", font=ThemeConfig.get_font(10, "bold"), text_color=ThemeConfig.TEXT_MUTED).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(
            card,
            text=f"👤 {student_data['first_name']} {student_data['last_name']}",
            font=ThemeConfig.get_font(13, "bold"),
            text_color=ThemeConfig.TEXT_MAIN
        ).pack(anchor="w", padx=12, pady=1)
        ctk.CTkLabel(
            card,
            text=f"Adm No: {student_data['admission_number']}  •  Class: {student_data.get('class_name', '')}-{student_data.get('section_name', '')} (Roll #{student_data.get('roll_number', '-')})",
            font=ThemeConfig.get_font(11),
            text_color=ThemeConfig.GOLD_ACCENT[1]
        ).pack(anchor="w", padx=12, pady=1)
        ctk.CTkLabel(
            card,
            text=f"Father: {student_data.get('father_name', '-')}  •  Phone: {student_data.get('father_phone', '-')}",
            font=ThemeConfig.get_font(10),
            text_color=ThemeConfig.TEXT_MUTED
        ).pack(anchor="w", padx=12, pady=(1, 8))

        # Warning advice text
        notice = ctk.CTkFrame(body, fg_color=ThemeConfig.BG_CARD_ALT, corner_radius=6)
        notice.pack(fill="x", pady=(0, 16))
        ctk.CTkLabel(
            notice,
            text="ℹ️ In school administration, students who leave or pass out should\n"
                 "preferably be marked as 'Passed Out' or 'Left' to preserve historical\n"
                 "exam transcripts, fee invoices, and attendance records.",
            font=ThemeConfig.get_font(10),
            text_color=ThemeConfig.TEXT_MAIN,
            justify="left"
        ).pack(padx=10, pady=8)

        def proceed_to_step2():
            d1.destroy()
            self._open_permanent_delete_student_step2(student_data)

        def proceed_to_status():
            d1.destroy()
            self._open_student_status_dialog()

        # Action Buttons
        ctk.CTkButton(
            body,
            text="🚪 Mark as Left / Passed Out (Archive - Recommended)",
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

    def _open_permanent_delete_student_step2(self, student_data: dict):
        """STEP 2 OF 2: Strict Double Confirmation requiring typing DELETE."""
        d2 = ctk.CTkToplevel(self)
        d2.title("🚨 CRITICAL: Permanent Deletion Verification (Step 2 of 2)")
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

        st_name = f"{student_data['first_name']} {student_data['last_name']} ({student_data['admission_number']})"
        ctk.CTkLabel(
            body,
            text=f"You are about to PERMANENTLY ERASE:\n{st_name}",
            font=ThemeConfig.get_font(12, "bold"),
            text_color=ThemeConfig.DANGER[1],
            justify="center"
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            body,
            text="This action CANNOT BE UNDONE. All associated attendance records,\n"
                 "fee invoices, payment receipts, and exam marks will be permanently\n"
                 "wiped from the database.",
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
            ok, msg = self.controller.delete_student(student_data["id"])
            if ok:
                self.dir_count_lbl.configure(text=f"✔ {msg}", text_color=ThemeConfig.SUCCESS[1])
                d2.destroy()
                self._refresh_directory()
            else:
                self.dir_count_lbl.configure(text=f"✖ {msg}", text_color=ThemeConfig.DANGER[1])

        btn_purge = ctk.CTkButton(
            body,
            text="🚨 Permanently Delete Student Record",
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

    # -------------------------------------------------------------------------
    # TAB 2: NEW STUDENT REGISTRATION WIZARD
    # -------------------------------------------------------------------------
    def _init_register_tab(self):
        tab = self.tab_register
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        # --- Card 1: Student Demographics (Left Column) ---
        c1 = ctk.CTkFrame(scroll, fg_color=ThemeConfig.BG_CARD, corner_radius=12, border_width=1, border_color=ThemeConfig.BORDER)
        c1.grid(row=0, column=0, padx=(0, 10), pady=4, sticky="nsew")
        c1.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(c1, text="1. STUDENT DEMOGRAPHICS", font=ThemeConfig.get_font(12, "bold"), text_color=ThemeConfig.PRIMARY[1]).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 12))

        # First Name
        ctk.CTkLabel(c1, text="First Name *", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=0, sticky="w", padx=16, pady=6)
        self.reg_fn = ctk.CTkEntry(c1, placeholder_text="e.g. Muhammad")
        self.reg_fn.grid(row=1, column=1, sticky="ew", padx=16, pady=6)

        # Last Name
        ctk.CTkLabel(c1, text="Last Name *", font=ThemeConfig.get_font(11, "bold")).grid(row=2, column=0, sticky="w", padx=16, pady=6)
        self.reg_ln = ctk.CTkEntry(c1, placeholder_text="e.g. Ali")
        self.reg_ln.grid(row=2, column=1, sticky="ew", padx=16, pady=6)

        # Gender
        ctk.CTkLabel(c1, text="Gender *", font=ThemeConfig.get_font(11, "bold")).grid(row=3, column=0, sticky="w", padx=16, pady=6)
        self.reg_gender = ctk.CTkComboBox(c1, values=["Male", "Female", "Other"])
        self.reg_gender.set("Male")
        self.reg_gender.grid(row=3, column=1, sticky="ew", padx=16, pady=6)

        # Date of Birth
        ctk.CTkLabel(c1, text="Date of Birth *", font=ThemeConfig.get_font(11, "bold")).grid(row=4, column=0, sticky="w", padx=16, pady=6)
        self.reg_dob = ctk.CTkEntry(c1, placeholder_text="YYYY-MM-DD (e.g. 2016-05-14)")
        self.reg_dob.insert(0, "2018-01-01")
        self.reg_dob.grid(row=4, column=1, sticky="ew", padx=16, pady=6)

        # Blood Group
        ctk.CTkLabel(c1, text="Blood Group", font=ThemeConfig.get_font(11)).grid(row=5, column=0, sticky="w", padx=16, pady=6)
        self.reg_bg = ctk.CTkComboBox(c1, values=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-", "Unknown"])
        self.reg_bg.set("B+")
        self.reg_bg.grid(row=5, column=1, sticky="ew", padx=16, pady=6)

        # Religion
        ctk.CTkLabel(c1, text="Religion", font=ThemeConfig.get_font(11)).grid(row=6, column=0, sticky="w", padx=16, pady=(6, 16))
        self.reg_rel = ctk.CTkEntry(c1)
        self.reg_rel.insert(0, "Islam")
        self.reg_rel.grid(row=6, column=1, sticky="ew", padx=16, pady=(6, 16))

        # --- Card 2: Parent / Guardian Info (Right Column) ---
        c2 = ctk.CTkFrame(scroll, fg_color=ThemeConfig.BG_CARD, corner_radius=12, border_width=1, border_color=ThemeConfig.BORDER)
        c2.grid(row=0, column=1, padx=(10, 0), pady=4, sticky="nsew")
        c2.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(c2, text="2. PARENT & GUARDIAN DETAILS", font=ThemeConfig.get_font(12, "bold"), text_color=ThemeConfig.SECONDARY[1]).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(16, 12))

        # Father Name
        ctk.CTkLabel(c2, text="Father Name *", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=0, sticky="w", padx=16, pady=6)
        self.reg_p_name = ctk.CTkEntry(c2, placeholder_text="e.g. Tariq Mehmood")
        self.reg_p_name.grid(row=1, column=1, sticky="ew", padx=16, pady=6)

        # Father CNIC / NID
        ctk.CTkLabel(c2, text="Father CNIC", font=ThemeConfig.get_font(11)).grid(row=2, column=0, sticky="w", padx=16, pady=6)
        self.reg_p_cnic = ctk.CTkEntry(c2, placeholder_text="35201-XXXXXXXX-X")
        self.reg_p_cnic.grid(row=2, column=1, sticky="ew", padx=16, pady=6)

        # Primary Phone
        ctk.CTkLabel(c2, text="Contact Phone *", font=ThemeConfig.get_font(11, "bold")).grid(row=3, column=0, sticky="w", padx=16, pady=6)
        self.reg_p_phone = ctk.CTkEntry(c2, placeholder_text="0300-1234567")
        self.reg_p_phone.grid(row=3, column=1, sticky="ew", padx=16, pady=6)

        # Emergency Contact
        ctk.CTkLabel(c2, text="Emergency Phone *", font=ThemeConfig.get_font(11, "bold")).grid(row=4, column=0, sticky="w", padx=16, pady=6)
        self.reg_p_emergency = ctk.CTkEntry(c2, placeholder_text="Alternative contact number")
        self.reg_p_emergency.grid(row=4, column=1, sticky="ew", padx=16, pady=6)

        # Residential Address
        ctk.CTkLabel(c2, text="Residential Address *", font=ThemeConfig.get_font(11, "bold")).grid(row=5, column=0, sticky="w", padx=16, pady=6)
        self.reg_p_addr = ctk.CTkEntry(c2, placeholder_text="House #, Street, City")
        self.reg_p_addr.grid(row=5, column=1, sticky="ew", padx=16, pady=6)

        # Father Occupation
        ctk.CTkLabel(c2, text="Occupation", font=ThemeConfig.get_font(11)).grid(row=6, column=0, sticky="w", padx=16, pady=(6, 16))
        self.reg_p_occ = ctk.CTkEntry(c2, placeholder_text="e.g. Businessman / Engineer")
        self.reg_p_occ.grid(row=6, column=1, sticky="ew", padx=16, pady=(6, 16))

        # --- Card 3: Class Assignment & Enrollment (Spans full width) ---
        c3 = ctk.CTkFrame(scroll, fg_color=ThemeConfig.BG_CARD, corner_radius=12, border_width=1, border_color=ThemeConfig.BORDER)
        c3.grid(row=1, column=0, columnspan=2, pady=16, sticky="ew")
        c3.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(c3, text="3. CLASS & ACADEMIC SESSION ASSIGNMENT", font=ThemeConfig.get_font(12, "bold"), text_color=ThemeConfig.GOLD_ACCENT[1]).grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=(16, 12))

        # Class
        ctk.CTkLabel(c3, text="Assigned Class *", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=0, sticky="w", padx=16, pady=8)
        class_names = [c["name"] for c in self.classes_cache]
        self.reg_class = ctk.CTkComboBox(c3, values=class_names, command=self._on_reg_class_change)
        if class_names:
            self.reg_class.set(class_names[0])
        self.reg_class.grid(row=1, column=1, sticky="ew", padx=16, pady=8)

        # Section
        ctk.CTkLabel(c3, text="Section *", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=2, sticky="w", padx=16, pady=8)
        self.reg_sec = ctk.CTkComboBox(c3, values=["A", "B"])
        self.reg_sec.set("A")
        self.reg_sec.grid(row=1, column=3, sticky="ew", padx=16, pady=8)

        # Save Button & Status Label
        btn_bar = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_bar.grid(row=2, column=0, columnspan=2, pady=(0, 20), sticky="ew")

        self.reg_status_lbl = ctk.CTkLabel(btn_bar, text="", font=ThemeConfig.get_font(12, "bold"))
        self.reg_status_lbl.pack(side="left", padx=16)

        save_btn = ctk.CTkButton(
            btn_bar,
            text="✔ Confirm & Register Student",
            font=ThemeConfig.get_font(13, "bold"),
            fg_color=ThemeConfig.PRIMARY,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            height=44,
            width=260,
            command=self._do_register
        )
        save_btn.pack(side="right", padx=16)

        self._on_reg_class_change(self.reg_class.get())

    def _on_reg_class_change(self, class_name: str):
        c_id = next((c["id"] for c in self.classes_cache if c["name"] == class_name), None)
        if c_id:
            sections = self.repo.get_sections_by_class(c_id)
            sec_names = [s["name"] for s in sections] or ["A", "B"]
            self.reg_sec.configure(values=sec_names)
            self.reg_sec.set(sec_names[0])

    def _do_register(self):
        c_name = self.reg_class.get()
        c_obj = next((c for c in self.classes_cache if c["name"] == c_name), None)
        if not c_obj:
            self.reg_status_lbl.configure(text="Please select a valid class.", text_color=ThemeConfig.DANGER[1])
            return

        c_id = c_obj["id"]
        sections = self.repo.get_sections_by_class(c_id)
        sec_name = self.reg_sec.get()
        s_obj = next((s for s in sections if s["name"] == sec_name), None)
        sec_id = s_obj["id"] if s_obj else (sections[0]["id"] if sections else 1)

        session = self.repo.get_current_session()
        session_id = session["id"] if session else 1

        student_dict = {
            "first_name": self.reg_fn.get().strip(),
            "last_name": self.reg_ln.get().strip(),
            "gender": self.reg_gender.get(),
            "date_of_birth": self.reg_dob.get().strip(),
            "blood_group": self.reg_bg.get(),
            "religion": self.reg_rel.get().strip(),
            "registration_date": date.today().isoformat()
        }

        parent_dict = {
            "father_name": self.reg_p_name.get().strip(),
            "father_cnic_nid": self.reg_p_cnic.get().strip(),
            "father_phone": self.reg_p_phone.get().strip(),
            "emergency_contact": self.reg_p_emergency.get().strip() or self.reg_p_phone.get().strip(),
            "residential_address": self.reg_p_addr.get().strip() or "Civil Lines, Education Zone",
            "father_occupation": self.reg_p_occ.get().strip()
        }

        success, msg, sid = self.controller.register_new_student(
            student_dict=student_dict,
            parent_dict=parent_dict,
            class_id=c_id,
            section_id=sec_id,
            session_id=session_id
        )

        if success:
            self.reg_status_lbl.configure(text=f"✔ {msg}", text_color=ThemeConfig.SUCCESS[1])
            self.reg_fn.delete(0, "end")
            self.reg_ln.delete(0, "end")
            self.reg_p_name.delete(0, "end")
            self.reg_p_phone.delete(0, "end")
            self._refresh_directory()
        else:
            self.reg_status_lbl.configure(text=f"✖ {msg}", text_color=ThemeConfig.DANGER[1])

    # -------------------------------------------------------------------------
    # TAB 3: END-OF-YEAR PROMOTION LOGIC
    # -------------------------------------------------------------------------
    def _init_promote_tab(self):
        tab = self.tab_promote
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        top_card = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=12, border_width=1, border_color=ThemeConfig.BORDER)
        top_card.grid(row=0, column=0, padx=4, pady=(4, 12), sticky="ew")

        ctk.CTkLabel(top_card, text="Promote Class Cohort to Next Academic Year", font=ThemeConfig.get_font(13, "bold"), text_color=ThemeConfig.TEXT_MAIN).pack(anchor="w", padx=16, pady=(12, 6))
        ctk.CTkLabel(top_card, text="Promotes active students from their current class to the next successive grade. Class 10 students graduate automatically.", font=ThemeConfig.get_font(11), text_color=ThemeConfig.TEXT_MUTED).pack(anchor="w", padx=16, pady=(0, 10))

        controls = ctk.CTkFrame(top_card, fg_color="transparent")
        controls.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(controls, text="Source Class:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(0, 6))
        class_names = [c["name"] for c in self.classes_cache]
        self.prom_source_class = ctk.CTkComboBox(controls, values=class_names, command=self._refresh_promote_table)
        if class_names:
            self.prom_source_class.set(class_names[0])
        self.prom_source_class.pack(side="left", padx=(0, 20))

        # Promote Action Button
        self.prom_btn = ctk.CTkButton(
            controls,
            text="🚀 Execute Promotion for All in Class",
            font=ThemeConfig.get_font(12, "bold"),
            fg_color=ThemeConfig.PRIMARY,
            command=self._do_promotion
        )
        self.prom_btn.pack(side="right")

        self.prom_status = ctk.CTkLabel(controls, text="", font=ThemeConfig.get_font(11, "bold"))
        self.prom_status.pack(side="right", padx=16)

        # Table showing students in source class
        cols = [
            ("admission_number", "Adm No", 120),
            ("full_name", "Student Name", 200),
            ("class_name", "Current Class", 120),
            ("section_name", "Sec", 80),
            ("roll_number", "Roll #", 80),
            ("next_class", "Target Action", 160)
        ]
        self.prom_table = DataTable(tab, columns=cols)
        self.prom_table.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="nsew")

        self._refresh_promote_table(self.prom_source_class.get())

    def _refresh_promote_table(self, source_class_name: str):
        c_obj = next((c for c in self.classes_cache if c["name"] == source_class_name), None)
        if not c_obj:
            return

        c_id = c_obj["id"]
        curr_order = c_obj["numeric_order"]
        is_last_class = (curr_order >= 13)

        target_class = next((c for c in self.classes_cache if c["numeric_order"] == curr_order + 1), None)
        target_name = "🎓 Graduate from School" if is_last_class else f"Promote to {target_class['name'] if target_class else 'Next Class'}"

        students = self.repo.search_students(class_id=c_id, status="Active")
        formatted = []
        for s in students:
            formatted.append({
                "id": s["id"],
                "admission_number": s["admission_number"],
                "full_name": f"{s['first_name']} {s['last_name']}",
                "class_name": s.get("class_name", ""),
                "section_name": s.get("section_name", ""),
                "roll_number": s.get("roll_number", ""),
                "next_class": target_name
            })
        self.prom_table.populate(formatted)

    def _do_promotion(self):
        c_name = self.prom_source_class.get()
        c_obj = next((c for c in self.classes_cache if c["name"] == c_name), None)
        if not c_obj:
            return

        curr_order = c_obj["numeric_order"]
        is_graduate = (curr_order >= 13)
        target_class = next((c for c in self.classes_cache if c["numeric_order"] == curr_order + 1), None)
        target_class_id = target_class["id"] if target_class else None

        target_sec_id = 1
        if target_class_id:
            secs = self.repo.get_sections_by_class(target_class_id)
            if secs:
                target_sec_id = secs[0]["id"]

        session = self.repo.get_current_session()
        target_session_id = session["id"] if session else 1

        students = self.repo.search_students(class_id=c_obj["id"], status="Active")
        sids = [s["id"] for s in students]

        if not sids:
            self.prom_status.configure(text="No active students found in this class.", text_color=ThemeConfig.WARNING[1])
            return

        success, msg, count = self.controller.execute_annual_promotion(
            source_class_id=c_obj["id"],
            target_class_id=target_class_id,
            target_section_id=target_sec_id,
            target_session_id=target_session_id,
            student_ids=sids,
            is_graduation=is_graduate
        )

        if success:
            self.prom_status.configure(text=f"✔ {msg}", text_color=ThemeConfig.SUCCESS[1])
            self._refresh_promote_table(c_name)
            self._refresh_directory()
        else:
            self.prom_status.configure(text=f"✖ {msg}", text_color=ThemeConfig.DANGER[1])

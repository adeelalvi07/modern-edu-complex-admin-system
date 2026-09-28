"""
Academic Examination & Statistical Insights View.
Features:
- Class Subjects Setup (Admin can add/remove subjects per class with custom max/pass marks)
- Fast Marks Entry Grid with Instant Auto-Grading (A+, A, B, C, D, F) & Absent Handling
- Interactive All-Subject Student Marks Viewer with Multi-Filter (Exam, Class, Sec, Student, Search)
- Aggregate Academic KPIs (Total Marks, Percentage, Overall Grade, Result Status)
- Statistical Dashboard: Mean, Variance, Std Deviation, Pass/Fail Probabilities
- Official Report Card PDF Generator
- Centered, Straight, Low-Opacity Campus Watermark Background
"""
import os
import customtkinter as ctk
from config.theme_config import ThemeConfig
from src.views.components.data_table import DataTable
from src.views.components.stat_card import StatCard
from src.views.components.watermark import WatermarkManager
from src.controllers.exam_controller import ExamController, calculate_grade
from src.repositories.exam_repository import ExamRepository
from src.repositories.student_repository import StudentRepository
from src.repositories.staff_repository import StaffRepository
from src.services.pdf_generator import PDFGenerator

class ExamView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=ThemeConfig.BG_MAIN, **kwargs)
        self.controller = ExamController()
        self.repo = ExamRepository()
        self.student_repo = StudentRepository()
        self.staff_repo = StaffRepository()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Apply centered, straight watermark in background
        WatermarkManager.apply(self, width=820, height=560)

        self._ensure_default_exam()
        self._build_tabs()

    def _ensure_default_exam(self):
        """Ensures at least one exam term exists."""
        session = self.student_repo.get_current_session()
        session_id = session["id"] if session else 1
        exams = self.repo.get_all_exams(session_id)
        if not exams:
            self.repo.create_exam(session_id, "First Term Examination 2026", "2026-09-01", "2026-09-15")

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=ThemeConfig.BG_MAIN,
            segmented_button_selected_color=ThemeConfig.PRIMARY[1],
            segmented_button_selected_hover_color=ThemeConfig.PRIMARY_HOVER[1]
        )
        self.tabview.grid(row=0, column=0, padx=20, pady=16, sticky="nsew")

        self.tab_marks = self.tabview.add("📝 Marks Entry")
        self.tab_report = self.tabview.add("📋 Student Marks & Report Cards")
        self.tab_subjects = self.tabview.add("📚 Class Subjects Setup")
        self.tab_stats = self.tabview.add("📊 Statistical Insights & Probabilities")

        self._init_marks_tab()
        self._init_all_marks_tab()
        self._init_subjects_tab()
        self._init_stats_tab()

    # -------------------------------------------------------------------------
    # TAB 1: MARKS ENTRY GRID
    # -------------------------------------------------------------------------
    def _init_marks_tab(self):
        tab = self.tab_marks
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        bar.grid(row=0, column=0, padx=4, pady=(4, 12), sticky="ew")

        # Exam selector
        session = self.student_repo.get_current_session()
        self.exams_cache = self.repo.get_all_exams(session["id"] if session else 1)
        exam_names = [e["name"] for e in self.exams_cache] or ["First Term Examination 2026"]
        ctk.CTkLabel(bar, text="Exam:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(12, 4), pady=10)
        self.exam_cb = ctk.CTkComboBox(bar, values=exam_names, width=160, command=lambda v: self._load_marks_sheet())
        self.exam_cb.set(exam_names[0])
        self.exam_cb.pack(side="left", padx=4, pady=10)

        # Class
        self.classes_cache = self.student_repo.get_all_classes()
        class_names = [c["name"] for c in self.classes_cache]
        ctk.CTkLabel(bar, text="Class:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(8, 4), pady=10)
        self.exam_class_cb = ctk.CTkComboBox(bar, values=class_names, command=self._on_class_change, width=110)
        if class_names:
            self.exam_class_cb.set(class_names[0])
        self.exam_class_cb.pack(side="left", padx=4, pady=10)

        # Section
        ctk.CTkLabel(bar, text="Sec:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(8, 4), pady=10)
        self.exam_sec_cb = ctk.CTkComboBox(bar, values=["A", "B"], width=65, command=lambda v: self._load_marks_sheet())
        self.exam_sec_cb.set("A")
        self.exam_sec_cb.pack(side="left", padx=4, pady=10)

        # Subject
        ctk.CTkLabel(bar, text="Subject:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(8, 4), pady=10)
        self.exam_subj_cb = ctk.CTkComboBox(bar, values=["Mathematics", "English", "Science"], width=140, command=lambda v: self._load_marks_sheet())
        self.exam_subj_cb.pack(side="left", padx=4, pady=10)

        load_btn = ctk.CTkButton(
            bar,
            text="🔄 Refresh",
            font=ThemeConfig.get_font(11, "bold"),
            width=80,
            fg_color=ThemeConfig.PRIMARY,
            command=self._load_marks_sheet
        )
        load_btn.pack(side="left", padx=8, pady=10)

        save_btn = ctk.CTkButton(
            bar,
            text="💾 Save Marks",
            font=ThemeConfig.get_font(12, "bold"),
            fg_color=ThemeConfig.SECONDARY,
            hover_color=ThemeConfig.SECONDARY_HOVER,
            command=self._save_marks_sheet
        )
        save_btn.pack(side="right", padx=12, pady=10)

        self.marks_feedback = ctk.CTkLabel(bar, text="", font=ThemeConfig.get_font(11, "bold"))
        self.marks_feedback.pack(side="right", padx=10)

        cols = [
            ("roll_number", "Roll #", 70),
            ("admission_number", "Adm #", 110),
            ("student_name", "Student Name", 200),
            ("marks_obtained", "Marks Obtained (Click to Edit)", 220),
            ("grade", "Grade", 80),
            ("remarks", "Remarks", 150)
        ]
        self.marks_table = DataTable(tab, columns=cols, on_double_click=self._edit_marks_dialog)
        self.marks_table.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="nsew")

        self.current_marks_data = []
        if class_names:
            self._on_class_change(class_names[0])
        else:
            self._load_marks_sheet()

    def _on_class_change(self, class_name: str):
        c_obj = next((c for c in self.classes_cache if c["name"] == class_name), None)
        if c_obj:
            subjs = self.repo.get_subjects_by_class(c_obj["id"])
            if not subjs:
                self.repo.seed_default_subjects_for_class(c_obj["id"], c_obj["name"])
                subjs = self.repo.get_subjects_by_class(c_obj["id"])

            s_names = [s["subject_name"] for s in subjs] if subjs else ["(No subjects configured)"]
            self.exam_subj_cb.configure(values=s_names)
            self.exam_subj_cb.set(s_names[0])

            secs = self.student_repo.get_sections_by_class(c_obj["id"])
            sec_names = [s["name"] for s in secs] if secs else ["A"]
            self.exam_sec_cb.configure(values=sec_names)
            if sec_names:
                self.exam_sec_cb.set(sec_names[0])

        self._load_marks_sheet()

    def _load_marks_sheet(self):
        c_name = self.exam_class_cb.get()
        c_obj = next((c for c in self.classes_cache if c["name"] == c_name), None)
        if not c_obj:
            return

        session = self.student_repo.get_current_session()
        session_id = session["id"] if session else 1

        exam_name = self.exam_cb.get()
        exam_obj = next((e for e in self.exams_cache if e["name"] == exam_name), None)
        exam_id = exam_obj["id"] if exam_obj else 1

        subjs = self.repo.get_subjects_by_class(c_obj["id"])
        subj_name = self.exam_subj_cb.get()
        subj_obj = next((s for s in subjs if s["subject_name"] == subj_name), None)
        if not subj_obj:
            self.marks_table.populate([])
            self.marks_feedback.configure(
                text=f"⚠️ No subjects configured for {c_name}. Use 'Class Subjects Setup' tab.",
                text_color=ThemeConfig.WARNING[1]
            )
            return

        max_m = float(subj_obj.get("total_marks") or 100.0)
        pass_m = float(subj_obj.get("passing_marks") or 40.0)
        self.active_max_marks = max_m
        self.active_pass_marks = pass_m

        self.repo.schedule_exam_subject(exam_id, c_obj["id"], subj_obj["id"], max_marks=max_m, passing_marks=pass_m)
        exam_subjs = self.repo.get_exam_subjects(exam_id, c_obj["id"])
        target_es = next((es for es in exam_subjs if es["subject_id"] == subj_obj["id"]), None)
        if not target_es:
            return

        self.active_es_id = target_es["id"]
        secs = self.student_repo.get_sections_by_class(c_obj["id"])
        selected_sec = self.exam_sec_cb.get() if hasattr(self, "exam_sec_cb") else "A"
        sec_obj = next((s for s in secs if s["name"] == selected_sec), None)
        sec_id = sec_obj["id"] if sec_obj else (secs[0]["id"] if secs else 1)

        records = self.repo.get_students_for_marking(self.active_es_id, c_obj["id"], sec_id, session_id)
        self.current_marks_data = []
        formatted = []
        for r in records:
            raw_m = r.get("marks_obtained")
            marks = float(raw_m) if raw_m is not None else 0.0
            is_abs = bool(r.get("is_absent", False))
            pct = (marks / max_m) * 100.0 if max_m > 0 else 0.0
            st = {
                "student_id": r["student_id"],
                "roll_number": r.get("roll_number", ""),
                "admission_number": r["admission_number"],
                "student_name": f"{r['first_name']} {r['last_name']}",
                "marks_obtained": "ABS" if is_abs else (str(int(marks)) if marks % 1 == 0 else f"{marks:.1f}"),
                "is_absent": is_abs,
                "grade": "ABS" if is_abs else (r.get("grade") or calculate_grade(pct)),
                "remarks": r.get("teacher_remarks") or ""
            }
            self.current_marks_data.append(st)
            formatted.append(st)

        self.marks_table.populate(formatted)
        sec_label = sec_obj["name"] if sec_obj else selected_sec
        self.marks_feedback.configure(
            text=f"Loaded {len(formatted)} students ({c_name} - Sec {sec_label} - {subj_name} | Max: {max_m:.0f}).",
            text_color=ThemeConfig.TEXT_MUTED
        )

    def _edit_marks_dialog(self, row: dict):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Marks")
        dialog.geometry("340x270")
        dialog.grab_set()

        max_m = getattr(self, "active_max_marks", 100.0)

        ctk.CTkLabel(dialog, text=f"Marks for {row['student_name']}", font=ThemeConfig.get_font(12, "bold")).pack(pady=(16, 4))
        ctk.CTkLabel(dialog, text=f"Roll #{row['roll_number']} | Max Marks: {max_m:.0f}", font=ThemeConfig.get_font(11), text_color=ThemeConfig.TEXT_MUTED).pack(pady=(0, 10))

        marks_entry = ctk.CTkEntry(dialog, font=ThemeConfig.get_font(13))
        marks_entry.insert(0, str(row.get("marks_obtained", "0") if row.get("marks_obtained") != "ABS" else "0"))
        marks_entry.pack(fill="x", padx=40, pady=(0, 8))

        absent_var = ctk.BooleanVar(value=row.get("is_absent", False))
        absent_chk = ctk.CTkCheckBox(dialog, text="Mark as Absent (ABS)", variable=absent_var, font=ThemeConfig.get_font(11))
        absent_chk.pack(padx=40, pady=(0, 12), anchor="w")

        def save_mark():
            is_abs = absent_var.get()
            if is_abs:
                m = 0.0
                grd = "ABS"
            else:
                try:
                    m = float(marks_entry.get().strip())
                    m = max(0.0, min(max_m, m))
                except ValueError:
                    return
                pct = (m / max_m) * 100.0 if max_m > 0 else 0.0
                grd = calculate_grade(pct)

            for r in self.current_marks_data:
                if r["student_id"] == row["student_id"]:
                    r["marks_obtained"] = "ABS" if is_abs else (str(int(m)) if m % 1 == 0 else f"{m:.1f}")
                    r["is_absent"] = is_abs
                    r["grade"] = grd
                    break

            self.marks_table.populate(self.current_marks_data)
            dialog.destroy()

        ctk.CTkButton(dialog, text="Update Mark", font=ThemeConfig.get_font(11, "bold"), fg_color=ThemeConfig.SECONDARY, command=save_mark).pack(fill="x", padx=40, pady=6)
        marks_entry.focus()

    def _save_marks_sheet(self):
        if not hasattr(self, "active_es_id") or not self.current_marks_data:
            return

        saved = self.repo.save_batch_marks(self.active_es_id, self.current_marks_data, entered_by=1)
        self.marks_feedback.configure(text=f"✔ Saved {saved} student grades!", text_color=ThemeConfig.SUCCESS[1])

        # Refresh Tab 2 marks if active
        if hasattr(self, "rep_student_cb"):
            self._load_current_student_all_marks()

    # -------------------------------------------------------------------------
    # TAB 2: STUDENT MARKS & ALL-SUBJECT VIEW WITH COMPREHENSIVE FILTERS
    # -------------------------------------------------------------------------
    def _init_all_marks_tab(self):
        tab = self.tab_report
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # 1. Filter Bar
        bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        bar.grid(row=0, column=0, padx=4, pady=(4, 10), sticky="ew")

        # Exam selector
        exam_names = [e["name"] for e in self.exams_cache] or ["First Term Examination 2026"]
        ctk.CTkLabel(bar, text="Exam:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(10, 4), pady=8)
        self.rep_exam_cb = ctk.CTkComboBox(bar, values=exam_names, width=155, command=lambda v: self._load_current_student_all_marks())
        self.rep_exam_cb.set(exam_names[0])
        self.rep_exam_cb.pack(side="left", padx=2, pady=8)

        # Class selector
        class_names = [c["name"] for c in self.classes_cache]
        ctk.CTkLabel(bar, text="Class:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(8, 4), pady=8)
        self.rep_class_cb = ctk.CTkComboBox(bar, values=class_names, width=110, command=self._on_rep_class_or_sec_change)
        if class_names:
            self.rep_class_cb.set(class_names[0])
        self.rep_class_cb.pack(side="left", padx=2, pady=8)

        # Section selector
        ctk.CTkLabel(bar, text="Sec:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(8, 4), pady=8)
        self.rep_sec_cb = ctk.CTkComboBox(bar, values=["A", "B", "All"], width=65, command=self._on_rep_class_or_sec_change)
        self.rep_sec_cb.set("A")
        self.rep_sec_cb.pack(side="left", padx=2, pady=8)

        # Student selector
        ctk.CTkLabel(bar, text="Student:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(8, 4), pady=8)
        self.rep_student_cb = ctk.CTkComboBox(bar, values=[], width=230, command=lambda v: self._on_rep_student_selected())
        self.rep_student_cb.pack(side="left", padx=2, pady=8)

        # Quick Search Box
        self.rep_search_entry = ctk.CTkEntry(bar, placeholder_text="🔍 Search student...", width=140, height=32, font=ThemeConfig.get_font(11))
        self.rep_search_entry.pack(side="left", padx=(8, 4), pady=8)
        self.rep_search_entry.bind("<KeyRelease>", self._on_rep_search_keyup)

        # Action Buttons on right
        print_btn = ctk.CTkButton(
            bar,
            text="🖨️ PDF Report Card",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.PRIMARY,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            height=32,
            command=self._generate_pdf_report_card
        )
        print_btn.pack(side="right", padx=(4, 10), pady=8)

        refresh_btn = ctk.CTkButton(
            bar,
            text="🔄 Refresh",
            font=ThemeConfig.get_font(11, "bold"),
            width=75,
            height=32,
            command=self._refresh_report_view
        )
        refresh_btn.pack(side="right", padx=4, pady=8)

        # 2. Student Details Banner & KPI Cards Row
        summary_box = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        summary_box.grid(row=1, column=0, padx=4, pady=(0, 10), sticky="ew")
        summary_box.grid_columnconfigure(0, weight=3)
        summary_box.grid_columnconfigure(1, weight=1)
        summary_box.grid_columnconfigure(2, weight=1)
        summary_box.grid_columnconfigure(3, weight=1)
        summary_box.grid_columnconfigure(4, weight=1)

        # Left Info card
        info_frame = ctk.CTkFrame(summary_box, fg_color="transparent")
        info_frame.grid(row=0, column=0, padx=14, pady=10, sticky="w")

        self.rep_student_name_lbl = ctk.CTkLabel(
            info_frame,
            text="Select a student to view all subject marks",
            font=ThemeConfig.get_font(14, "bold"),
            text_color=ThemeConfig.PRIMARY[1]
        )
        self.rep_student_name_lbl.pack(anchor="w")

        self.rep_student_meta_lbl = ctk.CTkLabel(
            info_frame,
            text="Use the filters above to switch Class, Section, and Student.",
            font=ThemeConfig.get_font(11),
            text_color=ThemeConfig.TEXT_MUTED
        )
        self.rep_student_meta_lbl.pack(anchor="w", pady=(2, 0))

        # 4 KPI Stat Cards
        self.kpi_total_marks = StatCard(summary_box, title="Total Marks", value="--", subtitle="Obtained / Maximum", accent_color=ThemeConfig.PRIMARY[1])
        self.kpi_total_marks.grid(row=0, column=1, padx=4, pady=8, sticky="ew")

        self.kpi_percentage = StatCard(summary_box, title="Percentage", value="--", subtitle="Aggregate Score", accent_color=ThemeConfig.SECONDARY[1])
        self.kpi_percentage.grid(row=0, column=2, padx=4, pady=8, sticky="ew")

        self.kpi_grade = StatCard(summary_box, title="Overall Grade", value="--", subtitle="Letter Scale", accent_color=ThemeConfig.GOLD_ACCENT[1])
        self.kpi_grade.grid(row=0, column=3, padx=4, pady=8, sticky="ew")

        self.kpi_status = StatCard(summary_box, title="Result Status", value="--", subtitle="Academic Standing", accent_color=ThemeConfig.SUCCESS[1])
        self.kpi_status.grid(row=0, column=4, padx=(4, 10), pady=8, sticky="ew")

        # 3. All-Subjects Marks Table
        cols = [
            ("subject_name", "Subject Name", 190),
            ("subject_code", "Code", 80),
            ("max_marks", "Max Marks", 95),
            ("passing_marks", "Passing", 85),
            ("marks_obtained_str", "Marks Obtained", 115),
            ("percentage_str", "Percentage", 95),
            ("grade", "Grade", 75),
            ("status", "Status", 110),
            ("teacher_remarks", "Teacher Remarks", 180)
        ]
        self.all_subject_marks_table = DataTable(tab, columns=cols)
        self.all_subject_marks_table.grid(row=2, column=0, padx=4, pady=(0, 4), sticky="nsew")

        self.rep_students_cache = []
        self.current_report_data = None
        self._on_rep_class_or_sec_change()

    def _on_rep_class_or_sec_change(self, *args):
        c_name = self.rep_class_cb.get() if hasattr(self, "rep_class_cb") else ""
        c_obj = next((c for c in self.classes_cache if c["name"] == c_name), None)
        if not c_obj:
            return

        selected_sec = self.rep_sec_cb.get() if hasattr(self, "rep_sec_cb") else "A"
        students = self.student_repo.search_students(class_id=c_obj["id"], status="Active")
        if selected_sec != "All":
            students = [s for s in students if s.get("section_name") == selected_sec]

        self.rep_students_cache = students
        display_list = [f"Roll #{s.get('roll_number', '-')} - {s['first_name']} {s['last_name']} ({s['admission_number']})" for s in students]

        if display_list:
            self.rep_student_cb.configure(values=display_list)
            self.rep_student_cb.set(display_list[0])
            self._on_rep_student_selected()
        else:
            self.rep_student_cb.configure(values=["(No students enrolled)"])
            self.rep_student_cb.set("(No students enrolled)")
            self.all_subject_marks_table.populate([])
            self.rep_student_name_lbl.configure(text=f"No students enrolled in {c_name} - Sec {selected_sec}")
            self.rep_student_meta_lbl.configure(text="Please enroll students or switch class/section.")
            self.kpi_total_marks.update_value("--", "No students")
            self.kpi_percentage.update_value("--", "No students")
            self.kpi_grade.update_value("--", "No students")
            self.kpi_status.update_value("--", "No students")
            self.current_report_data = None

    def _on_rep_search_keyup(self, event=None):
        term = self.rep_search_entry.get().strip().lower()
        if not term:
            display_list = [f"Roll #{s.get('roll_number', '-')} - {s['first_name']} {s['last_name']} ({s['admission_number']})" for s in self.rep_students_cache]
            if display_list:
                self.rep_student_cb.configure(values=display_list)
            return

        matches = []
        for s in self.rep_students_cache:
            full_str = f"{s.get('roll_number', '')} {s['first_name']} {s['last_name']} {s['admission_number']} {s.get('father_name', '')}".lower()
            if term in full_str:
                matches.append(s)

        if matches:
            display_list = [f"Roll #{s.get('roll_number', '-')} - {s['first_name']} {s['last_name']} ({s['admission_number']})" for s in matches]
            self.rep_student_cb.configure(values=display_list)
            self.rep_student_cb.set(display_list[0])
            self._load_current_student_all_marks(matches[0]["id"])

    def _on_rep_student_selected(self):
        sel_str = self.rep_student_cb.get()
        if not sel_str or sel_str == "(No students enrolled)":
            return

        target_student = None
        for s in self.rep_students_cache:
            if s["admission_number"] in sel_str:
                target_student = s
                break

        if not target_student and self.rep_students_cache:
            target_student = self.rep_students_cache[0]

        if target_student:
            self._load_current_student_all_marks(target_student["id"])

    def _load_current_student_all_marks(self, student_id=None):
        if student_id is None:
            sel_str = self.rep_student_cb.get() if hasattr(self, "rep_student_cb") else ""
            for s in self.rep_students_cache:
                if s["admission_number"] in sel_str:
                    student_id = s["id"]
                    break

        if not student_id and self.rep_students_cache:
            student_id = self.rep_students_cache[0]["id"]

        if not student_id:
            return

        exam_name = self.rep_exam_cb.get() if hasattr(self, "rep_exam_cb") else ""
        exam_obj = next((e for e in self.exams_cache if e["name"] == exam_name), None)
        exam_id = exam_obj["id"] if exam_obj else 1

        data = self.repo.get_student_all_subjects_marks(exam_id, student_id)
        if not data or not data.get("student"):
            return

        self.current_report_data = data
        st = data["student"]

        self.rep_student_name_lbl.configure(
            text=f"{st['first_name']} {st['last_name']}  (Roll #{st.get('roll_number', '-')})"
        )
        self.rep_student_meta_lbl.configure(
            text=f"Adm: {st['admission_number']} | Class: {st['class_name']} - Sec {st.get('section_name', '')} | Father: {st.get('father_name', '')} | Session: {st.get('session_name', '2026-2027')}"
        )

        # Update KPIs
        self.kpi_total_marks.update_value(
            f"{data['total_obtained']:.0f} / {data['total_max']:.0f}",
            f"{data['passed_count']} Passed | {data['failed_count']} Failed"
        )
        self.kpi_percentage.update_value(
            f"{data['percentage']}%",
            "Aggregate Score"
        )
        self.kpi_grade.update_value(
            str(data["grade"]),
            "Letter Scale"
        )

        status_str = data["overall_status"]
        status_color = ThemeConfig.SUCCESS[1] if status_str == "PASSED" else (ThemeConfig.DANGER if status_str == "FAILED" else ThemeConfig.TEXT_MUTED)
        self.kpi_status.update_value(status_str, "Academic Standing")
        if hasattr(self.kpi_status, "val_label"):
            self.kpi_status.val_label.configure(text_color=status_color)
        if hasattr(self.kpi_status, "accent_indicator"):
            self.kpi_status.accent_indicator.configure(fg_color=status_color)

        self.all_subject_marks_table.populate(data["marks"])

    def _refresh_report_view(self):
        self._on_rep_class_or_sec_change()

    def _generate_pdf_report_card(self):
        if not self.current_report_data or not self.current_report_data.get("marks"):
            return

        pdf_path = PDFGenerator.generate_report_card(self.current_report_data)
        st = self.current_report_data.get("student", {})
        st_name = f"{st.get('first_name', '')} {st.get('last_name', '')}"
        try:
            os.startfile(pdf_path)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # TAB 3: CLASS SUBJECTS SETUP (ADMIN SUBJECT MANAGEMENT)
    # -------------------------------------------------------------------------
    def _init_subjects_tab(self):
        tab = self.tab_subjects
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        bar.grid(row=0, column=0, padx=4, pady=(4, 12), sticky="ew")

        # Class selector
        class_names = [c["name"] for c in self.classes_cache]
        ctk.CTkLabel(bar, text="Class:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(12, 4), pady=10)
        self.subj_class_cb = ctk.CTkComboBox(bar, values=class_names, width=120, command=lambda v: self._load_class_subjects())
        if class_names:
            self.subj_class_cb.set(class_names[0])
        self.subj_class_cb.pack(side="left", padx=4, pady=10)

        # Subject Search
        self.subj_search_entry = ctk.CTkEntry(bar, placeholder_text="🔍 Filter subjects...", width=160, font=ThemeConfig.get_font(11))
        self.subj_search_entry.pack(side="left", padx=(8, 4), pady=10)
        self.subj_search_entry.bind("<KeyRelease>", lambda e: self._load_class_subjects())

        # Buttons
        add_btn = ctk.CTkButton(
            bar,
            text="➕ Add Subject",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.PRIMARY,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            width=115,
            command=self._open_add_subject_dialog
        )
        add_btn.pack(side="left", padx=6, pady=10)

        remove_btn = ctk.CTkButton(
            bar,
            text="🗑️ Remove Subject",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.DANGER,
            hover_color=ThemeConfig.DANGER_HOVER,
            width=130,
            command=self._confirm_remove_subject
        )
        remove_btn.pack(side="left", padx=6, pady=10)

        seed_btn = ctk.CTkButton(
            bar,
            text="⚡ Load Recommended Curricula",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.SECONDARY,
            hover_color=ThemeConfig.SECONDARY_HOVER,
            width=190,
            command=self._seed_recommended_curriculum
        )
        seed_btn.pack(side="left", padx=6, pady=10)

        self.subj_feedback = ctk.CTkLabel(bar, text="", font=ThemeConfig.get_font(11, "bold"))
        self.subj_feedback.pack(side="right", padx=12)

        # DataTable
        cols = [
            ("id", "ID", 60),
            ("subject_name", "Subject Name", 220),
            ("subject_code", "Subject Code", 110),
            ("total_marks", "Max Marks", 110),
            ("passing_marks", "Passing Marks", 110),
            ("exam_count", "Linked Exam Papers", 140)
        ]
        self.subjects_table = DataTable(tab, columns=cols)
        self.subjects_table.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="nsew")

        self._load_class_subjects()

    def _load_class_subjects(self):
        c_name = self.subj_class_cb.get() if hasattr(self, "subj_class_cb") else ""
        c_obj = next((c for c in self.classes_cache if c["name"] == c_name), None)
        if not c_obj:
            return

        subjs = self.repo.get_subjects_by_class(c_obj["id"])
        term = self.subj_search_entry.get().strip().lower() if hasattr(self, "subj_search_entry") else ""
        if term:
            subjs = [s for s in subjs if term in s["subject_name"].lower() or term in (s.get("subject_code") or "").lower()]

        formatted = []
        for s in subjs:
            formatted.append({
                "id": str(s["id"]),
                "subject_name": s["subject_name"],
                "subject_code": s.get("subject_code") or "-",
                "total_marks": f"{float(s.get('total_marks', 100)):.0f}",
                "passing_marks": f"{float(s.get('passing_marks', 40)):.0f}",
                "exam_count": f"{s.get('exam_count', 0)} papers"
            })

        self.subjects_table.populate(formatted)
        self.subj_feedback.configure(
            text=f"Total Subjects: {len(formatted)} ({c_name})",
            text_color=ThemeConfig.TEXT_MUTED
        )

    def _open_add_subject_dialog(self):
        c_name = self.subj_class_cb.get()
        c_obj = next((c for c in self.classes_cache if c["name"] == c_name), None)
        if not c_obj:
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Add Subject - {c_name}")
        dialog.geometry("380x420")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"Add Subject for {c_name}", font=ThemeConfig.get_font(14, "bold"), text_color=ThemeConfig.PRIMARY[1]).pack(pady=(16, 12))

        form_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        form_frame.pack(fill="x", padx=30)

        ctk.CTkLabel(form_frame, text="Subject Name:", font=ThemeConfig.get_font(11, "bold")).pack(anchor="w", pady=(4, 2))
        name_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g. Computer Science, Physics, Art...")
        name_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(form_frame, text="Subject Code (Optional):", font=ThemeConfig.get_font(11, "bold")).pack(anchor="w", pady=(4, 2))
        code_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g. CS, PHY, ART")
        code_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(form_frame, text="Total / Max Marks:", font=ThemeConfig.get_font(11, "bold")).pack(anchor="w", pady=(4, 2))
        total_entry = ctk.CTkEntry(form_frame)
        total_entry.insert(0, "100.0")
        total_entry.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(form_frame, text="Passing Marks:", font=ThemeConfig.get_font(11, "bold")).pack(anchor="w", pady=(4, 2))
        passing_entry = ctk.CTkEntry(form_frame)
        passing_entry.insert(0, "40.0")
        passing_entry.pack(fill="x", pady=(0, 12))

        err_lbl = ctk.CTkLabel(dialog, text="", font=ThemeConfig.get_font(11, "bold"), text_color=ThemeConfig.DANGER)
        err_lbl.pack(pady=(0, 8))

        def save():
            s_name = name_entry.get().strip()
            if not s_name:
                err_lbl.configure(text="Subject name is required.")
                return

            try:
                tot = float(total_entry.get().strip())
                pas = float(passing_entry.get().strip())
                if tot <= 0 or pas <= 0 or pas > tot:
                    err_lbl.configure(text="Passing marks must be > 0 and <= Max Marks.")
                    return
            except ValueError:
                err_lbl.configure(text="Marks must be valid numbers.")
                return

            s_code = code_entry.get().strip() or s_name[:3].upper()
            ok, msg, _ = self.repo.add_subject_to_class(c_obj["id"], s_name, s_code, tot, pas)
            if not ok:
                err_lbl.configure(text=msg)
                return

            dialog.destroy()
            self._load_class_subjects()
            # Refresh Tab 1 class subjects if active
            if hasattr(self, "exam_class_cb") and self.exam_class_cb.get() == c_name:
                self._on_class_change(c_name)
            # Refresh Tab 2 if active
            if hasattr(self, "rep_class_cb") and self.rep_class_cb.get() == c_name:
                self._on_rep_class_or_sec_change()
            self.subj_feedback.configure(text=f"✔ Added '{s_name}' to {c_name}!", text_color=ThemeConfig.SUCCESS[1])

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(fill="x", padx=30, pady=(4, 16))

        cancel_btn = ctk.CTkButton(btn_row, text="Cancel", width=90, fg_color=ThemeConfig.BG_CARD, border_width=1, border_color=ThemeConfig.BORDER, command=dialog.destroy)
        cancel_btn.pack(side="left")

        save_btn = ctk.CTkButton(btn_row, text="Save Subject", width=140, fg_color=ThemeConfig.PRIMARY, hover_color=ThemeConfig.PRIMARY_HOVER, command=save)
        save_btn.pack(side="right")

        name_entry.focus()

    def _confirm_remove_subject(self):
        item = self.subjects_table.get_selected_item()
        if not item:
            self.subj_feedback.configure(text="Please select a subject from the table to remove.", text_color=ThemeConfig.WARNING[1])
            return

        c_name = self.subj_class_cb.get()
        subj_name = item.get("subject_name", "")
        subj_id = int(item["id"])

        dialog = ctk.CTkToplevel(self)
        dialog.title("Confirm Subject Removal")
        dialog.geometry("400x240")
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="Remove Subject from Class?", font=ThemeConfig.get_font(14, "bold"), text_color=ThemeConfig.DANGER).pack(pady=(18, 8))

        msg = (
            f"Are you sure you want to remove '{subj_name}' from {c_name}?\n\n"
            "⚠️ WARNING: This will permanently delete all recorded exam marks,\n"
            "scheduled papers, and teacher assignments linked to this subject."
        )
        ctk.CTkLabel(dialog, text=msg, font=ThemeConfig.get_font(11), justify="center").pack(padx=20, pady=(0, 16))

        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=10)

        ctk.CTkButton(btn_row, text="Cancel", width=100, fg_color=ThemeConfig.BG_CARD, border_width=1, border_color=ThemeConfig.BORDER, command=dialog.destroy).pack(side="left", padx=8)

        def do_delete():
            dialog.destroy()
            ok, rmsg = self.repo.remove_subject_from_class(subj_id)
            self._load_class_subjects()
            # Refresh Tab 1 & Tab 2
            if hasattr(self, "exam_class_cb") and self.exam_class_cb.get() == c_name:
                self._on_class_change(c_name)
            if hasattr(self, "rep_class_cb") and self.rep_class_cb.get() == c_name:
                self._on_rep_class_or_sec_change()
            self.subj_feedback.configure(text=rmsg, text_color=ThemeConfig.SUCCESS[1] if ok else ThemeConfig.DANGER)

        ctk.CTkButton(btn_row, text="Yes, Remove Subject", width=150, fg_color=ThemeConfig.DANGER, hover_color=ThemeConfig.DANGER_HOVER, command=do_delete).pack(side="left", padx=8)

    def _seed_recommended_curriculum(self):
        c_name = self.subj_class_cb.get()
        c_obj = next((c for c in self.classes_cache if c["name"] == c_name), None)
        if not c_obj:
            return

        added = self.repo.seed_default_subjects_for_class(c_obj["id"], c_name)
        self._load_class_subjects()
        if hasattr(self, "exam_class_cb") and self.exam_class_cb.get() == c_name:
            self._on_class_change(c_name)
        if hasattr(self, "rep_class_cb") and self.rep_class_cb.get() == c_name:
            self._on_rep_class_or_sec_change()
        self.subj_feedback.configure(
            text=f"✔ Added {added} recommended subjects to {c_name}." if added > 0 else f"Standard subjects already configured for {c_name}.",
            text_color=ThemeConfig.SUCCESS[1]
        )

    # -------------------------------------------------------------------------
    # TAB 4: STATISTICAL INSIGHTS DASHBOARD
    # -------------------------------------------------------------------------
    def _init_stats_tab(self):
        tab = self.tab_stats
        tab.grid_columnconfigure(0, weight=1)

        bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        bar.pack(fill="x", padx=4, pady=(4, 16))

        ctk.CTkLabel(bar, text="COMPUTE INFERENTIAL & DESCRIPTIVE CLASS STATISTICS", font=ThemeConfig.get_font(12, "bold"), text_color=ThemeConfig.PRIMARY[1]).pack(side="left", padx=12, pady=12)

        calc_btn = ctk.CTkButton(
            bar,
            text="⚡ Compute Class Analytics",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.PRIMARY,
            command=self._compute_stats
        )
        calc_btn.pack(side="right", padx=12, pady=10)

        cards_row = ctk.CTkFrame(tab, fg_color="transparent")
        cards_row.pack(fill="x", padx=4, pady=(0, 16))
        for i in range(4):
            cards_row.grid_columnconfigure(i, weight=1)

        self.stat_mean = StatCard(cards_row, title="Mean Score", value="--", subtitle="Average class performance", accent_color=ThemeConfig.PRIMARY[1])
        self.stat_mean.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.stat_var = StatCard(cards_row, title="Score Variance", value="--", subtitle="Spread in student capability", accent_color=ThemeConfig.SECONDARY[1])
        self.stat_var.grid(row=0, column=1, padx=(0, 10), sticky="ew")

        self.stat_std = StatCard(cards_row, title="Std Deviation (σ)", value="--", subtitle="Dispersion from the mean", accent_color=ThemeConfig.GOLD_ACCENT[1])
        self.stat_std.grid(row=0, column=2, padx=(0, 10), sticky="ew")

        self.stat_prob = StatCard(cards_row, title="Pass Probability", value="--", subtitle="Normal Gaussian model P(X≥40)", accent_color=ThemeConfig.SUCCESS[1])
        self.stat_prob.grid(row=0, column=3, sticky="ew")

        self.stats_details_box = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=12, border_width=1, border_color=ThemeConfig.BORDER)
        self.stats_details_box.pack(fill="both", expand=True, padx=4, pady=(0, 8))

        self.stats_text = ctk.CTkLabel(
            self.stats_details_box,
            text="Click 'Compute Class Analytics' after loading and saving marks in Tab 1 to view insights.",
            font=ThemeConfig.get_font(12),
            text_color=ThemeConfig.TEXT_MUTED
        )
        self.stats_text.pack(expand=True, pady=40)

    def _compute_stats(self):
        if not hasattr(self, "active_es_id"):
            self._load_marks_sheet()

        if not hasattr(self, "active_es_id"):
            return

        scores = self.repo.get_subject_mark_distribution(self.active_es_id)
        if not scores:
            scores = [float(r.get("marks_obtained", 0)) for r in self.current_marks_data if not r.get("is_absent") and r.get("marks_obtained") != "ABS"]

        stats = ExamController.compute_class_statistics(scores, passing_mark=getattr(self, "active_pass_marks", 40.0))

        self.stat_mean.update_value(f"{stats['mean']:.1f}", f"Median: {stats['median']:.1f}")
        self.stat_var.update_value(f"{stats['variance']:.1f}", "Sample Variance (s²)")
        self.stat_std.update_value(f"{stats['std_dev']:.2f}", f"Range: {stats['min_score']} - {stats['max_score']}")
        self.stat_prob.update_value(f"{stats['pass_probability']}%", f"Actual Pass: {stats['pass_percentage']}%")

        detail_msg = (
            f"STATISTICAL SUMMARY FOR LOADED EXAM PAPER\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Total Graded Students : {stats['count']}\n"
            f"• Minimum Score Recorded: {stats['min_score']} | Highest Score: {stats['max_score']}\n"
            f"• Students Passed (≥40) : {stats['pass_count']} ({stats['pass_percentage']}%)\n"
            f"• Students Failed (<40) : {stats['fail_count']}\n"
            f"• Normal Distribution Pass Likelihood : {stats['pass_probability']}%\n"
            f"• Variance Interpretation: "
            + ("High performance divergence across students." if stats['variance'] > 150 else "Uniform learning comprehension.")
        )
        self.stats_text.configure(text=detail_msg, justify="left", font=ThemeConfig.get_font(12, "bold"), text_color=ThemeConfig.TEXT_MAIN)

"""
Attendance Management View.
Features:
- Fast batch keyboard & click student attendance tracking
- Quick day navigation (Prev Day, Today, Next Day) and arbitrary date inspection/editing
- Live midnight date-rollover tracking (automatically updates to new date in real-time)
- School-wide daily attendance log & history with class-by-class breakdown
- One-click jump from daily log to edit any class attendance
- Daily attendance report Excel export
- Flexible date-range chronic absentee scanning (< 75% attendance)
- Centered, Straight, Low-Opacity Campus Watermark Background
"""
import os
import customtkinter as ctk
from datetime import date, timedelta
from config.theme_config import ThemeConfig
from src.views.components.data_table import DataTable
from src.views.components.watermark import WatermarkManager
from src.controllers.attendance_controller import AttendanceController
from src.repositories.student_repository import StudentRepository
from src.services.excel_service import ExcelService

class AttendanceView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=ThemeConfig.BG_MAIN, **kwargs)
        self.controller = AttendanceController()
        self.student_repo = StudentRepository()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Track system date for automatic midnight rollover
        self._system_calendar_date = date.today().isoformat()

        # Apply centered, straight watermark in background
        WatermarkManager.apply(self, width=820, height=560)

        self._build_tabs()
        self._check_date_rollover()

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=ThemeConfig.BG_MAIN,
            segmented_button_selected_color=ThemeConfig.PRIMARY[1],
            segmented_button_selected_hover_color=ThemeConfig.PRIMARY_HOVER[1]
        )
        self.tabview.grid(row=0, column=0, padx=20, pady=16, sticky="nsew")

        self.tab_mark = self.tabview.add("📋 Fast Student Attendance")
        self.tab_daily_log = self.tabview.add("📅 School-Wide Daily Log")
        self.tab_chronic = self.tabview.add("⚠️ Chronic Absentees Alert (<75%)")

        self._init_mark_tab()
        self._init_daily_log_tab()
        self._init_chronic_tab()

    # -------------------------------------------------------------------------
    # TAB 1: FAST STUDENT ATTENDANCE (RAPID BATCH ENTRY FOR ANY DATE)
    # -------------------------------------------------------------------------
    def _init_mark_tab(self):
        tab = self.tab_mark
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # Controls Bar
        bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        bar.grid(row=0, column=0, padx=4, pady=(4, 12), sticky="ew")

        # Class
        ctk.CTkLabel(bar, text="Class:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(10, 3), pady=10)
        self.classes_cache = self.student_repo.get_all_classes()
        class_names = [c["name"] for c in self.classes_cache]
        self.att_class = ctk.CTkComboBox(bar, values=class_names, command=self._on_class_change, width=110, height=32)
        if class_names:
            self.att_class.set(class_names[0])
        self.att_class.pack(side="left", padx=3, pady=10)

        # Section
        ctk.CTkLabel(bar, text="Sec:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(6, 3), pady=10)
        self.att_sec = ctk.CTkComboBox(bar, values=["A", "B"], width=65, height=32, command=lambda v: self._load_roster())
        self.att_sec.set("A")
        self.att_sec.pack(side="left", padx=3, pady=10)

        # Date Controls: Step Back, Date Entry, Step Forward, Today
        ctk.CTkLabel(bar, text="Date:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(8, 3), pady=10)
        
        ctk.CTkButton(
            bar,
            text="◀",
            font=ThemeConfig.get_font(11, "bold"),
            width=28,
            height=32,
            fg_color=ThemeConfig.BG_CARD_ALT,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            command=lambda: self._step_date(-1)
        ).pack(side="left", padx=(0, 2), pady=10)

        self.att_date = ctk.CTkEntry(bar, width=102, height=32)
        self.att_date.insert(0, date.today().isoformat())
        self.att_date.pack(side="left", padx=2, pady=10)
        self.att_date.bind("<Return>", lambda e: (self._update_date_label(), self._load_roster()))
        self.att_date.bind("<FocusOut>", lambda e: (self._update_date_label(), self._load_roster()))

        ctk.CTkButton(
            bar,
            text="▶",
            font=ThemeConfig.get_font(11, "bold"),
            width=28,
            height=32,
            fg_color=ThemeConfig.BG_CARD_ALT,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            command=lambda: self._step_date(1)
        ).pack(side="left", padx=(2, 3), pady=10)

        ctk.CTkButton(
            bar,
            text="📅 Today",
            font=ThemeConfig.get_font(10, "bold"),
            width=65,
            height=32,
            fg_color=ThemeConfig.PRIMARY,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            command=self._set_today
        ).pack(side="left", padx=(0, 4), pady=10)

        # Live Day of Week label
        self.att_day_lbl = ctk.CTkLabel(bar, text="", font=ThemeConfig.get_font(10, "bold"), text_color=ThemeConfig.GOLD_ACCENT[1])
        self.att_day_lbl.pack(side="left", padx=3, pady=10)
        self._update_date_label()

        # Refresh button
        load_btn = ctk.CTkButton(
            bar,
            text="🔍 Refresh",
            font=ThemeConfig.get_font(11, "bold"),
            width=75,
            height=32,
            fg_color=ThemeConfig.BG_CARD_ALT,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            command=self._load_roster
        )
        load_btn.pack(side="left", padx=4, pady=10)

        # Right Action Buttons
        save_btn = ctk.CTkButton(
            bar,
            text="💾 Save Attendance",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.SECONDARY,
            hover_color=ThemeConfig.SECONDARY_HOVER,
            height=32,
            command=self._save_attendance
        )
        save_btn.pack(side="right", padx=(4, 10), pady=10)

        all_abs_btn = ctk.CTkButton(
            bar,
            text="✖ All Absent",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.DANGER,
            hover_color="#991B1B",
            command=self._mark_all_absent,
            width=88,
            height=32
        )
        all_abs_btn.pack(side="right", padx=3, pady=10)

        all_pres_btn = ctk.CTkButton(
            bar,
            text="✔ All Present",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.PRIMARY,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            command=self._mark_all_present,
            width=88,
            height=32
        )
        all_pres_btn.pack(side="right", padx=3, pady=10)

        self.att_status = ctk.CTkLabel(bar, text="", font=ThemeConfig.get_font(11, "bold"))
        self.att_status.pack(side="right", padx=6)

        # Table showing current class roster
        cols = [
            ("roll_number", "Roll #", 70),
            ("admission_number", "Adm No", 120),
            ("student_name", "Student Name", 220),
            ("status", "Status (Double-Click to Toggle)", 240)
        ]
        self.roster_table = DataTable(tab, columns=cols, on_double_click=self._toggle_row_status)
        self.roster_table.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="nsew")

        self.current_roster_data = []
        if class_names:
            self._on_class_change(class_names[0])
        else:
            self._load_roster()

    def _step_date(self, days: int):
        """Steps attendance date backward or forward by N days."""
        try:
            cur = date.fromisoformat(self.att_date.get().strip())
        except ValueError:
            cur = date.today()
        new_dt = cur + timedelta(days=days)
        self.att_date.delete(0, "end")
        self.att_date.insert(0, new_dt.isoformat())
        self._update_date_label()
        self._load_roster()

    def _set_today(self):
        """Resets attendance date to today's real-time system date."""
        self.att_date.delete(0, "end")
        self.att_date.insert(0, date.today().isoformat())
        self._update_date_label()
        self._load_roster()

    def _update_date_label(self):
        """Updates day of week label adjacent to date input."""
        try:
            dt = date.fromisoformat(self.att_date.get().strip())
            day_name = dt.strftime("%a")
            is_today = (dt == date.today())
            tag = "• Today" if is_today else ""
            self.att_day_lbl.configure(text=f"{day_name} {tag}".strip())
        except Exception:
            self.att_day_lbl.configure(text="")

    def _check_date_rollover(self):
        """
        Periodically checks if the calendar day rolled over past midnight.
        Automatically updates active date if user is on 'Today'.
        """
        try:
            current_sys_date = date.today().isoformat()
            if current_sys_date != self._system_calendar_date:
                old_date = self._system_calendar_date
                self._system_calendar_date = current_sys_date
                # If mark tab was viewing old today's date, advance it to current date
                if hasattr(self, "att_date") and self.att_date.get().strip() == old_date:
                    self.att_date.delete(0, "end")
                    self.att_date.insert(0, current_sys_date)
                    self._update_date_label()
                    self._load_roster()
                # If daily log tab was viewing old today's date, advance it
                if hasattr(self, "log_date") and self.log_date.get().strip() == old_date:
                    self.log_date.delete(0, "end")
                    self.log_date.insert(0, current_sys_date)
                    self._load_daily_log()
        except Exception:
            pass
        # Check every 15 seconds
        self.after(15000, self._check_date_rollover)

    def _on_class_change(self, class_name: str):
        c_obj = next((c for c in self.classes_cache if c["name"] == class_name), None)
        if c_obj:
            secs = self.student_repo.get_sections_by_class(c_obj["id"])
            sec_names = [s["name"] for s in secs] if secs else ["A"]
            self.att_sec.configure(values=sec_names)
            if sec_names:
                self.att_sec.set(sec_names[0])
        self._load_roster()

    def _load_roster(self):
        c_name = self.att_class.get()
        c_obj = next((c for c in self.classes_cache if c["name"] == c_name), None)
        if not c_obj:
            return

        secs = self.student_repo.get_sections_by_class(c_obj["id"])
        selected_sec = self.att_sec.get()
        sec_obj = next((s for s in secs if s["name"] == selected_sec), None)
        sec_id = sec_obj["id"] if sec_obj else (secs[0]["id"] if secs else 1)

        session = self.student_repo.get_current_session()
        session_id = session["id"] if session else 1

        target_date = self.att_date.get().strip() or date.today().isoformat()
        roster = self.controller.get_roster(c_obj["id"], sec_id, target_date, session_id)

        self.current_roster_data = []
        for r in roster:
            st = {
                "student_id": r["student_id"],
                "roll_number": r.get("roll_number", ""),
                "admission_number": r["admission_number"],
                "student_name": f"{r['first_name']} {r['last_name']}",
                "status": r.get("status", "Present")
            }
            self.current_roster_data.append(st)

        self._render_roster()

    def _render_roster(self):
        c_name = self.att_class.get()
        selected_sec = self.att_sec.get()
        target_date = self.att_date.get().strip() or date.today().isoformat()

        formatted = []
        pres_count = 0
        abs_count = 0

        for r in self.current_roster_data:
            st_val = r.get("status", "Present")
            if st_val == "Present":
                display_status = "✔ Present"
                pres_count += 1
            elif st_val == "Absent":
                display_status = "✖ Absent"
                abs_count += 1
            elif st_val == "Late":
                display_status = "⏱ Late"
            elif st_val == "Excused":
                display_status = "ℹ Excused"
            else:
                display_status = st_val

            item = dict(r)
            item["raw_status"] = st_val
            item["status"] = display_status
            formatted.append(item)

        self.roster_table.populate(formatted)
        self.att_status.configure(
            text=f"[{target_date}] {c_name}-{selected_sec} ({len(formatted)} Students) | 🟢 Present: {pres_count}  🔴 Absent: {abs_count}",
            text_color=ThemeConfig.TEXT_MAIN
        )

    def _toggle_row_status(self, row: dict):
        raw_st = row.get("raw_status") or row.get("status", "Present")
        clean_st = raw_st.replace("✔", "").replace("✖", "").replace("⏱", "").replace("ℹ", "").strip()
        cycle = {"Present": "Absent", "Absent": "Late", "Late": "Excused", "Excused": "Present"}
        new_st = cycle.get(clean_st, "Present")

        for r in self.current_roster_data:
            if r["student_id"] == row["student_id"]:
                r["status"] = new_st
                break

        self._render_roster()

    def _mark_all_present(self):
        for r in self.current_roster_data:
            r["status"] = "Present"
        self._render_roster()

    def _mark_all_absent(self):
        for r in self.current_roster_data:
            r["status"] = "Absent"
        self._render_roster()

    def _save_attendance(self):
        if not self.current_roster_data:
            return

        c_obj = next((c for c in self.classes_cache if c["name"] == self.att_class.get()), None)
        if not c_obj:
            return

        secs = self.student_repo.get_sections_by_class(c_obj["id"])
        sec_obj = next((s for s in secs if s["name"] == self.att_sec.get()), None)
        sec_id = sec_obj["id"] if sec_obj else (secs[0]["id"] if secs else 1)

        target_date = self.att_date.get().strip() or date.today().isoformat()
        saved = self.controller.save_roster_attendance(
            class_id=c_obj["id"],
            section_id=sec_id,
            attendance_date=target_date,
            records=self.current_roster_data
        )
        self.att_status.configure(text=f"✔ Saved {saved} records successfully for {target_date}!", text_color=ThemeConfig.SUCCESS[1])

        # If daily log tab is initialized, refresh its data in background
        if hasattr(self, "log_date") and self.log_date.get().strip() == target_date:
            self._load_daily_log()

    # -------------------------------------------------------------------------
    # TAB 2: SCHOOL-WIDE DAILY ATTENDANCE LOG & HISTORY (ANY DATE ACCESS)
    # -------------------------------------------------------------------------
    def _init_daily_log_tab(self):
        tab = self.tab_daily_log
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        # 1. Controls Bar
        bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        bar.grid(row=0, column=0, padx=4, pady=(4, 8), sticky="ew")

        ctk.CTkLabel(bar, text="Daily Log Date:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(12, 4), pady=10)

        ctk.CTkButton(
            bar,
            text="◀",
            font=ThemeConfig.get_font(11, "bold"),
            width=30,
            height=32,
            fg_color=ThemeConfig.BG_CARD_ALT,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            command=lambda: self._step_log_date(-1)
        ).pack(side="left", padx=(0, 2), pady=10)

        self.log_date = ctk.CTkEntry(bar, width=105, height=32)
        self.log_date.insert(0, date.today().isoformat())
        self.log_date.pack(side="left", padx=2, pady=10)
        self.log_date.bind("<Return>", lambda e: self._load_daily_log())
        self.log_date.bind("<FocusOut>", lambda e: self._load_daily_log())

        ctk.CTkButton(
            bar,
            text="▶",
            font=ThemeConfig.get_font(11, "bold"),
            width=30,
            height=32,
            fg_color=ThemeConfig.BG_CARD_ALT,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            command=lambda: self._step_log_date(1)
        ).pack(side="left", padx=(2, 4), pady=10)

        ctk.CTkButton(
            bar,
            text="📅 Today",
            font=ThemeConfig.get_font(10, "bold"),
            width=68,
            height=32,
            fg_color=ThemeConfig.PRIMARY,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            command=self._set_log_today
        ).pack(side="left", padx=(0, 8), pady=10)

        load_log_btn = ctk.CTkButton(
            bar,
            text="🔍 Fetch School Log",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.PRIMARY,
            height=32,
            command=self._load_daily_log
        )
        load_log_btn.pack(side="left", padx=4, pady=10)

        export_btn = ctk.CTkButton(
            bar,
            text="📥 Export to Excel",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.SECONDARY,
            hover_color=ThemeConfig.SECONDARY_HOVER,
            height=32,
            command=self._export_daily_log_excel
        )
        export_btn.pack(side="right", padx=12, pady=10)

        self.log_feedback = ctk.CTkLabel(bar, text="", font=ThemeConfig.get_font(11, "bold"))
        self.log_feedback.pack(side="right", padx=8)

        # 2. KPI Summary Cards Bar for the selected date
        kpi_bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD_ALT, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        kpi_bar.grid(row=1, column=0, padx=4, pady=(0, 8), sticky="ew")
        for i in range(5):
            kpi_bar.grid_columnconfigure(i, weight=1)

        self.kpi_enrolled = ctk.CTkLabel(kpi_bar, text="👥 Enrolled: 0", font=ThemeConfig.get_font(11, "bold"), text_color=ThemeConfig.TEXT_MAIN)
        self.kpi_enrolled.grid(row=0, column=0, padx=8, pady=8)

        self.kpi_marked = ctk.CTkLabel(kpi_bar, text="📋 Classes Marked: 0/0", font=ThemeConfig.get_font(11, "bold"), text_color=ThemeConfig.INFO[1])
        self.kpi_marked.grid(row=0, column=1, padx=8, pady=8)

        self.kpi_present = ctk.CTkLabel(kpi_bar, text="🟢 Present: 0", font=ThemeConfig.get_font(11, "bold"), text_color=ThemeConfig.SUCCESS[1])
        self.kpi_present.grid(row=0, column=2, padx=8, pady=8)

        self.kpi_absent = ctk.CTkLabel(kpi_bar, text="🔴 Absent: 0", font=ThemeConfig.get_font(11, "bold"), text_color=ThemeConfig.DANGER[1])
        self.kpi_absent.grid(row=0, column=3, padx=8, pady=8)

        self.kpi_overall_pct = ctk.CTkLabel(kpi_bar, text="📊 Rate: 0.0%", font=ThemeConfig.get_font(11, "bold"), text_color=ThemeConfig.GOLD_ACCENT[1])
        self.kpi_overall_pct.grid(row=0, column=4, padx=8, pady=8)

        # 3. Class-by-Class DataTable
        cols = [
            ("display_class", "Class & Section", 140),
            ("total_enrolled", "Enrolled", 90),
            ("marked_count", "Marked", 90),
            ("present_count", "Present", 90),
            ("absent_count", "Absent", 90),
            ("late_count", "Late", 80),
            ("percentage", "Attendance %", 110),
            ("status", "Status (Double-Click to Edit Class)", 230)
        ]
        self.log_table = DataTable(tab, columns=cols, on_double_click=self._on_log_row_double_click)
        self.log_table.grid(row=2, column=0, padx=4, pady=(0, 4), sticky="nsew")

        self.current_log_data = []
        self.current_log_metrics = {}
        self._load_daily_log()

    def _step_log_date(self, days: int):
        try:
            cur = date.fromisoformat(self.log_date.get().strip())
        except ValueError:
            cur = date.today()
        new_dt = cur + timedelta(days=days)
        self.log_date.delete(0, "end")
        self.log_date.insert(0, new_dt.isoformat())
        self._load_daily_log()

    def _set_log_today(self):
        self.log_date.delete(0, "end")
        self.log_date.insert(0, date.today().isoformat())
        self._load_daily_log()

    def _load_daily_log(self):
        dt_str = self.log_date.get().strip() or date.today().isoformat()
        try:
            parsed = date.fromisoformat(dt_str)
            dt_str = parsed.isoformat()
        except ValueError:
            dt_str = date.today().isoformat()

        records = self.controller.get_daily_school_summary(dt_str)
        metrics = self.controller.get_school_metrics(dt_str)
        self.current_log_data = records
        self.current_log_metrics = metrics

        # Update KPI bar
        self.kpi_enrolled.configure(text=f"👥 Total Enrolled: {metrics.get('total_enrolled', 0)}")
        self.kpi_marked.configure(text=f"📋 Marked Classes: {metrics.get('classes_completed', 0)}/{metrics.get('classes_count', 0)}")
        self.kpi_present.configure(text=f"🟢 Present: {metrics.get('total_present', 0)}")
        self.kpi_absent.configure(text=f"🔴 Absent: {metrics.get('total_absent', 0)}")
        pct = metrics.get('overall_percentage', 0.0)
        self.kpi_overall_pct.configure(text=f"📊 School Rate: {pct}%")

        # Format rows for table
        formatted = []
        for r in records:
            item = dict(r)
            item["percentage"] = f"{r['percentage']}%"
            formatted.append(item)

        self.log_table.populate(formatted)
        self.log_feedback.configure(
            text=f"School-wide log loaded for {dt_str}",
            text_color=ThemeConfig.TEXT_MAIN
        )

    def _on_log_row_double_click(self, row: dict):
        """Switches to Fast Student Attendance tab with the selected class and date pre-loaded."""
        cls_name = row.get("class_name")
        sec_name = row.get("section_name")
        target_date = self.log_date.get().strip() or date.today().isoformat()

        if cls_name and hasattr(self, "att_class"):
            self.att_class.set(cls_name)
            self._on_class_change(cls_name)
            if sec_name and hasattr(self, "att_sec"):
                self.att_sec.set(sec_name)
            self.att_date.delete(0, "end")
            self.att_date.insert(0, target_date)
            self._update_date_label()
            self._load_roster()
            self.tabview.set("📋 Fast Student Attendance")

    def _export_daily_log_excel(self):
        if not self.current_log_data:
            self.log_feedback.configure(text="No log records to export.", text_color=ThemeConfig.WARNING[1])
            return
        dt_str = self.log_date.get().strip() or date.today().isoformat()
        try:
            path = ExcelService.export_daily_attendance_summary(
                self.current_log_data,
                self.current_log_metrics,
                dt_str
            )
            self.log_feedback.configure(
                text=f"✔ Exported: {os.path.basename(path)}",
                text_color=ThemeConfig.SUCCESS[1]
            )
        except Exception as e:
            self.log_feedback.configure(text=f"Export failed: {str(e)}", text_color=ThemeConfig.DANGER[1])

    # -------------------------------------------------------------------------
    # TAB 3: CHRONIC ABSENTEES AUDIT & SCANNER (FLEXIBLE DATE RANGES)
    # -------------------------------------------------------------------------
    def _init_chronic_tab(self):
        tab = self.tab_chronic
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        bar = ctk.CTkFrame(tab, fg_color=ThemeConfig.BG_CARD, corner_radius=10, border_width=1, border_color=ThemeConfig.BORDER)
        bar.grid(row=0, column=0, padx=4, pady=(4, 12), sticky="ew")

        # Class Filter
        ctk.CTkLabel(bar, text="Class:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(10, 3), pady=10)
        class_options = ["All Classes"] + [c["name"] for c in self.classes_cache]
        self.chronic_class_cb = ctk.CTkComboBox(
            bar,
            values=class_options,
            command=lambda v: self._load_chronic_absentees(),
            width=115,
            height=32
        )
        self.chronic_class_cb.set("All Classes")
        self.chronic_class_cb.pack(side="left", padx=3, pady=10)

        # Date Range: Start & End Date
        ctk.CTkLabel(bar, text="From:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(6, 3), pady=10)
        self.chronic_start_date = ctk.CTkEntry(bar, width=95, height=32)
        self.chronic_start_date.insert(0, f"{date.today().year}-01-01")
        self.chronic_start_date.pack(side="left", padx=2, pady=10)
        self.chronic_start_date.bind("<Return>", lambda e: self._load_chronic_absentees())

        ctk.CTkLabel(bar, text="To:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(4, 3), pady=10)
        self.chronic_end_date = ctk.CTkEntry(bar, width=95, height=32)
        self.chronic_end_date.insert(0, date.today().isoformat())
        self.chronic_end_date.pack(side="left", padx=2, pady=10)
        self.chronic_end_date.bind("<Return>", lambda e: self._load_chronic_absentees())

        # Quick Range Presets
        ctk.CTkButton(
            bar, text="7 Days", font=ThemeConfig.get_font(10), width=50, height=30,
            fg_color=ThemeConfig.BG_CARD_ALT, hover_color=ThemeConfig.PRIMARY_HOVER,
            command=lambda: self._set_chronic_preset("7days")
        ).pack(side="left", padx=2, pady=10)

        ctk.CTkButton(
            bar, text="Month", font=ThemeConfig.get_font(10), width=50, height=30,
            fg_color=ThemeConfig.BG_CARD_ALT, hover_color=ThemeConfig.PRIMARY_HOVER,
            command=lambda: self._set_chronic_preset("month")
        ).pack(side="left", padx=2, pady=10)

        ctk.CTkButton(
            bar, text="YTD", font=ThemeConfig.get_font(10), width=45, height=30,
            fg_color=ThemeConfig.BG_CARD_ALT, hover_color=ThemeConfig.PRIMARY_HOVER,
            command=lambda: self._set_chronic_preset("year")
        ).pack(side="left", padx=2, pady=10)

        # Threshold
        ctk.CTkLabel(bar, text="Min %:", font=ThemeConfig.get_font(11, "bold")).pack(side="left", padx=(6, 3), pady=10)
        self.thresh_entry = ctk.CTkEntry(bar, width=50, height=32)
        self.thresh_entry.insert(0, "75")
        self.thresh_entry.pack(side="left", padx=2, pady=10)
        self.thresh_entry.bind("<Return>", lambda e: self._load_chronic_absentees())

        load_chronic_btn = ctk.CTkButton(
            bar,
            text="⚠️ Scan Absentees",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.DANGER,
            height=32,
            command=self._load_chronic_absentees
        )
        load_chronic_btn.pack(side="left", padx=8, pady=10)

        self.chronic_count = ctk.CTkLabel(bar, text="", font=ThemeConfig.get_font(11, "bold"))
        self.chronic_count.pack(side="right", padx=12)

        cols = [
            ("admission_number", "Adm No", 120),
            ("student_name", "Student Name", 180),
            ("class_name", "Class", 100),
            ("father_phone", "Parent Contact", 130),
            ("total_days", "Total Days", 90),
            ("present_days", "Present", 80),
            ("percentage", "Attendance %", 110),
            ("alert", "Alert Status", 140)
        ]
        self.chronic_table = DataTable(tab, columns=cols)
        self.chronic_table.grid(row=1, column=0, padx=4, pady=(0, 4), sticky="nsew")

        # Initial scan
        self._load_chronic_absentees()

    def _set_chronic_preset(self, preset: str):
        today = date.today()
        if preset == "7days":
            st = today - timedelta(days=7)
            ed = today
        elif preset == "month":
            st = today.replace(day=1)
            ed = today
        elif preset == "year":
            st = date(today.year, 1, 1)
            ed = today
        else:
            st = date(today.year, 1, 1)
            ed = today

        self.chronic_start_date.delete(0, "end")
        self.chronic_start_date.insert(0, st.isoformat())
        self.chronic_end_date.delete(0, "end")
        self.chronic_end_date.insert(0, ed.isoformat())
        self._load_chronic_absentees()

    def _load_chronic_absentees(self):
        try:
            th = float(self.thresh_entry.get().strip())
        except ValueError:
            th = 75.0

        selected_class = self.chronic_class_cb.get() if hasattr(self, "chronic_class_cb") else "All Classes"
        class_id = None
        if selected_class and selected_class != "All Classes":
            c_obj = next((c for c in self.classes_cache if c["name"] == selected_class), None)
            if c_obj:
                class_id = c_obj["id"]

        start_date = self.chronic_start_date.get().strip() if hasattr(self, "chronic_start_date") else f"{date.today().year}-01-01"
        end_date = self.chronic_end_date.get().strip() if hasattr(self, "chronic_end_date") else date.today().isoformat()
        results = self.controller.get_chronic_absentees_report(start_date, end_date, th, class_id=class_id)

        formatted = []
        for r in results:
            formatted.append({
                "admission_number": r["admission_number"],
                "student_name": f"{r['first_name']} {r['last_name']}",
                "class_name": f"{r['class_name']} - {r['section_name']}",
                "father_phone": r.get("father_phone", "-"),
                "total_days": r["total_days"],
                "present_days": r["present_days"],
                "percentage": f"{r['percentage']}%",
                "alert": "🔴 CHRONIC DEFICIT"
            })

        self.chronic_table.populate(formatted)
        cls_info = f" ({selected_class})" if selected_class != "All Classes" else ""
        self.chronic_count.configure(text=f"Flagged: {len(formatted)} Students{cls_info}", text_color=ThemeConfig.DANGER[1])

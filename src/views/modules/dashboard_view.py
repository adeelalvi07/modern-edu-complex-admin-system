"""
Dashboard View Component.
Displays live real-time digital clock and date, institutional KPI cards,
attendance metrics for any date, class distribution, and quick action shortcuts.
Features centered, straight, low-opacity campus watermark background.
"""
import customtkinter as ctk
from datetime import date, datetime, timedelta
from config.theme_config import ThemeConfig
from src.views.components.stat_card import StatCard
from src.views.components.watermark import WatermarkManager
from src.repositories.student_repository import StudentRepository
from src.repositories.staff_repository import StaffRepository
from src.repositories.attendance_repository import AttendanceRepository
from src.repositories.fee_repository import FeeRepository
from typing import Callable

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, on_quick_nav: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=ThemeConfig.BG_MAIN, **kwargs)
        self.on_quick_nav = on_quick_nav

        self.student_repo = StudentRepository()
        self.staff_repo = StaffRepository()
        self.attendance_repo = AttendanceRepository()
        self.fee_repo = FeeRepository()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Track system date for automatic daily rollover
        self._current_calendar_date = date.today().isoformat()

        # Apply centered, straight, low-opacity watermark in the background
        WatermarkManager.apply(self, width=820, height=560)

        self._build_header()
        self._build_kpi_cards()
        self._build_content_panels()

        # Start live real-time clock ticker
        self._update_clock()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=24, pady=(18, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        # Left Info
        left_info = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_info.grid(row=0, column=0, sticky="w")

        greeting = ctk.CTkLabel(
            left_info,
            text="Executive Management Dashboard",
            font=ThemeConfig.font_title(),
            text_color=ThemeConfig.TEXT_MAIN
        )
        greeting.pack(anchor="w")

        sub_title = ctk.CTkLabel(
            left_info,
            text="AL-QAYYUM MODERN EDU COMPLEX  •  Automated Campus Operations",
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.GOLD_ACCENT[1]
        )
        sub_title.pack(anchor="w", pady=(2, 0))

        # Right Live Digital Clock Card
        clock_card = ctk.CTkFrame(
            header_frame,
            fg_color=ThemeConfig.BG_CARD,
            corner_radius=10,
            border_width=1,
            border_color=ThemeConfig.BORDER
        )
        clock_card.grid(row=0, column=1, sticky="e")

        self.clock_time_lbl = ctk.CTkLabel(
            clock_card,
            text="--:--:-- --",
            font=ThemeConfig.get_font(16, "bold"),
            text_color=ThemeConfig.PRIMARY[1]
        )
        self.clock_time_lbl.pack(padx=16, pady=(6, 0))

        self.clock_date_lbl = ctk.CTkLabel(
            clock_card,
            text="Loading date...",
            font=ThemeConfig.get_font(10, "bold"),
            text_color=ThemeConfig.TEXT_MUTED
        )
        self.clock_date_lbl.pack(padx=16, pady=(0, 6))

    def _build_kpi_cards(self):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=1, column=0, padx=24, pady=(0, 14), sticky="ew")
        wrapper.grid_columnconfigure(0, weight=1)

        # Date filter subbar for Attendance & Metrics
        subbar = ctk.CTkFrame(wrapper, fg_color="transparent")
        subbar.pack(fill="x", pady=(0, 6))

        ctk.CTkLabel(
            subbar,
            text="INSTITUTIONAL PERFORMANCE INDICATORS",
            font=ThemeConfig.get_font(10, "bold"),
            text_color=ThemeConfig.TEXT_MUTED
        ).pack(side="left")

        # Right Date Navigation for Attendance KPI
        date_ctrls = ctk.CTkFrame(subbar, fg_color="transparent")
        date_ctrls.pack(side="right")

        ctk.CTkLabel(date_ctrls, text="Attendance Date:", font=ThemeConfig.get_font(10, "bold"), text_color=ThemeConfig.TEXT_MUTED).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            date_ctrls, text="◀", font=ThemeConfig.get_font(10, "bold"), width=26, height=24,
            fg_color=ThemeConfig.BG_CARD_ALT, hover_color=ThemeConfig.PRIMARY_HOVER,
            command=lambda: self._step_dash_att_date(-1)
        ).pack(side="left", padx=1)

        self.dash_att_date = ctk.CTkEntry(date_ctrls, width=92, height=24, font=ThemeConfig.get_font(10))
        self.dash_att_date.insert(0, date.today().isoformat())
        self.dash_att_date.pack(side="left", padx=2)
        self.dash_att_date.bind("<Return>", lambda e: self._refresh_attendance_kpi())
        self.dash_att_date.bind("<FocusOut>", lambda e: self._refresh_attendance_kpi())

        ctk.CTkButton(
            date_ctrls, text="▶", font=ThemeConfig.get_font(10, "bold"), width=26, height=24,
            fg_color=ThemeConfig.BG_CARD_ALT, hover_color=ThemeConfig.PRIMARY_HOVER,
            command=lambda: self._step_dash_att_date(1)
        ).pack(side="left", padx=1)

        ctk.CTkButton(
            date_ctrls, text="Today", font=ThemeConfig.get_font(10, "bold"), width=48, height=24,
            fg_color=ThemeConfig.PRIMARY, hover_color=ThemeConfig.PRIMARY_HOVER,
            command=self._set_dash_att_today
        ).pack(side="left", padx=(3, 0))

        # 4 Cards Grid
        cards_frame = ctk.CTkFrame(wrapper, fg_color="transparent")
        cards_frame.pack(fill="x")
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)

        # 1. Total Students
        all_students = self.student_repo.search_students(status="Active")
        total_students = len(all_students)
        self.card_students = StatCard(
            cards_frame,
            title="Total Students",
            value=f"{total_students}",
            subtitle="Across 13 Classes (PG to 10)",
            accent_color=ThemeConfig.PRIMARY[1]
        )
        self.card_students.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        # 2. Total Faculty & Staff
        all_staff = self.staff_repo.get_all_staff()
        total_staff = len(all_staff)
        self.card_staff = StatCard(
            cards_frame,
            title="Faculty & Staff",
            value=f"{total_staff}",
            subtitle="Teaching & Support Staff",
            accent_color=ThemeConfig.SECONDARY[1]
        )
        self.card_staff.grid(row=0, column=1, padx=(0, 10), sticky="ew")

        # 3. Attendance for Selected Date (Defaults to Today)
        self.card_attendance = StatCard(
            cards_frame,
            title="Today's Attendance",
            value="0.0%",
            subtitle="Calculating...",
            accent_color=ThemeConfig.SUCCESS[1]
        )
        self.card_attendance.grid(row=0, column=2, padx=(0, 10), sticky="ew")
        self._refresh_attendance_kpi()

        # 4. Outstanding Fees
        defaulters = self.fee_repo.get_defaulters()
        total_due = sum(float(d.get("balance_amount", 0)) for d in defaulters)
        self.card_fees = StatCard(
            cards_frame,
            title="Pending Fees",
            value=f"PKR {total_due:,.0f}",
            subtitle=f"{len(defaulters)} Defaulters Flagged",
            accent_color=ThemeConfig.DANGER[1]
        )
        self.card_fees.grid(row=0, column=3, sticky="ew")

    def _step_dash_att_date(self, days: int):
        try:
            cur = date.fromisoformat(self.dash_att_date.get().strip())
        except ValueError:
            cur = date.today()
        new_dt = cur + timedelta(days=days)
        self.dash_att_date.delete(0, "end")
        self.dash_att_date.insert(0, new_dt.isoformat())
        self._refresh_attendance_kpi()

    def _set_dash_att_today(self):
        self.dash_att_date.delete(0, "end")
        self.dash_att_date.insert(0, date.today().isoformat())
        self._refresh_attendance_kpi()

    def _refresh_attendance_kpi(self):
        target_date = self.dash_att_date.get().strip() or date.today().isoformat()
        try:
            parsed = date.fromisoformat(target_date)
            target_date = parsed.isoformat()
        except ValueError:
            target_date = date.today().isoformat()

        is_today = (target_date == date.today().isoformat())
        card_title = "Today's Attendance" if is_today else f"Attendance ({target_date})"

        metrics = self.attendance_repo.get_school_attendance_metrics(target_date)
        tot_marked = metrics.get("total_marked", 0)
        pres_marked = metrics.get("total_present", 0)
        att_pct = metrics.get("overall_percentage", 0.0)

        val_text = f"{att_pct}%" if tot_marked > 0 else "Pending"
        sub_text = f"{pres_marked} Present of {tot_marked} Marked"

        self.card_attendance.update_title(card_title)
        self.card_attendance.update_value(val_text, sub_text)

    def _refresh_kpi_cards(self):
        # Refresh student count
        all_students = self.student_repo.search_students(status="Active")
        self.card_students.update_value(f"{len(all_students)}", "Across 13 Classes (PG to 10)")

        # Refresh staff count
        all_staff = self.staff_repo.get_all_staff()
        self.card_staff.update_value(f"{len(all_staff)}", "Teaching & Support Staff")

        # Refresh attendance
        self._refresh_attendance_kpi()

        # Refresh fees
        defaulters = self.fee_repo.get_defaulters()
        total_due = sum(float(d.get("balance_amount", 0)) for d in defaulters)
        self.card_fees.update_value(f"PKR {total_due:,.0f}", f"{len(defaulters)} Defaulters Flagged")

    def _update_clock(self):
        now = datetime.now()
        time_str = now.strftime("%I:%M:%S %p")
        date_str = now.strftime("%A, %d %B %Y")

        self.clock_time_lbl.configure(text=time_str)
        self.clock_date_lbl.configure(text=date_str)

        # Automatic midnight date rollover
        current_today = now.date().isoformat()
        if current_today != self._current_calendar_date:
            old_date = self._current_calendar_date
            self._current_calendar_date = current_today
            if hasattr(self, "dash_att_date") and self.dash_att_date.get().strip() == old_date:
                self.dash_att_date.delete(0, "end")
                self.dash_att_date.insert(0, current_today)
            self._refresh_kpi_cards()

        self.after(1000, self._update_clock)

    def _build_content_panels(self):
        panel_frame = ctk.CTkFrame(self, fg_color="transparent")
        panel_frame.grid(row=2, column=0, padx=24, pady=(0, 20), sticky="nsew")
        panel_frame.grid_columnconfigure(0, weight=2)
        panel_frame.grid_columnconfigure(1, weight=1)
        panel_frame.grid_rowconfigure(0, weight=1)

        # Left Panel: Class Distribution Matrix
        left_box = ctk.CTkFrame(
            panel_frame,
            corner_radius=12,
            fg_color=ThemeConfig.BG_CARD,
            border_width=1,
            border_color=ThemeConfig.BORDER
        )
        left_box.grid(row=0, column=0, padx=(0, 14), sticky="nsew")
        left_box.grid_columnconfigure(0, weight=1)
        left_box.grid_rowconfigure(1, weight=1)

        left_title = ctk.CTkLabel(
            left_box,
            text="CLASS-WISE ENROLLMENT MATRIX (PG TO CLASS 10)",
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.TEXT_MUTED
        )
        left_title.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        # Class list scrollable container
        class_scroll = ctk.CTkScrollableFrame(left_box, fg_color="transparent")
        class_scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        class_scroll.grid_columnconfigure(0, weight=1)

        classes = self.student_repo.get_all_classes()
        for idx, c in enumerate(classes):
            c_name = c["name"]
            st_count = len(self.student_repo.search_students(class_id=c["id"], status="Active"))

            c_row = ctk.CTkFrame(class_scroll, fg_color=ThemeConfig.BG_CARD_ALT, corner_radius=6, height=36)
            c_row.pack(fill="x", pady=2)

            name_l = ctk.CTkLabel(c_row, text=f"  {c_name}", font=ThemeConfig.get_font(11, "bold"), text_color=ThemeConfig.TEXT_MAIN)
            name_l.pack(side="left", padx=8)

            badge = ctk.CTkLabel(
                c_row,
                text=f"{st_count} Students",
                font=ThemeConfig.get_font(10, "bold"),
                fg_color=ThemeConfig.PRIMARY[1],
                text_color="#FFFFFF",
                corner_radius=10,
                width=80,
                height=22
            )
            badge.pack(side="right", padx=8)

        # Right Panel: Quick Shortcuts & Actions
        right_box = ctk.CTkFrame(
            panel_frame,
            corner_radius=12,
            fg_color=ThemeConfig.BG_CARD,
            border_width=1,
            border_color=ThemeConfig.BORDER
        )
        right_box.grid(row=0, column=1, sticky="nsew")
        right_box.grid_columnconfigure(0, weight=1)

        rt_title = ctk.CTkLabel(
            right_box,
            text="QUICK ACTION DISPATCH",
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.TEXT_MUTED
        )
        rt_title.pack(anchor="w", padx=16, pady=(14, 12))

        actions = [
            ("students", "➕  Register New Student", ThemeConfig.PRIMARY),
            ("attendance", "📋  Mark Student Attendance", ThemeConfig.SUCCESS),
            ("fees", "💳  Process Fee Payments", ThemeConfig.SECONDARY),
            ("exams", "📊  Exam Marks & Statistical Insights", ThemeConfig.INFO),
            ("backup", "💾  Create Instant DB Backup", ThemeConfig.PRIMARY)
        ]

        for nav_key, label, color_tup in actions:
            btn = ctk.CTkButton(
                right_box,
                text=label,
                font=ThemeConfig.get_font(12, "bold"),
                fg_color=color_tup,
                hover_color=ThemeConfig.PRIMARY_HOVER,
                corner_radius=8,
                height=42,
                anchor="w",
                command=lambda k=nav_key: self.on_quick_nav(k)
            )
            btn.pack(fill="x", padx=16, pady=5)

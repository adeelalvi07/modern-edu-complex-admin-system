"""
Main Application Container Window for CustomTkinter.
Coordinates authentication, sidebar routing, and view lifecycles.
Configured with Official School Logo and Color Theme.
"""
from pathlib import Path
from PIL import Image, ImageTk
import customtkinter as ctk
from config import settings
from config.theme_config import ThemeConfig
from src.controllers.auth_controller import AuthController
from src.services.backup_service import BackupDaemon
from src.views.components.sidebar import Sidebar
from src.views.modules.login_view import LoginView
from src.views.modules.dashboard_view import DashboardView
from src.views.modules.student_view import StudentView
from src.views.modules.staff_view import StaffView
from src.views.modules.attendance_view import AttendanceView
from src.views.modules.fee_view import FeeView
from src.views.modules.exam_view import ExamView
from src.views.modules.backup_view import BackupView

class SchoolAppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Appearance & Geometry
        ctk.set_appearance_mode(ThemeConfig.APPEARANCE_MODE)
        ctk.set_default_color_theme(ThemeConfig.COLOR_THEME)

        self.title("Modern Educational Complex - Al-Qayyum Campus Management System")
        self.geometry("1260x800")
        self.minsize(1080, 700)

        # Set Taskbar / Window Icon to School Logo (Without Background)
        ico_path = settings.ASSETS_DIR / "logo.ico"
        if ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
            except Exception:
                pass

        logo_icon_path = settings.ASSETS_DIR / "logo_64.png"
        if not logo_icon_path.exists():
            logo_icon_path = settings.ASSETS_DIR / "logo_transparent.png"
        if logo_icon_path.exists():
            try:
                icon_img = ImageTk.PhotoImage(Image.open(logo_icon_path))
                self.iconphoto(False, icon_img)
            except Exception:
                pass

        # Background backup daemon
        self.backup_daemon = BackupDaemon(settings.AUTO_BACKUP_TIME)
        self.backup_daemon.start()

        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Active view tracking
        self.current_view = None
        self.sidebar = None
        self.content_container = None

        self._show_login_screen()

    def _show_login_screen(self):
        self._clear_views()

        # Explicitly reset grid layout weights so column 0 takes 100% full screen
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.login_view = LoginView(self, on_login_success=self._on_login_success)
        self.login_view.grid(row=0, column=0, sticky="nsew")

    def _on_login_success(self):
        self._clear_views()
        self._build_main_shell()

    def _build_main_shell(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0) # Sidebar fixed width
        self.grid_columnconfigure(1, weight=1) # Main content expandable

        user = AuthController.get_current_user() or {
            "username": "admin",
            "full_name": "Administrator",
            "role_name": "Admin"
        }

        # Sidebar
        self.sidebar = Sidebar(
            self,
            on_navigate=self._navigate_to_module,
            on_logout=self._do_logout,
            current_user=user
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Main Content Container
        self.content_container = ctk.CTkFrame(self, fg_color=ThemeConfig.BG_MAIN, corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_rowconfigure(0, weight=1)
        self.content_container.grid_columnconfigure(0, weight=1)

        # Default to Dashboard
        self._navigate_to_module("dashboard")

    def _navigate_to_module(self, module_key: str):
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None

        views_map = {
            "dashboard": lambda: DashboardView(self.content_container, on_quick_nav=self._quick_nav),
            "students": lambda: StudentView(self.content_container),
            "staff": lambda: StaffView(self.content_container),
            "attendance": lambda: AttendanceView(self.content_container),
            "fees": lambda: FeeView(self.content_container),
            "exams": lambda: ExamView(self.content_container),
            "backup": lambda: BackupView(self.content_container)
        }

        factory = views_map.get(module_key, lambda: DashboardView(self.content_container, on_quick_nav=self._quick_nav))
        self.current_view = factory()
        self.current_view.grid(row=0, column=0, sticky="nsew")

    def _quick_nav(self, module_key: str):
        if self.sidebar:
            self.sidebar.set_active(module_key)

    def _do_logout(self):
        AuthController().logout()
        self._clear_views()
        self._show_login_screen()

    def _clear_views(self):
        for widget in self.winfo_children():
            widget.destroy()
        self.sidebar = None
        self.current_view = None
        self.content_container = None

    def _on_close(self):
        if hasattr(self, "backup_daemon"):
            self.backup_daemon.stop()
        self.destroy()

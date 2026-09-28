"""
Modern Sleek Sidebar Navigation Component.
Styled according to the Official School Logo with logo graphic and gold accents.
"""
from pathlib import Path
from datetime import datetime
from PIL import Image
import customtkinter as ctk
from config import settings
from config.theme_config import ThemeConfig
from typing import Callable, Dict

class Sidebar(ctk.CTkFrame):
    def __init__(
        self,
        master,
        on_navigate: Callable[[str], None],
        on_logout: Callable[[], None],
        current_user: Dict,
        **kwargs
    ):
        super().__init__(
            master,
            width=240,
            corner_radius=0,
            fg_color=ThemeConfig.BG_SIDEBAR,
            border_width=1,
            border_color=ThemeConfig.BORDER,
            **kwargs
        )
        self.on_navigate = on_navigate
        self.on_logout = on_logout
        self.current_user = current_user
        self.nav_buttons: Dict[str, ctk.CTkButton] = {}
        self.active_module = "dashboard"

        self.grid_rowconfigure(9, weight=1) # Spacer push to bottom

        self._build_header()
        self._build_nav_links()
        self._build_footer()

    def _build_header(self):
        # Header Container
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=16, pady=(16, 12), sticky="ew")

        # Official Logo Image (Without Background)
        logo_path = settings.ASSETS_DIR / "logo_transparent.png"
        if not logo_path.exists():
            logo_path = settings.ASSETS_DIR / "logo_64.png"
        if logo_path.exists():
            pil_logo = Image.open(logo_path)
            self.logo_ctk_img = ctk.CTkImage(
                light_image=pil_logo,
                dark_image=pil_logo,
                size=(46, 46)
            )
            logo_lbl = ctk.CTkLabel(header_frame, image=self.logo_ctk_img, text="", fg_color="transparent")
            logo_lbl.pack(side="left", padx=(0, 10))
        else:
            badge = ctk.CTkLabel(
                header_frame,
                text="MEC",
                font=ThemeConfig.get_font(12, "bold"),
                fg_color=ThemeConfig.PRIMARY[1],
                text_color="#FFFFFF",
                corner_radius=6,
                width=42,
                height=28
            )
            badge.pack(side="left", padx=(0, 10))

        # Title and Motto
        titles_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        titles_box.pack(side="left", fill="x", expand=True)

        title_lbl = ctk.CTkLabel(
            titles_box,
            text="MODERN EDU",
            font=ThemeConfig.get_font(13, "bold"),
            text_color=ThemeConfig.TEXT_MAIN,
            anchor="w"
        )
        title_lbl.pack(fill="x")

        motto_lbl = ctk.CTkLabel(
            titles_box,
            text="AL-QAYYUM COMPLEX",
            font=ThemeConfig.get_font(9, "bold"),
            text_color=ThemeConfig.GOLD_ACCENT[1],
            anchor="w"
        )
        motto_lbl.pack(fill="x")

        # Divider with Gold Tint
        div = ctk.CTkFrame(self, height=2, fg_color=ThemeConfig.GOLD_ACCENT[1])
        div.grid(row=1, column=0, padx=16, pady=(0, 14), sticky="ew")

    def _build_nav_links(self):
        modules = [
            ("dashboard", "📊  Dashboard"),
            ("students", "👨‍🎓  Students"),
            ("staff", "👨‍🏫  Staff & Faculty"),
            ("attendance", "📅  Attendance"),
            ("fees", "💳  Fees & Finance"),
            ("exams", "📝  Examinations"),
            ("backup", "💾  Data Backup")
        ]

        for i, (key, label) in enumerate(modules, start=2):
            btn = ctk.CTkButton(
                self,
                text=label,
                anchor="w",
                font=ThemeConfig.get_font(12, "bold" if key == self.active_module else "normal"),
                fg_color=ThemeConfig.PRIMARY if key == self.active_module else "transparent",
                text_color="#FFFFFF" if key == self.active_module else ThemeConfig.TEXT_MAIN,
                hover_color=ThemeConfig.BG_HOVER,
                corner_radius=8,
                height=38,
                command=lambda k=key: self.set_active(k)
            )
            btn.grid(row=i, column=0, padx=12, pady=3, sticky="ew")
            self.nav_buttons[key] = btn

    def set_active(self, module_key: str):
        self.active_module = module_key
        for k, btn in self.nav_buttons.items():
            if k == module_key:
                btn.configure(
                    fg_color=ThemeConfig.PRIMARY,
                    text_color="#FFFFFF",
                    font=ThemeConfig.get_font(12, "bold")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=ThemeConfig.TEXT_MAIN,
                    font=ThemeConfig.get_font(12, "normal")
                )
        self.on_navigate(module_key)

    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=10, column=0, padx=12, pady=16, sticky="ew")

        # User Info Pill
        u_box = ctk.CTkFrame(
            footer,
            fg_color=ThemeConfig.BG_CARD,
            corner_radius=8,
            border_width=1,
            border_color=ThemeConfig.BORDER
        )
        u_box.pack(fill="x", pady=(0, 10))

        u_name = self.current_user.get("full_name", "Administrator")
        u_role = self.current_user.get("role_name", "Admin")

        name_lbl = ctk.CTkLabel(
            u_box,
            text=u_name,
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.TEXT_MAIN,
            anchor="w"
        )
        name_lbl.pack(fill="x", padx=10, pady=(6, 0))

        role_badge = ctk.CTkLabel(
            u_box,
            text=f"● {u_role}",
            font=ThemeConfig.get_font(10, "bold"),
            text_color=ThemeConfig.GOLD_ACCENT[1],
            anchor="w"
        )
        role_badge.pack(fill="x", padx=10, pady=(0, 6))

        # Appearance mode switch
        def toggle_mode():
            current = ctk.get_appearance_mode()
            new_mode = "Light" if current == "Dark" else "Dark"
            ctk.set_appearance_mode(new_mode)

        mode_btn = ctk.CTkButton(
            footer,
            text="🌓  Toggle Dark/Light",
            font=ThemeConfig.get_font(11),
            fg_color="transparent",
            text_color=ThemeConfig.TEXT_MUTED,
            hover_color=ThemeConfig.BG_HOVER,
            height=30,
            command=toggle_mode
        )
        mode_btn.pack(fill="x", pady=(0, 4))

        # Live Clock & Date Ticker
        self.sidebar_clock_lbl = ctk.CTkLabel(
            footer,
            text="",
            font=ThemeConfig.get_font(9, "bold"),
            text_color=ThemeConfig.GOLD_ACCENT[1]
        )
        self.sidebar_clock_lbl.pack(fill="x", pady=(0, 6))

        # Logout Button
        logout_btn = ctk.CTkButton(
            footer,
            text="🚪  Sign Out",
            font=ThemeConfig.get_font(11, "bold"),
            fg_color=ThemeConfig.DANGER,
            text_color="#FFFFFF",
            hover_color="#991B1B",
            height=32,
            command=self.on_logout
        )
        logout_btn.pack(fill="x")

        self._update_sidebar_clock()

    def _update_sidebar_clock(self):
        try:
            now = datetime.now()
            t_str = now.strftime("%I:%M:%S %p")
            d_str = now.strftime("%d %b %Y")
            if hasattr(self, "sidebar_clock_lbl"):
                self.sidebar_clock_lbl.configure(text=f"🕒 {t_str} • {d_str}")
        except Exception:
            pass
        self.after(1000, self._update_sidebar_clock)


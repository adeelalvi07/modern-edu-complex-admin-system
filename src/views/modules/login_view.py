"""
Modern Login Card View.
Styled with the Official School Logo, Colors, and Campus Watermark Background.
Designed with generous horizontal width and proportional vertical balance.
"""
from pathlib import Path
from PIL import Image
import customtkinter as ctk
from config import settings
from config.theme_config import ThemeConfig
from src.controllers.auth_controller import AuthController
from src.views.components.watermark import WatermarkManager
from typing import Callable

class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_login_success: Callable[[], None], **kwargs):
        super().__init__(master, fg_color=ThemeConfig.BG_MAIN, **kwargs)
        self.on_login_success = on_login_success
        self.auth_controller = AuthController()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Centered straight low-opacity campus watermark background
        WatermarkManager.apply(self, width=900, height=620)

        self._build_card()

    def _build_card(self):
        # Center card container with generous horizontal width (~590px)
        card = ctk.CTkFrame(
            self,
            corner_radius=18,
            fg_color=ThemeConfig.BG_CARD,
            border_width=1.5,
            border_color=ThemeConfig.BORDER
        )
        card.grid(row=0, column=0, padx=30, pady=20)
        card.grid_columnconfigure(0, weight=1)

        # Golden Top Accent Bar
        gold_line = ctk.CTkFrame(card, height=3, fg_color=ThemeConfig.GOLD_ACCENT[1], corner_radius=2)
        gold_line.grid(row=0, column=0, sticky="ew", padx=24, pady=(14, 6))

        # Official Logo Image (Without Background)
        logo_path = settings.ASSETS_DIR / "logo_transparent.png"
        if not logo_path.exists():
            logo_path = settings.ASSETS_DIR / "logo_128.png"
        if logo_path.exists():
            pil_logo = Image.open(logo_path)
            self.logo_ctk_img = ctk.CTkImage(
                light_image=pil_logo,
                dark_image=pil_logo,
                size=(80, 80)
            )
            logo_lbl = ctk.CTkLabel(card, image=self.logo_ctk_img, text="", fg_color="transparent")
            logo_lbl.grid(row=1, column=0, pady=(2, 6))
        else:
            badge = ctk.CTkLabel(
                card,
                text="MEC",
                font=ThemeConfig.get_font(14, "bold"),
                fg_color=ThemeConfig.PRIMARY[1],
                text_color="#FFFFFF",
                corner_radius=8,
                width=54,
                height=34
            )
            badge.grid(row=1, column=0, pady=(6, 6))

        # Title & Motto
        motto_lbl = ctk.CTkLabel(
            card,
            text="★  AL-QAYYUM  ★",
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.GOLD_ACCENT[1]
        )
        motto_lbl.grid(row=2, column=0, pady=(0, 2))

        title_lbl = ctk.CTkLabel(
            card,
            text="MODERN EDUCATIONAL COMPLEX",
            font=ThemeConfig.get_font(17, "bold"),
            text_color=ThemeConfig.TEXT_MAIN
        )
        title_lbl.grid(row=3, column=0, padx=36, pady=(0, 2))

        sub_lbl = ctk.CTkLabel(
            card,
            text="School Management System • Offline & Local LAN Edition",
            font=ThemeConfig.get_font(11, "normal"),
            text_color=ThemeConfig.TEXT_MUTED
        )
        sub_lbl.grid(row=4, column=0, padx=20, pady=(0, 14))

        # Form Inputs Container (Spacious width)
        form_frame = ctk.CTkFrame(card, fg_color="transparent")
        form_frame.grid(row=5, column=0, padx=46, sticky="ew")
        form_frame.grid_columnconfigure(0, weight=1)

        # Username Label
        u_lbl = ctk.CTkLabel(
            form_frame,
            text="Username",
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.TEXT_MAIN,
            anchor="w"
        )
        u_lbl.grid(row=0, column=0, sticky="w", pady=(0, 2))

        # Username Entry
        self.username_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter your username",
            font=ThemeConfig.get_font(12),
            width=380,
            height=40,
            corner_radius=8,
            fg_color=ThemeConfig.BG_INPUT,
            border_color=ThemeConfig.BORDER
        )
        self.username_entry.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Password Row (Label + Show Password toggle)
        p_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        p_row.grid(row=2, column=0, sticky="ew", pady=(0, 2))
        p_row.grid_columnconfigure(0, weight=1)

        p_lbl = ctk.CTkLabel(
            p_row,
            text="Password",
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.TEXT_MAIN,
            anchor="w"
        )
        p_lbl.pack(side="left")

        self.show_pwd_var = ctk.BooleanVar(value=False)
        def toggle_pwd():
            if self.show_pwd_var.get():
                self.password_entry.configure(show="")
            else:
                self.password_entry.configure(show="•")

        show_pwd_cb = ctk.CTkCheckBox(
            p_row,
            text="Show",
            variable=self.show_pwd_var,
            command=toggle_pwd,
            font=ThemeConfig.get_font(10),
            checkbox_width=18,
            checkbox_height=18,
            corner_radius=4,
            fg_color=ThemeConfig.PRIMARY[1]
        )
        show_pwd_cb.pack(side="right")

        # Password Entry
        self.password_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter your password",
            font=ThemeConfig.get_font(12),
            show="•",
            width=380,
            height=40,
            corner_radius=8,
            fg_color=ThemeConfig.BG_INPUT,
            border_color=ThemeConfig.BORDER
        )
        self.password_entry.grid(row=3, column=0, sticky="ew", pady=(0, 6))

        # Error / Feedback Label
        self.error_label = ctk.CTkLabel(
            form_frame,
            text="",
            font=ThemeConfig.get_font(11, "bold"),
            text_color=ThemeConfig.DANGER[1]
        )
        self.error_label.grid(row=4, column=0, sticky="w", pady=(0, 6))

        # Sign In Button
        self.login_btn = ctk.CTkButton(
            form_frame,
            text="🔒  Sign In to Dashboard",
            font=ThemeConfig.get_font(13, "bold"),
            fg_color=ThemeConfig.PRIMARY,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            height=42,
            corner_radius=8,
            command=self._do_login
        )
        self.login_btn.grid(row=5, column=0, sticky="ew", pady=(0, 14))

        # System Status Info Box
        info_box = ctk.CTkFrame(
            card,
            fg_color=ThemeConfig.BG_CARD_ALT,
            corner_radius=8,
            border_width=1,
            border_color=ThemeConfig.BORDER_LIGHT
        )
        info_box.grid(row=6, column=0, padx=46, pady=(0, 18), sticky="ew")

        info_lbl = ctk.CTkLabel(
            info_box,
            text="🔒 Authorized Personnel Only\n● 100% Offline Capable  •  ● Multi-Station LAN Ready",
            font=ThemeConfig.get_font(10, "normal"),
            text_color=ThemeConfig.TEXT_MUTED,
            justify="center"
        )
        info_lbl.pack(padx=16, pady=8)

        # Keyboard shortcuts
        self.username_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self._do_login())
        self.username_entry.focus()

    def _do_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.error_label.configure(text="Please enter both username and password.")
            return

        self.error_label.configure(text="Authenticating...", text_color=ThemeConfig.INFO[1])
        self.update_idletasks()

        success = self.auth_controller.login(username, password)
        if success:
            self.on_login_success()
        else:
            self.error_label.configure(
                text="Invalid username or password. Please try again.",
                text_color=ThemeConfig.DANGER[1]
            )

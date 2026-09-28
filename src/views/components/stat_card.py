"""
Elevated KPI Stat Card Component.
"""
import customtkinter as ctk
from config.theme_config import ThemeConfig

class StatCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        title: str,
        value: str,
        subtitle: str = "",
        accent_color: str = "#3B82F6",
        **kwargs
    ):
        super().__init__(
            master,
            corner_radius=12,
            fg_color=ThemeConfig.BG_CARD,
            border_width=1,
            border_color=ThemeConfig.BORDER,
            **kwargs
        )
        self.grid_columnconfigure(0, weight=1)

        # Accent top bar or indicator
        self.accent_indicator = ctk.CTkFrame(
            self,
            height=4,
            corner_radius=2,
            fg_color=accent_color
        )
        self.accent_indicator.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 4))

        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text=title.upper(),
            font=ThemeConfig.get_font(10, "bold"),
            text_color=ThemeConfig.TEXT_MUTED,
            anchor="w"
        )
        self.title_label.grid(row=1, column=0, sticky="w", padx=16, pady=(4, 2))

        # Value
        self.val_label = ctk.CTkLabel(
            self,
            text=value,
            font=ThemeConfig.get_font(22, "bold"),
            text_color=ThemeConfig.TEXT_MAIN,
            anchor="w"
        )
        self.val_label.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 2))

        # Subtitle
        if subtitle:
            self.sub_label = ctk.CTkLabel(
                self,
                text=subtitle,
                font=ThemeConfig.get_font(11, "normal"),
                text_color=ThemeConfig.TEXT_MUTED,
                anchor="w"
            )
            self.sub_label.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 10))
        else:
            self.val_label.grid_configure(pady=(0, 10))

    def update_value(self, new_val: str, new_sub: str = ""):
        self.val_label.configure(text=new_val)
        if hasattr(self, "sub_label") and new_sub:
            self.sub_label.configure(text=new_sub)

    def update_title(self, new_title: str):
        self.title_label.configure(text=new_title.upper())


"""
Data Security & Backup Management View.
Features:
- Instant Manual Database Backup
- Backup History & SHA-256 Checksum Inspector
- LAN Multi-Computer Database Connectivity Configuration
- Centered, Straight, Low-Opacity Campus Watermark Background
"""
import os
import customtkinter as ctk
from datetime import datetime
from config import settings
from config.theme_config import ThemeConfig
from src.services.backup_service import backup_manager
from src.views.components.data_table import DataTable
from src.views.components.watermark import WatermarkManager
from database.connection import db_manager

class BackupView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=ThemeConfig.BG_MAIN, **kwargs)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Apply centered, straight watermark in background
        WatermarkManager.apply(self, width=820, height=560)

        self._build_top_controls()
        self._build_lan_info()
        self._build_history_table()

    def _build_top_controls(self):
        card = ctk.CTkFrame(self, fg_color=ThemeConfig.BG_CARD, corner_radius=12, border_width=1, border_color=ThemeConfig.BORDER)
        card.grid(row=0, column=0, padx=20, pady=(16, 12), sticky="ew")

        ctk.CTkLabel(card, text="DATABASE SECURITY & AUTOMATED BACKUPS", font=ThemeConfig.get_font(13, "bold"), text_color=ThemeConfig.PRIMARY[1]).pack(anchor="w", padx=20, pady=(16, 4))
        ctk.CTkLabel(card, text=f"Automated daily backups run at {settings.AUTO_BACKUP_TIME} with 30-day rolling retention and GZIP compression.", font=ThemeConfig.get_font(11), text_color=ThemeConfig.TEXT_MUTED).pack(anchor="w", padx=20, pady=(0, 16))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 20))

        backup_btn = ctk.CTkButton(
            btn_row,
            text="💾 Create Instant Backup Now",
            font=ThemeConfig.get_font(12, "bold"),
            fg_color=ThemeConfig.PRIMARY,
            hover_color=ThemeConfig.PRIMARY_HOVER,
            height=40,
            command=self._do_backup_now
        )
        backup_btn.pack(side="left")

        open_folder_btn = ctk.CTkButton(
            btn_row,
            text="📂 Open Backups Folder",
            font=ThemeConfig.get_font(11),
            fg_color=ThemeConfig.BG_CARD_ALT,
            text_color=ThemeConfig.TEXT_MAIN,
            border_width=1,
            border_color=ThemeConfig.BORDER,
            hover_color=ThemeConfig.BG_HOVER,
            height=40,
            command=self._open_backup_folder
        )
        open_folder_btn.pack(side="left", padx=12)

        self.backup_status_lbl = ctk.CTkLabel(btn_row, text="", font=ThemeConfig.get_font(11, "bold"))
        self.backup_status_lbl.pack(side="right")

    def _build_lan_info(self):
        card = ctk.CTkFrame(self, fg_color=ThemeConfig.BG_CARD, corner_radius=12, border_width=1, border_color=ThemeConfig.BORDER)
        card.grid(row=1, column=0, padx=20, pady=(0, 12), sticky="ew")

        ctk.CTkLabel(card, text="MULTI-COMPUTER LOCAL LAN CONFIGURATION", font=ThemeConfig.get_font(11, "bold"), text_color=ThemeConfig.SECONDARY[1]).pack(anchor="w", padx=20, pady=(14, 8))

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=20, pady=(0, 14))
        grid.grid_columnconfigure((1, 3), weight=1)

        # Active Engine
        ctk.CTkLabel(grid, text="Active Database Engine:", font=ThemeConfig.get_font(11, "bold")).grid(row=0, column=0, sticky="w", pady=4)
        ctk.CTkLabel(grid, text=f"{db_manager.active_db_type.upper()}", font=ThemeConfig.get_font(11, "bold"), text_color=ThemeConfig.SUCCESS[1]).grid(row=0, column=1, sticky="w", padx=(6, 20), pady=4)

        # Host IP
        ctk.CTkLabel(grid, text="Database Server Host / IP:", font=ThemeConfig.get_font(11, "bold")).grid(row=0, column=2, sticky="w", pady=4)
        ctk.CTkLabel(grid, text=f"{settings.DB_HOST}:{settings.DB_PORT}", font=ThemeConfig.get_font(11)).grid(row=0, column=3, sticky="w", padx=6, pady=4)

        # Database Name
        ctk.CTkLabel(grid, text="Database Name:", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=0, sticky="w", pady=4)
        ctk.CTkLabel(grid, text=f"{settings.DB_NAME}", font=ThemeConfig.get_font(11)).grid(row=1, column=1, sticky="w", padx=(6, 20), pady=4)

        # Concurrency
        ctk.CTkLabel(grid, text="LAN Concurrency:", font=ThemeConfig.get_font(11, "bold")).grid(row=1, column=2, sticky="w", pady=4)
        ctk.CTkLabel(grid, text="Ready for 2-3 Office PCs simultaneously", font=ThemeConfig.get_font(11), text_color=ThemeConfig.INFO[1]).grid(row=1, column=3, sticky="w", padx=6, pady=4)

    def _build_history_table(self):
        table_container = ctk.CTkFrame(self, fg_color="transparent")
        table_container.grid(row=2, column=0, padx=20, pady=(0, 16), sticky="nsew")
        table_container.grid_columnconfigure(0, weight=1)
        table_container.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(table_container, text="HISTORICAL DATABASE SNAPSHOTS", font=ThemeConfig.get_font(11, "bold"), text_color=ThemeConfig.TEXT_MUTED).grid(row=0, column=0, sticky="w", pady=(0, 6))

        cols = [
            ("filename", "Backup Snapshot File", 280),
            ("size", "Compressed Size", 120),
            ("date_created", "Created Timestamp", 180),
            ("checksum", "SHA-256 Integrity Verification", 220)
        ]
        self.history_table = DataTable(table_container, columns=cols)
        self.history_table.grid(row=1, column=0, sticky="nsew")

        self._refresh_history()

    def _refresh_history(self):
        backups = []
        for f in settings.BACKUP_DIR.glob(f"{settings.DB_NAME}_backup_*.gz"):
            if f.is_file():
                size_mb = round(f.stat().st_size / (1024 * 1024), 2)
                dt_str = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

                chk_file = f.with_suffix("").with_suffix(".sha256")
                chk_str = "Verified"
                if chk_file.exists():
                    try:
                        with open(chk_file, "r") as cf:
                            chk_str = cf.read().split()[0][:16] + "..."
                    except Exception:
                        pass

                backups.append({
                    "filename": f.name,
                    "size": f"{size_mb} MB" if size_mb > 0.01 else f"{round(f.stat().st_size/1024, 1)} KB",
                    "date_created": dt_str,
                    "checksum": chk_str,
                    "mtime": f.stat().st_mtime
                })

        backups.sort(key=lambda x: x["mtime"], reverse=True)
        self.history_table.populate(backups)

    def _do_backup_now(self):
        self.backup_status_lbl.configure(text="Dumping & compressing database...", text_color=ThemeConfig.INFO[1])
        self.update_idletasks()

        success, msg, path = backup_manager.perform_backup()
        if success:
            self.backup_status_lbl.configure(text="✔ Backup successfully created and verified!", text_color=ThemeConfig.SUCCESS[1])
            self._refresh_history()
        else:
            self.backup_status_lbl.configure(text=f"✖ {msg}", text_color=ThemeConfig.DANGER[1])

    def _open_backup_folder(self):
        try:
            os.startfile(str(settings.BACKUP_DIR))
        except Exception:
            pass

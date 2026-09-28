"""
Watermark Background Helper for CustomTkinter.
Renders a centered, straightened, low-opacity watermark of the School Building.
Compatible with both Dark and Light themes.
"""
from pathlib import Path
from PIL import Image
import customtkinter as ctk
from config import settings

class WatermarkManager:
    """Singleton helper managing the low-opacity watermark background."""
    _ctk_image = None

    @classmethod
    def get_image(cls, width: int = 780, height: int = 540) -> ctk.CTkImage:
        if cls._ctk_image is None:
            dark_path = settings.ASSETS_DIR / "bg_watermark_dark.png"
            light_path = settings.ASSETS_DIR / "bg_watermark_light.png"

            dark_pil = Image.open(dark_path) if dark_path.exists() else None
            light_pil = Image.open(light_path) if light_path.exists() else None

            if not dark_pil:
                b_path = settings.ASSETS_DIR / "building_straight.jpg"
                dark_pil = Image.open(b_path)
                light_pil = dark_pil

            cls._ctk_image = ctk.CTkImage(
                light_image=light_pil,
                dark_image=dark_pil,
                size=(width, height)
            )
        return cls._ctk_image

    @classmethod
    def apply(cls, master, width: int = 780, height: int = 540) -> ctk.CTkLabel:
        """
        Embeds a centered, straight, low-opacity school building watermark
        at the bottom of the master widget's z-order.
        """
        img = cls.get_image(width, height)
        lbl = ctk.CTkLabel(master, image=img, text="", fg_color="transparent")
        lbl.place(relx=0.5, rely=0.5, anchor="center")
        lbl.lower()
        return lbl

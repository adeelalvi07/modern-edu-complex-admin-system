"""
Theme and UI Styling Configuration for CustomTkinter.
Curated to match the Official School Logo:
- Deep Forest Emerald & Pine Jade
- Metallic Academic Gold
- Modern High-Contrast Light & Dark Modes
"""

class ThemeConfig:
    APPEARANCE_MODE = "dark"
    COLOR_THEME = "green"

    # Backgrounds
    BG_MAIN = ("#F3F6F4", "#0A1310")          # Soft Mint White / Deep Forest Charcoal
    BG_SIDEBAR = ("#FFFFFF", "#070E0C")       # Pure White / Obsidian Pine
    BG_CARD = ("#FFFFFF", "#12201B")          # Card surface: White / Deep Pine
    BG_CARD_ALT = ("#F7FAF8", "#172A24")      # Subtle elevated surface
    BG_INPUT = ("#F7FAF8", "#152620")         # Input fields
    BG_HOVER = ("#E5ECE9", "#1E362E")         # Hover highlight

    # Brand Colors (From School Logo)
    PRIMARY = ("#1E5647", "#2D7D68")          # Rich Forest Emerald
    PRIMARY_HOVER = ("#153E33", "#236353")
    SECONDARY = ("#B8860B", "#D4AF37")        # Royal Academic Gold
    SECONDARY_HOVER = ("#946D06", "#C59E2E")
    GOLD_ACCENT = ("#C59E3F", "#E5C158")      # Light Champagne Gold
    ACCENT_EMERALD = ("#15803D", "#22C55E")   # Bright Emerald

    # Status Colors
    SUCCESS = ("#166534", "#22C55E")          # Present / Paid / Active
    SUCCESS_BG = ("#DCFCE7", "#052E16")
    WARNING = ("#B45309", "#F59E0B")          # Late / Partial / Pending
    WARNING_BG = ("#FEF3C7", "#451A03")
    DANGER = ("#B91C1C", "#EF4444")           # Absent / Defaulter / Fail
    DANGER_HOVER = ("#991B1B", "#DC2626")
    DANGER_BG = ("#FEE2E2", "#450A0A")
    INFO = ("#0F766E", "#14B8A6")             # Notice / Stats Teal

    # Typography / Text
    TEXT_MAIN = ("#0E1D18", "#F0F5F2")        # Primary headings / body
    TEXT_MUTED = ("#556B62", "#8FA79D")       # Subtitles / placeholders
    TEXT_INVERTED = ("#FFFFFF", "#0E1D18")
    TEXT_ACCENT = ("#B8860B", "#E5C158")      # Gold Text Accent

    # Borders & Dividers
    BORDER = ("#DCE4E0", "#223B31")
    BORDER_LIGHT = ("#EBF0EE", "#182C24")

    # Font Families & Scales
    FONT_FAMILY = "Segoe UI"

    @classmethod
    def get_font(cls, size: int = 13, weight: str = "normal"):
        return (cls.FONT_FAMILY, size, weight)

    @classmethod
    def font_title(cls):
        return (cls.FONT_FAMILY, 22, "bold")

    @classmethod
    def font_h2(cls):
        return (cls.FONT_FAMILY, 16, "bold")

    @classmethod
    def font_h3(cls):
        return (cls.FONT_FAMILY, 14, "bold")

    @classmethod
    def font_body(cls):
        return (cls.FONT_FAMILY, 12, "normal")

    @classmethod
    def font_body_bold(cls):
        return (cls.FONT_FAMILY, 12, "bold")

    @classmethod
    def font_small(cls):
        return (cls.FONT_FAMILY, 10, "normal")

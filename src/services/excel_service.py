"""
Excel Import and Export Service using openpyxl.
Allows exporting student lists, fee defaulter registers, and attendance sheets.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from config import settings

class ExcelService:
    @staticmethod
    def export_defaulter_list(defaulters: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
        if not output_path:
            filename = f"Defaulters_List_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            output_path = str(settings.EXPORTS_DIR / filename)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Fee Defaulters"

        # Headers
        headers = [
            "Invoice No", "Admission No", "Student Name", "Class", "Section",
            "Father Name", "Phone", "Month/Year", "Net Payable", "Paid", "Balance Due", "Due Date"
        ]
        ws.append(headers)

        # Style Header
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Append Data
        for d in defaulters:
            ws.append([
                d.get("invoice_number"),
                d.get("admission_number"),
                f"{d.get('first_name')} {d.get('last_name')}",
                d.get("class_name"),
                d.get("section_name"),
                d.get("father_name"),
                d.get("father_phone"),
                f"{d.get('billing_month')}/{d.get('billing_year')}",
                float(d.get("net_payable", 0)),
                float(d.get("paid_amount", 0)),
                float(d.get("balance_amount", 0)),
                str(d.get("due_date"))
            ])

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(output_path)
        return output_path

    @staticmethod
    def export_daily_attendance_summary(
        records: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        attendance_date: str,
        output_path: Optional[str] = None
    ) -> str:
        """Exports school-wide daily attendance summary for any date to Excel."""
        if not output_path:
            settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
            filename = f"Daily_Attendance_{attendance_date}_{datetime.now().strftime('%H%M%S')}.xlsx"
            output_path = str(settings.EXPORTS_DIR / filename)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Attendance {attendance_date}"

        # Title Row
        ws.append([f"AL-QAYYUM MODERN EDUCATIONAL COMPLEX - DAILY ATTENDANCE REPORT ({attendance_date})"])
        ws.append([
            f"Total Enrolled: {metrics.get('total_enrolled', 0)}",
            f"Total Present: {metrics.get('total_present', 0)}",
            f"Total Absent: {metrics.get('total_absent', 0)}",
            f"Attendance Rate: {metrics.get('overall_percentage', 0)}%",
            f"Classes Marked: {metrics.get('classes_completed', 0)}/{metrics.get('classes_count', 0)}"
        ])
        ws.append([])

        headers = [
            "Class & Section", "Total Enrolled", "Marked Students", "Present", "Absent", "Late", "Excused", "Attendance %", "Status"
        ]
        ws.append(headers)

        header_fill = PatternFill(start_color="1E5647", end_color="1E5647", fill_type="solid")
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        for cell in ws[4]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for r in records:
            ws.append([
                r.get("display_class", f"{r.get('class_name')} - {r.get('section_name')}"),
                r.get("total_enrolled", 0),
                r.get("marked_count", 0),
                r.get("present_count", 0),
                r.get("absent_count", 0),
                r.get("late_count", 0),
                r.get("excused_count", 0),
                f"{r.get('percentage', 0)}%",
                r.get("status", "")
            ])

        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

        wb.save(output_path)
        return output_path


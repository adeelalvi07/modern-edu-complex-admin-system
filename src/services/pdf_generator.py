"""
High-Performance Offline PDF Generation Engine using ReportLab.
Generates:
1. 3-Part Standard Fee Challans (Student Copy, School Office Copy, Bank Copy)
2. Academic Term Report Cards
3. Single Fee Payment Receipts
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from config import settings

class PDFGenerator:
    """PDF Generator for official school documentation."""

    @staticmethod
    def generate_fee_voucher(invoice: Dict[str, Any], items: List[Dict[str, Any]], output_path: Optional[str] = None) -> str:
        """
        Generates a 3-part Fee Voucher (Student Copy, School Copy, Bank Copy).
        """
        if not output_path:
            filename = f"Challan_{invoice.get('invoice_number', '001')}.pdf"
            output_path = str(settings.EXPORTS_DIR / filename)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20
        )
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ChallanTitle',
            parent=styles['Heading1'],
            fontSize=12,
            leading=14,
            alignment=1, # Center
            textColor=colors.HexColor('#1E3A8A'),
            fontName='Helvetica-Bold'
        )
        sub_style = ParagraphStyle(
            'ChallanSub',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,
            alignment=1,
            textColor=colors.HexColor('#475569')
        )
        label_style = ParagraphStyle(
            'Label',
            fontSize=8,
            leading=10,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#0F172A')
        )
        val_style = ParagraphStyle(
            'Val',
            fontSize=8,
            leading=10,
            fontName='Helvetica',
            textColor=colors.HexColor('#1E293B')
        )

        copies = ["STUDENT COPY", "SCHOOL OFFICE COPY", "BANK / CASHIER COPY"]

        def build_copy_block(copy_title: str) -> Table:
            # Header
            header_table = Table([
                [Paragraph(f"<b>{settings.SCHOOL_NAME}</b>", title_style)],
                [Paragraph(settings.SCHOOL_ADDRESS, sub_style)],
                [Paragraph(f"<b>FEE CHALLAN - {copy_title}</b>", ParagraphStyle('H2', fontSize=9, alignment=1, textColor=colors.HexColor('#DC2626'), fontName='Helvetica-Bold'))]
            ], colWidths=[540])

            # Info block
            info_data = [
                [
                    Paragraph(f"<b>Challan No:</b> {invoice.get('invoice_number')}", val_style),
                    Paragraph(f"<b>Issue Date:</b> {invoice.get('issue_date')}", val_style),
                    Paragraph(f"<b>Due Date:</b> {invoice.get('due_date')}", val_style)
                ],
                [
                    Paragraph(f"<b>Student:</b> {invoice.get('first_name')} {invoice.get('last_name')}", val_style),
                    Paragraph(f"<b>Class:</b> {invoice.get('class_name')} - {invoice.get('section_name')}", val_style),
                    Paragraph(f"<b>Adm No:</b> {invoice.get('admission_number')}", val_style)
                ]
            ]
            info_table = Table(info_data, colWidths=[180, 180, 180])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))

            # Fee breakdown table
            items_data = [["Fee Description", "Amount (PKR)"]]
            for it in items:
                items_data.append([it.get("fee_head_name", "Fee"), f"{float(it.get('amount', 0)):,.2f}"])
            items_data.append(["<b>Total Payable:</b>", f"<b>PKR {float(invoice.get('net_payable', 0)):,.2f}</b>"])

            items_table = Table(items_data, colWidths=[380, 160])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 8),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                ('TOPPADDING', (0,0), (-1,-1), 3),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
                ('ALIGN', (1,0), (1,-1), 'RIGHT'),
                ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#F1F5F9')),
            ]))

            # Signature
            sig_data = [["Cashier / Bank Stamp: ___________________", "Authorized Signature: ___________________"]]
            sig_table = Table(sig_data, colWidths=[270, 270])
            sig_table.setStyle(TableStyle([
                ('FONTSIZE', (0,0), (-1,-1), 7),
                ('TOPPADDING', (0,0), (-1,-1), 10),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ]))

            block_data = [
                [header_table],
                [Spacer(1, 3)],
                [info_table],
                [Spacer(1, 3)],
                [items_table],
                [Spacer(1, 2)],
                [sig_table],
                [Spacer(1, 8)]
            ]
            return Table(block_data, colWidths=[540])

        for copy_name in copies:
            story.append(build_copy_block(copy_name))

        doc.build(story)
        return output_path

    @staticmethod
    def generate_report_card(data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Generates an official Academic Term Report Card.
        """
        st = data.get("student", {})
        if not output_path:
            filename = f"ReportCard_{st.get('admission_number', '001')}.pdf"
            output_path = str(settings.EXPORTS_DIR / filename)

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=25,
            leftMargin=25,
            topMargin=25,
            bottomMargin=25
        )
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            alignment=1,
            textColor=colors.HexColor('#1E3A8A'),
            fontName='Helvetica-Bold'
        )
        sub_style = ParagraphStyle(
            'ReportSub',
            fontSize=9,
            alignment=1,
            textColor=colors.HexColor('#475569')
        )
        bold_lbl = ParagraphStyle('BoldLbl', fontSize=9, fontName='Helvetica-Bold', textColor=colors.HexColor('#0F172A'))
        reg_val = ParagraphStyle('RegVal', fontSize=9, fontName='Helvetica', textColor=colors.HexColor('#334155'))

        story.append(Paragraph(f"<b>{settings.SCHOOL_NAME}</b>", title_style))
        story.append(Paragraph(f"{settings.SCHOOL_TAGLINE} | {settings.SCHOOL_ADDRESS}", sub_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"<b>OFFICIAL ACADEMIC PROGRESS REPORT - {st.get('exam_name', 'Examination')}</b>", ParagraphStyle('ExamName', fontSize=12, alignment=1, textColor=colors.HexColor('#2563EB'), fontName='Helvetica-Bold')))
        story.append(Spacer(1, 15))

        # Student Details Box
        info_data = [
            [
                Paragraph("<b>Student Name:</b>", bold_lbl),
                Paragraph(f"{st.get('first_name', '')} {st.get('last_name', '')}", reg_val),
                Paragraph("<b>Admission No:</b>", bold_lbl),
                Paragraph(str(st.get('admission_number', '')), reg_val)
            ],
            [
                Paragraph("<b>Father's Name:</b>", bold_lbl),
                Paragraph(str(st.get('father_name', '')), reg_val),
                Paragraph("<b>Roll Number:</b>", bold_lbl),
                Paragraph(str(st.get('roll_number', '')), reg_val)
            ],
            [
                Paragraph("<b>Class & Section:</b>", bold_lbl),
                Paragraph(f"{st.get('class_name', '')} - {st.get('section_name', '')}", reg_val),
                Paragraph("<b>Academic Year:</b>", bold_lbl),
                Paragraph(str(st.get('session_name', '2026-2027')), reg_val)
            ]
        ]
        info_table = Table(info_data, colWidths=[110, 160, 110, 160])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 15))

        # Marks Grid
        marks_rows = data.get("marks", [])
        table_data = [["Subject", "Max Marks", "Passing", "Obtained", "Grade", "Remarks"]]
        for m in marks_rows:
            is_abs = bool(m.get("is_absent", False))
            if is_abs:
                obt = "ABS"
            elif m.get("marks_obtained") is not None:
                obt = f"{float(m['marks_obtained']):.1f}"
            else:
                obt = "--"
            table_data.append([
                str(m.get("subject_name", "")),
                f"{float(m.get('max_marks', 100)):.0f}",
                f"{float(m.get('passing_marks', 40)):.0f}",
                obt,
                str(m.get("grade", "-")),
                str(m.get("teacher_remarks") or "")
            ])

        # Summary Row
        table_data.append([
            "<b>GRAND TOTAL</b>",
            f"<b>{data.get('total_max', 0):.0f}</b>",
            "-",
            f"<b>{data.get('total_obtained', 0):.1f}</b>",
            f"<b>{data.get('grade', '-')}</b>",
            f"<b>{data.get('percentage', 0)}%</b>"
        ])

        marks_table = Table(table_data, colWidths=[160, 75, 70, 75, 60, 100])
        marks_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 9),
            ('ALIGN', (1,0), (4,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EEF2F6')),
        ]))
        story.append(marks_table)
        story.append(Spacer(1, 30))

        # Signatures
        sig_data = [["Class Teacher Signature", "Exam Controller", "Principal Signature & Stamp"]]
        sig_table = Table(sig_data, colWidths=[180, 180, 180])
        sig_table.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,0), 1, colors.HexColor('#475569')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(sig_table)

        doc.build(story)
        return output_path

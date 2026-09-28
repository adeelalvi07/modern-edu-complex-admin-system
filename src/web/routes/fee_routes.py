"""
Fees, Invoicing, Counter POS Payments, and Defaulters API Endpoints.
Includes PDF Challan generation and Excel exports.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date
from pathlib import Path

from database.connection import db_manager
from src.repositories.fee_repository import FeeRepository
from src.repositories.student_repository import StudentRepository
from src.services.pdf_generator import PDFGenerator
from src.services.excel_service import ExcelService
from src.web.auth import get_current_user, require_admin
from config import settings

router = APIRouter(prefix="/api/fees", tags=["Fees"])
fee_repo = FeeRepository()
student_repo = StudentRepository()


class GenerateVouchersRequest(BaseModel):
    class_id: int
    billing_month: int
    billing_year: int
    due_date: str


class FeePaymentRequest(BaseModel):
    invoice_id: int
    amount_paid: float
    payment_mode: Optional[str] = "Cash"
    reference_number: Optional[str] = None
    remarks: Optional[str] = None
    payment_date: Optional[str] = None


class FeeStructureItem(BaseModel):
    fee_head_id: int
    amount: float
    frequency: Optional[str] = "Monthly"


class UpdateFeeStructureRequest(BaseModel):
    class_id: int
    items: List[FeeStructureItem]


@router.get("/fee-heads")
def get_fee_heads(current_user: dict = Depends(get_current_user)):
    """Returns active fee heads (Tuition, Admission, Sports, Exam)."""
    return {"success": True, "fee_heads": fee_repo.get_all_fee_heads()}


@router.get("/structures")
def get_fee_structures(
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Returns fee structure configured for a specific class."""
    session = student_repo.get_current_session()
    session_id = session["id"] if session else 1
    structure = fee_repo.get_fee_structure(class_id, session_id)
    return {"success": True, "class_id": class_id, "session_id": session_id, "structure": structure}


@router.post("/structures")
def update_fee_structure(
    payload: UpdateFeeStructureRequest,
    current_user: dict = Depends(require_admin)
):
    """Sets fee amounts per head for a class."""
    session = student_repo.get_current_session()
    session_id = session["id"] if session else 1

    for item in payload.items:
        fee_repo.set_fee_structure(
            session_id=session_id,
            class_id=payload.class_id,
            fee_head_id=item.fee_head_id,
            amount=item.amount,
            frequency=item.frequency or "Monthly"
        )
    return {"success": True, "message": "Fee structure updated successfully"}


@router.post("/vouchers/generate")
def generate_vouchers(
    payload: GenerateVouchersRequest,
    current_user: dict = Depends(require_admin)
):
    """Batch generates monthly fee invoices for all enrolled students in a class."""
    session = student_repo.get_current_session()
    session_id = session["id"] if session else 1

    count = fee_repo.generate_monthly_vouchers(
        class_id=payload.class_id,
        session_id=session_id,
        month=payload.billing_month,
        year=payload.billing_year,
        due_date_str=payload.due_date
    )
    return {
        "success": True,
        "message": f"Generated {count} fee vouchers for month {payload.billing_month}/{payload.billing_year}.",
        "vouchers_generated": count
    }


@router.get("/invoices")
def list_invoices(
    class_id: Optional[int] = None,
    section_id: Optional[int] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Searches fee invoices with multiple filters."""
    invoices = fee_repo.search_invoices(
        class_id=class_id,
        section_id=section_id,
        month=month,
        year=year,
        status=status,
        search_term=search
    )
    return {"success": True, "count": len(invoices), "invoices": invoices}


@router.get("/invoices/{invoice_id}")
def get_invoice_details(
    invoice_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Fetches single invoice details, line items, and payment history."""
    query = """
        SELECT 
            fi.*, s.admission_number, s.first_name, s.last_name,
            c.name as class_name, sec.name as section_name,
            p.father_name, p.father_phone, p.emergency_contact
        FROM fee_invoices fi
        JOIN students s ON fi.student_id = s.id
        JOIN parents_guardians p ON s.parent_id = p.id
        JOIN classes c ON fi.class_id = c.id
        JOIN sections sec ON fi.section_id = sec.id
        WHERE fi.id = :id
    """
    inv = db_manager.fetch_one(query, {"id": invoice_id})
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    items = db_manager.fetch_all(
        """SELECT fii.*, fh.name as fee_head_name
           FROM fee_invoice_items fii
           JOIN fee_heads fh ON fii.fee_head_id = fh.id
           WHERE fii.invoice_id = :id""",
        {"id": invoice_id}
    )
    payments = db_manager.fetch_all(
        """SELECT fp.*, u.full_name as received_by_name
           FROM fee_payments fp
           LEFT JOIN users u ON fp.received_by = u.id
           WHERE fp.invoice_id = :id ORDER BY fp.id DESC""",
        {"id": invoice_id}
    )
    return {"success": True, "invoice": inv, "items": items, "payments": payments}


@router.post("/pay")
def process_fee_payment(
    payload: FeePaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Processes counter fee collection, creates payment record and issues receipt."""
    if payload.amount_paid <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be greater than 0")

    receipt_num = fee_repo.process_payment(
        invoice_id=payload.invoice_id,
        amount_paid=payload.amount_paid,
        payment_mode=payload.payment_mode or "Cash",
        reference_number=payload.reference_number,
        received_by_user_id=current_user.get("sub") or current_user.get("id"),
        remarks=payload.remarks,
        payment_date=payload.payment_date or date.today().isoformat()
    )
    if not receipt_num:
        raise HTTPException(status_code=404, detail="Invoice not found or payment failed")

    return {
        "success": True,
        "message": f"Payment recorded successfully. Receipt No: {receipt_num}",
        "receipt_number": receipt_num
    }


@router.get("/defaulters")
def get_defaulters(
    class_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Lists all students with outstanding unpaid/partially paid invoices."""
    defaulters = fee_repo.get_defaulters(class_id=class_id)
    total_dues = sum(float(d.get("balance_amount", 0)) for d in defaulters)
    return {
        "success": True,
        "count": len(defaulters),
        "total_dues": total_dues,
        "defaulters": defaulters
    }


@router.get("/invoice/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Generates and serves official 3-part Fee Voucher PDF."""
    inv = db_manager.fetch_one(
        """SELECT fi.*, s.admission_number, s.first_name, s.last_name,
                  c.name as class_name, sec.name as section_name,
                  p.father_name
           FROM fee_invoices fi
           JOIN students s ON fi.student_id = s.id
           JOIN parents_guardians p ON s.parent_id = p.id
           JOIN classes c ON fi.class_id = c.id
           JOIN sections sec ON fi.section_id = sec.id
           WHERE fi.id = :id""",
        {"id": invoice_id}
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    items = db_manager.fetch_all(
        """SELECT fii.amount, fh.name as fee_head_name
           FROM fee_invoice_items fii
           JOIN fee_heads fh ON fii.fee_head_id = fh.id
           WHERE fii.invoice_id = :id""",
        {"id": invoice_id}
    )

    pdf_path = PDFGenerator.generate_fee_voucher(inv, items)
    if not Path(pdf_path).exists():
        raise HTTPException(status_code=500, detail="Failed to generate PDF")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"Challan_{inv['invoice_number']}.pdf"
    )


@router.get("/defaulters/excel")
def download_defaulters_excel(
    class_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generates and downloads Excel spreadsheet of fee defaulters."""
    defaulters = fee_repo.get_defaulters(class_id=class_id)
    excel_path = ExcelService.export_defaulter_list(defaulters)
    if not Path(excel_path).exists():
        raise HTTPException(status_code=500, detail="Failed to generate Excel file")

    return FileResponse(
        path=excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=Path(excel_path).name
    )

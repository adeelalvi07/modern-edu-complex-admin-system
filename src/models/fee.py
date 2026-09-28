"""
Fee and Finance Domain Models.
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import date, datetime

@dataclass
class FeeHead:
    id: Optional[int]
    name: str
    description: Optional[str] = None
    is_active: bool = True

@dataclass
class FeeStructure:
    id: Optional[int]
    academic_session_id: int
    class_id: int
    fee_head_id: int
    amount: float
    frequency: str = "Monthly"
    fee_head_name: Optional[str] = None
    class_name: Optional[str] = None

@dataclass
class FeeInvoiceItem:
    id: Optional[int]
    invoice_id: int
    fee_head_id: int
    amount: float
    fee_head_name: Optional[str] = None

@dataclass
class FeeInvoice:
    id: Optional[int]
    invoice_number: str
    student_id: int
    academic_session_id: int
    class_id: int
    section_id: int
    billing_month: int
    billing_year: int
    issue_date: date
    due_date: date
    gross_amount: float
    discount_amount: float
    fine_amount: float
    net_payable: float
    paid_amount: float = 0.0
    balance_amount: float = 0.0
    status: str = "Unpaid"
    student_name: Optional[str] = None
    admission_number: Optional[str] = None
    class_name: Optional[str] = None
    section_name: Optional[str] = None
    items: Optional[List[FeeInvoiceItem]] = None

@dataclass
class FeePayment:
    id: Optional[int]
    invoice_id: int
    receipt_number: str
    payment_date: date
    amount_paid: float
    payment_mode: str = "Cash"
    reference_number: Optional[str] = None
    received_by: Optional[int] = None
    remarks: Optional[str] = None

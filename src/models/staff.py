"""
Staff, Department, and Subject Domain Models.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

@dataclass
class Staff:
    id: Optional[int]
    employee_code: str
    department_id: int
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    designation: str
    joining_date: date
    contact_phone: str
    basic_salary: float
    user_id: Optional[int] = None
    cnic_nid: Optional[str] = None
    qualification: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    bank_account_info: Optional[str] = None
    is_active: bool = True
    department_name: Optional[str] = None

@dataclass
class Subject:
    id: Optional[int]
    class_id: int
    subject_name: str
    subject_code: Optional[str] = None
    total_marks: float = 100.0
    passing_marks: float = 40.0
    class_name: Optional[str] = None

@dataclass
class StaffPayroll:
    id: Optional[int]
    staff_id: int
    payroll_month: int
    payroll_year: int
    basic_salary: float
    allowances: float = 0.0
    deductions: float = 0.0
    net_salary: float = 0.0
    payment_status: str = "Pending"
    payment_method: str = "Cash"
    payment_date: Optional[date] = None
    transaction_ref: Optional[str] = None
    remarks: Optional[str] = None

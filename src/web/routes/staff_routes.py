"""
Staff, Faculty, and Payroll API Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date

from database.connection import db_manager
from src.repositories.staff_repository import StaffRepository
from src.web.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/staff", tags=["Staff"])
staff_repo = StaffRepository()


class StaffCreateRequest(BaseModel):
    first_name: str
    last_name: str
    gender: str = "Male"
    cnic_nid: Optional[str] = None
    date_of_birth: str
    qualification: Optional[str] = None
    department_id: int
    designation: str
    joining_date: Optional[str] = None
    contact_phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    basic_salary: float = 0.0
    bank_account_info: Optional[str] = None


class StaffUpdateRequest(BaseModel):
    first_name: str
    last_name: str
    gender: str
    cnic_nid: Optional[str] = None
    date_of_birth: str
    qualification: Optional[str] = None
    department_id: int
    designation: str
    contact_phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    basic_salary: float
    bank_account_info: Optional[str] = None
    is_active: bool = True


@router.get("/departments/all")
def get_departments(current_user: dict = Depends(get_current_user)):
    """Returns list of staff departments."""
    return {"success": True, "departments": staff_repo.get_all_departments()}


@router.get("")
def list_staff(
    department_id: Optional[int] = None,
    search: Optional[str] = None,
    status: Optional[str] = "Active",
    current_user: dict = Depends(get_current_user)
):
    """Searches staff members with filters."""
    staff_members = staff_repo.get_all_staff(
        department_id=department_id,
        search_term=search,
        status_filter=status
    )
    return {"success": True, "count": len(staff_members), "staff": staff_members}


@router.get("/{staff_id}")
def get_staff_details(
    staff_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Returns single staff member details."""
    staff = staff_repo.get_staff_by_id(staff_id)
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    payroll = db_manager.fetch_all(
        """SELECT * FROM staff_payroll WHERE staff_id = :sid ORDER BY payroll_year DESC, payroll_month DESC LIMIT 12""",
        {"sid": staff_id}
    )
    return {"success": True, "staff": staff, "payroll": payroll}


@router.post("")
def add_staff_member(
    payload: StaffCreateRequest,
    current_user: dict = Depends(require_admin)
):
    """Registers a new staff member with auto-generated code."""
    emp_code = staff_repo.generate_employee_code()
    join_date = payload.joining_date or date.today().isoformat()

    data = {
        "emp_code": emp_code,
        "dept_id": payload.department_id,
        "fn": payload.first_name.strip(),
        "ln": payload.last_name.strip(),
        "gen": payload.gender,
        "cnic": payload.cnic_nid,
        "dob": payload.date_of_birth,
        "qual": payload.qualification,
        "desig": payload.designation.strip(),
        "join_date": join_date,
        "phone": payload.contact_phone.strip(),
        "email": payload.email,
        "addr": payload.address,
        "salary": payload.basic_salary,
        "bank": payload.bank_account_info
    }

    try:
        new_id = staff_repo.add_staff(data)
        return {
            "success": True,
            "message": f"Staff member added successfully with Code: {emp_code}",
            "staff_id": new_id,
            "employee_code": emp_code
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add staff: {str(e)}")


@router.put("/{staff_id}")
def update_staff_member(
    staff_id: int,
    payload: StaffUpdateRequest,
    current_user: dict = Depends(require_admin)
):
    """Updates staff profile details."""
    data = {
        "department_id": payload.department_id,
        "first_name": payload.first_name.strip(),
        "last_name": payload.last_name.strip(),
        "gender": payload.gender,
        "cnic_nid": payload.cnic_nid,
        "date_of_birth": payload.date_of_birth,
        "qualification": payload.qualification,
        "designation": payload.designation.strip(),
        "contact_phone": payload.contact_phone.strip(),
        "email": payload.email,
        "address": payload.address,
        "basic_salary": payload.basic_salary,
        "bank_account_info": payload.bank_account_info,
        "is_active": 1 if payload.is_active else 0
    }
    success = staff_repo.update_staff(staff_id, data)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update staff member")

    return {"success": True, "message": "Staff details updated successfully"}


@router.delete("/{staff_id}")
def delete_staff_member(
    staff_id: int,
    current_user: dict = Depends(require_admin)
):
    """Permanently deletes staff member and related records (Admin only)."""
    success, message = staff_repo.delete_staff_permanently(staff_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}

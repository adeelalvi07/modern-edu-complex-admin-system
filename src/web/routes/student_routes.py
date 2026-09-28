"""
Student and Admissions API Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date

from database.connection import db_manager
from src.repositories.student_repository import StudentRepository
from src.web.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/students", tags=["Students"])
student_repo = StudentRepository()


class StudentRegisterRequest(BaseModel):
    # Student Details
    first_name: str
    last_name: str
    gender: str
    date_of_birth: str
    blood_group: Optional[str] = "O+"
    religion: Optional[str] = "Islam"
    registration_date: Optional[str] = None
    admission_number: Optional[str] = None
    # Parent / Guardian Details
    father_name: str
    father_phone: str
    father_cnic_nid: Optional[str] = None
    father_occupation: Optional[str] = None
    father_email: Optional[str] = None
    mother_name: Optional[str] = None
    emergency_contact: str
    residential_address: str
    guardian_relation: Optional[str] = "Father"
    # Enrollment Details
    class_id: int
    section_id: int
    roll_number: int


class StudentUpdateRequest(BaseModel):
    first_name: str
    last_name: str
    gender: str
    date_of_birth: str
    blood_group: Optional[str] = None
    religion: Optional[str] = "Islam"
    status: Optional[str] = "Active"
    father_name: str
    father_phone: str
    father_cnic_nid: Optional[str] = None
    father_occupation: Optional[str] = None
    father_email: Optional[str] = None
    mother_name: Optional[str] = None
    emergency_contact: str
    residential_address: str
    class_id: Optional[int] = None
    section_id: Optional[int] = None
    roll_number: Optional[int] = None


@router.get("")
def list_students(
    search: Optional[str] = None,
    class_id: Optional[int] = None,
    section_id: Optional[int] = None,
    status: Optional[str] = "Active",
    current_user: dict = Depends(get_current_user)
):
    """Searches and lists students with filters."""
    students = student_repo.search_students(
        search_term=search,
        class_id=class_id,
        section_id=section_id,
        status=status
    )
    return {"success": True, "count": len(students), "students": students}


@router.get("/next-admission-no")
def get_next_admission_no(current_user: dict = Depends(get_current_user)):
    """Generates preview of next sequential admission number."""
    adm_no = student_repo.generate_admission_number()
    return {"success": True, "admission_number": adm_no}


@router.get("/classes/all")
def get_classes_and_sections(current_user: dict = Depends(get_current_user)):
    """Returns all 13 standard classes and their respective sections."""
    classes = student_repo.get_all_classes()
    result = []
    for c in classes:
        sections = student_repo.get_sections_by_class(c["id"])
        result.append({
            "id": c["id"],
            "name": c["name"],
            "numeric_order": c["numeric_order"],
            "sections": sections
        })
    return {"success": True, "classes": result}


@router.get("/{student_id}")
def get_student_details(student_id: int, current_user: dict = Depends(get_current_user)):
    """Retrieves full student profile, parent info, and quick overview."""
    student = student_repo.get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Invoices history
    invoices = db_manager.fetch_all(
        """SELECT id, invoice_number, billing_month, billing_year, net_payable, paid_amount, balance_amount, status, due_date
           FROM fee_invoices WHERE student_id = :sid ORDER BY id DESC LIMIT 10""",
        {"sid": student_id}
    )

    # Attendance summary
    att_summary = db_manager.fetch_one(
        """SELECT 
               COUNT(*) as total_days,
               SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_days,
               SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
               SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late_days
           FROM student_attendance WHERE student_id = :sid""",
        {"sid": student_id}
    )
    tot = (att_summary["total_days"] if att_summary else 0) or 0
    pres = (att_summary["present_days"] if att_summary else 0) or 0
    att_pct = round((pres / tot) * 100, 1) if tot > 0 else 0.0

    return {
        "success": True,
        "student": student,
        "invoices": invoices,
        "attendance": {
            "total_days": tot,
            "present_days": pres,
            "absent_days": (att_summary["absent_days"] if att_summary else 0) or 0,
            "late_days": (att_summary["late_days"] if att_summary else 0) or 0,
            "percentage": att_pct
        }
    }


@router.post("/register")
def register_student(
    payload: StudentRegisterRequest,
    current_user: dict = Depends(require_admin)
):
    """Registers a new student, guardian, and enrolls in class."""
    session = student_repo.get_current_session()
    session_id = session["id"] if session else 1

    adm_number = payload.admission_number or student_repo.generate_admission_number()
    reg_date = payload.registration_date or date.today().isoformat()

    student_data = {
        "admission_number": adm_number,
        "registration_date": reg_date,
        "first_name": payload.first_name.strip(),
        "last_name": payload.last_name.strip(),
        "gender": payload.gender,
        "date_of_birth": payload.date_of_birth,
        "blood_group": payload.blood_group,
        "religion": payload.religion or "Islam",
        "photo_path": None
    }

    parent_data = {
        "father_name": payload.father_name.strip(),
        "father_phone": payload.father_phone.strip(),
        "father_cnic_nid": payload.father_cnic_nid,
        "father_occupation": payload.father_occupation,
        "father_email": payload.father_email,
        "mother_name": payload.mother_name,
        "mother_phone": None,
        "guardian_relation": payload.guardian_relation or "Father",
        "emergency_contact": payload.emergency_contact.strip(),
        "residential_address": payload.residential_address.strip()
    }

    enrollment_data = {
        "academic_session_id": session_id,
        "class_id": payload.class_id,
        "section_id": payload.section_id,
        "roll_number": payload.roll_number
    }

    try:
        new_student_id = student_repo.register_student(student_data, parent_data, enrollment_data)
        return {
            "success": True,
            "message": f"Student registered successfully with Admission No: {adm_number}",
            "student_id": new_student_id,
            "admission_number": adm_number
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")


@router.put("/{student_id}")
def update_student(
    student_id: int,
    payload: StudentUpdateRequest,
    current_user: dict = Depends(require_admin)
):
    """Updates student and parent information."""
    student_data = {
        "first_name": payload.first_name.strip(),
        "last_name": payload.last_name.strip(),
        "gender": payload.gender,
        "date_of_birth": payload.date_of_birth,
        "blood_group": payload.blood_group,
        "religion": payload.religion,
        "status": payload.status or "Active",
        "photo_path": None
    }
    parent_data = {
        "father_name": payload.father_name.strip(),
        "father_phone": payload.father_phone.strip(),
        "father_cnic_nid": payload.father_cnic_nid,
        "father_occupation": payload.father_occupation,
        "father_email": payload.father_email,
        "mother_name": payload.mother_name,
        "emergency_contact": payload.emergency_contact.strip(),
        "residential_address": payload.residential_address.strip()
    }
    enrollment_data = None
    if payload.class_id and payload.section_id and payload.roll_number:
        session = student_repo.get_current_session()
        enrollment_data = {
            "academic_session_id": session["id"] if session else 1,
            "class_id": payload.class_id,
            "section_id": payload.section_id,
            "roll_number": payload.roll_number
        }

    success = student_repo.update_student(student_id, student_data, parent_data, enrollment_data)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update student")

    return {"success": True, "message": "Student information updated successfully"}


class StudentStatusUpdateRequest(BaseModel):
    status: str
    remarks: Optional[str] = None


@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    current_user: dict = Depends(require_admin)
):
    """Permanently deletes student and associated records (Admin only)."""
    success, message = student_repo.delete_student_permanently(student_id)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"success": True, "message": message}


@router.patch("/{student_id}/status")
def change_student_status(
    student_id: int,
    payload: StudentStatusUpdateRequest,
    current_user: dict = Depends(require_admin)
):
    """Changes student status: Active, Inactive, Graduated, Transferred (Admin only)."""
    success = student_repo.change_student_status(student_id, payload.status, payload.remarks)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update student status")
    return {"success": True, "message": f"Student status updated to '{payload.status}'"}

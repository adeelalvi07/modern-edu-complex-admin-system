"""
Attendance System API Endpoints for Students & Staff.
Fast batch entry, roster loading, chronic absentees analytics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date, timedelta

from database.connection import db_manager
from src.repositories.attendance_repository import AttendanceRepository
from src.repositories.student_repository import StudentRepository
from src.web.auth import get_current_user

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])
attendance_repo = AttendanceRepository()
student_repo = StudentRepository()


class StudentAttendanceRecord(BaseModel):
    student_id: int
    status: str
    remarks: Optional[str] = None


class BatchAttendanceRequest(BaseModel):
    class_id: int
    section_id: int
    attendance_date: str
    records: List[StudentAttendanceRecord]


class StaffAttendanceRecord(BaseModel):
    staff_id: int
    status: str
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    remarks: Optional[str] = None


class BatchStaffAttendanceRequest(BaseModel):
    attendance_date: str
    records: List[StaffAttendanceRecord]


@router.get("/roster")
def get_class_roster(
    class_id: int,
    section_id: int,
    attendance_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Retrieves class roster for marking attendance on a target date."""
    target_date = attendance_date or date.today().isoformat()
    session = student_repo.get_current_session()
    session_id = session["id"] if session else 1

    roster = attendance_repo.get_class_roster_for_attendance(
        class_id=class_id,
        section_id=section_id,
        target_date=target_date,
        session_id=session_id
    )
    return {
        "success": True,
        "class_id": class_id,
        "section_id": section_id,
        "attendance_date": target_date,
        "count": len(roster),
        "students": roster
    }


@router.post("/save-batch")
def save_batch_attendance(
    payload: BatchAttendanceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Saves daily batch attendance for a class and section atomically."""
    formatted_records = [
        {
            "student_id": r.student_id,
            "status": r.status,
            "remarks": r.remarks
        }
        for r in payload.records
    ]

    saved = attendance_repo.save_batch_student_attendance(
        class_id=payload.class_id,
        section_id=payload.section_id,
        attendance_date=payload.attendance_date,
        records=formatted_records,
        marked_by_user_id=current_user.get("sub") or current_user.get("id")
    )
    return {
        "success": True,
        "message": f"Successfully saved attendance for {saved} students on {payload.attendance_date}."
    }


@router.get("/daily-summary")
def get_daily_attendance_summary(
    attendance_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Returns school-wide daily class-by-class attendance breakdown."""
    target_date = attendance_date or date.today().isoformat()
    breakdown = attendance_repo.get_daily_school_attendance_summary(target_date)
    metrics = attendance_repo.get_school_attendance_metrics(target_date)

    return {
        "success": True,
        "attendance_date": target_date,
        "metrics": metrics,
        "classes": breakdown
    }


@router.get("/chronic-absentees")
def get_chronic_absentees(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    threshold: float = 75.0,
    class_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Retrieves students with attendance below threshold."""
    if not end_date:
        end_date = date.today().isoformat()
    if not start_date:
        # Default to past 30 days
        start_date = (date.today() - timedelta(days=30)).isoformat()

    absentees = attendance_repo.get_chronic_absentees(
        start_date=start_date,
        end_date=end_date,
        threshold_percentage=threshold,
        class_id=class_id
    )
    return {
        "success": True,
        "start_date": start_date,
        "end_date": end_date,
        "threshold": threshold,
        "count": len(absentees),
        "absentees": absentees
    }


@router.get("/staff")
def get_staff_roster_attendance(
    attendance_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Retrieves staff list and attendance on a specific date."""
    target_date = attendance_date or date.today().isoformat()
    query = """
        SELECT 
            s.id as staff_id,
            s.employee_code,
            s.first_name,
            s.last_name,
            s.designation,
            d.name as department_name,
            COALESCE(sa.status, 'Present') as status,
            sa.check_in_time,
            sa.check_out_time,
            sa.remarks
        FROM staff s
        JOIN staff_departments d ON s.department_id = d.id
        LEFT JOIN staff_attendance sa 
            ON s.id = sa.staff_id 
            AND sa.attendance_date = :adate
        WHERE s.is_active = 1
        ORDER BY s.id ASC
    """
    staff_list = db_manager.fetch_all(query, {"adate": target_date})
    return {"success": True, "date": target_date, "count": len(staff_list), "staff": staff_list}


@router.post("/staff/save-batch")
def save_batch_staff_attendance(
    payload: BatchStaffAttendanceRequest,
    current_user: dict = Depends(get_current_user)
):
    """Saves staff attendance for a given date."""
    marked_by = current_user.get("sub") or current_user.get("id")
    with db_manager.transaction() as conn:
        from sqlalchemy import text
        for r in payload.records:
            existing = conn.execute(
                text("SELECT id FROM staff_attendance WHERE staff_id = :sid AND attendance_date = :adate"),
                {"sid": r.staff_id, "adate": payload.attendance_date}
            ).mappings().first()

            if existing:
                conn.execute(
                    text("""UPDATE staff_attendance SET
                                status = :st, check_in_time = :cin, check_out_time = :cout, remarks = :rem, marked_by = :uid
                            WHERE id = :id"""),
                    {
                        "id": existing["id"],
                        "st": r.status,
                        "cin": r.check_in_time,
                        "cout": r.check_out_time,
                        "rem": r.remarks,
                        "uid": marked_by
                    }
                )
            else:
                conn.execute(
                    text("""INSERT INTO staff_attendance (staff_id, attendance_date, status, check_in_time, check_out_time, remarks, marked_by)
                            VALUES (:sid, :adate, :st, :cin, :cout, :rem, :uid)"""),
                    {
                        "sid": r.staff_id,
                        "adate": payload.attendance_date,
                        "st": r.status,
                        "cin": r.check_in_time,
                        "cout": r.check_out_time,
                        "rem": r.remarks,
                        "uid": marked_by
                    }
                )
    return {"success": True, "message": f"Staff attendance saved for {len(payload.records)} members."}

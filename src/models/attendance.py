"""
Attendance Domain Models.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

@dataclass
class StudentAttendanceRecord:
    id: Optional[int]
    student_id: int
    class_id: int
    section_id: int
    attendance_date: date
    status: str  # 'Present', 'Absent', 'Late', 'Half Day', 'Excused'
    remarks: Optional[str] = None
    marked_by: Optional[int] = None
    student_name: Optional[str] = None
    admission_number: Optional[str] = None
    roll_number: Optional[int] = None

@dataclass
class StaffAttendanceRecord:
    id: Optional[int]
    staff_id: int
    attendance_date: date
    status: str  # 'Present', 'Absent', 'Late', 'On Leave'
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    remarks: Optional[str] = None
    marked_by: Optional[int] = None
    staff_name: Optional[str] = None
    employee_code: Optional[str] = None

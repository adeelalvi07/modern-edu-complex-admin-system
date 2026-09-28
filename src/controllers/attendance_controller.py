"""
Attendance Business Logic Controller.
"""
from typing import Dict, Any, List, Optional
from datetime import date
from src.repositories.attendance_repository import AttendanceRepository

class AttendanceController:
    def __init__(self):
        self.repo = AttendanceRepository()

    def get_roster(self, class_id: int, section_id: int, target_date: str, session_id: int) -> List[Dict[str, Any]]:
        return self.repo.get_class_roster_for_attendance(class_id, section_id, target_date, session_id)

    def save_roster_attendance(
        self,
        class_id: int,
        section_id: int,
        attendance_date: str,
        records: List[Dict[str, Any]],
        marked_by_user_id: Optional[int] = None
    ) -> int:
        return self.repo.save_batch_student_attendance(
            class_id, section_id, attendance_date, records, marked_by_user_id
        )

    def get_chronic_absentees_report(
        self,
        start_date: str,
        end_date: str,
        threshold: float = 75.0,
        class_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        return self.repo.get_chronic_absentees(start_date, end_date, threshold, class_id)

    def get_daily_school_summary(self, attendance_date: str, session_id: Optional[int] = None) -> List[Dict[str, Any]]:
        return self.repo.get_daily_school_attendance_summary(attendance_date, session_id)

    def get_school_metrics(self, attendance_date: str, session_id: Optional[int] = None) -> Dict[str, Any]:
        return self.repo.get_school_attendance_metrics(attendance_date, session_id)


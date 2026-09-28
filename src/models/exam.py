"""
Academic Examination and Grading Domain Models.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

@dataclass
class Exam:
    id: Optional[int]
    academic_session_id: int
    name: str
    start_date: date
    end_date: date
    status: str = "Scheduled"
    session_name: Optional[str] = None

@dataclass
class ExamSubject:
    id: Optional[int]
    exam_id: int
    class_id: int
    subject_id: int
    exam_date: Optional[date] = None
    max_marks: float = 100.0
    passing_marks: float = 40.0
    subject_name: Optional[str] = None
    class_name: Optional[str] = None

@dataclass
class ExamMark:
    id: Optional[int]
    exam_subject_id: int
    student_id: int
    marks_obtained: float
    is_absent: bool = False
    grade: Optional[str] = None
    teacher_remarks: Optional[str] = None
    student_name: Optional[str] = None
    admission_number: Optional[str] = None
    roll_number: Optional[int] = None
    subject_name: Optional[str] = None
    max_marks: Optional[float] = 100.0

@dataclass
class GradingScale:
    id: Optional[int]
    grade_name: str
    min_percentage: float
    max_percentage: float
    grade_point: Optional[float] = None
    remarks: Optional[str] = None

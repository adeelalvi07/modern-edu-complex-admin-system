"""
Academic Exams, Marks Entry, Grading, and Report Cards API Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path

from database.connection import db_manager
from src.repositories.exam_repository import ExamRepository
from src.repositories.student_repository import StudentRepository
from src.services.pdf_generator import PDFGenerator
from src.web.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/exams", tags=["Exams"])
exam_repo = ExamRepository()
student_repo = StudentRepository()


class CreateExamRequest(BaseModel):
    name: str
    start_date: str
    end_date: str


class ScheduleSubjectRequest(BaseModel):
    exam_id: int
    class_id: int
    subject_id: int
    exam_date: Optional[str] = None
    max_marks: float = 100.0
    passing_marks: float = 40.0


class StudentMarkItem(BaseModel):
    student_id: int
    marks_obtained: float = 0.0
    is_absent: bool = False
    teacher_remarks: Optional[str] = None


class BatchMarksRequest(BaseModel):
    exam_subject_id: int
    records: List[StudentMarkItem]


@router.get("")
def list_exams(current_user: dict = Depends(get_current_user)):
    """Lists all scheduled and past examination terms."""
    session = student_repo.get_current_session()
    session_id = session["id"] if session else 1
    exams = exam_repo.get_all_exams(session_id=session_id)
    return {"success": True, "exams": exams}


@router.post("")
def create_exam(
    payload: CreateExamRequest,
    current_user: dict = Depends(require_admin)
):
    """Creates a new examination session."""
    session = student_repo.get_current_session()
    session_id = session["id"] if session else 1

    new_id = exam_repo.create_exam(
        session_id=session_id,
        name=payload.name.strip(),
        start_date=payload.start_date,
        end_date=payload.end_date
    )
    return {"success": True, "message": "Exam term created successfully", "exam_id": new_id}


@router.get("/{exam_id}/subjects")
def get_exam_subjects(
    exam_id: int,
    class_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Retrieves scheduled subjects for an exam term in a given class."""
    subjects = exam_repo.get_exam_subjects(exam_id=exam_id, class_id=class_id)
    # Also fetch all available class subjects so user can schedule new ones
    all_subjects = db_manager.fetch_all(
        "SELECT * FROM subjects WHERE class_id = :cid ORDER BY subject_name ASC",
        {"cid": class_id}
    )
    return {
        "success": True,
        "exam_id": exam_id,
        "class_id": class_id,
        "scheduled_subjects": subjects,
        "available_subjects": all_subjects
    }


@router.post("/schedule-subject")
def schedule_subject(
    payload: ScheduleSubjectRequest,
    current_user: dict = Depends(require_admin)
):
    """Adds a subject to an exam term schedule."""
    exam_repo.schedule_exam_subject(
        exam_id=payload.exam_id,
        class_id=payload.class_id,
        subject_id=payload.subject_id,
        exam_date=payload.exam_date,
        max_marks=payload.max_marks,
        passing_marks=payload.passing_marks
    )
    return {"success": True, "message": "Exam subject scheduled successfully"}


@router.get("/marks/roster")
def get_marks_roster(
    exam_subject_id: int,
    class_id: int,
    section_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Loads student roster for entering marks in a specific exam paper."""
    session = student_repo.get_current_session()
    session_id = session["id"] if session else 1

    roster = exam_repo.get_students_for_marking(
        exam_subject_id=exam_subject_id,
        class_id=class_id,
        section_id=section_id,
        session_id=session_id
    )

    subj_info = db_manager.fetch_one(
        """SELECT es.*, s.subject_name, e.name as exam_name
           FROM exam_subjects es
           JOIN subjects s ON es.subject_id = s.id
           JOIN exams e ON es.exam_id = e.id
           WHERE es.id = :id""",
        {"id": exam_subject_id}
    )

    return {
        "success": True,
        "subject_info": subj_info,
        "count": len(roster),
        "students": roster
    }


@router.post("/marks/save-batch")
def save_batch_marks(
    payload: BatchMarksRequest,
    current_user: dict = Depends(get_current_user)
):
    """Batch saves student marks and calculates grades."""
    records = [
        {
            "student_id": r.student_id,
            "marks_obtained": r.marks_obtained,
            "is_absent": r.is_absent,
            "teacher_remarks": r.teacher_remarks
        }
        for r in payload.records
    ]
    saved = exam_repo.save_batch_marks(
        exam_subject_id=payload.exam_subject_id,
        records=records,
        entered_by=current_user.get("sub") or current_user.get("id")
    )
    return {"success": True, "message": f"Successfully updated marks for {saved} students."}


@router.get("/report-card/{student_id}")
def download_student_report_card(
    student_id: int,
    exam_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Generates and downloads formal Academic Report Card PDF."""
    student = student_repo.get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    exam = db_manager.fetch_one("SELECT * FROM exams WHERE id = :id", {"id": exam_id})
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    # Fetch marks obtained in all subjects
    marks_query = """
        SELECT 
            s.subject_name, s.subject_code,
            es.max_marks, es.passing_marks,
            em.marks_obtained, em.is_absent, em.grade, em.teacher_remarks
        FROM exam_subjects es
        JOIN subjects s ON es.subject_id = s.id
        LEFT JOIN exam_marks em 
            ON es.id = em.exam_subject_id 
            AND em.student_id = :sid
        WHERE es.exam_id = :eid AND es.class_id = :cid
        ORDER BY s.subject_name ASC
    """
    subjects_marks = db_manager.fetch_all(marks_query, {
        "sid": student_id,
        "eid": exam_id,
        "cid": student["class_id"]
    })

    pdf_path = PDFGenerator.generate_report_card(
        student_info=student,
        exam_info=exam,
        subjects_data=subjects_marks
    )
    if not Path(pdf_path).exists():
        raise HTTPException(status_code=500, detail="Failed to generate Report Card PDF")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=Path(pdf_path).name
    )

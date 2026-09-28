"""
Academic, Examination, Grading, and Marks Repository.
"""
from typing import Optional, List, Dict, Any
from src.repositories.base_repository import BaseRepository

class ExamRepository(BaseRepository):
    def get_all_exams(self, session_id: Optional[int] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT e.*, s.session_name 
            FROM exams e
            JOIN academic_sessions s ON e.academic_session_id = s.id
            WHERE 1=1
        """
        params: Dict[str, Any] = {}
        if session_id:
            query += " AND e.academic_session_id = :sid"
            params["sid"] = session_id
        query += " ORDER BY e.id DESC"
        return self.db.fetch_all(query, params)

    def create_exam(self, session_id: int, name: str, start_date: str, end_date: str) -> int:
        sql = """
            INSERT INTO exams (academic_session_id, name, start_date, end_date, status)
            VALUES (:sid, :name, :sdate, :edate, 'Scheduled')
        """
        self.db.execute_query(sql, {"sid": session_id, "name": name, "sdate": start_date, "edate": end_date})
        row = self.db.fetch_one("SELECT id FROM exams ORDER BY id DESC LIMIT 1")
        return row["id"] if row else 0

    def get_exam_subjects(self, exam_id: int, class_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT es.*, s.subject_name, s.subject_code, s.total_marks, s.passing_marks
            FROM exam_subjects es
            JOIN subjects s ON es.subject_id = s.id
            WHERE es.exam_id = :eid AND es.class_id = :cid
            ORDER BY s.subject_name ASC
        """
        return self.db.fetch_all(query, {"eid": exam_id, "cid": class_id})

    def schedule_exam_subject(self, exam_id: int, class_id: int, subject_id: int, exam_date: Optional[str] = None, max_marks: float = 100.0, passing_marks: float = 40.0):
        # Insert if not exists
        existing = self.db.fetch_one(
            "SELECT id FROM exam_subjects WHERE exam_id = :eid AND class_id = :cid AND subject_id = :sid",
            {"eid": exam_id, "cid": class_id, "sid": subject_id}
        )
        if not existing:
            self.db.execute_query(
                """INSERT INTO exam_subjects (exam_id, class_id, subject_id, exam_date, max_marks, passing_marks)
                   VALUES (:eid, :cid, :sid, :edate, :max_m, :pass_m)""",
                {"eid": exam_id, "cid": class_id, "sid": subject_id, "edate": exam_date, "max_m": max_marks, "pass_m": passing_marks}
            )

    def get_students_for_marking(self, exam_subject_id: int, class_id: int, section_id: int, session_id: int) -> List[Dict[str, Any]]:
        """Retrieves students for entering marks in a specific exam paper."""
        query = """
            SELECT 
                s.id as student_id,
                s.admission_number,
                s.first_name,
                s.last_name,
                se.roll_number,
                em.marks_obtained,
                COALESCE(em.is_absent, 0) as is_absent,
                em.grade,
                em.teacher_remarks
            FROM student_enrollments se
            JOIN students s ON se.student_id = s.id
            LEFT JOIN exam_marks em 
                ON s.id = em.student_id 
                AND em.exam_subject_id = :esid
            WHERE se.class_id = :cid 
              AND se.section_id = :secid
              AND se.academic_session_id = :asid
              AND s.status = 'Active'
            ORDER BY se.roll_number ASC
        """
        return self.db.fetch_all(query, {
            "esid": exam_subject_id,
            "cid": class_id,
            "secid": section_id,
            "asid": session_id
        })

    def save_batch_marks(self, exam_subject_id: int, records: List[Dict[str, Any]], entered_by: Optional[int] = None) -> int:
        """Saves or updates student marks and automatically assigns grades."""
        from src.controllers.exam_controller import calculate_grade

        # Fetch max marks for this exam subject
        subj = self.db.fetch_one("SELECT max_marks, passing_marks FROM exam_subjects WHERE id = :id", {"id": exam_subject_id})
        max_marks = float(subj["max_marks"]) if subj else 100.0

        saved = 0
        with self.db.transaction() as conn:
            from sqlalchemy import text
            for rec in records:
                is_absent = bool(rec.get("is_absent", False))
                marks = 0.0 if is_absent else float(rec.get("marks_obtained", 0.0))
                pct = (marks / max_marks) * 100.0 if max_marks > 0 else 0.0
                grade = "ABS" if is_absent else calculate_grade(pct)

                existing = conn.execute(
                    text("SELECT id FROM exam_marks WHERE exam_subject_id = :esid AND student_id = :sid"),
                    {"esid": exam_subject_id, "sid": rec["student_id"]}
                ).mappings().first()

                if existing:
                    conn.execute(
                        text("""UPDATE exam_marks SET
                                    marks_obtained = :m,
                                    is_absent = :abs,
                                    grade = :g,
                                    teacher_remarks = :rem,
                                    entered_by = :uid,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = :id"""),
                        {
                            "m": marks,
                            "abs": 1 if is_absent else 0,
                            "g": grade,
                            "rem": rec.get("teacher_remarks"),
                            "uid": entered_by,
                            "id": existing["id"]
                        }
                    )
                else:
                    conn.execute(
                        text("""INSERT INTO exam_marks (
                                    exam_subject_id, student_id, marks_obtained, is_absent, grade, teacher_remarks, entered_by
                                ) VALUES (
                                    :esid, :sid, :m, :abs, :g, :rem, :uid
                                )"""),
                        {
                            "esid": exam_subject_id,
                            "sid": rec["student_id"],
                            "m": marks,
                            "abs": 1 if is_absent else 0,
                            "g": grade,
                            "rem": rec.get("teacher_remarks"),
                            "uid": entered_by
                        }
                    )
                saved += 1
        return saved

    def get_subject_mark_distribution(self, exam_subject_id: int) -> List[float]:
        """Returns list of marks obtained for statistical distribution."""
        rows = self.db.fetch_all(
            "SELECT marks_obtained FROM exam_marks WHERE exam_subject_id = :id AND is_absent = 0",
            {"id": exam_subject_id}
        )
        return [float(r["marks_obtained"]) for r in rows]

    def get_subjects_by_class(self, class_id: int) -> List[Dict[str, Any]]:
        """Returns all subjects configured for a specific class."""
        query = """
            SELECT s.*, c.name as class_name,
                   (SELECT COUNT(*) FROM exam_subjects es WHERE es.subject_id = s.id) as exam_count
            FROM subjects s
            JOIN classes c ON s.class_id = c.id
            WHERE s.class_id = :cid
            ORDER BY s.subject_name ASC
        """
        return self.db.fetch_all(query, {"cid": class_id})

    def add_subject_to_class(
        self, class_id: int, subject_name: str, subject_code: Optional[str] = None,
        total_marks: float = 100.0, passing_marks: float = 40.0
    ) -> tuple[bool, str, Optional[int]]:
        """Adds a new subject to a specific class after verifying uniqueness."""
        name_clean = subject_name.strip()
        if not name_clean:
            return False, "Subject name cannot be empty.", None

        existing = self.db.fetch_one(
            "SELECT id FROM subjects WHERE class_id = :cid AND LOWER(subject_name) = LOWER(:name)",
            {"cid": class_id, "name": name_clean}
        )
        if existing:
            return False, f"Subject '{name_clean}' already exists for this class.", None

        code_clean = (subject_code.strip() if subject_code else "") or name_clean[:3].upper()

        sql = """
            INSERT INTO subjects (class_id, subject_name, subject_code, total_marks, passing_marks)
            VALUES (:cid, :name, :code, :total, :passing)
        """
        self.db.execute_query(sql, {
            "cid": class_id,
            "name": name_clean,
            "code": code_clean,
            "total": float(total_marks),
            "passing": float(passing_marks)
        })
        row = self.db.fetch_one(
            "SELECT id FROM subjects WHERE class_id = :cid AND subject_name = :name",
            {"cid": class_id, "name": name_clean}
        )
        new_id = row["id"] if row else None
        return True, f"Subject '{name_clean}' added successfully.", new_id

    def remove_subject_from_class(self, subject_id: int) -> tuple[bool, str]:
        """Safely removes a subject and cascades deletion of associated exam marks and assignments."""
        subj = self.db.fetch_one("SELECT subject_name FROM subjects WHERE id = :id", {"id": subject_id})
        subj_name = subj["subject_name"] if subj else f"#{subject_id}"

        try:
            with self.db.transaction() as conn:
                from sqlalchemy import text
                # 1. Delete associated exam marks
                conn.execute(
                    text("""DELETE FROM exam_marks WHERE exam_subject_id IN (
                        SELECT id FROM exam_subjects WHERE subject_id = :sid
                    )"""),
                    {"sid": subject_id}
                )
                # 2. Delete exam_subjects
                conn.execute(
                    text("DELETE FROM exam_subjects WHERE subject_id = :sid"),
                    {"sid": subject_id}
                )
                # 3. Delete teacher subject assignments
                conn.execute(
                    text("DELETE FROM teacher_subject_assignments WHERE subject_id = :sid"),
                    {"sid": subject_id}
                )
                # 4. Delete subject
                conn.execute(
                    text("DELETE FROM subjects WHERE id = :sid"),
                    {"sid": subject_id}
                )
            return True, f"Subject '{subj_name}' removed successfully."
        except Exception as e:
            return False, f"Failed to remove subject: {str(e)}"

    def seed_default_subjects_for_class(self, class_id: int, class_name: str) -> int:
        """Seeds standard curriculum subjects tailored to the specific class grade."""
        from src.controllers.exam_controller import get_standard_curriculum_for_class
        curriculum = get_standard_curriculum_for_class(class_name)
        added_count = 0
        for item in curriculum:
            success, _, _ = self.add_subject_to_class(
                class_id, item["name"], item.get("code"),
                item.get("total_marks", 100.0), item.get("passing_marks", 40.0)
            )
            if success:
                added_count += 1
        return added_count

    def get_student_all_subjects_marks(self, exam_id: int, student_id: int) -> Dict[str, Any]:
        """
        Retrieves complete breakdown of marks for ALL subjects configured for a student's class,
        with individual subject statuses, grades, percentages, and overall aggregate performance.
        """
        student_query = """
            SELECT 
                s.id, s.admission_number, s.first_name, s.last_name, s.date_of_birth,
                c.id as class_id, c.name as class_name, sec.id as section_id, sec.name as section_name, se.roll_number,
                p.father_name, e.name as exam_name, ac.session_name
            FROM students s
            JOIN student_enrollments se ON s.id = se.student_id
            JOIN classes c ON se.class_id = c.id
            JOIN sections sec ON se.section_id = sec.id
            JOIN academic_sessions ac ON se.academic_session_id = ac.id
            JOIN exams e ON e.id = :eid
            JOIN parents_guardians p ON s.parent_id = p.id
            WHERE s.id = :sid AND ac.is_current = 1
        """
        student_info = self.db.fetch_one(student_query, {"eid": exam_id, "sid": student_id})
        if not student_info:
            return {}

        cid = student_info["class_id"]

        marks_query = """
            SELECT 
                sub.id as subject_id,
                sub.subject_name,
                sub.subject_code,
                COALESCE(es.max_marks, sub.total_marks, 100.0) as max_marks,
                COALESCE(es.passing_marks, sub.passing_marks, 40.0) as passing_marks,
                em.id as mark_id,
                em.marks_obtained,
                em.is_absent,
                em.grade,
                em.teacher_remarks
            FROM subjects sub
            LEFT JOIN exam_subjects es 
                ON sub.id = es.subject_id AND es.exam_id = :eid AND es.class_id = :cid
            LEFT JOIN exam_marks em 
                ON es.id = em.exam_subject_id AND em.student_id = :sid
            WHERE sub.class_id = :cid
            ORDER BY sub.subject_name ASC
        """
        marks_rows = self.db.fetch_all(marks_query, {"eid": exam_id, "sid": student_id, "cid": cid})

        from src.controllers.exam_controller import calculate_grade

        processed_marks = []
        total_max = 0.0
        total_obtained = 0.0
        passed_subjects = 0
        failed_subjects = 0
        absent_subjects = 0
        has_graded = False

        for r in marks_rows:
            max_m = float(r["max_marks"] or 100.0)
            pass_m = float(r["passing_marks"] or 40.0)
            is_abs = bool(r.get("is_absent"))
            raw_obtained = r.get("marks_obtained")

            total_max += max_m

            if is_abs:
                has_graded = True
                absent_subjects += 1
                subj_status = "Absent"
                obtained_str = "ABS"
                subj_pct = 0.0
                subj_grade = "ABS"
            elif raw_obtained is not None:
                has_graded = True
                m_val = float(raw_obtained)
                total_obtained += m_val
                subj_pct = round((m_val / max_m) * 100.0, 1) if max_m > 0 else 0.0
                subj_grade = r.get("grade") or calculate_grade(subj_pct)
                if m_val >= pass_m:
                    subj_status = "Passed"
                    passed_subjects += 1
                else:
                    subj_status = "Failed"
                    failed_subjects += 1
                obtained_str = f"{m_val:.1f}" if m_val % 1 != 0 else f"{int(m_val)}"
            else:
                subj_status = "Not Graded"
                obtained_str = "--"
                subj_pct = 0.0
                subj_grade = "--"

            processed_marks.append({
                "subject_id": r["subject_id"],
                "subject_name": r["subject_name"],
                "subject_code": r.get("subject_code") or "",
                "max_marks": max_m,
                "passing_marks": pass_m,
                "marks_obtained": r.get("marks_obtained"),
                "marks_obtained_str": obtained_str,
                "is_absent": is_abs,
                "percentage": subj_pct,
                "percentage_str": f"{subj_pct}%" if subj_status != "Not Graded" else "--",
                "grade": subj_grade,
                "status": subj_status,
                "teacher_remarks": r.get("teacher_remarks") or ""
            })

        overall_percentage = round((total_obtained / total_max) * 100.0, 1) if total_max > 0 and has_graded else 0.0
        overall_grade = calculate_grade(overall_percentage) if has_graded else "--"

        if not has_graded:
            overall_status = "Pending Evaluation"
        elif failed_subjects > 0 or absent_subjects > 0:
            overall_status = "FAILED"
        else:
            overall_status = "PASSED"

        return {
            "student": student_info,
            "marks": processed_marks,
            "total_max": total_max,
            "total_obtained": total_obtained,
            "percentage": overall_percentage,
            "grade": overall_grade,
            "overall_status": overall_status,
            "passed_count": passed_subjects,
            "failed_count": failed_subjects,
            "absent_count": absent_subjects,
            "subject_count": len(processed_marks)
        }

    def get_student_report_card(self, exam_id: int, student_id: int) -> Dict[str, Any]:
        """Gathers complete exam marks, totals, percentages, and GPA for official PDF report card."""
        return self.get_student_all_subjects_marks(exam_id, student_id)


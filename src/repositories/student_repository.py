"""
Student and Academic Enrollment Repository.
"""
from typing import Optional, List, Dict, Any, Tuple
from src.repositories.base_repository import BaseRepository

class StudentRepository(BaseRepository):
    def get_all_classes(self) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM classes ORDER BY numeric_order ASC")

    def get_sections_by_class(self, class_id: int) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM sections WHERE class_id = :cid ORDER BY name ASC", {"cid": class_id})

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        return self.db.fetch_one("SELECT * FROM academic_sessions WHERE is_current = 1")

    def generate_admission_number(self) -> str:
        """Generates unique admission number format: SMS-YYYY-XXXX."""
        row = self.db.fetch_one("SELECT COUNT(*) as total FROM students")
        next_num = (row["total"] if row else 0) + 1
        from datetime import datetime
        return f"SMS-{datetime.now().year}-{next_num:04d}"

    def register_student(
        self,
        student_data: Dict[str, Any],
        parent_data: Dict[str, Any],
        enrollment_data: Dict[str, Any]
    ) -> int:
        """Atomically registers parent, student, and creates initial session enrollment."""
        with self.db.transaction() as conn:
            from sqlalchemy import text

            # 1. Insert Parent
            p_sql = """
                INSERT INTO parents_guardians (
                    father_name, father_cnic_nid, father_occupation, father_phone,
                    father_email, mother_name, mother_phone, guardian_relation,
                    emergency_contact, residential_address
                ) VALUES (
                    :fn, :f_cnic, :f_occ, :f_phone, :f_email, :mn, :m_phone,
                    :g_rel, :em_contact, :addr
                )
            """
            conn.execute(text(p_sql), {
                "fn": parent_data["father_name"],
                "f_cnic": parent_data.get("father_cnic_nid"),
                "f_occ": parent_data.get("father_occupation"),
                "f_phone": parent_data["father_phone"],
                "f_email": parent_data.get("father_email"),
                "mn": parent_data.get("mother_name"),
                "m_phone": parent_data.get("mother_phone"),
                "g_rel": parent_data.get("guardian_relation", "Father"),
                "em_contact": parent_data["emergency_contact"],
                "addr": parent_data["residential_address"]
            })

            # Retrieve inserted parent id
            p_row = conn.execute(text("SELECT id FROM parents_guardians ORDER BY id DESC LIMIT 1")).mappings().first()
            parent_id = p_row["id"]

            # 2. Insert Student
            s_sql = """
                INSERT INTO students (
                    admission_number, registration_date, first_name, last_name,
                    gender, date_of_birth, blood_group, religion, parent_id,
                    photo_path, status
                ) VALUES (
                    :adm, :reg_date, :fn, :ln, :gen, :dob, :bg, :rel, :pid, :photo, 'Active'
                )
            """
            conn.execute(text(s_sql), {
                "adm": student_data["admission_number"],
                "reg_date": student_data["registration_date"],
                "fn": student_data["first_name"],
                "ln": student_data["last_name"],
                "gen": student_data["gender"],
                "dob": student_data["date_of_birth"],
                "bg": student_data.get("blood_group"),
                "rel": student_data.get("religion", "Islam"),
                "pid": parent_id,
                "photo": student_data.get("photo_path")
            })

            s_row = conn.execute(text("SELECT id FROM students WHERE admission_number = :adm"), {"adm": student_data["admission_number"]}).mappings().first()
            student_id = s_row["id"]

            # 3. Insert Enrollment
            e_sql = """
                INSERT INTO student_enrollments (
                    student_id, academic_session_id, class_id, section_id, roll_number, enrollment_status
                ) VALUES (
                    :sid, :asid, :cid, :sec_id, :roll, 'Enrolled'
                )
            """
            conn.execute(text(e_sql), {
                "sid": student_id,
                "asid": enrollment_data["academic_session_id"],
                "cid": enrollment_data["class_id"],
                "sec_id": enrollment_data["section_id"],
                "roll": enrollment_data["roll_number"]
            })

            return student_id

    def search_students(
        self,
        search_term: Optional[str] = None,
        class_id: Optional[int] = None,
        section_id: Optional[int] = None,
        status: Optional[str] = "Active"
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT 
                s.id, s.admission_number, s.first_name, s.last_name, s.gender, s.date_of_birth,
                s.status, p.father_name, p.father_phone, p.emergency_contact,
                c.name as class_name, c.numeric_order, sec.name as section_name,
                se.roll_number, se.academic_session_id, ac.session_name
            FROM students s
            JOIN parents_guardians p ON s.parent_id = p.id
            LEFT JOIN student_enrollments se ON s.id = se.student_id
            LEFT JOIN academic_sessions ac ON se.academic_session_id = ac.id AND ac.is_current = 1
            LEFT JOIN classes c ON se.class_id = c.id
            LEFT JOIN sections sec ON se.section_id = sec.id
            WHERE 1=1
        """
        params: Dict[str, Any] = {}

        if status and status != "All":
            query += " AND s.status = :status"
            params["status"] = status

        if class_id:
            query += " AND se.class_id = :class_id"
            params["class_id"] = class_id

        if section_id:
            query += " AND se.section_id = :section_id"
            params["section_id"] = section_id

        if search_term:
            query += """ AND (
                s.admission_number LIKE :term OR
                s.first_name LIKE :term OR
                s.last_name LIKE :term OR
                p.father_name LIKE :term OR
                p.father_phone LIKE :term
            )"""
            params["term"] = f"%{search_term}%"

        query += " ORDER BY c.numeric_order ASC, sec.name ASC, se.roll_number ASC"
        return self.db.fetch_all(query, params)

    def get_student_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT 
                s.*, p.father_name, p.father_cnic_nid, p.father_occupation, p.father_phone,
                p.father_email, p.mother_name, p.mother_phone, p.guardian_relation,
                p.emergency_contact, p.residential_address,
                c.name as class_name, c.id as class_id, c.numeric_order,
                sec.name as section_name, sec.id as section_id,
                se.roll_number, se.academic_session_id, ac.session_name
            FROM students s
            JOIN parents_guardians p ON s.parent_id = p.id
            LEFT JOIN student_enrollments se ON s.id = se.student_id
            LEFT JOIN academic_sessions ac ON se.academic_session_id = ac.id AND ac.is_current = 1
            LEFT JOIN classes c ON se.class_id = c.id
            LEFT JOIN sections sec ON se.section_id = sec.id
            WHERE s.id = :sid
        """
        return self.db.fetch_one(query, {"sid": student_id})

    def update_student(
        self,
        student_id: int,
        student_data: Dict[str, Any],
        parent_data: Dict[str, Any],
        enrollment_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        with self.db.transaction() as conn:
            from sqlalchemy import text
            s_row = conn.execute(text("SELECT parent_id FROM students WHERE id = :sid"), {"sid": student_id}).mappings().first()
            if not s_row:
                return False
            parent_id = s_row["parent_id"]

            # Update Parent
            p_sql = """
                UPDATE parents_guardians SET
                    father_name = :fn, father_phone = :f_phone, father_occupation = :f_occ,
                    father_cnic_nid = :f_cnic, father_email = :f_email, mother_name = :mn,
                    emergency_contact = :em, residential_address = :addr
                WHERE id = :pid
            """
            conn.execute(text(p_sql), {
                "pid": parent_id,
                "fn": parent_data["father_name"],
                "f_phone": parent_data["father_phone"],
                "f_occ": parent_data.get("father_occupation"),
                "f_cnic": parent_data.get("father_cnic_nid"),
                "f_email": parent_data.get("father_email"),
                "mn": parent_data.get("mother_name"),
                "em": parent_data.get("emergency_contact", parent_data["father_phone"]),
                "addr": parent_data.get("residential_address", "")
            })

            # Update Student
            s_sql = """
                UPDATE students SET
                    first_name = :fn, last_name = :ln, gender = :gen,
                    date_of_birth = :dob, blood_group = :bg, religion = :rel,
                    status = :st, updated_at = CURRENT_TIMESTAMP
                WHERE id = :sid
            """
            conn.execute(text(s_sql), {
                "sid": student_id,
                "fn": student_data["first_name"],
                "ln": student_data["last_name"],
                "gen": student_data["gender"],
                "dob": student_data["date_of_birth"],
                "bg": student_data.get("blood_group"),
                "rel": student_data.get("religion", "Islam"),
                "st": student_data.get("status", "Active")
            })

            # Update Enrollment (Class, Section, Roll Number) if provided
            if enrollment_data and enrollment_data.get("class_id") and enrollment_data.get("section_id"):
                e_sql = """
                    UPDATE student_enrollments SET
                        class_id = :cid,
                        section_id = :secid,
                        roll_number = :roll
                    WHERE student_id = :sid AND academic_session_id = :asid
                """
                conn.execute(text(e_sql), {
                    "sid": student_id,
                    "asid": enrollment_data.get("academic_session_id", 1),
                    "cid": enrollment_data["class_id"],
                    "secid": enrollment_data["section_id"],
                    "roll": enrollment_data.get("roll_number", 1)
                })

            return True

    def promote_students(
        self,
        student_ids: List[int],
        source_class_id: int,
        target_class_id: Optional[int],
        target_section_id: int,
        new_session_id: int,
        is_graduate: bool = False
    ) -> int:
        """Promotes selected students to the next class in a new academic session."""
        promoted_count = 0
        with self.db.transaction() as conn:
            from sqlalchemy import text
            for sid in student_ids:
                if is_graduate or target_class_id is None:
                    # Mark student graduated
                    conn.execute(
                        text("UPDATE students SET status = 'Graduated' WHERE id = :sid"),
                        {"sid": sid}
                    )
                    conn.execute(
                        text("UPDATE student_enrollments SET enrollment_status = 'Graduated' WHERE student_id = :sid"),
                        {"sid": sid}
                    )
                else:
                    # Update previous enrollment status
                    conn.execute(
                        text("UPDATE student_enrollments SET enrollment_status = 'Promoted' WHERE student_id = :sid"),
                        {"sid": sid}
                    )
                    # Next roll number in target class/section
                    max_roll = conn.execute(
                        text("""SELECT COALESCE(MAX(roll_number), 0) + 1 as next_roll 
                                FROM student_enrollments 
                                WHERE academic_session_id = :asid AND class_id = :cid AND section_id = :secid"""),
                        {"asid": new_session_id, "cid": target_class_id, "secid": target_section_id}
                    ).mappings().first()["next_roll"]

                    # Insert new enrollment
                    conn.execute(
                        text("""INSERT INTO student_enrollments (
                                    student_id, academic_session_id, class_id, section_id, roll_number, enrollment_status
                                ) VALUES (:sid, :asid, :cid, :secid, :roll, 'Enrolled')"""),
                        {
                            "sid": sid,
                            "asid": new_session_id,
                            "cid": target_class_id,
                            "secid": target_section_id,
                            "roll": max_roll
                        }
                    )
                promoted_count += 1
        return promoted_count

    def update_student_status(self, student_id: int, new_status: str, remarks: Optional[str] = None) -> bool:
        """Updates student lifecycle status (Active, Passed Out, Left, Transferred, Inactive)."""
        with self.db.transaction() as conn:
            from sqlalchemy import text
            conn.execute(
                text("UPDATE students SET status = :st, updated_at = CURRENT_TIMESTAMP WHERE id = :sid"),
                {"st": new_status, "sid": student_id}
            )
            conn.execute(
                text("UPDATE student_enrollments SET enrollment_status = :st WHERE student_id = :sid"),
                {"st": new_status, "sid": student_id}
            )
            # Log audit trail
            conn.execute(
                text("""INSERT INTO audit_logs (action, module, record_id, details)
                        VALUES ('STUDENT_STATUS_UPDATE', 'students', :rid, :det)"""),
                {"rid": str(student_id), "det": f"Status changed to '{new_status}'. Reason: {remarks or 'Administrative update'}"}
            )
            return True

    def delete_student_permanently(self, student_id: int) -> Tuple[bool, str]:
        """
        Permanently deletes a student and all cascading dependencies
        in a single atomic transaction.
        """
        try:
            with self.db.transaction() as conn:
                from sqlalchemy import text
                st = conn.execute(
                    text("SELECT first_name, last_name, admission_number FROM students WHERE id = :sid"),
                    {"sid": student_id}
                ).mappings().first()

                if not st:
                    return False, "Student not found."

                st_name = f"{st['first_name']} {st['last_name']} ({st['admission_number']})"

                # 1. Delete Exam Marks
                conn.execute(text("DELETE FROM exam_marks WHERE student_id = :sid"), {"sid": student_id})

                # 2. Delete Student Attendance
                conn.execute(text("DELETE FROM student_attendance WHERE student_id = :sid"), {"sid": student_id})

                # 3. Delete Fee Payments and Invoice Items, then Invoices
                conn.execute(
                    text("""DELETE FROM fee_payments WHERE invoice_id IN (
                                SELECT id FROM fee_invoices WHERE student_id = :sid
                            )"""),
                    {"sid": student_id}
                )
                conn.execute(
                    text("""DELETE FROM fee_invoice_items WHERE invoice_id IN (
                                SELECT id FROM fee_invoices WHERE student_id = :sid
                            )"""),
                    {"sid": student_id}
                )
                conn.execute(text("DELETE FROM fee_invoices WHERE student_id = :sid"), {"sid": student_id})

                # 4. Delete Fee Discounts
                conn.execute(text("DELETE FROM student_fee_discounts WHERE student_id = :sid"), {"sid": student_id})

                # 5. Delete Enrollments
                conn.execute(text("DELETE FROM student_enrollments WHERE student_id = :sid"), {"sid": student_id})

                # 6. Delete Student Record
                conn.execute(text("DELETE FROM students WHERE id = :sid"), {"sid": student_id})

                # 7. Add Audit Log
                conn.execute(
                    text("""INSERT INTO audit_logs (action, module, record_id, details)
                            VALUES ('PERMANENT_STUDENT_DELETE', 'students', :rid, :det)"""),
                    {"rid": str(student_id), "det": f"Permanently deleted student {st_name} and all related records."}
                )

            return True, f"Successfully and permanently deleted {st_name}."
        except Exception as e:
            return False, f"Failed to delete student: {str(e)}"


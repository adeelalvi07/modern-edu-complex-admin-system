"""
Attendance Repository for Students and Staff.
Supports fast batch-entry, percentage analytics, and chronic absentee detection.
"""
from typing import Optional, List, Dict, Any
from datetime import date
from src.repositories.base_repository import BaseRepository

class AttendanceRepository(BaseRepository):
    def get_class_roster_for_attendance(
        self,
        class_id: int,
        section_id: int,
        target_date: str,
        session_id: int
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all enrolled students in a class & section along with their
        recorded attendance status for the given date (defaulting to 'Present' if not yet marked).
        """
        query = """
            SELECT 
                s.id as student_id,
                s.admission_number,
                s.first_name,
                s.last_name,
                se.roll_number,
                COALESCE(sa.status, 'Present') as status,
                sa.remarks
            FROM student_enrollments se
            JOIN students s ON se.student_id = s.id
            LEFT JOIN student_attendance sa 
                ON s.id = sa.student_id 
                AND sa.attendance_date = :att_date
            WHERE se.class_id = :cid 
              AND se.section_id = :secid
              AND se.academic_session_id = :asid
              AND s.status = 'Active'
            ORDER BY se.roll_number ASC
        """
        return self.db.fetch_all(query, {
            "cid": class_id,
            "secid": section_id,
            "att_date": target_date,
            "asid": session_id
        })

    def save_batch_student_attendance(
        self,
        class_id: int,
        section_id: int,
        attendance_date: str,
        records: List[Dict[str, Any]],
        marked_by_user_id: Optional[int] = None
    ) -> int:
        """Batch saves or updates daily attendance in a single atomic transaction."""
        saved_count = 0
        with self.db.transaction() as conn:
            from sqlalchemy import text
            for rec in records:
                # Upsert pattern
                check_sql = """
                    SELECT id FROM student_attendance 
                    WHERE student_id = :sid AND attendance_date = :adate
                """
                existing = conn.execute(text(check_sql), {
                    "sid": rec["student_id"],
                    "adate": attendance_date
                }).mappings().first()

                if existing:
                    upd_sql = """
                        UPDATE student_attendance 
                        SET status = :st, remarks = :rem, marked_by = :uid
                        WHERE id = :id
                    """
                    conn.execute(text(upd_sql), {
                        "id": existing["id"],
                        "st": rec["status"],
                        "rem": rec.get("remarks"),
                        "uid": marked_by_user_id
                    })
                else:
                    ins_sql = """
                        INSERT INTO student_attendance (
                            student_id, class_id, section_id, attendance_date, status, remarks, marked_by
                        ) VALUES (:sid, :cid, :secid, :adate, :st, :rem, :uid)
                    """
                    conn.execute(text(ins_sql), {
                        "sid": rec["student_id"],
                        "cid": class_id,
                        "secid": section_id,
                        "adate": attendance_date,
                        "st": rec["status"],
                        "rem": rec.get("remarks"),
                        "uid": marked_by_user_id
                    })
                saved_count += 1
        return saved_count

    def get_student_attendance_summary(
        self,
        student_id: int,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Calculates attendance percentage and breakdown for an individual student."""
        query = """
            SELECT 
                COUNT(*) as total_days,
                SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_days,
                SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
                SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late_days,
                SUM(CASE WHEN status = 'Half Day' THEN 1 ELSE 0 END) as half_days,
                SUM(CASE WHEN status = 'Excused' THEN 1 ELSE 0 END) as excused_days
            FROM student_attendance
            WHERE student_id = :sid AND attendance_date BETWEEN :sdate AND :edate
        """
        row = self.db.fetch_one(query, {"sid": student_id, "sdate": start_date, "edate": end_date})
        total = (row["total_days"] if row else 0) or 0
        present = (row["present_days"] if row else 0) or 0
        late = (row["late_days"] if row else 0) or 0
        effective_present = present + (late * 0.5)
        percentage = round((effective_present / total) * 100, 1) if total > 0 else 0.0

        return {
            "total_days": total,
            "present_days": present,
            "absent_days": (row["absent_days"] if row else 0) or 0,
            "late_days": late,
            "excused_days": (row["excused_days"] if row else 0) or 0,
            "percentage": percentage
        }

    def get_chronic_absentees(
        self,
        start_date: str,
        end_date: str,
        threshold_percentage: float = 75.0,
        class_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Identifies students whose attendance falls below a minimum compliance threshold."""
        query = """
            SELECT 
                s.id as student_id,
                s.admission_number,
                s.first_name,
                s.last_name,
                c.name as class_name,
                sec.name as section_name,
                p.father_name,
                p.father_phone,
                COUNT(sa.id) as total_days,
                SUM(CASE WHEN sa.status = 'Present' THEN 1 ELSE 0 END) as present_days,
                SUM(CASE WHEN sa.status = 'Absent' THEN 1 ELSE 0 END) as absent_days
            FROM students s
            JOIN parents_guardians p ON s.parent_id = p.id
            JOIN student_enrollments se ON s.id = se.student_id
            JOIN classes c ON se.class_id = c.id
            JOIN sections sec ON se.section_id = sec.id
            LEFT JOIN student_attendance sa 
                ON s.id = sa.student_id 
                AND sa.attendance_date BETWEEN :sdate AND :edate
            WHERE s.status = 'Active'
        """
        params: Dict[str, Any] = {"sdate": start_date, "edate": end_date}
        if class_id:
            query += " AND se.class_id = :cid"
            params["cid"] = class_id

        query += """
            GROUP BY s.id, s.admission_number, s.first_name, s.last_name, 
                     c.name, sec.name, p.father_name, p.father_phone
            HAVING COUNT(sa.id) > 0
        """
        rows = self.db.fetch_all(query, params)
        chronic_list = []
        for r in rows:
            tot = r["total_days"]
            pres = r["present_days"] or 0
            pct = round((pres / tot) * 100, 1) if tot > 0 else 0.0
            if pct < threshold_percentage:
                r["percentage"] = pct
                chronic_list.append(r)
        return chronic_list

    def get_daily_school_attendance_summary(
        self,
        attendance_date: str,
        session_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves school-wide attendance summary breakdown for every class and section
        for ANY given date.
        """
        if not session_id:
            curr_session = self.db.fetch_one("SELECT id FROM academic_sessions WHERE is_current = 1")
            session_id = curr_session["id"] if curr_session else 1

        query = """
            SELECT 
                c.id as class_id,
                c.name as class_name,
                sec.id as section_id,
                sec.name as section_name,
                COUNT(DISTINCT s.id) as total_enrolled,
                COUNT(DISTINCT sa.id) as marked_count,
                SUM(CASE WHEN sa.status = 'Present' THEN 1 ELSE 0 END) as present_count,
                SUM(CASE WHEN sa.status = 'Absent' THEN 1 ELSE 0 END) as absent_count,
                SUM(CASE WHEN sa.status = 'Late' THEN 1 ELSE 0 END) as late_count,
                SUM(CASE WHEN sa.status = 'Excused' THEN 1 ELSE 0 END) as excused_count
            FROM classes c
            JOIN sections sec ON c.id = sec.class_id
            LEFT JOIN student_enrollments se 
                ON c.id = se.class_id 
                AND sec.id = se.section_id 
                AND se.academic_session_id = :sid
            LEFT JOIN students s 
                ON se.student_id = s.id 
                AND s.status = 'Active'
            LEFT JOIN student_attendance sa 
                ON s.id = sa.student_id 
                AND sa.attendance_date = :adate
            GROUP BY c.id, c.name, sec.id, sec.name
            ORDER BY c.id ASC, sec.name ASC
        """
        rows = self.db.fetch_all(query, {"sid": session_id, "adate": attendance_date})
        results = []
        for r in rows:
            enrolled = r["total_enrolled"] or 0
            marked = r["marked_count"] or 0
            pres = r["present_count"] or 0
            absent = r["absent_count"] or 0
            late = r["late_count"] or 0
            excused = r["excused_count"] or 0

            if enrolled == 0:
                pct = 0.0
                status_label = "No Students"
            elif marked == 0:
                pct = 0.0
                status_label = "⏳ Pending"
            elif marked >= enrolled:
                pct = round((pres / marked) * 100, 1) if marked > 0 else 0.0
                status_label = "✔ Completed"
            else:
                pct = round((pres / marked) * 100, 1) if marked > 0 else 0.0
                status_label = f"⚠️ Partial ({marked}/{enrolled})"

            results.append({
                "class_id": r["class_id"],
                "class_name": r["class_name"],
                "section_id": r["section_id"],
                "section_name": r["section_name"],
                "display_class": f"{r['class_name']} - {r['section_name']}",
                "total_enrolled": enrolled,
                "marked_count": marked,
                "present_count": pres,
                "absent_count": absent,
                "late_count": late,
                "excused_count": excused,
                "percentage": pct,
                "status": status_label
            })
        return results

    def get_school_attendance_metrics(
        self,
        attendance_date: str,
        session_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Returns aggregated school-wide attendance metrics for a specific date.
        """
        breakdown = self.get_daily_school_attendance_summary(attendance_date, session_id)
        total_enrolled = sum(r["total_enrolled"] for r in breakdown)
        total_marked = sum(r["marked_count"] for r in breakdown)
        total_present = sum(r["present_count"] for r in breakdown)
        total_absent = sum(r["absent_count"] for r in breakdown)
        total_late = sum(r["late_count"] for r in breakdown)
        classes_count = len(breakdown)
        classes_completed = sum(1 for r in breakdown if r["status"] == "✔ Completed")
        overall_pct = round((total_present / total_marked) * 100, 1) if total_marked > 0 else 0.0

        return {
            "attendance_date": attendance_date,
            "total_enrolled": total_enrolled,
            "total_marked": total_marked,
            "total_present": total_present,
            "total_absent": total_absent,
            "total_late": total_late,
            "overall_percentage": overall_pct,
            "classes_count": classes_count,
            "classes_completed": classes_completed,
            "is_fully_marked": (classes_completed == classes_count and classes_count > 0)
        }


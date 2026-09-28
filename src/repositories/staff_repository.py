"""
Staff, Faculty, Subject Assignments, and Payroll Repository.
"""
from typing import Optional, List, Dict, Any, Tuple
from src.repositories.base_repository import BaseRepository

class StaffRepository(BaseRepository):
    def get_all_departments(self) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM staff_departments ORDER BY id ASC")

    def generate_employee_code(self) -> str:
        row = self.db.fetch_one("SELECT COUNT(*) as total FROM staff")
        count = (row["total"] if row else 0) + 1
        return f"EMP-{count:04d}"

    def add_staff(self, data: Dict[str, Any]) -> int:
        sql = """
            INSERT INTO staff (
                employee_code, department_id, first_name, last_name, gender,
                cnic_nid, date_of_birth, qualification, designation, joining_date,
                contact_phone, email, address, basic_salary, bank_account_info, is_active
            ) VALUES (
                :emp_code, :dept_id, :fn, :ln, :gen,
                :cnic, :dob, :qual, :desig, :join_date,
                :phone, :email, :addr, :salary, :bank, 1
            )
        """
        self.db.execute_query(sql, data)
        row = self.db.fetch_one("SELECT id FROM staff WHERE employee_code = :emp_code", {"emp_code": data["emp_code"]})
        return row["id"] if row else 0

    def get_all_staff(
        self,
        department_id: Optional[int] = None,
        search_term: Optional[str] = None,
        status_filter: Optional[str] = "Active"
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT s.*, d.name as department_name
            FROM staff s
            JOIN staff_departments d ON s.department_id = d.id
            WHERE 1=1
        """
        params: Dict[str, Any] = {}
        if status_filter == "Active":
            query += " AND s.is_active = 1"
        elif status_filter in ("Inactive", "Relieved", "Resigned"):
            query += " AND s.is_active = 0"
        if department_id:
            query += " AND s.department_id = :dept_id"
            params["dept_id"] = department_id
        if search_term:
            query += """ AND (
                s.employee_code LIKE :term OR
                s.first_name LIKE :term OR
                s.last_name LIKE :term OR
                s.designation LIKE :term OR
                s.contact_phone LIKE :term
            )"""
            params["term"] = f"%{search_term}%"

        query += " ORDER BY s.id ASC"
        return self.db.fetch_all(query, params)

    def get_staff_by_id(self, staff_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT s.*, d.name as department_name
            FROM staff s
            JOIN staff_departments d ON s.department_id = d.id
            WHERE s.id = :sid
        """
        return self.db.fetch_one(query, {"sid": staff_id})

    def update_staff(self, staff_id: int, data: Dict[str, Any]) -> bool:
        sql = """
            UPDATE staff SET
                department_id = :dept_id,
                first_name = :fn,
                last_name = :ln,
                gender = :gen,
                cnic_nid = :cnic,
                date_of_birth = :dob,
                qualification = :qual,
                designation = :desig,
                contact_phone = :phone,
                email = :email,
                address = :addr,
                basic_salary = :salary,
                bank_account_info = :bank,
                is_active = :active
            WHERE id = :sid
        """
        params = {
            "sid": staff_id,
            "dept_id": data["department_id"],
            "fn": data["first_name"],
            "ln": data["last_name"],
            "gen": data["gender"],
            "cnic": data.get("cnic_nid"),
            "dob": data["date_of_birth"],
            "qual": data.get("qualification"),
            "desig": data["designation"],
            "phone": data["contact_phone"],
            "email": data.get("email"),
            "addr": data.get("address"),
            "salary": float(data.get("basic_salary", 0)),
            "bank": data.get("bank_account_info"),
            "active": 1 if data.get("is_active", True) else 0
        }
        rows = self.db.execute_query(sql, params)
        return rows > 0

    def get_subjects_by_class(self, class_id: int) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM subjects WHERE class_id = :cid ORDER BY subject_name ASC", {"cid": class_id})

    def add_subject(self, class_id: int, subject_name: str, subject_code: str, total_marks: float, passing_marks: float) -> int:
        sql = """
            INSERT INTO subjects (class_id, subject_name, subject_code, total_marks, passing_marks)
            VALUES (:cid, :sname, :code, :total, :passing)
        """
        self.db.execute_query(sql, {
            "cid": class_id,
            "sname": subject_name,
            "code": subject_code,
            "total": total_marks,
            "passing": passing_marks
        })
        row = self.db.fetch_one("SELECT id FROM subjects WHERE class_id = :cid AND subject_name = :sname", {"cid": class_id, "sname": subject_name})
        return row["id"] if row else 0

    def generate_monthly_payroll(self, month: int, year: int) -> int:
        """Generates pending payroll records for all active staff for the given month/year."""
        active_staff = self.get_all_staff()
        count = 0
        for s in active_staff:
            exists = self.db.fetch_one(
                "SELECT id FROM staff_payroll WHERE staff_id = :sid AND payroll_month = :m AND payroll_year = :y",
                {"sid": s["id"], "m": month, "y": year}
            )
            if not exists:
                basic = float(s["basic_salary"])
                self.db.execute_query(
                    """INSERT INTO staff_payroll (
                        staff_id, payroll_month, payroll_year, basic_salary, allowances, deductions, net_salary, payment_status
                    ) VALUES (:sid, :m, :y, :basic, 0, 0, :basic, 'Pending')""",
                    {"sid": s["id"], "m": month, "y": year, "basic": basic}
                )
                count += 1
        return count

    def get_payroll_records(self, month: int, year: int) -> List[Dict[str, Any]]:
        query = """
            SELECT sp.*, s.employee_code, s.first_name, s.last_name, s.designation, d.name as department_name
            FROM staff_payroll sp
            JOIN staff s ON sp.staff_id = s.id
            JOIN staff_departments d ON s.department_id = d.id
            WHERE sp.payroll_month = :m AND sp.payroll_year = :y
            ORDER BY s.employee_code ASC
        """
        return self.db.fetch_all(query, {"m": month, "y": year})

    def mark_payroll_paid(self, payroll_id: int, payment_method: str, transaction_ref: str) -> bool:
        from datetime import date
        sql = """
            UPDATE staff_payroll SET
                payment_status = 'Paid',
                payment_date = :pdate,
                payment_method = :pmethod,
                transaction_ref = :ref
            WHERE id = :pid
        """
        rows = self.db.execute_query(sql, {
            "pid": payroll_id,
            "pdate": date.today().isoformat(),
            "pmethod": payment_method,
            "ref": transaction_ref
        })
        return rows > 0

    def update_staff_status(
        self,
        staff_id: int,
        is_active: bool,
        status_label: str = "Resigned",
        remarks: Optional[str] = None
    ) -> bool:
        """Updates staff active/inactive status and logs audit trail."""
        sql = "UPDATE staff SET is_active = :act WHERE id = :sid"
        self.db.execute_query(sql, {"act": 1 if is_active else 0, "sid": staff_id})

        # Log audit trail
        audit_sql = """
            INSERT INTO audit_logs (action, module, record_id, details)
            VALUES ('STAFF_STATUS_UPDATE', 'staff', :rid, :det)
        """
        st_text = "Active" if is_active else status_label
        self.db.execute_query(audit_sql, {
            "rid": str(staff_id),
            "det": f"Staff status updated to '{st_text}'. Remarks: {remarks or 'Administrative action'}"
        })
        return True

    def delete_staff_permanently(self, staff_id: int) -> Tuple[bool, str]:
        """
        Permanently deletes a staff member and all associated dependencies
        in a single atomic transaction.
        """
        try:
            with self.db.transaction() as conn:
                from sqlalchemy import text
                st = conn.execute(
                    text("SELECT first_name, last_name, employee_code, user_id FROM staff WHERE id = :sid"),
                    {"sid": staff_id}
                ).mappings().first()

                if not st:
                    return False, "Staff member not found."

                staff_name = f"{st['first_name']} {st['last_name']} ({st['employee_code']})"

                # 1. Delete Teacher Subject Assignments
                conn.execute(text("DELETE FROM teacher_subject_assignments WHERE staff_id = :sid"), {"sid": staff_id})

                # 2. Delete Staff Attendance
                conn.execute(text("DELETE FROM staff_attendance WHERE staff_id = :sid"), {"sid": staff_id})

                # 3. Delete Staff Payroll records
                conn.execute(text("DELETE FROM staff_payroll WHERE staff_id = :sid"), {"sid": staff_id})

                # 4. Unlink linked user if any
                if st.get("user_id"):
                    conn.execute(
                        text("UPDATE staff SET user_id = NULL WHERE id = :sid"),
                        {"sid": staff_id}
                    )

                # 5. Delete Staff record
                conn.execute(text("DELETE FROM staff WHERE id = :sid"), {"sid": staff_id})

                # 6. Audit log
                conn.execute(
                    text("""INSERT INTO audit_logs (action, module, record_id, details)
                            VALUES ('PERMANENT_STAFF_DELETE', 'staff', :rid, :det)"""),
                    {"rid": str(staff_id), "det": f"Permanently deleted staff member {staff_name} and related records."}
                )

            return True, f"Successfully and permanently deleted {staff_name}."
        except Exception as e:
            return False, f"Failed to delete staff member: {str(e)}"


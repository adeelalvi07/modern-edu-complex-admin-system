"""
Fee, Billing, Payments, and Defaulter Tracking Repository.
"""
from typing import Optional, List, Dict, Any
from datetime import date
from src.repositories.base_repository import BaseRepository

class FeeRepository(BaseRepository):
    def get_all_fee_heads(self) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM fee_heads WHERE is_active = 1 ORDER BY id ASC")

    def get_fee_structure(self, class_id: int, session_id: int) -> List[Dict[str, Any]]:
        query = """
            SELECT fs.*, fh.name as fee_head_name
            FROM fee_structures fs
            JOIN fee_heads fh ON fs.fee_head_id = fh.id
            WHERE fs.class_id = :cid AND fs.academic_session_id = :asid
            ORDER BY fs.id ASC
        """
        return self.db.fetch_all(query, {"cid": class_id, "asid": session_id})

    def set_fee_structure(self, session_id: int, class_id: int, fee_head_id: int, amount: float, frequency: str = "Monthly"):
        sql = """
            INSERT INTO fee_structures (academic_session_id, class_id, fee_head_id, amount, frequency)
            VALUES (:asid, :cid, :fhid, :amt, :freq)
            ON CONFLICT (academic_session_id, class_id, fee_head_id)
            DO UPDATE SET amount = :amt, frequency = :freq
        """
        # For SQLite compatibility with ON CONFLICT or separate check
        existing = self.db.fetch_one(
            """SELECT id FROM fee_structures 
               WHERE academic_session_id = :asid AND class_id = :cid AND fee_head_id = :fhid""",
            {"asid": session_id, "cid": class_id, "fhid": fee_head_id}
        )
        if existing:
            self.db.execute_query(
                "UPDATE fee_structures SET amount = :amt, frequency = :freq WHERE id = :id",
                {"id": existing["id"], "amt": amount, "freq": frequency}
            )
        else:
            self.db.execute_query(
                """INSERT INTO fee_structures (academic_session_id, class_id, fee_head_id, amount, frequency)
                   VALUES (:asid, :cid, :fhid, :amt, :freq)""",
                {"asid": session_id, "cid": class_id, "fhid": fee_head_id, "amt": amount, "freq": frequency}
            )

    def generate_monthly_vouchers(
        self,
        class_id: int,
        session_id: int,
        month: int,
        year: int,
        due_date_str: str
    ) -> int:
        """Generates fee vouchers for all enrolled students in a class for a specific month."""
        structures = self.get_fee_structure(class_id, session_id)
        if not structures:
            return 0

        # Get all enrolled students in class
        students = self.db.fetch_all(
            """SELECT se.student_id, se.section_id 
               FROM student_enrollments se
               JOIN students s ON se.student_id = s.id
               WHERE se.class_id = :cid AND se.academic_session_id = :asid AND s.status = 'Active'""",
            {"cid": class_id, "asid": session_id}
        )

        vouchers_created = 0
        with self.db.transaction() as conn:
            from sqlalchemy import text
            for st in students:
                sid = st["student_id"]
                sec_id = st["section_id"]

                # Check if voucher already exists for this cycle
                chk = conn.execute(
                    text("""SELECT id FROM fee_invoices 
                            WHERE student_id = :sid AND academic_session_id = :asid 
                              AND billing_month = :m AND billing_year = :y"""),
                    {"sid": sid, "asid": session_id, "m": month, "y": year}
                ).mappings().first()

                if chk:
                    continue

                # Calculate gross
                gross = sum(float(item["amount"]) for item in structures)
                inv_number = f"INV-{year}{month:02d}-{sid:04d}"

                # Insert invoice
                ins_inv = """
                    INSERT INTO fee_invoices (
                        invoice_number, student_id, academic_session_id, class_id, section_id,
                        billing_month, billing_year, issue_date, due_date, gross_amount,
                        discount_amount, fine_amount, net_payable, paid_amount, balance_amount, status
                    ) VALUES (
                        :inv, :sid, :asid, :cid, :secid,
                        :m, :y, :issue, :due, :gross,
                        0.00, 0.00, :gross, 0.00, :gross, 'Unpaid'
                    )
                """
                conn.execute(text(ins_inv), {
                    "inv": inv_number,
                    "sid": sid,
                    "asid": session_id,
                    "cid": class_id,
                    "secid": sec_id,
                    "m": month,
                    "y": year,
                    "issue": date.today().isoformat(),
                    "due": due_date_str,
                    "gross": gross
                })

                inv_id_row = conn.execute(
                    text("SELECT id FROM fee_invoices WHERE invoice_number = :inv"),
                    {"inv": inv_number}
                ).mappings().first()
                inv_id = inv_id_row["id"]

                # Insert line items
                for fs in structures:
                    conn.execute(
                        text("""INSERT INTO fee_invoice_items (invoice_id, fee_head_id, amount) 
                                VALUES (:invid, :fhid, :amt)"""),
                        {"invid": inv_id, "fhid": fs["fee_head_id"], "amt": fs["amount"]}
                    )

                vouchers_created += 1

        return vouchers_created

    def search_invoices(
        self,
        class_id: Optional[int] = None,
        section_id: Optional[int] = None,
        month: Optional[int] = None,
        year: Optional[int] = None,
        status: Optional[str] = None,
        search_term: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT 
                fi.*, s.admission_number, s.first_name, s.last_name,
                c.name as class_name, sec.name as section_name,
                p.father_name, p.father_phone
            FROM fee_invoices fi
            JOIN students s ON fi.student_id = s.id
            JOIN parents_guardians p ON s.parent_id = p.id
            JOIN classes c ON fi.class_id = c.id
            JOIN sections sec ON fi.section_id = sec.id
            WHERE 1=1
        """
        params: Dict[str, Any] = {}
        if class_id:
            query += " AND fi.class_id = :cid"
            params["cid"] = class_id
        if section_id:
            query += " AND fi.section_id = :secid"
            params["secid"] = section_id
        if month:
            query += " AND fi.billing_month = :m"
            params["m"] = month
        if year:
            query += " AND fi.billing_year = :y"
            params["y"] = year
        if status and status != "All":
            query += " AND fi.status = :status"
            params["status"] = status
        if search_term:
            query += """ AND (
                fi.invoice_number LIKE :term OR
                s.admission_number LIKE :term OR
                s.first_name LIKE :term OR
                p.father_name LIKE :term
            )"""
            params["term"] = f"%{search_term}%"

        query += " ORDER BY fi.id DESC"
        return self.db.fetch_all(query, params)

    def process_payment(
        self,
        invoice_id: int,
        amount_paid: float,
        payment_mode: str = "Cash",
        reference_number: Optional[str] = None,
        received_by_user_id: Optional[int] = None,
        remarks: Optional[str] = None,
        payment_date: Optional[str] = None
    ) -> Optional[str]:
        """Processes a payment, generates receipt, and updates invoice balance atomically."""
        actual_payment_date = payment_date.strip() if (payment_date and payment_date.strip()) else date.today().isoformat()
        with self.db.transaction() as conn:
            from sqlalchemy import text
            inv = conn.execute(
                text("SELECT * FROM fee_invoices WHERE id = :id"),
                {"id": invoice_id}
            ).mappings().first()

            if not inv:
                return None

            cur_paid = float(inv["paid_amount"])
            net_payable = float(inv["net_payable"])
            new_paid = cur_paid + amount_paid
            new_balance = max(0.0, net_payable - new_paid)

            new_status = "Paid" if new_balance <= 0.00 else "Partially Paid"
            receipt_num = f"REC-{date.today().year}-{invoice_id:04d}"

            # 1. Insert Payment
            conn.execute(
                text("""INSERT INTO fee_payments (
                            invoice_id, receipt_number, payment_date, amount_paid,
                            payment_mode, reference_number, received_by, remarks
                        ) VALUES (
                            :invid, :rec, :pdate, :amt, :mode, :ref, :uid, :rem
                        )"""),
                {
                    "invid": invoice_id,
                    "rec": receipt_num,
                    "pdate": actual_payment_date,
                    "amt": amount_paid,
                    "mode": payment_mode,
                    "ref": reference_number,
                    "uid": received_by_user_id,
                    "rem": remarks
                }
            )

            # 2. Update Invoice
            conn.execute(
                text("""UPDATE fee_invoices SET
                            paid_amount = :paid,
                            balance_amount = :bal,
                            status = :st
                        WHERE id = :id"""),
                {
                    "paid": new_paid,
                    "bal": new_balance,
                    "st": new_status,
                    "id": invoice_id
                }
            )

            return receipt_num

    def get_defaulters(self, class_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Returns all students with outstanding balances past their due dates."""
        query = """
            SELECT 
                fi.id as invoice_id,
                fi.invoice_number,
                fi.billing_month,
                fi.billing_year,
                fi.net_payable,
                fi.paid_amount,
                fi.balance_amount,
                fi.due_date,
                s.admission_number,
                s.first_name,
                s.last_name,
                c.name as class_name,
                sec.name as section_name,
                p.father_name,
                p.father_phone
            FROM fee_invoices fi
            JOIN students s ON fi.student_id = s.id
            JOIN parents_guardians p ON s.parent_id = p.id
            JOIN classes c ON fi.class_id = c.id
            JOIN sections sec ON fi.section_id = sec.id
            WHERE fi.status IN ('Unpaid', 'Partially Paid')
        """
        params: Dict[str, Any] = {}
        if class_id:
            query += " AND fi.class_id = :cid"
            params["cid"] = class_id

        query += " ORDER BY c.numeric_order ASC, fi.due_date ASC"
        return self.db.fetch_all(query, params)

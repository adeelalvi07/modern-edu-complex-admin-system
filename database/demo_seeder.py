"""
Demo Data Seeder for School Management System.
Populates realistic students across 13 classes, teachers, attendance, and fee invoices.
"""
import random
from datetime import date, timedelta
from database.connection import db_manager
from config import settings

def seed_demo_environment():
    """Seeds realistic demo students and faculty if database is clean."""
    existing = db_manager.fetch_one("SELECT COUNT(*) as cnt FROM students")
    if existing and existing["cnt"] > 10:
        return # Already seeded

    print("Seeding demo students and faculty for 13 classes...")

    first_names = ["Muhammad", "Ali", "Fatima", "Ayesha", "Zain", "Hamza", "Bilal", "Sara", "Hassan", "Usman", "Khadija", "Omer", "Zahra", "Ibrahim", "Maryam", "Ahmed", "Noor", "Mustafa", "Dua", "Rayyan"]
    last_names = ["Khan", "Ahmed", "Malik", "Chaudhry", "Bhatti", "Qureshi", "Siddiqui", "Rehman", "Shah", "Mirza", "Raza", "Tariq", "Iqbal", "Farooq", "Gul"]

    # 1. Seed Faculty with unique CNIC & phone numbers
    depts = db_manager.fetch_all("SELECT id, name FROM staff_departments")
    teaching_dept = next((d["id"] for d in depts if "Teach" in d["name"]), 1)
    
    sample_staff = [
        ("EMP-1001", "Tariq", "Mahmood", "M.Sc Mathematics", "Senior Math Teacher", 55000),
        ("EMP-1002", "Amina", "Sheikh", "M.A English", "English Lecturer", 50000),
        ("EMP-1003", "Rashid", "Minhas", "M.Sc Physics", "Science Teacher", 52000),
        ("EMP-1004", "Farhana", "Naz", "B.Ed, M.A Urdu", "Primary Wing Incharge", 48000),
        ("EMP-1005", "Zubair", "Khalid", "M.Com / ACCA", "Senior Accountant", 45000)
    ]
    for i, (code, fn, ln, qual, desig, sal) in enumerate(sample_staff, start=1):
        if not db_manager.fetch_one("SELECT id FROM staff WHERE employee_code = :c", {"c": code}):
            db_manager.execute_query(
                """INSERT INTO staff (
                    employee_code, department_id, first_name, last_name, gender,
                    cnic_nid, date_of_birth, qualification, designation, joining_date,
                    contact_phone, basic_salary, is_active
                ) VALUES (
                    :code, :dept, :fn, :ln, 'Male',
                    :cnic, '1988-04-12', :qual, :desig, '2022-08-15',
                    :phone, :sal, 1
                )""",
                {
                    "code": code,
                    "dept": teaching_dept,
                    "fn": fn,
                    "ln": ln,
                    "cnic": f"35201-123456{i}-{i}",
                    "qual": qual,
                    "desig": desig,
                    "sal": sal,
                    "phone": f"0300-987654{i}"
                }
            )

    # 2. Seed Students in Each Class (Nursery, Prep, PG, Class 1-10)
    classes = db_manager.fetch_all("SELECT id, name FROM classes ORDER BY numeric_order ASC")
    session = db_manager.fetch_one("SELECT id FROM academic_sessions WHERE is_current = 1")
    session_id = session["id"] if session else 1

    reg_year = date.today().year

    for c in classes:
        c_id = c["id"]
        sections = db_manager.fetch_all("SELECT id FROM sections WHERE class_id = :cid", {"cid": c_id})
        sec_id = sections[0]["id"] if sections else 1

        # Configure default tuition fee
        existing_fs = db_manager.fetch_one(
            "SELECT id FROM fee_structures WHERE academic_session_id = :asid AND class_id = :cid AND fee_head_id = 1",
            {"asid": session_id, "cid": c_id}
        )
        if not existing_fs:
            db_manager.execute_query(
                """INSERT INTO fee_structures (academic_session_id, class_id, fee_head_id, amount, frequency)
                   VALUES (:asid, :cid, 1, 3500.0, 'Monthly')""",
                {"asid": session_id, "cid": c_id}
            )

        # Seed 4 students per class
        for s_idx in range(1, 5):
            fn = random.choice(first_names)
            ln = random.choice(last_names)
            father = f"{random.choice(first_names)} {ln}"
            phone = f"03{random.randint(10,49)}-{random.randint(1000000, 9999999)}"
            adm_no = f"SMS-{reg_year}-{c_id:02d}{s_idx:02d}"

            if db_manager.fetch_one("SELECT id FROM students WHERE admission_number = :adm", {"adm": adm_no}):
                continue

            # Insert Parent
            db_manager.execute_query(
                """INSERT INTO parents_guardians (
                    father_name, father_phone, emergency_contact, residential_address
                ) VALUES (:fn, :phone, :phone, 'Civil Lines, Education Zone')""",
                {"fn": father, "phone": phone}
            )
            parent = db_manager.fetch_one("SELECT id FROM parents_guardians ORDER BY id DESC LIMIT 1")
            parent_id = parent["id"]

            # Insert Student
            db_manager.execute_query(
                """INSERT INTO students (
                    admission_number, registration_date, first_name, last_name,
                    gender, date_of_birth, parent_id, status
                ) VALUES (
                    :adm, '2026-04-01', :fn, :ln, 'Male', '2015-06-15', :pid, 'Active'
                )""",
                {"adm": adm_no, "fn": fn, "ln": ln, "pid": parent_id}
            )
            st_row = db_manager.fetch_one("SELECT id FROM students WHERE admission_number = :adm", {"adm": adm_no})
            st_id = st_row["id"]

            # Insert Enrollment
            db_manager.execute_query(
                """INSERT INTO student_enrollments (
                    student_id, academic_session_id, class_id, section_id, roll_number, enrollment_status
                ) VALUES (:sid, :asid, :cid, :secid, :roll, 'Enrolled')""",
                {"sid": st_id, "asid": session_id, "cid": c_id, "secid": sec_id, "roll": s_idx}
            )

            # Insert sample attendance for today
            db_manager.execute_query(
                """INSERT INTO student_attendance (
                    student_id, class_id, section_id, attendance_date, status
                ) VALUES (:sid, :cid, :secid, :dt, 'Present')""",
                {"sid": st_id, "cid": c_id, "secid": sec_id, "dt": date.today().isoformat()}
            )

            # Insert sample monthly fee invoice
            inv_no = f"INV-{reg_year}{date.today().month:02d}-{st_id:04d}"
            db_manager.execute_query(
                """INSERT INTO fee_invoices (
                    invoice_number, student_id, academic_session_id, class_id, section_id,
                    billing_month, billing_year, issue_date, due_date, gross_amount,
                    discount_amount, fine_amount, net_payable, paid_amount, balance_amount, status
                ) VALUES (
                    :inv, :sid, :asid, :cid, :secid,
                    :m, :y, :issue, :due, 3500.0,
                    0, 0, 3500.0, 0, 3500.0, 'Unpaid'
                )""",
                {
                    "inv": inv_no, "sid": st_id, "asid": session_id, "cid": c_id, "secid": sec_id,
                    "m": date.today().month, "y": reg_year, "issue": date.today().isoformat(),
                    "due": f"{reg_year}-{date.today().month:02d}-15"
                }
            )

    print("Demo dataset seeded successfully!")

"""
Database Connection and Lifecycle Manager.
Supports PostgreSQL (LAN Multi-PC), MySQL, and SQLite (Offline Fallback).
Engineered with connection pooling and thread safety.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
import bcrypt

from config import settings

logger = logging.getLogger("sms.database")


class DatabaseManager:
    """Singleton Database Manager handling connections, transactions, and initialization."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.engine: Optional[Engine] = None
        self.active_db_type = settings.DB_TYPE
        self._setup_engine()
        self._initialized = True

    def _setup_engine(self):
        """Initializes the SQLAlchemy engine based on configuration."""
        try:
            if settings.DB_TYPE == "postgresql":
                if settings.DATABASE_URL:
                    url = settings.DATABASE_URL
                    if url.startswith("postgres://"):
                        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
                    elif url.startswith("postgresql://") and "+psycopg2" not in url:
                        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
                else:
                    url = (
                        f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
                        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
                    )
                self.engine = create_engine(
                    url,
                    poolclass=QueuePool,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                    pool_timeout=15
                )
                # Test connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info(f"Connected to PostgreSQL database successfully.")
                self.active_db_type = "postgresql"

            elif settings.DB_TYPE == "mysql":
                url = (
                    f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
                    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
                )
                self.engine = create_engine(
                    url,
                    poolclass=QueuePool,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True
                )
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info(f"Connected to MySQL at {settings.DB_HOST}:{settings.DB_PORT}")
                self.active_db_type = "mysql"

            else:
                self._setup_sqlite()

        except Exception as e:
            logger.warning(f"Could not connect to {settings.DB_TYPE} ({e}). Falling back to local SQLite database.")
            self._setup_sqlite()

    def _setup_sqlite(self):
        """Initializes SQLite engine for standalone offline operation."""
        sqlite_path = settings.SQLITE_DB_PATH
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite:///{sqlite_path.as_posix()}"
        self.engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        # Enable foreign keys for SQLite
        with self.engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys = ON;"))
        logger.info(f"Connected to SQLite database at {sqlite_path}")
        self.active_db_type = "sqlite"

    @contextmanager
    def transaction(self):
        """Context manager for atomic transaction handling."""
        connection = self.engine.connect()
        trans = connection.begin()
        try:
            yield connection
            trans.commit()
        except Exception as e:
            trans.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise e
        finally:
            connection.close()

    def execute_query(self, query_str: str, params: Optional[Dict[str, Any]] = None) -> int:
        """Executes INSERT, UPDATE, DELETE query. Returns affected row count."""
        with self.transaction() as conn:
            result = conn.execute(text(query_str), params or {})
            return result.rowcount

    def fetch_one(self, query_str: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Fetches a single record as a dictionary."""
        with self.engine.connect() as conn:
            result = conn.execute(text(query_str), params or {})
            row = result.mappings().first()
            return dict(row) if row else None

    def fetch_all(self, query_str: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetches all records matching query as list of dictionaries."""
        with self.engine.connect() as conn:
            result = conn.execute(text(query_str), params or {})
            return [dict(row) for row in result.mappings().all()]

    def init_database(self):
        """Creates all required tables if they don't exist and seeds initial data."""
        # DDL definitions compatible with both PostgreSQL and SQLite
        is_sqlite = (self.active_db_type == "sqlite")
        pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"
        big_pk_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "BIGSERIAL PRIMARY KEY"

        ddl_statements = [
            f"""CREATE TABLE IF NOT EXISTS roles (
                id {pk_type},
                name VARCHAR(50) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",

            f"""CREATE TABLE IF NOT EXISTS users (
                id {pk_type},
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE,
                phone VARCHAR(20),
                role_id INT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
                is_active BOOLEAN DEFAULT 1,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",

            f"""CREATE TABLE IF NOT EXISTS audit_logs (
                id {big_pk_type},
                user_id INT REFERENCES users(id) ON DELETE SET NULL,
                action VARCHAR(100) NOT NULL,
                module VARCHAR(50) NOT NULL,
                record_id VARCHAR(50),
                details TEXT,
                ip_address VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",

            f"""CREATE TABLE IF NOT EXISTS academic_sessions (
                id {pk_type},
                session_name VARCHAR(50) UNIQUE NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_current BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",

            f"""CREATE TABLE IF NOT EXISTS classes (
                id {pk_type},
                name VARCHAR(50) UNIQUE NOT NULL,
                numeric_order INT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",

            f"""CREATE TABLE IF NOT EXISTS sections (
                id {pk_type},
                class_id INT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                name VARCHAR(20) NOT NULL,
                room_number VARCHAR(20),
                capacity INT DEFAULT 40,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (class_id, name)
            );""",

            f"""CREATE TABLE IF NOT EXISTS parents_guardians (
                id {pk_type},
                father_name VARCHAR(100) NOT NULL,
                father_cnic_nid VARCHAR(30),
                father_occupation VARCHAR(100),
                father_phone VARCHAR(25) NOT NULL,
                father_email VARCHAR(100),
                mother_name VARCHAR(100),
                mother_occupation VARCHAR(100),
                mother_phone VARCHAR(25),
                guardian_relation VARCHAR(50) DEFAULT 'Father',
                emergency_contact VARCHAR(25) NOT NULL,
                residential_address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",

            f"""CREATE TABLE IF NOT EXISTS students (
                id {pk_type},
                admission_number VARCHAR(30) UNIQUE NOT NULL,
                registration_date DATE NOT NULL,
                first_name VARCHAR(60) NOT NULL,
                last_name VARCHAR(60) NOT NULL,
                gender VARCHAR(10) NOT NULL,
                date_of_birth DATE NOT NULL,
                blood_group VARCHAR(5),
                religion VARCHAR(40) DEFAULT 'Islam',
                parent_id INT NOT NULL REFERENCES parents_guardians(id) ON DELETE RESTRICT,
                photo_path VARCHAR(255),
                status VARCHAR(20) DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",

            f"""CREATE TABLE IF NOT EXISTS student_enrollments (
                id {big_pk_type},
                student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                academic_session_id INT NOT NULL REFERENCES academic_sessions(id) ON DELETE RESTRICT,
                class_id INT NOT NULL REFERENCES classes(id) ON DELETE RESTRICT,
                section_id INT NOT NULL REFERENCES sections(id) ON DELETE RESTRICT,
                roll_number INT NOT NULL,
                enrollment_status VARCHAR(20) DEFAULT 'Enrolled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (student_id, academic_session_id),
                UNIQUE (academic_session_id, class_id, section_id, roll_number)
            );""",

            f"""CREATE TABLE IF NOT EXISTS staff_departments (
                id {pk_type},
                name VARCHAR(50) UNIQUE NOT NULL
            );""",

            f"""CREATE TABLE IF NOT EXISTS staff (
                id {pk_type},
                employee_code VARCHAR(30) UNIQUE NOT NULL,
                user_id INT UNIQUE REFERENCES users(id) ON DELETE SET NULL,
                department_id INT NOT NULL REFERENCES staff_departments(id) ON DELETE RESTRICT,
                first_name VARCHAR(60) NOT NULL,
                last_name VARCHAR(60) NOT NULL,
                gender VARCHAR(10) NOT NULL,
                cnic_nid VARCHAR(30) UNIQUE,
                date_of_birth DATE NOT NULL,
                qualification VARCHAR(150),
                designation VARCHAR(80) NOT NULL,
                joining_date DATE NOT NULL,
                contact_phone VARCHAR(25) NOT NULL,
                email VARCHAR(100),
                address TEXT,
                basic_salary NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
                bank_account_info TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",

            f"""CREATE TABLE IF NOT EXISTS subjects (
                id {pk_type},
                class_id INT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                subject_name VARCHAR(100) NOT NULL,
                subject_code VARCHAR(20),
                total_marks NUMERIC(5, 2) DEFAULT 100.00,
                passing_marks NUMERIC(5, 2) DEFAULT 40.00,
                UNIQUE (class_id, subject_name)
            );""",

            f"""CREATE TABLE IF NOT EXISTS teacher_subject_assignments (
                id {pk_type},
                staff_id INT NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
                academic_session_id INT NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
                class_id INT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                section_id INT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
                subject_id INT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (academic_session_id, section_id, subject_id)
            );""",

            f"""CREATE TABLE IF NOT EXISTS staff_payroll (
                id {big_pk_type},
                staff_id INT NOT NULL REFERENCES staff(id) ON DELETE RESTRICT,
                payroll_month INT NOT NULL,
                payroll_year INT NOT NULL,
                basic_salary NUMERIC(12, 2) NOT NULL,
                allowances NUMERIC(12, 2) DEFAULT 0.00,
                deductions NUMERIC(12, 2) DEFAULT 0.00,
                net_salary NUMERIC(12, 2) NOT NULL,
                payment_date DATE,
                payment_status VARCHAR(20) DEFAULT 'Pending',
                payment_method VARCHAR(30) DEFAULT 'Cash',
                transaction_ref VARCHAR(100),
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (staff_id, payroll_month, payroll_year)
            );""",

            f"""CREATE TABLE IF NOT EXISTS student_attendance (
                id {big_pk_type},
                student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                class_id INT NOT NULL REFERENCES classes(id) ON DELETE RESTRICT,
                section_id INT NOT NULL REFERENCES sections(id) ON DELETE RESTRICT,
                attendance_date DATE NOT NULL,
                status VARCHAR(15) NOT NULL,
                remarks VARCHAR(150),
                marked_by INT REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (student_id, attendance_date)
            );""",

            f"""CREATE TABLE IF NOT EXISTS staff_attendance (
                id {big_pk_type},
                staff_id INT NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
                attendance_date DATE NOT NULL,
                status VARCHAR(15) NOT NULL,
                check_in_time VARCHAR(20),
                check_out_time VARCHAR(20),
                remarks VARCHAR(150),
                marked_by INT REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (staff_id, attendance_date)
            );""",

            f"""CREATE TABLE IF NOT EXISTS fee_heads (
                id {pk_type},
                name VARCHAR(80) UNIQUE NOT NULL,
                description TEXT,
                is_active BOOLEAN DEFAULT 1
            );""",

            f"""CREATE TABLE IF NOT EXISTS fee_structures (
                id {pk_type},
                academic_session_id INT NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
                class_id INT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                fee_head_id INT NOT NULL REFERENCES fee_heads(id) ON DELETE RESTRICT,
                amount NUMERIC(10, 2) NOT NULL,
                frequency VARCHAR(20) DEFAULT 'Monthly',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (academic_session_id, class_id, fee_head_id)
            );""",

            f"""CREATE TABLE IF NOT EXISTS student_fee_discounts (
                id {pk_type},
                student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                fee_head_id INT NOT NULL REFERENCES fee_heads(id) ON DELETE RESTRICT,
                discount_type VARCHAR(15) NOT NULL,
                discount_value NUMERIC(10, 2) NOT NULL,
                reason VARCHAR(100),
                is_active BOOLEAN DEFAULT 1
            );""",

            f"""CREATE TABLE IF NOT EXISTS fee_invoices (
                id {big_pk_type},
                invoice_number VARCHAR(40) UNIQUE NOT NULL,
                student_id INT NOT NULL REFERENCES students(id) ON DELETE RESTRICT,
                academic_session_id INT NOT NULL REFERENCES academic_sessions(id) ON DELETE RESTRICT,
                class_id INT NOT NULL REFERENCES classes(id) ON DELETE RESTRICT,
                section_id INT NOT NULL REFERENCES sections(id) ON DELETE RESTRICT,
                billing_month INT NOT NULL,
                billing_year INT NOT NULL,
                issue_date DATE NOT NULL,
                due_date DATE NOT NULL,
                gross_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
                discount_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
                fine_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
                net_payable NUMERIC(10, 2) NOT NULL,
                paid_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
                balance_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
                status VARCHAR(20) DEFAULT 'Unpaid',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (student_id, academic_session_id, billing_month, billing_year)
            );""",

            f"""CREATE TABLE IF NOT EXISTS fee_invoice_items (
                id {big_pk_type},
                invoice_id BIGINT NOT NULL REFERENCES fee_invoices(id) ON DELETE CASCADE,
                fee_head_id INT NOT NULL REFERENCES fee_heads(id) ON DELETE RESTRICT,
                amount NUMERIC(10, 2) NOT NULL
            );""",

            f"""CREATE TABLE IF NOT EXISTS fee_payments (
                id {big_pk_type},
                invoice_id BIGINT NOT NULL REFERENCES fee_invoices(id) ON DELETE RESTRICT,
                receipt_number VARCHAR(40) UNIQUE NOT NULL,
                payment_date DATE NOT NULL,
                amount_paid NUMERIC(10, 2) NOT NULL,
                payment_mode VARCHAR(30) DEFAULT 'Cash',
                reference_number VARCHAR(60),
                received_by INT REFERENCES users(id) ON DELETE SET NULL,
                remarks TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",

            f"""CREATE TABLE IF NOT EXISTS exams (
                id {pk_type},
                academic_session_id INT NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
                name VARCHAR(80) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                status VARCHAR(20) DEFAULT 'Scheduled',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );""",

            f"""CREATE TABLE IF NOT EXISTS exam_subjects (
                id {pk_type},
                exam_id INT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
                class_id INT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                subject_id INT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
                exam_date DATE,
                max_marks NUMERIC(5, 2) NOT NULL DEFAULT 100.00,
                passing_marks NUMERIC(5, 2) NOT NULL DEFAULT 40.00,
                UNIQUE (exam_id, class_id, subject_id)
            );""",

            f"""CREATE TABLE IF NOT EXISTS grading_scales (
                id {pk_type},
                grade_name VARCHAR(10) NOT NULL,
                min_percentage NUMERIC(5, 2) NOT NULL,
                max_percentage NUMERIC(5, 2) NOT NULL,
                grade_point NUMERIC(4, 2),
                remarks VARCHAR(50)
            );""",

            f"""CREATE TABLE IF NOT EXISTS exam_marks (
                id {big_pk_type},
                exam_subject_id INT NOT NULL REFERENCES exam_subjects(id) ON DELETE CASCADE,
                student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                marks_obtained NUMERIC(5, 2) DEFAULT 0.00,
                is_absent BOOLEAN DEFAULT 0,
                grade VARCHAR(10),
                teacher_remarks VARCHAR(150),
                entered_by INT REFERENCES users(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (exam_subject_id, student_id)
            );"""
        ]

        with self.transaction() as conn:
            for stmt in ddl_statements:
                conn.execute(text(stmt))

        logger.info("Database tables verified/created successfully.")
        self._seed_default_data()

    def _seed_default_data(self):
        """Seeds initial roles, admin user, 13 classes, sections, fee heads, and grading."""
        # 1. Roles
        roles = [
            ("Admin", "Full administrative control over all modules"),
            ("Teacher", "Academic marks entry, attendance marking, student viewing"),
            ("Staff", "Fee collection, student registration, basic reporting")
        ]
        for role_name, desc in roles:
            existing = self.fetch_one("SELECT id FROM roles WHERE name = :name", {"name": role_name})
            if not existing:
                self.execute_query(
                    "INSERT INTO roles (name, description) VALUES (:name, :desc)",
                    {"name": role_name, "desc": desc}
                )

        # 2. Default Admin User
        admin_role = self.fetch_one("SELECT id FROM roles WHERE name = 'Admin'")
        admin_user = self.fetch_one("SELECT id FROM users WHERE username = 'admin'")
        if not admin_user and admin_role:
            hashed_pwd = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            self.execute_query(
                """INSERT INTO users (username, password_hash, full_name, email, role_id)
                   VALUES (:u, :p, :fn, :em, :rid)""",
                {
                    "u": "admin",
                    "p": hashed_pwd,
                    "fn": "System Administrator",
                    "em": "admin@school.local",
                    "rid": admin_role["id"]
                }
            )
            logger.info("Default admin user created ('admin' / 'admin123').")

        # 3. Academic Session
        cur_session = self.fetch_one("SELECT id FROM academic_sessions WHERE is_current = 1")
        if not cur_session:
            self.execute_query(
                """INSERT INTO academic_sessions (session_name, start_date, end_date, is_current)
                   VALUES ('2026-2027', '2026-04-01', '2027-03-31', 1)"""
            )

        # 4. 13 Standard Classes & Default Sections (A, B)
        for order, class_name in enumerate(settings.CLASS_LEVELS, start=1):
            c_row = self.fetch_one("SELECT id FROM classes WHERE name = :name", {"name": class_name})
            if not c_row:
                self.execute_query(
                    "INSERT INTO classes (name, numeric_order) VALUES (:name, :order)",
                    {"name": class_name, "order": order}
                )
                c_row = self.fetch_one("SELECT id FROM classes WHERE name = :name", {"name": class_name})

            class_id = c_row["id"]
            for sec_name in ["A", "B"]:
                sec_row = self.fetch_one(
                    "SELECT id FROM sections WHERE class_id = :cid AND name = :sname",
                    {"cid": class_id, "sname": sec_name}
                )
                if not sec_row:
                    self.execute_query(
                        "INSERT INTO sections (class_id, name) VALUES (:cid, :sname)",
                        {"cid": class_id, "sname": sec_name}
                    )

        # 5. Fee Heads
        fee_heads = [
            ("Tuition Fee", "Monthly regular tuition fee"),
            ("Admission Fee", "One-time registration & admission fee"),
            ("Exam Fee", "Per-term examination and materials fee"),
            ("Sports & Lab Fee", "Sports facilities and science/computer lab maintenance")
        ]
        for fh_name, desc in fee_heads:
            if not self.fetch_one("SELECT id FROM fee_heads WHERE name = :name", {"name": fh_name}):
                self.execute_query(
                    "INSERT INTO fee_heads (name, description) VALUES (:name, :desc)",
                    {"name": fh_name, "desc": desc}
                )

        # 6. Staff Departments
        departments = ["Teaching Faculty", "Accounts & Administration", "Support & Maintenance"]
        for dept in departments:
            if not self.fetch_one("SELECT id FROM staff_departments WHERE name = :name", {"name": dept}):
                self.execute_query(
                    "INSERT INTO staff_departments (name) VALUES (:name)",
                    {"name": dept}
                )

        # 7. Grading Scales
        for g in settings.DEFAULT_GRADING:
            if not self.fetch_one("SELECT id FROM grading_scales WHERE grade_name = :g", {"g": g["grade"]}):
                self.execute_query(
                    """INSERT INTO grading_scales (grade_name, min_percentage, max_percentage, grade_point, remarks)
                       VALUES (:g, :min, :max, :gpa, :rem)""",
                    {
                        "g": g["grade"],
                        "min": g["min"],
                        "max": g["max"],
                        "gpa": g["gpa"],
                        "rem": g["remarks"]
                    }
                )


# Global Database Instance
db_manager = DatabaseManager()

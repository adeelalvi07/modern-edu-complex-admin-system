-- ============================================================================
-- SCHOOL MANAGEMENT SYSTEM (SMS) - PRODUCTION RELATIONAL DATABASE SCHEMA
-- Compatible with PostgreSQL 14+ / 16+, MySQL 8+, and SQLite (via SQLAlchemy)
-- ============================================================================

-- 1. AUTHENTICATION & ROLES
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    role_id INT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    module VARCHAR(50) NOT NULL,
    record_id VARCHAR(50),
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. ACADEMIC SETUP & STUDENTS
CREATE TABLE IF NOT EXISTS academic_sessions (
    id SERIAL PRIMARY KEY,
    session_name VARCHAR(50) UNIQUE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    numeric_order INT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sections (
    id SERIAL PRIMARY KEY,
    class_id INT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    name VARCHAR(20) NOT NULL,
    room_number VARCHAR(20),
    capacity INT DEFAULT 40,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (class_id, name)
);

CREATE TABLE IF NOT EXISTS parents_guardians (
    id SERIAL PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS student_enrollments (
    id BIGSERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    academic_session_id INT NOT NULL REFERENCES academic_sessions(id) ON DELETE RESTRICT,
    class_id INT NOT NULL REFERENCES classes(id) ON DELETE RESTRICT,
    section_id INT NOT NULL REFERENCES sections(id) ON DELETE RESTRICT,
    roll_number INT NOT NULL,
    enrollment_status VARCHAR(20) DEFAULT 'Enrolled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (student_id, academic_session_id),
    UNIQUE (academic_session_id, class_id, section_id, roll_number)
);

-- 3. TEACHER & STAFF MANAGEMENT & PAYROLL
CREATE TABLE IF NOT EXISTS staff_departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS staff (
    id SERIAL PRIMARY KEY,
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
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subjects (
    id SERIAL PRIMARY KEY,
    class_id INT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_name VARCHAR(100) NOT NULL,
    subject_code VARCHAR(20),
    total_marks NUMERIC(5, 2) DEFAULT 100.00,
    passing_marks NUMERIC(5, 2) DEFAULT 40.00,
    UNIQUE (class_id, subject_name)
);

CREATE TABLE IF NOT EXISTS teacher_subject_assignments (
    id SERIAL PRIMARY KEY,
    staff_id INT NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    academic_session_id INT NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    class_id INT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    section_id INT NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    subject_id INT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (academic_session_id, section_id, subject_id)
);

CREATE TABLE IF NOT EXISTS staff_payroll (
    id BIGSERIAL PRIMARY KEY,
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
);

-- 4. ATTENDANCE SYSTEM
CREATE TABLE IF NOT EXISTS student_attendance (
    id BIGSERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id INT NOT NULL REFERENCES classes(id) ON DELETE RESTRICT,
    section_id INT NOT NULL REFERENCES sections(id) ON DELETE RESTRICT,
    attendance_date DATE NOT NULL,
    status VARCHAR(15) NOT NULL,
    remarks VARCHAR(150),
    marked_by INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (student_id, attendance_date)
);

CREATE TABLE IF NOT EXISTS staff_attendance (
    id BIGSERIAL PRIMARY KEY,
    staff_id INT NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    status VARCHAR(15) NOT NULL,
    check_in_time VARCHAR(20),
    check_out_time VARCHAR(20),
    remarks VARCHAR(150),
    marked_by INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (staff_id, attendance_date)
);

-- 5. FEE & FINANCE MODULE
CREATE TABLE IF NOT EXISTS fee_heads (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS fee_structures (
    id SERIAL PRIMARY KEY,
    academic_session_id INT NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    class_id INT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    fee_head_id INT NOT NULL REFERENCES fee_heads(id) ON DELETE RESTRICT,
    amount NUMERIC(10, 2) NOT NULL,
    frequency VARCHAR(20) DEFAULT 'Monthly',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (academic_session_id, class_id, fee_head_id)
);

CREATE TABLE IF NOT EXISTS student_fee_discounts (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    fee_head_id INT NOT NULL REFERENCES fee_heads(id) ON DELETE RESTRICT,
    discount_type VARCHAR(15) NOT NULL,
    discount_value NUMERIC(10, 2) NOT NULL,
    reason VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS fee_invoices (
    id BIGSERIAL PRIMARY KEY,
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
);

CREATE TABLE IF NOT EXISTS fee_invoice_items (
    id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT NOT NULL REFERENCES fee_invoices(id) ON DELETE CASCADE,
    fee_head_id INT NOT NULL REFERENCES fee_heads(id) ON DELETE RESTRICT,
    amount NUMERIC(10, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS fee_payments (
    id BIGSERIAL PRIMARY KEY,
    invoice_id BIGINT NOT NULL REFERENCES fee_invoices(id) ON DELETE RESTRICT,
    receipt_number VARCHAR(40) UNIQUE NOT NULL,
    payment_date DATE NOT NULL,
    amount_paid NUMERIC(10, 2) NOT NULL,
    payment_mode VARCHAR(30) DEFAULT 'Cash',
    reference_number VARCHAR(60),
    received_by INT REFERENCES users(id) ON DELETE SET NULL,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. ACADEMIC & EXAMINATION MODULE
CREATE TABLE IF NOT EXISTS exams (
    id SERIAL PRIMARY KEY,
    academic_session_id INT NOT NULL REFERENCES academic_sessions(id) ON DELETE CASCADE,
    name VARCHAR(80) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'Scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Exam Subjects schedule
CREATE TABLE IF NOT EXISTS exam_subjects (
    id SERIAL PRIMARY KEY,
    exam_id INT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    class_id INT NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id INT NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    exam_date DATE,
    max_marks NUMERIC(5, 2) NOT NULL DEFAULT 100.00,
    passing_marks NUMERIC(5, 2) NOT NULL DEFAULT 40.00,
    UNIQUE (exam_id, class_id, subject_id)
);

CREATE TABLE IF NOT EXISTS grading_scales (
    id SERIAL PRIMARY KEY,
    grade_name VARCHAR(10) NOT NULL,
    min_percentage NUMERIC(5, 2) NOT NULL,
    max_percentage NUMERIC(5, 2) NOT NULL,
    grade_point NUMERIC(4, 2),
    remarks VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS exam_marks (
    id BIGSERIAL PRIMARY KEY,
    exam_subject_id INT NOT NULL REFERENCES exam_subjects(id) ON DELETE CASCADE,
    student_id INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    marks_obtained NUMERIC(5, 2) DEFAULT 0.00,
    is_absent BOOLEAN DEFAULT FALSE,
    grade VARCHAR(10),
    teacher_remarks VARCHAR(150),
    entered_by INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (exam_subject_id, student_id)
);

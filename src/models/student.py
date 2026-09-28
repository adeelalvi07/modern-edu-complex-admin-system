"""
Student, Parent, and Enrollment Domain Models.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

@dataclass
class ParentGuardian:
    id: Optional[int]
    father_name: str
    father_phone: str
    emergency_contact: str
    residential_address: str
    father_cnic_nid: Optional[str] = None
    father_occupation: Optional[str] = None
    father_email: Optional[str] = None
    mother_name: Optional[str] = None
    mother_occupation: Optional[str] = None
    mother_phone: Optional[str] = None
    guardian_relation: str = "Father"

@dataclass
class Student:
    id: Optional[int]
    admission_number: str
    registration_date: date
    first_name: str
    last_name: str
    gender: str
    date_of_birth: date
    parent_id: int
    blood_group: Optional[str] = None
    religion: str = "Islam"
    photo_path: Optional[str] = None
    status: str = "Active"
    parent: Optional[ParentGuardian] = None
    current_class: Optional[str] = None
    current_section: Optional[str] = None
    roll_number: Optional[int] = None

@dataclass
class StudentEnrollment:
    id: Optional[int]
    student_id: int
    academic_session_id: int
    class_id: int
    section_id: int
    roll_number: int
    enrollment_status: str = "Enrolled"

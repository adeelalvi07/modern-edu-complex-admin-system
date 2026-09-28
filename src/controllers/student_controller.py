"""
Student Business Logic and Lifecycle Controller.
"""
from typing import Dict, Any, List, Optional, Tuple
from src.repositories.student_repository import StudentRepository

class StudentController:
    def __init__(self):
        self.repo = StudentRepository()

    def validate_registration_payload(
        self,
        first_name: str,
        last_name: str,
        father_name: str,
        father_phone: str,
        class_id: Any,
        section_id: Any
    ) -> Tuple[bool, str]:
        if not first_name.strip() or not last_name.strip():
            return False, "Student first and last names are mandatory."
        if not father_name.strip():
            return False, "Father / Guardian name is mandatory."
        if not father_phone.strip() or len(father_phone.strip()) < 7:
            return False, "A valid primary contact phone number is mandatory."
        if not class_id or not section_id:
            return False, "Class and Section assignment is required."
        return True, ""

    def register_new_student(
        self,
        student_dict: Dict[str, Any],
        parent_dict: Dict[str, Any],
        class_id: int,
        section_id: int,
        session_id: int
    ) -> Tuple[bool, str, Optional[int]]:
        valid, err = self.validate_registration_payload(
            student_dict.get("first_name", ""),
            student_dict.get("last_name", ""),
            parent_dict.get("father_name", ""),
            parent_dict.get("father_phone", ""),
            class_id,
            section_id
        )
        if not valid:
            return False, err, None

        adm_num = self.repo.generate_admission_number()
        student_dict["admission_number"] = adm_num

        # Auto-compute next roll number in section
        all_students_in_sec = self.repo.search_students(class_id=class_id, section_id=section_id)
        next_roll = len(all_students_in_sec) + 1

        enrollment_data = {
            "academic_session_id": session_id,
            "class_id": class_id,
            "section_id": section_id,
            "roll_number": next_roll
        }

        try:
            student_id = self.repo.register_student(student_dict, parent_dict, enrollment_data)
            return True, f"Student successfully registered with Admission No: {adm_num}", student_id
        except Exception as e:
            return False, f"Failed to register student: {str(e)}", None

    def execute_annual_promotion(
        self,
        source_class_id: int,
        target_class_id: Optional[int],
        target_section_id: int,
        target_session_id: int,
        student_ids: List[int],
        is_graduation: bool = False
    ) -> Tuple[bool, str, int]:
        if not student_ids:
            return False, "Please select at least one student to promote.", 0

        try:
            count = self.repo.promote_students(
                student_ids=student_ids,
                source_class_id=source_class_id,
                target_class_id=target_class_id,
                target_section_id=target_section_id,
                new_session_id=target_session_id,
                is_graduate=is_graduation
            )
            action = "graduated" if is_graduation else "promoted"
            return True, f"Successfully {action} {count} student(s).", count
        except Exception as e:
            return False, f"Promotion process failed: {str(e)}", 0

    def change_student_status(self, student_id: int, new_status: str, remarks: Optional[str] = None) -> Tuple[bool, str]:
        try:
            ok = self.repo.update_student_status(student_id, new_status, remarks)
            if ok:
                return True, f"Student status updated to '{new_status}' successfully."
            return False, "Failed to update student status."
        except Exception as e:
            return False, f"Error updating status: {str(e)}"

    def delete_student(self, student_id: int) -> Tuple[bool, str]:
        return self.repo.delete_student_permanently(student_id)


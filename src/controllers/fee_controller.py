"""
Fee & Financial Operations Controller.
"""
from typing import Dict, Any, List, Optional, Tuple
from src.repositories.fee_repository import FeeRepository

class FeeController:
    def __init__(self):
        self.repo = FeeRepository()

    def generate_monthly_bills(
        self,
        class_id: int,
        session_id: int,
        month: int,
        year: int,
        due_date_str: str
    ) -> Tuple[bool, str, int]:
        try:
            count = self.repo.generate_monthly_vouchers(
                class_id=class_id,
                session_id=session_id,
                month=month,
                year=year,
                due_date_str=due_date_str
            )
            if count == 0:
                return True, "No new vouchers created (either already generated or no fee structure defined).", 0
            return True, f"Successfully created {count} monthly fee vouchers!", count
        except Exception as e:
            return False, f"Failed to generate vouchers: {str(e)}", 0

    def record_fee_payment(
        self,
        invoice_id: int,
        amount: float,
        payment_mode: str,
        ref_number: Optional[str],
        user_id: Optional[int],
        remarks: Optional[str],
        payment_date: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        if amount <= 0:
            return False, "Payment amount must be greater than zero.", None

        try:
            receipt_no = self.repo.process_payment(
                invoice_id=invoice_id,
                amount_paid=amount,
                payment_mode=payment_mode,
                reference_number=ref_number,
                received_by_user_id=user_id,
                remarks=remarks,
                payment_date=payment_date
            )
            if receipt_no:
                return True, f"Payment recorded successfully! Receipt: {receipt_no}", receipt_no
            return False, "Invoice not found or invalid.", None
        except Exception as e:
            return False, f"Payment error: {str(e)}", None

    def get_defaulter_summary(self, class_id: Optional[int] = None) -> List[Dict[str, Any]]:
        return self.repo.get_defaulters(class_id)

"""
Dashboard Analytics and Aggregated KPI Endpoints.
"""

from fastapi import APIRouter, Depends
from datetime import date
from typing import Dict, Any

from database.connection import db_manager
from src.repositories.attendance_repository import AttendanceRepository
from src.repositories.fee_repository import FeeRepository
from src.web.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
attendance_repo = AttendanceRepository()
fee_repo = FeeRepository()


@router.get("/stats")
def get_dashboard_stats(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Returns aggregated real-time school stats for dashboard KPI cards and widgets."""
    today_str = date.today().isoformat()
    current_year = date.today().year
    current_month = date.today().month

    # 1. Total Active Students
    s_row = db_manager.fetch_one("SELECT COUNT(*) as cnt FROM students WHERE status = 'Active'")
    total_students = s_row["cnt"] if s_row else 0

    # 2. Total Active Staff
    st_row = db_manager.fetch_one("SELECT COUNT(*) as cnt FROM staff WHERE is_active = 1")
    total_staff = st_row["cnt"] if st_row else 0

    # 3. Total Classes
    c_row = db_manager.fetch_one("SELECT COUNT(*) as cnt FROM classes")
    total_classes = c_row["cnt"] if c_row else 13

    # 4. Today's Attendance Metrics
    att_metrics = attendance_repo.get_school_attendance_metrics(today_str)
    class_attendance_breakdown = attendance_repo.get_daily_school_attendance_summary(today_str)

    # 5. Financial Summary for Current Month
    fin_query = """
        SELECT 
            COUNT(*) as total_invoices,
            COALESCE(SUM(gross_amount), 0) as total_gross,
            COALESCE(SUM(net_payable), 0) as total_payable,
            COALESCE(SUM(paid_amount), 0) as total_collected,
            COALESCE(SUM(balance_amount), 0) as total_outstanding,
            SUM(CASE WHEN status = 'Paid' THEN 1 ELSE 0 END) as paid_invoices,
            SUM(CASE WHEN status = 'Unpaid' OR status = 'Partially Paid' THEN 1 ELSE 0 END) as unpaid_invoices
        FROM fee_invoices
        WHERE billing_month = :m AND billing_year = :y
    """
    fin_row = db_manager.fetch_one(fin_query, {"m": current_month, "y": current_year})

    # Total Overall Defaulters (All months)
    defaulters_query = """
        SELECT COUNT(DISTINCT student_id) as defaulters_count, COALESCE(SUM(balance_amount), 0) as total_dues
        FROM fee_invoices
        WHERE balance_amount > 0 AND status != 'Paid'
    """
    def_row = db_manager.fetch_one(defaulters_query)

    # 6. Current Academic Session
    sess_row = db_manager.fetch_one("SELECT session_name FROM academic_sessions WHERE is_current = 1")
    session_name = sess_row["session_name"] if sess_row else "2026-2027"

    return {
        "success": True,
        "date": today_str,
        "academic_session": session_name,
        "kpis": {
            "total_students": total_students,
            "total_staff": total_staff,
            "total_classes": total_classes,
            "attendance_today": {
                "percentage": att_metrics.get("overall_percentage", 0.0),
                "total_marked": att_metrics.get("total_marked", 0),
                "total_present": att_metrics.get("total_present", 0),
                "total_absent": att_metrics.get("total_absent", 0),
                "total_late": att_metrics.get("total_late", 0),
                "classes_completed": att_metrics.get("classes_completed", 0),
                "total_classes": att_metrics.get("classes_count", 0),
                "is_fully_marked": att_metrics.get("is_fully_marked", False)
            },
            "finance_month": {
                "month": current_month,
                "year": current_year,
                "total_invoiced": float(fin_row["total_payable"]) if fin_row else 0.0,
                "total_collected": float(fin_row["total_collected"]) if fin_row else 0.0,
                "collection_percentage": round((float(fin_row["total_collected"]) / float(fin_row["total_payable"]) * 100), 1) if fin_row and float(fin_row["total_payable"]) > 0 else 0.0,
                "paid_count": fin_row["paid_invoices"] if fin_row else 0,
                "unpaid_count": fin_row["unpaid_invoices"] if fin_row else 0
            },
            "defaulters": {
                "count": def_row["defaulters_count"] if def_row else 0,
                "total_dues": float(def_row["total_dues"]) if def_row else 0.0
            }
        },
        "class_attendance_summary": class_attendance_breakdown
    }


@router.get("/recent-activity")
def get_recent_activity(current_user: dict = Depends(get_current_user)):
    """Returns recent audit logs and transactions for the activity feed."""
    logs = db_manager.fetch_all(
        """SELECT a.*, u.full_name as user_full_name, u.username
           FROM audit_logs a
           LEFT JOIN users u ON a.user_id = u.id
           ORDER BY a.id DESC LIMIT 15"""
    )
    payments = db_manager.fetch_all(
        """SELECT p.*, fi.invoice_number, s.first_name, s.last_name, s.admission_number, c.name as class_name
           FROM fee_payments p
           JOIN fee_invoices fi ON p.invoice_id = fi.id
           JOIN students s ON fi.student_id = s.id
           JOIN classes c ON fi.class_id = c.id
           ORDER BY p.id DESC LIMIT 10"""
    )
    return {
        "success": True,
        "logs": logs,
        "recent_payments": payments
    }

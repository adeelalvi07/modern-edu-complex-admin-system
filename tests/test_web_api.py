"""
Automated Integration and Unit Tests for SMS Web Portal API.
"""

import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from src.web.app import app
from database.connection import db_manager
from database.demo_seeder import seed_demo_environment

# Initialize DB and Seed for testing
db_manager.init_database()
seed_demo_environment()

client = TestClient(app)


def test_health_check():
    """Verify health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("[PASS] Health check passed")


def test_unauthenticated_access_blocked():
    """Verify protected endpoints reject unauthenticated access with 401."""
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 401
    print("[PASS] Unauthenticated access protection passed")


def test_admin_login_failure():
    """Verify bad credentials return 401."""
    response = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401
    print("[PASS] Invalid credentials rejection passed")


def test_admin_login_success():
    """Verify successful login returns valid JWT token and admin user payload."""
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "Admin"
    print("[PASS] Admin authentication passed")
    return data["token"]


def test_authenticated_workflows(token: str):
    headers = {"Authorization": f"Bearer {token}"}

    # 1. /api/auth/me
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["user"]["username"] == "admin"
    print("[PASS] Current user session verified")

    # 2. /api/dashboard/stats
    dash_res = client.get("/api/dashboard/stats", headers=headers)
    assert dash_res.status_code == 200
    stats = dash_res.json()
    assert stats["success"] is True
    assert stats["kpis"]["total_students"] > 0
    assert stats["kpis"]["total_staff"] > 0
    print(f"[PASS] Dashboard stats verified ({stats['kpis']['total_students']} students, {stats['kpis']['total_staff']} staff)")

    # 3. /api/students
    stu_res = client.get("/api/students", headers=headers)
    assert stu_res.status_code == 200
    stu_data = stu_res.json()
    assert stu_data["success"] is True
    assert len(stu_data["students"]) > 0
    print(f"[PASS] Student directory verified ({stu_data['count']} students loaded)")

    # 4. /api/students/classes/all
    classes_res = client.get("/api/students/classes/all", headers=headers)
    assert classes_res.status_code == 200
    classes = classes_res.json()["classes"]
    assert len(classes) >= 13
    print(f"[PASS] Classes & sections verified ({len(classes)} classes loaded)")

    # 5. /api/attendance/roster
    class_id = classes[0]["id"]
    section_id = classes[0]["sections"][0]["id"]
    att_res = client.get(f"/api/attendance/roster?class_id={class_id}&section_id={section_id}", headers=headers)
    assert att_res.status_code == 200
    assert att_res.json()["success"] is True
    print("[PASS] Attendance roster loading verified")

    # 6. /api/fees/invoices
    fee_res = client.get("/api/fees/invoices", headers=headers)
    assert fee_res.status_code == 200
    assert fee_res.json()["success"] is True
    print(f"[PASS] Fee invoices verified ({fee_res.json()['count']} invoices loaded)")

    # 7. /api/staff
    staff_res = client.get("/api/staff", headers=headers)
    assert staff_res.status_code == 200
    assert staff_res.json()["success"] is True
    print(f"[PASS] Staff & faculty verified ({staff_res.json()['count']} staff members loaded)")

    # 8. /api/exams
    exam_res = client.get("/api/exams", headers=headers)
    assert exam_res.status_code == 200
    assert exam_res.json()["success"] is True
    print("[PASS] Exams endpoint verified")

    # 9. /api/system/backup/create
    backup_res = client.post("/api/system/backup/create", headers=headers)
    assert backup_res.status_code == 200
    assert backup_res.json()["success"] is True
    print("[PASS] Instant backup creation verified")


def run_all_tests():
    print("\n--- Running SMS Web Portal API Tests ---")
    test_health_check()
    test_unauthenticated_access_blocked()
    test_admin_login_failure()
    token = test_admin_login_success()
    test_authenticated_workflows(token)
    print("--- ALL TESTS PASSED SUCCESSFULLY! ---\n")


if __name__ == "__main__":
    run_all_tests()

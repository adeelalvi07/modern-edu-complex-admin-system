"""
Unit and integration tests for security features:
- Brute-force lockout / rate-limiting
- Password change and strength validation
- Profile update
- Security response headers
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from src.web.app import app
from database.connection import db_manager
from src.repositories.user_repository import UserRepository
from src.web.auth import _failed_attempts

client = TestClient(app)
repo = UserRepository()


def test_security_headers():
    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    print("[PASS] Security headers verified.")


def test_password_strength_validation():
    # Weak passwords
    assert not UserRepository.validate_password_strength("short")[0]
    assert not UserRepository.validate_password_strength("alllowercase123")[0]
    assert not UserRepository.validate_password_strength("ALLUPPERCASE123")[0]
    # Strong password
    assert UserRepository.validate_password_strength("StrongPass#2026")[0]
    print("[PASS] Password strength validation verified.")


def test_rate_limiting_brute_force():
    _failed_attempts.clear()
    
    # 5 failed attempts
    for i in range(5):
        res = client.post("/api/auth/login", json={"username": "attacker", "password": "wrongpassword"})
        assert res.status_code == 401

    # 6th attempt should return 429 Too Many Requests
    blocked_res = client.post("/api/auth/login", json={"username": "attacker", "password": "wrongpassword"})
    assert blocked_res.status_code == 429
    assert "lockout" in blocked_res.json()["detail"].lower()
    print("[PASS] Brute-force rate limiting and account lockout verified.")
    _failed_attempts.clear()


def test_change_password_flow():
    _failed_attempts.clear()
    # Reset admin password to admin123 before starting test
    user = repo.get_user_by_username("admin")
    if user:
        repo.force_update_password(user["id"], "admin123", validate=False)

    # Log in as admin
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert login_res.status_code == 200
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify security status
    status_res = client.get("/api/auth/security-status", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["is_default_password"] is True

    # Attempt weak password
    weak_res = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"old_password": "admin123", "new_password": "weak", "confirm_password": "weak"}
    )
    assert weak_res.status_code == 400

    # Attempt mismatched password
    mismatch_res = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"old_password": "admin123", "new_password": "StrongPassword1", "confirm_password": "DifferentPassword1"}
    )
    assert mismatch_res.status_code == 400

    # Successful password change
    change_res = client.post(
        "/api/auth/change-password",
        headers=headers,
        json={"old_password": "admin123", "new_password": "NewStrongPass#2026", "confirm_password": "NewStrongPass#2026"}
    )
    assert change_res.status_code == 200
    assert change_res.json()["success"] is True

    # Old password no longer works
    fail_res = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert fail_res.status_code == 401

    # New password works
    success_res = client.post("/api/auth/login", json={"username": "admin", "password": "NewStrongPass#2026"})
    assert success_res.status_code == 200
    new_token = success_res.json()["token"]

    # Verify is_default_password is now False
    new_status = client.get("/api/auth/security-status", headers={"Authorization": f"Bearer {new_token}"})
    assert new_status.json()["is_default_password"] is False
    print("[PASS] Full password change lifecycle verified.")

    # Revert back to admin123 so demo remains predictable for user until they choose their own password
    repo.force_update_password(login_res.json()["user"]["id"], "admin123", validate=False)


if __name__ == "__main__":
    print("\n--- Running Security & Authentication Tests ---")
    test_security_headers()
    test_password_strength_validation()
    test_rate_limiting_brute_force()
    test_change_password_flow()
    print("--- ALL SECURITY TESTS PASSED! ---\n")

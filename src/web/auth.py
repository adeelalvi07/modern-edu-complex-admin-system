"""
Authentication and Session Security for SMS Web Portal.
Implements HMAC-SHA256 signed session tokens with HTTP-only cookies and Bearer tokens.
"""

import hmac
import hashlib
import json
import base64
import time
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import settings
from src.repositories.user_repository import UserRepository

# Secret key loaded dynamically from settings / persistent salt
SECRET_KEY = settings.SECRET_KEY

security_scheme = HTTPBearer(auto_error=False)
user_repo = UserRepository()

# In-memory sliding window rate limiter: maps keys to lists of timestamp floats
_failed_attempts: Dict[str, list] = {}

def check_login_rate_limit(client_ip: str, username: str) -> Optional[int]:
    """
    Checks if client IP or username has exceeded maximum failed login attempts.
    Returns remaining lockout seconds if blocked, or None if allowed.
    """
    now = time.time()
    window = settings.LOGIN_LOCKOUT_MINUTES * 60
    max_attempts = settings.LOGIN_MAX_FAILED_ATTEMPTS

    for key in [f"ip:{client_ip}", f"user:{username.strip().lower()}"]:
        attempts = _failed_attempts.get(key, [])
        valid_attempts = [t for t in attempts if now - t < window]
        _failed_attempts[key] = valid_attempts

        if len(valid_attempts) >= max_attempts:
            oldest = valid_attempts[0]
            remaining = int(window - (now - oldest))
            return max(remaining, 1)

    return None

def record_failed_login(client_ip: str, username: str):
    """Records a failed login attempt for rate limiting."""
    now = time.time()
    for key in [f"ip:{client_ip}", f"user:{username.strip().lower()}"]:
        if key not in _failed_attempts:
            _failed_attempts[key] = []
        _failed_attempts[key].append(now)

def reset_failed_login(client_ip: str, username: str):
    """Resets failed login counter upon successful authentication."""
    for key in [f"ip:{client_ip}", f"user:{username.strip().lower()}"]:
        _failed_attempts.pop(key, None)


def _base64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _base64_url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def create_access_token(user: Dict[str, Any], remember: bool = False) -> str:
    """Creates an HMAC-SHA256 signed JWT-like token."""
    header = {"alg": "HS256", "typ": "JWT"}
    expiry_seconds = (86400 * 30) if remember else (settings.SESSION_EXPIRE_HOURS * 3600)
    payload = {
        "sub": user["id"],
        "username": user["username"],
        "full_name": user.get("full_name", ""),
        "role": user.get("role_name") or user.get("role", "Admin"),
        "exp": int(time.time()) + expiry_seconds
    }

    encoded_header = _base64_url_encode(json.dumps(header).encode("utf-8"))
    encoded_payload = _base64_url_encode(json.dumps(payload).encode("utf-8"))
    signature_base = f"{encoded_header}.{encoded_payload}".encode("utf-8")

    signature = hmac.new(SECRET_KEY.encode("utf-8"), signature_base, hashlib.sha256).digest()
    encoded_signature = _base64_url_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verifies HMAC-SHA256 token and returns payload if valid and not expired."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        encoded_header, encoded_payload, encoded_signature = parts
        signature_base = f"{encoded_header}.{encoded_payload}".encode("utf-8")

        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), signature_base, hashlib.sha256).digest()
        actual_sig = _base64_url_decode(encoded_signature)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_bytes = _base64_url_decode(encoded_payload)
        payload = json.loads(payload_bytes.decode("utf-8"))

        if payload.get("exp", 0) < int(time.time()):
            return None

        return payload
    except Exception:
        return None


def get_current_user(request: Request) -> Dict[str, Any]:
    """Dependency: Extracts and verifies user from Authorization header or cookie."""
    token = None

    # 1. Check Authorization Bearer header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]

    # 2. Fallback to access_token cookie
    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or not logged in. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency: Enforces administrator privileges."""
    if current_user.get("role") != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required for this action."
        )
    return current_user

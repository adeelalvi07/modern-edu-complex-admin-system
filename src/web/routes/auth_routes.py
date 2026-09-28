"""
Authentication API Endpoints.
Includes brute-force rate limiting, password changing, profile management, and session tokens.
"""

import time
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends
from pydantic import BaseModel
from typing import Optional

from config import settings
from src.repositories.user_repository import UserRepository
from src.web.auth import (
    create_access_token,
    get_current_user,
    check_login_rate_limit,
    record_failed_login,
    reset_failed_login
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
user_repo = UserRepository()


class LoginRequest(BaseModel):
    username: str
    password: str
    remember: Optional[bool] = False


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


class UpdateProfileRequest(BaseModel):
    username: str
    full_name: str
    email: Optional[str] = None


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response):
    """Authenticates admin with brute-force rate-limiting, returns session token + sets secure cookie."""
    username = payload.username.strip()
    password = payload.password
    ip = request.client.host if request.client else "127.0.0.1"

    # 1. Check Rate Limit Lockout
    lockout_remaining = check_login_rate_limit(ip, username)
    if lockout_remaining:
        mins = max(1, round(lockout_remaining / 60))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Security lockout active. Please wait {mins} minute(s) before trying again."
        )

    # 2. Verify Credentials
    user = user_repo.verify_credentials(username, password)

    if not user:
        # Record failed attempt for rate limiting
        record_failed_login(ip, username)
        time.sleep(0.4)  # Mitigation against timing/brute force attacks

        try:
            user_repo.log_audit(
                user_id=None,
                action="LOGIN_FAILED",
                module="AUTH",
                record_id=username,
                details=f"Failed login attempt for user '{username}' from IP {ip}"
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password. Please verify and try again."
        )

    # 3. Reset rate limit counter on success
    reset_failed_login(ip, username)

    # 4. Generate token
    token = create_access_token(user, remember=payload.remember)

    # 5. Set HTTP-only Cookie with modern security
    max_age = (86400 * 30) if payload.remember else (settings.SESSION_EXPIRE_HOURS * 3600)
    is_secure = settings.COOKIE_SECURE or (request.url.scheme == "https")
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=max_age,
        samesite="lax",
        secure=is_secure
    )

    # 6. Log successful login
    try:
        user_repo.log_audit(
            user_id=user["id"],
            action="LOGIN_SUCCESS",
            module="AUTH",
            record_id=str(user["id"]),
            details=f"User {user['username']} logged in via Web Portal from IP {ip}"
        )
    except Exception:
        pass

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user.get("full_name", ""),
            "role": user.get("role_name", "Admin"),
            "email": user.get("email")
        },
        "is_default_password": user_repo.is_default_password(user["id"])
    }


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    """Changes the current authenticated user's password with strength validation."""
    user_id = current_user.get("sub") or current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user session.")

    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirmation password do not match.")

    success, msg = user_repo.change_password(
        user_id=user_id,
        old_password=payload.old_password,
        new_password=payload.new_password
    )

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"success": True, "message": msg}


@router.post("/update-profile")
def update_profile(payload: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    """Updates admin username, full name, and email."""
    user_id = current_user.get("sub") or current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user session.")

    success, msg = user_repo.update_profile(
        user_id=user_id,
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email
    )

    if not success:
        raise HTTPException(status_code=400, detail=msg)

    # Return refreshed user info
    updated_user = user_repo.get_user_by_id(user_id)
    return {
        "success": True,
        "message": msg,
        "user": {
            "id": updated_user["id"],
            "username": updated_user["username"],
            "full_name": updated_user.get("full_name", ""),
            "role": updated_user.get("role_name", "Admin"),
            "email": updated_user.get("email")
        }
    }


@router.get("/security-status")
def get_security_status(current_user: dict = Depends(get_current_user)):
    """Checks whether the current user is still using default credentials."""
    user_id = current_user.get("sub") or current_user.get("id")
    user = user_repo.get_user_by_id(user_id) if user_id else None
    is_default = user_repo.is_default_password(user_id) if user_id else False

    return {
        "success": True,
        "is_default_password": is_default,
        "username": user["username"] if user else current_user.get("username"),
        "full_name": user["full_name"] if user else current_user.get("full_name"),
        "email": user.get("email") if user else None,
        "role": user.get("role_name") if user else current_user.get("role")
    }


@router.post("/logout")
def logout(response: Response, current_user: dict = Depends(get_current_user)):
    """Logs out user and clears session cookie."""
    response.delete_cookie(key="access_token")
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Returns current active user details."""
    user_id = current_user.get("sub") or current_user.get("id")
    user = user_repo.get_user_by_id(user_id) if user_id else None
    return {
        "success": True,
        "user": current_user,
        "is_default_password": user_repo.is_default_password(user_id) if user_id else False,
        "email": user.get("email") if user else None
    }

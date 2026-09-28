"""
Authentication & Access Control Session Controller.
"""
from typing import Optional, Dict, Any
from src.repositories.user_repository import UserRepository

class AuthController:
    """Manages active user session and role-based permissions."""
    _current_user: Optional[Dict[str, Any]] = None

    def __init__(self):
        self.repo = UserRepository()

    def login(self, username: str, password_plain: str) -> bool:
        user = self.repo.verify_credentials(username, password_plain)
        if user:
            AuthController._current_user = user
            self.repo.log_audit(user["id"], "LOGIN", "AUTH", str(user["id"]), "User logged in successfully")
            return True
        return False

    def logout(self):
        if AuthController._current_user:
            self.repo.log_audit(AuthController._current_user["id"], "LOGOUT", "AUTH", str(AuthController._current_user["id"]))
        AuthController._current_user = None

    @classmethod
    def get_current_user(cls) -> Optional[Dict[str, Any]]:
        return cls._current_user

    @classmethod
    def is_authenticated(cls) -> bool:
        return cls._current_user is not None

    @classmethod
    def has_role(cls, *allowed_roles: str) -> bool:
        if not cls._current_user:
            return False
        role = cls._current_user.get("role_name", "")
        return role in allowed_roles or "Admin" in role

    @classmethod
    def get_role_name(cls) -> str:
        if not cls._current_user:
            return "Guest"
        return cls._current_user.get("role_name", "User")

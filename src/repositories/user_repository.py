"""
User & Authentication Repository.
"""
from typing import Optional, List, Dict, Any
from src.repositories.base_repository import BaseRepository
import bcrypt

class UserRepository(BaseRepository):
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT u.*, r.name as role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = :username AND u.is_active = 1
        """
        return self.db.fetch_one(query, {"username": username})

    def verify_credentials(self, username: str, password_plain: str) -> Optional[Dict[str, Any]]:
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        stored_hash = user["password_hash"].encode("utf-8")
        if bcrypt.checkpw(password_plain.encode("utf-8"), stored_hash):
            # Update last login
            self.db.execute_query(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = :id",
                {"id": user["id"]}
            )
            return user
        return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        query = """
            SELECT u.id, u.username, u.full_name, u.email, u.phone, r.name as role, u.is_active, u.last_login
            FROM users u
            JOIN roles r ON u.role_id = r.id
            ORDER BY u.id ASC
        """
        return self.db.fetch_all(query)

    def get_all_roles(self) -> List[Dict[str, Any]]:
        return self.db.fetch_all("SELECT * FROM roles ORDER BY id ASC")

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT u.*, r.name as role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.id = :id AND u.is_active = 1
        """
        return self.db.fetch_one(query, {"id": user_id})

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """Validates that a password meets baseline security standards."""
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter (A-Z)."
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter (a-z)."
        if not any(c.isdigit() or not c.isalnum() for c in password):
            return False, "Password must contain at least one number (0-9) or special symbol."
        return True, ""

    def is_default_password(self, user_id: int) -> bool:
        """Checks if the user's password is the default 'admin123'."""
        user = self.get_user_by_id(user_id)
        if not user or not user.get("password_hash"):
            return False
        stored_hash = user["password_hash"].encode("utf-8")
        return bcrypt.checkpw("admin123".encode("utf-8"), stored_hash)

    def change_password(self, user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
        """Changes user password after verifying old password and validating new strength."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "User not found."

        stored_hash = user["password_hash"].encode("utf-8")
        if not bcrypt.checkpw(old_password.encode("utf-8"), stored_hash):
            return False, "Current password is incorrect."

        if old_password == new_password:
            return False, "New password cannot be identical to current password."

        valid, err_msg = self.validate_password_strength(new_password)
        if not valid:
            return False, err_msg

        new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        self.db.execute_query(
            "UPDATE users SET password_hash = :hash, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
            {"hash": new_hash, "id": user_id}
        )

        self.log_audit(
            user_id=user_id,
            action="PASSWORD_CHANGED",
            module="AUTH",
            record_id=str(user_id),
            details=f"User {user['username']} successfully changed their password."
        )
        return True, "Password changed successfully."

    def force_update_password(self, user_id: int, new_password: str, validate: bool = True) -> tuple[bool, str]:
        """Directly updates a user's password (used by CLI, test teardown, or SuperAdmin reset)."""
        if validate:
            valid, err_msg = self.validate_password_strength(new_password)
            if not valid:
                return False, err_msg

        new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        self.db.execute_query(
            "UPDATE users SET password_hash = :hash, updated_at = CURRENT_TIMESTAMP WHERE id = :id",
            {"hash": new_hash, "id": user_id}
        )
        return True, "Password updated successfully."

    def update_profile(self, user_id: int, username: str, full_name: str, email: Optional[str] = None) -> tuple[bool, str]:
        """Updates user profile information ensuring username and email uniqueness."""
        username = username.strip()
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters."

        # Check if username is taken by another user
        existing_u = self.db.fetch_one(
            "SELECT id FROM users WHERE username = :u AND id != :id",
            {"u": username, "id": user_id}
        )
        if existing_u:
            return False, f"Username '{username}' is already taken by another account."

        if email:
            email = email.strip()
            existing_e = self.db.fetch_one(
                "SELECT id FROM users WHERE email = :e AND id != :id",
                {"e": email, "id": user_id}
            )
            if existing_e:
                return False, f"Email address '{email}' is already in use."

        self.db.execute_query(
            """UPDATE users 
               SET username = :u, full_name = :fn, email = :em, updated_at = CURRENT_TIMESTAMP 
               WHERE id = :id""",
            {"u": username, "fn": full_name.strip(), "em": email or None, "id": user_id}
        )

        self.log_audit(
            user_id=user_id,
            action="PROFILE_UPDATED",
            module="AUTH",
            record_id=str(user_id),
            details=f"User updated profile: username={username}, name={full_name}"
        )
        return True, "Profile updated successfully."

    def log_audit(self, user_id: Optional[int], action: str, module: str, record_id: Optional[str] = None, details: Optional[str] = None):
        query = """
            INSERT INTO audit_logs (user_id, action, module, record_id, details)
            VALUES (:uid, :act, :mod, :rid, :det)
        """
        self.db.execute_query(query, {
            "uid": user_id,
            "act": action,
            "mod": module,
            "rid": record_id,
            "det": details
        })


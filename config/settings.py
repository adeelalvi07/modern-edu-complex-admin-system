"""
Central Settings and Configuration for School Management System.
Handles environment variables, paths, database credentials, and school constants.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKUP_DIR = BASE_DIR / "backups"
LOGS_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"
EXPORTS_DIR = BASE_DIR / "exports"

for d in [BACKUP_DIR, LOGS_DIR, ASSETS_DIR, EXPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Load optional .env file
ENV_FILE = BASE_DIR / ".env"
if ENV_FILE.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(ENV_FILE)
    except ImportError:
        pass

# School Profile
SCHOOL_NAME = os.getenv("SCHOOL_NAME", "MODERN EDUCATIONAL COMPLEX")
SCHOOL_TAGLINE = os.getenv("SCHOOL_TAGLINE", "Excellence in Education & Character Building")
SCHOOL_ADDRESS = os.getenv("SCHOOL_ADDRESS", "Main Campus, Education City")
SCHOOL_PHONE = os.getenv("SCHOOL_PHONE", "+92-300-1234567")
SCHOOL_EMAIL = os.getenv("SCHOOL_EMAIL", "info@modernedu.edu.pk")

# Database Configuration (Multi-user LAN, Cloud Postgres, or Offline Local)
# DB_TYPE options: "sqlite" (offline standalone) | "postgresql" (LAN / Cloud) | "mysql"
DATABASE_URL = os.getenv("DATABASE_URL")
DB_TYPE = os.getenv("DB_TYPE", "postgresql" if DATABASE_URL else "sqlite")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "5432" if DB_TYPE == "postgresql" else "3306"))
DB_NAME = os.getenv("DB_NAME", "school_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# SQLite fallback path
SQLITE_DB_PATH = BASE_DIR / "database" / "school_system.db"

# Security Configuration
import secrets

def _get_or_create_secret_key() -> str:
    env_key = os.getenv("SECRET_KEY")
    if env_key:
        return env_key
    key_file = BASE_DIR / ".secret_key"
    if key_file.exists():
        try:
            return key_file.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    new_key = secrets.token_hex(32)
    try:
        key_file.write_text(new_key, encoding="utf-8")
    except Exception:
        pass
    return new_key

SECRET_KEY = _get_or_create_secret_key()
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() in ("true", "1", "yes")
SESSION_EXPIRE_HOURS = int(os.getenv("SESSION_EXPIRE_HOURS", "24"))
LOGIN_MAX_FAILED_ATTEMPTS = int(os.getenv("LOGIN_MAX_FAILED_ATTEMPTS", "5"))
LOGIN_LOCKOUT_MINUTES = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))

# 13 Standard Classes
CLASS_LEVELS = [
    "Playgroup",
    "Nursery",
    "Prep",
    "Class 1",
    "Class 2",
    "Class 3",
    "Class 4",
    "Class 5",
    "Class 6",
    "Class 7",
    "Class 8",
    "Class 9",
    "Class 10"
]

DEFAULT_SECTIONS = ["A", "B", "C"]

# Grading Scale Standard
DEFAULT_GRADING = [
    {"grade": "A+", "min": 85.0, "max": 100.0, "gpa": 4.0, "remarks": "Outstanding"},
    {"grade": "A",  "min": 75.0, "max": 84.99, "gpa": 3.5, "remarks": "Excellent"},
    {"grade": "B",  "min": 65.0, "max": 74.99, "gpa": 3.0, "remarks": "Very Good"},
    {"grade": "C",  "min": 50.0, "max": 64.99, "gpa": 2.5, "remarks": "Satisfactory"},
    {"grade": "D",  "min": 40.0, "max": 49.99, "gpa": 2.0, "remarks": "Pass"},
    {"grade": "F",  "min": 0.0,  "max": 39.99, "gpa": 0.0, "remarks": "Fail"}
]

# Backup Settings
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
AUTO_BACKUP_TIME = os.getenv("AUTO_BACKUP_TIME", "23:00")

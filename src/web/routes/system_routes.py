"""
System Operations, Database Backups, Audit Logs, and School Settings Endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from database.connection import db_manager
from src.services.backup_service import DatabaseBackupManager
from src.web.auth import get_current_user, require_admin
from config import settings

router = APIRouter(prefix="/api/system", tags=["System"])
backup_manager = DatabaseBackupManager()


@router.get("/school-info")
def get_school_info():
    """Returns general school profile settings (public or authenticated)."""
    cur_sess = db_manager.fetch_one("SELECT session_name FROM academic_sessions WHERE is_current = 1")
    return {
        "success": True,
        "school_name": settings.SCHOOL_NAME,
        "school_tagline": settings.SCHOOL_TAGLINE,
        "school_address": settings.SCHOOL_ADDRESS,
        "school_phone": settings.SCHOOL_PHONE,
        "school_email": settings.SCHOOL_EMAIL,
        "active_session": cur_sess["session_name"] if cur_sess else "2026-2027",
        "db_type": settings.DB_TYPE
    }


@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 50,
    current_user: dict = Depends(require_admin)
):
    """Lists system audit logs."""
    logs = db_manager.fetch_all(
        f"""SELECT a.*, u.username, u.full_name as user_full_name
            FROM audit_logs a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.id DESC LIMIT {limit}"""
    )
    return {"success": True, "count": len(logs), "logs": logs}


@router.get("/backups")
def list_backups(current_user: dict = Depends(require_admin)):
    """Lists existing database backup archives."""
    backup_files = []
    if settings.BACKUP_DIR.exists():
        for p in sorted(settings.BACKUP_DIR.glob("*.sql.gz"), key=lambda x: x.stat().st_mtime, reverse=True):
            stat = p.stat()
            backup_files.append({
                "filename": p.name,
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
    return {"success": True, "count": len(backup_files), "backups": backup_files}


@router.post("/backup/create")
def create_instant_backup(current_user: dict = Depends(require_admin)):
    """Triggers immediate database backup and compresses to GZIP archive."""
    success, msg, checksum = backup_manager.perform_backup()
    if not success:
        raise HTTPException(status_code=500, detail=msg)

    # Log audit
    user_id = current_user.get("sub") or current_user.get("id")
    try:
        db_manager.execute_query(
            """INSERT INTO audit_logs (user_id, action, module, record_id, details)
               VALUES (:uid, 'BACKUP_CREATED', 'SYSTEM', :rid, :det)""",
            {
                "uid": user_id,
                "rid": msg,
                "det": f"Instant backup created via Web Portal. SHA-256: {checksum}"
            }
        )
    except Exception:
        pass

    return {
        "success": True,
        "message": f"Backup created successfully: {msg}",
        "checksum": checksum
    }


@router.get("/backups/{filename}/download")
def download_backup(filename: str, current_user: dict = Depends(require_admin)):
    """Downloads a backup archive safely."""
    # Prevent path traversal
    safe_name = Path(filename).name
    backup_file = settings.BACKUP_DIR / safe_name
    if not backup_file.exists() or not backup_file.is_file():
        raise HTTPException(status_code=404, detail="Backup file not found")

    return FileResponse(
        path=str(backup_file),
        media_type="application/gzip",
        filename=safe_name
    )

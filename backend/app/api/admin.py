import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.database.session import get_db
from app.models.user import User, AuditLog, UserRole
from app.schemas.auth import UserResponse
from app.schemas.evidence import AuditLogResponse
from app.core.security import get_public_key_hex
from app.api.deps import require_roles
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/admin", tags=["System Administration"])

@router.get("/users", response_model=List[UserResponse])
def list_system_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.SUPERVISOR.value]))
):
    users = db.query(User).order_by(User.id.asc()).all()
    return users

@router.put("/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN.value]))
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own administrator account.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.is_active = not user.is_active
    db.commit()

    log_audit_event(
        db,
        event_type="USER_STATUS_TOGGLED",
        user_id=current_user.id,
        user_name=current_user.username,
        details={"target_user": user.username, "new_active_status": user.is_active}
    )

    return {"message": f"User {user.username} active status set to {user.is_active}.", "is_active": user.is_active}

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.AUDITOR.value]))
):
    logs = db.query(AuditLog).order_by(desc(AuditLog.id)).limit(limit).all()
    return logs

@router.get("/system-health")
def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.SUPERVISOR.value, UserRole.AUDITOR.value]))
):
    # Check disk storage usage
    upload_stat = shutil.disk_usage(settings.UPLOAD_PATH)
    
    return {
        "status": "HEALTHY",
        "system_version": settings.SYSTEM_VERSION,
        "algorithm_version": settings.ALGORITHM_VERSION,
        "signing_key_id": settings.ED25519_KEY_ID,
        "public_key_hex": get_public_key_hex(),
        "database_connected": True,
        "storage": {
            "upload_path": settings.UPLOAD_PATH,
            "total_gb": round(upload_stat.total / (1024**3), 2),
            "free_gb": round(upload_stat.free / (1024**3), 2)
        }
    }

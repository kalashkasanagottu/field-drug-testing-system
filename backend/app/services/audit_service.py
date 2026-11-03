import uuid
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.user import AuditLog
from app.cryptography.audit_chain import compute_event_hash, GENESIS_HASH

def log_audit_event(
    db: Session,
    event_type: str,
    user_id: Optional[int] = None,
    user_name: Optional[str] = None,
    related_record_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    client_ip: Optional[str] = None,
    user_agent: Optional[str] = None
) -> AuditLog:
    """
    Creates an immutable, hash-linked chain-of-custody audit event.
    """
    if details is None:
        details = {}

    # Get hash of most recent audit log entry to link the chain
    last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_log.event_hash if last_log and last_log.event_hash else GENESIS_HASH

    now = datetime.now(timezone.utc)
    timestamp_iso = now.isoformat()
    event_id = f"EVT-{now.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"

    event_hash = compute_event_hash(
        prev_event_hash=prev_hash,
        timestamp_iso=timestamp_iso,
        user_id=user_id,
        event_type=event_type,
        related_record_id=related_record_id,
        details=details
    )

    audit_entry = AuditLog(
        event_id=event_id,
        user_id=user_id,
        user_name=user_name,
        event_type=event_type,
        related_record_id=related_record_id,
        details=json.dumps(details),
        client_ip=client_ip,
        user_agent=user_agent,
        prev_event_hash=prev_hash,
        event_hash=event_hash,
        timestamp=now
    )

    db.add(audit_entry)
    db.commit()
    db.refresh(audit_entry)
    return audit_entry

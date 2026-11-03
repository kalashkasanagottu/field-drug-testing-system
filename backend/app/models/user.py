import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from app.database.session import Base

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    FIELD_OFFICER = "FIELD_OFFICER"
    SUPERVISOR = "SUPERVISOR"
    AUDITOR = "AUDITOR"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    badge_number = Column(String(50), nullable=True)
    department = Column(String(100), default="Forensic Field Operations")
    role = Column(String(30), default=UserRole.FIELD_OFFICER.value, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=True)
    user_name = Column(String(100), nullable=True)
    event_type = Column(String(50), index=True, nullable=False)
    related_record_id = Column(String(64), index=True, nullable=True)
    details = Column(Text, nullable=True)
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    prev_event_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

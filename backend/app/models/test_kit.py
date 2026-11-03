import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class ValidationStatus(str, enum.Enum):
    APPROVED = "APPROVED"
    PENDING_VALIDATION = "PENDING_VALIDATION"
    SIMULATION_ONLY = "SIMULATION_ONLY"

class TestKit(Base):
    __tablename__ = "test_kits"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    manufacturer = Column(String(100), nullable=False)
    model_number = Column(String(50), nullable=False)
    analyte = Column(String(100), nullable=False)
    reaction_time_seconds = Column(Integer, default=60)
    instructions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    profiles = relationship("TestKitProfile", back_populates="kit", cascade="all, delete-orphan")

class TestKitProfile(Base):
    __tablename__ = "test_kit_profiles"

    id = Column(Integer, primary_key=True, index=True)
    kit_id = Column(Integer, ForeignKey("test_kits.id"), nullable=False)
    profile_version = Column(String(30), nullable=False)
    validation_status = Column(String(30), default=ValidationStatus.APPROVED.value, nullable=False)
    reference_source = Column(String(200), nullable=False)
    approval_details = Column(String(255), nullable=True)
    
    # Validated Positive Reference (CIELAB)
    positive_cielab_l = Column(Float, nullable=False)
    positive_cielab_a = Column(Float, nullable=False)
    positive_cielab_b = Column(Float, nullable=False)
    positive_delta_e_threshold = Column(Float, default=18.0)

    # Validated Negative Reference (CIELAB)
    negative_cielab_l = Column(Float, nullable=False)
    negative_cielab_a = Column(Float, nullable=False)
    negative_cielab_b = Column(Float, nullable=False)
    negative_delta_e_threshold = Column(Float, default=20.0)

    # Inconclusive margin
    inconclusive_delta_e_threshold = Column(Float, default=10.0)

    # Expected Region of Interest (Normalized 0.0 to 1.0)
    reaction_roi_x = Column(Float, default=0.25)
    reaction_roi_y = Column(Float, default=0.40)
    reaction_roi_w = Column(Float, default=0.50)
    reaction_roi_h = Column(Float, default=0.35)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    kit = relationship("TestKit", back_populates="profiles")

class CalibrationCard(Base):
    __tablename__ = "calibration_cards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    card_type = Column(String(50), nullable=False)
    layout_json = Column(Text, nullable=False)  # JSON specifying reference patches & known Lab values
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

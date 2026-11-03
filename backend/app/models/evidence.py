import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database.session import Base

class ClassificationResult(str, enum.Enum):
    PRESUMPTIVE_POSITIVE = "PRESUMPTIVE_POSITIVE"
    PRESUMPTIVE_NEGATIVE = "PRESUMPTIVE_NEGATIVE"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNABLE_TO_CLASSIFY = "UNABLE_TO_CLASSIFY"

class VerificationStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    INTEGRITY_FAILED = "INTEGRITY_FAILED"
    PENDING = "PENDING"

class SyncStatus(str, enum.Enum):
    SAVED_LOCALLY = "SAVED_LOCALLY"
    PENDING_SYNC = "PENDING_SYNC"
    SYNCHRONIZED = "SYNCHRONIZED"
    FAILED = "FAILED"

class TestRecord(Base):
    __tablename__ = "test_records"

    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(String(50), unique=True, index=True, nullable=False)
    case_reference = Column(String(100), index=True, nullable=True)
    operator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    operator_name = Column(String(100), nullable=False)
    operator_badge = Column(String(50), nullable=True)
    
    kit_id = Column(Integer, ForeignKey("test_kits.id"), nullable=False)
    kit_profile_id = Column(Integer, ForeignKey("test_kit_profiles.id"), nullable=True)
    kit_batch_number = Column(String(50), nullable=False)
    kit_expiry_date = Column(String(30), nullable=True)
    notes = Column(Text, nullable=True)

    # Classification output
    classification_result = Column(String(30), default=ClassificationResult.UNABLE_TO_CLASSIFY.value, nullable=False)
    classification_reason = Column(Text, nullable=True)
    classification_confidence = Column(Float, nullable=True)
    analyte_detected = Column(String(100), nullable=True)
    algorithm_version = Column(String(50), nullable=False)
    profile_version = Column(String(30), nullable=True)

    # GPS and timing
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    gps_accuracy_meters = Column(Float, nullable=True)
    location_unavailable_reason = Column(String(150), nullable=True)
    device_timestamp = Column(DateTime, nullable=False)
    server_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Images and cryptographic hashing
    original_image_path = Column(String(255), nullable=True)
    processed_image_path = Column(String(255), nullable=True)
    original_image_hash = Column(String(64), nullable=True, index=True)  # SHA-256
    image_byte_size = Column(Integer, nullable=True)

    # Asymmetric Digital Signing
    digital_signature = Column(Text, nullable=True)  # Ed25519 signature hex
    signature_algorithm = Column(String(30), default="Ed25519", nullable=False)
    signing_key_id = Column(String(50), nullable=True)
    canonical_record_hash = Column(String(64), nullable=True)

    # Integrity & Verification
    verification_status = Column(String(30), default=VerificationStatus.VERIFIED.value, nullable=False)
    is_provisional = Column(Boolean, default=False)
    client_uuid = Column(String(64), unique=True, index=True, nullable=True)  # Idempotency key
    sync_status = Column(String(30), default=SyncStatus.SYNCHRONIZED.value, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    kit = relationship("TestKit")
    profile = relationship("TestKitProfile")
    analysis = relationship("ImageAnalysisResult", back_populates="record", uselist=False, cascade="all, delete-orphan")
    verifications = relationship("VerificationEvent", back_populates="record", cascade="all, delete-orphan")

class ImageAnalysisResult(Base):
    __tablename__ = "image_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    test_record_id = Column(Integer, ForeignKey("test_records.id"), nullable=False, unique=True)
    
    # Image Quality Checks
    blur_score = Column(Float, nullable=False)
    is_blurry = Column(Boolean, default=False)
    illumination_score = Column(Float, nullable=False)
    is_underexposed = Column(Boolean, default=False)
    is_overexposed = Column(Boolean, default=False)
    card_detected = Column(Boolean, default=True)
    
    # Calibration output
    calibration_error_delta_e = Column(Float, nullable=True)
    
    # Measured Reaction CIELAB
    reaction_cielab_l = Column(Float, nullable=True)
    reaction_cielab_a = Column(Float, nullable=True)
    reaction_cielab_b = Column(Float, nullable=True)
    reaction_rgb_hex = Column(String(10), nullable=True)
    
    # Delta E distances
    positive_delta_e = Column(Float, nullable=True)
    negative_delta_e = Column(Float, nullable=True)
    
    reaction_roi_json = Column(Text, nullable=True)
    quality_passed = Column(Boolean, default=True)
    quality_notes = Column(Text, nullable=True)

    record = relationship("TestRecord", back_populates="analysis")

class VerificationEvent(Base):
    __tablename__ = "verification_events"

    id = Column(Integer, primary_key=True, index=True)
    test_record_id = Column(Integer, ForeignKey("test_records.id"), nullable=False)
    verifier_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    verifier_name = Column(String(100), nullable=False)
    hash_verified = Column(Boolean, nullable=False)
    signature_verified = Column(Boolean, nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    record = relationship("TestRecord", back_populates="verifications")

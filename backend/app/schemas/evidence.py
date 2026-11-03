from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class TestCreateRequest(BaseModel):
    case_reference: Optional[str] = None
    kit_id: int
    kit_batch_number: str
    kit_expiry_date: Optional[str] = None
    notes: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_accuracy_meters: Optional[float] = None
    location_unavailable_reason: Optional[str] = None
    device_timestamp: Optional[datetime] = None
    client_uuid: Optional[str] = None  # Idempotency key for offline sync

class ImageQualityResponse(BaseModel):
    passed: bool
    blur_score: float
    is_blurry: bool
    illumination_score: float
    is_underexposed: bool
    is_overexposed: bool
    notes: str

class ImageAnalysisResponse(BaseModel):
    test_id: str
    classification_result: str
    classification_reason: str
    classification_confidence: float
    analyte_detected: Optional[str] = None
    disclaimer: str
    quality: ImageQualityResponse
    calibration_error_delta_e: Optional[float] = None
    reaction_cielab: Optional[Dict[str, float]] = None
    reaction_hex: Optional[str] = None
    positive_delta_e: Optional[float] = None
    negative_delta_e: Optional[float] = None
    original_image_hash: str
    digital_signature: str
    signing_key_id: str

class VerificationRequest(BaseModel):
    test_id: str
    check_image_tampering: bool = True
    check_digital_signature: bool = True

class VerificationResponse(BaseModel):
    test_id: str
    status: str
    image_hash_verified: bool
    signature_verified: bool
    original_image_hash: str
    computed_image_hash: str
    signing_key_id: str
    details: str
    timestamp: datetime

class TestRecordSummary(BaseModel):
    id: int
    test_id: str
    case_reference: Optional[str] = None
    operator_name: str
    operator_badge: Optional[str] = None
    kit_name: str
    kit_batch_number: str
    analyte_detected: Optional[str] = None
    classification_result: str
    verification_status: str
    sync_status: str
    original_image_hash: Optional[str] = None
    device_timestamp: datetime
    server_timestamp: datetime
    has_gps: bool
    created_at: datetime

class TestRecordDetailResponse(BaseModel):
    id: int
    test_id: str
    case_reference: Optional[str] = None
    operator_id: int
    operator_name: str
    operator_badge: Optional[str] = None
    kit_id: int
    kit_name: str
    kit_manufacturer: str
    kit_batch_number: str
    kit_expiry_date: Optional[str] = None
    notes: Optional[str] = None
    classification_result: str
    classification_reason: Optional[str] = None
    classification_confidence: Optional[float] = None
    analyte_detected: Optional[str] = None
    algorithm_version: str
    profile_version: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_accuracy_meters: Optional[float] = None
    location_unavailable_reason: Optional[str] = None
    device_timestamp: datetime
    server_timestamp: datetime
    original_image_url: Optional[str] = None
    processed_image_url: Optional[str] = None
    original_image_hash: Optional[str] = None
    image_byte_size: Optional[int] = None
    digital_signature: Optional[str] = None
    signature_algorithm: str
    signing_key_id: Optional[str] = None
    canonical_record_hash: Optional[str] = None
    verification_status: str
    is_provisional: bool
    client_uuid: Optional[str] = None
    sync_status: str
    created_at: datetime
    analysis: Optional[Dict[str, Any]] = None
    verifications: List[Dict[str, Any]] = []

class AuditLogResponse(BaseModel):
    id: int
    event_id: str
    user_name: Optional[str] = None
    event_type: str
    related_record_id: Optional[str] = None
    details: Optional[str] = None
    client_ip: Optional[str] = None
    prev_event_hash: Optional[str] = None
    event_hash: str
    timestamp: datetime

    class Config:
        from_attributes = True

class DashboardStatsResponse(BaseModel):
    total_tests: int
    positive_count: int
    negative_count: int
    inconclusive_count: int
    unable_to_classify_count: int
    pending_sync_count: int
    verified_count: int
    integrity_failure_count: int
    recent_tests: List[TestRecordSummary]
    kit_breakdown: List[Dict[str, Any]]
    monthly_trends: List[Dict[str, Any]]
    officer_stats: List[Dict[str, Any]]

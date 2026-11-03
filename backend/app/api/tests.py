import os
import uuid
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.core.config import settings
from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.test_kit import TestKit, TestKitProfile, ValidationStatus
from app.models.evidence import (
    TestRecord, ImageAnalysisResult, ClassificationResult, VerificationStatus, SyncStatus
)
from app.schemas.evidence import (
    TestCreateRequest, ImageAnalysisResponse, ImageQualityResponse,
    TestRecordSummary, TestRecordDetailResponse
)
from app.cryptography.hasher import compute_sha256
from app.core.security import sign_data, build_canonical_payload
from app.computer_vision.quality_checks import check_image_quality
from app.computer_vision.color_calibration import detect_and_calibrate
from app.classification.engine import ClassificationEngine, STATUTORY_DISCLAIMER
from app.services.audit_service import log_audit_event
from app.api.deps import get_current_user

router = APIRouter(prefix="/tests", tags=["Test Management & Field Capture"])

def generate_test_id() -> str:
    now = datetime.now(timezone.utc)
    short_hash = uuid.uuid4().hex[:6].upper()
    return f"DT-{now.strftime('%Y%m%d')}-{short_hash}"

@router.post("", response_model=TestRecordDetailResponse)
def create_test_record(
    test_in: TestCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Idempotency check for offline sync
    if test_in.client_uuid:
        existing = db.query(TestRecord).filter(TestRecord.client_uuid == test_in.client_uuid).first()
        if existing:
            return format_test_detail(existing)

    kit = db.query(TestKit).filter(TestKit.id == test_in.kit_id, TestKit.is_active == True).first()
    if not kit:
        raise HTTPException(status_code=404, detail="Selected test kit not found or inactive.")

    # Find latest approved profile for this kit
    profile = db.query(TestKitProfile).filter(
        TestKitProfile.kit_id == kit.id,
        TestKitProfile.validation_status.in_([ValidationStatus.APPROVED.value, ValidationStatus.SIMULATION_ONLY.value])
    ).order_by(TestKitProfile.id.desc()).first()

    now_utc = datetime.now(timezone.utc)
    test_id = generate_test_id()

    new_record = TestRecord(
        test_id=test_id,
        case_reference=test_in.case_reference,
        operator_id=current_user.id,
        operator_name=current_user.full_name,
        operator_badge=current_user.badge_number,
        kit_id=kit.id,
        kit_profile_id=profile.id if profile else None,
        kit_batch_number=test_in.kit_batch_number,
        kit_expiry_date=test_in.kit_expiry_date,
        notes=test_in.notes,
        classification_result=ClassificationResult.UNABLE_TO_CLASSIFY.value,
        classification_reason="Awaiting camera capture and colorimetric analysis.",
        analyte_detected=None,
        algorithm_version=settings.ALGORITHM_VERSION,
        profile_version=profile.profile_version if profile else "NONE",
        gps_latitude=test_in.gps_latitude,
        gps_longitude=test_in.gps_longitude,
        gps_accuracy_meters=test_in.gps_accuracy_meters,
        location_unavailable_reason=test_in.location_unavailable_reason,
        device_timestamp=test_in.device_timestamp or now_utc,
        server_timestamp=now_utc,
        signature_algorithm="Ed25519",
        signing_key_id=settings.ED25519_KEY_ID,
        verification_status=VerificationStatus.PENDING.value,
        is_provisional=False,
        client_uuid=test_in.client_uuid,
        sync_status=SyncStatus.SYNCHRONIZED.value
    )

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    log_audit_event(
        db,
        event_type="TEST_CREATED",
        user_id=current_user.id,
        user_name=current_user.username,
        related_record_id=new_record.test_id,
        details={
            "case_ref": new_record.case_reference,
            "kit": kit.name,
            "batch": new_record.kit_batch_number,
            "gps": bool(new_record.gps_latitude)
        }
    )

    return format_test_detail(new_record)

@router.post("/{test_id}/capture", response_model=ImageAnalysisResponse)
async def capture_and_analyze(
    test_id: str,
    file: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.query(TestRecord).filter(TestRecord.test_id == test_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Test record not found.")

    # 1. Acquire raw image bytes directly
    raw_bytes = None
    if file:
        raw_bytes = await file.read()
    elif image_base64:
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
        try:
            raw_bytes = base64.b64decode(image_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image data.")

    if not raw_bytes or len(raw_bytes) < 100:
        raise HTTPException(status_code=400, detail="No valid image data provided.")

    # 2. IMMEDIATE CRYPTOGRAPHIC HASHING BEFORE MODIFICATION
    image_sha256 = compute_sha256(raw_bytes)
    image_byte_size = len(raw_bytes)

    # Save original raw uncompressed image directly
    orig_filename = f"{test_id}_orig.jpg"
    orig_path = Path(settings.UPLOAD_PATH) / "original" / orig_filename
    with open(orig_path, "wb") as f:
        f.write(raw_bytes)

    # 3. Decode image with OpenCV for Computer Vision analysis
    nparr = np.frombuffer(raw_bytes, np.uint8)
    image_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image_bgr is None:
        raise HTTPException(status_code=400, detail="Failed to decode image binary.")

    # 4. Forensic Quality Checks
    quality = check_image_quality(image_bgr)

    # 5. Reference Color Card Detection & CIELAB Calibration
    profile = record.profile
    reaction_roi = None
    if profile:
        reaction_roi = {
            "x": profile.reaction_roi_x,
            "y": profile.reaction_roi_y,
            "w": profile.reaction_roi_w,
            "h": profile.reaction_roi_h
        }

    calib = detect_and_calibrate(image_bgr, reaction_roi=reaction_roi)

    # Save processed derivative image
    proc_filename = f"{test_id}_proc.jpg"
    proc_path = Path(settings.UPLOAD_PATH) / "processed" / proc_filename
    cv2.imwrite(str(proc_path), calib["annotated_image_bgr"])

    # 6. Automated Presumptive Classification
    measured_lab = (
        calib["reaction_cielab"]["L"],
        calib["reaction_cielab"]["a"],
        calib["reaction_cielab"]["b"]
    )
    all_approved_profiles = db.query(TestKitProfile).filter(
        TestKitProfile.validation_status.in_([ValidationStatus.APPROVED.value, ValidationStatus.SIMULATION_ONLY.value])
    ).all()

    classification = ClassificationEngine.classify_reaction(
        measured_lab=measured_lab,
        kit_profile=profile,
        quality_assessment=quality,
        calibration_assessment=calib,
        all_profiles=all_approved_profiles
    )

    # Determine detected analyte and sync matched kit
    matched_kit_id = classification.get("matched_kit_id")
    if matched_kit_id and matched_kit_id != record.kit_id:
        record.kit_id = matched_kit_id
        record.kit_profile_id = classification.get("matched_profile_id")
        matched_kit = db.query(TestKit).filter(TestKit.id == matched_kit_id).first()
        if matched_kit:
            record.kit = matched_kit

    analyte_detected = classification.get("analyte_detected")
    if not analyte_detected and classification["result"] == ClassificationResult.PRESUMPTIVE_POSITIVE.value and record.kit:
        analyte_detected = record.kit.analyte

    # 7. Asymmetric Digital Signature Generation (Ed25519 over Canonical JSON)
    record.original_image_path = str(orig_path)
    record.processed_image_path = str(proc_path)
    record.original_image_hash = image_sha256
    record.image_byte_size = image_byte_size
    record.classification_result = classification["result"]
    record.classification_reason = classification["reason"]
    record.classification_confidence = classification["confidence"]
    record.analyte_detected = analyte_detected

    canonical_payload = build_canonical_payload(record)
    sig_hex, record_hash, key_id = sign_data(canonical_payload)

    # 8. Update Test Record in Database
    record.digital_signature = sig_hex
    record.canonical_record_hash = record_hash
    record.signing_key_id = key_id
    record.verification_status = VerificationStatus.VERIFIED.value

    # Store CV analysis result
    existing_analysis = db.query(ImageAnalysisResult).filter(ImageAnalysisResult.test_record_id == record.id).first()
    if existing_analysis:
        analysis_obj = existing_analysis
    else:
        analysis_obj = ImageAnalysisResult(test_record_id=record.id)
        db.add(analysis_obj)

    analysis_obj.blur_score = quality["blur_score"]
    analysis_obj.is_blurry = quality["is_blurry"]
    analysis_obj.illumination_score = quality["illumination_score"]
    analysis_obj.is_underexposed = quality["is_underexposed"]
    analysis_obj.is_overexposed = quality["is_overexposed"]
    analysis_obj.card_detected = calib.get("card_detected", calib["calibration_success"])
    analysis_obj.calibration_error_delta_e = calib["calibration_error_delta_e"]
    analysis_obj.reaction_cielab_l = measured_lab[0]
    analysis_obj.reaction_cielab_a = measured_lab[1]
    analysis_obj.reaction_cielab_b = measured_lab[2]
    analysis_obj.reaction_rgb_hex = calib["reaction_hex"]
    analysis_obj.positive_delta_e = classification["d_pos"]
    analysis_obj.negative_delta_e = classification["d_neg"]
    analysis_obj.quality_passed = quality["passed"]
    analysis_obj.quality_notes = quality["notes"]

    db.commit()
    db.refresh(record)

    # 9. Audit Logging
    log_audit_event(
        db,
        event_type="IMAGE_CAPTURED",
        user_id=current_user.id,
        user_name=current_user.username,
        related_record_id=record.test_id,
        details={
            "image_sha256": image_sha256,
            "byte_size": image_byte_size,
            "quality_passed": quality["passed"],
            "blur_score": quality["blur_score"],
            "calib_delta_e": calib["calibration_error_delta_e"]
        }
    )

    log_audit_event(
        db,
        event_type="RECORD_SIGNED",
        user_id=current_user.id,
        user_name=current_user.username,
        related_record_id=record.test_id,
        details={
            "classification": record.classification_result,
            "key_id": key_id,
            "signature_prefix": sig_hex[:16]
        }
    )

    return ImageAnalysisResponse(
        test_id=record.test_id,
        classification_result=record.classification_result,
        classification_reason=record.classification_reason or "",
        classification_confidence=record.classification_confidence or 0.0,
        analyte_detected=record.analyte_detected,
        disclaimer=STATUTORY_DISCLAIMER,
        quality=ImageQualityResponse(
            passed=quality["passed"],
            blur_score=quality["blur_score"],
            is_blurry=quality["is_blurry"],
            illumination_score=quality["illumination_score"],
            is_underexposed=quality["is_underexposed"],
            is_overexposed=quality["is_overexposed"],
            notes=quality["notes"]
        ),
        calibration_error_delta_e=calib["calibration_error_delta_e"],
        reaction_cielab=calib["reaction_cielab"],
        reaction_hex=calib["reaction_hex"],
        positive_delta_e=classification["d_pos"],
        negative_delta_e=classification["d_neg"],
        original_image_hash=image_sha256,
        digital_signature=sig_hex,
        signing_key_id=key_id
    )

@router.get("", response_model=List[TestRecordSummary])
def list_test_records(
    q: Optional[str] = None,
    classification: Optional[str] = None,
    kit_id: Optional[int] = None,
    verification_status: Optional[str] = None,
    sync_status: Optional[str] = None,
    page: int = 1,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(TestRecord)

    # Role-based restriction: Field officers can only see their own records if not supervisor/admin/auditor
    if current_user.role == UserRole.FIELD_OFFICER.value:
        query = query.filter(TestRecord.operator_id == current_user.id)

    if q:
        query = query.filter(
            or_(
                TestRecord.test_id.ilike(f"%{q}%"),
                TestRecord.case_reference.ilike(f"%{q}%"),
                TestRecord.operator_name.ilike(f"%{q}%"),
                TestRecord.kit_batch_number.ilike(f"%{q}%"),
                TestRecord.analyte_detected.ilike(f"%{q}%")
            )
        )

    if classification and classification != "ALL":
        query = query.filter(TestRecord.classification_result == classification)

    if kit_id:
        query = query.filter(TestRecord.kit_id == kit_id)

    if verification_status and verification_status != "ALL":
        query = query.filter(TestRecord.verification_status == verification_status)

    if sync_status and sync_status != "ALL":
        query = query.filter(TestRecord.sync_status == sync_status)

    query = query.order_by(desc(TestRecord.created_at))
    offset = (page - 1) * limit
    records = query.offset(offset).limit(limit).all()

    results = []
    for r in records:
        results.append(TestRecordSummary(
            id=r.id,
            test_id=r.test_id,
            case_reference=r.case_reference,
            operator_name=r.operator_name,
            operator_badge=r.operator_badge,
            kit_name=r.kit.name if r.kit else "Unknown Kit",
            kit_batch_number=r.kit_batch_number,
            analyte_detected=r.analyte_detected,
            classification_result=r.classification_result,
            verification_status=r.verification_status,
            sync_status=r.sync_status,
            original_image_hash=r.original_image_hash,
            device_timestamp=r.device_timestamp,
            server_timestamp=r.server_timestamp,
            has_gps=bool(r.gps_latitude and r.gps_longitude),
            created_at=r.created_at
        ))
    return results

@router.get("/{test_id}", response_model=TestRecordDetailResponse)
def get_test_record_detail(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.query(TestRecord).filter(TestRecord.test_id == test_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Test record not found.")

    if current_user.role == UserRole.FIELD_OFFICER.value and record.operator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to other officers' records.")

    log_audit_event(
        db,
        event_type="RECORD_ACCESSED",
        user_id=current_user.id,
        user_name=current_user.username,
        related_record_id=record.test_id,
        details={"viewer_role": current_user.role}
    )

    return format_test_detail(record)

def format_test_detail(record: TestRecord) -> TestRecordDetailResponse:
    analysis_dict = None
    if record.analysis:
        a = record.analysis
        analysis_dict = {
            "blur_score": a.blur_score,
            "is_blurry": a.is_blurry,
            "illumination_score": a.illumination_score,
            "is_underexposed": a.is_underexposed,
            "is_overexposed": a.is_overexposed,
            "card_detected": a.card_detected,
            "calibration_error_delta_e": a.calibration_error_delta_e,
            "reaction_cielab": {
                "L": a.reaction_cielab_l,
                "a": a.reaction_cielab_a,
                "b": a.reaction_cielab_b
            } if a.reaction_cielab_l is not None else None,
            "reaction_hex": a.reaction_rgb_hex,
            "positive_delta_e": a.positive_delta_e,
            "negative_delta_e": a.negative_delta_e,
            "quality_passed": a.quality_passed,
            "quality_notes": a.quality_notes
        }

    verifications_list = []
    for v in record.verifications:
        verifications_list.append({
            "id": v.id,
            "verifier_name": v.verifier_name,
            "hash_verified": v.hash_verified,
            "signature_verified": v.signature_verified,
            "details": v.details,
            "timestamp": v.timestamp.isoformat()
        })

    orig_url = f"/uploads/original/{Path(record.original_image_path).name}" if record.original_image_path else None
    proc_url = f"/uploads/processed/{Path(record.processed_image_path).name}" if record.processed_image_path else None

    return TestRecordDetailResponse(
        id=record.id,
        test_id=record.test_id,
        case_reference=record.case_reference,
        operator_id=record.operator_id,
        operator_name=record.operator_name,
        operator_badge=record.operator_badge,
        kit_id=record.kit_id,
        kit_name=record.kit.name if record.kit else "Unknown Kit",
        kit_manufacturer=record.kit.manufacturer if record.kit else "Unknown Mfg",
        kit_batch_number=record.kit_batch_number,
        kit_expiry_date=record.kit_expiry_date,
        notes=record.notes,
        classification_result=record.classification_result,
        classification_reason=record.classification_reason,
        classification_confidence=record.classification_confidence,
        analyte_detected=record.analyte_detected,
        algorithm_version=record.algorithm_version,
        profile_version=record.profile_version,
        gps_latitude=record.gps_latitude,
        gps_longitude=record.gps_longitude,
        gps_accuracy_meters=record.gps_accuracy_meters,
        location_unavailable_reason=record.location_unavailable_reason,
        device_timestamp=record.device_timestamp,
        server_timestamp=record.server_timestamp,
        original_image_url=orig_url,
        processed_image_url=proc_url,
        original_image_hash=record.original_image_hash,
        image_byte_size=record.image_byte_size,
        digital_signature=record.digital_signature,
        signature_algorithm=record.signature_algorithm,
        signing_key_id=record.signing_key_id,
        canonical_record_hash=record.canonical_record_hash,
        verification_status=record.verification_status,
        is_provisional=record.is_provisional,
        client_uuid=record.client_uuid,
        sync_status=record.sync_status,
        created_at=record.created_at,
        analysis=analysis_dict,
        verifications=verifications_list
    )

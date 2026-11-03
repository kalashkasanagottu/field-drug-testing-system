import os
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User, UserRole
from app.models.evidence import TestRecord, VerificationEvent, VerificationStatus
from app.schemas.evidence import VerificationRequest, VerificationResponse
from app.cryptography.hasher import compute_sha256
from app.core.security import verify_signature, get_public_key_hex, build_canonical_payload
from app.services.audit_service import log_audit_event
from app.api.deps import get_current_user

router = APIRouter(prefix="/evidence", tags=["Cryptographic Evidence & Tamper Detection"])

@router.post("/{test_id}/verify", response_model=VerificationResponse)
def verify_test_evidence(
    test_id: str,
    verify_req: VerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.query(TestRecord).filter(TestRecord.test_id == test_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Test record not found.")

    # 1. Independent SHA-256 Image Hash Verification
    hash_verified = True
    computed_hash = "UNAVAILABLE"
    hash_error = None

    if verify_req.check_image_tampering:
        if record.original_image_path and os.path.exists(record.original_image_path):
            with open(record.original_image_path, "rb") as f:
                disk_bytes = f.read()
            computed_hash = compute_sha256(disk_bytes)
            if computed_hash.lower() != (record.original_image_hash or "").lower():
                hash_verified = False
                hash_error = f"MISMATCH: Disk hash ({computed_hash}) != Sealed Record hash ({record.original_image_hash})"
        else:
            hash_verified = False
            hash_error = "Original image file missing from object storage repository."

    # 2. Independent Ed25519 Digital Signature Verification
    signature_verified = True
    sig_error = None

    if verify_req.check_digital_signature:
        if not record.digital_signature:
            signature_verified = False
            sig_error = "No digital signature attached to this evidence record."
        else:
            canonical_payload = build_canonical_payload(record)
            is_valid_sig = verify_signature(canonical_payload, record.digital_signature)
            if not is_valid_sig:
                signature_verified = False
                sig_error = "Digital signature cryptographic validation failed against active Ed25519 public key."

    # Final integrity determination
    all_passed = hash_verified and signature_verified
    new_status = VerificationStatus.VERIFIED.value if all_passed else VerificationStatus.INTEGRITY_FAILED.value
    record.verification_status = new_status

    details = "Cryptographic integrity verified successfully. No evidence tampering detected."
    if not all_passed:
        errors = [e for e in [hash_error, sig_error] if e]
        details = f"TAMPER ALERT: {'; '.join(errors)}"

    # Record verification event
    event = VerificationEvent(
        test_record_id=record.id,
        verifier_user_id=current_user.id,
        verifier_name=current_user.full_name,
        hash_verified=hash_verified,
        signature_verified=signature_verified,
        details=details,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(event)
    db.commit()

    # Log audit event
    log_audit_event(
        db,
        event_type="EVIDENCE_VERIFIED" if all_passed else "TAMPER_DETECTED",
        user_id=current_user.id,
        user_name=current_user.username,
        related_record_id=record.test_id,
        details={
            "hash_verified": hash_verified,
            "signature_verified": signature_verified,
            "status": new_status,
            "details": details
        }
    )

    return VerificationResponse(
        test_id=record.test_id,
        status=new_status,
        image_hash_verified=hash_verified,
        signature_verified=signature_verified,
        original_image_hash=record.original_image_hash or "NONE",
        computed_image_hash=computed_hash,
        signing_key_id=record.signing_key_id or "UNKNOWN",
        details=details,
        timestamp=datetime.now(timezone.utc)
    )

@router.post("/{test_id}/simulate-tampering")
def simulate_evidence_tampering(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Forensic demonstration helper: Flips bytes in the original evidence image to prove
    that the cryptographic verification pipeline instantly flags pixel-level alterations!
    """
    record = db.query(TestRecord).filter(TestRecord.test_id == test_id).first()
    if not record or not record.original_image_path or not os.path.exists(record.original_image_path):
        raise HTTPException(status_code=404, detail="Valid test record image not found to simulate tampering.")

    # Invert 16 bytes in the middle of the image file
    with open(record.original_image_path, "r+b") as f:
        f.seek(500)
        bytes_to_alter = f.read(16)
        altered_bytes = bytes([b ^ 0xFF for b in bytes_to_alter])
        f.seek(500)
        f.write(altered_bytes)

    log_audit_event(
        db,
        event_type="SIMULATED_TAMPERING_INJECTED",
        user_id=current_user.id,
        user_name=current_user.username,
        related_record_id=record.test_id,
        details={"action": "Modified 16 bytes in original image file to test tamper detection"}
    )

    return {
        "message": "Simulated tampering injected into image file bytes. Run 'Verify Evidence' now to observe immediate cryptographic failure!",
        "test_id": test_id
    }

@router.get("/public-key")
def get_public_verification_key():
    """Returns the Ed25519 public key hex for third-party judicial / defense audit verification."""
    return {
        "key_id": "KEY-FORENSIC-2026-V1",
        "algorithm": "Ed25519",
        "public_key_hex": get_public_key_hex()
    }

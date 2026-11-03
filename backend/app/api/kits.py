from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.test_kit import TestKit, TestKitProfile, CalibrationCard, ValidationStatus
from app.models.user import User, UserRole
from app.schemas.test_kit import (
    TestKitResponse, TestKitCreate, TestKitProfileResponse, TestKitProfileCreate, TestKitProfileBase, CalibrationCardResponse
)
from app.api.deps import get_current_user, require_roles
from app.services.audit_service import log_audit_event

router = APIRouter(prefix="/kits", tags=["Test Kits & Calibration Profiles"])

@router.get("", response_model=List[TestKitResponse])
def list_test_kits(db: Session = Depends(get_db)):
    kits = db.query(TestKit).filter(TestKit.is_active == True).all()
    return kits

@router.post("", response_model=TestKitResponse)
def create_test_kit(
    kit_in: TestKitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN.value]))
):
    existing = db.query(TestKit).filter(TestKit.name == kit_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Test kit with this name already exists.")

    new_kit = TestKit(**kit_in.model_dump())
    db.add(new_kit)
    db.commit()
    db.refresh(new_kit)

    log_audit_event(
        db,
        event_type="KIT_CREATED",
        user_id=current_user.id,
        user_name=current_user.username,
        related_record_id=f"KIT-{new_kit.id}",
        details={"name": new_kit.name, "analyte": new_kit.analyte}
    )

    return new_kit

@router.post("/{kit_id}/profiles", response_model=TestKitProfileResponse)
def create_kit_profile(
    kit_id: int,
    profile_in: TestKitProfileBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN.value]))
):
    kit = db.query(TestKit).filter(TestKit.id == kit_id).first()
    if not kit:
        raise HTTPException(status_code=404, detail="Test kit not found.")

    new_profile = TestKitProfile(
        kit_id=kit_id,
        **profile_in.model_dump()
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)

    log_audit_event(
        db,
        event_type="PROFILE_UPDATED",
        user_id=current_user.id,
        user_name=current_user.username,
        related_record_id=f"KIT-{kit_id}",
        details={"profile_version": new_profile.profile_version, "status": new_profile.validation_status}
    )

    return new_profile

@router.get("/{kit_id}/profiles", response_model=List[TestKitProfileResponse])
def list_kit_profiles(
    kit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    kit = db.query(TestKit).filter(TestKit.id == kit_id).first()
    if not kit:
        raise HTTPException(status_code=404, detail="Test kit not found.")
    profiles = db.query(TestKitProfile).filter(TestKitProfile.kit_id == kit_id).all()
    return profiles

@router.get("/calibration-cards", response_model=List[CalibrationCardResponse])
def list_calibration_cards(db: Session = Depends(get_db)):
    cards = db.query(CalibrationCard).filter(CalibrationCard.is_active == True).all()
    return cards

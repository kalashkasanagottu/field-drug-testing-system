import os
import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import SessionLocal, Base, engine
from app.models.user import User, UserRole, AuditLog
from app.models.test_kit import TestKit, TestKitProfile, CalibrationCard, ValidationStatus
from app.models.evidence import (
    TestRecord, ImageAnalysisResult, ClassificationResult, VerificationStatus, SyncStatus
)
from app.core.security import hash_password, sign_data, build_canonical_payload
from app.cryptography.hasher import compute_sha256
from app.computer_vision.color_calibration import detect_and_calibrate, REFERENCE_PATCHES, cielab_to_bgr_hex
from app.classification.engine import ClassificationEngine
from app.services.audit_service import log_audit_event

def create_synthetic_field_image(reaction_bgr: tuple, output_path: str) -> str:
    """
    Synthesizes a realistic 800x600 field test pouch image containing:
    - 6-patch reference color card on the left
    - Transparent test pouch with chemical reaction color in the center
    - Background texture with subtle lighting variance
    """
    img = np.ones((600, 800, 3), dtype=np.uint8) * 215  # Light gray desk background
    
    # Add subtle lighting gradient/shadow
    for y in range(600):
        factor = 1.0 - (y / 600.0) * 0.12
        img[y, :] = np.clip(img[y, :] * factor, 0, 255).astype(np.uint8)

    # Draw Reference Card (x: 40 to 220, y: 80 to 520)
    card_x1, card_y1, card_x2, card_y2 = 40, 80, 220, 520
    cv2.rectangle(img, (card_x1 - 5, card_y1 - 5), (card_x2 + 5, card_y2 + 5), (40, 40, 40), -1) # Black card border
    cv2.rectangle(img, (card_x1, card_y1), (card_x2, card_y2), (245, 245, 245), -1) # Card body

    patch_h = (card_y2 - card_y1) // 6
    for i, patch in enumerate(REFERENCE_PATCHES):
        py1 = card_y1 + i * patch_h + 8
        py2 = card_y1 + (i + 1) * patch_h - 8
        px1 = card_x1 + 15
        px2 = card_x2 - 15
        bgr = patch["ref_bgr"]
        cv2.rectangle(img, (px1, py1), (px2, py2), bgr, -1)
        cv2.rectangle(img, (px1, py1), (px2, py2), (100, 100, 100), 1)

    # Draw Chemical Testing Pouch (x: 300 to 740, y: 150 to 480)
    pouch_x1, pouch_y1, pouch_x2, pouch_y2 = 300, 150, 740, 480
    # Pouch outer seal
    cv2.rectangle(img, (pouch_x1, pouch_y1), (pouch_x2, pouch_y2), (180, 180, 180), 3)
    cv2.rectangle(img, (pouch_x1 + 8, pouch_y1 + 8), (pouch_x2 - 8, pouch_y2 - 8), (225, 225, 225), -1)

    # Inner reaction liquid ampoule / zone
    rx1, ry1, rx2, ry2 = pouch_x1 + 50, pouch_y1 + 50, pouch_x2 - 50, pouch_y2 - 50
    cv2.rectangle(img, (rx1, ry1), (rx2, ry2), reaction_bgr, -1)
    
    # Add glossy specular reflection line across pouch
    cv2.line(img, (pouch_x1 + 30, pouch_y1 + 40), (pouch_x2 - 30, pouch_y1 + 40), (255, 255, 255), 2)

    # Text markings on kit
    cv2.putText(img, "FORENSIC DRUG TESTING POUCH", (pouch_x1 + 30, pouch_y1 + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (70, 70, 70), 1, cv2.LINE_AA)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(output_path, img)
    return output_path

def seed_database():
    """Initializes tables, seeds administrative users, kits, profiles, and demo test records."""
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Seed Users
        users_data = [
            {
                "username": "admin",
                "email": "admin@forensic.gov",
                "password": "AdminPass123!",
                "full_name": "Dr. Sarah Lin",
                "badge_number": "DIR-01",
                "department": "Forensic Laboratory Director",
                "role": UserRole.ADMIN.value
            },
            {
                "username": "officer1",
                "email": "miller@police.gov",
                "password": "OfficerPass123!",
                "full_name": "Det. James Miller",
                "badge_number": "DET-8492",
                "department": "Narcotics Interdiction Taskforce",
                "role": UserRole.FIELD_OFFICER.value
            },
            {
                "username": "supervisor1",
                "email": "vance@police.gov",
                "password": "SupervisorPass123!",
                "full_name": "Lt. Robert Vance",
                "badge_number": "LT-2201",
                "department": "Field Operations Oversight",
                "role": UserRole.SUPERVISOR.value
            },
            {
                "username": "auditor1",
                "email": "rostova@justice.gov",
                "password": "AuditorPass123!",
                "full_name": "Inspector Elena Rostova",
                "badge_number": "AUD-104",
                "department": "Judicial Evidence Audit Division",
                "role": UserRole.AUDITOR.value
            }
        ]

        created_users = {}
        for u in users_data:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if not existing:
                user = User(
                    username=u["username"],
                    email=u["email"],
                    hashed_password=hash_password(u["password"]),
                    full_name=u["full_name"],
                    badge_number=u["badge_number"],
                    department=u["department"],
                    role=u["role"],
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                created_users[u["username"]] = user
            else:
                created_users[u["username"]] = existing

        # 2. Seed Reference Calibration Card
        existing_card = db.query(CalibrationCard).filter(CalibrationCard.name == "FORENSIC-CARD-6PATCH-V1").first()
        if not existing_card:
            card = CalibrationCard(
                name="FORENSIC-CARD-6PATCH-V1",
                card_type="STANDARD_6_PATCH",
                layout_json=json.dumps(REFERENCE_PATCHES),
                is_active=True
            )
            db.add(card)
            db.commit()

        # 3. Seed Test Kits and Validated Profiles
        kits_data = [
            {
                "name": "Scott Reagent (Cobalt Thiocyanate)",
                "manufacturer": "ForensicTech Reagents Ltd.",
                "model_number": "SC-COC-300",
                "analyte": "Cocaine Hydrochloride / Base",
                "reaction_time_seconds": 45,
                "instructions": "Place 2-5mg test sample into pouch ampoule A, crush and shake. Observe turquoise-blue precipitate.",
                "profile": {
                    "version": "V1.4",
                    "status": ValidationStatus.APPROVED.value,
                    "ref_source": "SWGDRUG Validation Protocol & Forensic Tech Lab Spec 2025",
                    "approval_details": "Approved by Forensic Standards Board FSB-2025-08",
                    "pos_lab": (46.2, -22.5, -42.0), # Deep turquoise blue
                    "pos_thresh": 18.0,
                    "neg_lab": (76.0, 14.0, 6.0),    # Pinkish / clear
                    "neg_thresh": 16.0,
                    "inconc_thresh": 7.0,
                    "roi": (0.38, 0.25, 0.54, 0.50)
                }
            },
            {
                "name": "Marquis Reagent",
                "manufacturer": "NarcCheck Forensics",
                "model_number": "MQ-OPI-100",
                "analyte": "Opiates (Heroin, Morphine, Codeine)",
                "reaction_time_seconds": 60,
                "instructions": "Introduce suspected powder into Marquis ampoule. Rapid purple/violet reaction indicates opiate alkaloid.",
                "profile": {
                    "version": "V2.1",
                    "status": ValidationStatus.APPROVED.value,
                    "ref_source": "National Forensic Science Registry Benchmark #884",
                    "approval_details": "Approved by Forensic Standards Board FSB-2025-11",
                    "pos_lab": (24.0, 26.5, -22.0), # Deep purple/violet
                    "pos_thresh": 18.0,
                    "neg_lab": (64.0, -1.5, 27.0),   # Amber-yellow unreacted / negative
                    "neg_thresh": 16.0,
                    "inconc_thresh": 7.0,
                    "roi": (0.38, 0.25, 0.54, 0.50)
                }
            },
            {
                "name": "Ehrlich's Reagent (p-DMAB)",
                "manufacturer": "ForensicTech Reagents Ltd.",
                "model_number": "EH-LSD-200",
                "analyte": "LSD / Indole Alkaloids",
                "reaction_time_seconds": 90,
                "instructions": "Add suspected blotter or liquid. Formation of deep violet-blue ring confirms indole ring structure.",
                "profile": {
                    "version": "V1.2",
                    "status": ValidationStatus.APPROVED.value,
                    "ref_source": "European ENFSI Drug Testing Monograph #14",
                    "approval_details": "Approved by Forensic Standards Board FSB-2025-12",
                    "pos_lab": (32.0, 31.0, -16.5),
                    "pos_thresh": 18.0,
                    "neg_lab": (78.0, -1.5, 18.0),
                    "neg_thresh": 16.0,
                    "inconc_thresh": 7.0,
                    "roi": (0.38, 0.25, 0.54, 0.50)
                }
            },
            {
                "name": "Duquenois-Levine Test",
                "manufacturer": "SafeField Forensics",
                "model_number": "DL-THC-400",
                "analyte": "Cannabis / Delta-9-THC",
                "reaction_time_seconds": 60,
                "instructions": "Add plant material. Add Reagent A & B, then chloroform C. Violet extraction into bottom chloroform layer indicates cannabinoid.",
                "profile": {
                    "version": "V1.0",
                    "status": ValidationStatus.APPROVED.value,
                    "ref_source": "UNODC Recommended Methods for Cannabis Testing",
                    "approval_details": "Approved by Forensic Standards Board FSB-2026-01",
                    "pos_lab": (30.5, 24.0, -20.0),
                    "pos_thresh": 18.0,
                    "neg_lab": (70.0, -15.0, 30.0),
                    "neg_thresh": 16.0,
                    "inconc_thresh": 7.0,
                    "roi": (0.38, 0.25, 0.54, 0.50)
                }
            },
            {
                "name": "Synthetic Demonstration Kit (Simulation Only)",
                "manufacturer": "Training Simulations Corp",
                "model_number": "SIM-DEV-99",
                "analyte": "Demonstration Analytes",
                "reaction_time_seconds": 30,
                "instructions": "FOR TRAINING ONLY. Not for real evidence prosecution.",
                "profile": {
                    "version": "V0.9-SIM",
                    "status": ValidationStatus.SIMULATION_ONLY.value,
                    "ref_source": "Simulation Sandbox Reference Data",
                    "approval_details": "SIMULATION ONLY - NOT VALIDATED FOR COURT EVIDENCE",
                    "pos_lab": (50.0, 30.0, 30.0),
                    "pos_thresh": 20.0,
                    "neg_lab": (80.0, 0.0, 0.0),
                    "neg_thresh": 20.0,
                    "inconc_thresh": 8.0,
                    "roi": (0.38, 0.25, 0.54, 0.50)
                }
            }
        ]

        created_kits = {}
        for kd in kits_data:
            kit = db.query(TestKit).filter(TestKit.name == kd["name"]).first()
            if not kit:
                kit = TestKit(
                    name=kd["name"],
                    manufacturer=kd["manufacturer"],
                    model_number=kd["model_number"],
                    analyte=kd["analyte"],
                    reaction_time_seconds=kd["reaction_time_seconds"],
                    instructions=kd["instructions"],
                    is_active=True
                )
                db.add(kit)
                db.commit()
                db.refresh(kit)

                # Add profile
                prof_data = kd["profile"]
                profile = TestKitProfile(
                    kit_id=kit.id,
                    profile_version=prof_data["version"],
                    validation_status=prof_data["status"],
                    reference_source=prof_data["ref_source"],
                    approval_details=prof_data["approval_details"],
                    positive_cielab_l=prof_data["pos_lab"][0],
                    positive_cielab_a=prof_data["pos_lab"][1],
                    positive_cielab_b=prof_data["pos_lab"][2],
                    positive_delta_e_threshold=prof_data["pos_thresh"],
                    negative_cielab_l=prof_data["neg_lab"][0],
                    negative_cielab_a=prof_data["neg_lab"][1],
                    negative_cielab_b=prof_data["neg_lab"][2],
                    negative_delta_e_threshold=prof_data["neg_thresh"],
                    inconclusive_delta_e_threshold=prof_data["inconc_thresh"],
                    reaction_roi_x=prof_data["roi"][0],
                    reaction_roi_y=prof_data["roi"][1],
                    reaction_roi_w=prof_data["roi"][2],
                    reaction_roi_h=prof_data["roi"][3]
                )
                db.add(profile)
                db.commit()
            created_kits[kd["name"]] = kit

        # 4. Seed Demonstrative Test Records if database is empty of tests
        if db.query(TestRecord).count() == 0:
            officer = created_users["officer1"]
            scott_kit = created_kits["Scott Reagent (Cobalt Thiocyanate)"]
            marquis_kit = created_kits["Marquis Reagent"]
            
            demo_cases = [
                {
                    "test_id": "DT-20261102-C7E1",
                    "case_ref": "CASE-2026-0941",
                    "kit": scott_kit,
                    "batch": "LOT-2025-SC-881",
                    "expiry": "2027-06-30",
                    "notes": "Field interdiction at Highway checkpoint 4. White powdery substance packaged in clear zip bag.",
                    "reaction_bgr": (195, 120, 20), # Turquoise-blue (Scott Positive)
                    "gps": (37.7749, -122.4194, 4.2),
                    "days_ago": 2
                },
                {
                    "test_id": "DT-20261101-A482",
                    "case_ref": "CASE-2026-0938",
                    "kit": marquis_kit,
                    "batch": "LOT-2025-MQ-419",
                    "expiry": "2027-08-15",
                    "notes": "Suspected brown granular material seized during port container inspection.",
                    "reaction_bgr": (120, 30, 85), # Violet-purple (Marquis Positive Opiates)
                    "gps": (37.7833, -122.4167, 3.8),
                    "days_ago": 3
                },
                {
                    "test_id": "DT-20261029-F910",
                    "case_ref": "CASE-2026-0925",
                    "kit": scott_kit,
                    "batch": "LOT-2025-SC-881",
                    "expiry": "2027-06-30",
                    "notes": "White crystalline substance tested; no blue reaction observed, remained light pink.",
                    "reaction_bgr": (180, 160, 210), # Pinkish negative
                    "gps": (37.7650, -122.4200, 5.0),
                    "days_ago": 6
                },
                {
                    "test_id": "DT-20261026-B331",
                    "case_ref": "CASE-2026-0914",
                    "kit": marquis_kit,
                    "batch": "LOT-2025-MQ-419",
                    "expiry": "2027-08-15",
                    "notes": "Substance with heavy adulterants produced ambiguous grey-brown hue.",
                    "reaction_bgr": (110, 110, 120), # Ambiguous / Inconclusive
                    "gps": (37.7500, -122.4100, 8.5),
                    "days_ago": 9
                }
            ]

            for case in demo_cases:
                kit_obj = case["kit"]
                prof_obj = db.query(TestKitProfile).filter(TestKitProfile.kit_id == kit_obj.id).first()
                
                now_utc = datetime.now(timezone.utc)
                record_time = now_utc - timedelta(days=case["days_ago"], hours=3)
                
                # Create synthetic image file
                orig_file = f"{case['test_id']}_orig.jpg"
                orig_path = str(Path(settings.UPLOAD_PATH) / "original" / orig_file)
                create_synthetic_field_image(case["reaction_bgr"], orig_path)

                with open(orig_path, "rb") as f:
                    raw_bytes = f.read()

                sha256_hash = compute_sha256(raw_bytes)
                byte_size = len(raw_bytes)

                # Run CV calibration
                img_bgr = cv2.imread(orig_path)
                quality = {"passed": True, "blur_score": 142.5, "is_blurry": False, "illumination_score": 115.0, "is_underexposed": False, "is_overexposed": False, "notes": "Quality passed"}
                calib = detect_and_calibrate(img_bgr, reaction_roi={"x": 0.38, "y": 0.25, "w": 0.54, "h": 0.50})

                proc_file = f"{case['test_id']}_proc.jpg"
                proc_path = str(Path(settings.UPLOAD_PATH) / "processed" / proc_file)
                cv2.imwrite(proc_path, calib["annotated_image_bgr"])

                measured_lab = (calib["reaction_cielab"]["L"], calib["reaction_cielab"]["a"], calib["reaction_cielab"]["b"])
                classification = ClassificationEngine.classify_reaction(
                    measured_lab=measured_lab,
                    kit_profile=prof_obj,
                    quality_assessment=quality,
                    calibration_assessment=calib
                )

                analyte_detected = kit_obj.analyte if classification["result"] == ClassificationResult.PRESUMPTIVE_POSITIVE.value else None

                record = TestRecord(
                    test_id=case["test_id"],
                    case_reference=case["case_ref"],
                    operator_id=officer.id,
                    operator_name=officer.full_name,
                    operator_badge=officer.badge_number,
                    kit_id=kit_obj.id,
                    kit_profile_id=prof_obj.id,
                    kit_batch_number=case["batch"],
                    kit_expiry_date=case["expiry"],
                    notes=case["notes"],
                    classification_result=classification["result"],
                    classification_reason=classification["reason"],
                    classification_confidence=classification["confidence"],
                    analyte_detected=analyte_detected,
                    algorithm_version=settings.ALGORITHM_VERSION,
                    profile_version=prof_obj.profile_version,
                    gps_latitude=case["gps"][0],
                    gps_longitude=case["gps"][1],
                    gps_accuracy_meters=case["gps"][2],
                    device_timestamp=record_time,
                    server_timestamp=record_time,
                    original_image_path=orig_path,
                    processed_image_path=proc_path,
                    original_image_hash=sha256_hash,
                    image_byte_size=byte_size,
                    signature_algorithm="Ed25519",
                    verification_status=VerificationStatus.VERIFIED.value,
                    is_provisional=False,
                    sync_status=SyncStatus.SYNCHRONIZED.value,
                    created_at=record_time
                )

                canonical_payload = build_canonical_payload(record)
                sig_hex, rec_hash, key_id = sign_data(canonical_payload)
                record.digital_signature = sig_hex
                record.canonical_record_hash = rec_hash
                record.signing_key_id = key_id
                db.add(record)
                db.commit()
                db.refresh(record)

                analysis = ImageAnalysisResult(
                    test_record_id=record.id,
                    blur_score=quality["blur_score"],
                    is_blurry=False,
                    illumination_score=quality["illumination_score"],
                    is_underexposed=False,
                    is_overexposed=False,
                    card_detected=True,
                    calibration_error_delta_e=calib["calibration_error_delta_e"],
                    reaction_cielab_l=measured_lab[0],
                    reaction_cielab_a=measured_lab[1],
                    reaction_cielab_b=measured_lab[2],
                    reaction_rgb_hex=calib["reaction_hex"],
                    positive_delta_e=classification["d_pos"],
                    negative_delta_e=classification["d_neg"],
                    quality_passed=True,
                    quality_notes=quality["notes"]
                )
                db.add(analysis)
                db.commit()

                log_audit_event(
                    db,
                    event_type="TEST_RECORD_CREATED",
                    user_id=officer.id,
                    user_name=officer.username,
                    related_record_id=record.test_id,
                    details={"seed": True, "result": record.classification_result}
                )

        print("Database initialized and seeded successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

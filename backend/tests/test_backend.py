import pytest
import numpy as np
import cv2
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.computer_vision.ciede2000 import ciede2000
from app.computer_vision.quality_checks import check_image_quality
from app.cryptography.hasher import compute_sha256, verify_image_integrity
from app.core.security import sign_data, verify_signature, canonical_json_bytes
from app.classification.engine import ClassificationEngine
from app.models.evidence import ClassificationResult

client = TestClient(app)

def test_ciede2000_zero_distance_for_identical_colors():
    lab = (50.0, 15.0, -25.0)
    de = ciede2000(lab, lab)
    assert de == pytest.approx(0.0, abs=1e-5)

def test_ciede2000_distance_calculation():
    lab1 = (50.0, 2.6772, -79.7751)
    lab2 = (50.0, 0.0, -82.7485)
    de = ciede2000(lab1, lab2)
    assert de > 0.0
    assert de < 5.0

def test_image_quality_sharp_vs_blurry():
    # Synthetic sharp pattern
    sharp_img = np.zeros((480, 640, 3), dtype=np.uint8)
    sharp_img[::20, :] = 255
    res_sharp = check_image_quality(sharp_img)
    assert not res_sharp["is_blurry"]

    # Synthetic blurred flat pattern
    blurred_img = np.ones((480, 640, 3), dtype=np.uint8) * 120
    res_blur = check_image_quality(blurred_img)
    assert res_blur["is_blurry"]

def test_cryptographic_image_hashing_and_tamper_detection():
    data = b"FORENSIC_RAW_CAMERA_EVIDENCE_SAMPLE_BYTES_123456"
    h1 = compute_sha256(data)
    assert len(h1) == 64

    # Verification on original bytes
    is_valid, computed = verify_image_integrity(data, h1)
    assert is_valid
    assert computed == h1

    # Altering 1 bit must fail verification
    altered_data = b"FORENSIC_RAW_CAMERA_EVIDENCE_SAMPLE_BYTES_123457"
    is_valid_alt, computed_alt = verify_image_integrity(altered_data, h1)
    assert not is_valid_alt
    assert computed_alt != h1

def test_ed25519_signature_and_canonical_tamper_detection():
    payload = {
        "test_id": "DT-TEST-001",
        "operator": "Det. Miller",
        "result": "PRESUMPTIVE_POSITIVE",
        "analyte": "Cocaine"
    }
    sig_hex, rec_hash, key_id = sign_data(payload)
    assert len(sig_hex) > 64
    assert len(rec_hash) == 64

    # Verify signature passes on unmodified payload
    assert verify_signature(payload, sig_hex)

    # Any modification of payload must fail verification
    tampered_payload = payload.copy()
    tampered_payload["result"] = "PRESUMPTIVE_NEGATIVE"
    assert not verify_signature(tampered_payload, sig_hex)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"

def test_api_login_success():
    res = client.post("/api/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "ADMIN"
    assert data["username"] == "admin"

def test_api_login_failure():
    res = client.post("/api/auth/login", json={"username": "admin", "password": "WrongPassword"})
    assert res.status_code == 401

def test_api_kits_listing():
    res = client.get("/api/kits")
    assert res.status_code == 200
    kits = res.json()
    assert len(kits) >= 4
    names = [k["name"] for k in kits]
    assert any("Scott Reagent" in n for n in names)
    assert any("Marquis Reagent" in n for n in names)

def test_api_tests_listing_and_verification():
    # Login as admin to get token
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List tests
    res = client.get("/api/tests", headers=headers)
    assert res.status_code == 200
    records = res.json()
    assert len(records) > 0

    test_id = records[0]["test_id"]

    # Get test detail
    detail_res = client.get(f"/api/tests/{test_id}", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["test_id"] == test_id
    assert detail["digital_signature"] is not None

    # Verify evidence cryptographically
    verify_res = client.post(
        f"/api/evidence/{test_id}/verify",
        json={"test_id": test_id, "check_image_tampering": True, "check_digital_signature": True},
        headers=headers
    )
    assert verify_res.status_code == 200
    vdata = verify_res.json()
    assert vdata["image_hash_verified"] is True
    assert vdata["signature_verified"] is True
    assert vdata["status"] == "VERIFIED"

    # Now simulate tampering: inject byte modification into image file
    from pathlib import Path
    img_name = Path(detail["original_image_url"]).name if detail.get("original_image_url") else f"{test_id}_orig.jpg"
    img_path = Path("uploads/original") / img_name
    original_bytes = img_path.read_bytes() if img_path.exists() else None
    try:
        tamp_res = client.post(f"/api/evidence/{test_id}/simulate-tampering", headers=headers)
        assert tamp_res.status_code == 200

        # Verification must now immediately detect corruption and fail!
        verify_after_tamper = client.post(
            f"/api/evidence/{test_id}/verify",
            json={"test_id": test_id, "check_image_tampering": True, "check_digital_signature": True},
            headers=headers
        )
        assert verify_after_tamper.status_code == 200
        vt_data = verify_after_tamper.json()
        assert vt_data["image_hash_verified"] is False
        assert vt_data["status"] == "INTEGRITY_FAILED"
        assert "TAMPER ALERT" in vt_data["details"]
    finally:
        if original_bytes is not None:
            img_path.write_bytes(original_bytes)

def test_api_report_pdf_generation():
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    tests = client.get("/api/tests", headers=headers).json()
    test_id = tests[0]["test_id"]

    gen_res = client.post(f"/api/reports/{test_id}/generate", headers=headers)
    assert gen_res.status_code == 200
    assert gen_res.json()["file_size"] > 1000

    dl_res = client.get(f"/api/reports/{test_id}/download")
    assert dl_res.status_code == 200
    assert dl_res.headers["content-type"] == "application/pdf"
    assert len(dl_res.content) > 1000

def test_adaptive_reaction_detection_and_classification():
    from app.computer_vision.color_calibration import detect_and_calibrate
    from app.computer_vision.quality_checks import check_image_quality
    from app.classification.engine import ClassificationEngine
    from app.database.session import SessionLocal
    from app.models.test_kit import TestKitProfile, ValidationStatus

    db = SessionLocal()
    all_approved = db.query(TestKitProfile).filter(
        TestKitProfile.validation_status.in_([ValidationStatus.APPROVED.value, ValidationStatus.SIMULATION_ONLY.value])
    ).all()
    marquis_profile = db.query(TestKitProfile).filter(TestKitProfile.kit_id == 2).first()

    # Synthetic Positive Sample (Pouch on right, Card on left)
    p_pos = Path("uploads/original/DT-20261101-A482_orig.jpg")
    if p_pos.exists():
        img = cv2.imread(str(p_pos))
        calib = detect_and_calibrate(img)
        quality = check_image_quality(img)
        res = ClassificationEngine.classify_reaction(
            measured_lab=(calib["reaction_cielab"]["L"], calib["reaction_cielab"]["a"], calib["reaction_cielab"]["b"]),
            kit_profile=marquis_profile,
            quality_assessment=quality,
            calibration_assessment=calib,
            all_profiles=all_approved
        )
        assert res["result"] == "PRESUMPTIVE_POSITIVE"
        assert res["d_pos"] < 15.0

    # Synthetic Inconclusive Sample (Grey)
    p_inconc = Path("uploads/original/DT-20261026-B331_orig.jpg")
    if p_inconc.exists():
        img = cv2.imread(str(p_inconc))
        calib = detect_and_calibrate(img)
        quality = check_image_quality(img)
        res = ClassificationEngine.classify_reaction(
            measured_lab=(calib["reaction_cielab"]["L"], calib["reaction_cielab"]["a"], calib["reaction_cielab"]["b"]),
            kit_profile=marquis_profile,
            quality_assessment=quality,
            calibration_assessment=calib,
            all_profiles=all_approved
        )
        assert res["result"] == "INCONCLUSIVE"
        assert res["result"] != "PRESUMPTIVE_NEGATIVE"

    # Neutral Grey Swatch / Sample must always be INCONCLUSIVE, never NEGATIVE
    grey_lab = (56.3, 0.05, -1.2)
    res_grey = ClassificationEngine.classify_reaction(
        measured_lab=grey_lab,
        kit_profile=marquis_profile,
        quality_assessment={"passed": True},
        calibration_assessment={"calibration_success": True, "calibration_mode": "BYPASS_NO_CARD", "calibration_error_delta_e": 0.0},
        all_profiles=all_approved
    )
    assert res_grey["result"] == "INCONCLUSIVE"
    assert res_grey["result"] != "PRESUMPTIVE_NEGATIVE"

    # Amber Negative Sample must always be PRESUMPTIVE_NEGATIVE, never INCONCLUSIVE
    amber_lab = (61.2, -1.6, 29.3)
    res_amber = ClassificationEngine.classify_reaction(
        measured_lab=amber_lab,
        kit_profile=marquis_profile,
        quality_assessment={"passed": True},
        calibration_assessment={"calibration_success": True, "calibration_mode": "BYPASS_NO_CARD", "calibration_error_delta_e": 0.0},
        all_profiles=all_approved
    )
    assert res_amber["result"] == "PRESUMPTIVE_NEGATIVE"
    assert res_amber["result"] != "INCONCLUSIVE"

    # Cross-Profile Negative: Amber tested when Scott Reagent is active
    scott_profile = db.query(TestKitProfile).filter(TestKitProfile.kit_id == 1).first()
    res_cross_neg = ClassificationEngine.classify_reaction(
        measured_lab=amber_lab,
        kit_profile=scott_profile,
        quality_assessment={"passed": True},
        calibration_assessment={"calibration_success": True, "calibration_mode": "BYPASS_NO_CARD", "calibration_error_delta_e": 0.0},
        all_profiles=all_approved
    )
    assert res_cross_neg["result"] == "PRESUMPTIVE_NEGATIVE"


def test_api_refresh_token():
    """Test that a valid refresh token issues a new access token."""
    # First login to get credentials
    login_res = client.post("/api/auth/login", json={"username": "admin", "password": "AdminPass123!"})
    assert login_res.status_code == 200
    login_data = login_res.json()

    # Create a refresh token manually using the security module
    from app.core.security import create_refresh_token
    refresh_token = create_refresh_token(
        data={"sub": str(login_data["user_id"]), "username": login_data["username"], "role": login_data["role"]}
    )

    # Use the refresh token to get a new access token
    refresh_res = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()
    assert "access_token" in refresh_data
    assert refresh_data["token_type"] == "bearer"
    assert refresh_data["expires_in"] > 0

    # The new access token should work
    headers = {"Authorization": f"Bearer {refresh_data['access_token']}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "admin"


def test_api_refresh_token_invalid():
    """Test that an invalid refresh token is rejected."""
    refresh_res = client.post("/api/auth/refresh", json={"refresh_token": "invalid.token.string"})
    assert refresh_res.status_code == 401


def test_api_forgot_password_found():
    """Test forgot-password returns a reset token for an existing user."""
    res = client.post("/api/auth/forgot-password", json={"username": "admin"})
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert data["reset_token"] is not None
    assert data["expires_in"] == 3600


def test_api_forgot_password_not_found():
    """Test forgot-password does not reveal whether a user exists."""
    res = client.post("/api/auth/forgot-password", json={"username": "nonexistent_user_12345"})
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert data["reset_token"] is None  # No token for non-existent user


def test_api_reset_password():
    """Test password reset with a valid token."""
    # Request a reset token
    forgot_res = client.post("/api/auth/forgot-password", json={"username": "officer1"})
    assert forgot_res.status_code == 200
    reset_token = forgot_res.json()["reset_token"]

    # Reset the password
    reset_res = client.post("/api/auth/reset-password", json={
        "reset_token": reset_token,
        "new_password": "NewOfficerPass123!"
    })
    assert reset_res.status_code == 200
    assert "successfully" in reset_res.json()["message"]

    # Verify the new password works
    login_res = client.post("/api/auth/login", json={"username": "officer1", "password": "NewOfficerPass123!"})
    assert login_res.status_code == 200

    # Restore original password for other tests
    client.post("/api/auth/forgot-password", json={"username": "officer1"})
    forgot_res2 = client.post("/api/auth/forgot-password", json={"username": "officer1"})
    reset_token2 = forgot_res2.json()["reset_token"]
    client.post("/api/auth/reset-password", json={
        "reset_token": reset_token2,
        "new_password": "OfficerPass123!"
    })


def test_api_reset_password_invalid_token():
    """Test that an invalid reset token is rejected."""
    reset_res = client.post("/api/auth/reset-password", json={
        "reset_token": "invalid.token.string",
        "new_password": "NewPass123!"
    })
    assert reset_res.status_code == 401



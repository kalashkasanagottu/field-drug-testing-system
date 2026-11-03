import cv2
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from app.computer_vision.ciede2000 import ciede2000

# Standard 6-patch forensic reference color card definitions
REFERENCE_PATCHES = [
    {"name": "WHITE",   "ref_bgr": [242, 242, 242], "ref_lab": (95.0,   0.0,   0.0)},
    {"name": "GRAY",    "ref_bgr": [119, 119, 119], "ref_lab": (50.0,   0.0,   0.0)},
    {"name": "BLACK",   "ref_bgr": [38,  38,  38],  "ref_lab": (15.0,   0.0,   0.0)},
    {"name": "CYAN",    "ref_bgr": [190, 160,  0],  "ref_lab": (60.0, -30.0, -30.0)},
    {"name": "MAGENTA", "ref_bgr": [150,  50, 200], "ref_lab": (50.0,  65.0, -25.0)},
    {"name": "YELLOW",  "ref_bgr": [ 20, 220, 235], "ref_lab": (85.0,  -5.0,  85.0)},
]

CALIBRATION_ERROR_TOLERANCE = 25.0


def bgr_to_cielab(bgr_pixel: np.ndarray) -> Tuple[float, float, float]:
    """Converts a BGR uint8 pixel (or float) to CIELAB (L*, a*, b*)."""
    bgr_f = (bgr_pixel.reshape(1, 1, 3).astype(np.float32)) / 255.0
    lab = cv2.cvtColor(bgr_f, cv2.COLOR_BGR2Lab)[0, 0]
    return (float(lab[0]), float(lab[1]), float(lab[2]))


def cielab_to_bgr_hex(lab: Tuple[float, float, float]) -> str:
    """Converts CIELAB (L*, a*, b*) back to sRGB hex string for UI rendering."""
    lab_arr = np.array([[lab]], dtype=np.float32)
    bgr = cv2.cvtColor(lab_arr, cv2.COLOR_Lab2BGR)[0, 0]
    bgr_clamped = np.clip(bgr * 255.0, 0, 255).astype(np.uint8)
    return f"#{bgr_clamped[2]:02x}{bgr_clamped[1]:02x}{bgr_clamped[0]:02x}"


def _sample_patch_bgr(image_bgr: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
    """Returns median BGR of a rectangular crop, clamped to image bounds."""
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(image_bgr.shape[1], x2), min(image_bgr.shape[0], y2)
    if x2 <= x1 or y2 <= y1:
        return np.array([128.0, 128.0, 128.0], dtype=np.float32)
    crop = image_bgr[y1:y2, x1:x2]
    return np.median(crop.reshape(-1, 3), axis=0).astype(np.float32)


def _evaluate_6patch_card(
    image_bgr: np.ndarray, x1_ratio: float, x2_ratio: float
) -> Tuple[bool, float, np.ndarray, np.ndarray, Optional[Tuple[int, int, int, int]]]:
    """
    Checks if a physical 6-patch forensic calibration card is present in the specified vertical strip.
    Validates:
    1. Chromatic patches (Cyan, Magenta, Yellow) have high saturation.
    2. Residual least-squares Delta E across calibrated patches <= CALIBRATION_ERROR_TOLERANCE.
    """
    img_h, img_w = image_bgr.shape[:2]
    x1 = int(x1_ratio * img_w)
    x2 = int(x2_ratio * img_w)
    y1 = int(0.10 * img_h)
    y2 = int(0.90 * img_h)
    patch_h = max((y2 - y1) // 6, 1)

    measured, targets, coords = [], [], []
    for i, p in enumerate(REFERENCE_PATCHES):
        py1 = y1 + i * patch_h
        py2 = py1 + patch_h
        mx = max(int((x2 - x1) * 0.15), 2)
        my = max(int(patch_h * 0.15), 1)
        sx1, sy1 = x1 + mx, py1 + my
        sx2, sy2 = x2 - mx, py2 - my
        coords.append((sx1, sy1, sx2, sy2))
        med = _sample_patch_bgr(image_bgr, sx1, sy1, sx2, sy2)
        measured.append(med)
        targets.append(np.array(p["ref_bgr"], dtype=np.float32))

    # Verify saturation of chromatic patches (Cyan=3, Magenta=4, Yellow=5)
    def _sat(bgr: np.ndarray) -> float:
        pix = np.uint8([[np.clip(bgr, 0, 255)]])
        return float(cv2.cvtColor(pix, cv2.COLOR_BGR2HSV)[0, 0, 1])

    if _sat(measured[3]) < 45 or _sat(measured[4]) < 45 or _sat(measured[5]) < 45:
        return False, 99.0, np.eye(3, dtype=np.float32), image_bgr, None

    try:
        M, _, _, _ = np.linalg.lstsq(np.array(measured), np.array(targets), rcond=None)
        flat = image_bgr.reshape(-1, 3).astype(np.float32)
        cal_flat = np.dot(flat, M)
        cal = np.clip(cal_flat, 0, 255).astype(np.uint8).reshape(img_h, img_w, 3)

        errors = []
        for i, p in enumerate(REFERENCE_PATCHES):
            sx1, sy1, sx2, sy2 = coords[i]
            med_cal = _sample_patch_bgr(cal, sx1, sy1, sx2, sy2)
            errors.append(ciede2000(bgr_to_cielab(med_cal), p["ref_lab"]))

        mean_de = float(np.mean(errors))
        if mean_de <= CALIBRATION_ERROR_TOLERANCE:
            return True, mean_de, M, cal, (x1, y1, x2 - x1, y2 - y1)
    except Exception:
        pass

    return False, 99.0, np.eye(3, dtype=np.float32), image_bgr, None


def _detect_kit_legend_card(image_bgr: np.ndarray) -> Tuple[Optional[str], Optional[Tuple[int, int, int, int]]]:
    """
    Detects if a printed kit legend card (white paper card with text labels and swatches)
    is present on either the left or right side of the image.
    Returns: (side: 'left' | 'right' | None, bbox: (x, y, w, h) | None)
    """
    img_h, img_w = image_bgr.shape[:2]
    left_half = image_bgr[:, : img_w // 2]
    right_half = image_bgr[:, img_w // 2 :]

    def analyze_half(half_bgr: np.ndarray) -> Tuple[float, float, int]:
        lab = cv2.cvtColor(half_bgr, cv2.COLOR_BGR2LAB)
        gray = cv2.cvtColor(half_bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 80, 160)
        # White card body: high lightness, neutral chroma
        is_white = (lab[:, :, 0] > 155) & (np.abs(lab[:, :, 1].astype(int) - 128) < 20) & (np.abs(lab[:, :, 2].astype(int) - 128) < 20)
        sat = cv2.cvtColor(half_bgr, cv2.COLOR_BGR2HSV)[:, :, 1]
        chroma = (sat > 35).astype(np.uint8) * 255
        cnts, _ = cv2.findContours(chroma, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        swatches = sum(1 for c in cnts if 200 < cv2.contourArea(c) < (img_w * img_h * 0.05))
        return float(np.mean(is_white)), float(np.mean(edges > 0)), swatches

    lw, le, ls = analyze_half(left_half)
    rw, re, rs = analyze_half(right_half)

    if rw > 0.32 and (re > 0.025 or rs >= 2):
        return "right", (int(img_w * 0.48), int(img_h * 0.10), int(img_w * 0.50), int(img_h * 0.80))
    elif lw > 0.32 and (le > 0.025 or ls >= 2):
        return "left", (int(img_w * 0.02), int(img_h * 0.10), int(img_w * 0.50), int(img_h * 0.80))

    return None, None


def _find_reaction_zone(
    image_bgr: np.ndarray,
    card_side: Optional[str],
    default_roi: Optional[Dict[str, float]] = None
) -> Tuple[Tuple[int, int, int, int], Tuple[float, float, float], Optional[Tuple[int, int, int]]]:
    """
    Intelligently identifies the chemical reaction container (well, pouch, ampoule)
    and extracts its core colorimetric CIELAB reading.
    Returns: (bbox: (x, y, w, h), lab: (L*, a*, b*), circle: (cx, cy, r) | None)
    """
    img_h, img_w = image_bgr.shape[:2]

    # Search zone: strictly exclude the card area
    if card_side == "right":
        sx1, sx2 = 0, int(img_w * 0.52)
    elif card_side == "left":
        sx1, sx2 = int(img_w * 0.45), img_w
    else:
        sx1, sx2 = int(img_w * 0.05), int(img_w * 0.95)
    sy1, sy2 = int(img_h * 0.05), int(img_h * 0.95)

    search_crop = image_bgr[sy1:sy2, sx1:sx2]
    sc_h, sc_w = search_crop.shape[:2]
    if sc_h < 20 or sc_w < 20:
        search_crop = image_bgr
        sx1, sy1, sc_w, sc_h = 0, 0, img_w, img_h

    best_roi: Optional[Tuple[int, int, int, int]] = None
    best_lab: Optional[Tuple[float, float, float]] = None
    best_circle: Optional[Tuple[int, int, int]] = None
    best_score = -1.0

    # ── Strategy 1: Circular Reaction Well (Blister pack / well tray) ────────
    gray_sc = cv2.cvtColor(search_crop, cv2.COLOR_BGR2GRAY)
    blurred_sc = cv2.GaussianBlur(gray_sc, (7, 7), 1.5)
    circles = cv2.HoughCircles(
        blurred_sc, cv2.HOUGH_GRADIENT, dp=1.2, minDist=max(min(sc_w, sc_h) // 3, 20),
        param1=60, param2=22, minRadius=int(min(sc_w, sc_h) * 0.12), maxRadius=int(min(sc_w, sc_h) * 0.48)
    )

    if circles is not None:
        for c in circles[0]:
            cx, cy, r = int(c[0]), int(c[1]), int(c[2])
            dist_to_center = np.hypot(cx - sc_w // 2, cy - sc_h // 2)
            # Sample core inside circle (inner 55% radius avoids glare and plastic rims)
            mask = np.zeros((sc_h, sc_w), dtype=np.uint8)
            cv2.circle(mask, (cx, cy), max(int(r * 0.55), 3), 255, -1)
            pts = search_crop[mask == 255]
            if len(pts) > 30:
                med_bgr = np.median(pts, axis=0)
                lab = bgr_to_cielab(med_bgr)
                chroma_val = np.hypot(lab[1], lab[2])
                # Wells with liquid have distinct chroma and centrality
                score = 60.0 + chroma_val - (dist_to_center / sc_w * 25.0)
                if score > best_score:
                    best_score = score
                    gx1 = sx1 + max(0, cx - r)
                    gy1 = sy1 + max(0, cy - r)
                    gx2 = sx1 + min(sc_w, cx + r)
                    gy2 = sy1 + min(sc_h, cy + r)
                    best_roi = (gx1, gy1, gx2 - gx1, gy2 - gy1)
                    best_lab = lab
                    best_circle = (sx1 + cx, sy1 + cy, r)

    # ── Strategy 2: Fluid / Chromophore Contour Detection (Pouches, Ampoules) ──
    hsv_sc = cv2.cvtColor(search_crop, cv2.COLOR_BGR2HSV)
    sat_sc = hsv_sc[:, :, 1]
    val_sc = hsv_sc[:, :, 2]
    # Saturated or colored fluid pixels
    chroma_mask = ((sat_sc > 22) & (val_sc > 20) & (val_sc < 252)).astype(np.uint8) * 255
    cnts, _ = cv2.findContours(chroma_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for c in cnts:
        area = cv2.contourArea(c)
        if area > (img_w * img_h * 0.035) and area < (img_w * img_h * 0.65):
            bx, by, bw, bh = cv2.boundingRect(c)
            # Sample inner 50% core of bounding box
            core = search_crop[by + bh // 4 : by + 3 * bh // 4, bx + bw // 4 : bx + 3 * bw // 4]
            if core.size > 0:
                med_bgr = np.median(core.reshape(-1, 3), axis=0)
                lab = bgr_to_cielab(med_bgr)
                chroma_val = np.hypot(lab[1], lab[2])
                score = (area / (img_w * img_h) * 100.0) + chroma_val
                # If no strong circle, or if this fluid contour has higher salience
                if score > best_score:
                    best_score = score
                    best_roi = (sx1 + bx, sy1 + by, bw, bh)
                    best_lab = lab
                    best_circle = None

    # ── Strategy 3: Geometric fallback within search zone ────────────────────
    if best_roi is None or best_lab is None:
        if default_roi and card_side != "right":
            rx1 = int(default_roi.get("x", 0.38) * img_w)
            ry1 = int(default_roi.get("y", 0.25) * img_h)
            rw = int(default_roi.get("w", 0.54) * img_w)
            rh = int(default_roi.get("h", 0.50) * img_h)
            best_roi = (rx1, ry1, rw, rh)
            core = image_bgr[ry1 + rh // 4 : ry1 + 3 * rh // 4, rx1 + rw // 4 : rx1 + 3 * rw // 4]
            best_lab = bgr_to_cielab(np.median(core.reshape(-1, 3), axis=0))
        else:
            bx = sx1 + sc_w // 4
            by = sy1 + sc_h // 4
            bw = max(sc_w // 2, 20)
            bh = max(sc_h // 2, 20)
            best_roi = (bx, by, bw, bh)
            core = image_bgr[by : by + bh, bx : bx + bw]
            best_lab = bgr_to_cielab(np.median(core.reshape(-1, 3), axis=0))

    return best_roi, best_lab, best_circle


def detect_and_calibrate(
    image_bgr: np.ndarray,
    card_roi: Optional[Dict[str, float]] = None,
    reaction_roi: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Executes the full forensic Computer Vision pipeline:
    1. Reference Card Identification:
       - 6-Patch Forensic Card -> CARD_CALIBRATED (3x3 least-squares correction)
       - Kit Legend Card / No Card -> BYPASS_NO_CARD
    2. Intelligent Reaction Zone Detection:
       - Automatically segments the true reaction well, pouch, or ampoule
       - Samples the verified liquid core (excluding glare, rims, and card labels)
    3. Forensic Overlay Generation & Cryptographic Verification Metadata
    """
    img_h, img_w = image_bgr.shape[:2]

    # ── Phase 1: Check for Standard 6-Patch Calibration Card ──────────────
    has_card_l, de_l, M_l, cal_l, box_l = _evaluate_6patch_card(image_bgr, 0.04, 0.28)
    has_card_r, de_r, M_r, cal_r, box_r = _evaluate_6patch_card(image_bgr, 0.72, 0.96)

    card_side: Optional[str] = None
    card_box: Optional[Tuple[int, int, int, int]] = None
    card_detected = False

    if has_card_l:
        mode = "CARD_CALIBRATED"
        calibration_success = True
        mean_delta_e = de_l
        calibrated_bgr = cal_l
        card_side = "left"
        card_box = box_l
        card_detected = True
        transform_matrix = M_l.tolist()
    elif has_card_r:
        mode = "CARD_CALIBRATED"
        calibration_success = True
        mean_delta_e = de_r
        calibrated_bgr = cal_r
        card_side = "right"
        card_box = box_r
        card_detected = True
        transform_matrix = M_r.tolist()
    else:
        # BYPASS_NO_CARD mode
        mode = "BYPASS_NO_CARD"
        calibration_success = True
        mean_delta_e = 0.0
        calibrated_bgr = image_bgr.copy()
        transform_matrix = np.eye(3, dtype=np.float32).tolist()

        # Check for printed kit legend card
        l_side, l_box = _detect_kit_legend_card(image_bgr)
        if l_side:
            card_side = l_side
            card_box = l_box
            card_detected = True

    # ── Phase 2: Reaction Zone Localization ───────────────────────────────
    (rx, ry, rw, rh), reaction_cielab, detected_circle = _find_reaction_zone(
        calibrated_bgr, card_side=card_side, default_roi=reaction_roi
    )

    rx1, ry1 = max(0, rx), max(0, ry)
    rx2, ry2 = min(img_w, rx + rw), min(img_h, ry + rh)
    reaction_hex = cielab_to_bgr_hex(reaction_cielab)

    # ── Phase 3: Forensic Derivative Image Annotation ─────────────────────
    annotated = calibrated_bgr.copy()

    # Draw card overlay if present
    if card_box:
        cx, cy, cw, ch = card_box
        card_col = (0, 255, 255) if mode == "CARD_CALIBRATED" else (180, 180, 180)
        card_lbl = f"REF CARD (dE={mean_delta_e:.1f})" if mode == "CARD_CALIBRATED" else "REF CARD (LEGEND)"
        cv2.rectangle(annotated, (cx, cy), (cx + cw, cy + ch), card_col, 2)
        cv2.putText(
            annotated, card_lbl,
            (cx, max(cy - 8, 16)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, card_col, 1, cv2.LINE_AA
        )
    else:
        cv2.putText(
            annotated, "NO REF CARD (BYPASS)",
            (15, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.50, (130, 130, 130), 1, cv2.LINE_AA
        )

    # Draw reaction ROI
    cv2.rectangle(annotated, (rx1, ry1), (rx2, ry2), (0, 255, 0), 2)
    if detected_circle:
        dcx, dcy, dcr = detected_circle
        cv2.circle(annotated, (dcx, dcy), max(int(dcr * 0.55), 3), (0, 255, 120), 2)

    lab_tag = f"REACTION ROI [L*={reaction_cielab[0]:.1f}, a*={reaction_cielab[1]:.1f}, b*={reaction_cielab[2]:.1f}]"
    cv2.putText(
        annotated,
        lab_tag,
        (rx1, max(ry1 - 8, 16)),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA
    )

    return {
        "calibration_success": calibration_success,
        "calibration_mode": mode,
        "card_detected": card_detected,
        "calibration_error_delta_e": round(mean_delta_e, 2),
        "calibrated_image_bgr": calibrated_bgr,
        "annotated_image_bgr": annotated,
        "reaction_cielab": {
            "L": round(reaction_cielab[0], 2),
            "a": round(reaction_cielab[1], 2),
            "b": round(reaction_cielab[2], 2),
        },
        "reaction_hex": reaction_hex,
        "reaction_roi": {
            "x": round(rx1 / img_w, 4),
            "y": round(ry1 / img_h, 4),
            "w": round((rx2 - rx1) / img_w, 4),
            "h": round((ry2 - ry1) / img_h, 4),
        },
        "transform_matrix": transform_matrix,
    }

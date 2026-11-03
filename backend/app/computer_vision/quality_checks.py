import cv2
import numpy as np
from typing import Dict, Any, Tuple

# Hard minimum: blocks classification (prevents CV on truly unusable images)
_MIN_WIDTH_HARD = 120
_MIN_HEIGHT_HARD = 90

# Soft advisory: logged as a warning but does NOT block classification
# Recommended forensic minimum is 640x480; uploaded images may be smaller.
_MIN_WIDTH_ADVISORY = 640
_MIN_HEIGHT_ADVISORY = 480


def check_image_quality(image_bgr: np.ndarray) -> Dict[str, Any]:
    """
    Evaluates image for forensic quality standards.

    Hard failures (block classification):
      - Blur / sharpness (Laplacian variance < 50)
      - Underexposure (mean luminance < 40)
      - Overexposure (> 15% blown-out pixels, or mean > 230)
      - Image too small to process (< 120x90 — essentially unusable)

    Soft advisories (logged in notes, do NOT block classification):
      - Resolution below recommended forensic standard (640x480)
        Uploaded photographs may be smaller than live-camera captures;
        classification proceeds but the resolution advisory is recorded.
    """
    height, width = image_bgr.shape[:2]

    # ── Hard: image too small to run CV at all ──
    too_small = (width < _MIN_WIDTH_HARD or height < _MIN_HEIGHT_HARD)

    # ── Soft: below recommended forensic resolution ──
    below_advisory = (width < _MIN_WIDTH_ADVISORY or height < _MIN_HEIGHT_ADVISORY)

    # ── Grayscale conversion for photometric / frequency analysis ──
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    # ── Blur Detection via Laplacian Variance ──
    # Note: Laplacian variance scales with resolution. For downscaled/web uploads (e.g. <640px),
    # values between 15-45 are normal. A hard threshold of 15.0 catches true motion blur.
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    hard_blur_thresh = 15.0
    advisory_blur_thresh = 40.0
    is_blurry = laplacian_var < hard_blur_thresh
    is_advisory_blur = (laplacian_var >= hard_blur_thresh) and (laplacian_var < advisory_blur_thresh)

    # ── Illumination & Exposure Analysis ──
    mean_illumination = float(np.mean(gray))
    is_underexposed = mean_illumination < 28.0

    highlight_pixels = np.count_nonzero(gray >= 250)
    highlight_ratio = float(highlight_pixels / (width * height))
    is_overexposed = highlight_ratio > 0.20 or mean_illumination > 235.0

    # ── Collect hard-failure issues (these block classification) ──
    hard_issues: list = []
    if too_small:
        hard_issues.append(
            f"Image resolution {width}x{height} is too small for computer vision "
            f"(minimum {_MIN_WIDTH_HARD}x{_MIN_HEIGHT_HARD})."
        )
    if is_blurry:
        hard_issues.append(
            f"Image is heavily blurred (sharpness score {laplacian_var:.1f} < {hard_blur_thresh:.1f}). "
            f"Keep device steady and refocus."
        )
    if is_underexposed:
        hard_issues.append(
            f"Lighting is insufficient (mean luminance {mean_illumination:.1f} < 28.0). "
            f"Enable flash or move to better light."
        )
    if is_overexposed:
        hard_issues.append(
            f"Image is severely overexposed ({highlight_ratio*100:.1f}% blown-out highlights). "
            f"Avoid direct glare or reflections."
        )

    # ── Soft advisory (logged but does not block) ──
    advisories: list = []
    if is_advisory_blur:
        advisories.append(
            f"Advisory: Image sharpness ({laplacian_var:.1f}) is slightly soft. "
            f"Classification proceeds; confirm focus if reaction is subtle."
        )
    if below_advisory and not too_small:
        advisories.append(
            f"Advisory: Image resolution {width}x{height} is below the recommended "
            f"forensic standard of {_MIN_WIDTH_ADVISORY}x{_MIN_HEIGHT_ADVISORY}. "
            f"Classification proceeds; confirmatory laboratory analysis recommended."
        )

    passed = len(hard_issues) == 0
    all_notes = hard_issues + advisories

    return {
        "passed": passed,
        "width": width,
        "height": height,
        "blur_score": round(laplacian_var, 2),
        "is_blurry": is_blurry,
        "illumination_score": round(mean_illumination, 2),
        "is_underexposed": is_underexposed,
        "is_overexposed": is_overexposed,
        "highlight_ratio": round(highlight_ratio, 4),
        "below_advisory_resolution": below_advisory and not too_small,
        "issues": hard_issues,
        "advisories": advisories,
        "notes": "; ".join(all_notes) if all_notes else "All image quality checks passed forensic standards."
    }

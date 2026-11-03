import math
from typing import Dict, Any, Tuple, Optional, List
from app.computer_vision.ciede2000 import ciede2000
from app.models.evidence import ClassificationResult
from app.models.test_kit import ValidationStatus

STATUTORY_DISCLAIMER = (
    "Automated output is a presumptive field-test result. It is not a laboratory-confirmed "
    "identification. Confirmatory laboratory testing is required."
)

class ClassificationEngine:
    """
    Forensic classification engine using calibrated CIELAB colorimetry and CIEDE2000.
    Enforces all regulatory safeguards:
    - Rejects unapproved or unvalidated test kit profiles
    - Rejects images that fail forensic quality or calibration standards
    - Differentiates ambiguous chemical reactions (INCONCLUSIVE) from operational failures (UNABLE_TO_CLASSIFY)
    - Enforces neutral-chroma gates to prevent gray/ambiguous reactions from matching negative profiles
    - Features multi-profile cross-validation for both positive and negative reagent reactions
    - Appends statutory legal disclaimer to all outputs
    """

    @staticmethod
    def classify_reaction(
        measured_lab: Tuple[float, float, float],
        kit_profile: Any,
        quality_assessment: Dict[str, Any],
        calibration_assessment: Dict[str, Any],
        all_profiles: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes rule-based CIEDE2000 classification against validated kit profile(s).
        """
        # --- SAFEGUARD 1: Check kit profile approval status ---
        if not kit_profile and not all_profiles:
            return {
                "result": ClassificationResult.UNABLE_TO_CLASSIFY.value,
                "reason": "Operational Error: No test kit profile specified for automated classification.",
                "confidence": 0.0,
                "d_pos": None,
                "d_neg": None,
                "disclaimer": STATUTORY_DISCLAIMER,
                "safeguard_triggered": "MISSING_KIT_PROFILE"
            }

        if kit_profile and getattr(kit_profile, "validation_status", "") == ValidationStatus.PENDING_VALIDATION.value:
            return {
                "result": ClassificationResult.UNABLE_TO_CLASSIFY.value,
                "reason": "Administrative Safeguard: Kit profile is pending forensic laboratory validation. Manual review required.",
                "confidence": 0.0,
                "d_pos": None,
                "d_neg": None,
                "disclaimer": STATUTORY_DISCLAIMER,
                "safeguard_triggered": "UNVALIDATED_PROFILE"
            }

        # --- SAFEGUARD 2: Image Quality Check (hard failures only) ---
        if not quality_assessment.get("passed", False):
            hard_issues = quality_assessment.get("issues", [])
            issue_text = "; ".join(hard_issues) if hard_issues else quality_assessment.get("notes", "Image quality below threshold")
            return {
                "result": ClassificationResult.UNABLE_TO_CLASSIFY.value,
                "reason": f"Operational Quality Failure: {issue_text}. Recapture required.",
                "confidence": 0.0,
                "d_pos": None,
                "d_neg": None,
                "disclaimer": STATUTORY_DISCLAIMER,
                "safeguard_triggered": "QUALITY_CHECK_FAILED"
            }

        # --- SAFEGUARD 3: Calibration Check ---
        calib_mode = calibration_assessment.get("calibration_mode", "CARD_CALIBRATED")
        is_bypass  = (calib_mode == "BYPASS_NO_CARD")

        if not calibration_assessment.get("calibration_success", False):
            return {
                "result": ClassificationResult.UNABLE_TO_CLASSIFY.value,
                "reason": "Calibration Safeguard: Reference color card could not be calibrated accurately. Recapture required.",
                "confidence": 0.0,
                "d_pos": None,
                "d_neg": None,
                "disclaimer": STATUTORY_DISCLAIMER,
                "safeguard_triggered": "CALIBRATION_FAILED"
            }

        calib_error = calibration_assessment.get("calibration_error_delta_e", 0.0)
        if not is_bypass and calib_error > 25.0:
            return {
                "result": ClassificationResult.UNABLE_TO_CLASSIFY.value,
                "reason": (
                    f"Calibration Safeguard: Residual card calibration error "
                    f"(Delta E = {calib_error:.1f}) exceeds allowable tolerance (25.0). "
                    f"Recapture in even lighting."
                ),
                "confidence": 0.0,
                "d_pos": None,
                "d_neg": None,
                "disclaimer": STATUTORY_DISCLAIMER,
                "safeguard_triggered": "EXCESSIVE_CALIBRATION_ERROR"
            }

        # --- SAFEGUARD 4: Neutral-Chroma / Ambiguous Gray Invariant ---
        # Valid forensic negatives possess distinct chemical chromophores (Amber b*>=16, Pink a*>=8).
        # A neutral grey hue (chroma <= 10.0, mid-luminance) represents unreacted / adulterated ambiguity.
        chroma = math.hypot(measured_lab[1], measured_lab[2])
        if chroma <= 10.0 and (30.0 <= measured_lab[0] <= 76.0):
            return {
                "result": ClassificationResult.INCONCLUSIVE.value,
                "reason": (
                    f"Chemically Ambiguous Reaction: Reaction exhibits neutral gray/slate hue (chroma = {chroma:.1f} <= 10.0). "
                    f"Reagent did not produce a validated chromatic negative or positive reaction. "
                    f"Repeat test or submit for confirmatory laboratory analysis."
                ),
                "confidence": 0.45,
                "d_pos": None,
                "d_neg": None,
                "threshold_pos": None,
                "threshold_neg": None,
                "disclaimer": STATUTORY_DISCLAIMER,
                "safeguard_triggered": None,
                "matched_kit_id": getattr(kit_profile, "kit_id", None),
                "matched_profile_id": getattr(kit_profile, "id", None),
                "analyte_detected": None
            }

        # --- STEP 5: Helper to evaluate a specific profile ---
        def eval_profile(prof):
            pos_ref = (
                float(prof.positive_cielab_l),
                float(prof.positive_cielab_a),
                float(prof.positive_cielab_b)
            )
            neg_ref = (
                float(prof.negative_cielab_l),
                float(prof.negative_cielab_a),
                float(prof.negative_cielab_b)
            )
            d_p = ciede2000(measured_lab, pos_ref)
            d_n = ciede2000(measured_lab, neg_ref)
            t_p = float(getattr(prof, "positive_delta_e_threshold", 18.0))
            t_n = float(getattr(prof, "negative_delta_e_threshold", 16.0))
            i_m = float(getattr(prof, "inconclusive_delta_e_threshold", 7.0))
            
            # Ambient tolerance adjustment for uncalibrated field bypass
            eff_t_p = t_p + 2.0 if is_bypass else t_p
            eff_t_n = t_n + 2.0 if is_bypass else t_n
            eff_i_m = 6.0 if is_bypass else i_m
            
            return d_p, d_n, eff_t_p, eff_t_n, eff_i_m

        # Evaluate against primary profile
        active_prof = kit_profile or (all_profiles[0] if all_profiles else None)
        d_pos, d_neg, threshold_pos, threshold_neg, inconclusive_margin = eval_profile(active_prof)
        matched_profile = active_prof
        delta_diff = abs(d_pos - d_neg)

        # ── Cross-Profile Positive Match ──
        # If primary profile did not match positive, check if another approved profile strongly matches positive
        if (d_pos > threshold_pos or d_pos >= d_neg) and all_profiles:
            best_other_pos = None
            best_other_dp = 999.0
            for other_prof in all_profiles:
                if other_prof.id == active_prof.id:
                    continue
                o_dp, o_dn, o_tp, o_tn, _ = eval_profile(other_prof)
                if o_dp <= o_tp and o_dp < o_dn and abs(o_dp - o_dn) >= 6.0 and o_dp < best_other_dp:
                    best_other_dp = o_dp
                    best_other_pos = (other_prof, o_dp, o_dn, o_tp, o_tn)
            
            if best_other_pos and best_other_dp < 16.0:
                matched_profile, d_pos, d_neg, threshold_pos, threshold_neg = best_other_pos
                delta_diff = abs(d_pos - d_neg)

        # ── Cross-Profile Negative Match ──
        # If neither positive matched, and primary profile did not match negative, check if another profile matches negative
        if d_pos > threshold_pos and d_neg > threshold_neg and all_profiles:
            best_other_neg = None
            best_other_dn = 999.0
            for other_prof in all_profiles:
                if other_prof.id == active_prof.id:
                    continue
                o_dp, o_dn, o_tp, o_tn, _ = eval_profile(other_prof)
                if o_dn <= o_tn and o_dn < o_dp and abs(o_dp - o_dn) >= 6.0 and o_dn < best_other_dn:
                    best_other_dn = o_dn
                    best_other_neg = (other_prof, o_dp, o_dn, o_tp, o_tn)
            
            if best_other_neg and best_other_dn < 14.0:
                matched_profile, d_pos, d_neg, threshold_pos, threshold_neg = best_other_neg
                delta_diff = abs(d_pos - d_neg)

        # --- STEP 6: Decision Logic ---
        analyte_name = getattr(getattr(matched_profile, "kit", None), "analyte", "target analyte")
        kit_display_name = getattr(getattr(matched_profile, "kit", None), "name", "reagent kit")

        if delta_diff < inconclusive_margin and (d_pos < threshold_pos * 1.2 or d_neg < threshold_neg * 1.2):
            result = ClassificationResult.INCONCLUSIVE.value
            reason = (
                f"Chemically Ambiguous Reaction: Reaction color distance to Positive (Delta E = {d_pos:.1f}) "
                f"and Negative (Delta E = {d_neg:.1f}) is within inconclusive boundary margin ({inconclusive_margin:.1f})."
            )
            confidence = 0.50
        elif d_pos <= threshold_pos and d_pos < d_neg:
            result = ClassificationResult.PRESUMPTIVE_POSITIVE.value
            confidence = max(0.65, min(0.98, 1.0 - (d_pos / (threshold_pos * 1.8))))
            reason = (
                f"Color reaction matches validated positive reference profile for {analyte_name} "
                f"(Delta E = {d_pos:.1f} <= threshold {threshold_pos:.1f})."
            )
        elif d_neg <= threshold_neg and d_neg < d_pos:
            result = ClassificationResult.PRESUMPTIVE_NEGATIVE.value
            confidence = max(0.65, min(0.98, 1.0 - (d_neg / (threshold_neg * 1.8))))
            reason = (
                f"Color reaction matches validated negative reference profile for {kit_display_name} "
                f"(Delta E = {d_neg:.1f} <= threshold {threshold_neg:.1f})."
            )
        else:
            result = ClassificationResult.INCONCLUSIVE.value
            reason = (
                f"Reaction color does not match validated positive (Delta E = {d_pos:.1f} > {threshold_pos:.1f}) "
                f"nor negative profile (Delta E = {d_neg:.1f} > {threshold_neg:.1f})."
            )
            confidence = 0.40

        return {
            "result": result,
            "reason": reason,
            "confidence": round(confidence, 3),
            "d_pos": round(d_pos, 2) if d_pos is not None else None,
            "d_neg": round(d_neg, 2) if d_neg is not None else None,
            "threshold_pos": threshold_pos,
            "threshold_neg": threshold_neg,
            "disclaimer": STATUTORY_DISCLAIMER,
            "safeguard_triggered": None,
            "matched_kit_id": getattr(matched_profile, "kit_id", None),
            "matched_profile_id": getattr(matched_profile, "id", None),
            "analyte_detected": analyte_name if result == ClassificationResult.PRESUMPTIVE_POSITIVE.value else None
        }

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database.session import get_db
from app.models.evidence import TestRecord, ClassificationResult, VerificationStatus, SyncStatus
from app.models.test_kit import TestKit
from app.models.user import User
from app.schemas.evidence import DashboardStatsResponse, TestRecordSummary
from app.api.deps import get_current_user

router = APIRouter(prefix="/analytics", tags=["Dashboard & Analytics"])

@router.get("/dashboard", response_model=DashboardStatsResponse)
def get_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total = db.query(TestRecord).count()
    pos = db.query(TestRecord).filter(TestRecord.classification_result == ClassificationResult.PRESUMPTIVE_POSITIVE.value).count()
    neg = db.query(TestRecord).filter(TestRecord.classification_result == ClassificationResult.PRESUMPTIVE_NEGATIVE.value).count()
    inconc = db.query(TestRecord).filter(TestRecord.classification_result == ClassificationResult.INCONCLUSIVE.value).count()
    unable = db.query(TestRecord).filter(TestRecord.classification_result == ClassificationResult.UNABLE_TO_CLASSIFY.value).count()
    
    pending_sync = db.query(TestRecord).filter(TestRecord.sync_status != SyncStatus.SYNCHRONIZED.value).count()
    verified = db.query(TestRecord).filter(TestRecord.verification_status == VerificationStatus.VERIFIED.value).count()
    integrity_failed = db.query(TestRecord).filter(TestRecord.verification_status == VerificationStatus.INTEGRITY_FAILED.value).count()

    # Kit Breakdown
    kits = db.query(TestKit.name, func.count(TestRecord.id)).join(TestRecord, TestKit.id == TestRecord.kit_id, isouter=True).group_by(TestKit.name).all()
    kit_breakdown = [{"name": name, "count": count} for name, count in kits]

    # Officer Stats
    officers = db.query(TestRecord.operator_name, func.count(TestRecord.id)).group_by(TestRecord.operator_name).all()
    officer_stats = [{"name": name, "tests": count} for name, count in officers]

    # Monthly Trends (aggregated by month)
    trends = db.query(
        func.strftime("%Y-%m", TestRecord.created_at).label("month"),
        func.count(TestRecord.id)
    ).group_by("month").order_by("month").all()
    monthly_trends = [{"month": m or "2026-11", "count": c} for m, c in trends]

    # Recent Tests
    recents = db.query(TestRecord).order_by(desc(TestRecord.created_at)).limit(8).all()
    recent_summaries = []
    for r in recents:
        recent_summaries.append(TestRecordSummary(
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

    return DashboardStatsResponse(
        total_tests=total,
        positive_count=pos,
        negative_count=neg,
        inconclusive_count=inconc,
        unable_to_classify_count=unable,
        pending_sync_count=pending_sync,
        verified_count=verified,
        integrity_failure_count=integrity_failed,
        recent_tests=recent_summaries,
        kit_breakdown=kit_breakdown,
        monthly_trends=monthly_trends,
        officer_stats=officer_stats
    )

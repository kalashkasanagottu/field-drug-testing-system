import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.session import get_db
from app.models.evidence import TestRecord
from app.models.user import User
from app.reports.pdf_generator import generate_pdf_report
from app.services.audit_service import log_audit_event
from app.api.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["Forensic PDF Reports"])

@router.get("", response_model=List[Dict[str, Any]])
def list_generated_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all generated PDF reports."""
    from typing import List, Dict, Any
    reports_dir = Path(settings.REPORTS_PATH)
    reports = []
    if reports_dir.exists():
        for pdf_file in sorted(reports_dir.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True):
            test_id = pdf_file.stem.replace("_report", "")
            stat = pdf_file.stat()
            reports.append({
                "report_id": pdf_file.stem,
                "test_id": test_id,
                "filename": pdf_file.name,
                "file_size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "download_url": f"/api/reports/{test_id}/download"
            })
    return reports

@router.post("/{test_id}/generate")
def create_pdf_report(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = db.query(TestRecord).filter(TestRecord.test_id == test_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Test record not found.")

    pdf_filename = f"{test_id}_report.pdf"
    pdf_path = str(Path(settings.REPORTS_PATH) / pdf_filename)

    generate_pdf_report(record, pdf_path)

    log_audit_event(
        db,
        event_type="REPORT_GENERATED",
        user_id=current_user.id,
        user_name=current_user.username,
        related_record_id=record.test_id,
        details={"report_filename": pdf_filename, "file_size_bytes": os.path.getsize(pdf_path)}
    )

    return {
        "message": "Report generated successfully.",
        "test_id": test_id,
        "download_url": f"/api/reports/{test_id}/download",
        "file_size": os.path.getsize(pdf_path)
    }

@router.get("/{test_id}/download")
def download_pdf_report(
    test_id: str,
    db: Session = Depends(get_db)
):
    record = db.query(TestRecord).filter(TestRecord.test_id == test_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Test record not found.")

    pdf_filename = f"{test_id}_report.pdf"
    pdf_path = Path(settings.REPORTS_PATH) / pdf_filename

    # If not yet generated, generate on-the-fly
    if not pdf_path.exists():
        generate_pdf_report(record, str(pdf_path))

    return FileResponse(
        path=str(pdf_path),
        filename=f"Forensic_Evidence_Report_{test_id}.pdf",
        media_type="application/pdf"
    )

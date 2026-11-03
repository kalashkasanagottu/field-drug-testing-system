from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.auth import router as auth_router
from app.api.kits import router as kits_router
from app.api.tests import router as tests_router
from app.api.evidence import router as evidence_router
from app.api.reports import router as reports_router
from app.api.analytics import router as analytics_router
from app.api.admin import router as admin_router
from app.services.seed_data import seed_database

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.SYSTEM_VERSION,
    description="Automated Drug Colorimetric Reaction Analysis, CIEDE2000 Calibration & Ed25519 Tamper-Evident Evidence Management API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# Enable CORS for web and mobile clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for images and generated PDF reports
uploads_dir = Path(settings.UPLOAD_PATH)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Include API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(kits_router, prefix=settings.API_V1_STR)
app.include_router(tests_router, prefix=settings.API_V1_STR)
app.include_router(evidence_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def on_startup():
    """Seeds default accounts, approved test kits, and profiles on application startup."""
    seed_database()

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.SYSTEM_VERSION,
        "status": "OPERATIONAL",
        "docs": f"{settings.API_V1_STR}/docs"
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "timestamp": datetime.now(timezone.utc).isoformat() if "datetime" in globals() else None
    }

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
KEYS_DIR = DATA_DIR / "keys"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
KEYS_DIR.mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "original").mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "processed").mkdir(parents=True, exist_ok=True)
(UPLOAD_DIR / "reports").mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Digital Field Drug Testing & Forensic Evidence Management System"
    API_V1_STR: str = "/api"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "forensic-field-drug-testing-master-secret-key-2026-ciede2000-ed25519")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database URL: default SQLite with absolute path for reliable cross-platform execution
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'field_evidence.db'}")
    
    # Cryptographic keys
    ED25519_KEY_ID: str = "KEY-FORENSIC-2026-V1"
    ED25519_PRIVATE_KEY_PATH: str = str(KEYS_DIR / "ed25519_private.pem")
    ED25519_PUBLIC_KEY_PATH: str = str(KEYS_DIR / "ed25519_public.pem")
    
    # Storage paths
    UPLOAD_PATH: str = str(UPLOAD_DIR)
    REPORTS_PATH: str = str(UPLOAD_DIR / "reports")
    
    # Application versioning
    ALGORITHM_VERSION: str = "CV-CALIB-V1.4-CIEDE2000"
    SYSTEM_VERSION: str = "2.0.0"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")

settings = Settings()

import os
import json
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
import jwt
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

from app.core.config import settings

# --- Password Hashing (PBKDF2-HMAC-SHA256 with 200,000 rounds) ---

def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000)
    return f"pbkdf2:sha256:200000${salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        iterations = int(parts[0].split(":")[2])
        salt = parts[1]
        stored_hash = parts[2]
        new_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return hmac.compare_digest(new_hash.hex(), stored_hash)
    except Exception:
        return False

# --- JWT Token Management ---

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a long-lived refresh token for token rotation."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=7)  # 7-day refresh token
    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except jwt.PyJWTError:
        return None

# --- Canonical JSON Serialization & Timestamp Formatting ---

def format_canonical_timestamp(dt: Any) -> str:
    if not dt:
        return ""
    if isinstance(dt, str):
        # Normalize ISO strings
        try:
            parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            return dt[:19] + "Z"
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return str(dt)

def build_canonical_payload(record: Any) -> Dict[str, Any]:
    """
    Constructs the canonical dictionary representation of an evidence record.
    Used identically during initial signing and subsequent independent verification.
    """
    dev_ts = getattr(record, "device_timestamp", None)
    srv_ts = getattr(record, "server_timestamp", None)

    lat = getattr(record, "gps_latitude", None)
    lon = getattr(record, "gps_longitude", None)

    return {
        "test_id": str(getattr(record, "test_id", "")),
        "case_reference": getattr(record, "case_reference", None),
        "operator_id": int(getattr(record, "operator_id", 0)),
        "kit_id": int(getattr(record, "kit_id", 0)),
        "kit_batch_number": str(getattr(record, "kit_batch_number", "")),
        "original_image_hash": str(getattr(record, "original_image_hash", "")),
        "classification_result": str(getattr(record, "classification_result", "")),
        "analyte_detected": getattr(record, "analyte_detected", None),
        "algorithm_version": str(getattr(record, "algorithm_version", settings.ALGORITHM_VERSION)),
        "gps_latitude": round(float(lat), 6) if lat is not None else None,
        "gps_longitude": round(float(lon), 6) if lon is not None else None,
        "device_timestamp": format_canonical_timestamp(dev_ts),
        "server_timestamp": format_canonical_timestamp(srv_ts)
    }

def canonical_json_bytes(data: Dict[str, Any]) -> bytes:
    """
    Produce a deterministic byte representation of a dictionary for digital signing.
    Sorts all keys, removes indentation, uses minimal separators (',', ':'), UTF-8.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

# --- Ed25519 Digital Signing and Verification ---

def _load_or_create_ed25519_keys() -> Tuple[ed25519.Ed25519PrivateKey, ed25519.Ed25519PublicKey]:
    priv_path = settings.ED25519_PRIVATE_KEY_PATH
    pub_path = settings.ED25519_PUBLIC_KEY_PATH
    
    if os.path.exists(priv_path) and os.path.exists(pub_path):
        try:
            with open(priv_path, "rb") as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)
            with open(pub_path, "rb") as f:
                public_key = serialization.load_pem_public_key(f.read())
            if isinstance(private_key, ed25519.Ed25519PrivateKey) and isinstance(public_key, ed25519.Ed25519PublicKey):
                return private_key, public_key
        except Exception:
            pass

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    with open(priv_path, "wb") as f:
        f.write(priv_bytes)
    with open(pub_path, "wb") as f:
        f.write(pub_bytes)
        
    return private_key, public_key

_private_key, _public_key = _load_or_create_ed25519_keys()

def get_public_key_hex() -> str:
    pub_bytes = _public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return pub_bytes.hex()

def sign_data(data: Dict[str, Any]) -> Tuple[str, str, str]:
    canon_bytes = canonical_json_bytes(data)
    record_hash = hashlib.sha256(canon_bytes).hexdigest()
    signature = _private_key.sign(canon_bytes)
    return signature.hex(), record_hash, settings.ED25519_KEY_ID

def verify_signature(data: Dict[str, Any], signature_hex: str, public_key_hex: Optional[str] = None) -> bool:
    try:
        canon_bytes = canonical_json_bytes(data)
        signature_bytes = bytes.fromhex(signature_hex)
        
        if public_key_hex:
            pub_bytes = bytes.fromhex(public_key_hex)
            verifier = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        else:
            verifier = _public_key
            
        verifier.verify(signature_bytes, canon_bytes)
        return True
    except Exception:
        return False

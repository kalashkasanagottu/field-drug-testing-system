import hashlib
from typing import Tuple

def compute_sha256(data_bytes: bytes) -> str:
    """Computes SHA-256 hex digest of raw binary bytes."""
    return hashlib.sha256(data_bytes).hexdigest()

def verify_image_integrity(data_bytes: bytes, expected_hash: str) -> Tuple[bool, str]:
    """
    Recalculates SHA-256 on input bytes and compares with expected hash.
    Returns (is_valid, computed_hash).
    """
    computed = compute_sha256(data_bytes)
    return (computed.lower() == expected_hash.lower(), computed)

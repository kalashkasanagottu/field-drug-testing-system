import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def compute_event_hash(
    prev_event_hash: str,
    timestamp_iso: str,
    user_id: Optional[int],
    event_type: str,
    related_record_id: Optional[str],
    details: Dict[str, Any]
) -> str:
    """
    Computes a deterministic SHA-256 hash chaining this event to the previous event.
    """
    payload = {
        "prev_hash": prev_event_hash or GENESIS_HASH,
        "timestamp": timestamp_iso,
        "user_id": user_id,
        "event_type": event_type,
        "related_record_id": related_record_id,
        "details": details
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

import json
import logging
import os
import ipaddress
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


LOG_FILE = (
    Path(os.environ.get("OT_LOG_DIR") or Path(__file__).resolve().parents[1] / "logs")
    / "ot_events.jsonl"
)

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Protect writes by threads within this Python process.
_write_lock = threading.Lock()

VALID_RESULTS = {"ACCEPTED", "REJECTED"}

REASON_SEVERITY = {
    "AUTH_FAILED": "high",
    "INVALID_SETPOINT": "medium",
    "INVALID_TURBINE": "medium",
    "MALFORMED_REQUEST": "low",
    "COMMAND_APPLIED": "info",
}


def log_security_event(
    *,
    result,
    reason_code,
    source_ip,
    turbine_id=None,
    requested_limit_kw=None,
    actor=None,
    old_limit_kw=None,
    new_limit_kw=None,
):
    """Write one structured OT security event."""

    if result not in VALID_RESULTS:
        raise ValueError("Unsupported result")

    if reason_code not in REASON_SEVERITY:
        raise ValueError("Unsupported reason code")

    event = {
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "event_id": str(uuid4()),
        "event_type": "OT_COMMAND",
        "action": "SET_POWER_LIMIT",
        "result": result,
        "reason_code": reason_code,
        "severity": REASON_SEVERITY[reason_code],
        "source_ip": source_ip,
        "turbine_id": turbine_id,
        "requested_limit_kw": requested_limit_kw,
        "actor": actor,
        "old_limit_kw": old_limit_kw,
        "new_limit_kw": new_limit_kw,
    }

    # Derive identity from the socket peer, never an HTTP forwarding header.
    # JSON array encoding keeps the two fields unambiguous.
    if turbine_id in ("WT-01", "WT-02", "WT-03"):
        event["correlation_key"] = json.dumps(
            [str(ipaddress.ip_address(source_ip)), turbine_id],
            separators=(",", ":"),
        )

    with _write_lock:
        with LOG_FILE.open(
            "a", encoding="utf-8"
        ) as file:
            file.write(
                json.dumps(event, allow_nan=False)
                + "\n"
            )

    return event

import json
from pathlib import Path
from uuid import UUID
from datetime import datetime

# Locate the security log
log_file = (
    Path(__file__).resolve().parents[1]
    / "logs"
    / "ot_events.jsonl"
)

assert log_file.exists(), "Security log not found"

# Read security events
events = [
    json.loads(line)
    for line in log_file.read_text(
        encoding="utf-8"
    ).splitlines()
    if line.strip()
]

# Check the latest three events
recent = events[-3:]

assert len(recent) == 3, "Expected three security events"

required_fields = {
    "timestamp",
    "event_id",
    "event_type",
    "action",
    "result",
    "reason_code",
    "severity",
    "source_ip",
    "turbine_id",
    "requested_limit_kw",
}

# Validate event structure
for event in recent:
    assert required_fields.issubset(event)

    assert event["event_type"] == "OT_COMMAND"
    assert event["action"] == "SET_POWER_LIMIT"

    UUID(event["event_id"])
    datetime.fromisoformat(event["timestamp"])

# Check unique event IDs
assert len({
    event["event_id"] for event in recent
}) == 3

# Check classifications
assert [e["reason_code"] for e in recent] == [
    "COMMAND_APPLIED",
    "AUTH_FAILED",
    "INVALID_SETPOINT",
]

# Check outcomes
assert [e["result"] for e in recent] == [
    "ACCEPTED",
    "REJECTED",
    "REJECTED",
]

print("CP2.4.4 SECURITY LOG TEST PASSED")
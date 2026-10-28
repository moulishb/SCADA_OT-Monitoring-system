"""Reconstruct command activity; do not infer physical impact from audit logs."""
import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path


def read_records(path):
    records, errors = [], []
    with Path(path).open(encoding="utf-8-sig") as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("expected object")
                records.append(record)
            except (ValueError, TypeError) as error:
                errors.append({"line": number, "error": str(error)})
    return records, errors


def analyze(events, alerts=(), turbine_id=None):
    timeline, invalid = [], 0
    for event in events:
        try:
            if event.get("event_type") != "OT_COMMAND":
                raise ValueError("not a command")
            when = datetime.fromisoformat(event["timestamp"])
            if when.tzinfo is None or not isinstance(event.get("event_id"), str):
                raise ValueError("missing identity or timezone")
            if event.get("result") not in ("ACCEPTED", "REJECTED"):
                raise ValueError("missing result")
            if event.get("turbine_id") not in ("WT-01", "WT-02", "WT-03"):
                raise ValueError("missing turbine")
            if turbine_id is None or event["turbine_id"] == turbine_id:
                timeline.append((when, event))
        except (KeyError, ValueError, TypeError, AttributeError):
            invalid += 1
    timeline.sort(key=lambda item: item[0])
    events = [event for _, event in timeline]
    rule_ids = {}
    for alert in alerts:
        data = alert.get("data", {})
        if isinstance(data, dict) and data.get("event_id"):
            rule_ids.setdefault(data["event_id"], set()).add(str(alert.get("rule", {}).get("id")))
    changes = [e for e in events if e["result"] == "ACCEPTED"
               and e.get("reason_code") == "COMMAND_APPLIED"
               and isinstance(e.get("old_limit_kw"), (int, float))
               and isinstance(e.get("new_limit_kw"), (int, float))
               and e["old_limit_kw"] != e["new_limit_kw"]]
    return {
        "first_observed": events[0]["timestamp"] if events else None,
        "last_observed": events[-1]["timestamp"] if events else None,
        "event_count": len(events), "invalid_records": invalid,
        "suspicious_requests": sum(e.get("reason_code") == "AUTH_FAILED" for e in events),
        "results": dict(Counter(e["result"] for e in events)),
        "turbines": dict(Counter(e["turbine_id"] for e in events)),
        "sources": dict(Counter(str(e.get("source_ip")) for e in events)),
        "verified_actors": sorted({e["actor"] for e in events if e.get("actor")}),
        "configuration_changes": changes,
        "operational_impact": "Configuration change recorded; physical impact unknown" if changes
            else "No accepted configuration change observed; operational impact unverified",
        "timeline": [{**e, "wazuh_rule_ids": sorted(rule_ids.get(e["event_id"], []))} for e in events],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events")
    parser.add_argument("--alerts")
    parser.add_argument("--turbine", choices=["WT-01", "WT-02", "WT-03"])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    events, errors = read_records(args.events)
    alerts, alert_errors = read_records(args.alerts) if args.alerts else ([], [])
    report = analyze(events, alerts, args.turbine)
    report.update(parse_errors=errors, alert_parse_errors=alert_errors)
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

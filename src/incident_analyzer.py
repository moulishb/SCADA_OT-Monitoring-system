import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG_FILE = ROOT / "logs" / "ot_events.jsonl"

START = datetime(2026, 11, 3, 16, 26, 45, tzinfo=timezone.utc)
END = datetime(2026, 11, 3, 16, 27, 15, tzinfo=timezone.utc)


def load_incident_events():
    events = []

    with LOG_FILE.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                event = json.loads(line)
                timestamp = datetime.fromisoformat(
                    event["timestamp"].replace("Z", "+00:00")
                )

                if (
                    START <= timestamp <= END
                    and event.get("turbine_id") == "WT-02"
                ):
                    events.append(event)

            except (ValueError, KeyError, TypeError) as error:
                print(f"Skipped line {line_number}: {error}")

    return sorted(events, key=lambda e: e["timestamp"])


def main():
    events = load_incident_events()

    print("INCIDENT WF-001 — EVENT TIMELINE")
    print("=" * 75)

    for event in events:
        print(
            f"{event['timestamp']} | "
            f"{event.get('event_type')} | "
            f"{event.get('result')} | "
            f"{event.get('reason_code')} | "
            f"Limit: {event.get('requested_limit_kw')} kW | "
            f"ID: {event.get('event_id')}"
        )

    rejected = sum(
        event.get("result") == "REJECTED"
        for event in events
    )

    accepted = sum(
        event.get("result") == "ACCEPTED"
        for event in events
    )

    print("=" * 75)
    print(f"Total events: {len(events)}")
    print(f"Rejected commands: {rejected}")
    print(f"Accepted commands: {accepted}")

    output = ROOT / "evidence" / "cp3.5_timeline.json"
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as file:
        json.dump(events, file, indent=2)

    print(f"Evidence saved to: {output}")


if __name__ == "__main__":
    main()
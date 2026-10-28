import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from incident_analyzer import analyze, read_records


def event(second, result="REJECTED", turbine="WT-02"):
    return dict(timestamp=f"2026-10-28T12:00:{second:02d}+00:00", event_id=str(second),
                event_type="OT_COMMAND", turbine_id=turbine, result=result,
                reason_code="AUTH_FAILED" if result == "REJECTED" else "COMMAND_APPLIED",
                source_ip="127.0.0.1", requested_limit_kw=1000,
                actor=None if result == "REJECTED" else "lab_operator",
                old_limit_kw=2000 if result == "ACCEPTED" else None,
                new_limit_kw=1000 if result == "ACCEPTED" else None)


class IncidentTests(unittest.TestCase):
    def test_order_counts_attribution_and_alert_join(self):
        report = analyze([event(3), event(1, "ACCEPTED"), event(2), event(4, turbine="WT-01")],
                         [{"data": {"event_id": "3"}, "rule": {"id": "100204"}}], "WT-02")
        self.assertEqual(report["event_count"], 3)
        self.assertEqual(report["suspicious_requests"], 2)
        self.assertEqual(report["first_observed"], event(1)["timestamp"])
        self.assertEqual(report["last_observed"], event(3)["timestamp"])
        self.assertEqual(report["timeline"][-1]["wazuh_rule_ids"], ["100204"])
        self.assertEqual(len(report["configuration_changes"]), 1)
        self.assertIn("physical impact unknown", report["operational_impact"])

    def test_incomplete_and_blocked_events(self):
        report = analyze([{}, event(1), {**event(2), "timestamp": "bad"}])
        self.assertEqual(report["invalid_records"], 2)
        self.assertEqual(report["configuration_changes"], [])
        self.assertIn("unverified", report["operational_impact"])

    def test_malformed_json(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            path.write_text(json.dumps(event(1)) + "\ninvalid\n[]\n", encoding="utf-8")
            records, errors = read_records(path)
            self.assertEqual(len(records), 1)
            self.assertEqual([e["line"] for e in errors], [2, 3])


if __name__ == "__main__":
    unittest.main()

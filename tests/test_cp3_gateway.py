"""Exercise the real HTTP handler on an ephemeral loopback port."""
import http.client
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("OT_OPERATOR_TOKEN", "cp3-test-only-token")
import modbus_server as gateway
import security_logger


class GatewayTests(unittest.TestCase):
    def test_rejected_burst_and_source_grouping(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            server = ThreadingHTTPServer(("127.0.0.1", 0), gateway.CommandHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            before = gateway.farm.turbines[1].power_limit_kw
            try:
                with patch.object(security_logger, "LOG_FILE", path):
                    for _ in range(5):
                        client = http.client.HTTPConnection(*server.server_address, timeout=5)
                        client.request("POST", "/command", json.dumps({
                            "turbine_id": "WT-02", "power_limit_kw": 1500}),
                            {"Content-Type": "application/json", "X-Operator-Token": "invalid"})
                        response = client.getresponse()
                        self.assertEqual(response.status, 403)
                        response.read()
                        client.close()
                    events = [json.loads(line) for line in path.read_text().splitlines()]
                    self.assertEqual(len(events), 5)
                    self.assertTrue(all(e["reason_code"] == "AUTH_FAILED" and e["actor"] is None for e in events))
                    self.assertEqual(len({e["correlation_key"] for e in events}), 1)
                    from datetime import datetime
                    self.assertLess((datetime.fromisoformat(events[-1]["timestamp"]) -
                                     datetime.fromisoformat(events[0]["timestamp"])).total_seconds(), 60)
                    self.assertEqual(gateway.farm.turbines[1].power_limit_kw, before)
                    for source, turbine in [("127.0.0.2", "WT-02"), ("127.0.0.1", "WT-01")]:
                        other = security_logger.log_security_event(result="REJECTED", reason_code="AUTH_FAILED",
                            source_ip=source, turbine_id=turbine)
                        self.assertNotEqual(other["correlation_key"], events[0]["correlation_key"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


if __name__ == "__main__":
    unittest.main()

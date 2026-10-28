"""Run CP2 regression scripts and a blocked-command exercise on localhost.

Requires ports 5020 and 8081 to be free. Starts and stops its own simulator.
Writes local evidence under ignored logs/cp3-exercise; never writes Wazuh alerts.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from incident_analyzer import analyze, read_records


def main():
    for port in (5020, 8081):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))
    directory = ROOT / "logs" / "cp3-exercise" / time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    directory.mkdir(parents=True)
    env = {**os.environ, "OT_OPERATOR_TOKEN": secrets.token_hex(24),
           "OT_LOG_DIR": str(ROOT / "logs"), "PYTHONPATH": str(ROOT)}
    with (directory / "server.txt").open("w", encoding="utf-8") as output:
        server = subprocess.Popen([sys.executable, "src/modbus_server.py"], cwd=ROOT,
                                  env=env, stdout=output, stderr=output)
        try:
            for _ in range(100):
                if server.poll() is not None:
                    raise RuntimeError("simulator exited; inspect server.txt")
                try:
                    with socket.create_connection(("127.0.0.1", 8081), timeout=.2):
                        break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError("gateway did not start")
            for name in ("test_power_control.py", "test_holding_registers.py",
                         "test_integrated_security.py", "test_modbus_write_security.py"):
                run = subprocess.run([sys.executable, str(ROOT / "tests" / name)], cwd=ROOT,
                                     env=env, capture_output=True, text=True, timeout=45)
                (directory / (name + ".txt")).write_text(run.stdout + run.stderr, encoding="utf-8")
                if run.returncode:
                    raise RuntimeError(f"{name} failed; inspect evidence")
                print(f"PASS {name}")
            from pymodbus.client import ModbusTcpClient
            from scada_client import read_turbine
            client = ModbusTcpClient("127.0.0.1", port=5020, timeout=3)
            assert client.connect()
            try:
                before = client.read_holding_registers(0, count=1, device_id=2)
                assert not before.isError()
                logfile = ROOT / "logs" / "ot_events.jsonl"
                offset = logfile.stat().st_size
                statuses = []
                for _ in range(5):
                    request = Request("http://127.0.0.1:8081/command", method="POST",
                        data=json.dumps({"turbine_id": "WT-02", "power_limit_kw": 1500}).encode(),
                        headers={"Content-Type": "application/json", "X-Operator-Token": "invalid"})
                    try:
                        with urlopen(request, timeout=5) as response:
                            statuses.append(response.status)
                    except HTTPError as error:
                        statuses.append(error.code)
                        error.close()
                after = client.read_holding_registers(0, count=1, device_id=2)
                assert not after.isError()
                assert statuses == [403] * 5
                assert before.registers == after.registers
                telemetry = [read_turbine(client, i, f"WT-0{i}") for i in range(1, 4)]
                assert all(telemetry)
                with logfile.open("rb") as stream:
                    stream.seek(offset)
                    captured = stream.read()
                evidence = directory / "incident-events.jsonl"
                evidence.write_bytes(captured)
                events, errors = read_records(evidence)
                assert not errors and len(events) == 5
                report = analyze(events, turbine_id="WT-02")
                report["recovery_checks"] = {"before_kw": before.registers[0],
                    "after_kw": after.registers[0], "http_statuses": statuses,
                    "telemetry": telemetry, "events_sha256": hashlib.sha256(captured).hexdigest(),
                    "wazuh_validation": "not performed by this runner; verify separately"}
                (directory / "incident-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
                print(f"PASS blocked-command exercise; evidence: {directory}")
            finally:
                client.close()
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    main()

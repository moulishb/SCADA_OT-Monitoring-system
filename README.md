# Wind Farm OT/SCADA Monitoring System

## System Design

- Three simulated turbines: WT-01, WT-02 and WT-03

- Simulated wind speed, rotor RPM, generated power, gearbox temperature and operational status

- Modbus/TCP communication for telemetry and control

- Separate monitoring and controlled command operations

## Running the lab

Use Python 3.12 with PyModbus 3.11.2 in the existing virtual environment. Set
`OT_OPERATOR_TOKEN` in the terminal, then run `python src/modbus_server.py`.
Run `python src/scada_client.py` in another terminal. The command endpoint is
`http://127.0.0.1:8081/command`; Modbus telemetry is at `127.0.0.1:5020`.
`OT_LOG_DIR` optionally selects the audit directory (default: repository `logs`).
Use the same absolute directory for the Wazuh read-only mount.

## CP3 validation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_cp3_gateway.py -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_incident_analyzer.py -v
.\.venv\Scripts\python.exe tests/run_cp3_lab.py
```

The last command requires free lab ports, starts its own simulator, exercises
authorised and rejected commands, restores the 2000 kW test baseline and records
local evidence. Existing integration scripts require a running simulator when
invoked individually. The security-log test expects the three-event sequence
generated midway through the integration test and is now invoked there.

CP3 remains incomplete: live Wazuh correlation and dashboard validation could
not run because the Docker engine was unavailable. Candidate custom rules are
in `config/wazuh/`; they have not been deployed. See [checkpoint status](docs/checkpoints.md),
[actual results](docs/cp3-test-results.md), [live detection procedure](docs/detection-rules.md),
[investigation](docs/incident-investigation.md) and [response playbook](docs/incident-response-playbook.md).

# Reconstructing an incident

Run from the repository root using the existing virtual environment:

```powershell
.\.venv\Scripts\python.exe tests/run_cp3_lab.py
.\.venv\Scripts\python.exe src/incident_analyzer.py logs/cp3-exercise/20261028T125358Z/incident-events.jsonl --turbine WT-02 --output logs/cp3-report.json
```

The runner requires free localhost ports 5020 and 8081 and stops its own process.
It runs authorised regression commands before the blocked incident and restores
WT-02 to 2000 kW. Do not run it against an existing simulator. A fresh random lab
token is passed to child processes without writing it to evidence.

The analyzer sorts timezone-aware timestamps, counts accepted/rejected requests,
groups turbines and sources, preserves requested values and event IDs, and reports
malformed JSON lines and incomplete events. Optional `--alerts <export.jsonl>` joins
real Wazuh alert IDs through `data.event_id`; missing alerts remain empty, never
inferred from reason codes. A correlation alert can replace the base alert for
the triggering event. Raw archives may contain other non-command events.

An accepted old/new setpoint difference proves a recorded configuration change,
not physical impact. Rejected-only logs cannot independently prove unchanged
equipment state. Use contemporaneous Modbus reads; the runner records these.
Shared lab-token authentication identifies `lab_operator`, not an individual.
Loopback tests establish source addresses, not attacker identity. This utility
does not verify log authenticity, deduplicate copied events or detect missing logs.

## Observed local exercise

The report under `logs/cp3-exercise/20261028T125358Z/incident-report.json` was built
from five actual gateway events, not a fixture. It contains UTC start/end times,
event IDs, requested values, source, outcomes and before/after register reads.
Reproduce the analysis from the adjacent event slice. Evidence is ignored by Git;
retain this local directory. Wazuh rule attribution is pending because Docker was
unavailable during this exercise. No successful compromise or physical impact is
claimed.

# Observed validation, 28 October 2026

Environment: Windows, Python 3.12.10, PyModbus 3.11.2, existing virtual environment.

## Passed

- `python -m unittest discover -s tests -p test_cp3_gateway.py -v`: one test,
  real HTTP handler; five rejections in less than 60 seconds, unchanged in-memory
  setpoint, distinct source/turbine keys.
- `python -m unittest discover -s tests -p test_incident_analyzer.py -v`: three
  tests covering ordering, counts, time bounds, attribution, malformed/incomplete
  input, alert joins and impact classification.
- `python tests/run_cp3_lab.py`: power-control, holding-register, integrated
  security and direct-write scripts passed. On the second run the integrated
  test also invoked the existing security-log validation at the required
  three-event sequence; it passed. Actual script output is saved locally under
  `logs/cp3-exercise/20261028T125520Z/`.
- Five additional real invalid-token requests were rejected; WT-02 holding
  register stayed at 2000 kW and all three SCADA telemetry reads succeeded.
- Candidate XML parsed successfully and contains IDs 100201-100204. This is
  structural validation only, not Wazuh rule validation.

The first exercise evidence is under `logs/cp3-exercise/20261028T125358Z/`.
Its incident interval was 12:54:08.785981-12:54:08.848725 UTC. Five requests from
127.0.0.1 requested 1500 kW on WT-02; all were rejected without a verified actor.
The event slice SHA-256 is
`d56efd80c8e98749037349028c0deb1f40b24a7b34e6b915e352ce90ffd5f2ad`.
Reviewed loopback-only event and report copies are retained in
`evidence/cp3-investigation/`; these contain no operator token.

## Unavailable / unresolved

Docker engine checks failed both inside and outside the restricted session.
The configured Docker Desktop Linux engine pipe was absent. No Docker process
was found in the restricted session; the usual Program Files executable path
was absent. Docker was not installed, containers were not recreated and no Wazuh
data was altered. Compose also reported `OT_LOG_DIR` unset in this terminal.
This does not establish what value earlier running services used.

Consequently the active mount, service status, new archives, manager errors,
rule precedence, observed frequency semantics, reload loss and dashboard index
visibility could not be verified. The historical missing-alert root cause is
unresolved. No live 100204 level 12 alert or new dashboard screenshot is claimed.
Candidate correlation rules remain uninstalled. Follow `detection-rules.md` and
the matrix to finish acceptance once Docker is available.

## Git

The original branch is `main` with an existing GitHub origin. The deleted
`evidence/image.png` and untracked user screenshots/direct-write test were
preserved. Commits use a per-command safe-directory exception because the
execution account differs from the repository owner. Git writes required the
approved elevated execution path; no global Git settings or history were changed.
No push was attempted because explicit push authorization has not been supplied.
The previously tracked hardcoded token was removed from the integration test;
older Git history still contains it, so retire that lab credential before reuse.

# Wazuh detection and live verification

The version-controlled `config/wazuh/windfarm_rules.xml` is a **candidate**, not
an installed or engine-validated change. Rules 100201-100203 preserve the working
86600 parent. Rule 100204 retains frequency 5 / timeframe 60 and changes grouping
to `correlation_key` (canonical socket IP plus validated turbine ID). Old events
without that field cannot satisfy the new grouping. Restart the Python gateway
to load its new schema before testing. Do not alter frequency based on folklore;
measure which live request triggers the installed Wazuh 4.14.9 rule.

Wazuh describes `same_field` as dynamic-field correlation with frequency and
timeframe: https://documentation.wazuh.com/current/user-manual/ruleset/ruleset-xml-syntax/rules.html
That documentation is not proof of this installation's observed threshold.

## Diagnose before installing the candidate

In the Wazuh Compose directory, set `$env:OT_LOG_DIR` to the absolute repository
`logs` directory. Set the same value in the gateway terminal. The logger now
honours it; previously it always wrote into the repository's logs directory.
Neither observation proves the historical alert failure's cause.

```powershell
docker info
docker compose ps
docker compose config --format json > $env:TEMP\windfarm-compose.json
$cid = docker compose ps -q wazuh.manager
docker inspect $cid --format '{{json .Mounts}}'
docker compose exec -T wazuh.manager /var/ossec/bin/wazuh-control status
docker compose exec -T wazuh.manager sh -c 'tail -n 100 /var/ossec/logs/ossec.log'
docker compose exec -T wazuh.manager sh -c 'cat /var/ossec/etc/rules/windfarm_rules.xml'
docker compose exec -T wazuh.manager sh -c 'tail -n 5 /windfarm-logs/ot_events.jsonl'
docker compose exec -T wazuh.manager sh -c 'tail -n 20 /var/ossec/logs/archives/archives.json'
```

Inspect the resolved mount locally; Compose output may include secrets, so do not
commit it. Compare fresh event IDs across host JSONL, container-mounted JSONL,
archives and alerts. Check analysisd and logcollector status/errors. If the host
file changes but the mounted file does not, fix the bind source first. If archives
contain the event but alerts do not, investigate rule loading/precedence and alert
thresholds. A stale rules file requires a configuration reload, not fabricated logs.

Back up the deployed custom rules before copying the candidate into the existing
host `config/windfarm_rules.xml`. Do not replace Compose, certificates or volumes.
Validate with the running manager before restarting it:

```powershell
docker compose exec -T wazuh.manager /var/ossec/bin/wazuh-analysisd -t
docker compose exec -T wazuh.manager /var/ossec/bin/wazuh-logcollector -t
docker compose exec wazuh.manager /var/ossec/bin/wazuh-logtest
```

Paste complete, newly captured gateway JSON lines into one logtest session. Test
single failures, repeated failures and accepted commands. Save phase 2 decoding
and phase 3 matches. Logtest is not live ingestion evidence. Revert the backed-up
rules if validation fails; do not restart with invalid configuration. A manager
restart, if needed after successful validation, interrupts collection: preserve
the source log, record the interval and compare event IDs afterward. Never assume
archives replay automatically or recreate a container to reset correlation state.

## Live acceptance test

With the existing simulator and SIEM running, capture the starting file offsets
and WT-02 holding register 0. Send one invalid-token request to `/command`, then
inspect archives and alerts by its exact event ID. Expect 100202. Wait more than
60 seconds before each independent correlation scenario to clear prior history.
Send exactly five failures from one socket source against WT-02 within 60 seconds;
record each response, UTC time and ID and inspect alerts after each request.
Expect 100204 level 12 at the policy threshold; if it triggers at another count,
record the actual count and adjust/retest the candidate before accepting it.
Read WT-02's holding register afterward and compare with baseline.

Repeat with interleaved turbines and with distinct socket source addresses (a
Python `http.client.HTTPConnection(..., source_address=('127.0.0.2', 0))` can be
used if Windows permits). Forwarded headers are not distinct source identities.
For expiry, send four failures, wait at least 61 seconds, then send one: no
100204 is expected. Use wall-clock arrival delays; editing JSON timestamps does
not validate Wazuh's correlation timer. Finally test an authorised command and
an invalid setpoint, with operator-approved baseline restoration.

```powershell
docker compose exec -T wazuh.manager sh -c 'tail -n 100 /var/ossec/logs/alerts/alerts.json'
docker compose exec -T wazuh.manager sh -c 'tail -n 100 /var/ossec/logs/ossec.log'
```

Save genuine archives/alerts exports locally, then run the incident analyzer with
`--alerts`. Confirm each source event ID survives any reload interval. Any missing
ID is an unresolved collection gap. No live correlation has been verified here.

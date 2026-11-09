# CP4.2 — Wazuh SIEM to Shuffle SOAR Integration

**Project:** Wind Farm OT/SCADA Security Monitoring & Incident Response  
**Checkpoint:** CP4.2  
**Status:** **Completed — PASS**  
**Validated:** 9 November 2026 (UTC)  
**Environment:** Windows 11, Docker Desktop/WSL2, Wazuh 4.14.9, self-hosted Shuffle SOAR, Python wind farm simulator

## 1. Objective

Integrate the Wazuh SIEM with Shuffle SOAR so that a confirmed, correlated OT security alert is automatically delivered to a Shuffle webhook and produces a completed workflow execution. The integration is **detection-only**: it does not issue turbine-control commands, modify setpoints, or initiate an automated response.

**Acceptance criteria:**

1. The simulated OT command gateway rejects invalid authentication attempts without changing turbine power limits.
2. Wazuh detects repeated failures against the same turbine using custom rule `100204` (level 12).
3. Wazuh forwards the matching alert to Shuffle through its built-in `shuffle` integration.
4. The Shuffle workflow receives the real Wazuh alert, executes its test action, and reaches `FINISHED`.

## 2. Architecture and data flow

```text
Wind Farm Simulator (Python)
  └─ HTTP command gateway — 127.0.0.1:8081
       └─ Denied request: WT-02 / invalid token / HTTP 403
            └─ logs/ot_events.jsonl (structured JSON)
                 └─ Wazuh Manager (Docker)
                      └─ Custom correlation rule 100204, level 12
                           └─ Built-in Wazuh Shuffle integration
                                └─ http://host.docker.internal:3001/api/v1/hooks/<webhook-id>
                                     └─ Shuffle: WindFarm-OT-Security-Incident
                                          └─ Change Me / repeat_back_to_me
                                               └─ Workflow execution: FINISHED
```

The Wazuh container uses `host.docker.internal` to reach Shuffle through the Windows host. `localhost` **must not** be used as the webhook hostname inside the Wazuh container; there it would refer to the Wazuh container itself.

## 3. Components and configuration

| Component | Configuration / role |
|---|---|
| Wind farm simulator | Python Modbus TCP server on `127.0.0.1:5020`; HTTP control gateway on `127.0.0.1:8081` |
| Security event source | `logs/ot_events.jsonl`, mounted into Wazuh as `/windfarm-logs/ot_events.jsonl` |
| Wazuh manager | `wazuh/wazuh-manager:4.14.9`, container `single-node-wazuh.manager-1` |
| Detection | Custom rule `100204`, level 12, repeated `AUTH_FAILED` events against the same turbine |
| Shuffle Core | `http://localhost:3001` from Windows |
| Shuffle environment | `Shuffle` (running) |
| Shuffle workflow | `WindFarm-OT-Security-Incident` |
| Initial workflow action | `Change Me` → `repeat_back_to_me` (verification-only) |

### 3.1 Wazuh manager integration configuration

The active file is `/var/ossec/etc/ossec.conf`. The host-mounted source is:

```text
C:\Users\warri\wazuh-docker\single-node\config\wazuh_cluster\wazuh_manager.conf
```

The relevant Wazuh configuration block is:

```xml
<integration>
  <name>shuffle</name>
  <hook_url>http://host.docker.internal:3001/api/v1/hooks/<actual-webhook-id></hook_url>
  <rule_id>100204</rule_id>
  <alert_format>json</alert_format>
</integration>
```

**Security:** The actual webhook identifier is intentionally redacted in this document. Treat the full URL as a secret and avoid committing it to a public repository. Wazuh's configuration can contain multiple top-level `<ossec_config>` blocks; the additional `<localfile>` block for the wind farm JSONL log was preserved.

### 3.2 Configuration persistence

In this Docker deployment, the source Wazuh configuration was bind-mounted at `/wazuh-config-mount/etc/ossec.conf`, while the active configuration resided in a persistent Docker volume at `/var/ossec/etc/ossec.conf`. Editing the Windows source file and restarting the manager did **not** automatically update the active copy.

After backing up the active file, the updated source was copied into place and the manager configuration validated:

```powershell
docker exec single-node-wazuh.manager-1 cp /var/ossec/etc/ossec.conf /var/ossec/etc/ossec.conf.cp4-backup
docker exec single-node-wazuh.manager-1 cp /wazuh-config-mount/etc/ossec.conf /var/ossec/etc/ossec.conf
docker exec single-node-wazuh.manager-1 /var/ossec/bin/wazuh-analysisd -t
docker restart single-node-wazuh.manager-1
```

Later, a separate backup was taken before correcting the URL hostname to `host.docker.internal`. The active file was revalidated, and the manager restarted successfully.

## 4. Implementation and verification

### 4.1 Verify Shuffle locally

Shuffle Core was accessible at `http://localhost:3001`. The Workflows and Apps pages loaded, and the `Shuffle` environment showed as running. A synthetic alert posted directly to the workflow webhook was accepted and successfully executed, establishing that the webhook and workflow engine worked before Wazuh was connected.

### 4.2 Verify Wazuh-to-Shuffle network connectivity

From the Wazuh manager container:

```powershell
docker exec single-node-wazuh.manager-1 curl -I --connect-timeout 5 http://host.docker.internal:3001/
```

**Observed result:** `HTTP/1.1 200 OK`, confirming that the Wazuh container could reach the Shuffle frontend.

### 4.3 Enable Wazuh's built-in Shuffle integration

The manager's active configuration was updated with `<name>shuffle</name>`, the actual webhook endpoint, `<rule_id>100204</rule_id>`, and `<alert_format>json</alert_format>`.

The Wazuh manager log subsequently confirmed:

```text
2026/11/09 21:58:22 wazuh-integratord: INFO: Started (pid: 412).
2026/11/09 21:58:22 wazuh-integratord: INFO: Enabling integration for: 'shuffle'.
```

An incorrect `localhost:3001` webhook hostname was identified in the active configuration and corrected to `host.docker.internal:3001`. The corrected configuration was copied into the active file and verified.

### 4.4 Execute controlled unauthorised-request scenario

The Python simulator was started, and connectivity checks confirmed that the Modbus and gateway ports `5020` and `8081` were reachable.

A PowerShell test sent **six** HTTP `POST /command` requests against `WT-02`, using a deliberately invalid `X-Operator-Token` and requesting a 1500 kW limit. No valid operator credentials were supplied.

Example test payload:

```json
{
  "turbine_id": "WT-02",
  "power_limit_kw": 1500
}
```

**Observed result:** All six requests returned `HTTP 403` and `All requests rejected: True`.

The newly appended JSONL events contained these values:

```json
{
  "event_type": "OT_COMMAND",
  "action": "SET_POWER_LIMIT",
  "result": "REJECTED",
  "reason_code": "AUTH_FAILED",
  "severity": "high",
  "source_ip": "127.0.0.1",
  "turbine_id": "WT-02",
  "requested_limit_kw": 1500,
  "actor": null
}
```

This is an abbreviated representative event, not a verbatim complete log entry. The observed events also carried timestamps, unique event IDs, null old/new limits, and a correlation key for source IP and turbine ID.

### 4.5 Verify Wazuh correlation

A JSON-aware search of `/var/ossec/logs/alerts/alerts.json` confirmed:

```text
Rule 100204 alerts: 1
Latest alert: 2026-11-09T22:29:29.480+0000
```

The result confirms one newly recorded correlated rule `100204` alert for the test run. It is not merely a manually constructed webhook payload.

### 4.6 Verify automatic Shuffle execution

The corresponding Shuffle workflow execution showed:

```text
Status: FINISHED
Source: webhook
Started: 09/11/2026, 22:29:34
Finished: 09/11/2026, 22:30:25
Location: Shuffle
rule_id: 100204
Wazuh alert timestamp: 2026-11-09T22:29:29.480+0000
Title: Wind farm: Repeated authentication failures against the same turbine
Action: Change Me / repeat_back_to_me
```

Unlike the earlier synthetic event, this received message had the structure of Wazuh's forwarded alert, including `pretext: "WAZUH Alert"`, `rule_id`, alert timestamp, title, `text`, and `all_fields`. The workflow action returned the same alert content, and the execution reached `FINISHED`.

## 5. Test results

| Test ID | Validation | Observed outcome | Result |
|---|---|---|---|
| CP4.2-T01 | Shuffle workflow engine | Earlier synthetic webhook execution reached `FINISHED` | PASS |
| CP4.2-T02 | Wazuh container → Shuffle frontend | HTTP 200 from `host.docker.internal:3001` | PASS |
| CP4.2-T03 | Integration configuration | Wazuh integratord enabled `shuffle`; correct URL active | PASS |
| CP4.2-T04 | Invalid-token gateway requests | 6/6 returned HTTP 403 | PASS |
| CP4.2-T05 | Structured OT audit logging | Six fresh `AUTH_FAILED` events for WT-02 | PASS |
| CP4.2-T06 | Wazuh correlation | Rule `100204` generated at 22:29:29 UTC | PASS |
| CP4.2-T07 | Automatic alert forwarding | Real Wazuh alert received by Shuffle webhook | PASS |
| CP4.2-T08 | Workflow processing | `repeat_back_to_me` action; workflow `FINISHED` | PASS |

## 6. Troubleshooting and resolutions

| Issue | Root cause / finding | Resolution |
|---|---|---|
| Shuffle frontend initially failed | Locally inspected image had empty entrypoint and application entry file; subsequently a pull showed nonempty files | Restored functional frontend and verified login |
| OpenSearch startup failed | Initial admin password missing | Configured password in `.env`, passed it through Compose and recreated OpenSearch |
| Shuffle execution stuck in `EXECUTING` | Orborus worker execution configuration and runtime issues; precise contribution of Tenzir errors not conclusively isolated | Set `SHUFFLE_SWARM_CONFIG` to empty for non-Swarm Compose runtime; subsequent workflow reached `FINISHED` |
| Wazuh integration not visible | Active `/var/ossec/etc/ossec.conf` differed from host-mounted source | Backed up and copied corrected source into active configuration |
| Wazuh could not reach `localhost` webhook | `localhost` inside Wazuh referred to itself | Changed URL hostname to `host.docker.internal` |
| Docker Desktop would not launch via default path | Docker Desktop was installed in the user-local Programs directory | Launched the correct executable; existing volumes and containers remained intact |
| `OT_LOG_DIR` Compose warning | Environment variable was unset in the shell running Compose | Existing bind mount was verified; **follow-up:** configure this variable before recreating Wazuh containers |

## 7. Safety and operational constraints

- All requests in the final test used an **invalid** operator token and returned HTTP 403.
- The demonstrated CP4.2 workflow is **detection-only** and contains no automated turbine actuation or network blocking.
- The rule filter limits forwarding to Wazuh rule `100204`.
- The webhook URL should not be committed to a public repository.
- Do not remove Wazuh or Shuffle Docker volumes as part of further configuration changes.
- Future active-response logic must include an OT-safe human approval step (CP4.5).
- The test demonstrated rejected requests and successful alert flow. An independent post-test register comparison was not captured in the supplied final evidence; do not describe it as separately verified here.

## 8. Evidence checklist

Store screenshots and redacted log excerpts under a project evidence folder, using names such as:

```text
evidence/
  cp4.2_gateway_6x403.png
  cp4.2_ot_events_2026-11-09.png
  cp4.2_wazuh_rule_100204.png
  cp4.2_wazuh_integratord_enabled.png
  cp4.2_shuffle_execution_finished.png
```

These are **suggested filenames**, not a claim that the files already exist. Redact webhook identifiers, passwords, keys, and other secrets before sharing screenshots.

## 9. Completion statement

**CP4.2 is complete.** On 9 November 2026, six unauthorised WT-02 gateway requests were rejected with HTTP 403, a Wazuh custom correlation alert (`100204`) was generated, the alert was automatically forwarded via Wazuh's Shuffle integration, and the Shuffle workflow ran its test action and finished successfully. This verifies the live, detection-only **Wind Farm → Wazuh SIEM → Shuffle SOAR** pipeline.

**Next checkpoint: CP4.3 — Alert enrichment.** Extract structured incident fields from Wazuh's forwarded payload, add context, and produce an investigation-ready incident record without performing automatic turbine-control actions.

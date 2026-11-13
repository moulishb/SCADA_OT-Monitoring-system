# CP5.1 — Incident Response Report

**Project:** Wind Farm OT/SCADA Security Monitoring & Incident Response  
**Document type:** Technical incident-response case study (simulated environment)  
**Case reference:** WF-IR-2026-11-11-001  
**Wazuh alert / incident ID:** `1794425821.4188`  
**Incident date:** 11 November 2026 (UTC)  
**Report prepared:** 13 November 2026  
**Classification:** P1 — Critical OT Security Incident (lab workflow classification)  
**Status:** Detection, escalation and authorisation workflow validated; investigation itself not performed as part of CP4

> **Scope note:** This report documents a controlled simulation, not an intrusion into an operational wind farm. P1 is the lab's classification, not a declaration of production operational impact.

## 1. Executive summary

A controlled series of unauthorised requests targeted the simulated `WT-02` turbine's HTTP control gateway. The requests sought a `SET_POWER_LIMIT` action with a requested limit of `1500 kW`, but failed authentication and were recorded as `REJECTED` with reason `AUTH_FAILED`. Wazuh SIEM correlated repeated authentication failures and generated rule **100204**, level **12**, for the same turbine. At **19:37:01.491 UTC on 11 November 2026**, Wazuh timestamped the alert; Shuffle SOAR automatically received it through its webhook at **19:37:03 UTC**.

Shuffle normalised the alert, classified it as `CRITICAL_OT_SECURITY_INCIDENT` with priority `P1`, and paused for human approval. The `admin` operator approved an investigation. Shuffle recorded `INVESTIGATION_AUTHORISED` and finished at **19:38:13 UTC**. The recorded response explicitly retained `automated_turbine_control: false`.

**Outcome:** The SIEM-to-SOAR human-approval workflow worked end to end. The evidence supports successful detection, routing, escalation, approval and workflow completion. It does **not** establish that a forensic investigation, separate evidence export or incident remediation was completed.

## 2. Environment and relevant assets

| Component | Function | Relevant detail |
|---|---|---|
| Simulated wind turbines | OT process model | `WT-01`, `WT-02`, `WT-03` |
| Python Modbus TCP server | Simulated telemetry and control registers | Port `5020` |
| SCADA client | Reads turbine state and aggregate power | Lab monitoring client |
| Authenticated HTTP command gateway | Controls access to simulated turbine power-limit operations | Port `8081`; rejects invalid authentication |
| OT audit log | Structured security event capture | JSONL, including `OT_COMMAND`, `AUTH_FAILED` |
| Wazuh SIEM | Log ingestion and correlation | Version 4.14.9; rule `100204`, level `12` |
| Shuffle SOAR | Incident-response orchestration | Local Docker deployment; webhook and human-approval workflow |

**Affected simulated asset:** `WT-02`. **Observed source address:** `127.0.0.1` (local test source, not an external attacker IP). **Affected interface:** HTTP command gateway's `SET_POWER_LIMIT` endpoint. **Requested limit:** `1500 kW` (a *requested* value, not evidence that the limit changed).

## 3. Detection scenario and rule

The test simulated repeated unauthorised attempts to modify a turbine power limit. The gateway's authentication guard was designed to reject requests with an invalid operator token. Rejections produced structured audit entries that Wazuh ingested.

**Relevant alert fields from the final validation:**

```json
{
  "id": "1794425821.4188",
  "timestamp": "2026-11-11T19:37:01.491+0000",
  "rule_id": "100204",
  "rule_level": "12",
  "rule_description": "Wind farm: Repeated authentication failures against the same turbine",
  "turbine_id": "WT-02",
  "source_ip": "127.0.0.1",
  "event_id": "07b77b0d-d332-4266-9edc-cf9a7da76eb3",
  "event_type": "OT_COMMAND",
  "action": "SET_POWER_LIMIT",
  "result": "REJECTED",
  "reason_code": "AUTH_FAILED",
  "requested_limit_kw": "1500"
}
```

Rule `100204` was configured to correlate **five matching authentication failures within 60 seconds**, grouped by the relevant turbine context. During CP4.6, a fresh generated alert demonstrated that this rule could trigger the Shuffle webhook without manual execution arguments.

## 4. Reconstructed incident timeline

All times UTC, 11 November 2026. Times below come from the final execution and alert output; intermediate action timestamps were not independently supplied for this incident.

| Time | Event | Evidence / interpretation |
|---|---|---|
| Before 19:37:01 | Simulated invalid-token command attempts against `WT-02` | Controlled CP4.6 test; audit result `REJECTED` / `AUTH_FAILED` |
| **19:37:01.491** | Wazuh critical correlation alert timestamp | Rule `100204`, level `12`, alert `1794425821.4188` |
| **19:37:03** | Shuffle main execution started | Source explicitly shown as `webhook` |
| During execution | `Normalize_Wazuh_Alert` completed | Created 18-field structured incident record |
| During execution | `Escalate_Critical_Incident` completed | Classified incident `CRITICAL_OT_SECURITY_INCIDENT`, priority `P1` |
| During execution | `User_Input_1` presented human decision | Workflow paused pending input; `admin` approved |
| During execution | `Record_Approved_Investigation` completed | Recorded `APPROVED`, `INVESTIGATION_AUTHORISED` |
| **19:38:13** | Shuffle workflow finished | Overall status `FINISHED` |

**Measured intervals:** Wazuh alert timestamp to Shuffle execution start was approximately **1.5 seconds**. Shuffle execution start to finish was **70 seconds**, **including** the human approval step. This is not an unattended automation latency benchmark.

## 5. Triage and incident classification

Shuffle's normalisation step mapped the Wazuh webhook's fields into a consistent incident record, retaining the alert ID, source, turbine, action, rejection result and detection rule. The classification path required the matching rule ID `100204` **and** Wazuh rule level `12`.

The escalation action then emitted:

```json
{
  "incident_id": "1794425821.4188",
  "turbine_id": "WT-02",
  "source_ip": "127.0.0.1",
  "rule_id": "100204",
  "rule_level": "12",
  "classification": "CRITICAL_OT_SECURITY_INCIDENT",
  "priority": "P1",
  "escalation": "SECURITY_OPERATOR_REVIEW",
  "status": "PENDING_HUMAN_APPROVAL",
  "recommended_response": "Investigate authentication failures and preserve evidence",
  "automated_turbine_control": false
}
```

This lab classification is appropriate to the simulated threat scenario: repeated failed control attempts merit investigation even where authentication blocked the requests. The records supplied do not demonstrate physical safety impact, power interruption, malicious attribution or a successful turbine setpoint change.

## 6. Response actions performed

### 6.1 Automated actions

1. **Alert intake:** Wazuh forwarded rule `100204` to the existing Shuffle webhook.
2. **Normalisation:** Shuffle converted the incoming event to its standard incident fields.
3. **Escalation:** The workflow recorded `P1` and requested operator review.
4. **Approval gate:** `User_Input_1` paused the main workflow until a decision was supplied.
5. **Authorisation record:** Following approval, the final action recorded the approved investigation status.

### 6.2 Human decision

Shuffle's final execution recorded:

```json
{
  "success": true,
  "source": "userinput",
  "reason": "User approved the input",
  "click_info": {
    "clicked": true,
    "user": "admin"
  }
}
```

The approved result was:

```json
{
  "incident_id": "1794425821.4188",
  "decision": "APPROVED",
  "status": "INVESTIGATION_AUTHORISED",
  "action": "Security analyst may review logs and preserve evidence",
  "automated_turbine_control": false
}
```

**Interpretation:** This is an approval and audit record in Shuffle. It is not proof that an analyst subsequently reviewed the logs or preserved files in an independent evidence store.

### 6.3 OT safety boundary

The response workflow contains no authorised turbine-control action. Its output explicitly uses `automated_turbine_control: false`. The attempted `1500 kW` value is recorded only as an untrusted request from the simulated security event. Do not interpret it as a command executed by Shuffle or a confirmed power-limit change.

## 7. Validation and controls evidence

The following CP4.6 tests validate the behaviour of the workflow:

| Test | Execution / input | Observed outcome | Assessment |
|---|---|---|---|
| Human rejection | Saved critical Wazuh alert; execution 18:35:19–18:36:15 UTC | `User declined the input`; approved-investigation action absent; `FINISHED` | **PASS** |
| Noncritical filtering | Synthetic rule `100201`, level `5`; execution 19:00:59–19:01:46 UTC | Normalisation succeeded; no P1 escalation, approval or approved investigation action | **PASS** |
| Fresh webhook end to end | New Wazuh alert `1794425821.4188`; execution 19:37:03–19:38:13 UTC | Source `webhook`; critical escalation; `admin` approval; investigation-authorisation record; `FINISHED` | **PASS** |

The noncritical test was intentionally synthetic and tested routing conditions, not Wazuh's creation of a rule `100201` alert.

## 8. Findings and limitations

**Verified findings**

- Invalid authenticated-control attempts can be rejected and represented as `AUTH_FAILED` audit events.
- Rule `100204` can correlate repeated failures and automatically trigger Shuffle.
- The incident workflow can normalise, classify, pause, resume and finish following human approval.
- A rejected human decision does not execute `Record_Approved_Investigation` in the observed test.
- Noncritical synthetic test data does not pass into the P1 path.

**Limits of the evidence**

- The simulation used a loopback source address; the alert does not establish an external adversary.
- No production turbines, PLCs or live grid infrastructure were involved.
- No independently verified forensic acquisition, evidence hash, case ticket or external archive was demonstrated.
- No actual remediation or restoration step was performed or claimed.
- A normalisation field, `operator_approval_required`, was statically `true` even in the noncritical test, although conditions prevented escalation. This should be derived from classification in a future revision.
- Debugging exposed some Shuffle platform warnings (including worker reruns, timestamp parsing and Tenzir networking); final successful executions do not establish that every underlying warning has been remediated.
- The supplied execution output verifies the decision record, but a separate gateway/Modbus before-and-after state check was not provided for the final run.

## 9. Recommended follow-up (outside CP5.1 acceptance scope)

1. Derive `operator_approval_required` from actual rule classification instead of a constant.
2. Send approved and declined decisions to an external incident-management system with immutable timestamps and case identifiers.
3. Add an optional evidence collection playbook that preserves source logs, file hashes, acquisition timestamps and chain-of-custody records **after** appropriate authorisation.
4. Review Shuffle authentication warnings, worker lifecycle logs and Tenzir network errors as a platform-maintenance task.
5. For future controlled tests, record explicit gateway HTTP response counts and a before/after turbine setpoint snapshot.
6. Redact webhook URLs, callback authorisation values and API tokens from public GitHub evidence.

These are enhancements, not claims of completed functionality.

## 10. Conclusion and disposition

The simulated repeated unauthorised control scenario was detected by Wazuh and automatically forwarded into Shuffle. Shuffle performed successful normalisation and P1 escalation, paused for a human decision, recorded approval from `admin` and completed the incident workflow with investigation authorisation. The final run finished at **19:38:13 UTC on 11 November 2026**.

**Disposition:** **SOAR workflow validation successful.** The gateway rejected the observed unauthorised requests, and the SOAR workflow issued no turbine-control action. An actual forensic investigation and remediation are **not** represented as completed.

**CP5.1 result:** Incident response report drafted from verified lab evidence. Remaining CP5 deliverables: screenshots/evidence indexing, repository README and final documentation review.

---

### Appendix A — Evidence references to retain

- **Wazuh:** Rule `100204` alert, level `12`, timestamp `2026-11-11T19:37:01.491+0000`, alert ID `1794425821.4188`.
- **Shuffle main workflow:** `WindFarm-OT-Security-Incident`, final execution source `webhook`, start `19:37:03`, finish `19:38:13`, status `FINISHED`.
- **Normalisation:** 18-field `Normalize_Wazuh_Alert` output identifying `WT-02`, `AUTH_FAILED`, `REJECTED`.
- **P1 escalation:** `Escalate_Critical_Incident` output with `PENDING_HUMAN_APPROVAL`.
- **Human decision:** `User_Input_1` with `User approved the input`, operator `admin`.
- **Final audit:** `Record_Approved_Investigation` with `INVESTIGATION_AUTHORISED`.
- **Negative paths:** 18:35 rejection run; 19:00 noncritical synthetic input run.

The actual screenshots should be attached and linked during CP5.2; none are represented as attached to this report yet.

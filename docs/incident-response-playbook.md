# WF-001 — OT Security Incident Response Playbook

**Project:** Wind Farm OT/SCADA Security Monitoring & Incident Response  
**Incident:** WF-001  
**Environment:** Simulated three-turbine wind farm  
**Incident date:** 3 November 2026  
**Initial priority:** High — repeated authentication failures  
**Operational impact:** No confirmed impact from observed commands

## 1. Purpose

Define a repeatable procedure for handling suspicious or unauthorised industrial control requests in the simulated wind farm environment.

The response must prioritise safe turbine operation, evidence preservation and controlled recovery.

## 2. Detection and Identification

The command gateway recorded six rejected requests targeting WT-02, each attempting to set the power limit to 1,500 kW.

All six events had the reason code `AUTH_FAILED`.

Wazuh detected the individual events using rule 100202 and generated a correlated level 12 alert using rule 100204.

## 3. Triage

The analyst should:

- Verify the alert and associated event IDs.
- Identify the target turbine and requested command.
- Examine source IP, timestamp and request outcome.
- Determine whether any relevant command succeeded.
- Review turbine configuration and operational status.
- Escalate if successful unauthorised control, suspicious configuration changes or operational abnormalities are observed.

**WF-001 finding:** Six rejected requests, zero accepted requests within the investigated window.

## 4. Evidence Preservation

Preserve:

- Original JSONL security audit records.
- Incident-specific event timeline.
- Wazuh alert records.
- Relevant rule configuration.
- Turbine setpoint verification.
- Investigation notes and evidence hashes.

Record the collection time, file source and any transformations applied to evidence.

## 5. Containment Decision

Because the observed requests were rejected, the initial response is to maintain monitoring and investigate the source.

Recommended actions:

- Review the origin of the requests.
- Review operator token handling and access policies.
- Increase scrutiny of WT-02 control events.
- Consider credential rotation if compromise becomes credible.

Restricting gateway access or changing credentials requires approval because legitimate control operations could be affected.

**Decision:** No automatic turbine shutdown or operational isolation.

## 6. Recovery Verification

Before closing the response exercise:

1. Verify Modbus/TCP connectivity.
2. Verify telemetry from WT-01, WT-02 and WT-03.
3. Confirm turbine power limits match the expected authorised configuration.
4. Confirm relevant security events are still collected by Wazuh.
5. Confirm the detection rules remain operational.
6. Record whether any services required restoration.

## 7. Closure Criteria

The exercise can be closed when:

- Relevant evidence has been preserved.
- The incident timeline is complete.
- No successful unauthorised command was identified in the investigated window.
- Current turbine configuration is verified.
- Monitoring remains operational.
- Outstanding risks and limitations are documented.

## 8. Lessons Learned

The monitoring system successfully identified and correlated repeated unauthorised control attempts.

Application-level authorisation prevented the observed requests from reaching turbine control logic.

The incident demonstrates the importance of contextual investigation: repeated authentication failures require review, but they do not automatically prove compromise or justify disruptive containment.

## 9. Limitations

This exercise uses simulated turbines, localhost command requests and software-based Modbus communication.

The local source IP does not identify a real external attacker.

The available investigation records support conclusions about observed gateway requests, not every possible industrial protocol action or historical equipment state.
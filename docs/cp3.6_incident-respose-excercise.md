# CP3.6 — Incident Response Exercise

**Incident:** WF-001  
**Exercise type:** Simulated OT security incident response  
**Date:** 3 November 2026  
**Status:** Pending recovery verification

## Scenario

Repeated unauthorised requests targeted the WT-02 power-limit control through the application command gateway.

## Investigation Findings

- Six rejected commands.
- No accepted commands in the selected incident window.
- Wazuh correlation rule 100204 generated a level 12 alert.
- No confirmed successful unauthorised setpoint modification.
- Subsequent holding-register test showed all three turbines at 2,000 kW.

## Response Decisions

**Evidence preservation:** Preserve the incident timeline and Wazuh alert records.

**Containment:** Maintain operational availability. Recommend credential and access review. Do not automatically shut down turbines.

**Escalation:** Treat the repeated attempts as a high-priority security investigation because control commands targeted an OT asset.

## Recovery Verification

- Modbus connectivity: Pending fresh verification
- Three-turbine SCADA telemetry: Pending verification
- Expected turbine setpoints: Pending fresh verification
- Wazuh services: Pending verification
- Security event monitoring: Pending verification

## Outcome

To be finalised after completing recovery checks. Document any failed verification and the corrective action taken.

## Lessons Learned

The lab demonstrates detection, investigation and response decision-making without requiring disruptive industrial control actions.

Future improvements include stronger operator identity, enhanced network-level monitoring, more complete state history and automated alert escalation with human approval.

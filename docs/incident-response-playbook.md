# Unauthorised turbine control attempts

Scope: localhost Python simulation. The response owner is the lab operator.
No procedure here isolates hardware or controls production equipment.

1. **Identify.** Start with rule 100202 or 100204 and retain the alert's full JSON.
   Match `data.event_id` to the gateway log. Record UTC timestamps, turbine,
   socket source IP, requested setpoint and result. A failed token has no verified
   actor; a source IP alone does not identify a person.
2. **Triage.** Count failures per source and turbine within 60 seconds. Check for
   COMMAND_APPLIED events before and after the burst. Escalate to the operator
   immediately if an unexpected accepted change, lost telemetry or changed
   register is observed. Treat repeated blocked requests as suspicious activity,
   not proof of compromise.
3. **Preserve evidence before changing configuration.** Copy the relevant JSONL
   interval, Wazuh archives and alerts, active rules and manager errors into a
   dated local evidence directory. Record SHA-256 hashes, capture time and commands.
   Keep originals. Do not truncate logs, delete indices or recreate containers.
   Review exports for credentials and personal information before committing them.
4. **Contain with operator approval.** Options are rotating the lab token and
   restarting the gateway during a planned interruption, or restricting access
   to the gateway. Keep telemetry available where possible. Record the approval,
   action, time and rollback. Do not automatically stop turbines or disable safety
   behaviour. This project implements no automatic containment.
5. **Recover.** Read holding register 0 on devices 1-3 and compare with the last
   operator-approved baseline; do not assume 2000 kW is always intended. Read all
   five telemetry registers and check SCADA output. Verify a failed token remains
   rejected. Test an authorised change only in the lab with an agreed setpoint,
   then restore and verify the baseline. Confirm log ingestion and Wazuh alerts
   separately; readable telemetry does not prove SIEM recovery.
6. **Close.** The operator confirms expected setpoints, working telemetry,
   functioning detection, preserved evidence and no unexplained accepted changes.
   Record unresolved questions, detection gaps and follow-up actions. Keep an
   incident open if required Wazuh validation is unavailable.

## Exercise record, 28 October 2026

`tests/run_cp3_lab.py` started an isolated localhost simulator, ran CP2 regressions
and sent five invalid-token commands against WT-02. All five returned 403; the
holding register was 2000 kW before and after; all three telemetry reads succeeded.
No containment action was applied. The runner stopped only the simulator process
it started. Report and raw evidence are under
`logs/cp3-exercise/20261028T125358Z/`. See `incident-investigation.md` for reproduction.

This validates rejection, local evidence preservation and recovery reads. Wazuh
alert handling, containment execution and full incident closure remain pending.

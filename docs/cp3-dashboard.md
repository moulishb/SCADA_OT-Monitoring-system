# Native Wazuh monitoring views (pending execution)

Use Threat Hunting with the existing `wazuh-alerts-*` index pattern and an absolute
time range covering the exercise (timestamps in the report are UTC). Start with
`rule.groups: windfarm` and display timestamp, rule.id, rule.level,
data.turbine_id, data.source_ip, data.reason_code, data.result and data.event_id.

Save searches for `rule.id: 100202`, `rule.id: 100201`, `rule.id: 100203`, and
`rule.id: 100204`. Add `data.turbine_id: "WT-02"` for the incident view. Search
by a captured `data.event_id` to prove index visibility independently of logtest.

Use native visualizations for counts by rule ID, counts by turbine, counts by
severity and a date histogram split by rule ID. Keep the common windfarm filter
and time range. Save a dashboard with these panels and the event table. Confirm
that 100204 is level 12 and linked to a real gateway event.

Capture actual screenshots of the filters, absolute time range, event detail and
panels under `evidence/cp3-dashboard/` after reviewing for secrets. Existing user
screenshots are preserved; they have not been reclassified as new validation.
No dashboard was changed or screenshot manufactured in this session. Dashboard
access and new alert indexing remain pending while Docker is unavailable.

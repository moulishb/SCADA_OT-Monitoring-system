# CP3.4 — Repeated authentication-failure event correlation

**Status:** Positive Logtest and live test passed 3 November 2026. Dashboard and negative isolation tests remain pending in the conversation.

## Objective
Escalate multiple rejected turbine-control commands into a high-priority, time-bounded alert; avoid combining unrelated turbine or source events.

## Rules
- Base rule 100202: individual `AUTH_FAILED`, level 8.
- Correlation rule 100204: `frequency=5`, `timeframe=60`, `<if_matched_sid>100202</if_matched_sid>`, `<same_field>turbine_id</same_field>`, level 12.
- Newer live events include a `correlation_key` with source and turbine, but the last shown rule file still groups only by `turbine_id`. The live key appeared in decoded Wazuh data as an array. Do not claim source-IP isolation until tested or corrected.

## Positive Logtest result
On 3 Nov 2026, five matching JSON samples in a single `wazuh-logtest` session produced:
- first four: rule 100202, level 8
- fifth: rule 100204, level 12

## Live integration result
The uploaded `evidence/CP3_4_live_alerts_2026-11-03.txt` contains the real `alerts.json` output. At 16:26:52.660180 UTC the first failed command was created, and at 16:27:02.541 UTC the level 12 correlation alert was recorded. The event on which it fired was generated at 16:27:01.738365 UTC. A sixth failed command followed and matched 100202.

All six test events were local to `127.0.0.1`, targeted WT-02 and requested 1500 kW. Every request was rejected with `AUTH_FAILED`; no successful control change is evidenced in this alert stream.

## Outstanding acceptance tests
1. Confirm rule 100204 is visible in Wazuh dashboard Threat Hunting and capture screenshot.
2. In a fresh Logtest session, submit 2 WT-01 + 2 WT-02 failures; verify **no** correlated alert yet. Add 3 more WT-02 failures; verify only WT-02 crosses threshold.
3. Verify separate source identities do not aggregate. The current localhost setup cannot test truly distinct network sources without adjusted test fixtures or lab network simulation; document the scope.
4. Verify five failures separated beyond the 60-second window do not match.
5. Validate an accepted control command does not contribute to authentication-failure correlation.
6. Commit verified work after reviewing staged changes; do not commit credentials or runtime logs.

## Recommended honest status label
**CP3.4: positive correlation path verified; negative tests and dashboard confirmation pending.**

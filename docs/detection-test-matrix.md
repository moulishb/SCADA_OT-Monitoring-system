# Detection test matrix

| Scenario | Expected | Observed in this session |
|---|---|---|
| Authorised change | HTTP 200, 100201, intended register update | HTTP/register passed; Wazuh pending |
| Single bad token | HTTP 403, 100202, no change | HTTP/register passed; Wazuh pending |
| Invalid setpoint | HTTP 400, 100203, no change | HTTP/register passed; Wazuh pending |
| Five same-source WT-02 failures in 60 s | 100204 level 12; no setpoint change | Five 403s/no change passed; Wazuh pending |
| Interleaved turbines below threshold | No 100204 | Key separation passed; Wazuh pending |
| Distinct socket sources below threshold | No 100204 | Key separation passed; live distinct-source test pending |
| Four failures, 61 s pause, one failure | No 100204 | Pending; no engine available |
| Accepted command amid failures | Must not count as AUTH_FAILED | Gateway classification passed; Wazuh pending |
| Direct Modbus single-register write | Exception/no persistent setpoint change | Passed immediately and after refresh |
| Malformed/incomplete investigation input | Report skipped records without false attribution | Three analyzer tests passed |
| Reload/restart collection interval | All event IDs retained | Pending |

Key separation tests validate audit schema, not Wazuh counters. Follow the live
procedure in `detection-rules.md`; retain raw output and report failures honestly.

# Monitoring & alerting setup

Poll `GET /health` every 30s and `GET /metrics` (operator key) every 60s.

## Alert rules

| Signal | Threshold | Action |
|--------|-----------|--------|
| `status != healthy` for 2 consecutive polls | degraded/unhealthy | Page on-call; check `dependencies` field |
| `error_rate` | > `MCP_ERROR_RATE_THRESHOLD` (default 0.1) for 5 min | Investigate recent error types on `/dashboard` |
| `latency_ms.p95` | > 2000 ms for 5 min | Check cache hit ratio and store latency |
| `rate_limited_total` growth | sudden spike | Identify abusive `key_id` in audit log |
| `circuit_states.mock_store != closed` | any occurrence | Dependency incident; verify auto-recovery |

## Backup & recovery

- Mock datasets reset to seed on every startup by design; there is no
  business-data backup to manage.
- Back up: `.env` secrets (vault), audit-log exports (see below), container
  image tags.
- Export audit trail: call the audit read path with an `admin`/`auditor` key
  and persist the JSON daily.
- Recovery: redeploy the container image, mount secrets, confirm
  `/health` returns `healthy`.

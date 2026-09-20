# Monitoring & Alerting Guide

## Metrics Interpretation

The MCP Portfolio exposes metrics at `GET /metrics` (requires operator API key).

### Request Counts

The `requests_total` map contains `{endpoint}:{outcome}` keys with cumulative counts:

| Key Pattern | Meaning |
|-------------|---------|
| `tool_name:success` | Tool call completed successfully |
| `tool_name:failed` | Tool call raised an exception |
| `tool_name:denied` | Tool call rejected by RBAC |

**Use**: Track throughput by tool. A sudden drop may indicate upstream failures or client misconfiguration.

### Latency Percentiles

```json
{
  "latency_ms": {
    "p50": 12.3,
    "p95": 87.6,
    "mean": 24.1
  }
}
```

- **p50** — Median response time; target < 50 ms for most tools.
- **p95** — Tail latency; target < 2 s. Spikes here indicate hot paths or downstream contention.
- **mean** — Overall average; useful for capacity planning.

### Error Rate

`error_rate` = `(failed + denied) / total_requests`. The threshold is configurable via `MCP_PORTFOLIO_ERROR_RATE_THRESHOLD` (default 0.10 = 10%).

### Circuit Breaker

`circuit_states` shows the current state of the mock-store circuit breaker:

| State | Meaning |
|-------|---------|
| `closed` | Normal operation |
| `half-open` | Testing recovery after timeout |
| `open` | Failing; calls rejected immediately |

### Cache

```json
{
  "cache": { "hits": 1420, "misses": 38 }
}
```

**Hit ratio** = `hits / (hits + miss)` — target > 90% for stable workloads.

---

## Alerting Rules

Configure alerts in your monitoring stack (Prometheus Alertmanager, PagerDuty, etc.):

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| **HighErrorRate** | `error_rate > 0.10` for 5 min | Critical | Page on-call; investigate tool failures |
| **LatencyP95High** | `p95 > 2000 ms` for 10 min | Warning | Check downstream mock-store latency |
| **CircuitOpen** | `circuit_states.mock_store == "open"` for 3 min | Critical | Restart server or investigate root cause |
| **AuditSinkBroken** | `dependencies.audit_sink == "broken"` | Warning | Audit log unavailable; data not persisted |
| **RateLimitSpike** | `rate_limited_total` increases > 50/min | Warning | Review client rate or increase limits |
| **CacheDegraded** | `cache.hit_ratio < 0.70` for 15 min | Info | Check TTL config or data volatility |

---

## Dashboard Usage

Access the HTML dashboard at `GET /dashboard` (requires operator API key).

### Panels

1. **Status Banner** — Current health: `healthy`, `degraded`, or `unhealthy`.
2. **Uptime** — Seconds since last server start.
3. **Request Summary** — Total requests, error rate, and p95 latency at a glance.
4. **Recent Errors** — Last 10 sanitized error records (step, error type, timestamp).

### Refresh Strategy

- **Real-time ops**: Poll `/health` every 5–10 s from an external uptime monitor (UptimeRobot, Checkly).
- **Dashboard review**: Load `/dashboard` every 60 s during active incidents.
- **Metrics export**: Scrape `/metrics` every 30 s into Prometheus/Grafana for historical analysis.

---

## Incident Response Procedures

### 1. Health Check Fails (`/health` returns unhealthy)

1. Check container status: `docker ps` / `docker logs mcp-portfolio`.
2. Verify the ops port (8001) is reachable: `curl http://localhost:8001/health`.
3. If `audit_sink == "broken"`, the audit log is failing — restart the server.
4. If `mock_store` is `open`, the circuit breaker tripped — wait 30 s for half-open or restart.

### 2. Error Rate > 10%

1. Pull `/metrics` and identify which `{endpoint}:failed` keys dominate.
2. Check recent errors in the dashboard or logs.
3. If the issue is transient (downstream blip), the circuit breaker + retry logic should self-heal.
4. If persistent, restart the container and monitor.

### 3. Latency Spike (p95 > 2 s)

1. Check `mock_latency_ms` config — it may be set too high.
2. Inspect Docker resource usage: `docker stats mcp-portfolio`.
3. Review connection pool or cache settings; see `scaling-guide.md`.
4. If CPU/memory bounded, increase container limits or scale horizontally.

### 4. TLS Certificate Expiry

1. Check cert expiry: `openssl x509 -enddate -noout -in /etc/ssl/certs/server.crt`.
2. Renew via your CA (Let's Encrypt, internal PKI).
3. Reload nginx: `nginx -s reload`.
4. Set a calendar reminder 30 days before next expiry.

### Post-Incident

- Export audit logs: `curl -H "X-Api-Key: <key>" http://localhost:8001/dashboard`.
- Record timestamps, root cause, and resolution in your incident tracker.
- Review alerting thresholds if the incident was not caught early enough.

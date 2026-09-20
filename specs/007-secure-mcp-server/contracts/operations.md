# Contract: Operations (Health, Metrics, Errors)

**Date**: 2026-09-18 | **Spec refs**: FR-009–FR-015

Served by the `fastapi` sidecar (`ops_app.py`). Route handlers are thin wrappers over plain functions (unit-testable without HTTP). Auth: `operator`/`admin` API key via `X-API-Key` header; business-data roles receive `FORBIDDEN` on ops endpoints except `/health` liveness (public, no data).

## `GET /health`

**Response**:

```json
{
  "status": "healthy | degraded | unhealthy",
  "uptime_seconds": 1234.5,
  "dependencies": { "mock_store": "closed", "audit_sink": "ok" },
  "version": "0.1.0"
}
```

- `degraded`: any circuit open OR trailing error rate above `Settings.ERROR_RATE_THRESHOLD`.
- `unhealthy`: audit sink unavailable (fail-closed) or store uninitialized.
- No authentication required; contains zero business data.

## `GET /metrics`

**Auth**: `admin` or `operator` key required.

**Response** (JSON; Prometheus-style text available via `?format=text`):

```json
{
  "requests_total": { "resource.read:success": 120, "tool.execute:denied": 3 },
  "latency_ms": { "p50": 4.2, "p95": 18.7 },
  "error_rate": 0.012,
  "rate_limited_total": 5,
  "circuit_states": { "mock_store": "closed" },
  "cache": { "hits": 80, "misses": 40 }
}
```

## `GET /dashboard`

**Auth**: `admin` or `operator` key required. Server-rendered HTML summary: current status, key metrics, circuit states, recent (sanitized) error entries. No PII rendered.

## Rate limiting contract (HTTP + MCP)

- Token bucket per API key: `RATE_LIMIT_PER_MINUTE` sustained, `RATE_LIMIT_BURST` burst (via `Settings`).
- Excess → `429` (HTTP) / `RATE_LIMITED` (MCP) with `retryAfterMs`; normal clients unaffected.

## Transport security contract

- STDIO transport: no network layer; host process isolation applies.
- HTTP transport + sidecar: TLS terminated at deployment ingress (see deployment guide); `TLS_ENABLED`/`TLS_CERT_PATH`/`TLS_KEY_PATH` settings surface reserved for direct termination via stdlib `ssl`.
- Secrets exclusively via environment/`.env`; responses and logs never contain keys or PII beyond the caller's authorized view.

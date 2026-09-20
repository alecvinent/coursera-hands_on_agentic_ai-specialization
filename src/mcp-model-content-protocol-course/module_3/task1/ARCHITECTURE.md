# Architecture: Secure MCP Server with Monitoring

## Decision log

1. **Official `mcp` SDK v2 (`MCPServer`)** — canonical protocol implementation
   (resources, tools, STDIO + Streamable HTTP); hand-rolled JSON-RPC and a
   REST-only API were rejected (conformance risk / not MCP-compliant).
2. **Single-credential server binding** — the server is built for one API key;
   handlers close over its `AuthContext`. Explicit and auditable for local and
   demo use; production multi-tenancy should adopt MCP OAuth Authorization.
3. **RBAC before state changes** — permission checks run before validation on
   write paths so unauthorized callers learn nothing about stored data.
   (Design contracts were corrected to this ordering during implementation.)
4. **Role-scoped cache keys** — `(role, uri, query)` prevents masked/full
   representation leaks across roles.
5. **Mocked backend, reset-to-seed** — seeded in-memory registries with
   `off|unavailable|slow` failure injection make resilience deterministic
   without infrastructure (per clarification 2026-09-18).
6. **Fail-closed audit** — if the audit sink is unavailable, operations are
   denied rather than executed unaudited.
7. **Ops via approved `fastapi` sidecar** — `/health` (public), `/metrics` and
   `/dashboard` (operator/admin); handlers are plain functions so unit tests
   need no HTTP client. TLS terminates at ingress.
8. **No new dependencies beyond `mcp`** — rate limiting, circuit breaking,
   retry, and metrics are stdlib implementations (~100 lines each).

## Request lifecycle (reads)

`authenticate → rate-limit → RBAC → role-scoped cache → circuit-breaker +
timeout-guarded store call → role masking → audit + metrics`.

## Write lifecycle (tools)

`authenticate → rate-limit → RBAC → validate/sanitize → execute with timeout →
rollback on failure → audit + metrics`. Slow executions return `task_id`.

## Failure model

| Failure | Behavior |
|---------|----------|
| Bad/missing/revoked key | Deny, generic error, audit `denied` |
| Wrong role | Deny before any state access, audit `denied` |
| Rate exceeded | Throttle with `retryAfterMs`, others unaffected |
| Dependency down/slow | `partial` outcome, breaker opens, `/health` → `degraded`, auto-recovery |
| Audit sink down | Fail closed (deny) |
| Mid-write crash | Checkpoint rollback restores prior state |

## Observability

`loguru` logs, in-memory counters + latency ring + error list exposed via
`/metrics` and `/dashboard`; per-operation latency recorded on every
read/tool call; degraded outputs tagged `processing_outcome="partial"`.

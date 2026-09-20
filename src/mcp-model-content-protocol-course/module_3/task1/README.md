# Secure MCP Server with Monitoring (module_3 · task1)

Production-style [Model Context Protocol](https://modelcontextprotocol.io/) server
providing secure, monitored access to e-commerce customer-service data for the
DataFlow Solutions scenario (`Build a Complete MCP Server with Security and
Monitoring.pdf`, same folder).

## Layout

```text
task1/
├── mcp_server/        # implementation (importable package)
│   ├── server.py      # MCPServer assembly + transport entrypoints
│   ├── resources.py   # resource handlers (URI routing, RBAC, masking, cache)
│   ├── tools.py       # data-modifying tools (validation, rollback, async)
│   ├── ops_app.py     # FastAPI sidecar: /health /metrics /dashboard
│   ├── auth.py audit.py cache.py ratelimit.py resilience.py metrics.py
│   ├── config.py models.py seed_data.py store.py
├── tests/             # colocated unittest suite (62 tests)
├── Dockerfile         # production container
├── deploy/            # reverse-proxy TLS snippet + monitoring/alerting guide
├── ARCHITECTURE.md    # design decisions
└── README.md          # this file
```

## Setup

```bash
poetry install
cp .env.example .env   # from repo root, then fill MCP_API_KEYS
```

`MCP_API_KEYS` is JSON mapping `key_id → {key_id, api_key (≥16 chars), role, revoked}`:

```json
{"agent-1": {"key_id": "agent-1", "api_key": "…", "role": "support_agent", "revoked": false}}
```

Roles: `admin` (full), `support_agent` (reads + ticket/order tools),
`auditor` (reads with PII masked + audit log), `operator` (health/metrics only).

## Run

```bash
cd src/mcp-model-content-protocol-course/module_3/task1
MCP_SERVER_API_KEY=<key> poetry run python -m mcp_server.server --transport stdio
MCP_SERVER_API_KEY=<key> poetry run python -m mcp_server.server --transport http --port 8000 --ops-port 8001
```

Ops endpoints (sidecar, `--ops-port`, default 8001): `/health` (public),
`/metrics` + `/dashboard` (`X-API-Key` of an operator/admin key).

## Test

```bash
poetry run python -m unittest discover -s src/mcp-model-content-protocol-course/module_3/task1/tests -t src/mcp-model-content-protocol-course/module_3/task1 -v
```

## API reference

Resources (`store://`, `application/json`): `customers/{id}`,
`customers/{id}/orders`, `customers/{id}/tickets`, `orders/{id}`,
`orders/status/{status}`, `tickets/{id}`, `tickets/status/{status}`,
`products`, `products/{id}`. Empty filtered views return `[]`.

Tools: `create_ticket(customer_id, subject, description, order_id?)`,
`update_order(order_id, new_status, reason?)`,
`update_ticket_status(ticket_id, new_status, note?)`.
Every call is authenticated, RBAC-checked **before** any state change,
rate-limited, and audit-logged (`success`/`denied`/`failed`).
Failures roll back; slow executions return a `task_id` for status polling.

Errors never leak PII or secrets
(`UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR`,
`RATE_LIMITED` + `retryAfterMs`, `DEPENDENCY_UNAVAILABLE`/`TIMEOUT` with
`processing_outcome: partial`).

## Deployment

```bash
docker build -f src/mcp-model-content-protocol-course/module_3/task1/Dockerfile -t mcp-secure-server .
docker run --env-file .env -p 8000:8000 mcp-secure-server
```

TLS terminates at ingress — see `deploy/reverse-proxy-tls.conf`.
Monitoring/alerting rules and backup/recovery in `deploy/monitoring.md`.
Mock data resets to seed on every startup by design; back up secrets and
audit exports only.

## Design notes

See [ARCHITECTURE.md](ARCHITECTURE.md) and
`specs/007-secure-mcp-server/` (spec, plan, contracts, quickstart, tasks).

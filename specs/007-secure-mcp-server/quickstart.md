# Quickstart: Secure MCP Server with Monitoring

**Date**: 2026-09-18 | **Feature**: `specs/007-secure-mcp-server/spec.md`

Validation guide proving the feature works end-to-end. Implementation lives in
`src/mcp-model-content-protocol-course/module_3/task1/mcp_server/` with colocated
tests in `src/mcp-model-content-protocol-course/module_3/task1/tests/`
(see [plan.md](plan.md)). Contracts: [resources](contracts/resources.md),
[tools](contracts/tools.md), [operations](contracts/operations.md).
Data shapes: [data-model.md](data-model.md).

## Prerequisites

1. Python 3.10+ and Poetry installed.
2. From repo root: `poetry install` (installs the `mcp` SDK, `fastapi`, `pydantic`, `loguru`).
3. Copy env template and set keys: `cp .env.example .env` — fill `MCP_API_KEYS`
   (key→role mappings for all four roles; JSON per `task1/README.md`), adjust
   `MCP_RATE_LIMIT_PER_MINUTE`, `MCP_CACHE_TTL_SECONDS` if needed.

## Run the server

```bash
cd src/mcp-model-content-protocol-course/module_3/task1
# STDIO transport (local dev, MCP client integration)
MCP_SERVER_API_KEY=<key> poetry run python -m mcp_server.server --transport stdio

# HTTP transport + ops sidecar (deployment-like)
MCP_SERVER_API_KEY=<key> poetry run python -m mcp_server.server --transport http --port 8000 --ops-port 8001
# Ops endpoints: http://localhost:8001/health  (public)
#                http://localhost:8001/metrics (X-API-Key: <operator-or-admin-key>)
#                http://localhost:8001/dashboard
```

## Run the tests

```bash
# Colocated suite (62 tests: unit + end-to-end workflows)
poetry run python -m unittest discover -s src/mcp-model-content-protocol-course/module_3/task1/tests -t src/mcp-model-content-protocol-course/module_3/task1 -v
poetry run ruff check .                      # lint gate
```

## Validation scenarios (map to Success Criteria)

| # | Scenario | Steps | Expected | Spec |
|---|----------|-------|----------|------|
| 1 | Authorized lookup | MCP client with `support_agent` key reads `store://customers/cust_1001` + orders + tickets | Full data returned; 3 `resource.read/success` audit records | SC-002, SC-003 |
| 2 | Masked read | Same reads with `auditor` key | `full_name`/`email`/`phone` masked as `"***"` | SC-002 |
| 3 | Denied access | Read with invalid key; business read with `operator` key | `UNAUTHENTICATED` / `FORBIDDEN`, no data, attempts audit-logged | SC-002, SC-003 |
| 4 | Create ticket | `create_ticket` with valid input, then read `store://tickets/{new_id}` | Ticket persisted and retrievable; audit `success` | SC-001 |
| 5 | Validation + rollback | `create_ticket` with bad input; `update_order` with illegal transition | `VALIDATION_ERROR`, zero state change, audit entries present | SC-003 |
| 6 | Rate limiting | Burst past `RATE_LIMIT_BURST` on one key while a second key sends normally | First key throttled with `retryAfterMs`; second unaffected | SC-005 |
| 7 | Dependency failure | Set `MOCK_FAILURE_MODE=unavailable`, read resource, check `/health`, unset flag, re-check | Graceful error → `degraded` status → auto-recovery to `healthy` | SC-006 |
| 8 | Metrics + dashboard | Exercise traffic, then `GET /metrics` and `/dashboard` with operator key | Counts/latencies/error-rate reflect traffic; no PII rendered | SC-008 |
| 9 | Fresh-setup check | New shell: follow README setup only, run test suite | Server runs; suite green in one command | SC-007 |
| 10 | Concurrency smoke | 50 parallel readers + 2 writers on distinct orders | No permission bypass, no corruption, 95% reads <2s | SC-004, SC-005 |

## Container validation

```bash
docker build -f src/mcp-model-content-protocol-course/module_3/task1/Dockerfile -t mcp-secure-server .
docker run --env-file .env -p 8000:8000 -p 8001:8001 mcp-secure-server
curl localhost:8001/health   # expect {"status": "healthy", ...}
```

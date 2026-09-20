# Implementation Plan: Secure MCP Server with Monitoring

**Branch**: `007-secure-mcp-server` | **Date**: 2026-09-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-secure-mcp-server/spec.md` (plus clarifications: mock-everything backend, reset-to-seed on startup)

## Summary

Build a production-style MCP server (`src/mcp_secure_server/`) exposing e-commerce customer-service data (customers, orders, products, support tickets) as MCP resources plus audited data-modifying tools (`create_ticket`, `update_order`). All access goes through API-key authentication with role-based access control and per-request audit logging. Resilience (timeouts, circuit breaker, graceful degradation), observability (health, metrics, error tracking via `loguru`), and performance (role-scoped caching, per-key rate limiting) layers wrap the MCP core. All external dependencies are mocked with seeded in-memory data per clarification. Ops surface (health/metrics/dashboard) reuses the approved `fastapi` dependency; the only new dependency is the canonical `mcp` Python SDK (justified below).

## Technical Context

**Language/Version**: Python 3.10+ (repo `pyproject` requires `^3.10`; dev env is 3.12)

**Primary Dependencies**: `mcp` Python SDK v2 (`MCPServer` class) — NEW (justification under Constitution Check, Principle VI); approved existing: `pydantic`/`pydantic-settings` (schemas, config), `loguru` (logging), `fastapi` (ops HTTP sidecar: `/health`, `/metrics`, dashboard). Everything else from stdlib (`asyncio`, `time`, `ssl` config surface, `unittest`).

**Storage**: N/A — seeded in-memory mock datasets, re-initialized to seed on every startup (clarified 2026-09-18). No database, no external APIs.

**Testing**: `unittest` (stdlib), single command `poetry run python -m unittest discover -v`; ops handlers written as plain functions so they are unit-testable without an HTTP client dependency.

**Target Platform**: Local dev (Windows/Linux) via STDIO transport; Linux container (`python:3.12-slim`, non-root) via Streamable HTTP transport for deployment.

**Project Type**: Service (MCP server + HTTP ops sidecar).

**Performance Goals**: ≥1,000 interactions/day; 95% of routine reads <2s; ≥50 concurrent requesters with zero permission bypass or data corruption (SC-004, SC-005).

**Constraints**: No hardcoded secrets (all via `Settings` + `.env`); `ruff` + Black-88 + Python 3.10+ type hints; stdlib→third-party→local import order; `loguru` only; no real network dependencies in tests (mocked transports/failure injection flags).

**Scale/Scope**: Single host; seeded catalog of tens of records per entity; 4 roles; 4 resource types; 2 modifying tools; 1 Dockerfile + deployment guide.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. LangGraph primitives | ✅ Pass (N/A) | No agentic graph workflow in scope; server is a request/response MCP service. No `StateGraph` needed; nothing to migrate. |
| II. Configuration-driven | ✅ Pass | All secrets (API keys, TLS flags, rate limits, seed sizes) via `Settings` (`src/mcp_secure_server/config.py`, `pydantic-settings`) + `.env`. Gate enforced by test asserting no secret literals. |
| III. Observability by default | ✅ Pass | `loguru` logging; per-operation latency via manual `time.monotonic()` (plain functions per AGENTS.md note, not `@timed_node` which assumes classmethod state); errors as `list[ErrorRecord]`; exponential backoff on retryable mock-dependency calls; `processing_outcome="partial"` on degraded outputs. |
| IV. LLM abstraction | ✅ Pass (N/A) | Server makes zero LLM calls; `LLMFactory` not applicable. |
| V. Test discipline | ✅ Pass | `unittest`, `tests/test_mcp_secure_server/` mirroring `src/mcp_secure_server/`, one `TestCase` per subject, shared fixtures in `tests/base.py` (extend `BaseTestCase`). Unit + end-to-end workflow tests. |
| VI. Dependency discipline | ⚠️ New dep `mcp` — justified | Evaluated: (a) hand-rolled JSON-RPC over STDIO — reimplements the MCP spec, high defect risk, no conformance; (b) `fastapi`-only HTTP API — not MCP-compliant, fails the core requirement. The official `mcp` SDK is the canonical, minimal choice. `fastapi` reuse for ops endpoints avoids adding `uvicorn`/`httpx` (ops handlers are plain functions; HTTP is thin wiring). |
| Code quality gates | ✅ Pass | `ruff`, Black-88, type hints, import order — verified pre-merge. |

**Post-design re-check (Phase 1)**: design introduces no new dependencies, no hardcoded config, no LLM coupling, no graph workflows. All gates remain ✅. No Complexity Tracking entries required.

## Project Structure

### Documentation (this feature)

```text
specs/007-secure-mcp-server/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── resources.md
│   ├── tools.md
│   └── operations.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/mcp-model-content-protocol-course/module_3/task1/   # self-contained submission
├── mcp_server/
│   ├── __init__.py
│   ├── config.py          # Settings (API keys, roles, limits, TLS flags, seed sizes)
│   ├── models.py          # Pydantic entities + ErrorRecord + enums
│   ├── seed_data.py       # Deterministic seed datasets (reset on startup)
│   ├── store.py           # In-memory registries + failure/latency injection hooks
│   ├── auth.py            # API-key authentication + RBAC permission checks
│   ├── audit.py           # Append-only audit log (fail-closed)
│   ├── cache.py           # TTL cache with role-scoped keys
│   ├── ratelimit.py       # Per-key token-bucket rate limiter
│   ├── resilience.py      # Timeouts, circuit breaker, retry with backoff
│   ├── metrics.py         # Counters, latency histograms, error tracking
│   ├── resources.py       # MCP resource handlers (URI routing, filtering, masking)
│   ├── tools.py           # MCP tool handlers (validation, rollback, async tasks)
│   ├── ops_app.py         # FastAPI sidecar: /health, /metrics, dashboard (thin wiring)
│   └── server.py          # MCPServer assembly + transport entrypoints
├── tests/                 # Colocated unittest suite (fixtures + test_*.py)
├── Dockerfile             # Production container (non-root, python:3.12-slim)
├── deploy/                # Reverse-proxy TLS snippet + monitoring/alerting guide
├── README.md              # Setup / API / deployment guide
└── ARCHITECTURE.md        # Design decisions
```

**Structure Decision**: Self-contained `module_3/task1/` submission package
(`mcp_server/` + colocated `tests/`, per user direction that code live in
task1). The hyphenated course folder is not importable, so the runnable
package is nested inside it and tests run via
`python -m unittest discover -s .../task1/tests -t .../task1`.
Tests mirror under `tests/test_mcp_secure_server/`. README updated with setup/deployment sections.

## Complexity Tracking

> No constitution violations requiring justification. This section intentionally left empty.

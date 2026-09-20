# Research: Secure MCP Server with Monitoring

**Date**: 2026-09-18 | **Feature**: `specs/007-secure-mcp-server/spec.md`

All unknowns from Technical Context resolved below. No NEEDS CLARIFICATION remains.

## R1: MCP server framework

- **Decision**: Use the official `mcp` Python SDK v2 (`MCPServer` class; `FastMCP` was renamed in v2) as the protocol layer.
- **Rationale**: Canonical implementation of the MCP spec (resources, tools, STDIO + Streamable HTTP transports); avoids hand-rolling JSON-RPC with its conformance and defect risk.
- **Alternatives considered**: (a) Raw JSON-RPC over STDIO — rejected: reimplements framing, capability negotiation, and error codes; (b) FastAPI-only REST API — rejected: not MCP-compliant, fails the core course requirement.
- **Consequence**: Single justified new dependency per Principle VI (recorded in plan.md Constitution Check).

## R2: Transports

- **Decision**: STDIO transport for local dev and test harness; Streamable HTTP transport (provided by the SDK) for container deployment.
- **Rationale**: STDIO keeps local runs dependency-free; HTTP enables the "thousands of daily interactions" deployment story and lets the ops sidecar share the same port family.
- **Alternatives considered**: SSE-only — rejected: superseded by Streamable HTTP in current SDK.

## R3: Authentication + RBAC over MCP

- **Decision**: Custom `auth.py` layer: API key presented per session (STDIO: server-side key mapping via `Settings`; HTTP: `X-API-Key` header), resolved to an `AuthContext(role, key_id)` that every resource/tool handler must check before touching data.
- **Rationale**: MCP's built-in OAuth 2.1 flow is enterprise-grade overkill for the course's explicit "API key + RBAC" requirement; a thin explicit layer is auditable and unit-testable without network.
- **Alternatives considered**: MCP OAuth provider integration — rejected: scope creep, no identity provider available in this environment.

## R4: Roles and permission matrix

- **Decision**: Four roles — `admin` (full), `support_agent` (read all entities + create/update tickets + update orders), `auditor` (read all + read audit log, PII masked), `operator` (health/metrics only, no business data).
- **Rationale**: Covers least-privilege demonstration (denials in both directions: data roles can't see ops internals beyond health; operator can't see customer data) with a small, testable matrix.
- **Alternatives considered**: 2-role (agent/admin) — rejected: too coarse to demonstrate field masking and separation of duties.

## R5: Mock data backend

- **Decision**: Seeded in-memory registries (`store.py` + `seed_data.py`), deterministic seed for repeatable tests, full re-initialization on startup (per clarification 2026-09-18). Failure/latency injection via config flags (`MOCK_FAILURE_MODE`, `MOCK_LATENCY_MS`) to exercise resilience paths deterministically.
- **Rationale**: Zero infrastructure, deterministic tests, and failure injection without flaky network simulation.
- **Alternatives considered**: SQLite persistence — rejected: contradicts reset-to-seed clarification and adds file-state management to tests.

## R6: Caching without leaking across roles

- **Decision**: In-memory TTL cache (`cache.py`) whose keys incorporate `(role, uri, query_hash)`; PII-bearing entries never shared across roles; TTL via `Settings.CACHE_TTL_SECONDS`.
- **Rationale**: Naive URI-keyed caching would leak masked fields between roles — the role-scoped key is a security requirement, not an optimization.
- **Alternatives considered**: `functools.lru_cache` — rejected: no TTL, no role namespacing, unbounded growth.

## R7: Rate limiting

- **Decision**: In-memory token-bucket limiter per API key (`ratelimit.py`), limits via `Settings` (`RATE_LIMIT_PER_MINUTE`, `RATE_LIMIT_BURST`); excess calls return MCP error with `retryAfterMs` hint.
- **Rationale**: stdlib-only, per-key fairness (one abusive client doesn't starve others), deterministic tests via injectable clock.
- **Alternatives considered**: Fixed-window counter — rejected: burst-abuse at window edges.

## R8: Resilience patterns

- **Decision**: `resilience.py` with `asyncio.wait_for` timeouts on every store/dependency call, a three-state circuit breaker (closed/open/half-open) per dependency, exponential-backoff retry for transient mock failures, graceful degradation tagging (`processing_outcome="partial"`), and automatic recovery when the dependency heals.
- **Rationale**: Directly implements FR-013/FR-014 and SC-006 with patterns testable via the R5 injection flags.
- **Alternatives considered**: Third-party `tenacity`/`pybreaker` — rejected: trivial to implement correctly in ~100 lines; avoids two new dependencies.

## R9: Observability

- **Decision**: `loguru` for all logging; `metrics.py` in-memory registry (counters + latency samples + error counts) exposed via ops surface; per-operation latency with manual `time.monotonic()` (plain functions, per AGENTS.md); errors recorded as `list[ErrorRecord]` (step, error_type, message, timestamp).
- **Rationale**: Matches Constitution III and repo conventions exactly; no new deps.
- **Alternatives considered**: Prometheus client library — rejected: exposition format can be hand-rendered for course scope; avoids a new dependency.

## R10: Ops surface (health/metrics/dashboard)

- **Decision**: `fastapi` sidecar app (`ops_app.py`) with `GET /health`, `GET /metrics`, `GET /dashboard` (server-rendered HTML summary). Route handlers are thin wrappers over plain testable functions so `unittest` needs no HTTP client dependency.
- **Rationale**: Reuses an approved dependency; keeps MCP protocol surface clean while satisfying FR-011/FR-012.
- **Alternatives considered**: MCP tools for health/metrics — rejected: operators need access without MCP credentials or an MCP client.

## R11: Encrypted transport (TLS)

- **Decision**: TLS terminated at deployment ingress (documented in deployment guide with example reverse-proxy config); server reads `TLS_ENABLED`/`TLS_CERT_PATH`/`TLS_KEY_PATH` settings surface for environments where the sidecar terminates TLS directly via stdlib `ssl`.
- **Rationale**: STDIO transport has no network layer to encrypt; adding a TLS stack for the course scope would be theater. Honest, documented termination point satisfies FR-009's intent without new dependencies.
- **Alternatives considered**: Self-signed cert generation in-repo — rejected: ships private key material habits; docs show how to mount real certs instead.

## R12: Testing strategy

- **Decision**: `unittest` only. Unit tests per module (`test_auth`, `test_resources`, `test_tools`, `test_resilience`, `test_ops`) + `test_workflows` end-to-end (seed → auth → read → write → audit-verify → health-check). Shared fixtures extend `tests/base.py::BaseTestCase`. Deterministic via fixed seed + injectable clock + injection flags; no network, no sleep-based timing assertions.
- **Rationale**: Constitution V compliance with hermetic, fast tests.

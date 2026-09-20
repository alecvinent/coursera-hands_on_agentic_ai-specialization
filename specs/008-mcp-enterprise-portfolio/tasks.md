# Tasks: MCP Enterprise Integration Portfolio

**Input**: Design documents from `/specs/008-mcp-enterprise-portfolio/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included — spec requires unit and integration tests (FR-010).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, package structure, configuration, and shared models

- [x] T001 Create project directory structure at `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/` with `__init__.py`
- [x] T002 [P] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/config.py` with pydantic-settings `Settings` class (env prefix `MCP_PORTFOLIO_`, fields: api_keys, cache_ttl_seconds, rate_limit_per_minute, rate_limit_burst, tool_timeout_seconds, seed, mock_failure_mode, mock_latency_ms)
- [x] T003 [P] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/models.py` with Pydantic models for Customer, Order, SupportTicket, Product, InventoryItem, Credential, AuditRecord, HealthReport — field types and constraints from `data-model.md`
- [x] T004 [P] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/store.py` with `MockStore` class: in-memory dicts, seeded on `__init__`, reset-to-seed behavior, async methods for CRUD on all entity types
- [x] T005 [P] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/cache.py` with `TTLCache` class: role-scoped cache keys `(role, uri, query)`, configurable TTL, `get`/`set`/`invalidate` methods
- [x] T006 [P] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/__init__.py` with package docstring and version
- [x] T007 [P] Create test directory `src/mcp-model-content-protocol-course/module_3/task2/tests/__init__.py` and `src/mcp-model-content-protocol-course/module_3/task2/tests/fixtures.py` with shared test helpers (credential fixtures per role, mock store factory)
- [x] T008 [P] Create `src/mcp-model-content-protocol-course/module_3/task2/README.md` with initial setup instructions matching task1 conventions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Auth, audit, rate limiting, resilience, metrics — core infrastructure ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 [P] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/auth.py` with `AuthContext`, `authenticate()`, `require()` functions: validate API key, extract role, raise `Unauthenticated`/`Forbidden` on failure — matching task1 patterns
- [x] T010 [P] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/audit.py` with `AuditLog` class: append-only list of `AuditRecord`, method `log(key_id, role, action, resource_type, inputs, outcome, latency_ms)`
- [x] T011 [P] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/ratelimit.py` with `RateLimiter` class: per-minute sliding window, burst allowance, returns `retryAfterMs` on limit hit
- [x] T012 [P] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/resilience.py` with `CircuitBreaker` class: closed/open/half-open states, timeout guard decorator, failure isolation
- [x] T013 [P] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/metrics.py` with `MetricsRegistry` class: request counts, latency ring buffer, error list, `record_request()`, `record_latency()`, `record_error()` methods
- [x] T014 [P] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/ops_app.py` with FastAPI sidecar: `/health` (public), `/metrics` (operator/admin), `/dashboard` (operator/admin) endpoints — matching task1 patterns

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Architecture Assessment and Design (Priority: P1) 🎯 MVP

**Goal**: Produce a complete architecture assessment with diagram, MCP-vs-traditional comparison, risk assessment, ROI analysis, and executive summary for the Fortune 500 retail scenario.

**Independent Test**: All 5 architecture documents exist, are non-empty, reference CRM/ERP/inventory/support systems, contain ≥3 trade-offs in comparison, and executive summary uses business language.

### Implementation for User Story 1

- [x] T015 [US1] Create `src/mcp-model-content-protocol-course/module_3/task2/architecture/architecture-diagram.md` with Mermaid diagram showing MCP integration points across CRM, ERP, inventory databases, and customer support platforms (FR-001)
- [x] T016 [US1] Create `src/mcp-model-content-protocol-course/module_3/task2/architecture/mcp-vs-traditional.md` with detailed comparison of MCP vs REST/SOAP/gRPC integration: at least 3 concrete trade-offs with evidence and recommendation per FR-002
- [x] T017 [US1] Create `src/mcp-model-content-protocol-course/module_3/task2/architecture/risk-assessment.md` with risk register: identified risks with probability/impact ratings and mitigation strategies per FR-003
- [x] T018 [US1] Create `src/mcp-model-content-protocol-course/module_3/task2/architecture/roi-analysis.md` with ROI projections, cost estimates, efficiency metrics, timeline projections, and documented assumptions per FR-004
- [x] T019 [US1] Create `src/mcp-model-content-protocol-course/module_3/task2/architecture/executive-summary.md` with C-level summary in business language covering all 3 components per FR-005
- [x] T020 [US1] Create `src/mcp-model-content-protocol-course/module_3/task2/ARCHITECTURE.md` with design decisions log documenting how architecture assessment informed server and security design (FR-019 integration)

**Checkpoint**: Architecture assessment complete — 5 documents present, all acceptance scenarios verifiable

---

## Phase 4: User Story 2 — Production MCP Server Implementation (Priority: P1) 🎯 MVP

**Goal**: Implement a production-ready MCP server with customer/inventory/sales resources, order/inventory/service tools, and comprehensive tests.

**Independent Test**: Server starts, all resource/tool calls return correct data, full test suite passes, API docs cover every endpoint.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T021 [P] [US2] Create `src/mcp-model-content-protocol-course/module_3/task2/tests/test_auth.py` with unit tests for authentication, RBAC, unauthenticated/forbidden scenarios per role
- [x] T022 [P] [US2] Create `src/mcp-model-content-protocol-course/module_3/task2/tests/test_resources.py` with unit tests for all resource URI patterns, role-based filtering, PII masking, cache behavior
- [x] T023 [P] [US2] Create `src/mcp-model-content-protocol-course/module_3/task2/tests/test_tools.py` with unit tests for all tools: input validation, state changes, rollback on failure, optimistic locking
- [x] T024 [P] [US2] Create `src/mcp-model-content-protocol-course/module_3/task2/tests/test_ops.py` with unit tests for health/metrics/dashboard endpoints
- [x] T025 [P] [US2] Create `src/mcp-model-content-protocol-course/module_3/task2/tests/test_integration.py` with integration tests: full read workflow, full write workflow, error propagation, concurrent access

### Implementation for User Story 2

- [x] T026 [US2] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/resources.py` with `ResourceService` class: URI routing, RBAC checks, PII masking for auditor role, cache integration, error handling — resource URIs: `retail://customers/{id}`, `retail://customers/{id}/orders`, `retail://customers/{id}/tickets`, `retail://orders/{id}`, `retail://orders/status/{status}`, `retail://inventory/{product_id}`, `retail://inventory/low-stock`, `retail://products`, `retail://products/{id}` (FR-007)
- [x] T027 [US2] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/tools.py` with `ToolService` class and `TOOL_ROLES` mapping: `create_order`, `update_order_status`, `update_inventory`, `reserve_inventory`, `create_support_ticket`, `update_ticket_status`, `get_task_status` — each with input validation, RBAC, rollback, audit logging (FR-008)
- [x] T028 [US2] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/server.py` with `ServerDeps` class and `build_server()` function: assemble MCPServer with all resources and tools bound, STDIO + Streamable HTTP transports, ops sidecar integration (FR-006)
- [x] T029 [US2] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/__main__.py` with CLI entrypoint: argparse for `--transport`, `--host`, `--port`, `--ops-port`, `--api-key` — matching task1 patterns
- [x] T030 [US2] Create `src/mcp-model-content-protocol-course/module_3/task2/mcp_portfolio/seed_data.py` with seed data generators for customers, orders, products, tickets, inventory — matching task1 conventions with configurable counts

**Checkpoint**: MCP server fully functional — all resources and tools work, tests pass

---

## Phase 5: User Story 3 — Enterprise Security and Deployment Framework (Priority: P2)

**Goal**: Add Docker containerization, CI/CD pipeline, monitoring guide, disaster recovery procedures, and performance optimization documentation.

**Independent Test**: Docker image builds and runs, CI config is valid YAML, monitoring/DR docs contain actionable procedures, security controls block unauthorized access.

### Implementation for User Story 3

- [x] T031 [P] [US3] Create `src/mcp-model-content-protocol-course/module_3/task2/deploy/Dockerfile` with multi-stage build: Python 3.12 base, poetry install, non-root user, health check, exposed ports 8000/8001 (FR-015)
- [x] T032 [P] [US3] Create `src/mcp-model-content-protocol-course/module_3/task2/deploy/docker-compose.yml` with service definition: env-file, port mapping, health check, restart policy (FR-015)
- [x] T033 [P] [US3] Create `src/mcp-model-content-protocol-course/module_3/task2/deploy/ci.yml` with GitHub Actions workflow: lint (ruff), test (unittest), Docker build stages (FR-016)
- [x] T034 [P] [US3] Create `src/mcp-model-content-protocol-course/module_3/task2/deploy/reverse-proxy-tls.conf` with nginx TLS termination config matching task1 conventions (FR-012)
- [x] T035 [US3] Create `src/mcp-model-content-protocol-course/module_3/task2/deploy/monitoring.md` with monitoring guide: metrics interpretation, alerting rules, dashboard usage, incident response procedures (FR-014)
- [x] T036 [US3] Create `src/mcp-model-content-protocol-course/module_3/task2/deploy/disaster-recovery.md` with DR procedures: seed data reset, audit log export, configuration backup, recovery steps with time targets (FR-017)
- [x] T037 [US3] Create `src/mcp-model-content-protocol-course/module_3/task2/deploy/scaling-guide.md` with performance optimization and scaling strategies: connection pooling, caching, horizontal scaling recommendations, load testing approach (FR-018)

**Checkpoint**: Deployment framework complete — container builds, CI valid, monitoring/DR documented

---

## Phase 6: User Story 4 — Integrated Portfolio Presentation (Priority: P3)

**Goal**: Create a professional portfolio presentation tying all components together with executive summary, technical deep-dive, demo scripts, trade-off discussion, and roadmap.

**Independent Test**: Presentation covers all required sections, references correct components, demo scripts are executable, roadmap aligns with architecture assessment.

### Implementation for User Story 4

- [x] T038 [US4] Create `src/mcp-model-content-protocol-course/module_3/task2/portfolio/presentation.md` with full portfolio walkthrough: executive summary, technical deep-dive per component, live demo script (sequence of resource/tool calls), design trade-off discussion (≥3 decisions), integration narrative (FR-021)
- [x] T039 [US4] Create `src/mcp-model-content-protocol-course/module_3/task2/portfolio/roadmap.md` with future enhancements: prioritized list aligned with architecture assessment's enterprise needs, effort estimates, dependency mapping (FR-021)
- [x] T040 [US4] Create `src/mcp-model-content-protocol-course/module_3/task2/portfolio/demo-script.md` with step-by-step live demo: server startup, authentication, resource reads, tool executions, monitoring check, error scenario demonstration

**Checkpoint**: Portfolio presentation complete — all sections present, demo executable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final integration validation, documentation sync, and quickstart verification

- [x] T041 Update `src/mcp-model-content-protocol-course/module_3/task2/README.md` with complete setup, run, test, and deployment instructions per quickstart.md
- [x] T042 Validate all cross-references: architecture assessment → server design → security framework → deployment → portfolio (FR-019)
- [x] T043 Run quickstart.md validation: follow all steps, verify outcomes match expected results
- [x] T044 Run full test suite: `poetry run python -m unittest discover -s src/mcp-model-content-protocol-course/module_3/task2/tests -t src/mcp-model-content-protocol-course/module_3/task2 -v` — all tests must pass
- [x] T045 Verify Docker build: `docker build -f src/mcp-model-content-protocol-course/module_3/task2/deploy/Dockerfile -t mcp-portfolio .` — image builds without error
- [x] T046 Verify CI config validity: `python -c "import yaml; yaml.safe_load(open('src/mcp-model-content-protocol-course/module_3/task2/deploy/ci.yml'))"` — no parse errors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (models.py, config.py from T003/T002) — BLOCKS all user stories
- **US1 (Phase 3)**: Can start after Phase 1 (documentation only, no code dependencies)
- **US2 (Phase 4)**: Depends on Phase 2 (auth, audit, metrics, resilience, store, cache, config, models all required)
- **US3 (Phase 5)**: Depends on Phase 4 (deployment wraps the running server)
- **US4 (Phase 6)**: Depends on Phases 3, 4, 5 (references all three components)
- **Polish (Phase 7)**: Depends on all previous phases

### User Story Dependencies

- **US1 (P1)**: Independent — documentation only, can start after Phase 1
- **US2 (P1)**: Depends on Phase 2 foundational, independent of US1
- **US3 (P2)**: Depends on US2 server being functional (deployment wraps it)
- **US4 (P3)**: Depends on US1, US2, US3 all being complete (references all)

### Within Each User Story

- Tests (T021-T025) MUST be written and FAIL before implementation (T026-T030)
- Models before services (T003 before T026/T027)
- Services before server assembly (T026/T027 before T028)
- Core implementation before integration (T028 before T030)

### Parallel Opportunities

- Phase 1: T002-T008 all [P] — different files, no dependencies
- Phase 2: T009-T014 all [P] — different files, no dependencies
- Phase 3: T015-T020 all [P] — different documentation files
- Phase 4 tests: T021-T025 all [P] — different test files
- Phase 5: T031-T034 all [P] — different deployment config files
- Phase 6: T038-T040 can run in parallel (different portfolio files)

---

## Parallel Example: User Story 2

```bash
# Launch all test files first (T021-T025, all [P]):
Task: "Create test_auth.py in tests/test_auth.py"
Task: "Create test_resources.py in tests/test_resources.py"
Task: "Create test_tools.py in tests/test_tools.py"
Task: "Create test_ops.py in tests/test_ops.py"
Task: "Create test_integration.py in tests/test_integration.py"

# Then implementation (T026-T027 can run in parallel after tests exist):
Task: "Create resources.py in mcp_portfolio/resources.py"
Task: "Create tools.py in mcp_portfolio/tools.py"

# Then server assembly (T028 depends on T026+T027):
Task: "Create server.py in mcp_portfolio/server.py"

# Then entrypoint + seed data (T029-T030, [P]):
Task: "Create __main__.py in mcp_portfolio/__main__.py"
Task: "Create seed_data.py in mcp_portfolio/seed_data.py"
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: Architecture Assessment (US1) — documentation deliverable
4. Complete Phase 4: MCP Server (US2) — code deliverable
5. **STOP and VALIDATE**: Server runs, tests pass, architecture docs complete
6. Demo-ready MVP with assessment + working server

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Architecture Assessment (US1) → Document deliverable ready
3. MCP Server (US2) → Working server + tests → Deploy/Demo (MVP!)
4. Security/Deployment (US3) → Production-ready deployment
5. Portfolio Presentation (US4) → Complete portfolio
6. Polish → Final validation

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: Architecture Assessment (US1) — documentation
   - Developer B: MCP Server (US2) — server code + tests
3. Once server is functional:
   - Developer A: Portfolio Presentation (US4)
   - Developer B: Security/Deployment (US3)
4. Polish and integration together

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Total tasks: 46 (13 setup/foundational, 6 US1, 10 US2, 7 US3, 3 US4, 6 polish)

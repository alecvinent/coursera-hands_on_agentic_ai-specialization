# Tasks: Secure MCP Server with Monitoring

**Input**: Design documents from `/specs/007-secure-mcp-server/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — explicitly requested in FR-019 (unit tests for core functionality + end-to-end workflow tests, runnable with a single documented command). TDD: write each test task first and verify it FAILS before its implementation task.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create src/mcp-model-content-protocol-course/module_3/task1/mcp_server/ and src/mcp-model-content-protocol-course/module_3/task1/tests/ scaffold with __init__.py files per plan.md
- [X] T002 [P] Add mcp Python SDK dependency to pyproject.toml and update poetry lock file
- [X] T003 [P] Create .env.example in repo root with MCP_API_KEYS and all tuning keys from plan.md Technical Context
- [X] T004 [P] Add deterministic seed fixture helper to tests/base.py by extending BaseTestCase
  (adapted during implementation: colocated tests use task1/tests/fixtures.py; SeededTestCase also added to tests/base.py)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement Settings class in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/config.py (API keys, roles, RATE_LIMIT_PER_MINUTE/BURST, CACHE_TTL_SECONDS, TOOL_TIMEOUT_SECONDS, ERROR_RATE_THRESHOLD, MOCK_FAILURE_MODE, MOCK_LATENCY_MS, TLS_* flags, seed sizes; pydantic-settings, no hardcoded secrets)
- [X] T006 [P] Implement pydantic entities in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/models.py (Customer with tier standard|premium|enterprise; Order with items quantity ≥ 1 unit_price ≥ 0 and computed total; SupportTicket with subject 5–120 chars and description 1–2000 chars; Product; ApiCredential with Role admin|support_agent|auditor|operator; AuditRecord; HealthReport; ErrorRecord TypedDict with step, error_type, message, timestamp)
- [X] T007 [P] Implement deterministic seed datasets in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/seed_data.py (tens of customers, orders, products, tickets with ids matching cust_[0-9]{4,}, ord_[0-9]{4,}, tkt_[0-9]{4,}, prd_[0-9]{4,})
- [X] T008 Implement in-memory registries with failure/latency injection hooks in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/store.py (depends on T006, T007; full re-initialization to seed on startup)
- [X] T009 [P] Implement API-key authentication with hmac.compare_digest, revoked-key handling, and AuthContext in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/auth.py
- [X] T010 [P] Implement append-only audit log with fail-closed behavior and sanitized inputs_hash in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/audit.py
- [X] T011 [P] Implement TTL cache with role-scoped (role, uri, query_hash) keys in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/cache.py
- [X] T012 [P] Implement per-key token-bucket rate limiter with injectable clock in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/ratelimit.py
- [X] T013 [P] Implement timeouts via asyncio.wait_for, three-state circuit breaker (closed/open/half-open), exponential-backoff retry, and processing_outcome partial tagging in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/resilience.py
- [X] T014 [P] Implement metrics registry with counters, bounded latency ring buffer, and error-rate computation in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/metrics.py
- [X] T015 [P] Write failing-then-passing unit tests for config and models in src/mcp-model-content-protocol-course/module_3/task1/tests/test_config.py and src/mcp-model-content-protocol-course/module_3/task1/tests/test_models.py
- [X] T016 [P] Write failing-then-passing unit tests for auth and audit in src/mcp-model-content-protocol-course/module_3/task1/tests/test_auth.py and src/mcp-model-content-protocol-course/module_3/task1/tests/test_audit.py
- [X] T017 [P] Write failing-then-passing unit tests for store seeding determinism and injection flags in src/mcp-model-content-protocol-course/module_3/task1/tests/test_store.py
- [X] T018 [P] Write failing-then-passing unit tests for cache, rate limiter, resilience, and metrics in src/mcp-model-content-protocol-course/module_3/task1/tests/test_cache.py, src/mcp-model-content-protocol-course/module_3/task1/tests/test_ratelimit.py, src/mcp-model-content-protocol-course/module_3/task1/tests/test_resilience.py, and src/mcp-model-content-protocol-course/module_3/task1/tests/test_metrics.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Secure customer data lookup (Priority: P1) 🎯 MVP

**Goal**: Authenticated, permission-checked, audit-logged read access to customers, orders, tickets, and products with PII masking and caching

**Independent Test**: Authenticate with each of the 4 roles, request every URI pattern in contracts/resources.md, verify full/masked/denied responses plus one audit record per access

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T019 [P] [US1] Write failing unit tests for resource reads, PII masking, cache behavior, and error envelope in src/mcp-model-content-protocol-course/module_3/task1/tests/test_resources.py

### Implementation for User Story 1

- [X] T020 [US1] Implement URI routing and MCP resource handlers for all store:// patterns in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/resources.py (depends on T019; see contracts/resources.md)
- [X] T021 [US1] Implement role-based field filtering with full_name/email/phone masked as "***" for auditor and FORBIDDEN for operator in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/resources.py
- [X] T022 [US1] Integrate role-scoped cache and audit logging into resource reads with empty-filtered-view-returns-[] semantics in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/resources.py
- [X] T023 [US1] Wire resource handlers into FastMCP server assembly with STDIO transport in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/server.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Audited support actions (Priority: P1)

**Goal**: create_ticket, update_order, and update_ticket_status tools with validation, rollback, async execution, and audit logging

**Independent Test**: Execute each tool with valid, invalid, unauthorized, and conflicting inputs; verify state changes, rejections, rollback, and audit entries

### Tests for User Story 2 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T024 [P] [US2] Write failing unit tests for tool validation, RBAC denial, rollback, conflict handling, and async task_id flow in src/mcp-model-content-protocol-course/module_3/task1/tests/test_tools.py

### Implementation for User Story 2

- [X] T025 [US2] Implement create_ticket, update_order, and update_ticket_status handlers in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/tools.py (depends on T024; see contracts/tools.md for input schemas)
- [X] T026 [US2] Implement input validation/sanitization with VALIDATION_ERROR and zero state change plus checkpoint-based rollback with failed audit record in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/tools.py
- [X] T027 [US2] Implement order/ticket legal transition maps with CONFLICT response on concurrent writes and async execution returning task_id past TOOL_TIMEOUT_SECONDS in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/tools.py
- [X] T028 [US2] Register tool handlers in FastMCP server assembly in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/server.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Operated and monitored production service (Priority: P2)

**Goal**: Health/metrics/dashboard ops surface, rate limiting, TLS configuration, graceful degradation with auto-recovery

**Independent Test**: Start server from docs, hit /health and /metrics, trigger rate-limit and MOCK_FAILURE_MODE outage, verify throttle signals, degraded status, and recovery without restart

### Tests for User Story 3 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T029 [P] [US3] Write failing unit tests for health statuses, metrics output, dashboard sanitization, and TLS settings in src/mcp-model-content-protocol-course/module_3/task1/tests/test_ops.py

### Implementation for User Story 3

- [X] T030 [US3] Implement health/metrics/dashboard as plain testable functions in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/ops_app.py (depends on T029; status healthy|degraded|unhealthy per contracts/operations.md)
- [X] T031 [US3] Wire FastAPI routes GET /health (public, no business data), GET /metrics, and GET /dashboard (operator/admin key) in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/ops_app.py
- [X] T032 [US3] Implement error tracking with alerting hooks and 429/RATE_LIMITED responses carrying retryAfterMs in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/metrics.py and src/mcp-model-content-protocol-course/module_3/task1/mcp_server/server.py
- [X] T033 [US3] Implement TLS_ENABLED/TLS_CERT_PATH/TLS_KEY_PATH settings surface with stdlib ssl wiring for direct termination in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/config.py and src/mcp-model-content-protocol-course/module_3/task1/mcp_server/ops_app.py

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Verified, documented, deployable release (Priority: P3)

**Goal**: Fresh-checkout setup, full test suite, container, deployment/monitoring/recovery docs, architecture documentation

**Independent Test**: Fresh checkout → follow README only → server runs, suite green, container serves /health, docs answer reviewer questions without author help

### Tests for User Story 4 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T034 [P] [US4] Write failing end-to-end workflow tests covering seed, auth, read, write, audit verification, and health check in src/mcp-model-content-protocol-course/module_3/task1/tests/test_workflows.py

### Implementation for User Story 4

- [X] T035 [P] [US4] Write production Dockerfile based on python:3.12-slim running as non-root user in src/mcp-model-content-protocol-course/module_3/task1/Dockerfile
- [X] T036 [P] [US4] Write task1 README.md with setup, API reference, deployment, monitoring, and backup/recovery sections for the MCP server
- [X] T037 [P] [US4] Write architecture documentation explaining design decisions in src/mcp-model-content-protocol-course/module_3/task1/ARCHITECTURE.md
- [X] T038 [US4] Add deployment configuration with reverse-proxy TLS termination snippet and monitoring/alerting setup in src/mcp-model-content-protocol-course/module_3/task1/deploy/ (depends on T035)
- [X] T039 [US4] Run quickstart.md validation scenarios 1-10 end to end and fix all discrepancies found

**Checkpoint**: Release is verified, documented, and deployable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Run poetry run ruff check . and fix all findings across src/mcp-model-content-protocol-course/module_3/task1/mcp_server/ and src/mcp-model-content-protocol-course/module_3/task1/tests/
- [X] T041 [P] Run 50-concurrent-requester smoke test verifying zero permission bypass, zero corruption, and 95% reads under 2s per SC-004/SC-005
- [X] T042 Verify README.md is in sync with final project structure per AGENTS.md and fix drift
- [X] T043 Run full suite via poetry run python -m unittest discover -v and fix all failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Reuses US1 auth/audit/store but independently testable via tools
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Observes US1/US2 via metrics but independently testable via injection flags
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Validates US1-US3 artifacts end to end

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003, T004 can run in parallel (different files)
- T006, T007 and T009-T014 can run in parallel (different files, T008 waits for T006+T007)
- T015, T016, T017, T018 can run in parallel (different test files)
- Once Foundational completes, US1-US4 phases can start in parallel if staffed
- T035, T036, T037 can run in parallel (different files)
- T040, T041 can run in parallel (verification tracks)

---

## Parallel Example: User Story 1

```bash
# Launch test task for User Story 1 first (must FAIL before implementation):
Task: "Write failing unit tests for resource reads, PII masking, cache behavior, and error envelope in src/mcp-model-content-protocol-course/module_3/task1/tests/test_resources.py"

# Implementation follows sequentially (same file, no parallelization):
Task: "Implement URI routing and MCP resource handlers for all store:// patterns in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/resources.py"
# Then filtering/masking, then cache+audit integration, then server wiring
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (quickstart scenarios 1-3)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Full release validation → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Phase 8: Convergence

**Purpose**: Close verified gaps between spec/plan/tasks and the implemented code (converge run 2026-09-18). Append-only; no existing task was modified.

- [ ] T044 Expose tool task-status query over MCP by registering a get_task tool in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/server.py per FR-017 (partial)
- [ ] T045 Serialize concurrent conflicting writes with per-entity locking or version checks returning CONFLICT in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/tools.py and src/mcp-model-content-protocol-course/module_3/task1/mcp_server/store.py per contracts/tools.md cross-cutting guarantee (partial)
- [ ] T046 Add programmatic alerting hook emitting on degraded status and error-rate threshold breach in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/ops_app.py per FR-012 (partial)
- [ ] T047 Add expires_at to ApiCredential with expired-key denial and unit tests in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/models.py, src/mcp-model-content-protocol-course/module_3/task1/mcp_server/auth.py, and task1 tests per spec edge cases (partial)
- [ ] T048 Record errors as ErrorRecord TypedDict in src/mcp-model-content-protocol-course/module_3/task1/mcp_server/metrics.py per Constitution III (partial)


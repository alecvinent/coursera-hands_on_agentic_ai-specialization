# Contract: MCP Tools

**Date**: 2026-09-18 | **Spec refs**: FR-001–FR-002, FR-006–FR-008, FR-010, FR-013–FR-014, FR-017

Every tool call requires a valid API key, passes RBAC **before** any state change, is rate-limited, and emits an `AuditRecord` (`tool.execute`) with outcome `success`/`denied`/`failed`. Validation failures change nothing. Mid-execution failures roll back partial changes. Long-running executions run asynchronously and return a `task_id` for status polling.

## `create_ticket`

Creates a support ticket.

**Input schema**:

```json
{
  "customer_id": "cust_1001 (must exist)",
  "order_id": "ord_2001 | null (must belong to same customer if present)",
  "subject": "5–120 chars, sanitized",
  "description": "1–2000 chars, sanitized"
}
```

**Output**: `{ ticket_id, status: "open", created_at }` with `processing_outcome: ok`.

**Denied/failed**: `FORBIDDEN` for `auditor`/`operator`; `VALIDATION_ERROR` (lists offending fields, no PII echo) for bad input; `DEPENDENCY_UNAVAILABLE`/`TIMEOUT` on store failure (nothing persisted).

**Allowed roles**: `admin`, `support_agent`.

## `update_order`

Updates an order's status following the legal transition map (`pending → confirmed → shipped → delivered`; `cancelled` from `pending`/`confirmed`).

**Input schema**:

```json
{
  "order_id": "ord_2001 (must exist)",
  "new_status": "confirmed | shipped | delivered | cancelled",
  "reason": "optional, ≤280 chars, sanitized"
}
```

**Output**: `{ order_id, old_status, new_status, updated_at }`.

**Denied/failed**: `FORBIDDEN` for `auditor`/`operator`; `VALIDATION_ERROR` for illegal transitions (state unchanged); concurrent conflicting writes are serialized — loser receives `CONFLICT` with current `status` and no write is lost silently.

**Allowed roles**: `admin`, `support_agent`.

## `update_ticket_status` (supporting tool)

Transitions ticket status per the legal map (`open → in_progress → resolved → closed`; `open → closed` allowed).

**Input schema**:

```json
{
  "ticket_id": "tkt_3001 (must exist)",
  "new_status": "in_progress | resolved | closed",
  "note": "optional, ≤280 chars, sanitized"
}
```

**Output**: `{ ticket_id, old_status, new_status, updated_at }`.

**Allowed roles**: `admin`, `support_agent`.

## Cross-cutting tool guarantees

1. **RBAC first, then validation**: permission is checked before any state is
   touched so unauthorized callers learn nothing; unsafe input is then rejected
   with `VALIDATION_ERROR` and zero state change.
2. **Rollback**: multi-step executions checkpoint prior state; on failure, prior state restored and `failed` audit record written.
3. **Async**: executions exceeding `Settings.TOOL_TIMEOUT_SECONDS` return `{ task_id, status: "running" }`; outcome retrievable via task status query; never blocks other requests.
4. **Rate limits**: per-key token bucket; excess → `RATE_LIMITED` + `retryAfterMs`, no state change, audit-logged as `denied`.

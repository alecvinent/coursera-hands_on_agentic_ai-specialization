# Data Model: Secure MCP Server with Monitoring

**Date**: 2026-09-18 | **Source**: [spec.md](spec.md) entities + research R4/R5

All entities are `pydantic.BaseModel` subclasses in `src/mcp_secure_server/models.py`. Storage is in-memory only (reset to seed on startup).

## Customer

Represents a person receiving support. Sensitive contact fields are role-restricted (FR-004).

| Field | Type | Rules |
|-------|------|-------|
| `customer_id` | `str` | Unique, pattern `cust_[0-9]{4,}` |
| `full_name` | `str` | Non-empty; **sensitive** (masked for `auditor`, hidden from `operator`) |
| `email` | `str` | Valid email format; **sensitive** |
| `phone` | `str \| None` | Optional; **sensitive** |
| `tier` | `CustomerTier` | `standard` \| `premium` \| `enterprise` |
| `created_at` | `datetime` | Set at seed; immutable |

Relationships: one-to-many → `Order`, `SupportTicket`.

## Order

Purchase record linked to a customer; status mutable via `update_order` tool.

| Field | Type | Rules |
|-------|------|-------|
| `order_id` | `str` | Unique, pattern `ord_[0-9]{4,}` |
| `customer_id` | `str` | Must reference an existing `Customer` |
| `items` | `list[OrderItem]` | Non-empty; each item has `product_id`, `quantity ≥ 1`, `unit_price ≥ 0` |
| `total` | `Decimal` | Must equal `sum(quantity × unit_price)`; computed, not accepted from input |
| `status` | `OrderStatus` | `pending` → `confirmed` → `shipped` → `delivered`; `cancelled` reachable from `pending`/`confirmed` only |
| `updated_at` | `datetime` | Bump on every status change |

State transitions enforced in `tools.py`; illegal transitions rejected with validation error and no state change.

## SupportTicket

Help request linked to a customer (and optionally an order).

| Field | Type | Rules |
|-------|------|-------|
| `ticket_id` | `str` | Unique, pattern `tkt_[0-9]{4,}`; server-generated on create |
| `customer_id` | `str` | Must reference an existing `Customer` |
| `order_id` | `str \| None` | If present, must reference an existing `Order` of the same customer |
| `subject` | `str` | 5–120 chars, sanitized (no control chars, HTML-escaped on render) |
| `description` | `str` | 1–2000 chars, sanitized as above |
| `status` | `TicketStatus` | `open` → `in_progress` → `resolved` → `closed`; `open` → `closed` allowed (duplicate/invalid) |
| `created_at` / `updated_at` | `datetime` | Server-set; `updated_at` bumps on change |

## Product

Catalog item referenced by orders; cacheable, never PII-bearing.

| Field | Type | Rules |
|-------|------|-------|
| `product_id` | `str` | Unique, pattern `prd_[0-9]{4,}` |
| `name` | `str` | Non-empty |
| `category` | `str` | Non-empty |
| `price` | `Decimal` | `≥ 0` |
| `in_stock` | `bool` | — |

## ApiCredential / Role

| Field | Type | Rules |
|-------|------|-------|
| `key_id` | `str` | Unique public identifier (logged in audit records) |
| `api_key` | `str` | Secret; stored only in `Settings`/`.env`, never logged, compared with `hmac.compare_digest` |
| `role` | `Role` | `admin` \| `support_agent` \| `auditor` \| `operator` |
| `revoked` | `bool` | Revoked keys authenticate as invalid |

Permission matrix (see `contracts/resources.md` and `contracts/tools.md` for per-endpoint mapping): `admin` = all; `support_agent` = read business entities + `create_ticket` + `update_order` + `update_ticket_status`; `auditor` = read business entities (PII masked) + read audit log; `operator` = health/metrics only.

## AuditRecord

Immutable log entry per data access and tool execution (FR-008).

| Field | Type | Rules |
|-------|------|-------|
| `seq` | `int` | Monotonic sequence number (ordering guarantee) |
| `timestamp` | `datetime` | Server clock (UTC) |
| `key_id` | `str` | Credential identity; `"anonymous"` for denied unauthenticated attempts |
| `role` | `str` | Role at time of action |
| `action` | `str` | `resource.read` \| `tool.execute` \| `auth.denied` |
| `target` | `str` | Resource URI or tool name |
| `inputs_hash` | `str \| None` | Hash of sanitized inputs (never raw PII) for tool executions |
| `outcome` | `Outcome` | `success` \| `denied` \| `failed` |

Append-only; if the audit sink is unavailable, the operation fails closed (deny with logged error) rather than executing unaudited.

## HealthReport / MetricSample

| Field | Type | Rules |
|-------|------|-------|
| `status` | `str` | `healthy` \| `degraded` \| `unhealthy` (degraded if any circuit open or error rate above threshold) |
| `uptime_seconds` | `float` | Since server start |
| `requests_total` | `int` | Per (endpoint, outcome) counters in `metrics.py` |
| `latency_ms_p50` / `latency_ms_p95` | `float` | Computed from in-memory samples (bounded ring buffer) |
| `error_rate` | `float` | Failed / total over trailing window |
| `dependencies` | `dict[str, str]` | Per-dependency state (`closed`/`open`/`half-open`, mock store health) |

## ErrorRecord (TypedDict, per Constitution III)

`{ step: str, error_type: str, message: str (sanitized, no PII/secrets), timestamp: datetime }`. Collected per operation; degraded outputs tagged `processing_outcome="partial"`.

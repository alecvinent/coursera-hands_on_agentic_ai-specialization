# Data Model: MCP Enterprise Integration Portfolio

**Feature**: 008-mcp-enterprise-portfolio
**Date**: 2026-09-18

## Entities

### Customer

Represents a retail customer.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| customer_id | str | required, unique | Primary key |
| name | str | required | Full name |
| email | str | required, sensitive | Masked for non-admin roles |
| phone | str | optional, sensitive | Masked for non-admin roles |
| address | str | optional, sensitive | Masked for non-admin roles |
| tier | str | enum: standard, premium, enterprise | Determines service level |
| created_at | str | required | ISO 8601 timestamp |
| order_ids | list[str] | computed | References to Order |
| ticket_ids | list[str] | computed | References to SupportTicket |

**State transitions**: None (read-only entity).

### Order

Represents a customer purchase.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| order_id | str | required, unique | Primary key |
| customer_id | str | required, FK | References Customer |
| items | list[OrderItem] | required | At least one item |
| status | str | enum: pending, confirmed, shipped, delivered, cancelled | Mutable via tool |
| total | float | required, computed | Sum of item prices |
| created_at | str | required | ISO 8601 timestamp |
| updated_at | str | required | ISO 8601 timestamp |
| version | int | required | Optimistic concurrency control |

**State transitions**:
- pending → confirmed (by support_agent, admin)
- confirmed → shipped (by admin)
- shipped → delivered (by admin)
- any → cancelled (by admin, with reason)

### SupportTicket

Represents a customer support request.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| ticket_id | str | required, unique | Primary key |
| customer_id | str | required, FK | References Customer |
| order_id | str | optional, FK | References Order |
| subject | str | required | Brief description |
| description | str | required | Full details |
| status | str | enum: open, in_progress, resolved, closed | Mutable via tool |
| created_at | str | required | ISO 8601 timestamp |
| updated_at | str | required | ISO 8601 timestamp |
| version | int | required | Optimistic concurrency control |

**State transitions**:
- open → in_progress (by support_agent, admin)
- in_progress → resolved (by support_agent, admin)
- resolved → closed (by admin)
- any → open (reopened, by admin)

### Product

Represents a catalog item.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| product_id | str | required, unique | Primary key |
| name | str | required | Product name |
| description | str | optional | Product details |
| price | float | required | Unit price |
| stock_quantity | int | required | Current inventory level |
| category | str | required | Product category |

**State transitions**: None (read-only for resources; inventory updates via tool).

### InventoryItem

Represents stock for a product at a location.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| product_id | str | required, FK | References Product |
| location | str | required | Warehouse/store identifier |
| quantity | int | required | Current stock |
| reserved | int | required | Reserved for pending orders |
| reorder_threshold | int | required | Trigger for low-stock alerts |

**State transitions**: Quantity changes via inventory update tool.

### Credential

Represents an API key with role assignment.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| key_id | str | required, unique | Identifier |
| api_key | str | required, ≥16 chars | Secret, never logged |
| role | str | enum: admin, support_agent, auditor, operator | Permission level |
| revoked | bool | required | If true, all access denied |

### AuditRecord

Immutable log entry for every access and tool execution.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| timestamp | str | required | ISO 8601 |
| key_id | str | required | Who |
| role | str | required | Role at time of action |
| action | str | required | Resource URI or tool name |
| resource_type | str | required | customer, order, ticket, product, inventory |
| inputs | dict | optional, sanitized | Tool parameters (PII masked) |
| outcome | str | enum: success, denied, failed | Result |
| latency_ms | float | required | Execution time |

### HealthReport

Operational snapshot.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| status | str | enum: healthy, degraded, unhealthy | Overall state |
| uptime_seconds | float | required | Time since start |
| request_count | int | required | Total requests |
| error_count | int | required | Total errors |
| avg_latency_ms | float | required | Rolling average |
| dependency_status | dict[str, str] | required | Per-dependency state |

## Relationships

```
Customer 1──* Order
Customer 1──* SupportTicket
Order 1──0..1 SupportTicket (optional order_id)
Order *──1 Product (via items)
InventoryItem *──1 Product (via product_id)
Credential 1──1 role (determines access to all entities)
AuditRecord *──1 Credential (via key_id)
```

## Validation Rules

- All string IDs must be non-empty and unique within their entity type.
- Status transitions must follow the defined state machine.
- Version must increment on every write (optimistic locking).
- Sensitive fields (email, phone, address) must be masked for non-admin roles.
- Audit records must be immutable once created.
- Rate limits: max 120 requests/minute per credential, burst of 20.

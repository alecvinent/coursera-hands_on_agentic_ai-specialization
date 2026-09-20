# Contract: MCP Resources

**Date**: 2026-09-18 | **Spec refs**: FR-001–FR-005, FR-008

All resources return `application/json`. Every read requires a valid API key, passes RBAC, and emits an `AuditRecord` (`resource.read`). Failures use the error envelope below — never including PII or secrets.

## Error envelope

```json
{
  "error": { "code": "string", "message": "generic, non-leaking message" },
  "processing_outcome": "ok | partial"
}
```

Codes: `UNAUTHENTICATED` (missing/invalid/revoked key) → deny; `FORBIDDEN` (role lacks permission); `NOT_FOUND` (unknown URI/id — same shape for existent-but-forbidden ids to avoid oracle leaks); `RATE_LIMITED` (includes `retryAfterMs`); `DEPENDENCY_UNAVAILABLE`; `TIMEOUT`.

## URI patterns

Base scheme `store://`. Patterns:

| Resource | URI pattern | Example |
|----------|-------------|---------|
| Customer profile | `store://customers/{customer_id}` | `store://customers/cust_1001` |
| Customer orders | `store://customers/{customer_id}/orders` | `store://customers/cust_1001/orders` |
| Customer tickets | `store://customers/{customer_id}/tickets` | `store://customers/cust_1001/tickets` |
| Order detail | `store://orders/{order_id}` | `store://orders/ord_2001` |
| Orders by status | `store://orders/status/{status}` | `store://orders/status/pending` |
| Ticket detail | `store://tickets/{ticket_id}` | `store://tickets/tkt_3001` |
| Tickets by status | `store://tickets/status/{status}` | `store://tickets/status/open` |
| Product detail | `store://products/{product_id}` | `store://products/prd_4001` |
| Product catalog | `store://products` | `store://products` |

Empty filtered views return `[]` with `processing_outcome: ok` (never an error).

## Schemas (response shapes)

- **Customer**: `{ customer_id, full_name, email, phone, tier, created_at }` — `full_name`/`email`/`phone` masked (`"***"`) for `auditor`; `operator` receives `FORBIDDEN`.
- **Order**: `{ order_id, customer_id, items[], total, status, updated_at }`.
- **Ticket**: `{ ticket_id, customer_id, order_id, subject, description, status, created_at, updated_at }`.
- **Product / catalog**: `{ product_id, name, category, price, in_stock }` (array for catalog).

## Permission matrix (reads)

| Role | customers | orders | tickets | products | audit log |
|------|-----------|--------|---------|----------|-----------|
| `admin` | full | full | full | full | read |
| `support_agent` | full | full | full | full | denied |
| `auditor` | masked PII | full | full | full | read |
| `operator` | denied | denied | denied | denied | denied |

## Caching contract

- Cache key = `(role, uri, query_hash)`; TTL = `Settings.CACHE_TTL_SECONDS`.
- Masked vs. full representations are never shared across roles.
- Stale-cache or cache-backend failure → bypass cache, serve from store, tag `processing_outcome: partial`.

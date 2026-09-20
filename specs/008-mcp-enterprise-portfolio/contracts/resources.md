# Resource Contracts: MCP Enterprise Integration Portfolio

**Feature**: 008-mcp-enterprise-portfolio
**Date**: 2026-09-18

All resources follow MCP protocol specifications. URI patterns use `retail://` prefix to distinguish from task1's `store://`.

## Customer Resources

### `retail://customers/{customer_id}`

- **MIME**: `application/json`
- **Method**: Resource read
- **Roles**: admin (full), support_agent (read), auditor (read, PII masked), operator (denied)
- **Response**:
  ```json
  {
    "customer_id": "C001",
    "name": "Alice Johnson",
    "email": "alice@example.com",  // masked for auditor: "***@***"
    "phone": "+1-555-0101",        // masked for auditor: "***"
    "address": "123 Main St",      // masked for auditor: "***"
    "tier": "premium",
    "created_at": "2026-01-15T10:30:00Z"
  }
  ```
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`

### `retail://customers/{customer_id}/orders`

- **MIME**: `application/json`
- **Method**: Resource read
- **Roles**: admin, support_agent, auditor (PII-masked), operator (denied)
- **Response**: Array of order summaries (order_id, status, total, created_at)
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`

### `retail://customers/{customer_id}/tickets`

- **MIME**: `application/json`
- **Method**: Resource read
- **Roles**: admin, support_agent, auditor (PII-masked), operator (denied)
- **Response**: Array of ticket summaries (ticket_id, subject, status, created_at)
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`

## Order Resources

### `retail://orders/{order_id}`

- **MIME**: `application/json`
- **Method**: Resource read
- **Roles**: admin, support_agent, auditor (PII-masked), operator (denied)
- **Response**:
  ```json
  {
    "order_id": "ORD001",
    "customer_id": "C001",
    "items": [{"product_id": "P001", "name": "Widget", "quantity": 2, "price": 29.99}],
    "status": "shipped",
    "total": 59.98,
    "created_at": "2026-03-01T14:00:00Z",
    "updated_at": "2026-03-05T09:00:00Z"
  }
  ```
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`

### `retail://orders/status/{status}`

- **MIME**: `application/json`
- **Method**: Resource read
- **Roles**: admin, support_agent, auditor, operator (denied)
- **Response**: Array of order summaries matching the status filter
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `VALIDATION_ERROR` (invalid status)

## Inventory Resources

### `retail://inventory/{product_id}`

- **MIME**: `application/json`
- **Method**: Resource read
- **Roles**: admin, support_agent, operator, auditor (denied)
- **Response**:
  ```json
  {
    "product_id": "P001",
    "location": "warehouse-east",
    "quantity": 150,
    "reserved": 12,
    "reorder_threshold": 20
  }
  ```
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`

### `retail://inventory/low-stock`

- **MIME**: `application/json`
- **Method**: Resource read
- **Roles**: admin, operator, support_agent (denied), auditor (denied)
- **Response**: Array of inventory items where quantity ≤ reorder_threshold
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`

## Product Resources

### `retail://products`

- **MIME**: `application/json`
- **Method**: Resource read
- **Roles**: admin, support_agent, auditor, operator (denied)
- **Response**: Array of product summaries (product_id, name, price, category)
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`

### `retail://products/{product_id}`

- **MIME**: `application/json`
- **Method**: Resource read
- **Roles**: admin, support_agent, auditor, operator (denied)
- **Response**: Full product detail (product_id, name, description, price, stock_quantity, category)
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`

## Error Response Format

All errors follow the same structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Generic, non-leaking message",
    "retryAfterMs": 5000  // only for RATE_LIMITED
  }
}
```

Error codes: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR`, `RATE_LIMITED`, `DEPENDENCY_UNAVAILABLE`, `TIMEOUT`

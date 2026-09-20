# Tool Contracts: MCP Enterprise Integration Portfolio

**Feature**: 008-mcp-enterprise-portfolio
**Date**: 2026-09-18

All tools follow MCP protocol specifications. Every tool execution is authenticated, RBAC-checked, rate-limited, validated, and audit-logged.

## Order Processing Tools

### `create_order`

Creates a new order for a customer.

- **Parameters**:
  ```json
  {
    "customer_id": "C001",           // required, string
    "items": [                        // required, array of objects
      {"product_id": "P001", "quantity": 2}
    ]
  }
  ```
- **Roles**: admin, support_agent
- **Behavior**: Validates customer exists, validates all products exist and have sufficient stock, reserves inventory, creates order with status "pending", computes total.
- **Response**:
  ```json
  {
    "order_id": "ORD002",
    "status": "pending",
    "total": 59.98,
    "items": [...]
  }
  ```
- **Rollback**: If any step fails, all partial changes are reverted (inventory unreserved, order not created).
- **Audit**: Logged with inputs (sanitized), outcome, latency.
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `VALIDATION_ERROR` (invalid product, insufficient stock), `DEPENDENCY_UNAVAILABLE`

### `update_order_status`

Updates the status of an existing order.

- **Parameters**:
  ```json
  {
    "order_id": "ORD001",            // required, string
    "new_status": "shipped",          // required, enum: confirmed, shipped, delivered, cancelled
    "reason": "Shipped via FedEx",    // optional, string
    "expected_version": 3             // optional, int (optimistic locking)
  }
  ```
- **Roles**: admin (all transitions), support_agent (pending→confirmed, confirmed→pending only)
- **Behavior**: Validates transition is legal, checks version if provided, updates status and version, records reason.
- **Response**: Updated order summary.
- **Rollback**: On failure, status reverts to prior value.
- **Audit**: Logged with inputs, outcome, latency.
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR` (invalid transition), `DEPENDENCY_UNAVAILABLE`

## Inventory Tools

### `update_inventory`

Updates stock quantity for a product.

- **Parameters**:
  ```json
  {
    "product_id": "P001",            // required, string
    "quantity_change": -10,           // required, int (negative = decrease, positive = increase)
    "reason": "Sold 10 units",        // optional, string
    "location": "warehouse-east"      // optional, string (defaults to primary)
  }
  ```
- **Roles**: admin, operator
- **Behavior**: Validates product exists, applies quantity change (must not go below zero), updates timestamp.
- **Response**:
  ```json
  {
    "product_id": "P001",
    "quantity": 140,
    "previous_quantity": 150,
    "location": "warehouse-east"
  }
  ```
- **Rollback**: If update fails, quantity reverts.
- **Audit**: Logged.
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR` (insufficient stock for decrease), `DEPENDENCY_UNAVAILABLE`

### `reserve_inventory`

Reserves stock for a pending order.

- **Parameters**:
  ```json
  {
    "product_id": "P001",            // required, string
    "quantity": 2,                    // required, int
    "order_id": "ORD002"             // required, string
  }
  ```
- **Roles**: admin, support_agent
- **Behavior**: Validates sufficient unreserved stock, increments reserved count, links to order.
- **Response**: Updated reservation status.
- **Rollback**: On failure, reservation reverts.
- **Audit**: Logged.
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR` (insufficient unreserved stock), `DEPENDENCY_UNAVAILABLE`

## Customer Service Tools

### `create_support_ticket`

Creates a new support ticket.

- **Parameters**:
  ```json
  {
    "customer_id": "C001",           // required, string
    "subject": "Order not received",  // required, string (1-200 chars)
    "description": "Order ORD001 was...", // required, string (1-5000 chars)
    "order_id": "ORD001"             // optional, string
  }
  ```
- **Roles**: admin, support_agent
- **Behavior**: Validates customer exists, validates order if provided, creates ticket with status "open".
- **Response**:
  ```json
  {
    "ticket_id": "TKT001",
    "status": "open",
    "subject": "Order not received"
  }
  ```
- **Rollback**: On failure, ticket not created.
- **Audit**: Logged.
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `VALIDATION_ERROR`, `DEPENDENCY_UNAVAILABLE`

### `update_ticket_status`

Updates the status of a support ticket.

- **Parameters**:
  ```json
  {
    "ticket_id": "TKT001",           // required, string
    "new_status": "in_progress",      // required, enum: in_progress, resolved, closed, open
    "note": "Investigating...",       // optional, string
    "expected_version": 2             // optional, int
  }
  ```
- **Roles**: admin, support_agent
- **Behavior**: Validates transition is legal, checks version if provided, updates status.
- **Response**: Updated ticket summary.
- **Rollback**: On failure, status reverts.
- **Audit**: Logged.
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR`, `DEPENDENCY_UNAVAILABLE`

### `get_task_status`

Polls the outcome of an asynchronous tool execution.

- **Parameters**:
  ```json
  {
    "task_id": "task-abc-123"         // required, string
  }
  ```
- **Roles**: admin, support_agent, operator
- **Behavior**: Returns the status and result of a previously submitted async tool call.
- **Response**:
  ```json
  {
    "task_id": "task-abc-123",
    "status": "completed",
    "result": {...}
  }
  ```
- **Errors**: `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`

## Common Tool Behavior

- **Input validation**: All inputs are validated before any state change. Invalid input returns `VALIDATION_ERROR` without modifying data.
- **Optimistic locking**: Tools that modify state accept optional `expected_version`. If provided and mismatched, returns `VALIDATION_ERROR` with current version.
- **Async execution**: Slow operations (>5s) return a `task_id` immediately; poll with `get_task_status`.
- **Rollback**: All partial changes are reverted on failure. Audit record indicates "failed" outcome.
- **Rate limiting**: Max 120 requests/minute per credential. Exceeded requests receive `RATE_LIMITED` with `retryAfterMs`.

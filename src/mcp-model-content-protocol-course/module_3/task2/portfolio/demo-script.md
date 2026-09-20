# MCP Enterprise Integration Portfolio — Live Demo Script

Step-by-step demonstration of the production MCP server with expected outputs.

---

## Prerequisites

```bash
# From the task2 directory
cd src/mcp-model-content-protocol-course/module_3/task2

# Install dependencies
poetry install

# Set environment variables (or use .env file)
export MCP_PORTFOLIO_API_KEY="test-admin-key-12345678"
```

---

## Step 1: Server Startup

### 1.1 Start in STDIO mode (local testing)

```bash
python -m mcp_portfolio.server --transport stdio --api-key "test-admin-key-12345678"
```

**Expected**: Server starts and listens on stdin/stdout for MCP protocol messages.

### 1.2 Start in HTTP mode (production-like)

```bash
python -m mcp_portfolio.server \
  --transport http \
  --host 127.0.0.1 \
  --port 8000 \
  --ops-port 8001 \
  --api-key "test-admin-key-12345678"
```

**Expected output**:
```
INFO | building MCP server for key_id=admin role=admin
INFO | ops sidecar on 127.0.0.1:8001
```

### 1.3 Verify health

```bash
curl http://127.0.0.1:8001/health
```

**Expected output**:
```json
{
  "status": "healthy",
  "uptime_seconds": 2.34,
  "dependencies": {
    "mock_store": "closed",
    "audit_sink": "ok"
  },
  "version": "0.1.0"
}
```

---

## Step 2: Authentication with Different Roles

The server uses pre-configured API keys, each mapped to a role. Configure these in your `.env`:

```
MCP_PORTFOLIO_API_KEYS='{
  "admin": {"key_id": "admin", "api_key": "test-admin-key-12345678", "role": "admin"},
  "support_1": {"key_id": "support_1", "api_key": "test-support-key-12345678", "role": "support_agent"},
  "auditor_1": {"key_id": "auditor_1", "api_key": "test-auditor-key-12345678", "role": "auditor"},
  "operator_1": {"key_id": "operator_1", "api_key": "test-operator-key-12345678", "role": "operator"}
}'
```

### 2.1 Admin role (full access)

```bash
curl -H "X-Api-Key: test-admin-key-12345678" \
     http://127.0.0.1:8001/metrics | python -m json.tool
```

**Expected**: Returns full metrics snapshot (200 OK).

### 2.2 Support agent role

```bash
curl -H "X-Api-Key: test-support-key-12345678" \
     http://127.0.0.1:8001/metrics
```

**Expected**: 403 Forbidden — support agents cannot access metrics.

### 2.3 Operator role

```bash
curl -H "X-Api-Key: test-operator-key-12345678" \
     http://127.0.0.1:8001/metrics
```

**Expected**: 200 OK — operators have metrics access.

### 2.4 No credentials

```bash
curl http://127.0.0.1:8001/metrics
```

**Expected**: 401 Unauthorized.

---

## Step 3: Resource Reads

### 3.1 Customer profile

```bash
curl -H "X-Api-Key: test-admin-key-12345678" \
     "http://127.0.0.1:8000/retail://customers/cust_0001"
```

**Expected output**:
```json
{
  "data": {
    "customer_id": "cust_0001",
    "full_name": "Customer 1",
    "email": "customer1@example.com",
    "phone": "+1-555-0001",
    "address": "1 Main St, Anytown",
    "tier": "premium",
    "created_at": "2026-09-18T..."
  },
  "processing_outcome": "ok"
}
```

### 3.2 Customer profile (auditor role — PII masked)

```bash
curl -H "X-Api-Key: test-auditor-key-12345678" \
     "http://127.0.0.1:8000/retail://customers/cust_0001"
```

**Expected output** (note masked fields):
```json
{
  "data": {
    "customer_id": "cust_0001",
    "full_name": "Customer 1",
    "email": "***",
    "phone": "***",
    "address": "***",
    "tier": "premium",
    "created_at": "2026-09-18T..."
  },
  "processing_outcome": "ok"
}
```

### 3.3 Customer orders

```bash
curl -H "X-Api-Key: test-admin-key-12345678" \
     "http://127.0.0.1:8000/retail://customers/cust_0001/orders"
```

**Expected output**: Array of order objects for customer `cust_0001`.

### 3.4 Product catalog

```bash
curl -H "X-Api-Key: test-admin-key-12345678" \
     "http://127.0.0.1:8000/retail://products"
```

**Expected output**: Array of product objects (prd_0001 through prd_0010).

### 3.5 Low stock inventory

```bash
curl -H "X-Api-Key: test-admin-key-12345678" \
     "http://127.0.0.1:8000/retail://inventory/low-stock"
```

**Expected output**: Array of inventory items where `quantity <= reorder_threshold`.

### 3.6 Orders by status

```bash
curl -H "X-Api-Key: test-admin-key-12345678" \
     "http://127.0.0.1:8000/retail://orders/status/pending"
```

**Expected output**: Array of orders with `status: "pending"`.

---

## Step 4: Tool Executions

### 4.1 Create a support ticket

```bash
curl -X POST -H "Content-Type: application/json" \
     -H "X-Api-Key: test-admin-key-12345678" \
     -d '{
       "customer_id": "cust_0001",
       "subject": "Damaged item received",
       "description": "Product 3 arrived with cracked packaging",
       "order_id": "ord_0001"
     }' \
     http://127.0.0.1:8000/tools/create_support_ticket
```

**Expected output**:
```json
{
  "data": {
    "ticket_id": "tkt_4016",
    "status": "open",
    "created_at": "2026-09-18T..."
  },
  "processing_outcome": "ok"
}
```

### 4.2 Update order status (valid transition)

```bash
curl -X POST -H "Content-Type: application/json" \
     -H "X-Api-Key: test-admin-key-12345678" \
     -d '{
       "order_id": "ord_0001",
       "new_status": "confirmed",
       "reason": "Payment verified"
     }' \
     http://127.0.0.1:8000/tools/update_order_status
```

**Expected output**:
```json
{
  "data": {
    "order_id": "ord_0001",
    "old_status": "pending",
    "new_status": "confirmed",
    "updated_at": "2026-09-18T..."
  },
  "processing_outcome": "ok"
}
```

### 4.3 Update order status (invalid transition)

```bash
curl -X POST -H "Content-Type: application/json" \
     -H "X-Api-Key: test-admin-key-12345678" \
     -d '{
       "order_id": "ord_0001",
       "new_status": "delivered"
     }' \
     http://127.0.0.1:8000/tools/update_order_status
```

**Expected output**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "illegal transition confirmed -> delivered"
  },
  "processing_outcome": "ok"
}
```

### 4.4 Create an order

```bash
curl -X POST -H "Content-Type: application/json" \
     -H "X-Api-Key: test-admin-key-12345678" \
     -d '{
       "customer_id": "cust_0001",
       "items": [
         {"product_id": "prd_0001", "quantity": 2, "unit_price": 49.99},
         {"product_id": "prd_0003", "quantity": 1, "unit_price": 129.99}
       ]
     }' \
     http://127.0.0.1:8000/tools/create_order
```

**Expected output**:
```json
{
  "data": {
    "order_id": "ord_10001",
    "status": "pending",
    "total": "229.97",
    "created_at": "2026-09-18T..."
  },
  "processing_outcome": "ok"
}
```

### 4.5 Update inventory

```bash
curl -X POST -H "Content-Type: application/json" \
     -H "X-Api-Key: test-operator-key-12345678" \
     -d '{
       "product_id": "prd_0001",
       "quantity": 50
     }' \
     http://127.0.0.1:8000/tools/update_inventory
```

**Expected output**:
```json
{
  "data": {"product_id": "prd_0001", "quantity": 50},
  "processing_outcome": "ok"
}
```

### 4.6 Reserve inventory

```bash
curl -X POST -H "Content-Type: application/json" \
     -H "X-Api-Key: test-operator-key-12345678" \
     -d '{
       "product_id": "prd_0001",
       "quantity": 5
     }' \
     http://127.0.0.1:8000/tools/reserve_inventory
```

**Expected output**:
```json
{
  "data": {"product_id": "prd_0001", "reserved": 5, "available": 45},
  "processing_outcome": "ok"
}
```

---

## Step 5: Error Scenarios

### 5.1 Unauthorized access (missing credentials)

```bash
curl "http://127.0.0.1:8000/retail://customers/cust_0001"
```

**Expected output**:
```json
{
  "error": {"code": "UNAUTHENTICATED", "message": "invalid or missing credentials"},
  "processing_outcome": "ok"
}
```

### 5.2 Forbidden access (insufficient role)

```bash
curl -H "X-Api-Key: test-auditor-key-12345678" \
     -X POST -H "Content-Type: application/json" \
     -d '{"customer_id": "cust_0001", "items": []}' \
     http://127.0.0.1:8000/tools/create_order
```

**Expected output**:
```json
{
  "error": {"code": "FORBIDDEN", "message": "insufficient permissions"},
  "processing_outcome": "ok"
}
```

### 5.3 Resource not found

```bash
curl -H "X-Api-Key: test-admin-key-12345678" \
     "http://127.0.0.1:8000/retail://customers/cust_9999"
```

**Expected output**:
```json
{
  "error": {"code": "NOT_FOUND", "message": "resource not found"},
  "processing_outcome": "ok"
}
```

### 5.4 Invalid ticket transition

```bash
curl -X POST -H "Content-Type: application/json" \
     -H "X-Api-Key: test-admin-key-12345678" \
     -d '{"ticket_id": "tkt_0001", "new_status": "open"}' \
     http://127.0.0.1:8000/tools/update_ticket_status
```

**Expected output**:
```json
{
  "error": {"code": "VALIDATION_ERROR", "message": "illegal transition <current_status> -> open"},
  "processing_outcome": "ok"
}
```

### 5.5 Inventory validation error (negative quantity)

```bash
curl -X POST -H "Content-Type: application/json" \
     -H "X-Api-Key: test-operator-key-12345678" \
     -d '{"product_id": "prd_0001", "quantity": -5}' \
     http://127.0.0.1:8000/tools/update_inventory
```

**Expected output**:
```json
{
  "error": {"code": "VALIDATION_ERROR", "message": "quantity must be a non-negative integer"},
  "processing_outcome": "ok"
}
```

### 5.6 Insufficient stock for reservation

```bash
curl -X POST -H "Content-Type: application/json" \
     -H "X-Api-Key: test-operator-key-12345678" \
     -d '{"product_id": "prd_0001", "quantity": 9999}' \
     http://127.0.0.1:8000/tools/reserve_inventory
```

**Expected output**:
```json
{
  "error": {"code": "VALIDATION_ERROR", "message": "insufficient stock: <available> available"},
  "processing_outcome": "ok"
}
```

---

## Step 6: Monitoring Checks

### 6.1 Health endpoint (public, no auth)

```bash
curl http://127.0.0.1:8001/health
```

**Expected output**:
```json
{
  "status": "healthy",
  "uptime_seconds": 145.2,
  "dependencies": {"mock_store": "closed", "audit_sink": "ok"},
  "version": "0.1.0"
}
```

### 6.2 Metrics endpoint (operator/admin only)

```bash
curl -H "X-Api-Key: test-admin-key-12345678" \
     http://127.0.0.1:8001/metrics
```

**Expected output**:
```json
{
  "requests_total": {"resource.read:success": 12, "tool.execute:success": 5},
  "requests_count": 17,
  "latency_ms": {"p50": 3.2, "p95": 45.8, "mean": 8.7},
  "error_rate": 0.12,
  "rate_limited_total": 0,
  "cache": {"hits": 8, "misses": 4},
  "circuit_states": {"mock_store": "closed"}
}
```

### 6.3 HTML dashboard (operator/admin only)

```bash
curl -H "X-Api-Key: test-admin-key-12345678" \
     http://127.0.0.1:8001/dashboard
```

**Expected**: HTML page with status banner, uptime, request summary, and recent errors table.

### 6.4 Operator role — metrics access

```bash
curl -H "X-Api-Key: test-operator-key-12345678" \
     http://127.0.0.1:8001/metrics
```

**Expected**: 200 OK — operators have metrics/dashboard access.

---

## Step 7: Optimistic Locking (Concurrency Control)

### 7.1 First update succeeds (version 0 → 1)

```bash
curl -X POST -H "Content-Type: application/json" \
     -H "X-Api-Key: test-admin-key-12345678" \
     -d '{"order_id": "ord_0002", "new_status": "confirmed"}' \
     http://127.0.0.1:8000/tools/update_order_status
```

**Expected**: `{"data": {"order_id": "ord_0002", "old_status": "pending", "new_status": "confirmed", ...}}`

### 7.2 Stale update detected (expected_version conflicts)

```bash
curl -X POST -H "Content-Type: application/json" \
     -H "X-Api-Key: test-admin-key-12345678" \
     -d '{"order_id": "ord_0002", "new_status": "shipped", "expected_version": 0}' \
     http://127.0.0.1:8000/tools/update_order_status
```

**Expected output**:
```json
{
  "error": {"code": "CONFLICT", "message": "order changed concurrently (version 1)"},
  "current": {"status": "confirmed", "version": 1},
  "processing_outcome": "ok"
}
```

---

## Step 8: Cache Behavior

### 8.1 First read — cache miss

```bash
curl -H "X-Api-Key: test-admin-key-12345678" \
     "http://127.0.0.1:8000/retail://products/prd_0001"
```

### 8.2 Second read — cache hit (same data, faster)

```bash
curl -H "X-Api-Key: test-admin-key-12345678" \
     "http://127.0.0.1:8000/retail://products/prd_0001"
```

### 8.3 Verify via metrics

```bash
curl -H "X-Api-Key: test-admin-key-12345678" \
     http://127.0.0.1:8001/metrics | python -c "import sys,json; d=json.load(sys.stdin); print(d['cache'])"
```

**Expected**: `{"hits": <incremented>, "misses": <initial>}`

---

## Step 9: Audit Log Verification

Audit records are append-only with fail-closed semantics. Each record contains:

| Field | Description |
|-------|-------------|
| `seq` | Sequential number |
| `timestamp` | UTC datetime |
| `key_id` | Authenticated key identifier |
| `role` | Role that performed the action |
| `action` | Operation type (resource.read, tool.execute, auth.denied) |
| `resource_type` | URI or tool name |
| `inputs_hash` | SHA-256 hash of input parameters (privacy-preserving) |
| `outcome` | success / denied / failed |
| `latency_ms` | Operation latency in milliseconds |

```python
# Verify audit trail exists
from mcp_portfolio.audit import AuditLog
# audit_log.list_records()  # Returns list of AuditRecord objects
```

---

## Step 10: Cleanup

```bash
# Stop the server
Ctrl+C

# Or for Docker deployment
docker stop mcp-portfolio
```

---

## Summary of Demo Coverage

| Area | Steps | What It Proves |
|------|-------|----------------|
| Startup | 1 | Clean initialization with ops sidecar |
| Auth/RBAC | 2 | 4 roles, correct permission boundaries |
| Resources | 3 | 9 retail:// URIs, PII masking, cache |
| Tools | 4 | Create/update operations, validation |
| Errors | 5 | Unauthenticated, forbidden, not found, validation |
| Monitoring | 6 | Health, metrics, dashboard |
| Concurrency | 7 | Optimistic locking, conflict detection |
| Audit | 9 | Append-only, fail-closed, SHA-256 hashing |

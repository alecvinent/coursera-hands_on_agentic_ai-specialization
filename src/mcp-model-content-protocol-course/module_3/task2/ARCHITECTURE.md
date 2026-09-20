# ARCHITECTURE.md — MCP Enterprise Integration Portfolio

## Design Decisions

This document records how the architecture assessment informed the MCP server design and security/deployment strategy.

---

## Decision Log

| ID | Date | Decision | Rationale | Status |
|----|------|----------|-----------|--------|
| DEC-001 | 2026-09 | Use MCP as primary integration protocol | AI-native tool discovery; 61% faster integration vs REST custom bridge | Approved |
| DEC-002 | 2026-09 | Maintain REST fallback for non-AI consumers | Existing batch ETL and monitoring tools require REST; zero disruption guarantee | Approved |
| DEC-003 | 2026-09 | Single centralized MCP server | Simplifies tool registry management; easier security policy enforcement | Approved |
| DEC-004 | 2026-09 | OAuth 2.0 + JWT for authentication | Industry standard; short-lived tokens reduce credential leakage risk | Approved |
| DEC-005 | 2026-09 | Deny-by-default RBAC for tool access | Principle of least privilege; critical for PII/financial data protection | Approved |
| DEC-006 | 2026-09 | Redis caching layer for hot data | Customer profiles and inventory snapshots accessed every 2-3 seconds; caching reduces latency from 200ms to 15ms | Approved |
| DEC-007 | 2026-09 | Horizontal scaling via Kubernetes | Risk assessment identified peak load as High risk; K8s auto-scaling mitigates | Approved |
| DEC-008 | 2026-09 | Circuit breakers per enterprise system | Risk R-002 identified cascading failure risk; circuit breakers isolate blast radius | Approved |
| DEC-009 | 2026-09 | Audit logging for all tool calls | Required for GDPR/CCPA compliance; also enables debugging and usage analytics | Approved |
| DEC-010 | 2026-09 | Shadow mode before full production | Change management risk (R-007) mitigated by letting humans validate AI suggestions first | Approved |

---

## Request Lifecycle

Every tool call from an AI agent through the MCP server follows this path:

```
1. Client → MCP Server
   └─ Client sends JSON-RPC tool_call with method + params
   └─ Request includes JWT token in Authorization header

2. MCP Server → Auth Gateway
   └─ Validate JWT signature, expiry, and audience claim
   └─ Extract client identity and allowed tool scopes
   └─ Reject if: token expired, invalid signature, insufficient scope

3. MCP Server → Rate Limiter
   └─ Check per-client rate limit (50 calls/min default)
   └─ Check per-tool rate limit (1000 calls/min per system)
   └─ Reject with 429 if exceeded

4. MCP Server → Tool Registry
   └─ Look up tool by method name
   └─ Validate params against tool's JSON Schema
   └─ Reject with -32602 (Invalid Params) if schema validation fails

5. MCP Server → Cache Layer (Redis)
   └─ Check if fresh cached response exists (TTL: 30s for inventory, 5min for customer data)
   └─ If cache hit: return cached response, log as "cache_hit"
   └─ If cache miss: proceed to step 6

6. MCP Server → Enterprise System Adapter
   └─ Circuit breaker check: is system healthy?
   └─ If circuit OPEN: return cached stale data (if available) or error
   └─ If circuit CLOSED: forward request to enterprise system

7. Enterprise System → MCP Server
   └─ Receive response from CRM/ERP/Inventory/Support/Analytics
   └─ Transform to MCP tool result format (JSON content blocks)
   └─ Apply PII masking if response contains sensitive data

8. MCP Server → Audit Log
   └─ Log: timestamp, client_id, tool_name, params_hash, response_status, latency_ms
   └─ Async write to audit store (non-blocking)

9. MCP Server → Client
   └─ Return JSON-RPC result with tool response
   └─ Include latency header for client-side monitoring
```

---

## Write Lifecycle

Write operations (create_support_ticket, update_inventory, modify_order) follow an enhanced path:

```
1-4. Same as Request Lifecycle (validation + auth)

5. MCP Server → Pre-Flight Check
   └─ Validate write operation against business rules
   └─ Check for conflicting concurrent writes (optimistic locking)
   └─ Flag if write affects >1 system (multi-system transaction)

6. MCP Server → Enterprise System (Write)
   └─ Execute write with idempotency key (client-provided or server-generated)
   └─ Wait for confirmation (sync) or accept async acknowledgement
   └─ Circuit breaker applies

7. MCP Server → Cache Invalidation
   └─ Invalidate affected cache keys
   └─ Broadcast cache invalidation event (for multi-replica deployments)

8. MCP Server → Audit Log (Enhanced)
   └─ Log: operation_type, before_snapshot, after_snapshot, affected_systems
   └─ Required for compliance (audit trail for data modifications)

9. MCP Server → Client
   └─ Return success/failure with write confirmation
   └─ Include idempotency key in response for retry safety
```

---

## Failure Model

### Failure Categories

| Category | Examples | Handling Strategy |
|----------|----------|-------------------|
| **Transient** | Network timeout, temporary overload, DNS blip | Retry with exponential backoff (3 attempts, 1s/2s/4s) |
| **System Down** | Enterprise system completely unreachable | Circuit breaker opens after 5 consecutive failures; serve cached data; alert ops |
| **Data Error** | Invalid response format, missing required fields | Return tool error to client; log for investigation; do not retry |
| **Auth Failure** | Expired token, insufficient permissions | Immediate rejection; no retry; return clear error message |
| **Rate Limit** | Client exceeds call quota | 429 response with Retry-After header; no retry |
| **Partial Failure** | Multi-system write succeeds on System A, fails on System B | Compensating transaction (rollback System A); alert for manual review |

### Circuit Breaker Configuration

```
Failure Threshold: 5 consecutive failures
Open Duration: 30 seconds (then half-open)
Half-Open: Allow 1 probe request
  - If success: close circuit
  - If failure: re-open for 60 seconds (exponential)
```

### Degraded Mode Behavior

When enterprise systems are partially unavailable:

| System Down | Degraded Behavior |
|-------------|-------------------|
| CRM | AI agent can still handle inventory/support queries; customer context returns "unavailable" |
| ERP | Order status queries return cached data (up to 1 hour stale); writes queued for retry |
| Inventory | Stock queries return last-known values; writes blocked; alert triggered |
| Support Platform | Ticket creation fails gracefully; agent provides manual escalation path |
| Analytics | Sales metrics unavailable; AI agent acknowledges limitation; non-critical tool |
| Competitor Intel | Rate-limited external API; non-critical; tool returns "service unavailable" |

---

## Observability

### Metrics Collected

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `mcp_tool_call_total` | Counter | tool_name, client_id, status | Total tool calls |
| `mcp_tool_call_latency_ms` | Histogram | tool_name, target_system | Latency distribution |
| `mcp_circuit_breaker_state` | Gauge | target_system | Circuit breaker status |
| `mcp_cache_hit_ratio` | Gauge | tool_name | Cache effectiveness |
| `mcp_auth_rejection_total` | Counter | reason | Security monitoring |
| `mcp_write_operation_total` | Counter | tool_name, status | Write operation tracking |

### Logging Standards

All MCP server logs use structured JSON format:

```json
{
  "timestamp": "2026-09-18T14:32:01.123Z",
  "level": "info",
  "event": "tool_call",
  "client_id": "ai-agent-cs-001",
  "tool_name": "get_customer_context",
  "latency_ms": 145,
  "status": "success",
  "target_system": "crm",
  "trace_id": "abc-123-def-456"
}
```

### Alerting Rules

| Condition | Severity | Action |
|-----------|----------|--------|
| Tool call latency > 500ms (p95) for 5 minutes | Warning | Page on-call engineer |
| Circuit breaker OPEN for > 2 minutes | Critical | Page on-call + incident channel |
| Auth rejection rate > 10% of requests | Critical | Security team alert |
| Cache hit ratio < 50% for 15 minutes | Warning | Review caching config |
| Write operation failure rate > 5% | Critical | Page on-call; pause affected writes |

### Distributed Tracing

- All tool calls are assigned a `trace_id` propagated through the entire request chain
- Trace spans: `mcp.request` → `mcp.auth` → `mcp.tool_lookup` → `mcp.cache_check` → `mcp.system_call` → `mcp.response`
- Integration with Jaeger/Zipkin for trace visualization
- Sampling rate: 100% for errors, 10% for success (configurable)

---

## References

- Architecture Assessment: `architecture/architecture-diagram.md`
- Protocol Comparison: `architecture/mcp-vs-traditional.md`
- Risk Register: `architecture/risk-assessment.md`
- ROI Analysis: `architecture/roi-analysis.md`
- Executive Summary: `architecture/executive-summary.md`

# Scaling & Performance Guide

## Connection Pooling

The MCP Portfolio communicates with downstream mock services over HTTP. Connection pooling reduces TCP handshake overhead.

### uvicorn / FastAPI Tuning

```yaml
# docker-compose.yml — uvicorn worker config
CMD: >
  python -m mcp_portfolio.server
  --transport http
  --port 8000
  --ops-port 8001
  --workers 4
```

| Setting | Recommended | Notes |
|---------|-------------|-------|
| `--workers` | 2–4 per CPU core | Each worker is a separate process with its own store; use shared state if scaling beyond 1 worker |
| `--limit-concurrency` | 200 | Prevents worker overload |
| `--backlog` | 64 | Queue depth for incoming connections |
| `--timeout-keep-alive` | 30 s | Frees idle connections |

### OS-Level Tuning

```bash
# Increase file descriptor limit
ulimit -n 65536

# Enable TCP reuse (Linux sysctl)
sysctl -w net.ipv4.tcp_tw_reuse=1
sysctl -w net.core.somaxconn=4096
```

---

## Caching Strategy

The built-in `TTLCache` (`mcp_portfolio.cache`) provides per-key caching with configurable TTL.

### Configuration

| Env Variable | Default | Description |
|--------------|---------|-------------|
| `MCP_PORTFOLIO_CACHE_TTL_SECONDS` | 60 | Time-to-live for cached entries |

### Cache Key Design

Use **role-scoped keys** to prevent cross-role data leakage:

```python
# Pseudo-implementation
cache_key = f"{role}:{resource_type}:{resource_id}"
# e.g. "admin:customer:cust_00012"
```

### When to Cache

| Data Type | Cache? | TTL | Rationale |
|-----------|--------|-----|-----------|
| Customer lookup | Yes | 60 s | Read-heavy, rarely mutated |
| Order list | Yes | 30 s | Moderate mutation rate |
| Product catalog | Yes | 120 s | Low mutation rate |
| Support tickets | No | — | Write-heavy, real-time status matters |
| Inventory levels | No | — | Must be current for reservations |

### Cache Metrics

Monitor via `/metrics`:

```json
{
  "cache": { "hits": 1420, "misses": 38 }
}
```

**Target hit ratio**: > 90%. If below 70%, review TTL and key granularity.

---

## Horizontal Scaling

### Architecture

```
                    ┌─────────────────┐
                    │  Load Balancer   │
                    │  (nginx / ALB)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
        │  Worker 1  │ │  Worker 2  │ │  Worker 3  │
        │  :8000     │ │  :8001     │ │  :8002     │
        └───────────┘ └───────────┘ └───────────┘
```

### docker-compose Scale

```bash
docker compose up -d --scale mcp-portfolio=3
```

**Limitation**: Each worker has an independent in-memory store. For shared state, introduce Redis or PostgreSQL.

### Load Balancer Config (nginx)

```nginx
upstream mcp_backend {
    least_conn;
    server 127.0.0.1:8000 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 weight=1 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8002 weight=1 max_fails=3 fail_timeout=30s;

    keepalive 32;
}

server {
    listen 443 ssl;

    location / {
        proxy_pass http://mcp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_http_version 1.1;
        proxy_connect_timeout 5s;
        proxy_read_timeout 60s;
    }
}
```

### Health-Aware Routing

Configure the load balancer to check `/health` on each upstream:

```nginx
location /health {
    proxy_pass http://127.0.0.1:8001/health;
    access_log off;
}
```

Remove unhealthy workers from rotation automatically with `max_fails` and `fail_timeout`.

---

## Load Testing

### Tools

| Tool | Use Case |
|------|----------|
| **Locust** | Python-native; easy to script MCP tool calls |
| **k6** | Lightweight; good for HTTP endpoint benchmarks |
| **wrk** | Raw throughput testing |

### Test Script (Locust)

```python
from locust import HttpUser, task, between

class MCPUUser(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def health(self):
        self.client.get("/health")

    @task(5)
    def list_customers(self):
        self.client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "list_customers", "arguments": {"limit": 10}},
                "id": 1,
            },
            headers={"X-Api-Key": "test-admin-key"},
        )

    @task(2)
    def get_order(self):
        self.client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "get_order", "arguments": {"order_id": "ord_00001"}},
                "id": 2,
            },
            headers={"X-Api-Key": "test-admin-key"},
        )
```

### Execution

```bash
# 100 users, 10 users/s spawn rate, 5-minute test
locust -f locustfile.py --host=http://localhost:8000 \
    --users 100 --spawn-rate 10 --run-time 5m --headless
```

---

## Performance Benchmarks & Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **p50 latency** | < 50 ms | `/metrics` → `latency_ms.p50` |
| **p95 latency** | < 2000 ms | `/metrics` → `latency_ms.p95` |
| **Error rate** | < 1% | `/metrics` → `error_rate` |
| **Cache hit ratio** | > 90% | `/metrics` → `cache.hits / (hits + misses)` |
| **Throughput** | > 500 req/s | Load test (k6, locust) |
| **Memory per worker** | < 256 MB | `docker stats` |
| **Startup time** | < 5 s | Time from `docker start` to `healthy` |
| **Recovery time** | < 30 s | Time from crash to `healthy` |

### Capacity Planning

| Concurrent Users | Workers | Memory | CPU |
|-----------------|---------|--------|-----|
| 1–50 | 1 | 128 MB | 0.25 |
| 50–200 | 2 | 256 MB | 0.5 |
| 200–500 | 4 | 512 MB | 1.0 |
| 500+ | 4+ | 1 GB+ | 2+ |

Scale beyond 500 concurrent users with:
- Horizontal scaling (more replicas)
- External caching layer (Redis)
- Persistent storage (PostgreSQL)
- CDN for static dashboard assets

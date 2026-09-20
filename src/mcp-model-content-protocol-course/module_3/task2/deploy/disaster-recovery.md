# Disaster Recovery Procedures

## Overview

The MCP Portfolio uses an **in-memory store** by design. There is no external database — all data is seeded on startup. This simplifies DR: recovery means restarting the server with the same configuration.

**Recovery Time Objective (RTO):** < 5 minutes  
**Recovery Point Objective (RPO):** 0 (data is regenerated, not restored)

---

## Seed Data Reset Procedure

If the in-memory store is corrupted or lost (container restart, crash, OOM kill):

1. **Stop the existing server** (if running):
   ```bash
   docker stop mcp-portfolio
   ```

2. **Restart with the same environment**:
   ```bash
   docker start mcp-portfolio
   # or
   docker compose -f deploy/docker-compose.yml up -d
   ```

3. **Verify seed data** — call a read-only tool (e.g., `list_customers`) to confirm data is present.

4. **Verify health**:
   ```bash
   curl http://localhost:8001/health
   # Expected: {"status": "healthy", ...}
   ```

The server re-seeds on every startup using the `seed` value in your configuration. The same seed produces identical data.

---

## Audit Log Export Procedure

Audit logs are held in memory and lost on restart. Export before planned restarts:

1. **Export via ops API**:
   ```bash
   curl -H "X-Api-Key: <operator-key>" \
        http://localhost:8001/metrics > metrics_$(date +%Y%m%d_%H%M%S).json
   ```

2. **Export dashboard snapshot**:
   ```bash
   curl -H "X-Api-Key: <operator-key>" \
        http://localhost:8001/dashboard > dashboard_$(date +%Y%m%d_%H%M%S).html
   ```

3. **For unplanned outages**: Logs are lost. The audit trail in `mcp_portfolio.audit.AuditLog` is ephemeral. To persist audit logs long-term, integrate an external sink (see Configuration Backup below).

---

## Configuration Backup

All configuration lives in environment variables and the `.env` file. Back up these artifacts:

| Item | Location | Backup Method |
|------|----------|---------------|
| `.env` | Project root | `cp .env .env.backup.$(date +%Y%m%d)` |
| `docker-compose.yml` | `deploy/` | Committed to git — use repo backup |
| `Dockerfile` | `deploy/` | Committed to git |
| TLS certificates | `/etc/ssl/` | Copy to secure off-host storage |
| API keys | `.env` or vault | Rotate if compromised; never commit |

### Automated Backup Script

```bash
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="/opt/backups/mcp-portfolio/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Copy env file
cp .env "$BACKUP_DIR/.env"

# Copy deploy configs
cp deploy/docker-compose.yml "$BACKUP_DIR/"
cp deploy/Dockerfile "$BACKUP_DIR/"

# Copy TLS certs (if present)
if [ -d /etc/ssl/certs/server.crt ]; then
    cp /etc/ssl/certs/server.crt "$BACKUP_DIR/"
    cp /etc/ssl/private/server.key "$BACKUP_DIR/"
fi

echo "Backup complete: $BACKUP_DIR"
```

---

## Recovery Steps

### Scenario 1: Container Crash

| Step | Command | Time |
|------|---------|------|
| 1. Detect | Health check fails | 30 s |
| 2. Restart | `docker compose up -d` | 15 s |
| 3. Verify health | `curl localhost:8001/health` | 5 s |
| 4. Verify data | Call a read tool | 5 s |
| **Total** | | **< 1 min** |

### Scenario 2: Host Failure (new VM)

| Step | Command | Time |
|------|---------|------|
| 1. Provision host | Spin up new VM with Docker | 2 min |
| 2. Clone repo | `git clone <repo>` | 30 s |
| 3. Restore config | Copy `.env` from backup | 10 s |
| 4. Restore TLS certs | Copy from secure backup | 10 s |
| 5. Build & start | `docker compose up -d --build` | 2 min |
| 6. Verify | Health + data check | 30 s |
| **Total** | | **< 5 min** |

### Scenario 3: Data Integrity Issue

| Step | Command | Time |
|------|---------|------|
| 1. Stop server | `docker stop mcp-portfolio` | 5 s |
| 2. Clear memory | (happens automatically on stop) | 0 s |
| 3. Restart | `docker compose up -d` | 15 s |
| 4. Verify data | Confirm seed data is consistent | 30 s |
| **Total** | | **< 1 min** |

---

## Business Continuity Considerations

### Single-Instance Limitations

The current architecture is **single-instance** with an in-memory store. This means:

- **No automatic failover** — a crashed instance serves zero traffic until restarted.
- **No data persistence** — all mutations are lost on restart.
- **No horizontal scaling** — each instance has independent state.

### Mitigations

| Risk | Mitigation |
|------|------------|
| Downtime during restart | Keep container restart policy as `unless-stopped`; Docker auto-restarts on crash. |
| Data loss | Acceptable for demo/eval environments. For production, add a persistence layer (PostgreSQL, Redis). |
| Single point of failure | Deploy behind a load balancer with health checks; use `docker compose scale` for warm standby. |
| Config drift | Store `.env` in a secrets manager (Vault, AWS Secrets Manager), not on disk. |
| TLS expiry | Automate cert renewal with certbot or an internal PKI; monitor expiry dates. |

### Upgrade Path

For production use, consider:

1. **PostgreSQL / Redis** for persistent state and shared cache.
2. **Kubernetes** with liveness/readiness probes for orchestration.
3. **Prometheus + Grafana** for metrics export and dashboards.
4. **Vault** for secrets management and automatic rotation.

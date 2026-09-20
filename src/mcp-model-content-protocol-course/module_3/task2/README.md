# MCP Enterprise Integration Portfolio (module_3 · task2)

Capstone project demonstrating complete MCP integration mastery across three
interconnected components for a Fortune 500 retail company scenario.

## Layout

```text
task2/
├── mcp_portfolio/        # implementation (importable package)
│   ├── server.py         # MCPServer assembly + transport entrypoints
│   ├── resources.py      # resource handlers (URI routing, RBAC, masking, cache)
│   ├── tools.py          # data-modifying tools (validation, rollback, async)
│   ├── ops_app.py        # FastAPI sidecar: /health /metrics /dashboard
│   ├── auth.py audit.py cache.py ratelimit.py resilience.py metrics.py
│   ├── config.py models.py seed_data.py store.py
├── tests/                # colocated unittest suite
├── deploy/               # Dockerfile, docker-compose, CI/CD, monitoring, DR
├── architecture/         # Component 1: Architecture Assessment
├── portfolio/            # Component 3: Portfolio Presentation
├── README.md             # this file
└── ARCHITECTURE.md       # design decisions
```

## Setup

```bash
poetry install
cp .env.example .env   # from repo root, then fill MCP_PORTFOLIO_API_KEYS
```

`MCP_PORTFOLIO_API_KEYS` is JSON mapping `key_id → {key_id, api_key (≥16 chars), role, revoked}`:

```json
{"admin-1": {"key_id": "admin-1", "api_key": "...", "role": "admin", "revoked": false}}
```

Roles: `admin` (full), `support_agent` (reads + order/ticket tools),
`auditor` (reads with PII masked + audit log), `operator` (inventory + health/metrics only).

## Run

```bash
cd src/mcp-model-content-protocol-course/module_3/task2
MCP_PORTFOLIO_SERVER_API_KEY=<key> poetry run python -m mcp_portfolio.server --transport stdio
MCP_PORTFOLIO_SERVER_API_KEY=<key> poetry run python -m mcp_portfolio.server --transport http --port 8000 --ops-port 8001
```

## Test

```bash
poetry run python -m unittest discover -s src/mcp-model-content-protocol-course/module_3/task2/tests -t src/mcp-model-content-protocol-course/module_3/task2 -v
```

## Deployment

```bash
docker build -f src/mcp-model-content-protocol-course/module_3/task2/deploy/Dockerfile -t mcp-portfolio .
docker run --env-file .env -p 8000:8000 mcp-portfolio
```

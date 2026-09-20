# MCP (Model Context Protocol)

Workbook for the Model Context Protocol course on Coursera. Evaluate MCP for AI integration, design resource schemas, and build complete MCP servers with security, monitoring, and enterprise deployment.

## Modules

| Module | Topic | Key Files |
|--------|-------|-----------|
| 1 | Evaluate MCP for AI Integration | Task text files, evaluation PDF |
| 2 | Design MCP Resource Schema | `mcp-demo.txt`, schema design PDF |
| 3 | Build Complete MCP Server | `mcp_server/` (full implementation), `mcp_portfolio/` (enterprise capstone) |

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/)
- Docker (for Module 3 deployment)
- API key for an LLM provider

## Setup

```bash
poetry install
cp .env.example .env
# Edit .env with your API keys and MCP configuration
```

## Running

```bash
# Module 3, Task 1 — Secure MCP Server with Monitoring
cd src/mcp-model-content-protocol-course/module_3/task1
poetry run python -m mcp_server.server

# Module 3, Task 2 — Enterprise MCP Portfolio
cd src/mcp-model-content-protocol-course/module_3/task2
poetry run python -m mcp_portfolio.server

# Docker deployment
cd src/mcp-model-content-protocol-course/module_3/task2/deploy
docker compose up
```

## Tests

```bash
# Module 3, Task 1 — 62 tests
cd src/mcp-model-content-protocol-course/module_3/task1
poetry run python -m pytest tests/ -v

# Module 3, Task 2
cd src/mcp-model-content-protocol-course/module_3/task2
poetry run python -m pytest tests/ -v
```

## Additional Resources

- **[Task 1: Secure MCP Server](module_3/task1/README.md)** — API reference, setup, run, test, and deployment guide for the production MCP server with RBAC, audit logging, rate limiting, and monitoring
- **[Task 2: Enterprise MCP Portfolio](module_3/task2/README.md)** — Capstone project with architecture assessment, Docker Compose, CI/CD, and portfolio presentation

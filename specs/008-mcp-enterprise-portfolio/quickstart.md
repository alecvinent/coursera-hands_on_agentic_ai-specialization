# Quickstart: MCP Enterprise Integration Portfolio

**Feature**: 008-mcp-enterprise-portfolio
**Date**: 2026-09-18

## Prerequisites

- Python 3.12+
- Poetry (for dependency management)
- Docker (for containerized deployment)
- Git

## Setup

```bash
# Clone and install
cd src/mcp-model-content-protocol-course/module_3/task2
poetry install

# Configure
cp .env.example .env
# Edit .env with API keys (JSON format matching task1 conventions)
```

## Validate Component 1: Architecture Assessment

```bash
# Verify all architecture documents exist and are non-empty
ls architecture/architecture-diagram.md architecture/mcp-vs-traditional.md \
   architecture/risk-assessment.md architecture/roi-analysis.md \
   architecture/executive-summary.md

# Verify executive summary is accessible to non-technical readers
# (manual review — no automated check)
```

**Expected outcome**: 5 architecture documents present, executive summary uses business language.

## Validate Component 2: MCP Server

```bash
# Run the full test suite
poetry run python -m unittest discover \
  -s src/mcp-model-content-protocol-course/module_3/task2/tests \
  -t src/mcp-model-content-protocol-course/module_3/task2 \
  -v

# Start the server (STDIO mode)
MCP_SERVER_API_KEY=<your-key> poetry run python -m mcp_portfolio.server --transport stdio

# Start the server (HTTP mode with ops sidecar)
MCP_SERVER_API_KEY=<your-key> poetry run python -m mcp_portfolio.server \
  --transport http --port 8000 --ops-port 8001
```

**Expected outcome**: All tests pass. Server starts and responds to MCP resource/tool calls.

## Validate Component 3: Security & Deployment

```bash
# Check health endpoint
curl http://localhost:8001/health
# Expected: {"status": "healthy", ...}

# Check metrics (requires operator/admin key)
curl -H "X-API-Key: <operator-key>" http://localhost:8001/metrics
# Expected: JSON with request counts, latencies, error rates

# Check dashboard
curl -H "X-API-Key: <operator-key>" http://localhost:8001/dashboard
# Expected: HTML or JSON dashboard view

# Build Docker image
docker build -f deploy/Dockerfile -t mcp-portfolio .
docker run --env-file .env -p 8000:8000 mcp-portfolio

# Verify CI config is valid YAML
python -c "import yaml; yaml.safe_load(open('deploy/ci.yml'))"
```

**Expected outcome**: Health/metrics/dashboard endpoints respond. Docker image builds and runs. CI config is valid YAML.

## Validate Integration

```bash
# Verify all three components reference each other
grep -r "architecture" architecture/ portfolio/ | head -5
grep -r "mcp_portfolio" portfolio/ README.md | head -5
grep -r "security" architecture/ deploy/ | head -5
```

**Expected outcome**: Cross-references between components are present and consistent.

## Validate Disaster Recovery

```bash
# Verify DR document exists and contains procedures
cat deploy/disaster-recovery.md | grep -c "step"  # Should be > 0
cat deploy/monitoring.md | grep -c "alert"        # Should be > 0
```

**Expected outcome**: DR and monitoring docs contain actionable procedures.

## End-to-End Smoke Test

```bash
# 1. Start server in HTTP mode
# 2. Authenticate with a support_agent key
# 3. Read a customer resource
# 4. Create a support ticket
# 5. Update the ticket status
# 6. Check audit log via dashboard
# 7. Verify metrics show the operations
```

**Expected outcome**: Full workflow completes with correct data, audit records, and metrics.

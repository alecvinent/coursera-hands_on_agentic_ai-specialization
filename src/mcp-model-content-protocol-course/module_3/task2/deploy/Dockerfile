# ---- Stage 1: build dependencies ----
FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir poetry==1.8.*

WORKDIR /build

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.in-project true && \
    poetry install --no-root --no-interaction --no-ansi

# ---- Stage 2: runtime ----
FROM python:3.12-slim AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 app && \
    useradd  --uid 1000 --gid app --create-home app

COPY --from=builder /build/.venv /app/.venv

WORKDIR /app/src/mcp-model-content-protocol-course/module_3/task2

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app

EXPOSE 8000 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8001/health || exit 1

CMD ["python", "-m", "mcp_portfolio.server", "--transport", "http", "--port", "8000", "--ops-port", "8001"]

# Production container for the secure MCP server (module_3 task1).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN useradd --create-home --uid 10001 appuser
WORKDIR /app

COPY pyproject.toml poetry.lock* /app/
RUN pip install --no-cache-dir poetry \
    && poetry install --only main --no-root \
    && pip uninstall -y poetry

COPY src/mcp-model-content-protocol-course/module_3/task1/mcp_server /app/mcp_server

USER appuser
EXPOSE 8000 8001

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8001/health').status==200 else 1)"

CMD ["python", "-m", "mcp_server.server", "--transport", "http", "--host", "0.0.0.0", "--port", "8000", "--ops-port", "8001"]

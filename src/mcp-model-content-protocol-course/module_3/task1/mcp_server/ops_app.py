"""Operations surface: health, metrics, dashboard over FastAPI.

Route handlers are thin wrappers over plain testable functions.
TLS terminates at deployment ingress; direct termination via stdlib ssl
is supported through Settings (see run_ops).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field

from mcp_server.audit import AuditLog
from mcp_server.auth import AuthContext, Unauthenticated, authenticate, require
from mcp_server.config import Settings
from mcp_server.metrics import MetricsRegistry
from mcp_server.models import ApiCredential, Role
from mcp_server.resilience import CircuitBreaker
from mcp_server.store import MockStore

VERSION = "0.1.0"
OPS_ROLES: set[Role] = {Role.ADMIN, Role.OPERATOR}

AlertHook = Callable[[dict], None]


@dataclass
class OpsDeps:
    settings: Settings
    credentials: dict[str, ApiCredential]
    store: MockStore
    audit: AuditLog
    metrics: MetricsRegistry
    breaker: CircuitBreaker
    started_at: float
    alert_hooks: list[AlertHook] = field(default_factory=list)


def get_health(deps: OpsDeps) -> dict:
    uptime = time.monotonic() - deps.started_at
    dependencies = {
        "mock_store": deps.breaker.state,
        "audit_sink": "broken" if deps.audit.broken else "ok",
    }
    if deps.audit.broken:
        status = "unhealthy"
    elif deps.breaker.state != "closed" or (
        deps.metrics.error_rate() > deps.settings.error_rate_threshold
    ):
        status = "degraded"
    else:
        status = "healthy"
    report = {
        "status": status,
        "uptime_seconds": uptime,
        "dependencies": dependencies,
        "version": VERSION,
    }
    if status != "healthy":
        for hook in deps.alert_hooks:
            hook(report)
    return report


def get_metrics(deps: OpsDeps, ctx: AuthContext) -> dict:
    require(ctx, OPS_ROLES)
    snapshot = deps.metrics.snapshot()
    snapshot["circuit_states"] = {"mock_store": deps.breaker.state}
    return snapshot


def render_dashboard(deps: OpsDeps, ctx: AuthContext) -> str:
    require(ctx, OPS_ROLES)
    health = get_health(deps)
    snapshot = deps.metrics.snapshot()
    recent = deps.metrics.errors[-10:]
    rows = "".join(
        f"<tr><td>{e['timestamp']}</td><td>{e['step']}</td><td>{e['error_type']}</td></tr>"
        for e in recent
    )
    return (
        "<html><head><title>MCP Server Dashboard</title></head><body>"
        f"<h1>Status: {health['status']}</h1>"
        f"<p>Uptime: {health['uptime_seconds']:.1f}s | Version: {VERSION}</p>"
        f"<p>Requests: {snapshot['requests_count']} | "
        f"Error rate: {snapshot['error_rate']:.3f} | "
        f"p95: {snapshot['latency_ms']['p95']:.1f} ms</p>"
        f"<p>Circuit: {deps.breaker.state}</p>"
        "<h2>Recent errors (sanitized)</h2>"
        f"<table><tr><th>Time</th><th>Step</th><th>Type</th></tr>{rows}</table>"
        "</body></html>"
    )


def _ctx_from_header(deps: OpsDeps, api_key: str | None) -> AuthContext:
    try:
        return authenticate(deps.credentials, api_key)
    except Unauthenticated as exc:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=401, detail="invalid or missing credentials"
        ) from exc


def create_ops_app(deps: OpsDeps):
    """Build the FastAPI sidecar app (thin wiring over plain functions)."""
    from fastapi import FastAPI, Header, HTTPException
    from fastapi.responses import HTMLResponse

    app = FastAPI(title="MCP Server Ops")

    @app.get("/health")
    def health() -> dict:
        return get_health(deps)

    @app.get("/metrics")
    def metrics(x_api_key: str | None = Header(default=None)) -> dict:
        ctx = _ctx_from_header(deps, x_api_key)
        try:
            return get_metrics(deps, ctx)
        except Exception as exc:
            raise HTTPException(
                status_code=403, detail="insufficient permissions"
            ) from exc

    @app.get("/dashboard", response_class=HTMLResponse)
    def dashboard(x_api_key: str | None = Header(default=None)) -> str:
        ctx = _ctx_from_header(deps, x_api_key)
        try:
            return render_dashboard(deps, ctx)
        except Exception as exc:
            raise HTTPException(
                status_code=403, detail="insufficient permissions"
            ) from exc

    return app


def run_ops(deps: OpsDeps, host: str = "127.0.0.1", port: int = 8000) -> None:
    """Serve the ops sidecar, honoring TLS settings for direct termination."""
    import uvicorn

    kwargs: dict = {}
    if deps.settings.tls_enabled:
        import ssl

        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(deps.settings.tls_cert_path, deps.settings.tls_key_path)
        kwargs["ssl"] = context
    uvicorn.run(create_ops_app(deps), host=host, port=port, **kwargs)

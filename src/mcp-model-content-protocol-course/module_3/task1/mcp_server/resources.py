"""MCP resource handlers: URI routing, RBAC, masking, caching, audit."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from loguru import logger

from mcp_server.audit import AuditLog, AuditUnavailable
from mcp_server.auth import (
    AuthContext,
    Forbidden,
    Unauthenticated,
    authenticate,
    require,
)
from mcp_server.cache import TTLCache, make_key
from mcp_server.config import Settings
from mcp_server.metrics import MetricsRegistry
from mcp_server.models import ApiCredential, Customer, Role
from mcp_server.ratelimit import RateLimiter
from mcp_server.resilience import CircuitBreaker, CircuitOpen, ToolTimeout, with_timeout
from mcp_server.store import DependencyUnavailable, MockStore, NotFound

READ_ROLES: set[Role] = {Role.ADMIN, Role.SUPPORT_AGENT, Role.AUDITOR}
AUDIT_READ_ROLES: set[Role] = {Role.ADMIN, Role.AUDITOR}


def error_envelope(
    code: str, message: str, outcome: str = "ok", **extra: object
) -> dict:
    return {
        "error": {"code": code, "message": message},
        "processing_outcome": outcome,
        **extra,
    }


def mask_customer(customer: Customer, role: Role) -> dict:
    data = customer.model_dump(mode="json")
    if role == Role.AUDITOR:
        for field in ("full_name", "email", "phone"):
            if data.get(field) is not None:
                data[field] = "***"
    return data


class ResourceService:
    def __init__(
        self,
        settings: Settings,
        credentials: dict[str, ApiCredential],
        store: MockStore,
        cache: TTLCache,
        audit: AuditLog,
        metrics: MetricsRegistry,
        limiter: RateLimiter,
        breaker: CircuitBreaker,
    ) -> None:
        self._settings = settings
        self._credentials = credentials
        self._store = store
        self._cache = cache
        self._audit = audit
        self._metrics = metrics
        self._limiter = limiter
        self._breaker = breaker

    async def read(self, uri: str, presented_key: str | None) -> dict:
        start = time.monotonic()
        try:
            ctx = authenticate(self._credentials, presented_key)
        except Unauthenticated:
            self._safe_audit(None, "auth.denied", uri, "denied")
            return error_envelope("UNAUTHENTICATED", "invalid or missing credentials")

        allowed, retry_ms = self._limiter.allow(ctx.key_id)
        if not allowed:
            self._safe_audit(ctx, "resource.read", uri, "denied")
            self._metrics.record_rate_limited()
            self._finish("resource.read", "limited", start)
            return error_envelope(
                "RATE_LIMITED", "rate limit exceeded", retryAfterMs=retry_ms
            )

        try:
            require(ctx, READ_ROLES)
        except Forbidden:
            self._safe_audit(ctx, "resource.read", uri, "denied")
            self._finish("resource.read", "denied", start)
            return error_envelope("FORBIDDEN", "insufficient permissions")

        cache_key = make_key(ctx.role, uri)
        cached = self._cache.get(cache_key)
        self._metrics.record_cache(cached is not None)
        if cached is not None:
            self._safe_audit(ctx, "resource.read", uri, "success")
            self._finish("resource.read", "success", start)
            return {"data": cached, "processing_outcome": "ok"}

        try:
            self._breaker.before_call()
        except CircuitOpen:
            self._safe_audit(ctx, "resource.read", uri, "failed")
            self._finish("resource.read", "failed", start)
            return error_envelope(
                "DEPENDENCY_UNAVAILABLE",
                "data source temporarily unavailable",
                outcome="partial",
            )

        try:
            payload = await with_timeout(
                self._fetch(uri, ctx), self._settings.tool_timeout_seconds
            )
        except NotFound:
            self._breaker.after_call(True)
            self._safe_audit(ctx, "resource.read", uri, "failed")
            self._finish("resource.read", "failed", start)
            return error_envelope("NOT_FOUND", "resource not found")
        except (DependencyUnavailable, ToolTimeout) as exc:
            self._breaker.after_call(False)
            logger.warning(
                f"resource read degraded uri={uri} error={type(exc).__name__}"
            )
            self._safe_audit(ctx, "resource.read", uri, "failed")
            self._metrics.record_error(
                "resource.read",
                type(exc).__name__,
                "dependency failure",
                datetime.now(timezone.utc).isoformat(),
            )
            self._finish("resource.read", "failed", start)
            code = (
                "TIMEOUT" if isinstance(exc, ToolTimeout) else "DEPENDENCY_UNAVAILABLE"
            )
            return error_envelope(
                code, "data source temporarily unavailable", outcome="partial"
            )

        self._breaker.after_call(True)
        self._cache.set(cache_key, payload)
        self._safe_audit(ctx, "resource.read", uri, "success")
        self._finish("resource.read", "success", start)
        return {"data": payload, "processing_outcome": "ok"}

    async def _fetch(self, uri: str, ctx: AuthContext) -> object:
        if not uri.startswith("store://"):
            raise NotFound(uri)
        parts = uri[len("store://") :].strip("/").split("/")
        store = self._store
        if parts[0] == "customers" and len(parts) == 2:
            customer = await store.get_customer(parts[1])
            return mask_customer(customer, ctx.role)
        if parts[0] == "customers" and len(parts) == 3 and parts[2] == "orders":
            orders = await store.list_customer_orders(parts[1])
            return [o.model_dump(mode="json") for o in orders]
        if parts[0] == "customers" and len(parts) == 3 and parts[2] == "tickets":
            tickets = await store.list_customer_tickets(parts[1])
            return [t.model_dump(mode="json") for t in tickets]
        if parts[0] == "orders" and len(parts) == 2:
            return (await store.get_order(parts[1])).model_dump(mode="json")
        if parts[0] == "orders" and len(parts) == 3 and parts[1] == "status":
            orders = await store.list_orders_by_status(parts[2])
            return [o.model_dump(mode="json") for o in orders]
        if parts[0] == "tickets" and len(parts) == 2:
            return (await store.get_ticket(parts[1])).model_dump(mode="json")
        if parts[0] == "tickets" and len(parts) == 3 and parts[1] == "status":
            tickets = await store.list_tickets_by_status(parts[2])
            return [t.model_dump(mode="json") for t in tickets]
        if parts == ["products"]:
            products = await store.list_products()
            return [p.model_dump(mode="json") for p in products]
        if parts[0] == "products" and len(parts) == 2:
            return (await store.get_product(parts[1])).model_dump(mode="json")
        raise NotFound(uri)

    def read_audit_log(self, ctx: AuthContext) -> dict:
        try:
            require(ctx, AUDIT_READ_ROLES)
        except Forbidden:
            self._safe_audit(ctx, "audit.read", "audit-log", "denied")
            return error_envelope("FORBIDDEN", "insufficient permissions")
        records = [r.model_dump(mode="json") for r in self._audit.list_records()]
        self._safe_audit(ctx, "audit.read", "audit-log", "success")
        return {"data": records, "processing_outcome": "ok"}

    def _safe_audit(
        self, ctx: AuthContext | None, action: str, target: str, outcome: str
    ) -> None:
        from mcp_server.models import Outcome

        try:
            self._audit.record(ctx, action, target, Outcome(outcome))
        except AuditUnavailable:
            logger.error("audit sink unavailable; failing closed")

    def _finish(self, endpoint: str, outcome: str, start: float) -> None:
        self._metrics.record(endpoint, outcome, (time.monotonic() - start) * 1000)

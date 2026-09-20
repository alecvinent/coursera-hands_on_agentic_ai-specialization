"""MCP resource handlers: URI routing, RBAC, masking, caching, audit."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from loguru import logger

from mcp_portfolio.audit import AuditLog, AuditUnavailable
from mcp_portfolio.auth import (
    AuthContext,
    Forbidden,
    Unauthenticated,
    authenticate,
    require,
)
from mcp_portfolio.cache import TTLCache
from mcp_portfolio.config import Settings
from mcp_portfolio.metrics import MetricsRegistry
from mcp_portfolio.models import (
    MASKED,
    INVENTORY_ROLES_READ,
    LOW_STOCK_ROLES,
    RESOURCE_ROLES_READ,
    ApiCredential,
    Customer,
    Outcome,
    Role,
)
from mcp_portfolio.ratelimit import RateLimiter
from mcp_portfolio.resilience import CircuitBreaker, CircuitOpen, ToolTimeout, with_timeout
from mcp_portfolio.store import MockStore, NotFound


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
        for field in ("email", "phone", "address"):
            if data.get(field) is not None:
                data[field] = MASKED
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
            self._safe_audit(None, "auth.denied", uri, Outcome.DENIED)
            return error_envelope("UNAUTHENTICATED", "invalid or missing credentials")

        allowed, retry_ms = self._limiter.allow(ctx.key_id)
        if not allowed:
            self._safe_audit(ctx, "resource.read", uri, Outcome.DENIED)
            self._metrics.record_rate_limited()
            self._finish("resource.read", "limited", start)
            return error_envelope(
                "RATE_LIMITED", "rate limit exceeded", retryAfterMs=retry_ms
            )

        resource_roles = _resolve_roles(uri)
        try:
            require(ctx, resource_roles)
        except Forbidden:
            self._safe_audit(ctx, "resource.read", uri, Outcome.DENIED)
            self._finish("resource.read", "denied", start)
            return error_envelope("FORBIDDEN", "insufficient permissions")

        cache_key = f"{ctx.role.value}:{uri}"
        cached = self._cache.get(ctx.role.value, uri)
        self._metrics.record_cache(cached is not None)
        if cached is not None:
            self._safe_audit(ctx, "resource.read", uri, Outcome.SUCCESS)
            self._finish("resource.read", "success", start)
            return {"data": cached, "processing_outcome": "ok"}

        try:
            self._breaker.before_call()
        except CircuitOpen:
            self._safe_audit(ctx, "resource.read", uri, Outcome.FAILED)
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
            self._safe_audit(ctx, "resource.read", uri, Outcome.FAILED)
            self._finish("resource.read", "failed", start)
            return error_envelope("NOT_FOUND", "resource not found")
        except (ToolTimeout, Exception) as exc:
            self._breaker.after_call(False)
            logger.warning(
                f"resource read degraded uri={uri} error={type(exc).__name__}"
            )
            self._safe_audit(ctx, "resource.read", uri, Outcome.FAILED)
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
        self._cache.set(ctx.role.value, uri, payload)
        self._safe_audit(ctx, "resource.read", uri, Outcome.SUCCESS)
        self._finish("resource.read", "success", start)
        return {"data": payload, "processing_outcome": "ok"}

    async def _fetch(self, uri: str, ctx: AuthContext) -> object:
        if not uri.startswith("retail://"):
            raise NotFound(uri)
        parts = uri[len("retail://") :].strip("/").split("/")
        store = self._store

        if parts[0] == "customers" and len(parts) == 2:
            customer = await store.get_customer(parts[1])
            if customer is None:
                raise NotFound(uri)
            return mask_customer(customer, ctx.role)
        if parts[0] == "customers" and len(parts) == 3 and parts[2] == "orders":
            orders = await store.get_customer_orders(parts[1])
            return [o.model_dump(mode="json") for o in orders]
        if parts[0] == "customers" and len(parts) == 3 and parts[2] == "tickets":
            tickets = await store.get_customer_tickets(parts[1])
            return [t.model_dump(mode="json") for t in tickets]
        if parts[0] == "orders" and len(parts) == 2:
            order = await store.get_order(parts[1])
            if order is None:
                raise NotFound(uri)
            return order.model_dump(mode="json")
        if parts[0] == "orders" and len(parts) == 3 and parts[1] == "status":
            orders = await store.get_orders_by_status(parts[2])
            return [o.model_dump(mode="json") for o in orders]
        if parts[0] == "inventory" and len(parts) == 2 and parts[1] == "low-stock":
            items = await store.get_low_stock_inventory()
            return [i.model_dump(mode="json") for i in items]
        if parts[0] == "inventory" and len(parts) == 2:
            item = await store.get_inventory(parts[1])
            if item is None:
                raise NotFound(uri)
            return item.model_dump(mode="json")
        if parts == ["products"]:
            products = await store.get_all_products()
            return [p.model_dump(mode="json") for p in products]
        if parts[0] == "products" and len(parts) == 2:
            product = await store.get_product(parts[1])
            if product is None:
                raise NotFound(uri)
            return product.model_dump(mode="json")
        raise NotFound(uri)

    def _safe_audit(
        self, ctx: AuthContext | None, action: str, target: str, outcome: Outcome
    ) -> None:
        try:
            self._audit.record(ctx, action, target, outcome)
        except AuditUnavailable:
            logger.error("audit sink unavailable; failing closed")

    def _finish(self, endpoint: str, outcome: str, start: float) -> None:
        self._metrics.record(endpoint, outcome, (time.monotonic() - start) * 1000)


def _resolve_roles(uri: str) -> set[Role]:
    parts = uri.replace("retail://", "").strip("/").split("/")
    if parts[0] == "inventory":
        if len(parts) == 2 and parts[1] == "low-stock":
            return LOW_STOCK_ROLES
        return INVENTORY_ROLES_READ
    return RESOURCE_ROLES_READ

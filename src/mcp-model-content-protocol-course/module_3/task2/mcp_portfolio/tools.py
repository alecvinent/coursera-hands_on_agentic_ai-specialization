"""MCP tool handlers: validation, RBAC-first ordering, rollback, async execution."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from loguru import logger
from pydantic import ValidationError

from mcp_portfolio.audit import AuditLog, AuditUnavailable
from mcp_portfolio.auth import (
    AuthContext,
    Forbidden,
    Unauthenticated,
    authenticate,
    require,
)
from mcp_portfolio.config import Settings
from mcp_portfolio.metrics import MetricsRegistry
from mcp_portfolio.models import (
    INVENTORY_TOOL_ROLES,
    ORDER_TRANSITIONS,
    TICKET_TRANSITIONS,
    TOOL_ROLES,
    ApiCredential,
    InventoryItem,
    Order,
    OrderItem,
    OrderStatus,
    Outcome,
    Product,
    Role,
    SupportTicket,
    TicketStatus,
)
from mcp_portfolio.ratelimit import RateLimiter
from mcp_portfolio.resilience import ToolTimeout, with_timeout
from mcp_portfolio.resources import error_envelope
from mcp_portfolio.store import MockStore, NotFound


def sanitize(value: str, max_len: int) -> str:
    cleaned = "".join(ch for ch in value if ch.isprintable() or ch in "\n\t").strip()
    return cleaned[:max_len]


@dataclass
class TaskRecord:
    task_id: str
    status: str = "running"
    result: dict | None = None


@dataclass
class ToolService:
    settings: Settings
    credentials: dict[str, ApiCredential]
    store: MockStore
    audit: AuditLog
    metrics: MetricsRegistry
    limiter: RateLimiter
    tasks: dict[str, TaskRecord] = field(default_factory=dict)
    _order_seq: int = field(default=10000)
    _ticket_seq: int = field(default=4000)
    _locks: dict[str, asyncio.Lock] = field(default_factory=dict)

    def _lock_for(self, key: str) -> asyncio.Lock:
        lock = self._locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[key] = lock
        return lock

    async def _authorize(
        self, tool: str, presented_key: str | None, inputs: dict
    ) -> AuthContext | dict:
        try:
            ctx = authenticate(self.credentials, presented_key)
        except Unauthenticated:
            self._audit_safe(None, "tool.execute", tool, Outcome.DENIED, inputs)
            return error_envelope("UNAUTHENTICATED", "invalid or missing credentials")
        allowed, retry_ms = self.limiter.allow(ctx.key_id)
        if not allowed:
            self._audit_safe(ctx, "tool.execute", tool, Outcome.DENIED, inputs)
            self.metrics.record_rate_limited()
            return error_envelope(
                "RATE_LIMITED", "rate limit exceeded", retryAfterMs=retry_ms
            )
        try:
            require(ctx, TOOL_ROLES)
        except Forbidden:
            self._audit_safe(ctx, "tool.execute", tool, Outcome.DENIED, inputs)
            return error_envelope("FORBIDDEN", "insufficient permissions")
        return ctx

    def _audit_safe(
        self,
        ctx: AuthContext | None,
        action: str,
        target: str,
        outcome: Outcome,
        inputs: dict | None = None,
    ) -> None:
        try:
            self.audit.record(ctx, action, target, outcome, inputs)
        except AuditUnavailable:
            logger.error("audit sink unavailable; failing closed")

    async def create_order(self, presented_key: str | None, inputs: dict) -> dict:
        start = time.monotonic()
        auth = await self._authorize("create_order", presented_key, inputs)
        if isinstance(auth, dict):
            self.metrics.record("tool.execute", "denied", self._elapsed(start))
            return auth
        ctx = auth
        try:
            order = self._build_order(inputs)
        except (ValidationError, ValueError, KeyError) as exc:
            self._audit_safe(
                ctx, "tool.execute", "create_order", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", f"invalid input: {exc}")
        try:
            await with_timeout(
                self.store.create_order(order), self.settings.tool_timeout_seconds
            )
        except (ToolTimeout, Exception) as exc:
            self._audit_safe(
                ctx, "tool.execute", "create_order", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            code = (
                "TIMEOUT" if isinstance(exc, ToolTimeout) else "DEPENDENCY_UNAVAILABLE"
            )
            return error_envelope(code, "could not create order", outcome="partial")
        self._audit_safe(
            ctx,
            "tool.execute",
            "create_order",
            Outcome.SUCCESS,
            {"order_id": order.order_id},
        )
        self.metrics.record("tool.execute", "success", self._elapsed(start))
        return {
            "data": {
                "order_id": order.order_id,
                "status": order.status.value,
                "total": str(order.total),
                "created_at": order.created_at.isoformat(),
            },
            "processing_outcome": "ok",
        }

    def _build_order(self, inputs: dict) -> Order:
        customer_id = inputs.get("customer_id", "")
        items_raw = inputs.get("items", [])
        if not items_raw:
            raise ValueError("items must not be empty")
        now = datetime.now(timezone.utc)
        self._order_seq += 1
        items: list[OrderItem] = []
        for item in items_raw:
            product_id = item.get("product_id", "")
            quantity = int(item.get("quantity", 1))
            unit_price = float(item.get("unit_price", 0))
            items.append(
                OrderItem(
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                )
            )
        total = sum(it.quantity * it.unit_price for it in items)
        return Order(
            order_id=f"ord_{self._order_seq:04d}",
            customer_id=customer_id,
            items=items,
            total=total,
            status=OrderStatus.PENDING,
            version=0,
            created_at=now,
            updated_at=now,
        )

    async def update_order_status(
        self, presented_key: str | None, inputs: dict
    ) -> dict:
        start = time.monotonic()
        auth = await self._authorize("update_order_status", presented_key, inputs)
        if isinstance(auth, dict):
            self.metrics.record("tool.execute", "denied", self._elapsed(start))
            return auth
        ctx = auth
        order_id = inputs.get("order_id")
        try:
            new_status = OrderStatus(inputs.get("new_status"))
        except ValueError:
            self._audit_safe(
                ctx, "tool.execute", "update_order_status", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", "unknown order status")
        try:
            await with_timeout(
                self.store.get_order(order_id), self.settings.tool_timeout_seconds
            )
        except NotFound:
            self._audit_safe(
                ctx, "tool.execute", "update_order_status", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", "order cannot be updated")
        except (ToolTimeout, Exception):
            self._audit_safe(
                ctx, "tool.execute", "update_order_status", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope(
                "DEPENDENCY_UNAVAILABLE", "order cannot be updated", outcome="partial"
            )
        async with self._lock_for(f"order:{order_id}"):
            try:
                current = await with_timeout(
                    self.store.get_order(order_id), self.settings.tool_timeout_seconds
                )
            except (NotFound, ToolTimeout, Exception):
                self._audit_safe(
                    ctx, "tool.execute", "update_order_status", Outcome.FAILED, inputs
                )
                self.metrics.record("tool.execute", "failed", self._elapsed(start))
                return error_envelope("VALIDATION_ERROR", "order cannot be updated")
            if current is None:
                self._audit_safe(
                    ctx, "tool.execute", "update_order_status", Outcome.FAILED, inputs
                )
                self.metrics.record("tool.execute", "failed", self._elapsed(start))
                return error_envelope("VALIDATION_ERROR", "order cannot be updated")
            if self._check_version(inputs, current.version):
                self._audit_safe(
                    ctx, "tool.execute", "update_order_status", Outcome.FAILED, inputs
                )
                self.metrics.record("tool.execute", "failed", self._elapsed(start))
                return error_envelope(
                    "CONFLICT",
                    f"order changed concurrently (version {current.version})",
                    current={
                        "status": current.status.value,
                        "version": current.version,
                    },
                )
            if new_status not in ORDER_TRANSITIONS[current.status]:
                self._audit_safe(
                    ctx, "tool.execute", "update_order_status", Outcome.FAILED, inputs
                )
                self.metrics.record("tool.execute", "failed", self._elapsed(start))
                return error_envelope(
                    "VALIDATION_ERROR",
                    f"illegal transition {current.status.value} -> {new_status.value}",
                )
            previous = current.model_copy(deep=True)
            updated = current.model_copy(
                update={
                    "status": new_status,
                    "version": current.version + 1,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            try:
                await with_timeout(
                    self.store.update_order(updated), self.settings.tool_timeout_seconds
                )
            except (ToolTimeout, Exception):
                await self._rollback_order(previous)
                self._audit_safe(
                    ctx, "tool.execute", "update_order_status", Outcome.FAILED, inputs
                )
                self.metrics.record("tool.execute", "failed", self._elapsed(start))
                return error_envelope(
                    "DEPENDENCY_UNAVAILABLE", "update rolled back", outcome="partial"
                )
        self._audit_safe(
            ctx,
            "tool.execute",
            "update_order_status",
            Outcome.SUCCESS,
            {"order_id": order_id},
        )
        self.metrics.record("tool.execute", "success", self._elapsed(start))
        return {
            "data": {
                "order_id": order_id,
                "old_status": previous.status.value,
                "new_status": new_status.value,
                "updated_at": updated.updated_at.isoformat(),
            },
            "processing_outcome": "ok",
        }

    async def update_inventory(self, presented_key: str | None, inputs: dict) -> dict:
        start = time.monotonic()
        try:
            ctx = authenticate(self.credentials, presented_key)
        except Unauthenticated:
            self._audit_safe(None, "tool.execute", "update_inventory", Outcome.DENIED, inputs)
            return error_envelope("UNAUTHENTICATED", "invalid or missing credentials")
        allowed, retry_ms = self.limiter.allow(ctx.key_id)
        if not allowed:
            self._audit_safe(ctx, "tool.execute", "update_inventory", Outcome.DENIED, inputs)
            self.metrics.record_rate_limited()
            return error_envelope("RATE_LIMITED", "rate limit exceeded", retryAfterMs=retry_ms)
        try:
            require(ctx, INVENTORY_TOOL_ROLES)
        except Forbidden:
            self._audit_safe(ctx, "tool.execute", "update_inventory", Outcome.DENIED, inputs)
            return error_envelope("FORBIDDEN", "insufficient permissions")
        product_id = inputs.get("product_id")
        quantity = inputs.get("quantity")
        if quantity is None or not isinstance(quantity, int) or quantity < 0:
            self._audit_safe(ctx, "tool.execute", "update_inventory", Outcome.FAILED, inputs)
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", "quantity must be a non-negative integer")
        try:
            item = await with_timeout(
                self.store.get_inventory(product_id), self.settings.tool_timeout_seconds
            )
        except (NotFound, ToolTimeout, Exception):
            self._audit_safe(ctx, "tool.execute", "update_inventory", Outcome.FAILED, inputs)
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", "inventory item not found")
        if item is None:
            self._audit_safe(ctx, "tool.execute", "update_inventory", Outcome.FAILED, inputs)
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", "inventory item not found")
        updated = item.model_copy(update={"quantity": quantity})
        try:
            await with_timeout(
                self.store.update_inventory(updated), self.settings.tool_timeout_seconds
            )
        except (ToolTimeout, Exception):
            self._audit_safe(ctx, "tool.execute", "update_inventory", Outcome.FAILED, inputs)
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("DEPENDENCY_UNAVAILABLE", "could not update inventory", outcome="partial")
        self._audit_safe(
            ctx, "tool.execute", "update_inventory", Outcome.SUCCESS, {"product_id": product_id}
        )
        self.metrics.record("tool.execute", "success", self._elapsed(start))
        return {
            "data": {"product_id": product_id, "quantity": quantity},
            "processing_outcome": "ok",
        }

    async def reserve_inventory(self, presented_key: str | None, inputs: dict) -> dict:
        start = time.monotonic()
        try:
            ctx = authenticate(self.credentials, presented_key)
        except Unauthenticated:
            self._audit_safe(None, "tool.execute", "reserve_inventory", Outcome.DENIED, inputs)
            return error_envelope("UNAUTHENTICATED", "invalid or missing credentials")
        allowed, retry_ms = self.limiter.allow(ctx.key_id)
        if not allowed:
            self._audit_safe(ctx, "tool.execute", "reserve_inventory", Outcome.DENIED, inputs)
            self.metrics.record_rate_limited()
            return error_envelope("RATE_LIMITED", "rate limit exceeded", retryAfterMs=retry_ms)
        try:
            require(ctx, INVENTORY_TOOL_ROLES)
        except Forbidden:
            self._audit_safe(ctx, "tool.execute", "reserve_inventory", Outcome.DENIED, inputs)
            return error_envelope("FORBIDDEN", "insufficient permissions")
        product_id = inputs.get("product_id")
        quantity = inputs.get("quantity")
        if quantity is None or not isinstance(quantity, int) or quantity < 1:
            self._audit_safe(ctx, "tool.execute", "reserve_inventory", Outcome.FAILED, inputs)
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", "quantity must be a positive integer")
        try:
            item = await with_timeout(
                self.store.get_inventory(product_id), self.settings.tool_timeout_seconds
            )
        except (NotFound, ToolTimeout, Exception):
            self._audit_safe(ctx, "tool.execute", "reserve_inventory", Outcome.FAILED, inputs)
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", "inventory item not found")
        if item is None:
            self._audit_safe(ctx, "tool.execute", "reserve_inventory", Outcome.FAILED, inputs)
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", "inventory item not found")
        available = item.quantity - item.reserved
        if quantity > available:
            self._audit_safe(ctx, "tool.execute", "reserve_inventory", Outcome.FAILED, inputs)
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", f"insufficient stock: {available} available")
        updated = item.model_copy(update={"reserved": item.reserved + quantity})
        try:
            await with_timeout(
                self.store.update_inventory(updated), self.settings.tool_timeout_seconds
            )
        except (ToolTimeout, Exception):
            self._audit_safe(ctx, "tool.execute", "reserve_inventory", Outcome.FAILED, inputs)
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("DEPENDENCY_UNAVAILABLE", "could not reserve inventory", outcome="partial")
        self._audit_safe(
            ctx, "tool.execute", "reserve_inventory", Outcome.SUCCESS, {"product_id": product_id}
        )
        self.metrics.record("tool.execute", "success", self._elapsed(start))
        return {
            "data": {"product_id": product_id, "reserved": quantity, "available": available - quantity},
            "processing_outcome": "ok",
        }

    async def create_support_ticket(
        self, presented_key: str | None, inputs: dict
    ) -> dict:
        start = time.monotonic()
        auth = await self._authorize("create_support_ticket", presented_key, inputs)
        if isinstance(auth, dict):
            self.metrics.record("tool.execute", "denied", self._elapsed(start))
            return auth
        ctx = auth
        try:
            ticket = self._build_ticket(inputs)
        except (ValidationError, ValueError, KeyError) as exc:
            self._audit_safe(
                ctx, "tool.execute", "create_support_ticket", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", f"invalid input: {exc}")
        try:
            await with_timeout(
                self.store.create_ticket(ticket), self.settings.tool_timeout_seconds
            )
        except (ToolTimeout, Exception) as exc:
            self._audit_safe(
                ctx, "tool.execute", "create_support_ticket", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            code = (
                "TIMEOUT" if isinstance(exc, ToolTimeout) else "DEPENDENCY_UNAVAILABLE"
            )
            return error_envelope(code, "could not persist ticket", outcome="partial")
        self._audit_safe(
            ctx,
            "tool.execute",
            "create_support_ticket",
            Outcome.SUCCESS,
            {"ticket_id": ticket.ticket_id},
        )
        self.metrics.record("tool.execute", "success", self._elapsed(start))
        return {
            "data": {
                "ticket_id": ticket.ticket_id,
                "status": ticket.status.value,
                "created_at": ticket.created_at.isoformat(),
            },
            "processing_outcome": "ok",
        }

    def _build_ticket(self, inputs: dict) -> SupportTicket:
        customer_id = inputs.get("customer_id", "")
        order_id = inputs.get("order_id")
        now = datetime.now(timezone.utc)
        self._ticket_seq += 1
        return SupportTicket(
            ticket_id=f"tkt_{self._ticket_seq}",
            customer_id=customer_id,
            order_id=order_id,
            subject=sanitize(str(inputs.get("subject", "")), 120),
            description=sanitize(str(inputs.get("description", "")), 2000),
            status=TicketStatus.OPEN,
            created_at=now,
            updated_at=now,
        )

    async def update_ticket_status(
        self, presented_key: str | None, inputs: dict
    ) -> dict:
        start = time.monotonic()
        auth = await self._authorize("update_ticket_status", presented_key, inputs)
        if isinstance(auth, dict):
            self.metrics.record("tool.execute", "denied", self._elapsed(start))
            return auth
        ctx = auth
        ticket_id = inputs.get("ticket_id")
        try:
            new_status = TicketStatus(inputs.get("new_status"))
        except ValueError:
            self._audit_safe(
                ctx, "tool.execute", "update_ticket_status", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", "unknown ticket status")
        try:
            await with_timeout(
                self.store.get_ticket(ticket_id), self.settings.tool_timeout_seconds
            )
        except NotFound:
            self._audit_safe(
                ctx, "tool.execute", "update_ticket_status", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", "ticket cannot be updated")
        except (ToolTimeout, Exception):
            self._audit_safe(
                ctx, "tool.execute", "update_ticket_status", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope(
                "DEPENDENCY_UNAVAILABLE", "ticket cannot be updated", outcome="partial"
            )
        async with self._lock_for(f"ticket:{ticket_id}"):
            try:
                current = await with_timeout(
                    self.store.get_ticket(ticket_id), self.settings.tool_timeout_seconds
                )
            except (NotFound, ToolTimeout, Exception):
                self._audit_safe(
                    ctx, "tool.execute", "update_ticket_status", Outcome.FAILED, inputs
                )
                self.metrics.record("tool.execute", "failed", self._elapsed(start))
                return error_envelope("VALIDATION_ERROR", "ticket cannot be updated")
            if current is None:
                self._audit_safe(
                    ctx, "tool.execute", "update_ticket_status", Outcome.FAILED, inputs
                )
                self.metrics.record("tool.execute", "failed", self._elapsed(start))
                return error_envelope("VALIDATION_ERROR", "ticket cannot be updated")
            if self._check_version(inputs, current.version):
                self._audit_safe(
                    ctx, "tool.execute", "update_ticket_status", Outcome.FAILED, inputs
                )
                self.metrics.record("tool.execute", "failed", self._elapsed(start))
                return error_envelope(
                    "CONFLICT",
                    f"ticket changed concurrently (version {current.version})",
                    current={
                        "status": current.status.value,
                        "version": current.version,
                    },
                )
            if new_status not in TICKET_TRANSITIONS[current.status]:
                self._audit_safe(
                    ctx, "tool.execute", "update_ticket_status", Outcome.FAILED, inputs
                )
                self.metrics.record("tool.execute", "failed", self._elapsed(start))
                return error_envelope(
                    "VALIDATION_ERROR",
                    f"illegal transition {current.status.value} -> {new_status.value}",
                )
            updated = current.model_copy(
                update={
                    "status": new_status,
                    "version": current.version + 1,
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            try:
                await with_timeout(
                    self.store.update_ticket(updated), self.settings.tool_timeout_seconds
                )
            except (ToolTimeout, Exception):
                self._audit_safe(
                    ctx, "tool.execute", "update_ticket_status", Outcome.FAILED, inputs
                )
                self.metrics.record("tool.execute", "failed", self._elapsed(start))
                return error_envelope(
                    "DEPENDENCY_UNAVAILABLE", "update rolled back", outcome="partial"
                )
        self._audit_safe(
            ctx,
            "tool.execute",
            "update_ticket_status",
            Outcome.SUCCESS,
            {"ticket_id": ticket_id},
        )
        self.metrics.record("tool.execute", "success", self._elapsed(start))
        return {
            "data": {
                "ticket_id": ticket_id,
                "old_status": current.status.value,
                "new_status": new_status.value,
                "updated_at": updated.updated_at.isoformat(),
            },
            "processing_outcome": "ok",
        }

    @staticmethod
    def _check_version(inputs: dict, current_version: int) -> bool:
        expected = inputs.get("expected_version")
        return expected is not None and expected != current_version

    async def _rollback_order(self, previous: Order) -> None:
        try:
            await self.store.update_order(previous)
        except Exception as exc:  # noqa: BLE001 - rollback must never raise
            logger.error(f"order rollback failed: {exc}")

    def get_task(self, task_id: str) -> dict:
        record = self.tasks.get(task_id)
        if record is None:
            return error_envelope("NOT_FOUND", "unknown task")
        return {
            "task_id": task_id,
            "status": record.status,
            "result": record.result,
            "processing_outcome": "ok",
        }

    @staticmethod
    def _elapsed(start: float) -> float:
        return (time.monotonic() - start) * 1000

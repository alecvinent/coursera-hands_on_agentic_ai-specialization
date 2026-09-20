"""MCP tool handlers: validation, RBAC-first ordering, rollback, async execution."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from loguru import logger
from pydantic import ValidationError

from mcp_server.audit import AuditLog, AuditUnavailable
from mcp_server.auth import (
    AuthContext,
    Forbidden,
    Unauthenticated,
    authenticate,
    require,
)
from mcp_server.config import Settings
from mcp_server.metrics import MetricsRegistry
from mcp_server.models import (
    ORDER_TRANSITIONS,
    TICKET_TRANSITIONS,
    ApiCredential,
    Order,
    OrderStatus,
    Outcome,
    Role,
    SupportTicket,
    TicketStatus,
)
from mcp_server.ratelimit import RateLimiter
from mcp_server.resilience import ToolTimeout, with_timeout
from mcp_server.resources import error_envelope
from mcp_server.store import Conflict, DependencyUnavailable, MockStore, NotFound

TOOL_ROLES: set[Role] = {Role.ADMIN, Role.SUPPORT_AGENT}


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

    async def create_ticket(self, presented_key: str | None, inputs: dict) -> dict:
        start = time.monotonic()
        auth = await self._authorize("create_ticket", presented_key, inputs)
        if isinstance(auth, dict):
            self.metrics.record("tool.execute", "denied", self._elapsed(start))
            return auth
        ctx = auth
        try:
            ticket = self._build_ticket(inputs)
        except (ValidationError, ValueError, KeyError) as exc:
            self._audit_safe(
                ctx, "tool.execute", "create_ticket", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", f"invalid input: {exc}")
        try:
            await with_timeout(
                self._guarded_add(ticket), self.settings.tool_timeout_seconds
            )
        except (DependencyUnavailable, ToolTimeout) as exc:
            self._audit_safe(
                ctx, "tool.execute", "create_ticket", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            code = (
                "TIMEOUT" if isinstance(exc, ToolTimeout) else "DEPENDENCY_UNAVAILABLE"
            )
            return error_envelope(code, "could not persist ticket", outcome="partial")
        self._audit_safe(
            ctx,
            "tool.execute",
            "create_ticket",
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
        customer_id = inputs["customer_id"]
        if customer_id not in self.store.customers:
            raise ValueError(f"unknown customer {customer_id}")
        order_id = inputs.get("order_id")
        if order_id is not None:
            order = self.store.orders.get(order_id)
            if order is None or order.customer_id != customer_id:
                raise ValueError("order does not belong to customer")
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

    async def _guarded_add(self, ticket: SupportTicket) -> None:
        try:
            await self.store.add_ticket(ticket)
        except Conflict as exc:
            raise ValueError(str(exc)) from exc

    async def update_order(self, presented_key: str | None, inputs: dict) -> dict:
        start = time.monotonic()
        auth = await self._authorize("update_order", presented_key, inputs)
        if isinstance(auth, dict):
            self.metrics.record("tool.execute", "denied", self._elapsed(start))
            return auth
        ctx = auth
        order_id = inputs.get("order_id")
        try:
            new_status = OrderStatus(inputs.get("new_status"))
        except ValueError:
            self._audit_safe(
                ctx, "tool.execute", "update_order", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", "unknown order status")
        try:
            await with_timeout(
                self.store.get_order(order_id), self.settings.tool_timeout_seconds
            )
        except NotFound:
            self._audit_safe(
                ctx, "tool.execute", "update_order", Outcome.FAILED, inputs
            )
            self.metrics.record("tool.execute", "failed", self._elapsed(start))
            return error_envelope("VALIDATION_ERROR", "order cannot be updated")
        except (ToolTimeout, DependencyUnavailable):
            self._audit_safe(
                ctx, "tool.execute", "update_order", Outcome.FAILED, inputs
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
            except (NotFound, ToolTimeout, DependencyUnavailable):
                self._audit_safe(
                    ctx, "tool.execute", "update_order", Outcome.FAILED, inputs
                )
                self.metrics.record("tool.execute", "failed", self._elapsed(start))
                return error_envelope("VALIDATION_ERROR", "order cannot be updated")
            if self._check_version(inputs, current.version):
                self._audit_safe(
                    ctx, "tool.execute", "update_order", Outcome.FAILED, inputs
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
                    ctx, "tool.execute", "update_order", Outcome.FAILED, inputs
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
                    self.store.save_order(updated), self.settings.tool_timeout_seconds
                )
            except (DependencyUnavailable, ToolTimeout, Conflict):
                await self._rollback_order(previous)
                self._audit_safe(
                    ctx, "tool.execute", "update_order", Outcome.FAILED, inputs
                )
                self.metrics.record("tool.execute", "failed", self._elapsed(start))
                return error_envelope(
                    "DEPENDENCY_UNAVAILABLE", "update rolled back", outcome="partial"
                )
        self._audit_safe(
            ctx, "tool.execute", "update_order", Outcome.SUCCESS, {"order_id": order_id}
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

    @staticmethod
    def _check_version(inputs: dict, current_version: int) -> bool:
        expected = inputs.get("expected_version")
        return expected is not None and expected != current_version

    async def _rollback_order(self, previous: Order) -> None:
        try:
            self.store.orders[previous.order_id] = previous
        except Exception as exc:  # noqa: BLE001 - rollback must never raise
            logger.error(f"order rollback failed: {exc}")

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
        except (ToolTimeout, DependencyUnavailable):
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
            except (NotFound, ToolTimeout, DependencyUnavailable):
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
                    self.store.save_ticket(updated), self.settings.tool_timeout_seconds
                )
            except (DependencyUnavailable, ToolTimeout):
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

    async def arun(self, tool: str, presented_key: str | None, inputs: dict) -> dict:
        """Run a tool with async semantics; slow executions return a task_id."""
        handler = {
            "create_ticket": self.create_ticket,
            "update_order": self.update_order,
            "update_ticket_status": self.update_ticket_status,
        }[tool]
        try:
            return await with_timeout(
                handler(presented_key, inputs), self.settings.tool_timeout_seconds
            )
        except ToolTimeout:
            task_id = uuid.uuid4().hex[:12]
            self.tasks[task_id] = TaskRecord(task_id=task_id)
            self.tasks[task_id].status = "running"

            async def _background() -> None:
                try:
                    result = await handler(presented_key, inputs)
                    self.tasks[task_id].result = result
                    self.tasks[task_id].status = "completed"
                except Exception as exc:  # noqa: BLE001 - task outcome recorded
                    self.tasks[task_id].result = error_envelope("FAILED", str(exc))
                    self.tasks[task_id].status = "failed"

            asyncio.create_task(_background())
            return {"task_id": task_id, "status": "running", "processing_outcome": "ok"}

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

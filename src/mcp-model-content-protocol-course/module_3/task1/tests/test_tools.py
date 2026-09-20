"""Unit tests for US2 tools (T024). Written first; must fail before T025."""

import asyncio
from unittest import TestCase

from mcp_server.models import OrderStatus
from mcp_server.tools import ToolService

from tests.fixtures import (
    TEST_KEYS,
    make_audit,
    make_limiter,
    make_metrics,
    make_settings,
    make_store,
)


def make_service(**overrides):
    settings = overrides.pop("settings", make_settings())
    return ToolService(
        settings=settings,
        credentials=overrides.pop("credentials", dict(TEST_KEYS)),
        store=overrides.pop("store", make_store(settings)),
        audit=overrides.pop("audit", make_audit()),
        metrics=overrides.pop("metrics", make_metrics()),
        limiter=overrides.pop("limiter", make_limiter(settings)),
    )


def run(coro):
    return asyncio.run(coro)


AGENT_KEY = "test-agent-secret-key-1"
AUDITOR_KEY = "test-auditor-secret-key-1"


class TestCreateTicket(TestCase):
    def test_valid_input_creates_and_is_retrievable(self) -> None:
        svc = make_service()
        res = run(
            svc.create_ticket(
                AGENT_KEY,
                {
                    "customer_id": "cust_1001",
                    "subject": "Where is my package?",
                    "description": "Order seems delayed.",
                },
            )
        )
        self.assertIn("data", res)
        ticket = run(svc.store.get_ticket(res["data"]["ticket_id"]))
        self.assertEqual(ticket.subject, "Where is my package?")

    def test_invalid_input_changes_nothing(self) -> None:
        svc = make_service()
        before = len(svc.store.tickets)
        res = run(
            svc.create_ticket(AGENT_KEY, {"customer_id": "cust_1001", "subject": "x"})
        )
        self.assertEqual(res["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(len(svc.store.tickets), before)

    def test_unauthorized_role_denied_before_write(self) -> None:
        svc = make_service()
        before = len(svc.store.tickets)
        res = run(
            svc.create_ticket(
                AUDITOR_KEY,
                {
                    "customer_id": "cust_1001",
                    "subject": "Valid subject here",
                    "description": "Valid description.",
                },
            )
        )
        self.assertEqual(res["error"]["code"], "FORBIDDEN")
        self.assertEqual(len(svc.store.tickets), before)

    def test_executions_are_audited(self) -> None:
        audit = make_audit()
        svc = make_service(audit=audit)
        run(
            svc.create_ticket(
                AGENT_KEY,
                {
                    "customer_id": "cust_1001",
                    "subject": "Audit me please",
                    "description": "Checking audit.",
                },
            )
        )
        kinds = {(r.action, r.outcome.value) for r in audit.list_records()}
        self.assertIn(("tool.execute", "success"), kinds)


class TestUpdateOrder(TestCase):
    def _pending_order_id(self, svc) -> str:
        for order in svc.store.orders.values():
            if order.status == OrderStatus.PENDING:
                return order.order_id
        raise AssertionError("seed must contain a pending order")

    def test_legal_transition_succeeds(self) -> None:
        svc = make_service()
        order_id = self._pending_order_id(svc)
        res = run(
            svc.update_order(
                AGENT_KEY, {"order_id": order_id, "new_status": "confirmed"}
            )
        )
        self.assertEqual(res["data"]["new_status"], "confirmed")

    def test_illegal_transition_rejected_without_change(self) -> None:
        svc = make_service()
        order_id = self._pending_order_id(svc)
        res = run(
            svc.update_order(
                AGENT_KEY, {"order_id": order_id, "new_status": "delivered"}
            )
        )
        self.assertEqual(res["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(run(svc.store.get_order(order_id)).status, OrderStatus.PENDING)

    def test_failure_rolls_back(self) -> None:
        settings = make_settings()
        svc = make_service(settings=settings, store=make_store(settings))
        order_id = self._pending_order_id(svc)
        settings.mock_failure_mode = "unavailable"
        res = run(
            svc.update_order(
                AGENT_KEY, {"order_id": order_id, "new_status": "confirmed"}
            )
        )
        self.assertEqual(res["processing_outcome"], "partial")
        settings.mock_failure_mode = "off"
        self.assertEqual(run(svc.store.get_order(order_id)).status, OrderStatus.PENDING)


class TestAsyncExecution(TestCase):
    def test_slow_execution_returns_task_id(self) -> None:
        settings = make_settings(
            tool_timeout_seconds=0.01, mock_latency_ms=50, mock_failure_mode="slow"
        )
        svc = make_service(settings=settings, store=make_store(settings))
        res = run(
            svc.arun(
                "create_ticket",
                AGENT_KEY,
                {
                    "customer_id": "cust_1001",
                    "subject": "Slow subject here",
                    "description": "Slow description.",
                },
            )
        )
        self.assertEqual(res["status"], "running")
        self.assertIn("task_id", res)
        self.assertEqual(svc.get_task(res["task_id"])["status"], "running")
        self.assertEqual(svc.get_task("nope")["error"]["code"], "NOT_FOUND")

"""End-to-end workflow tests (T034): seed → auth → read → write → audit → health."""

import asyncio
import time
from unittest import TestCase

from mcp_server.models import OrderStatus, Role
from mcp_server.ops_app import OpsDeps, get_health, get_metrics
from mcp_server.resources import ResourceService
from mcp_server.tools import ToolService

from tests.fixtures import (
    TEST_KEYS,
    make_audit,
    make_breaker,
    make_cache,
    make_ctx,
    make_limiter,
    make_metrics,
    make_settings,
    make_store,
)


def run(coro):
    return asyncio.run(coro)


AGENT_KEY = "test-agent-secret-key-1"
ADMIN_KEY = "test-admin-secret-key-1"
OPERATOR_KEY = "test-operator-secret-key-1"


class TestLookupToResolutionFlow(TestCase):
    def setUp(self) -> None:
        self.settings = make_settings()
        self.store = make_store(self.settings)
        self.audit = make_audit()
        self.metrics = make_metrics()
        self.resources = ResourceService(
            self.settings,
            dict(TEST_KEYS),
            self.store,
            make_cache(self.settings),
            self.audit,
            self.metrics,
            make_limiter(self.settings),
            make_breaker(),
        )
        self.tools = ToolService(
            self.settings,
            dict(TEST_KEYS),
            self.store,
            self.audit,
            self.metrics,
            make_limiter(self.settings),
        )

    def test_full_flow_under_five_minutes(self) -> None:
        started = time.monotonic()
        customer = run(self.resources.read("store://customers/cust_1001", AGENT_KEY))
        self.assertIn("data", customer)
        orders = run(
            self.resources.read("store://customers/cust_1001/orders", AGENT_KEY)
        )
        self.assertTrue(orders["data"])
        created = run(
            self.tools.create_ticket(
                AGENT_KEY,
                {
                    "customer_id": "cust_1001",
                    "subject": "Help with my delivery",
                    "description": "Package is late.",
                },
            )
        )
        self.assertIn("data", created)
        ticket = run(
            self.resources.read(
                f"store://tickets/{created['data']['ticket_id']}", AGENT_KEY
            )
        )
        self.assertEqual(ticket["data"]["status"], "open")
        updated = run(
            self.tools.update_ticket_status(
                AGENT_KEY,
                {
                    "ticket_id": created["data"]["ticket_id"],
                    "new_status": "in_progress",
                },
            )
        )
        self.assertEqual(updated["data"]["new_status"], "in_progress")
        audit_entries = self.audit.list_records()
        self.assertGreaterEqual(len(audit_entries), 5)
        self.assertLess(time.monotonic() - started, 5 * 60)

    def test_order_update_visible_on_reread(self) -> None:
        pending = next(
            o.order_id
            for o in self.store.orders.values()
            if o.status == OrderStatus.PENDING
        )
        run(
            self.tools.update_order(
                AGENT_KEY, {"order_id": pending, "new_status": "confirmed"}
            )
        )
        reread = run(self.resources.read(f"store://orders/{pending}", AGENT_KEY))
        self.assertEqual(reread["data"]["status"], "confirmed")

    def test_health_reflects_traffic(self) -> None:
        run(self.resources.read("store://products", AGENT_KEY))
        deps = OpsDeps(
            settings=self.settings,
            credentials=dict(TEST_KEYS),
            store=self.store,
            audit=self.audit,
            metrics=self.metrics,
            breaker=make_breaker(),
            started_at=time.monotonic(),
        )
        self.assertEqual(get_health(deps)["status"], "healthy")
        snap = get_metrics(deps, make_ctx(Role.OPERATOR))
        self.assertGreater(snap["requests_count"], 0)

    def test_server_assembly_registers_surface(self) -> None:
        from mcp_server.server import build_server

        server = build_server(self.settings, ADMIN_KEY)
        listed_tools = run(server.list_tools())
        names = {t.name for t in listed_tools}
        self.assertTrue(
            {"create_ticket", "update_order", "update_ticket_status"} <= names
        )
        templates = run(server.list_resource_templates())
        self.assertGreaterEqual(len(templates), 8)

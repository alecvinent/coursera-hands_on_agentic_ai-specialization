"""Integration tests for end-to-end workflows."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from mcp_portfolio.auth import AuthContext, Forbidden, Unauthenticated, authenticate, require
from mcp_portfolio.models import (
    MASKED,
    Order,
    OrderItem,
    OrderStatus,
    RESOURCE_ROLES_READ,
    SupportTicket,
    TicketStatus,
    TOOL_ROLES,
)
from mcp_portfolio.store import MockStore

from .fixtures import ADMIN_KEY, AUDITOR_KEY, OPERATOR_KEY, SUPPORT_KEY, make_settings, make_store


class TestFullReadWorkflow(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings(
            seed_customers=3, seed_orders=5, seed_products=4, seed_tickets=4, seed=42
        )
        self.credentials = self.settings.api_keys
        self.store = make_store(self.settings)

    async def test_full_read_workflow(self) -> None:
        ctx = authenticate(self.credentials, SUPPORT_KEY)
        require(ctx, RESOURCE_ROLES_READ)
        self.assertEqual(ctx.role.value, "support_agent")

        customer = await self.store.get_customer("cust_0001")
        self.assertIsNotNone(customer)
        self.assertEqual(customer.customer_id, "cust_0001")

        orders = await self.store.get_customer_orders("cust_0001")
        self.assertIsInstance(orders, list)
        for order in orders:
            self.assertEqual(order.customer_id, "cust_0001")
            self.assertTrue(len(order.items) > 0)

        products = await self.store.get_all_products()
        self.assertGreater(len(products), 0)
        for product in products:
            self.assertGreater(product.price, 0)

    async def test_full_read_workflow_auditor(self) -> None:
        ctx = authenticate(self.credentials, AUDITOR_KEY)
        require(ctx, RESOURCE_ROLES_READ)

        customer = await self.store.get_customer("cust_0002")
        self.assertIsNotNone(customer)

        masked = customer.model_copy(
            update={
                "email": MASKED,
                "phone": MASKED if customer.phone else None,
                "address": MASKED if customer.address else None,
            }
        )
        self.assertEqual(masked.email, MASKED)
        self.assertEqual(masked.full_name, customer.full_name)


class TestFullWriteWorkflow(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings(
            seed_customers=2, seed_orders=3, seed_products=3, seed_tickets=2, seed=42
        )
        self.credentials = self.settings.api_keys
        self.store = make_store(self.settings)
        self.now = datetime.now(timezone.utc)

    async def test_full_write_workflow(self) -> None:
        ctx = authenticate(self.credentials, SUPPORT_KEY)
        require(ctx, TOOL_ROLES)

        ticket = SupportTicket(
            ticket_id="tkt_9001",
            customer_id="cust_0001",
            subject="Refund request",
            description="Customer wants a refund for order ord_0001",
            status=TicketStatus.OPEN,
            created_at=self.now,
            updated_at=self.now,
        )
        created = await self.store.create_ticket(ticket)
        self.assertEqual(created.status, TicketStatus.OPEN)

        in_progress = created.model_copy(
            update={
                "status": TicketStatus.IN_PROGRESS,
                "updated_at": self.now,
                "version": created.version + 1,
            }
        )
        updated = await self.store.update_ticket(in_progress)
        self.assertEqual(updated.status, TicketStatus.IN_PROGRESS)
        self.assertEqual(updated.version, 1)

        resolved = updated.model_copy(
            update={
                "status": TicketStatus.RESOLVED,
                "updated_at": self.now,
                "version": updated.version + 1,
            }
        )
        final = await self.store.update_ticket(resolved)
        self.assertEqual(final.status, TicketStatus.RESOLVED)

        fetched = await self.store.get_ticket("tkt_9001")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.status, TicketStatus.RESOLVED)

    async def test_full_order_workflow(self) -> None:
        ctx = authenticate(self.credentials, ADMIN_KEY)
        require(ctx, TOOL_ROLES)

        product = await self.store.get_product("prd_0001")
        self.assertIsNotNone(product)

        order = Order(
            order_id="ord_9001",
            customer_id="cust_0001",
            items=[
                OrderItem(
                    product_id="prd_0001",
                    quantity=2,
                    unit_price=product.price,
                )
            ],
            total=product.price * 2,
            status=OrderStatus.PENDING,
            created_at=self.now,
            updated_at=self.now,
        )
        created = await self.store.create_order(order)
        self.assertEqual(created.status, OrderStatus.PENDING)

        confirmed = created.model_copy(
            update={
                "status": OrderStatus.CONFIRMED,
                "updated_at": self.now,
                "version": created.version + 1,
            }
        )
        updated = await self.store.update_order(confirmed)
        self.assertEqual(updated.status, OrderStatus.CONFIRMED)

        fetched = await self.store.get_order("ord_9001")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.status, OrderStatus.CONFIRMED)


class TestUnauthorizedAccessDenied(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings()
        self.credentials = self.settings.api_keys
        self.store = make_store(self.settings)

    async def test_unauthenticated_access_denied(self) -> None:
        with self.assertRaises(Unauthenticated):
            authenticate(self.credentials, None)

    async def test_invalid_key_access_denied(self) -> None:
        with self.assertRaises(Unauthenticated):
            authenticate(self.credentials, "not-a-real-key-12345678")

    async def test_forbidden_role_access_denied(self) -> None:
        ctx = authenticate(self.credentials, AUDITOR_KEY)
        with self.assertRaises(Forbidden):
            require(ctx, TOOL_ROLES)

    async def test_read_role_cannot_write(self) -> None:
        ctx = authenticate(self.credentials, AUDITOR_KEY)
        require(ctx, RESOURCE_ROLES_READ)
        with self.assertRaises(Forbidden):
            require(ctx, TOOL_ROLES)

    async def test_support_cannot_access_inventory_tools(self) -> None:
        from mcp_portfolio.models import INVENTORY_TOOL_ROLES

        ctx = authenticate(self.credentials, SUPPORT_KEY)
        with self.assertRaises(Forbidden):
            require(ctx, INVENTORY_TOOL_ROLES)


class TestRateLimiting(unittest.TestCase):
    def test_rate_limit_allows_within_burst(self) -> None:
        from mcp_portfolio.ratelimit import RateLimiter

        clock_val = 1000.0

        def mock_clock() -> float:
            return clock_val

        limiter = RateLimiter(per_minute=60, burst=5, clock=mock_clock)
        for _ in range(5):
            allowed, retry_ms = limiter.allow("key-1")
            self.assertTrue(allowed)
            self.assertEqual(retry_ms, 0)

    def test_rate_limit_blocks_after_burst(self) -> None:
        from mcp_portfolio.ratelimit import RateLimiter

        clock_val = 1000.0

        def mock_clock() -> float:
            return clock_val

        limiter = RateLimiter(per_minute=60, burst=3, clock=mock_clock)
        for _ in range(3):
            allowed, _ = limiter.allow("key-1")
            self.assertTrue(allowed)

        allowed, retry_ms = limiter.allow("key-1")
        self.assertFalse(allowed)
        self.assertGreater(retry_ms, 0)

    def test_rate_limit_refills_over_time(self) -> None:
        from mcp_portfolio.ratelimit import RateLimiter

        clock_val = 1000.0

        def mock_clock() -> float:
            return clock_val

        limiter = RateLimiter(per_minute=60, burst=2, clock=mock_clock)
        for _ in range(2):
            limiter.allow("key-1")

        allowed, _ = limiter.allow("key-1")
        self.assertFalse(allowed)

        clock_val = 1001.0
        allowed, _ = limiter.allow("key-1")
        self.assertTrue(allowed)

    def test_rate_limit_separate_keys(self) -> None:
        from mcp_portfolio.ratelimit import RateLimiter

        clock_val = 1000.0

        def mock_clock() -> float:
            return clock_val

        limiter = RateLimiter(per_minute=60, burst=1, clock=mock_clock)
        allowed, _ = limiter.allow("key-a")
        self.assertTrue(allowed)

        allowed, _ = limiter.allow("key-a")
        self.assertFalse(allowed)

        allowed, _ = limiter.allow("key-b")
        self.assertTrue(allowed)


if __name__ == "__main__":
    unittest.main()

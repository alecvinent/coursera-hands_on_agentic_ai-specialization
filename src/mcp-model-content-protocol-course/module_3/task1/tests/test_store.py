"""Unit tests for store seeding and injection flags (T017)."""

import asyncio
from unittest import TestCase

from mcp_server.store import Conflict, DependencyUnavailable, MockStore, NotFound

from tests.fixtures import make_settings, make_store


def run(coro):
    return asyncio.run(coro)


class TestSeedDeterminism(TestCase):
    def test_same_seed_same_data(self) -> None:
        first = make_store()
        second = make_store()
        self.assertEqual(
            [c.customer_id for c in first.customers.values()],
            [c.customer_id for c in second.customers.values()],
        )
        self.assertEqual(len(first.customers), make_settings().seed_customers)

    def test_reset_restores_seed(self) -> None:
        store = make_store()
        store.customers.pop("cust_1001")
        store.reset()
        self.assertIn("cust_1001", store.customers)


class TestStoreReads(TestCase):
    def test_unknown_customer_raises_not_found(self) -> None:
        store = make_store()
        with self.assertRaises(NotFound):
            run(store.get_customer("cust_9999"))

    def test_order_totals_consistent(self) -> None:
        store = make_store()
        for order in store.orders.values():
            expected = sum(i.quantity * i.unit_price for i in order.items)
            self.assertEqual(order.total, expected)


class TestInjectionFlags(TestCase):
    def test_unavailable_mode_raises(self) -> None:
        store = MockStore(make_settings(mock_failure_mode="unavailable"))
        with self.assertRaises(DependencyUnavailable):
            run(store.list_products())

    def test_conflict_on_duplicate_ticket(self) -> None:
        from datetime import datetime, timezone

        from mcp_server.models import SupportTicket

        store = make_store()
        existing = next(iter(store.tickets.values()))
        dup = SupportTicket(
            ticket_id=existing.ticket_id,
            customer_id=existing.customer_id,
            subject="Another valid subject",
            description="Another description.",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        with self.assertRaises(Conflict):
            run(store.add_ticket(dup))

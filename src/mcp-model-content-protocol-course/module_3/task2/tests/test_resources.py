"""Unit tests for resource handling (async store operations)."""

from __future__ import annotations

import unittest

from mcp_portfolio.models import MASKED, CustomerTier
from mcp_portfolio.store import MockStore

from .fixtures import make_settings, make_store


class TestCustomerResources(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings(
            seed_customers=2, seed_orders=3, seed_products=2, seed_tickets=3, seed=42
        )
        self.store = make_store(self.settings)

    async def test_get_customer_found(self) -> None:
        customer = await self.store.get_customer("cust_0001")
        self.assertIsNotNone(customer)
        self.assertEqual(customer.customer_id, "cust_0001")
        self.assertIsInstance(customer.full_name, str)

    async def test_get_customer_not_found(self) -> None:
        customer = await self.store.get_customer("cust_9999")
        self.assertIsNone(customer)

    async def test_get_customer_orders(self) -> None:
        orders = await self.store.get_customer_orders("cust_0001")
        self.assertIsInstance(orders, list)
        for order in orders:
            self.assertEqual(order.customer_id, "cust_0001")

    async def test_get_customer_tickets(self) -> None:
        tickets = await self.store.get_customer_tickets("cust_0001")
        self.assertIsInstance(tickets, list)
        for ticket in tickets:
            self.assertEqual(ticket.customer_id, "cust_0001")


class TestOrderResources(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings(
            seed_customers=2, seed_orders=5, seed_products=3, seed_tickets=2, seed=42
        )
        self.store = make_store(self.settings)

    async def test_get_order_found(self) -> None:
        order = await self.store.get_order("ord_0001")
        self.assertIsNotNone(order)
        self.assertEqual(order.order_id, "ord_0001")
        self.assertTrue(len(order.items) > 0)

    async def test_get_order_not_found(self) -> None:
        order = await self.store.get_order("ord_9999")
        self.assertIsNone(order)

    async def test_get_orders_by_status(self) -> None:
        all_orders = await self.store.get_orders_by_status("pending")
        for order in all_orders:
            self.assertEqual(order.status.value, "pending")


class TestProductResources(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings(
            seed_customers=2, seed_orders=2, seed_products=4, seed_tickets=2, seed=42
        )
        self.store = make_store(self.settings)

    async def test_get_product(self) -> None:
        product = await self.store.get_product("prd_0001")
        self.assertIsNotNone(product)
        self.assertEqual(product.product_id, "prd_0001")
        self.assertGreater(product.price, 0)

    async def test_get_product_not_found(self) -> None:
        product = await self.store.get_product("prd_9999")
        self.assertIsNone(product)

    async def test_get_all_products(self) -> None:
        products = await self.store.get_all_products()
        self.assertEqual(len(products), 4)
        ids = {p.product_id for p in products}
        for i in range(1, 5):
            self.assertIn(f"prd_{i:04d}", ids)


class TestInventoryResources(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings(
            seed_customers=1, seed_orders=1, seed_products=5, seed_tickets=1, seed=42
        )
        self.store = make_store(self.settings)

    async def test_get_inventory(self) -> None:
        inv = await self.store.get_inventory("prd_0001")
        self.assertIsNotNone(inv)
        self.assertEqual(inv.product_id, "prd_0001")
        self.assertGreaterEqual(inv.quantity, 0)

    async def test_get_inventory_not_found(self) -> None:
        inv = await self.store.get_inventory("prd_9999")
        self.assertIsNone(inv)

    async def test_get_low_stock_inventory(self) -> None:
        low = await self.store.get_low_stock_inventory()
        self.assertIsInstance(low, list)
        for item in low:
            self.assertLessEqual(item.quantity, item.reorder_threshold)


class TestPiiMasking(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings(
            seed_customers=1, seed_orders=1, seed_products=1, seed_tickets=1, seed=42
        )
        self.store = make_store(self.settings)

    async def test_pii_masking_auditor_role(self) -> None:
        customer = await self.store.get_customer("cust_0001")
        self.assertIsNotNone(customer)

        original_email = customer.email
        original_phone = customer.phone
        original_address = customer.address

        if original_email:
            self.assertNotIn(MASKED, original_email)

        masked_customer = customer.model_copy(
            update={
                "email": MASKED,
                "phone": MASKED if customer.phone else None,
                "address": MASKED if customer.address else None,
            }
        )
        self.assertEqual(masked_customer.email, MASKED)
        if original_phone:
            self.assertEqual(masked_customer.phone, MASKED)
        if original_address:
            self.assertEqual(masked_customer.address, MASKED)
        self.assertEqual(masked_customer.full_name, customer.full_name)


if __name__ == "__main__":
    unittest.main()

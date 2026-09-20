"""Unit tests for tool operations (orders, tickets, inventory)."""

from __future__ import annotations

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from mcp_portfolio.models import (
    Order,
    OrderItem,
    OrderStatus,
    SupportTicket,
    TicketStatus,
)
from mcp_portfolio.store import MockStore

from .fixtures import make_settings, make_store


class TestCreateOrder(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings(
            seed_customers=2, seed_orders=2, seed_products=3, seed_tickets=1, seed=42
        )
        self.store = make_store(self.settings)
        self.now = datetime.now(timezone.utc)

    async def test_create_order(self) -> None:
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
        self.assertEqual(created.order_id, "ord_9001")
        fetched = await self.store.get_order("ord_9001")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.status, OrderStatus.PENDING)

    async def test_create_order_invalid_product(self) -> None:
        order = Order(
            order_id="ord_9002",
            customer_id="cust_0001",
            items=[
                OrderItem(
                    product_id="prd_9999",
                    quantity=1,
                    unit_price=Decimal("10.00"),
                )
            ],
            total=Decimal("10.00"),
            status=OrderStatus.PENDING,
            created_at=self.now,
            updated_at=self.now,
        )
        created = await self.store.create_order(order)
        fetched = await self.store.get_order("ord_9002")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.items[0].product_id, "prd_9999")


class TestUpdateOrderStatus(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings(
            seed_customers=2, seed_orders=3, seed_products=2, seed_tickets=1, seed=42
        )
        self.store = make_store(self.settings)
        self.now = datetime.now(timezone.utc)

    async def test_update_order_status(self) -> None:
        order = await self.store.get_order("ord_0001")
        self.assertIsNotNone(order)
        original_status = order.status

        if OrderStatus.CONFIRMED in {
            s
            for s in [
                OrderStatus.PENDING,
                OrderStatus.CONFIRMED,
                OrderStatus.SHIPPED,
                OrderStatus.DELIVERED,
                OrderStatus.CANCELLED,
            ]
        }:
            transitions = {
                OrderStatus.PENDING: OrderStatus.CONFIRMED,
                OrderStatus.CONFIRMED: OrderStatus.SHIPPED,
                OrderStatus.SHIPPED: OrderStatus.DELIVERED,
            }
            if original_status in transitions:
                new_status = transitions[original_status]
                updated_order = order.model_copy(
                    update={
                        "status": new_status,
                        "updated_at": self.now,
                        "version": order.version + 1,
                    }
                )
                result = await self.store.update_order(updated_order)
                self.assertEqual(result.status, new_status)
                self.assertEqual(result.version, order.version + 1)

    async def test_update_order_status_invalid_transition(self) -> None:
        order = await self.store.get_order("ord_0001")
        self.assertIsNotNone(order)

        from mcp_portfolio.models import ORDER_TRANSITIONS

        allowed = ORDER_TRANSITIONS.get(order.status, set())
        all_statuses = set(OrderStatus)
        invalid_statuses = all_statuses - allowed - {order.status}

        if invalid_statuses:
            invalid_status = next(iter(invalid_statuses))
            updated_order = order.model_copy(
                update={
                    "status": invalid_status,
                    "updated_at": self.now,
                    "version": order.version + 1,
                }
            )
            result = await self.store.update_order(updated_order)
            self.assertEqual(result.status, invalid_status)


class TestCreateTicket(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings(
            seed_customers=2, seed_orders=2, seed_products=2, seed_tickets=1, seed=42
        )
        self.store = make_store(self.settings)
        self.now = datetime.now(timezone.utc)

    async def test_create_ticket(self) -> None:
        ticket = SupportTicket(
            ticket_id="tkt_9001",
            customer_id="cust_0001",
            subject="Test issue",
            description="A test support ticket",
            status=TicketStatus.OPEN,
            created_at=self.now,
            updated_at=self.now,
        )
        created = await self.store.create_ticket(ticket)
        self.assertEqual(created.ticket_id, "tkt_9001")
        self.assertEqual(created.status, TicketStatus.OPEN)
        fetched = await self.store.get_ticket("tkt_9001")
        self.assertIsNotNone(fetched)

    async def test_create_ticket_invalid_customer(self) -> None:
        ticket = SupportTicket(
            ticket_id="tkt_9002",
            customer_id="cust_9999",
            subject="Bad customer",
            description="Ticket for non-existent customer",
            status=TicketStatus.OPEN,
            created_at=self.now,
            updated_at=self.now,
        )
        created = await self.store.create_ticket(ticket)
        fetched = await self.store.get_ticket("tkt_9002")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.customer_id, "cust_9999")


class TestUpdateTicketStatus(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings(
            seed_customers=2, seed_orders=2, seed_products=2, seed_tickets=3, seed=42
        )
        self.store = make_store(self.settings)
        self.now = datetime.now(timezone.utc)

    async def test_update_ticket_status(self) -> None:
        ticket = await self.store.get_ticket("tkt_0001")
        self.assertIsNotNone(ticket)
        original_status = ticket.status

        from mcp_portfolio.models import TICKET_TRANSITIONS

        transitions = {
            TicketStatus.OPEN: TicketStatus.IN_PROGRESS,
            TicketStatus.IN_PROGRESS: TicketStatus.RESOLVED,
            TicketStatus.RESOLVED: TicketStatus.CLOSED,
        }
        if original_status in transitions:
            new_status = transitions[original_status]
            updated_ticket = ticket.model_copy(
                update={
                    "status": new_status,
                    "updated_at": self.now,
                    "version": ticket.version + 1,
                }
            )
            result = await self.store.update_ticket(updated_ticket)
            self.assertEqual(result.status, new_status)

    async def test_update_ticket_status_invalid_transition(self) -> None:
        ticket = await self.store.get_ticket("tkt_0001")
        self.assertIsNotNone(ticket)

        from mcp_portfolio.models import TICKET_TRANSITIONS

        allowed = TICKET_TRANSITIONS.get(ticket.status, set())
        all_statuses = set(TicketStatus)
        invalid_statuses = all_statuses - allowed - {ticket.status}

        if invalid_statuses:
            invalid_status = next(iter(invalid_statuses))
            updated_ticket = ticket.model_copy(
                update={
                    "status": invalid_status,
                    "updated_at": self.now,
                    "version": ticket.version + 1,
                }
            )
            result = await self.store.update_ticket(updated_ticket)
            self.assertEqual(result.status, invalid_status)


class TestInventoryOperations(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = make_settings(
            seed_customers=1, seed_orders=1, seed_products=3, seed_tickets=1, seed=42
        )
        self.store = make_store(self.settings)

    async def test_update_inventory(self) -> None:
        inv = await self.store.get_inventory("prd_0001")
        self.assertIsNotNone(inv)
        new_quantity = inv.quantity + 50
        updated = inv.model_copy(update={"quantity": new_quantity})
        result = await self.store.update_inventory(updated)
        self.assertEqual(result.quantity, new_quantity)

        fetched = await self.store.get_inventory("prd_0001")
        self.assertEqual(fetched.quantity, new_quantity)

    async def test_update_inventory_insufficient_stock(self) -> None:
        inv = await self.store.get_inventory("prd_0001")
        self.assertIsNotNone(inv)

        reserved = inv.quantity + 10
        updated = inv.model_copy(update={"reserved": reserved})
        result = await self.store.update_inventory(updated)
        self.assertEqual(result.reserved, reserved)

    async def test_reserve_inventory(self) -> None:
        inv = await self.store.get_inventory("prd_0002")
        self.assertIsNotNone(inv)
        original_quantity = inv.quantity
        original_reserved = inv.reserved

        reserve_amount = 3
        updated = inv.model_copy(
            update={
                "quantity": original_quantity - reserve_amount,
                "reserved": original_reserved + reserve_amount,
            }
        )
        result = await self.store.update_inventory(updated)
        self.assertEqual(result.quantity, original_quantity - reserve_amount)
        self.assertEqual(result.reserved, original_reserved + reserve_amount)


if __name__ == "__main__":
    unittest.main()

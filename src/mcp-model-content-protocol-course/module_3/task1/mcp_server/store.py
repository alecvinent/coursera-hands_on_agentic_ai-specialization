"""In-memory mock store with failure/latency injection hooks."""

from __future__ import annotations

import asyncio

from mcp_server.config import Settings
from mcp_server.models import Customer, Order, Product, SupportTicket
from mcp_server.seed_data import SeedData, build_seed


class StoreError(Exception):
    pass


class DependencyUnavailable(StoreError):
    pass


class NotFound(StoreError):
    pass


class Conflict(StoreError):
    pass


class MockStore:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.reset()

    def reset(self) -> None:
        seed: SeedData = build_seed(self._settings)
        self.customers: dict[str, Customer] = {c.customer_id: c for c in seed.customers}
        self.products: dict[str, Product] = {p.product_id: p for p in seed.products}
        self.orders: dict[str, Order] = {o.order_id: o for o in seed.orders}
        self.tickets: dict[str, SupportTicket] = {t.ticket_id: t for t in seed.tickets}

    async def _gate(self) -> None:
        mode = self._settings.mock_failure_mode
        if mode == "unavailable":
            raise DependencyUnavailable("mock store is unavailable (injected)")
        if mode == "slow" and self._settings.mock_latency_ms > 0:
            await asyncio.sleep(self._settings.mock_latency_ms / 1000)

    async def get_customer(self, customer_id: str) -> Customer:
        await self._gate()
        try:
            return self.customers[customer_id]
        except KeyError:
            raise NotFound(f"customer {customer_id}") from None

    async def list_customer_orders(self, customer_id: str) -> list[Order]:
        await self._gate()
        if customer_id not in self.customers:
            raise NotFound(f"customer {customer_id}")
        return [o for o in self.orders.values() if o.customer_id == customer_id]

    async def list_customer_tickets(self, customer_id: str) -> list[SupportTicket]:
        await self._gate()
        if customer_id not in self.customers:
            raise NotFound(f"customer {customer_id}")
        return [t for t in self.tickets.values() if t.customer_id == customer_id]

    async def get_order(self, order_id: str) -> Order:
        await self._gate()
        try:
            return self.orders[order_id]
        except KeyError:
            raise NotFound(f"order {order_id}") from None

    async def list_orders_by_status(self, status: str) -> list[Order]:
        await self._gate()
        return [o for o in self.orders.values() if o.status.value == status]

    async def get_ticket(self, ticket_id: str) -> SupportTicket:
        await self._gate()
        try:
            return self.tickets[ticket_id]
        except KeyError:
            raise NotFound(f"ticket {ticket_id}") from None

    async def list_tickets_by_status(self, status: str) -> list[SupportTicket]:
        await self._gate()
        return [t for t in self.tickets.values() if t.status.value == status]

    async def get_product(self, product_id: str) -> Product:
        await self._gate()
        try:
            return self.products[product_id]
        except KeyError:
            raise NotFound(f"product {product_id}") from None

    async def list_products(self) -> list[Product]:
        await self._gate()
        return list(self.products.values())

    async def add_ticket(self, ticket: SupportTicket) -> SupportTicket:
        await self._gate()
        if ticket.ticket_id in self.tickets:
            raise Conflict(f"ticket {ticket.ticket_id} already exists")
        self.tickets[ticket.ticket_id] = ticket
        return ticket

    async def save_order(self, order: Order) -> Order:
        await self._gate()
        self.orders[order.order_id] = order
        return order

    async def save_ticket(self, ticket: SupportTicket) -> SupportTicket:
        await self._gate()
        self.tickets[ticket.ticket_id] = ticket
        return ticket

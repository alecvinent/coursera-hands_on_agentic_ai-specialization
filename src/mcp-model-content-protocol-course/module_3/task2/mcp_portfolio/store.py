"""In-memory mock store with seeded data. Resets on every startup."""

from __future__ import annotations

import random
from datetime import datetime, timezone
from decimal import Decimal

from mcp_portfolio.config import Settings
from mcp_portfolio.models import (
    Customer,
    CustomerTier,
    InventoryItem,
    Order,
    OrderItem,
    OrderStatus,
    Product,
    SupportTicket,
    TicketStatus,
)


class MockStore:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._customers: dict[str, Customer] = {}
        self._orders: dict[str, Order] = {}
        self._tickets: dict[str, SupportTicket] = {}
        self._products: dict[str, Product] = {}
        self._inventory: dict[str, InventoryItem] = {}
        self._seed_data()

    def _seed_data(self) -> None:
        rng = random.Random(self._settings.seed)
        now = datetime.now(timezone.utc)

        for i in range(1, self._settings.seed_products + 1):
            pid = f"prd_{i:04d}"
            price = Decimal(str(round(rng.uniform(9.99, 199.99), 2)))
            stock = rng.randint(10, 200)
            self._products[pid] = Product(
                product_id=pid,
                name=f"Product {i}",
                description=f"Description for product {i}",
                category=rng.choice(["Electronics", "Clothing", "Home", "Sports"]),
                price=price,
                stock_quantity=stock,
            )
            self._inventory[pid] = InventoryItem(
                product_id=pid,
                location="warehouse-east",
                quantity=stock,
                reserved=0,
                reorder_threshold=20,
            )

        for i in range(1, self._settings.seed_customers + 1):
            cid = f"cust_{i:04d}"
            self._customers[cid] = Customer(
                customer_id=cid,
                full_name=f"Customer {i}",
                email=f"customer{i}@example.com",
                phone=f"+1-555-{i:04d}",
                address=f"{i} Main St, Anytown",
                tier=rng.choice(list(CustomerTier)),
                created_at=now,
            )

        for i in range(1, self._settings.seed_orders + 1):
            oid = f"ord_{i:04d}"
            cid = f"cust_{rng.randint(1, self._settings.seed_customers):04d}"
            product_ids = [f"prd_{rng.randint(1, self._settings.seed_products):04d}"]
            items = [
                OrderItem(
                    product_id=pid,
                    quantity=rng.randint(1, 5),
                    unit_price=self._products[pid].price,
                )
                for pid in product_ids
            ]
            total = sum(it.quantity * it.unit_price for it in items)
            status = rng.choice(list(OrderStatus))
            self._orders[oid] = Order(
                order_id=oid,
                customer_id=cid,
                items=items,
                total=total,
                status=status,
                version=0,
                created_at=now,
                updated_at=now,
            )

        for i in range(1, self._settings.seed_tickets + 1):
            tid = f"tkt_{i:04d}"
            cid = f"cust_{rng.randint(1, self._settings.seed_customers):04d}"
            oid = f"ord_{rng.randint(1, self._settings.seed_orders):04d}" if rng.random() > 0.3 else None
            self._tickets[tid] = SupportTicket(
                ticket_id=tid,
                customer_id=cid,
                order_id=oid,
                subject=f"Support request {i}",
                description=f"Detailed description for support ticket {i}",
                status=rng.choice(list(TicketStatus)),
                version=0,
                created_at=now,
                updated_at=now,
            )

    async def get_customer(self, customer_id: str) -> Customer | None:
        return self._customers.get(customer_id)

    async def get_customer_orders(self, customer_id: str) -> list[Order]:
        return [o for o in self._orders.values() if o.customer_id == customer_id]

    async def get_customer_tickets(self, customer_id: str) -> list[SupportTicket]:
        return [t for t in self._tickets.values() if t.customer_id == customer_id]

    async def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    async def get_orders_by_status(self, status: str) -> list[Order]:
        return [o for o in self._orders.values() if o.status.value == status]

    async def get_ticket(self, ticket_id: str) -> SupportTicket | None:
        return self._tickets.get(ticket_id)

    async def get_tickets_by_status(self, status: str) -> list[SupportTicket]:
        return [t for t in self._tickets.values() if t.status.value == status]

    async def get_product(self, product_id: str) -> Product | None:
        return self._products.get(product_id)

    async def get_all_products(self) -> list[Product]:
        return list(self._products.values())

    async def get_inventory(self, product_id: str) -> InventoryItem | None:
        return self._inventory.get(product_id)

    async def get_low_stock_inventory(self) -> list[InventoryItem]:
        return [
            inv
            for inv in self._inventory.values()
            if inv.quantity <= inv.reorder_threshold
        ]

    async def create_order(self, order: Order) -> Order:
        self._orders[order.order_id] = order
        return order

    async def update_order(self, order: Order) -> Order:
        self._orders[order.order_id] = order
        return order

    async def create_ticket(self, ticket: SupportTicket) -> SupportTicket:
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    async def update_ticket(self, ticket: SupportTicket) -> SupportTicket:
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    async def update_inventory(self, item: InventoryItem) -> InventoryItem:
        self._inventory[item.product_id] = item
        return item

"""Deterministic seed datasets for the mocked retail backend.

Reference module documenting how seed data is generated.
Mirrors the logic in MockStore._seed_data() for standalone use.
"""

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


class SeedData:
    def __init__(
        self,
        customers: list[Customer],
        products: list[Product],
        orders: list[Order],
        tickets: list[SupportTicket],
        inventory: list[InventoryItem],
    ) -> None:
        self.customers = customers
        self.products = products
        self.orders = orders
        self.tickets = tickets
        self.inventory = inventory


def build_seed(settings: Settings) -> SeedData:
    rng = random.Random(settings.seed)
    now = datetime.now(timezone.utc)

    products: list[Product] = []
    inventory: list[InventoryItem] = []
    for i in range(1, settings.seed_products + 1):
        pid = f"prd_{i:04d}"
        price = Decimal(str(round(rng.uniform(9.99, 199.99), 2)))
        stock = rng.randint(10, 200)
        products.append(
            Product(
                product_id=pid,
                name=f"Product {i}",
                description=f"Description for product {i}",
                category=rng.choice(["Electronics", "Clothing", "Home", "Sports"]),
                price=price,
                stock_quantity=stock,
            )
        )
        inventory.append(
            InventoryItem(
                product_id=pid,
                location="warehouse-east",
                quantity=stock,
                reserved=0,
                reorder_threshold=20,
            )
        )

    customers: list[Customer] = []
    for i in range(1, settings.seed_customers + 1):
        cid = f"cust_{i:04d}"
        customers.append(
            Customer(
                customer_id=cid,
                full_name=f"Customer {i}",
                email=f"customer{i}@example.com",
                phone=f"+1-555-{i:04d}",
                address=f"{i} Main St, Anytown",
                tier=rng.choice(list(CustomerTier)),
                created_at=now,
            )
        )

    orders: list[Order] = []
    for i in range(1, settings.seed_orders + 1):
        oid = f"ord_{i:04d}"
        cid = f"cust_{rng.randint(1, settings.seed_customers):04d}"
        product_ids = [f"prd_{rng.randint(1, settings.seed_products):04d}"]
        items = [
            OrderItem(
                product_id=pid,
                quantity=rng.randint(1, 5),
                unit_price=next(p.price for p in products if p.product_id == pid),
            )
            for pid in product_ids
        ]
        total = sum(it.quantity * it.unit_price for it in items)
        status = rng.choice(list(OrderStatus))
        orders.append(
            Order(
                order_id=oid,
                customer_id=cid,
                items=items,
                total=total,
                status=status,
                version=0,
                created_at=now,
                updated_at=now,
            )
        )

    tickets: list[SupportTicket] = []
    for i in range(1, settings.seed_tickets + 1):
        tid = f"tkt_{i:04d}"
        cid = f"cust_{rng.randint(1, settings.seed_customers):04d}"
        oid = f"ord_{rng.randint(1, settings.seed_orders):04d}" if rng.random() > 0.3 else None
        tickets.append(
            SupportTicket(
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
        )

    return SeedData(
        customers=customers,
        products=products,
        orders=orders,
        tickets=tickets,
        inventory=inventory,
    )

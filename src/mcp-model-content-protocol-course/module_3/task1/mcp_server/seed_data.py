"""Deterministic seed datasets for the mocked backend."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from mcp_server.config import Settings
from mcp_server.models import (
    Customer,
    CustomerTier,
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
    ) -> None:
        self.customers = customers
        self.products = products
        self.orders = orders
        self.tickets = tickets


def build_seed(settings: Settings) -> SeedData:
    rng = random.Random(settings.seed)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    tiers = list(CustomerTier)

    customers = [
        Customer(
            customer_id=f"cust_{1001 + i}",
            full_name=f"Customer {1001 + i}",
            email=f"customer{1001 + i}@example.com",
            phone=f"+1-555-010{i % 10}{i % 7}",
            tier=tiers[i % len(tiers)],
            created_at=base + timedelta(days=i),
        )
        for i in range(settings.seed_customers)
    ]

    products = [
        Product(
            product_id=f"prd_{4001 + i}",
            name=f"Product {4001 + i}",
            category=rng.choice(["electronics", "home", "apparel"]),
            price=round(rng.uniform(5, 500), 2),
            in_stock=rng.random() > 0.15,
        )
        for i in range(settings.seed_products)
    ]

    statuses = list(OrderStatus)
    orders: list[Order] = []
    for i in range(settings.seed_orders):
        customer = customers[i % len(customers)]
        chosen = rng.sample(products, k=min(3, len(products)))
        items = [
            OrderItem(
                product_id=p.product_id, quantity=rng.randint(1, 4), unit_price=p.price
            )
            for p in chosen
        ]
        total = sum(it.quantity * it.unit_price for it in items)
        orders.append(
            Order(
                order_id=f"ord_{2001 + i}",
                customer_id=customer.customer_id,
                items=items,
                total=total,
                status=statuses[i % len(statuses)],
                updated_at=base + timedelta(days=i, hours=2),
            )
        )

    ticket_statuses = list(TicketStatus)
    tickets = [
        SupportTicket(
            ticket_id=f"tkt_{3001 + i}",
            customer_id=customers[i % len(customers)].customer_id,
            order_id=orders[i % len(orders)].order_id if i % 3 == 0 else None,
            subject=f"Support request {3001 + i} about delivery",
            description=f"Description of issue {3001 + i} filed by customer.",
            status=ticket_statuses[i % len(ticket_statuses)],
            created_at=base + timedelta(days=i, hours=4),
            updated_at=base + timedelta(days=i, hours=5),
        )
        for i in range(settings.seed_tickets)
    ]
    return SeedData(
        customers=customers, products=products, orders=orders, tickets=tickets
    )

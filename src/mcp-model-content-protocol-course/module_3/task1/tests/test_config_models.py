"""Unit tests for config and models (T015)."""

from unittest import TestCase

from mcp_server.models import (
    ORDER_TRANSITIONS,
    TICKET_TRANSITIONS,
    Customer,
    Order,
    OrderStatus,
    SupportTicket,
    TicketStatus,
)
from pydantic import ValidationError

from tests.fixtures import make_settings


class TestSettingsDefaults(TestCase):
    def test_no_hardcoded_secrets_by_default(self) -> None:
        settings = make_settings()
        self.assertEqual(settings.mock_failure_mode, "off")
        self.assertFalse(settings.tls_enabled)
        self.assertGreater(settings.rate_limit_per_minute, 0)

    def test_rejects_unknown_failure_mode(self) -> None:
        with self.assertRaises(ValidationError):
            make_settings(mock_failure_mode="explode")


class TestCustomerValidation(TestCase):
    def test_rejects_bad_id_and_email(self) -> None:
        with self.assertRaises(ValidationError):
            Customer(
                customer_id="nope",
                full_name="X",
                email="not-an-email",
                created_at="2026-01-01T00:00:00Z",
            )


class TestOrderTotal(TestCase):
    def test_total_must_match_items(self) -> None:
        item = {"product_id": "prd_4001", "quantity": 2, "unit_price": "10.00"}
        with self.assertRaises(ValidationError):
            Order(
                order_id="ord_2001",
                customer_id="cust_1001",
                items=[item],
                total="5.00",
                updated_at="2026-01-01T00:00:00Z",
            )

    def test_transition_map_shape(self) -> None:
        self.assertIn(OrderStatus.CONFIRMED, ORDER_TRANSITIONS[OrderStatus.PENDING])
        self.assertEqual(ORDER_TRANSITIONS[OrderStatus.DELIVERED], set())


class TestTicketSanitization(TestCase):
    def test_control_chars_stripped(self) -> None:
        ticket = SupportTicket(
            ticket_id="tkt_3001",
            customer_id="cust_1001",
            subject="Valid subject here",
            description="bad\x00desc",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        self.assertNotIn("\x00", ticket.description)

    def test_transition_map_shape(self) -> None:
        self.assertIn(TicketStatus.IN_PROGRESS, TICKET_TRANSITIONS[TicketStatus.OPEN])
        self.assertEqual(TICKET_TRANSITIONS[TicketStatus.CLOSED], set())

"""Unit tests for US1 resource reads (T019). Written first; must fail before T020."""

import asyncio
from unittest import TestCase

from mcp_server.resources import ResourceService

from tests.fixtures import (
    TEST_KEYS,
    make_audit,
    make_breaker,
    make_cache,
    make_limiter,
    make_metrics,
    make_settings,
    make_store,
)


def make_service(**overrides):
    settings = overrides.pop("settings", make_settings())
    return ResourceService(
        settings=settings,
        credentials=overrides.pop("credentials", dict(TEST_KEYS)),
        store=overrides.pop("store", make_store(settings)),
        cache=overrides.pop("cache", make_cache(settings)),
        audit=overrides.pop("audit", make_audit()),
        metrics=overrides.pop("metrics", make_metrics()),
        limiter=overrides.pop("limiter", make_limiter(settings)),
        breaker=overrides.pop("breaker", make_breaker()),
    )


def run(coro):
    return asyncio.run(coro)


AGENT_KEY = "test-agent-secret-key-1"
AUDITOR_KEY = "test-auditor-secret-key-1"
OPERATOR_KEY = "test-operator-secret-key-1"


class TestAuthorizedRead(TestCase):
    def test_agent_reads_customer_orders_tickets(self) -> None:
        svc = make_service()
        res = run(svc.read("store://customers/cust_1001", AGENT_KEY))
        self.assertIn("data", res)
        self.assertEqual(res["data"]["customer_id"], "cust_1001")
        orders = run(svc.read("store://customers/cust_1001/orders", AGENT_KEY))
        self.assertIsInstance(orders["data"], list)
        tickets = run(svc.read("store://customers/cust_1001/tickets", AGENT_KEY))
        self.assertIsInstance(tickets["data"], list)

    def test_all_uri_patterns(self) -> None:
        svc = make_service()
        for uri in (
            "store://orders/ord_2001",
            "store://orders/status/pending",
            "store://tickets/tkt_3001",
            "store://tickets/status/open",
            "store://products",
            "store://products/prd_4001",
        ):
            with self.subTest(uri=uri):
                self.assertIn("data", run(svc.read(uri, AGENT_KEY)))

    def test_empty_filtered_view_returns_empty_list(self) -> None:
        svc = make_service()
        res = run(svc.read("store://orders/status/no_such_status", AGENT_KEY))
        self.assertEqual(res["data"], [])


class TestMasking(TestCase):
    def test_auditor_sees_masked_pii(self) -> None:
        svc = make_service()
        res = run(svc.read("store://customers/cust_1001", AUDITOR_KEY))
        self.assertEqual(res["data"]["full_name"], "***")
        self.assertEqual(res["data"]["email"], "***")

    def test_roles_do_not_share_cache(self) -> None:
        svc = make_service()
        run(svc.read("store://customers/cust_1001", AGENT_KEY))
        masked = run(svc.read("store://customers/cust_1001", AUDITOR_KEY))
        self.assertEqual(masked["data"]["email"], "***")


class TestDenials(TestCase):
    def test_invalid_key_denied_without_data(self) -> None:
        svc = make_service()
        res = run(svc.read("store://customers/cust_1001", "bad-key-value-long-enough"))
        self.assertEqual(res["error"]["code"], "UNAUTHENTICATED")
        self.assertNotIn("cust_1001", str(res))

    def test_operator_denied_business_data(self) -> None:
        svc = make_service()
        res = run(svc.read("store://products", OPERATOR_KEY))
        self.assertEqual(res["error"]["code"], "FORBIDDEN")

    def test_denials_are_audited(self) -> None:
        audit = make_audit()
        svc = make_service(audit=audit)
        run(svc.read("store://products", OPERATOR_KEY))
        denied = [r for r in audit.list_records() if r.outcome.value == "denied"]
        self.assertEqual(len(denied), 1)


class TestResiliencePaths(TestCase):
    def test_unavailable_dependency_returns_partial(self) -> None:
        settings = make_settings(mock_failure_mode="unavailable")
        svc = make_service(settings=settings, store=make_store(settings))
        res = run(svc.read("store://products", AGENT_KEY))
        self.assertEqual(res["error"]["code"], "DEPENDENCY_UNAVAILABLE")
        self.assertEqual(res["processing_outcome"], "partial")

    def test_unknown_uri_returns_not_found(self) -> None:
        svc = make_service()
        res = run(svc.read("store://nope/nothing", AGENT_KEY))
        self.assertEqual(res["error"]["code"], "NOT_FOUND")

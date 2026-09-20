"""Convergence tests for Phase 8 (T044-T048): one TestCase per subject."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest import TestCase

from mcp_server.auth import Unauthenticated, authenticate
from mcp_server.models import ApiCredential, OrderStatus, Role
from mcp_server.ops_app import OpsDeps, get_health
from mcp_server.resources import ResourceService
from mcp_server.tools import ToolService

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


def run(coro):
    return asyncio.run(coro)


def make_services(**overrides):
    settings = overrides.pop("settings", make_settings())
    store = overrides.pop("store", make_store(settings))
    audit = overrides.pop("audit", make_audit())
    metrics = overrides.pop("metrics", make_metrics())
    resources = ResourceService(
        settings,
        dict(TEST_KEYS),
        store,
        make_cache(settings),
        audit,
        metrics,
        make_limiter(settings),
        make_breaker(),
    )
    tools = ToolService(
        settings, dict(TEST_KEYS), store, audit, metrics, make_limiter(settings)
    )
    return settings, store, audit, metrics, resources, tools


AGENT_KEY = "test-agent-secret-key-1"
ADMIN_KEY = "test-admin-secret-key-1"


class TestGetTaskToolRegistered(TestCase):
    def test_get_task_status_listed(self) -> None:
        from mcp_server.server import build_server

        server = build_server(make_settings(), ADMIN_KEY)
        names = {t.name for t in run(server.list_tools())}
        self.assertIn("get_task_status", names)


class TestOrderConflict(TestCase):
    def test_stale_version_returns_conflict(self) -> None:
        _, store, _, _, _, tools = make_services()
        pending = next(
            o.order_id for o in store.orders.values() if o.status == OrderStatus.PENDING
        )
        res = run(
            tools.update_order(
                AGENT_KEY,
                {
                    "order_id": pending,
                    "new_status": "confirmed",
                    "expected_version": 999,
                },
            )
        )
        self.assertEqual(res["error"]["code"], "CONFLICT")
        self.assertIn("version", res["current"])

    def test_concurrent_writers_one_conflicts(self) -> None:
        _, store, _, _, _, tools = make_services()
        pending = next(
            o.order_id for o in store.orders.values() if o.status == OrderStatus.PENDING
        )

        async def race() -> list:
            gate = asyncio.Event()

            async def writer() -> dict:
                await gate.wait()
                return await tools.update_order(
                    AGENT_KEY,
                    {
                        "order_id": pending,
                        "new_status": "confirmed",
                        "expected_version": 0,
                    },
                )

            first = asyncio.create_task(writer())
            second = asyncio.create_task(writer())
            gate.set()
            return [await first, await second]

        results = run(race())
        codes = sorted(r.get("error", {}).get("code", "ok") for r in results)
        self.assertEqual(codes, ["CONFLICT", "ok"])


class TestTicketConflict(TestCase):
    def test_stale_version_returns_conflict(self) -> None:
        _, store, _, _, _, tools = make_services()
        ticket_id = next(iter(store.tickets))
        res = run(
            tools.update_ticket_status(
                AGENT_KEY,
                {
                    "ticket_id": ticket_id,
                    "new_status": "closed",
                    "expected_version": 999,
                },
            )
        )
        self.assertEqual(res["error"]["code"], "CONFLICT")


class TestAlertHook(TestCase):
    def test_hook_fires_on_degraded(self) -> None:
        import time

        from mcp_server.store import MockStore

        settings = make_settings()
        fired: list = []
        breaker = make_breaker()
        deps = OpsDeps(
            settings=settings,
            credentials=dict(TEST_KEYS),
            store=MockStore(settings),
            audit=make_audit(),
            metrics=make_metrics(),
            breaker=breaker,
            started_at=time.monotonic(),
            alert_hooks=[fired.append],
        )
        self.assertEqual(get_health(deps)["status"], "healthy")
        self.assertEqual(fired, [])
        for _ in range(3):
            breaker.before_call()
            breaker.after_call(False)
        report = get_health(deps)
        self.assertEqual(report["status"], "degraded")
        self.assertEqual(len(fired), 1)
        self.assertEqual(fired[0]["status"], "degraded")


class TestKeyExpiry(TestCase):
    def test_expired_key_denied(self) -> None:
        creds = dict(TEST_KEYS)
        creds["old-1"] = ApiCredential(
            key_id="old-1",
            api_key="expired-secret-key-0001",
            role=Role.ADMIN,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        with self.assertRaises(Unauthenticated):
            authenticate(creds, "expired-secret-key-0001")

    def test_future_expiry_allowed(self) -> None:
        creds = dict(TEST_KEYS)
        creds["new-1"] = ApiCredential(
            key_id="new-1",
            api_key="future-secret-key-00001",
            role=Role.ADMIN,
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        ctx = authenticate(creds, "future-secret-key-00001")
        self.assertEqual(ctx.role, Role.ADMIN)


class TestErrorRecordType(TestCase):
    def test_error_entry_has_typed_fields(self) -> None:
        metrics = make_metrics()
        metrics.record_error(
            "resource.read", "NotFound", "gone", "2026-01-01T00:00:00Z"
        )
        entry = metrics.errors[0]
        self.assertEqual(
            set(entry.keys()), {"step", "error_type", "message", "timestamp"}
        )

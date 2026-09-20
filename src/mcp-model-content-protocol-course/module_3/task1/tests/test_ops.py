"""Unit tests for US3 ops surface (T029). Written first; must fail before T030."""

import time
from unittest import TestCase

from mcp_server.auth import Forbidden
from mcp_server.models import Role
from mcp_server.ops_app import (
    OpsDeps,
    create_ops_app,
    get_health,
    get_metrics,
    render_dashboard,
)

from tests.fixtures import (
    TEST_KEYS,
    make_audit,
    make_breaker,
    make_ctx,
    make_metrics,
    make_settings,
    make_store,
)


def make_deps(**overrides):
    settings = overrides.pop("settings", make_settings())
    return OpsDeps(
        settings=settings,
        credentials=dict(TEST_KEYS),
        store=overrides.pop("store", make_store(settings)),
        audit=overrides.pop("audit", make_audit()),
        metrics=overrides.pop("metrics", make_metrics()),
        breaker=overrides.pop("breaker", make_breaker()),
        started_at=time.monotonic(),
    )


class TestHealth(TestCase):
    def test_healthy_by_default(self) -> None:
        health = get_health(make_deps())
        self.assertEqual(health["status"], "healthy")
        self.assertIn("version", health)
        self.assertGreaterEqual(health["uptime_seconds"], 0)

    def test_degraded_when_circuit_open(self) -> None:
        deps = make_deps()
        deps.breaker.before_call()
        deps.breaker.after_call(False)
        deps.breaker.before_call()
        deps.breaker.after_call(False)
        deps.breaker.before_call()
        deps.breaker.after_call(False)
        self.assertEqual(get_health(deps)["status"], "degraded")

    def test_unhealthy_when_audit_broken(self) -> None:
        deps = make_deps()
        deps.audit.broken = True
        self.assertEqual(get_health(deps)["status"], "unhealthy")


class TestMetricsAccess(TestCase):
    def test_operator_reads_metrics(self) -> None:
        deps = make_deps()
        deps.metrics.record("resource.read", "success", 3.0)
        snap = get_metrics(deps, make_ctx(Role.OPERATOR))
        self.assertIn("requests_total", snap)
        self.assertIn("circuit_states", snap)

    def test_agent_denied_metrics(self) -> None:
        with self.assertRaises(Forbidden):
            get_metrics(make_deps(), make_ctx(Role.SUPPORT_AGENT))


class TestDashboard(TestCase):
    def test_no_pii_rendered(self) -> None:
        deps = make_deps()
        deps.metrics.record_error(
            "resource.read", "NotFound", "x", "2026-01-01T00:00:00Z"
        )
        html = render_dashboard(deps, make_ctx(Role.OPERATOR))
        self.assertIn("Status:", html)
        self.assertNotIn("customer", html.lower().replace("customers", ""))
        self.assertNotIn("@example.com", html)


class TestAppWiring(TestCase):
    def test_routes_registered(self) -> None:
        app = create_ops_app(make_deps())
        paths = {route.path for route in app.routes}
        self.assertTrue({"/health", "/metrics", "/dashboard"} <= paths)

    def test_tls_settings_surface(self) -> None:
        settings = make_settings(tls_enabled=True, tls_cert_path="c", tls_key_path="k")
        self.assertTrue(settings.tls_enabled)
        self.assertEqual(settings.tls_cert_path, "c")

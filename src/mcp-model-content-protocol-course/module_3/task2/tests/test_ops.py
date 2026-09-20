"""Unit tests for ops endpoints (health, metrics, dashboard)."""

from __future__ import annotations

import time
import unittest

from mcp_portfolio.audit import AuditLog
from mcp_portfolio.auth import AuthContext, Unauthenticated, authenticate
from mcp_portfolio.config import Settings
from mcp_portfolio.metrics import MetricsRegistry
from mcp_portfolio.models import ApiCredential, Role
from mcp_portfolio.ops_app import OpsDeps, get_health, get_metrics, render_dashboard
from mcp_portfolio.resilience import CircuitBreaker

from .fixtures import ADMIN_KEY, OPERATOR_KEY, AUDITOR_KEY, make_settings


def _make_deps(**overrides) -> OpsDeps:
    settings = make_settings(**overrides)
    audit = AuditLog()
    metrics = MetricsRegistry()
    breaker = CircuitBreaker()
    return OpsDeps(
        settings=settings,
        credentials=settings.api_keys,
        audit=audit,
        metrics=metrics,
        breaker=breaker,
        started_at=time.monotonic(),
        alert_hooks=[],
    )


class TestGetHealth(unittest.TestCase):
    def test_health_healthy(self) -> None:
        deps = _make_deps()
        report = get_health(deps)
        self.assertEqual(report["status"], "healthy")
        self.assertIn("uptime_seconds", report)
        self.assertIn("dependencies", report)
        self.assertEqual(report["dependencies"]["audit_sink"], "ok")
        self.assertEqual(report["dependencies"]["mock_store"], "closed")
        self.assertEqual(report["version"], "0.1.0")

    def test_health_degraded(self) -> None:
        deps = _make_deps()
        deps.breaker.state = "open"
        report = get_health(deps)
        self.assertEqual(report["status"], "degraded")

    def test_health_degraded_high_error_rate(self) -> None:
        deps = _make_deps()
        for i in range(15):
            deps.metrics.record("test", "success", 10.0)
        for i in range(5):
            deps.metrics.record("test", "failed", 10.0)
        report = get_health(deps)
        self.assertEqual(report["status"], "degraded")

    def test_health_unhealthy_audit_broken(self) -> None:
        deps = _make_deps()
        deps.audit.broken = True
        report = get_health(deps)
        self.assertEqual(report["status"], "unhealthy")

    def test_health_triggers_alert_hooks(self) -> None:
        alerts: list[dict] = []
        deps = _make_deps()
        deps.alert_hooks.append(lambda r: alerts.append(r))
        deps.breaker.state = "open"
        get_health(deps)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["status"], "degraded")


class TestGetMetrics(unittest.TestCase):
    def test_get_metrics_authorized(self) -> None:
        deps = _make_deps()
        ctx = AuthContext(key_id="admin-1", role=Role.ADMIN)
        result = get_metrics(deps, ctx)
        self.assertIn("requests_count", result)
        self.assertIn("latency_ms", result)
        self.assertIn("error_rate", result)
        self.assertIn("circuit_states", result)

    def test_get_metrics_authorized_operator(self) -> None:
        deps = _make_deps()
        ctx = AuthContext(key_id="operator-1", role=Role.OPERATOR)
        result = get_metrics(deps, ctx)
        self.assertIn("requests_count", result)

    def test_get_metrics_unauthorized(self) -> None:
        from mcp_portfolio.auth import Forbidden

        deps = _make_deps()
        ctx = AuthContext(key_id="auditor-1", role=Role.AUDITOR)
        with self.assertRaises(Forbidden):
            get_metrics(deps, ctx)


class TestRenderDashboard(unittest.TestCase):
    def test_dashboard_authorized(self) -> None:
        deps = _make_deps()
        ctx = AuthContext(key_id="admin-1", role=Role.ADMIN)
        html = render_dashboard(deps, ctx)
        self.assertIn("<html>", html)
        self.assertIn("MCP Portfolio Dashboard", html)
        self.assertIn("Status:", html)

    def test_dashboard_unauthorized(self) -> None:
        from mcp_portfolio.auth import Forbidden

        deps = _make_deps()
        ctx = AuthContext(key_id="auditor-1", role=Role.AUDITOR)
        with self.assertRaises(Forbidden):
            render_dashboard(deps, ctx)


if __name__ == "__main__":
    unittest.main()

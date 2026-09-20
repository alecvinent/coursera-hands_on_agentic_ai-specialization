"""Shared test helpers and fixtures."""

from __future__ import annotations

from mcp_portfolio.config import Settings
from mcp_portfolio.models import ApiCredential, Role
from mcp_portfolio.store import MockStore


ADMIN_KEY = "test-admin-key-12345678"
SUPPORT_KEY = "test-support-key-1234567"
AUDITOR_KEY = "test-auditor-key-123456"
OPERATOR_KEY = "test-operator-key-1234"


def make_settings(**overrides) -> Settings:
    defaults = {
        "api_keys": {
            "admin-1": ApiCredential(
                key_id="admin-1", api_key=ADMIN_KEY, role=Role.ADMIN
            ),
            "support-1": ApiCredential(
                key_id="support-1", api_key=SUPPORT_KEY, role=Role.SUPPORT_AGENT
            ),
            "auditor-1": ApiCredential(
                key_id="auditor-1", api_key=AUDITOR_KEY, role=Role.AUDITOR
            ),
            "operator-1": ApiCredential(
                key_id="operator-1", api_key=OPERATOR_KEY, role=Role.OPERATOR
            ),
        },
        "cache_ttl_seconds": 0,
        "rate_limit_per_minute": 1000,
        "rate_limit_burst": 100,
    }
    defaults.update(overrides)
    return Settings(**defaults)


def make_store(settings: Settings | None = None) -> MockStore:
    return MockStore(settings or make_settings())

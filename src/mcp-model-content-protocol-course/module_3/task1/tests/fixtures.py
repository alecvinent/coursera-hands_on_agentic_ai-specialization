"""Shared fixtures for the colocated MCP server test suite."""

from __future__ import annotations

from mcp_server.audit import AuditLog
from mcp_server.auth import AuthContext
from mcp_server.cache import TTLCache
from mcp_server.config import Settings
from mcp_server.metrics import MetricsRegistry
from mcp_server.models import ApiCredential, Role
from mcp_server.ratelimit import RateLimiter
from mcp_server.resilience import CircuitBreaker
from mcp_server.store import MockStore

TEST_KEYS: dict[str, ApiCredential] = {
    "admin-1": ApiCredential(
        key_id="admin-1", api_key="test-admin-secret-key-1", role=Role.ADMIN
    ),
    "agent-1": ApiCredential(
        key_id="agent-1", api_key="test-agent-secret-key-1", role=Role.SUPPORT_AGENT
    ),
    "audit-1": ApiCredential(
        key_id="audit-1", api_key="test-auditor-secret-key-1", role=Role.AUDITOR
    ),
    "ops-1": ApiCredential(
        key_id="ops-1", api_key="test-operator-secret-key-1", role=Role.OPERATOR
    ),
}


def make_settings(**overrides: object) -> Settings:
    return Settings(api_keys=dict(TEST_KEYS), **overrides)  # type: ignore[arg-type]


def make_ctx(role: Role) -> AuthContext:
    key_id = next(k for k, c in TEST_KEYS.items() if c.role == role)
    return AuthContext(key_id=key_id, role=role)


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def make_store(settings: Settings | None = None) -> MockStore:
    return MockStore(settings or make_settings())


def make_cache(settings: Settings | None = None) -> TTLCache:
    settings = settings or make_settings()
    return TTLCache(ttl_seconds=settings.cache_ttl_seconds)


def make_limiter(settings: Settings | None = None) -> RateLimiter:
    settings = settings or make_settings()
    return RateLimiter(
        per_minute=settings.rate_limit_per_minute, burst=settings.rate_limit_burst
    )


def make_breaker() -> CircuitBreaker:
    return CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)


def make_audit() -> AuditLog:
    return AuditLog()


def make_metrics() -> MetricsRegistry:
    return MetricsRegistry()

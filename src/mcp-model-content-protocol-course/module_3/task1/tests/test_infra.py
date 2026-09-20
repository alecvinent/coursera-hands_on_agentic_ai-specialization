"""Unit tests for cache, rate limiter, resilience, metrics (T018)."""

import asyncio
from unittest import TestCase

from mcp_server.cache import TTLCache, make_key
from mcp_server.models import Role
from mcp_server.ratelimit import RateLimiter
from mcp_server.resilience import (
    CircuitBreaker,
    CircuitOpen,
    ToolTimeout,
    retry_transient,
    with_timeout,
)

from tests.fixtures import FakeClock, make_metrics


class TestRoleScopedCache(TestCase):
    def test_roles_do_not_share_entries(self) -> None:
        cache = TTLCache(ttl_seconds=60)
        cache.set(make_key(Role.ADMIN, "store://customers/cust_1001"), {"full": True})
        self.assertIsNone(
            cache.get(make_key(Role.AUDITOR, "store://customers/cust_1001"))
        )
        self.assertEqual(cache.stats.misses, 1)

    def test_expired_entry_misses(self) -> None:
        clock = FakeClock()
        cache = TTLCache(ttl_seconds=10, clock=clock)
        cache.set(make_key(Role.ADMIN, "u"), 1)
        clock.advance(11)
        self.assertIsNone(cache.get(make_key(Role.ADMIN, "u")))


class TestRateLimiter(TestCase):
    def test_burst_then_throttle_with_retry_hint(self) -> None:
        clock = FakeClock()
        limiter = RateLimiter(per_minute=60, burst=2, clock=clock)
        self.assertTrue(limiter.allow("k")[0])
        self.assertTrue(limiter.allow("k")[0])
        allowed, retry_ms = limiter.allow("k")
        self.assertFalse(allowed)
        self.assertGreater(retry_ms, 0)

    def test_other_keys_unaffected(self) -> None:
        clock = FakeClock()
        limiter = RateLimiter(per_minute=60, burst=1, clock=clock)
        limiter.allow("a")
        self.assertTrue(limiter.allow("b")[0])

    def test_refill_over_time(self) -> None:
        clock = FakeClock()
        limiter = RateLimiter(per_minute=60, burst=1, clock=clock)
        limiter.allow("k")
        clock.advance(61)
        self.assertTrue(limiter.allow("k")[0])


class TestCircuitBreaker(TestCase):
    def test_opens_after_threshold_and_recovers(self) -> None:
        clock = FakeClock()
        breaker = CircuitBreaker(
            failure_threshold=2, recovery_timeout=30.0, clock=clock
        )
        breaker.before_call()
        breaker.after_call(False)
        breaker.before_call()
        breaker.after_call(False)
        with self.assertRaises(CircuitOpen):
            breaker.before_call()
        clock.advance(31)
        breaker.before_call()
        self.assertEqual(breaker.state, "half-open")
        breaker.after_call(True)
        self.assertEqual(breaker.state, "closed")


class TestTimeoutAndRetry(TestCase):
    def test_timeout_raises(self) -> None:
        async def slow():
            await asyncio.sleep(5)

        with self.assertRaises(ToolTimeout):
            asyncio.run(with_timeout(slow(), 0.01))

    def test_retry_succeeds_after_transient(self) -> None:
        calls = {"n": 0}

        async def flaky():
            calls["n"] += 1
            if calls["n"] < 3:
                raise ConnectionError("boom")
            return "ok"

        self.assertEqual(asyncio.run(retry_transient(flaky, base_delay=0)), "ok")


class TestMetrics(TestCase):
    def test_snapshot_and_error_rate(self) -> None:
        metrics = make_metrics()
        metrics.record("resource.read", "success", 4.0)
        metrics.record("tool.execute", "denied", 2.0)
        snap = metrics.snapshot()
        self.assertEqual(snap["requests_count"], 2)
        self.assertAlmostEqual(snap["error_rate"], 0.5)
        self.assertGreaterEqual(snap["latency_ms"]["p95"], snap["latency_ms"]["p50"])

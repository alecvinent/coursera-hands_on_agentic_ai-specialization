"""Resilience primitives: timeouts, circuit breaker, backoff retry."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")


class ToolTimeout(Exception):
    pass


class CircuitOpen(Exception):
    pass


async def with_timeout(coro: Awaitable[T], seconds: float) -> T:
    try:
        return await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        raise ToolTimeout(f"operation exceeded {seconds}s") from None


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._clock = clock or time.monotonic
        self.state = "closed"
        self._failures = 0
        self._opened_at = 0.0

    def before_call(self) -> None:
        if self.state == "open":
            if self._clock() - self._opened_at >= self._recovery_timeout:
                self.state = "half-open"
            else:
                raise CircuitOpen("circuit is open")
        if self.state == "half-open":
            pass

    def after_call(self, success: bool) -> None:
        if success:
            self._failures = 0
            self.state = "closed"
        else:
            self._failures += 1
            if self.state == "half-open" or self._failures >= self._threshold:
                self.state = "open"
                self._opened_at = self._clock()


async def retry_transient(
    fn: Callable[[], Awaitable[T]],
    attempts: int = 3,
    base_delay: float = 0.05,
    retryable: tuple[type[Exception], ...] = (ConnectionError, TimeoutError),
) -> T:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return await fn()
        except retryable as exc:
            last = exc
            await asyncio.sleep(base_delay * (2**attempt))
    raise last  # type: ignore[misc]

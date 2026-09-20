"""Per-key token-bucket rate limiter with injectable clock."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class _Bucket:
    tokens: float
    updated_at: float


class RateLimiter:
    def __init__(
        self,
        per_minute: int,
        burst: int,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._rate_per_sec = per_minute / 60.0
        self._burst = burst
        self._clock = clock or time.monotonic
        self._buckets: dict[str, _Bucket] = {}
        self.limited_total = 0

    def allow(self, key: str) -> tuple[bool, int]:
        now = self._clock()
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = _Bucket(tokens=float(self._burst), updated_at=now)
            self._buckets[key] = bucket
        elapsed = now - bucket.updated_at
        bucket.tokens = min(
            float(self._burst), bucket.tokens + elapsed * self._rate_per_sec
        )
        bucket.updated_at = now
        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            return True, 0
        self.limited_total += 1
        retry_ms = int((1.0 - bucket.tokens) / self._rate_per_sec * 1000)
        return False, max(retry_ms, 1)

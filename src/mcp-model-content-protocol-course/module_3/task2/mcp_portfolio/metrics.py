"""In-memory metrics registry: counters, latencies, error tracking."""

from __future__ import annotations

import statistics
from collections import deque

from mcp_portfolio.models import ErrorRecord


class MetricsRegistry:
    def __init__(self, max_samples: int = 1000) -> None:
        self.counters: dict[str, int] = {}
        self._latencies: deque[float] = deque(maxlen=max_samples)
        self.rate_limited_total = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors: list[ErrorRecord] = []

    def record(self, endpoint: str, outcome: str, latency_ms: float) -> None:
        key = f"{endpoint}:{outcome}"
        self.counters[key] = self.counters.get(key, 0) + 1
        self._latencies.append(latency_ms)

    def record_rate_limited(self) -> None:
        self.rate_limited_total += 1

    def record_cache(self, hit: bool) -> None:
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def record_error(
        self, step: str, error_type: str, message: str, timestamp: str
    ) -> None:
        entry: ErrorRecord = {
            "step": step,
            "error_type": error_type,
            "message": message,
            "timestamp": timestamp,
        }
        self.errors.append(entry)

    def _percentile(self, pct: float) -> float:
        if not self._latencies:
            return 0.0
        ordered = sorted(self._latencies)
        index = min(len(ordered) - 1, int(len(ordered) * pct / 100))
        return ordered[index]

    def error_rate(self) -> float:
        total = sum(self.counters.values())
        if total == 0:
            return 0.0
        failed = sum(
            v for k, v in self.counters.items() if k.endswith((":failed", ":denied"))
        )
        return failed / total

    def snapshot(self) -> dict:
        total = sum(self.counters.values())
        samples = list(self._latencies)
        return {
            "requests_total": dict(self.counters),
            "requests_count": total,
            "latency_ms": {
                "p50": self._percentile(50),
                "p95": self._percentile(95),
                "mean": statistics.fmean(samples) if samples else 0.0,
            },
            "error_rate": self.error_rate(),
            "rate_limited_total": self.rate_limited_total,
            "cache": {"hits": self.cache_hits, "misses": self.cache_misses},
        }

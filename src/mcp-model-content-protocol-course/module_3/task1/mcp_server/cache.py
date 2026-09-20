"""In-memory TTL cache with role-scoped keys.

Keys always incorporate the caller role so masked and full
representations are never shared across roles.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from mcp_server.models import Role


def make_key(role: Role, uri: str, query_hash: str = "") -> str:
    return f"{role.value}|{uri}|{query_hash}"


@dataclass
class _Entry:
    value: object
    expires_at: float


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0


class TTLCache:
    def __init__(
        self, ttl_seconds: int, clock: Callable[[], float] | None = None
    ) -> None:
        self._ttl = ttl_seconds
        self._clock = clock or time.monotonic
        self._entries: dict[str, _Entry] = {}
        self.stats = CacheStats()

    def get(self, key: str) -> object | None:
        entry = self._entries.get(key)
        if entry is None or entry.expires_at <= self._clock():
            self._entries.pop(key, None)
            self.stats.misses += 1
            return None
        self.stats.hits += 1
        return entry.value

    def set(self, key: str, value: object) -> None:
        self._entries[key] = _Entry(value=value, expires_at=self._clock() + self._ttl)

    def invalidate(self, key: str) -> None:
        self._entries.pop(key, None)

"""TTL cache with role-scoped keys."""

from __future__ import annotations

import time
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: int = 60) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def _key(self, role: str, uri: str, query: str = "") -> str:
        return f"{role}:{uri}:{query}"

    def get(self, role: str, uri: str, query: str = "") -> Any | None:
        key = self._key(role, uri, query)
        if key in self._store:
            ts, value = self._store[key]
            if time.monotonic() - ts < self._ttl:
                return value
            del self._store[key]
        return None

    def set(self, role: str, uri: str, value: Any, query: str = "") -> None:
        key = self._key(role, uri, query)
        self._store[key] = (time.monotonic(), value)

    def invalidate(self, role: str, uri: str, query: str = "") -> None:
        key = self._key(role, uri, query)
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

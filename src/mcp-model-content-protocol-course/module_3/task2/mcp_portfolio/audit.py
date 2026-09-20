"""Append-only audit log with fail-closed semantics."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from mcp_portfolio.auth import AuthContext
from mcp_portfolio.models import AuditRecord, Outcome


class AuditUnavailable(Exception):
    pass


def hash_inputs(inputs: dict) -> str:
    canonical = json.dumps(inputs, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self) -> None:
        self._records: list[AuditRecord] = []
        self.broken = False

    def record(
        self,
        ctx: AuthContext | None,
        action: str,
        resource_type: str,
        outcome: Outcome,
        inputs: dict | None = None,
        latency_ms: float = 0.0,
    ) -> AuditRecord:
        if self.broken:
            raise AuditUnavailable("audit sink unavailable")
        entry = AuditRecord(
            seq=len(self._records),
            timestamp=datetime.now(timezone.utc),
            key_id=ctx.key_id if ctx else "anonymous",
            role=ctx.role.value if ctx else "none",
            action=action,
            resource_type=resource_type,
            inputs_hash=hash_inputs(inputs) if inputs is not None else None,
            outcome=outcome,
            latency_ms=latency_ms,
        )
        self._records.append(entry)
        return entry

    def list_records(self) -> list[AuditRecord]:
        return list(self._records)

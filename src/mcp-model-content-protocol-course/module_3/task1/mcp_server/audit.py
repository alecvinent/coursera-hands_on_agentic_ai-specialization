"""Append-only audit log with fail-closed semantics."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from mcp_server.auth import AuthContext
from mcp_server.models import AuditRecord, Outcome


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
        target: str,
        outcome: Outcome,
        inputs: dict | None = None,
    ) -> AuditRecord:
        if self.broken:
            raise AuditUnavailable("audit sink unavailable")
        entry = AuditRecord(
            seq=len(self._records),
            timestamp=datetime.now(timezone.utc),
            key_id=ctx.key_id if ctx else "anonymous",
            role=ctx.role.value if ctx else "none",
            action=action,
            target=target,
            inputs_hash=hash_inputs(inputs) if inputs is not None else None,
            outcome=outcome,
        )
        self._records.append(entry)
        return entry

    def list_records(self) -> list[AuditRecord]:
        return list(self._records)

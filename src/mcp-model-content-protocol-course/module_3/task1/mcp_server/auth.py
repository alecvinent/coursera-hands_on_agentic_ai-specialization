"""API-key authentication and role-based access control."""

from __future__ import annotations

import hmac
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from mcp_server.models import ApiCredential, Role


class Unauthenticated(Exception):
    pass


class Forbidden(Exception):
    pass


@dataclass(frozen=True)
class AuthContext:
    key_id: str
    role: Role


def authenticate(
    credentials: Mapping[str, ApiCredential], presented: str | None
) -> AuthContext:
    if not presented:
        raise Unauthenticated("missing API key")
    for key_id, cred in credentials.items():
        if hmac.compare_digest(cred.api_key, presented):
            if cred.revoked:
                raise Unauthenticated("API key revoked")
            if cred.expires_at is not None and cred.expires_at <= datetime.now(
                timezone.utc
            ):
                raise Unauthenticated("API key expired")
            return AuthContext(key_id=key_id, role=cred.role)
    raise Unauthenticated("invalid API key")


def require(ctx: AuthContext, allowed: set[Role]) -> None:
    if ctx.role not in allowed:
        raise Forbidden(f"role {ctx.role.value} is not permitted")

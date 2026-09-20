"""Unit tests for authentication and RBAC."""

from __future__ import annotations

import unittest

from mcp_portfolio.auth import AuthContext, Forbidden, Unauthenticated, authenticate, require
from mcp_portfolio.models import Role

from .fixtures import (
    ADMIN_KEY,
    AUDITOR_KEY,
    OPERATOR_KEY,
    SUPPORT_KEY,
    make_settings,
)


class TestAuthenticate(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = make_settings()
        self.credentials = self.settings.api_keys

    def test_authenticate_valid_key(self) -> None:
        ctx = authenticate(self.credentials, ADMIN_KEY)
        self.assertIsInstance(ctx, AuthContext)
        self.assertEqual(ctx.key_id, "admin-1")
        self.assertEqual(ctx.role, Role.ADMIN)

    def test_authenticate_valid_support_key(self) -> None:
        ctx = authenticate(self.credentials, SUPPORT_KEY)
        self.assertEqual(ctx.key_id, "support-1")
        self.assertEqual(ctx.role, Role.SUPPORT_AGENT)

    def test_authenticate_valid_auditor_key(self) -> None:
        ctx = authenticate(self.credentials, AUDITOR_KEY)
        self.assertEqual(ctx.key_id, "auditor-1")
        self.assertEqual(ctx.role, Role.AUDITOR)

    def test_authenticate_valid_operator_key(self) -> None:
        ctx = authenticate(self.credentials, OPERATOR_KEY)
        self.assertEqual(ctx.key_id, "operator-1")
        self.assertEqual(ctx.role, Role.OPERATOR)

    def test_authenticate_missing_key(self) -> None:
        with self.assertRaises(Unauthenticated) as cm:
            authenticate(self.credentials, None)
        self.assertIn("missing", str(cm.exception))

    def test_authenticate_invalid_key(self) -> None:
        with self.assertRaises(Unauthenticated) as cm:
            authenticate(self.credentials, "completely-wrong-key-12345")
        self.assertIn("invalid", str(cm.exception))

    def test_authenticate_revoked_key(self) -> None:
        from mcp_portfolio.models import ApiCredential

        credentials = dict(self.credentials)
        credentials["revoked-1"] = ApiCredential(
            key_id="revoked-1",
            api_key="revoked-key-1234567890",
            role=Role.ADMIN,
            revoked=True,
        )
        with self.assertRaises(Unauthenticated) as cm:
            authenticate(credentials, "revoked-key-1234567890")
        self.assertIn("revoked", str(cm.exception))


class TestRequireRole(unittest.TestCase):
    def test_require_role_allowed(self) -> None:
        ctx = AuthContext(key_id="admin-1", role=Role.ADMIN)
        require(ctx, {Role.ADMIN, Role.SUPPORT_AGENT})

    def test_require_role_forbidden(self) -> None:
        ctx = AuthContext(key_id="auditor-1", role=Role.AUDITOR)
        with self.assertRaises(Forbidden) as cm:
            require(ctx, {Role.ADMIN, Role.SUPPORT_AGENT})
        self.assertIn("auditor", str(cm.exception))

    def test_require_role_exact_match(self) -> None:
        ctx = AuthContext(key_id="support-1", role=Role.SUPPORT_AGENT)
        require(ctx, {Role.SUPPORT_AGENT})

    def test_require_role_empty_set(self) -> None:
        ctx = AuthContext(key_id="admin-1", role=Role.ADMIN)
        with self.assertRaises(Forbidden):
            require(ctx, set())


if __name__ == "__main__":
    unittest.main()

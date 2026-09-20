"""Unit tests for auth and audit (T016)."""

import asyncio
from unittest import TestCase

from mcp_server.audit import AuditUnavailable
from mcp_server.auth import Forbidden, Unauthenticated, authenticate, require
from mcp_server.models import Outcome, Role

from tests.fixtures import TEST_KEYS, make_audit, make_ctx


class TestAuthenticate(TestCase):
    def test_valid_key_resolves_role(self) -> None:
        ctx = authenticate(TEST_KEYS, "test-agent-secret-key-1")
        self.assertEqual(ctx.role, Role.SUPPORT_AGENT)
        self.assertEqual(ctx.key_id, "agent-1")

    def test_missing_key_rejected(self) -> None:
        with self.assertRaises(Unauthenticated):
            authenticate(TEST_KEYS, None)

    def test_unknown_key_rejected(self) -> None:
        with self.assertRaises(Unauthenticated):
            authenticate(TEST_KEYS, "wrong-key-that-is-long-enough")

    def test_revoked_key_rejected(self) -> None:
        creds = dict(TEST_KEYS)
        revoked = creds["agent-1"].model_copy(update={"revoked": True})
        creds["agent-1"] = revoked
        with self.assertRaises(Unauthenticated):
            authenticate(creds, "test-agent-secret-key-1")


class TestRequire(TestCase):
    def test_denied_role_raises(self) -> None:
        with self.assertRaises(Forbidden):
            require(make_ctx(Role.OPERATOR), {Role.ADMIN, Role.SUPPORT_AGENT})

    def test_allowed_role_passes(self) -> None:
        require(make_ctx(Role.ADMIN), {Role.ADMIN})


class TestAuditLog(TestCase):
    def test_record_assigns_sequence_and_hash(self) -> None:
        audit = make_audit()
        entry = audit.record(
            make_ctx(Role.SUPPORT_AGENT),
            "tool.execute",
            "create_ticket",
            Outcome.SUCCESS,
            {"a": 1},
        )
        self.assertEqual(entry.seq, 0)
        self.assertIsNotNone(entry.inputs_hash)
        self.assertNotIn("secret", (entry.inputs_hash or ""))

    def test_anonymous_denied_attempt_recorded(self) -> None:
        audit = make_audit()
        entry = audit.record(
            None, "auth.denied", "store://customers/cust_1001", Outcome.DENIED
        )
        self.assertEqual(entry.key_id, "anonymous")

    def test_broken_sink_fails_closed(self) -> None:
        audit = make_audit()
        audit.broken = True
        with self.assertRaises(AuditUnavailable):
            audit.record(make_ctx(Role.ADMIN), "resource.read", "x", Outcome.SUCCESS)

    def test_asyncio_smoke(self) -> None:
        async def go() -> int:
            return 1

        self.assertEqual(asyncio.run(go()), 1)

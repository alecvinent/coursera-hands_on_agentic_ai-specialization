from unittest import TestCase


class BaseTestCase(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()


class SeededTestCase(BaseTestCase):
    """Base class for deterministic tests using a fixed seed."""

    SEED: int = 20260918

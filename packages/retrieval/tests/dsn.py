"""DSN for the integration tests, kept apart from DATABASE_URL so they cannot write to production."""

import os
from collections.abc import Mapping

DEFAULT_TEST_DSN = "postgresql://isra:isra@localhost:5432/isra"


def resolve_test_dsn(environ: Mapping[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    return env.get("ISRA_TEST_DATABASE_URL") or DEFAULT_TEST_DSN

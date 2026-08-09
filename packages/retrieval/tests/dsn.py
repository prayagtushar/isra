"""Database DSN used by the integration tests.

Deliberately independent of ``DATABASE_URL`` / ``ISRA_DATABASE_URL``: the
retrieval package calls ``load_dotenv()`` when ``db.py`` is imported, so the
deployed connection string is present in ``os.environ`` during a test run. The
integration tests insert and delete rows, so inheriting it would mutate the
production database. Point the tests at another server with
``ISRA_TEST_DATABASE_URL``.
"""

import os
from collections.abc import Mapping

DEFAULT_TEST_DSN = "postgresql://isra:isra@localhost:5432/isra"


def resolve_test_dsn(environ: Mapping[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    return env.get("ISRA_TEST_DATABASE_URL") or DEFAULT_TEST_DSN

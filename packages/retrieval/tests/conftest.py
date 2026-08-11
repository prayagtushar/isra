import os

import pytest

from tests.dsn import resolve_test_dsn


@pytest.fixture(scope="session", autouse=True)
def bind_test_database():
    """Force every connection made during tests onto the test database, not the deployed one."""
    dsn = resolve_test_dsn()
    previous = {
        key: os.environ.get(key) for key in ("DATABASE_URL", "ISRA_DATABASE_URL")
    }
    os.environ["DATABASE_URL"] = dsn
    os.environ["ISRA_DATABASE_URL"] = dsn
    try:
        yield dsn
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

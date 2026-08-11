"""Bind the API suite to a throwaway database; load_dotenv() would otherwise supply the deployed one."""

import os

import psycopg
import pytest

DEFAULT_TEST_DSN = "postgresql://isra:isra@localhost:5432/isra"


def test_dsn() -> str:
    return os.environ.get("ISRA_TEST_DATABASE_URL") or DEFAULT_TEST_DSN


@pytest.fixture(scope="session", autouse=True)
def bind_test_database():
    dsn = test_dsn()
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


@pytest.fixture
def db_conn(bind_test_database):
    try:
        psycopg.connect(bind_test_database, connect_timeout=2).close()
    except Exception:
        pytest.skip("Postgres not available")

    from isra_retrieval.db import get_conn

    with get_conn() as conn:
        yield conn
        conn.rollback()

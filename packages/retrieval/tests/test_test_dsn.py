from tests.dsn import DEFAULT_TEST_DSN, resolve_test_dsn


def test_uses_explicit_test_dsn_when_set():
    env = {"ISRA_TEST_DATABASE_URL": "postgresql://t:t@localhost:5432/t"}
    assert resolve_test_dsn(env) == "postgresql://t:t@localhost:5432/t"


def test_falls_back_to_local_default():
    assert resolve_test_dsn({}) == DEFAULT_TEST_DSN


def test_never_inherits_the_deployed_database_url():
    # db.py calls load_dotenv() at import time, which pushes the production DSN
    # into os.environ. The integration tests write and delete rows, so picking
    # that up would mutate the live database.
    env = {
        "DATABASE_URL": "postgresql://prod@db.supabase.co:5432/postgres",
        "ISRA_DATABASE_URL": "postgresql://prod@db.supabase.co:5432/postgres",
    }
    assert resolve_test_dsn(env) == DEFAULT_TEST_DSN

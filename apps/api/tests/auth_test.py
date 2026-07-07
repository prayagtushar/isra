import pytest
from isra_retrieval.db import get_conn

from src.auth import (
    create_password_reset,
    create_user,
    get_user_by_email,
    get_user_by_id,
    hash_password,
    update_password,
    validate_reset_token,
    verify_password,
)


@pytest.fixture
def db_conn():
    with get_conn() as conn:
        yield conn
        conn.rollback()


def test_password_hash_roundtrip():
    h = hash_password("secret123")
    assert verify_password("secret123", h)
    assert not verify_password("wrong", h)


def test_create_and_get_user(db_conn):
    email = f"test-{id(db_conn)}@example.com"
    user = create_user(db_conn, email, hash_password("secret123"))
    assert user["email"] == email

    found = get_user_by_email(db_conn, email)
    assert found and found["id"] == user["id"]

    by_id = get_user_by_id(db_conn, user["id"])
    assert by_id and by_id["email"] == email


def test_update_password(db_conn):
    email = f"test-{id(db_conn)}@example.com"
    user = create_user(db_conn, email, hash_password("oldpass"))
    update_password(db_conn, user["id"], hash_password("newpass"))
    updated = get_user_by_id(db_conn, user["id"])
    assert updated and verify_password("newpass", updated["password_hash"])


def test_password_reset_token(db_conn):
    email = f"test-{id(db_conn)}@example.com"
    user = create_user(db_conn, email, hash_password("secret123"))
    token = create_password_reset(db_conn, user["id"])
    assert validate_reset_token(db_conn, token) == user["id"]
    assert validate_reset_token(db_conn, "invalid-token") is None

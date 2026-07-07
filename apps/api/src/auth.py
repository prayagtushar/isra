import secrets
from datetime import datetime, timedelta, timezone
from typing import TypedDict

import bcrypt
from psycopg import Connection

PASSWORD_RESET_TTL_HOURS = 1


class User(TypedDict):
    id: str
    email: str
    password_hash: str
    created_at: datetime
    updated_at: datetime


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def _row_to_user(row: tuple) -> User:
    return {
        "id": str(row[0]),
        "email": row[1],
        "password_hash": row[2],
        "created_at": row[3],
        "updated_at": row[4],
    }


def create_user(conn: Connection, email: str, password_hash: str) -> User:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (email, password_hash)
            VALUES (%s, %s)
            RETURNING id, email, password_hash, created_at, updated_at
            """,
            (email, password_hash),
        )
        row = cur.fetchone()
        conn.commit()
        return _row_to_user(row)


def get_user_by_email(conn: Connection, email: str) -> User | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, password_hash, created_at, updated_at
            FROM users
            WHERE email = %s
            """,
            (email,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_user(row)


def get_user_by_id(conn: Connection, user_id: str) -> User | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, email, password_hash, created_at, updated_at
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return _row_to_user(row)


def create_password_reset(conn: Connection, user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = bcrypt.hashpw(token.encode(), bcrypt.gensalt(rounds=10)).decode()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=PASSWORD_RESET_TTL_HOURS)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO password_resets (user_id, token_hash, expires_at)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (user_id, token_hash, expires_at),
        )
        conn.commit()
    return token


def validate_reset_token(conn: Connection, token: str) -> str | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, user_id, token_hash, expires_at, used_at
            FROM password_resets
            WHERE expires_at > NOW() AND used_at IS NULL
            ORDER BY created_at DESC
            """,
        )
        for row in cur.fetchall():
            if bcrypt.checkpw(token.encode(), row[2].encode()):
                return str(row[1])
    return None


def mark_reset_used(conn: Connection, token: str) -> None:
    token_hash = bcrypt.hashpw(token.encode(), bcrypt.gensalt(rounds=10)).decode()
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE password_resets
            SET used_at = NOW()
            WHERE token_hash = %s
            """,
            (token_hash,),
        )
        conn.commit()


def update_password(conn: Connection, user_id: str, password_hash: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET password_hash = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (password_hash, user_id),
        )
        conn.commit()

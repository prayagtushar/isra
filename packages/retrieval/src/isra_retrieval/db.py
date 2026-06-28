import os
from contextlib import contextmanager
from typing import Generator

import psycopg
from pgvector.psycopg import register_vector
from psycopg import Connection
from dotenv import load_dotenv

load_dotenv()

def get_dsn() -> str:
    return os.environ.get(
        "ISRA_DATABASE_URL",
        os.environ.get("DATABASE_URL", "postgresql://isra:isra@localhost:5432/isra"),
    )

@contextmanager
def get_conn() -> Generator[Connection, None, None]:
    conn = psycopg.connect(get_dsn())
    try:
        register_vector(conn)
        yield conn
    finally:
        conn.close()

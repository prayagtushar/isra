from typing import List

import numpy as np
from psycopg import Connection

from isra_retrieval.models import Chunk

SQL = """
SELECT c.id, c.startup_id, s.name, c.chunk_index, c.text, s.source_url,
       c.embedding <=> %s::vector AS distance
FROM chunks c
JOIN startups s ON s.id = c.startup_id
ORDER BY distance
LIMIT %s
"""


def vector_search(conn: Connection, query: np.ndarray, top_k: int = 10) -> List[Chunk]:
    with conn.cursor() as cur:
        cur.execute(SQL, (query.tolist(), top_k))
        rows = cur.fetchall()

    return [
        Chunk(
            id=row[0],
            startup_id=row[1],
            startup_name=row[2],
            chunk_index=row[3],
            text=row[4],
            source_url=row[5],
            score=1.0 - float(row[6]),
        )
        for row in rows
    ]
import re
from typing import List

from psycopg import Connection
from isra_retrieval.models import Chunk

def _to_tsquery(query : str) -> str:
    terms = [t for t in re.split(r"\W+", query.lower()) if t and len(t) > 2]
    return " | ".join(terms)

SQL = """
SELECT c.id, c.startup_id, s.name, c.chunk_index, c.text, s.source_url,
ts_rank_cd(c.tsvec, to_tsquery('english', %s)) AS rank
FROM chunks c
JOIN startups s ON s.id = c.startup_id
WHERE c.tsvec @@ to_tsquery('english', %s)
ORDER BY rank DESC
LIMIT %s;
"""

def search_keyword(conn: Connection,query : str, top_k:int =10) -> List[Chunk]:
    tsq = _to_tsquery(query)
    if not tsq:
        return []

    with conn.cursor() as cur:
        cur.execute(SQL,(tsq,tsq,top_k))
        rows = cur.fetchall()
    
    return [
        Chunk(
            id=row[0],
            startup_id=row[1],
            startup_name=row[2],
            chunk_index=row[3],
            text=row[4],
            source_url=row[5],
            score=float(row[6]),
        )
        for row in rows
    ]

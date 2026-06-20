from typing import List


import numpy as np
import psycopg

from src.chunker import Chunk
from src.schema import Startup

STARTUP_PRESET = """ 
INSERT INTO startups (
    normalized_name,
    source_url,
    name,
    description,
    one_liner,
    founded_year,
    headquarters,
    founders,
    fundings,
    sectors,
    tags,
    scraped_date
) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
ON CONFLICT (normalized_name) DO UPDATE SET
    source_url = EXCLUDED.source_url,
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    one_liner = EXCLUDED.one_liner,
    founded_year = EXCLUDED.founded_year,
    headquarters = EXCLUDED.headquarters,
    fundings = EXCLUDED.fundings,
    founders = EXCLUDED.founders,
    sectors = EXCLUDED.sectors, 
    tags = EXCLUDED.tags,
    scraped_date = EXCLUDED.scraped_date
"""

CHUNK_UPSERT = """
INSERT INTO chunks (startup_id, chunk_index,text,embedding)
VALUES (%s,%s,%s,%s::vector)
ON CONFLICT (startup_id,chunk_index) DO UPDATE SET
    text = EXCLUDED.text,
    embedding = EXCLUDED.embedding
"""


def load_startups_and_chunks(
    conn: psycopg.Connection,
    startups: List[Startup],
    chunks: List[Chunk],
    embeddings: np.ndarray,
) -> None:
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"Mismatch : {len(chunks)} chunks but {len(embeddings)} embeddings."
        )

    with conn.transaction():
        with conn.cursor() as cursor:
            startup_rows = [
                (
                    s.normalized_name,
                    str(s.source_url),
                    s.name,
                    s.description,
                    s.one_liner,
                    s.founded_year,
                    s.headquarters,
                    s.founders,
                    s.fundings,
                    s.sectors,
                    s.tags,
                    s.scraped_date,
                )
                for s in startups
            ]
            cursor.executemany(STARTUP_PRESET,startup_rows)
            
            cursor.execute("SELECT id,normalized_name FROM startups")
            id_map = {
                name : id for id,name in cursor.fetchall()
            }
    
            chunk_rows = []
            for chunk,embedding in zip(chunks,embeddings):
                startup_id = id_map.get(chunk.startup_name)
                if startup_id is None:
                    raise ValueError(
                        f"Chunk references unknown startup: {chunk.startup_name}"
                    )
                chunk_rows.append((
                    startup_id,chunk.chunk_index,chunk.text,embedding.tolist()
                ))
                    
            cursor.executemany(CHUNK_UPSERT, chunk_rows)
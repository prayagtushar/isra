import os

import psycopg
from dotenv import load_dotenv

from src.chunker import naive_chunk
from src.embedder import embed_text
from src.loader import load_startups_and_chunks
from src.sample_data import sample_startups

load_dotenv()

def main() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")

    startups = sample_startups()
    
    chunks = []
    for s in startups:
        chunks.extend(naive_chunk(s.description,str(s.source_url),s.normalized_name))
    
    embeddings = embed_text([c.text for c in chunks])
    
    with psycopg.connect(url) as conn:
        load_startups_and_chunks(conn,startups,chunks,embeddings)
    
    print(f"Loaded {len(startups)} startups and {len(chunks)} chunks.")

if __name__ == "__main__":
    main()

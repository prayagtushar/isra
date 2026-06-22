from functools import lru_cache
from typing import List

from sentence_transformers import CrossEncoder

from isra_retrieval.models import Chunk

RERANKER_MODEL = "BAAI/bge-reranker-base"

@lru_cache(maxsize=1)
def _reranker() -> CrossEncoder:
    return CrossEncoder(RERANKER_MODEL)

def rerank(query: str,chunks: List[Chunk], top_k: int = 5) -> List[Chunk]:
    if not chunks:
        return []
    
    pairs = [[query,c.text] for c in chunks]
    
    scores = _reranker().predict(pairs)
    
    scored_chunk = [
        Chunk(
            id=c.id,
            startup_id=c.startup_id,
            startup_name=c.startup_name,
            chunk_index=c.chunk_index,
            text=c.text,
            source_url=c.source_url,
            score=float(s),
        )
        for c,s in zip(chunks,scores)
    ]
    
    return sorted(scored_chunk, key=lambda c : c.score, reverse=True)[:top_k]
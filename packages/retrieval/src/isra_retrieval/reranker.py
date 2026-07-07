from functools import lru_cache
from typing import List

from sentence_transformers import CrossEncoder

from isra_retrieval.models import Chunk

RERANKER_MODEL = "BAAI/bge-reranker-base"

@lru_cache(maxsize=1)
def _reranker() -> CrossEncoder:
    return CrossEncoder(RERANKER_MODEL)

def rerank(query: str, chunks: List[Chunk], top_k: int = 5, rerank_top_k: int = 20) -> List[Chunk]:
    if not chunks:
        return []

    # Cross-encoding every fused chunk is too slow on low-CPU hosts. Score a
    # smaller top-N subset and return the best top_k from it.
    chunks_to_score = chunks[:rerank_top_k]
    pairs = [[query, c.text] for c in chunks_to_score]

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
        for c, s in zip(chunks_to_score, scores)
    ]

    return sorted(scored_chunk, key=lambda c: c.score, reverse=True)[:top_k]

from typing import List
from isra_retrieval.models import Chunk

K = 60

def rrf_fusion(
    vector_result : List[Chunk],
    keyword_result : List[Chunk],
    top_k : int = 10
) -> List[Chunk]:
    
    scores: dict[int, float] = {}
    details: dict[int, Chunk] = {}

    for rank,chunk in enumerate(vector_result,start=1):
        scores[chunk.id] = scores.get(chunk.id,0.0) + 1 / (K+rank)
        details[chunk.id] = chunk

    for rank,chunk in enumerate(keyword_result,start=1):
        scores[chunk.id] = scores.get(chunk.id,0.0) + 1 / (K+rank)
        details[chunk.id] = chunk    
    
    sorted_ids = sorted(scores,key=lambda cid: scores[cid], reverse=True)
    
    return [
        Chunk(
            id=details[cid].id,
            startup_id=details[cid].startup_id,
            startup_name=details[cid].startup_name,
            chunk_index=details[cid].chunk_index,
            text=details[cid].text,
            source_url=details[cid].source_url,
            score=scores[cid],
        )
        for cid in sorted_ids[:top_k]
    ]

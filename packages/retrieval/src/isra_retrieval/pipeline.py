from typing import List

from isra_retrieval.db import get_conn
from isra_retrieval.embeddings import embed_query
from isra_retrieval.keyword_search import search_keyword
from isra_retrieval.models import Chunk
from isra_retrieval.reranker import rerank
from isra_retrieval.rrf_fusion import rrf_fusion
from isra_retrieval.vector_search import vector_search

RETRIEVAL_MODES = {"vector", "hybrid", "hybrid+rerank"}


def retrieve(
    query: str,
    top_k: int = 5,
    mode: str = "hybrid+rerank",
    retrieval_top_k: int = 100,
) -> List[Chunk]:
    if mode not in RETRIEVAL_MODES:
        raise ValueError(
            f"Mode {mode!r} is not supported. Use one of {RETRIEVAL_MODES}"
        )

    with get_conn() as conn:
        query_vector = embed_query(query)

        if mode == "vector":
            return vector_search(conn, query_vector, top_k=top_k)

        vector_results = vector_search(conn, query_vector, top_k=retrieval_top_k)
        keyword_results = search_keyword(conn, query, top_k=retrieval_top_k)
        fusion_results = rrf_fusion(
            vector_results, keyword_results, top_k=retrieval_top_k
        )

        if mode == "hybrid":
            return fusion_results[:top_k]

        return rerank(query, fusion_results, top_k=top_k)

import time
from typing import Iterator, List, Literal, TypedDict

from isra_retrieval.db import get_conn
from isra_retrieval.embeddings import embed_query
from isra_retrieval.keyword_search import search_keyword
from isra_retrieval.models import Chunk
from isra_retrieval.reranker import rerank
from isra_retrieval.rrf_fusion import rrf_fusion
from isra_retrieval.vector_search import vector_search

RETRIEVAL_MODES = {"vector", "hybrid", "hybrid+rerank"}


class StageSnapshot(TypedDict):
    name: Literal["vector", "keyword", "fusion", "rerank"]
    results: List[Chunk]


class RetrievalTrace(TypedDict):
    mode: Literal["vector", "hybrid", "hybrid+rerank"]
    latency_ms: float
    stages: List[StageSnapshot]


TRACE_STAGE_LIMIT = 8


class StageEvent(TypedDict):
    """One stage, reported the moment it finishes."""

    name: Literal["vector", "keyword", "fusion", "rerank"]
    results: List[Chunk]
    elapsed_ms: float
    # Candidates before truncation, or the funnel reads as loss rather than selection.
    total: int


def retrieve_stages(
    query: str,
    top_k: int = 5,
    mode: str = "hybrid+rerank",
    retrieval_top_k: int = 100,
    rerank_top_k: int = 20,
) -> Iterator[StageEvent]:
    """Run the pipeline, yielding each stage as it completes with elapsed_ms from the start."""
    if mode not in RETRIEVAL_MODES:
        raise ValueError(
            f"Mode {mode!r} is not supported. Use one of {RETRIEVAL_MODES}"
        )

    start = time.perf_counter()

    def elapsed() -> float:
        return (time.perf_counter() - start) * 1000

    with get_conn() as conn:
        query_vector = embed_query(query)

        if mode == "vector":
            vector_results = vector_search(conn, query_vector, top_k=retrieval_top_k)
            yield {
                "name": "vector",
                "results": vector_results[:TRACE_STAGE_LIMIT],
                "elapsed_ms": elapsed(),
                "total": len(vector_results),
            }
            return

        vector_results = vector_search(conn, query_vector, top_k=retrieval_top_k)
        yield {
            "name": "vector",
            "results": vector_results[:TRACE_STAGE_LIMIT],
            "elapsed_ms": elapsed(),
            "total": len(vector_results),
        }

        keyword_results = search_keyword(conn, query, top_k=retrieval_top_k)
        yield {
            "name": "keyword",
            "results": keyword_results[:TRACE_STAGE_LIMIT],
            "elapsed_ms": elapsed(),
            "total": len(keyword_results),
        }

        fusion_results = rrf_fusion(
            vector_results, keyword_results, top_k=retrieval_top_k
        )
        yield {
            "name": "fusion",
            "results": fusion_results[:TRACE_STAGE_LIMIT],
            "elapsed_ms": elapsed(),
            "total": len(fusion_results),
        }

        if mode == "hybrid":
            return

        rerank_results = rerank(
            query, fusion_results, top_k=top_k, rerank_top_k=rerank_top_k
        )
        yield {
            "name": "rerank",
            "results": rerank_results[:TRACE_STAGE_LIMIT],
            "elapsed_ms": elapsed(),
            "total": len(rerank_results),
        }


def retrieve_debug(
    query: str,
    top_k: int = 5,
    mode: str = "hybrid+rerank",
    retrieval_top_k: int = 100,
    rerank_top_k: int = 20,
) -> RetrievalTrace:
    """The whole trace at once, built on retrieve_stages so the pipeline is described once."""
    start = time.perf_counter()
    stages: List[StageSnapshot] = []
    for event in retrieve_stages(
        query,
        top_k=top_k,
        mode=mode,
        retrieval_top_k=retrieval_top_k,
        rerank_top_k=rerank_top_k,
    ):
        stages.append({"name": event["name"], "results": event["results"]})

    return {
        "mode": mode,  # type: ignore[typeddict-item]
        "latency_ms": (time.perf_counter() - start) * 1000,
        "stages": stages,
    }


def retrieve(
    query: str,
    top_k: int = 5,
    mode: str = "hybrid+rerank",
    retrieval_top_k: int = 100,
    rerank_top_k: int = 20,
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

        return rerank(query, fusion_results, top_k=top_k, rerank_top_k=rerank_top_k)

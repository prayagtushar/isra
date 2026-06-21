from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en-v1.5"


@lru_cache(maxsize=1)
def _model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: List[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, 384), dtype=np.float32)
    return _model().encode(texts, normalize_embeddings=True, show_progress_bar=False)


def embed_query(text: str) -> np.ndarray:
    return embed_texts([text])[0]

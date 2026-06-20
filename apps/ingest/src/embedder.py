from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL = "BAAI/bge-small-en-v1.5"


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL)


def embed_text(texts: List[str]) -> np.ndarray:
    if not texts:
        return np.empty((0, 384), dtype=np.float32)
    model = _load_model()
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False)


def embed_query(text: str) -> np.ndarray:
    return embed_text([text])[0]


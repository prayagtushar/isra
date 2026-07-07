from dataclasses import dataclass

@dataclass(frozen=True)
class Chunk:
    id: int
    startup_id: int
    startup_name: str
    chunk_index: int
    text: str
    source_url: str
    score: float = 0.0

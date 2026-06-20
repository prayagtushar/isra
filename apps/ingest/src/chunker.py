from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    text: str
    source_url: str
    startup_name: str
    chunk_index: int


def naive_chunk(
    text: str,
    source_url: str,
    startup_name: str,
    chunk_size: int = 200,
    overlap: int = 20,
) -> list[Chunk]:
    """Split text into overlapping word windows.

    Args:
        text: Raw text to chunk.
        source_url: URL the text came from.
        startup_name: Normalized startup name this text belongs to.
        chunk_size: Maximum number of words per chunk.
        overlap: Number of words shared between consecutive chunks.
    """

    if not text or not text.strip():
        return []

    words = text.split()

    if len(words) <= chunk_size:
        return [
            Chunk(
                text=text.strip(),
                source_url=source_url,
                startup_name=startup_name,
                chunk_index=0,
            )
        ]

    step = max(1, chunk_size - overlap)
    chunks: list[Chunk] = []

    for chunk_index, start in enumerate(range(0, len(words), step)):
        end = min(start + chunk_size, len(words))
        chunk_text = " ".join(words[start:end])
        chunks.append(
            [
                Chunk(
                    text=chunk_text,
                    source_url=source_url,
                    startup_name=startup_name,
                    chunk_index=chunk_index,
                )
            ]
        )
        if end == len(words):
            break

    return chunks


def semantic_chunk(
    text: str,
    source_url: str,
    startup_name: str,
    max_chunk_size: int = 200,
) -> list[Chunk]:

    if not text or not text.strip():
        return []

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if not paragraphs:
        return []

    chunks: list[Chunk] = []
    buffer: list[str] = []
    curr_word_count = 0
    chunk_index = 0

    def flush() -> None:
        nonlocal chunk_index, curr_word_count
        if not buffer:
            return
        chunk_text = "\n\n".join(buffer)
        chunks.append(
            Chunk(
                text=chunk_text,
                source_url=source_url,
                startup_name=startup_name,
                chunk_index=chunk_index,
            )
        )
        chunk_index += 1
        buffer.clear()
        curr_word_count = 0

    for para in paragraphs:
        para_word_count = len(para.split())
        if curr_word_count + para_word_count > max_chunk_size and buffer:
            flush()
        buffer.append(para)
        curr_word_count += para_word_count
    flush()
    return chunks

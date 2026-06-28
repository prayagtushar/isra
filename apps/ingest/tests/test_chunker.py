from src.chunker import Chunk, naive_chunk, semantic_chunk

def test_naive_chunk_empty():
    assert naive_chunk("", "https://a.com", "x") == []
    assert naive_chunk("   ", "https://a.com", "x") == []

def test_naive_chunk_short_text():
    chunks = naive_chunk("hello world", "https://a.com", "x", chunk_size=50)
    assert len(chunks) == 1
    assert chunks[0].text == "hello world"
    assert chunks[0].startup_name == "x"
    assert chunks[0].source_url == "https://a.com"
    assert chunks[0].chunk_index == 0

def test_naive_chunk_overlap():
    words = " ".join([f"w{i}" for i in range(10)])
    chunks = naive_chunk(words, "https://a.com", "x", chunk_size=4, overlap=2)
    assert len(chunks) > 1
    assert chunks[0].text.split() == [f"w{i}" for i in range(4)]
    assert "w2" in chunks[1].text

def test_naive_chunk_indexes_increment():
    text = " ".join([f"word{i}" for i in range(20)])
    chunks = naive_chunk(text, "https://a.com", "x", chunk_size=5)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))

def test_semantic_chunk_empty():
    assert semantic_chunk("", "https://a.com", "x") == []
    assert semantic_chunk("   \n\n  ", "https://a.com", "x") == []

def test_semantic_chunk_groups_paragraphs():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = semantic_chunk(text, "https://a.com", "x", max_chunk_size=10)
    assert len(chunks) >= 1
    assert all(isinstance(c, Chunk) for c in chunks)
    assert chunks[0].startup_name == "x"

def test_semantic_chunk_respects_max_size():
    paragraphs = [f"Para {i} has five words." for i in range(20)]
    text = "\n\n".join(paragraphs)
    chunks = semantic_chunk(text, "https://a.com", "x", max_chunk_size=20)
    for c in chunks:
        assert len(c.text.split()) <= 30

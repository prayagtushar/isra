from types import SimpleNamespace

from src.llm import _build_prompt, SYSTEM_PROMPT


def test_system_prompt_enforces_grounding():
    assert "using only the numbered sources" in SYSTEM_PROMPT.lower()
    assert "do not use outside knowledge" in SYSTEM_PROMPT.lower()
    assert "do not invent" in SYSTEM_PROMPT.lower()
    assert "do not mention any company that is not listed" in SYSTEM_PROMPT.lower()
    assert "cannot point to a specific source" in SYSTEM_PROMPT.lower()


def test_build_prompt_includes_sources_and_question():
    chunks = [SimpleNamespace(text="CRED is a fintech.", source_url="https://example.com")]
    prompt = _build_prompt("What is CRED?", chunks)
    assert "[Source 1]" in prompt
    assert "CRED is a fintech." in prompt
    assert "Question: What is CRED?" in prompt

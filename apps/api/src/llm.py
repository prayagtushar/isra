from collections.abc import AsyncGenerator

import openrouter

from src.config import settings

SYSTEM_PROMPT = """You are a helpful assistant answering questions about Indian startups.
Use only the provided context. Cite sources inline using [Source N] format.
If the context does not contain the answer, say you don't know."""

_client = openrouter.OpenRouter(api_key=settings.openrouter_api_key)

def _build_prompt(question: str, chunks: list) -> str:
    context_lines = [
        f"[Source {i + 1}] {c.text} (from {c.source_url})"
        for i, c in enumerate(chunks)
    ]
    context = "\n".join(context_lines)
    return f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"

async def stream_answer(
    question: str,
    chunks: list,
    history: list[dict] | None = None,
) -> AsyncGenerator[str, None]:
    prompt = _build_prompt(question, chunks)
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    stream = await _client.chat.send_async(
        model=settings.llm_model,
        messages=messages,
        max_tokens=1024,
        stream=True,
    )

    async for chunk in stream:
        choice = chunk.choices[0]
        if choice.delta and choice.delta.content:
            yield choice.delta.content

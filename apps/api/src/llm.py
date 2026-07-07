from collections.abc import AsyncGenerator

import openrouter

from src.config import settings

SYSTEM_PROMPT = """You are a research assistant answering questions about Indian startups using ONLY the numbered sources provided below.

Rules:
1. Base your answer entirely on the provided context. Do not use outside knowledge.
2. Cite sources inline using [Source N] format.
3. If the context does not contain enough information to answer, say exactly: "I don't have enough information in the provided context to answer this."
4. Do not invent companies, funding rounds, founders, locations, dates, or statistics that are not in the context.
5. Do not classify a company as fintech, healthcare, etc. unless the context explicitly says so.
6. When the question asks for funding rounds (e.g., Series A, Series B), answer only if the context explicitly mentions those rounds. Otherwise state that the context does not include funding-round details.
7. If you are tempted to add a fact you "know" but cannot point to a specific source above, stop and omit it.
8. Do not mention any company that is not listed in the sources above."""

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
        temperature=0.0,
        stream=True,
    )

    async for chunk in stream:
        choice = chunk.choices[0]
        if choice.delta and choice.delta.content:
            yield choice.delta.content

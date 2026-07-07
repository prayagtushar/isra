import json
from typing import Protocol

from openai import AsyncOpenAI

from src.config import settings

class Judge(Protocol):
    async def complete(self, prompt: str) -> str: ...

class OpenRouterJudge:
    

    def __init__(self, client: AsyncOpenAI | None = None, model: str | None = None):
        self._client = client or AsyncOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
        )
        self._model = model or settings.llm_model

    async def complete(self, prompt: str) -> str:
        resp = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=512,
        )
        return resp.choices[0].message.content or ""

def _extract_score(text: str) -> float | None:
    
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        obj = json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return None
    score = obj.get("score")
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        return None
    return max(0.0, min(1.0, float(score)))

async def score_with_judge(judge: Judge, prompt: str) -> float | None:
    try:
        text = await judge.complete(prompt)
    except Exception:
        return None
    return _extract_score(text)

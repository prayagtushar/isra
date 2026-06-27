from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from isra_retrieval import retrieve as _default_retrieve

from src.golden import GoldenItem
from src.judge import Judge, score_with_judge

SYSTEM_PROMPT = (
    "You are a helpful assistant answering questions about Indian startups.\n"
    "Use only the provided context. Cite sources inline using [Source N] format.\n"
    "If the context does not contain the answer, say you don't know."
)


def _format_contexts(chunks: Sequence) -> list[str]:
    return [f"{c.text} (from {c.source_url})" for c in chunks]


async def generate_answer(client, model: str, question: str, chunks: Sequence) -> str:
    numbered = "\n".join(
        f"[Source {i + 1}] {ctx}" for i, ctx in enumerate(_format_contexts(chunks))
    )
    prompt = f"Context:\n{numbered}\n\nQuestion: {question}\nAnswer:"
    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        max_tokens=512,
    )
    return resp.choices[0].message.content or ""


def _numbered(contexts: Sequence[str]) -> str:
    return "\n".join(f"[{i + 1}] {c}" for i, c in enumerate(contexts))


def faithfulness_prompt(answer: str, contexts: Sequence[str]) -> str:
    return (
        "You are grading whether an ANSWER is faithful to the CONTEXT.\n"
        "Faithfulness = the fraction of factual claims in the answer that are "
        "directly supported by the context. Penalize anything not in the context.\n\n"
        f"CONTEXT:\n{_numbered(contexts)}\n\n"
        f"ANSWER:\n{answer}\n\n"
        'Respond with JSON only: {"score": <float 0..1>, "reason": "<short>"}'
    )


def answer_relevancy_prompt(question: str, answer: str) -> str:
    return (
        "You are grading whether an ANSWER directly addresses the QUESTION.\n"
        "Answer relevancy = how completely and directly the answer responds to the "
        "question (ignore factual accuracy here).\n\n"
        f"QUESTION:\n{question}\n\n"
        f"ANSWER:\n{answer}\n\n"
        'Respond with JSON only: {"score": <float 0..1>, "reason": "<short>"}'
    )


def context_precision_prompt(question: str, contexts: Sequence[str]) -> str:
    return (
        "You are grading retrieval quality for a QUESTION.\n"
        "Context precision = the fraction of the retrieved CONTEXT passages that are "
        "relevant to answering the question.\n\n"
        f"QUESTION:\n{question}\n\n"
        f"CONTEXT:\n{_numbered(contexts)}\n\n"
        'Respond with JSON only: {"score": <float 0..1>, "reason": "<short>"}'
    )


@dataclass
class ItemScore:
    question: str
    answer: str
    faithfulness: float | None
    answer_relevancy: float | None
    context_precision: float | None


@dataclass
class GenerationReport:
    mode: str
    items: list[ItemScore] = field(default_factory=list)

    def mean(self, metric: str) -> float | None:
        vals = [v for i in self.items if (v := getattr(i, metric)) is not None]
        return sum(vals) / len(vals) if vals else None

    def coverage(self, metric: str) -> tuple[int, int]:
        scored = sum(1 for i in self.items if getattr(i, metric) is not None)
        return scored, len(self.items)


async def evaluate_generation(
    items: Sequence[GoldenItem],
    mode: str,
    top_k: int,
    judge: Judge,
    client,
    model: str,
    retrieve: Callable = _default_retrieve,
) -> GenerationReport:
    report = GenerationReport(mode=mode)
    for item in items:
        chunks = retrieve(item.question, top_k=top_k, mode=mode)
        contexts = _format_contexts(chunks)
        answer = await generate_answer(client, model, item.question, chunks)
        report.items.append(
            ItemScore(
                question=item.question,
                answer=answer,
                faithfulness=await score_with_judge(
                    judge, faithfulness_prompt(answer, contexts)
                ),
                answer_relevancy=await score_with_judge(
                    judge, answer_relevancy_prompt(item.question, answer)
                ),
                context_precision=await score_with_judge(
                    judge, context_precision_prompt(item.question, contexts)
                ),
            )
        )
    return report

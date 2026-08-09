import asyncio
from dataclasses import dataclass

from src.generation_eval import (
    GenerationReport,
    ItemScore,
    abstention_prompt,
    answer_relevancy_prompt,
    context_precision_prompt,
    evaluate_generation,
    faithfulness_prompt,
)
from src.golden import GoldenItem


@dataclass
class FakeChunk:
    text: str = "ctx"
    source_url: str = "http://x"
    startup_name: str = "Paytm"


def test_prompts_include_inputs_and_request_json():
    fp = faithfulness_prompt("ans", ["c1", "c2"])
    assert "ans" in fp and "c1" in fp and "score" in fp.lower()
    ap = answer_relevancy_prompt("q?", "ans")
    assert "q?" in ap and "ans" in ap and "score" in ap.lower()
    cp = context_precision_prompt("q?", ["c1"])
    assert "q?" in cp and "c1" in cp and "score" in cp.lower()


def test_abstention_prompt_includes_question_and_answer():
    prompt = abstention_prompt("q?", "I don't know")
    assert "q?" in prompt and "I don't know" in prompt
    assert "score" in prompt.lower()


class ScriptedJudge:
    def __init__(self, scores):
        self.scores = list(scores)

    async def complete(self, prompt: str) -> str:
        return f'{{"score": {self.scores.pop(0)}}}'


class FakeClient:
    pass


async def _fake_generate(client, model, question, chunks):
    return "generated answer"


def _answerable(question, expected):
    return GoldenItem(question=question, expected=(expected,))


def test_evaluate_generation_aggregates_means_and_coverage(monkeypatch):
    import src.generation_eval as ge

    monkeypatch.setattr(ge, "generate_answer", _fake_generate)

    items = [_answerable("q1", "paytm"), _answerable("q2", "zomato")]

    def retrieve(q, top_k=5, mode="hybrid+rerank"):
        return [FakeChunk()]

    judge = ScriptedJudge([1.0, 0.8, 0.6, 0.0, 0.4, 0.2])

    report = asyncio.run(
        evaluate_generation(
            items,
            mode="hybrid+rerank",
            top_k=5,
            judge=judge,
            client=FakeClient(),
            model="m",
            retrieve=retrieve,
        )
    )
    assert isinstance(report, GenerationReport)
    assert report.mode == "hybrid+rerank"
    assert abs(report.mean("faithfulness") - 0.5) < 1e-9
    assert abs(report.mean("answer_relevancy") - 0.6) < 1e-9
    assert abs(report.mean("context_precision") - 0.4) < 1e-9
    assert report.coverage("faithfulness") == (2, 2)


def test_unanswerable_items_are_scored_on_abstention_only(monkeypatch):
    import src.generation_eval as ge

    monkeypatch.setattr(ge, "generate_answer", _fake_generate)

    items = [GoldenItem(question="q1", expected=(), category="unanswerable")]

    def retrieve(q, top_k=5, mode="hybrid+rerank"):
        return [FakeChunk()]

    # A single judge call: the abstention grade. Faithfulness, relevancy and
    # context precision are meaningless when there is no correct answer.
    judge = ScriptedJudge([1.0])

    report = asyncio.run(
        evaluate_generation(
            items,
            mode="hybrid+rerank",
            top_k=5,
            judge=judge,
            client=FakeClient(),
            model="m",
            retrieve=retrieve,
        )
    )
    (scored,) = report.items
    assert scored.abstention == 1.0
    assert scored.faithfulness is None
    assert scored.answer_relevancy is None
    assert scored.context_precision is None


def test_answerable_items_are_not_scored_on_abstention(monkeypatch):
    import src.generation_eval as ge

    monkeypatch.setattr(ge, "generate_answer", _fake_generate)

    items = [_answerable("q1", "paytm")]

    def retrieve(q, top_k=5, mode="hybrid+rerank"):
        return [FakeChunk()]

    judge = ScriptedJudge([1.0, 0.8, 0.6])

    report = asyncio.run(
        evaluate_generation(
            items,
            mode="hybrid+rerank",
            top_k=5,
            judge=judge,
            client=FakeClient(),
            model="m",
            retrieve=retrieve,
        )
    )
    (scored,) = report.items
    assert scored.abstention is None
    assert scored.faithfulness == 1.0


def test_report_handles_all_none():
    report = GenerationReport(
        mode="vector",
        items=[ItemScore("q", "a", None, None, None, None)],
    )
    assert report.mean("faithfulness") is None
    assert report.coverage("faithfulness") == (0, 1)

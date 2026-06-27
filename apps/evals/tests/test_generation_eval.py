import asyncio
from dataclasses import dataclass

from src.generation_eval import (
    GenerationReport,
    ItemScore,
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


class ScriptedJudge:
    """Returns scores in call order so each metric gets a distinct value."""

    def __init__(self, scores):
        self.scores = list(scores)

    async def complete(self, prompt: str) -> str:
        return f'{{"score": {self.scores.pop(0)}}}'


class FakeClient:
    pass


async def _fake_generate(client, model, question, chunks):
    return "generated answer"


def test_evaluate_generation_aggregates_means_and_coverage(monkeypatch):
    import src.generation_eval as ge

    monkeypatch.setattr(ge, "generate_answer", _fake_generate)

    items = [GoldenItem("q1", "paytm"), GoldenItem("q2", "zomato")]

    def retrieve(q, top_k=5, mode="hybrid+rerank"):
        return [FakeChunk()]

    # 2 items x 3 metrics = 6 judge calls; q1 -> 1.0/0.8/0.6, q2 -> 0.0/0.4/0.2
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


def test_report_handles_all_none():
    report = GenerationReport(
        mode="vector",
        items=[ItemScore("q", "a", None, None, None)],
    )
    assert report.mean("faithfulness") is None
    assert report.coverage("faithfulness") == (0, 1)

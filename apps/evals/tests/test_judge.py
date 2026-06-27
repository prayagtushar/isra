import asyncio

from src.judge import _extract_score, score_with_judge


def test_extract_score_plain_json():
    assert _extract_score('{"score": 0.75, "reason": "ok"}') == 0.75


def test_extract_score_with_code_fence_and_prose():
    text = 'Here is my judgement:\n```json\n{"score": 1, "reason": "grounded"}\n```'
    assert _extract_score(text) == 1.0


def test_extract_score_clamps_out_of_range():
    assert _extract_score('{"score": 1.4}') == 1.0
    assert _extract_score('{"score": -0.2}') == 0.0


def test_extract_score_returns_none_on_garbage():
    assert _extract_score("no json here") is None
    assert _extract_score('{"score": "high"}') is None


class FakeJudge:
    def __init__(self, reply):
        self.reply = reply

    async def complete(self, prompt: str) -> str:
        return self.reply


def test_score_with_judge_parses_reply():
    score = asyncio.run(score_with_judge(FakeJudge('{"score": 0.5}'), "p"))
    assert score == 0.5


class BoomJudge:
    async def complete(self, prompt: str) -> str:
        raise RuntimeError("api down")


def test_score_with_judge_swallows_errors():
    assert asyncio.run(score_with_judge(BoomJudge(), "p")) is None

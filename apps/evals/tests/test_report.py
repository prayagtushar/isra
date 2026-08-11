import json
from pathlib import Path

from src.generation_eval import GenerationReport, ItemScore
from src.report import build_json, render_markdown, write_report
from src.retrieval_eval import CategoryResult, ModeResult


def _fixture():
    meta = {"generated_at": "2026-06-27T00:00:00Z", "n": 2, "top_k": 5, "model": "m"}
    modes = [
        ModeResult("vector", 0.5, 0.5, 0.4, 2),
        ModeResult(
            "hybrid+rerank",
            1.0,
            1.0,
            0.9,
            2,
            by_category={
                "direct": CategoryResult("direct", 1.0, 1.0, 0.9, 1),
                "multi_hop": CategoryResult("multi_hop", 0.0, 0.5, 0.0, 1),
            },
        ),
    ]
    gen = GenerationReport(
        mode="hybrid+rerank",
        items=[
            ItemScore("q1", "a1", 0.8, 0.9, 0.7, None, answerable=True),
            ItemScore("q2", "a2", None, 0.5, 0.6, None, answerable=True),
            ItemScore("q3", "a3", None, None, None, 1.0, answerable=False),
        ],
    )
    return meta, modes, gen


def test_coverage_denominator_excludes_inapplicable_items():
    # Each metric is attempted on its own subset, so coverage must not divide by all three.
    _, _, gen = _fixture()
    assert gen.coverage("faithfulness") == (1, 2)
    assert gen.coverage("abstention") == (1, 1)


def test_render_has_sections_and_rows():
    meta, modes, gen = _fixture()
    md = render_markdown(meta, modes, gen)
    assert "# Evaluation" in md
    assert "Retrieval mode comparison" in md
    assert "hybrid+rerank" in md
    assert "| 1.000 | 1.000 | 0.900 |" in md
    assert "Generation quality" in md
    assert "Faithfulness" in md
    assert "1/2" in md  # faithfulness scored on 1 of 2 answerable items


def test_render_includes_per_category_breakdown():
    meta, modes, gen = _fixture()
    md = render_markdown(meta, modes, gen)
    assert "multi_hop" in md


def test_render_includes_abstention_on_unanswerable_questions():
    meta, modes, gen = _fixture()
    md = render_markdown(meta, modes, gen)
    assert "Abstention" in md


def test_render_without_generation():
    meta, modes, _ = _fixture()
    md = render_markdown(meta, modes, None)
    assert "Retrieval mode comparison" in md
    assert "skipped" in md.lower()


def test_write_report_emits_md_and_json(tmp_path: Path):
    meta, modes, gen = _fixture()
    out = tmp_path / "EVALUATION.md"
    written = write_report(out, meta, modes, gen)
    assert written == out and out.exists()
    sidecar = tmp_path / "evaluation.json"
    assert sidecar.exists()
    data = json.loads(sidecar.read_text())
    assert data["meta"]["n"] == 2
    assert data["retrieval"][1]["mode"] == "hybrid+rerank"
    assert data["retrieval"][1]["recall_at_k"] == 1.0
    assert data["retrieval"][1]["by_category"]["multi_hop"]["recall_at_k"] == 0.5
    assert data["generation"]["mode"] == "hybrid+rerank"
    assert data["generation"]["means"]["abstention"] == 1.0

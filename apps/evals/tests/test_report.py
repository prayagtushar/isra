import json
from pathlib import Path

from src.generation_eval import GenerationReport, ItemScore
from src.report import build_json, render_markdown, write_report
from src.retrieval_eval import ModeResult

def _fixture():
    meta = {"generated_at": "2026-06-27T00:00:00Z", "n": 2, "top_k": 5, "model": "m"}
    modes = [
        ModeResult("vector", 0.5, 0.4, 2),
        ModeResult("hybrid+rerank", 1.0, 0.9, 2),
    ]
    gen = GenerationReport(
        mode="hybrid+rerank",
        items=[
            ItemScore("q1", "a1", 0.8, 0.9, 0.7),
            ItemScore("q2", "a2", None, 0.5, 0.6),
        ],
    )
    return meta, modes, gen

def test_render_has_sections_and_rows():
    meta, modes, gen = _fixture()
    md = render_markdown(meta, modes, gen)
    assert "# Evaluation" in md
    assert "Retrieval mode comparison" in md
    assert "hybrid+rerank" in md
    assert "| 1.000 | 0.900 |" in md  
    assert "Generation quality" in md
    assert "Faithfulness" in md
    assert "1/2" in md  

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
    assert data["generation"]["mode"] == "hybrid+rerank"

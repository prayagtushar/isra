from pathlib import Path

from src.golden import GoldenItem, load_golden, matches, normalize


def test_normalize_strips_case_and_punctuation():
    assert normalize("Ola Electric") == "olaelectric"
    assert normalize("BYJU'S") == "byjus"
    assert normalize("olaelectric") == "olaelectric"


def test_matches_display_name_to_label():
    assert matches("olaelectric", "Ola Electric") is True
    assert matches("paytm", "PharmEasy") is False


def test_load_golden_parses_and_skips_blanks(tmp_path: Path):
    f = tmp_path / "g.jsonl"
    f.write_text(
        '{"question": "q1", "expected": "paytm"}\n'
        "\n"
        '{"question": "q2", "expected": "zomato"}\n'
    )
    items = load_golden(f)
    assert items == [
        GoldenItem(question="q1", expected="paytm"),
        GoldenItem(question="q2", expected="zomato"),
    ]

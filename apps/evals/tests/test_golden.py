from pathlib import Path

from src.golden import GoldenItem, load_golden, matched_expected, matches, normalize


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
        '{"question": "q1", "expected": ["paytm"]}\n'
        "\n"
        '{"question": "q2", "expected": ["zomato"]}\n'
    )
    items = load_golden(f)
    assert [i.question for i in items] == ["q1", "q2"]
    assert [i.expected for i in items] == [("paytm",), ("zomato",)]


def test_load_golden_accepts_bare_string_expected(tmp_path: Path):
    # The original golden set wrote `expected` as a single string; keep reading it.
    f = tmp_path / "g.jsonl"
    f.write_text('{"question": "q1", "expected": "paytm"}\n')
    (item,) = load_golden(f)
    assert item.expected == ("paytm",)


def test_load_golden_defaults_category_and_match(tmp_path: Path):
    f = tmp_path / "g.jsonl"
    f.write_text('{"question": "q1", "expected": ["paytm"]}\n')
    (item,) = load_golden(f)
    assert item.category == "direct"
    assert item.match == "any"


def test_load_golden_reads_category_and_match(tmp_path: Path):
    f = tmp_path / "g.jsonl"
    f.write_text(
        '{"question": "q1", "expected": ["coindcx", "coinswitchkuber"],'
        ' "category": "multi_hop", "match": "all"}\n'
    )
    (item,) = load_golden(f)
    assert item.category == "multi_hop"
    assert item.match == "all"
    assert item.expected == ("coindcx", "coinswitchkuber")


def test_item_with_no_expected_entities_is_unanswerable(tmp_path: Path):
    f = tmp_path / "g.jsonl"
    f.write_text('{"question": "q1", "expected": [], "category": "unanswerable"}\n')
    (item,) = load_golden(f)
    assert item.answerable is False


def test_item_with_expected_entities_is_answerable():
    assert GoldenItem(question="q", expected=("paytm",)).answerable is True


def test_matched_expected_returns_entities_found_in_names():
    item = GoldenItem(
        question="q", expected=("coindcx", "coinswitchkuber"), match="all"
    )
    found = matched_expected(item, ["CoinDCX", "Zomato"])
    assert found == {"coindcx"}


def test_matched_expected_is_empty_when_nothing_matches():
    item = GoldenItem(question="q", expected=("paytm",))
    assert matched_expected(item, ["Zomato", "Oyo"]) == set()


def test_shipped_golden_set_covers_every_category():
    items = load_golden()
    categories = {i.category for i in items}
    assert categories == {"direct", "paraphrase", "multi_hop", "unanswerable"}
    assert len(items) >= 40


def test_shipped_unanswerable_items_have_no_expected_entities():
    for item in load_golden():
        if item.category == "unanswerable":
            assert item.expected == ()
            assert item.answerable is False


def test_shipped_multi_hop_items_require_every_entity():
    multi_hop = [i for i in load_golden() if i.category == "multi_hop"]
    assert multi_hop
    for item in multi_hop:
        assert item.match == "all"
        # A single-entity "all" question is just a direct question mislabelled.
        assert len(item.expected) >= 2


def test_shipped_expected_entities_are_not_mutually_ambiguous():
    # `matches` is deliberately fuzzy; two expected entities matching each other would inflate recall.
    for item in load_golden():
        if item.match != "all":
            continue
        for a in item.expected:
            others = [b for b in item.expected if b != a]
            assert not any(matches(a, b) for b in others), f"{item.question}: {a}"

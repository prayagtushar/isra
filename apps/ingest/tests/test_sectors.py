"""Sector normalization.

The /startups filter shipped roughly sixty chips for a corpus of 111 companies,
including "E-Commerce" twice, "Medical Device" beside "Medical Devices", and
"Fintech" beside "Financial technology". Two sources disagree on vocabulary --
Wikipedia infoboxes say "Financial technology", Y Combinator says "Fintech" --
and nothing reconciled them, so the filter offered choices that were the same
choice.

These tests pin what may and may not be merged. Over-merging is the worse
failure: "Financial Services" and "Financial Technology" are different
businesses, and collapsing them would quietly lose information rather than
just look untidy.
"""

from src.sectors import normalize_sectors

class TestSpellingVariants:
    def test_collapses_fintech_onto_the_spelled_out_form(self):
        assert normalize_sectors(["Fintech", "Financial technology"]) == ["Financial Technology"]

    def test_collapses_ecommerce_however_it_is_hyphenated(self):
        assert normalize_sectors(["E-Commerce", "E-commerce", "Ecommerce", "e commerce"]) == [
            "E-Commerce"
        ]

    def test_collapses_a_singular_plural_pair(self):
        assert normalize_sectors(["Medical Device", "Medical Devices"]) == ["Medical Devices"]

    def test_collapses_b2b_ecommerce_spellings(self):
        assert normalize_sectors(["B2B E-Commerce", "B2B Ecommerce"]) == ["B2B E-Commerce"]

    def test_case_alone_never_produces_two_sectors(self):
        assert normalize_sectors(["HOSPITALITY", "hospitality", "Hospitality"]) == ["Hospitality"]

    def test_collapses_the_same_sector_named_at_three_lengths(self):
        """All three appeared in one corpus of 107 companies, each on a single
        company, so the filter listed three chips that meant one thing."""
        assert normalize_sectors(
            ["Social Network", "Social Network Service", "Social Networking Service"]
        ) == ["Social Network"]

    def test_corrects_a_misspelling_carried_in_from_the_source_page(self):
        assert normalize_sectors(["Informational Technology"]) == ["Information Technology"]

    def test_folds_a_narrower_restatement_into_its_sector(self):
        assert normalize_sectors(["Payments", "Payment Gateway"]) == ["Payments"]
        assert normalize_sectors(["Healthcare", "Healthcare Services"]) == ["Healthcare"]

class TestThingsThatMustStaySeparate:
    def test_keeps_financial_services_apart_from_financial_technology(self):
        """A bank and a payments startup are not the same sector. Tidiness is
        not worth merging them."""
        assert normalize_sectors(["Financial Services", "Fintech"]) == [
            "Financial Services",
            "Financial Technology",
        ]

    def test_keeps_healthcare_apart_from_health_technology(self):
        assert normalize_sectors(["Healthcare", "Healthtech"]) == [
            "Health Technology",
            "Healthcare",
        ]

class TestOutputShape:
    def test_sorts_so_the_filter_order_is_stable_between_ingests(self):
        assert normalize_sectors(["Retail", "Agriculture", "Fintech"]) == [
            "Agriculture",
            "Financial Technology",
            "Retail",
        ]

    def test_preserves_acronyms_rather_than_title_casing_them_to_mush(self):
        assert normalize_sectors(["b2b", "saas", "ai / gpt"]) == ["AI / GPT", "B2B", "SaaS"]

    def test_drops_empty_and_whitespace_only_entries(self):
        assert normalize_sectors(["Retail", "", "   ", None]) == ["Retail"]

    def test_leaves_an_unknown_sector_alone_apart_from_casing(self):
        """The map is a fixup list, not an allowlist. A sector nobody
        anticipated should still reach the filter."""
        assert normalize_sectors(["quantum computing"]) == ["Quantum Computing"]

from src.merge import merge_startups
from src.schema import Startup
from src.yc_scraper import _founded_year, build_startup

def _yc(**over):
    base = {
        "name": "Razorpay",
        "slug": "razorpay",
        "website": "https://razorpay.com",
        "one_liner": "Payments for businesses",
        "long_description": (
            "Razorpay is a full-stack financial services company that helps "
            "businesses accept, process and disburse payments."
        ),
        "industries": ["Fintech", "Payments"],
        "tags": ["SaaS"],
        "regions": ["India", "South Asia"],
        "all_locations": "Bengaluru, KA, India",
        "team_size": 3000,
        "batch": "Winter 2015",
        "top_company": True,
    }
    base.update(over)
    return base

def test_build_startup_maps_fields():
    s = build_startup(_yc())
    assert isinstance(s, Startup)
    assert s.name == "Razorpay"
    assert s.normalized_name == "razorpay"
    assert "financial services" in s.description
    assert s.sectors == ["Fintech", "Payments"]
    assert str(s.source_url) == "https://www.ycombinator.com/companies/razorpay"
    assert s.founded_year == 2015
    assert s.headquarters == "Bengaluru, KA, India"

def test_build_startup_fallback_description():
    s = build_startup(_yc(long_description="", one_liner=""))
    assert "Y Combinator" in s.description
    assert "Razorpay" in s.description

def test_founded_year_parses_batch():
    assert _founded_year("Summer 2012") == 2012
    assert _founded_year("Winter 2015") == 2015
    assert _founded_year(None) is None
    assert _founded_year("no-year") is None

def test_cross_source_merge_dedupes_by_name():
    # Same company from two sources should merge into one record.
    wiki = Startup(
        name="Razorpay",
        normalized_name="Razorpay",
        source_url="https://en.wikipedia.org/wiki/Razorpay",
        description="Short wiki blurb.",
        founders=["Harshil Mathur", "Shashank Kumar"],
        sectors=["Financial technology"],
        fundings=7_500_000_000.0,
    )
    yc = build_startup(_yc())
    merged = merge_startups([wiki, yc])
    assert len(merged) == 1
    m = merged[0]
    # longer description (YC) wins; sectors unioned; wiki funding preserved
    assert "financial services" in m.description
    assert {"Fintech", "Payments", "Financial technology"}.issubset(set(m.sectors))
    assert m.fundings == 7_500_000_000.0

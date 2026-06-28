

from src.scraper import (
    UnicornRecord,
    _clean,
    _parse_valuation,
    _split_multi,
    build_startup,
    parse_infobox,
    parse_unicorn_table,
)

LIST_HTML = """
<table class="wikitable">
  <tbody>
    <tr><th>Company</th><th>Valuation (US$ billions)</th><th>Valuation date</th>
        <th>Industry</th><th>Country/ countries</th><th>Founder(s)</th></tr>
    <tr>
      <td><a href="/wiki/Oyo_Rooms" title="Oyo">Oyo</a></td>
      <td>9.6</td>
      <td>August 2021<sup><a href="#cite_note-90">[90]</a></sup></td>
      <td><a href="/wiki/Hospitality">Hospitality</a></td>
      <td>India</td>
      <td>Ritesh Agarwal</td>
    </tr>
    <tr>
      <td>Razorpay</td>
      <td>7.5</td>
      <td>December 2021</td>
      <td><a href="/wiki/Financial_technology">Fintech</a>, <a href="/wiki/Payments">Payments</a></td>
      <td>India</td>
      <td>Harshil Mathur, Shashank Kumar</td>
    </tr>
    <tr>
      <td><a href="/wiki/Stripe">Stripe</a></td>
      <td>95</td>
      <td>2021</td>
      <td><a href="/wiki/Fintech">Fintech</a></td>
      <td>United States / Ireland</td>
      <td>Patrick Collison, John Collison</td>
    </tr>
  </tbody>
</table>
"""

ARTICLE_HTML = """
<div class="mw-parser-output">
  <table class="infobox">
    <tbody>
      <tr><th>Industry</th><td>Hospitality</td></tr>
      <tr><th>Founded</th><td>2012<span>; 14 years ago</span><sup><a href="#c">[1]</a></sup></td></tr>
      <tr><th>Founder</th><td>Ritesh Agarwal</td></tr>
      <tr><th>Headquarters</th><td>Gurgaon, Haryana, India<sup>[2]</sup></td></tr>
    </tbody>
  </table>
  <p>Oyo Rooms, commonly known as Oyo, is an Indian multinational hospitality
     chain of leased and franchised hotels, homes, and living spaces.</p>
</div>
"""

def test_clean_strips_citations_and_comma_spacing():
    assert _clean("Gurgaon , Haryana , India [ 2 ] [ 3 ]") == "Gurgaon, Haryana, India"

def test_split_multi():
    assert _split_multi("A, B; C & D [ 9 ]") == ["A", "B", "C", "D"]

def test_parse_valuation():
    assert _parse_valuation("9.6") == 9.6
    assert _parse_valuation("$1.2 [ 3 ]") == 1.2
    assert _parse_valuation("n/a") is None

def test_parse_unicorn_table_filters_india_and_extracts_fields():
    records = parse_unicorn_table(LIST_HTML)
    assert [r.name for r in records] == ["Oyo", "Razorpay"]  

    oyo, razorpay = records
    assert oyo.slug == "Oyo_Rooms"
    assert oyo.valuation == 9.6
    assert oyo.sectors == ["Hospitality"]
    assert oyo.founders == ["Ritesh Agarwal"]

    
    assert razorpay.slug is None
    assert razorpay.valuation == 7.5
    assert razorpay.sectors == ["Fintech", "Payments"]
    assert razorpay.founders == ["Harshil Mathur", "Shashank Kumar"]

def test_parse_infobox():
    info = parse_infobox(ARTICLE_HTML)
    assert info["founded_year"] == 2012
    assert info["headquarters"] == "Gurgaon, Haryana, India"
    assert info["founders"] == ["Ritesh Agarwal"]
    assert info["industry"] == ["Hospitality"]

def test_build_startup_without_article_synthesizes_description():
    record = UnicornRecord(
        name="Razorpay",
        slug=None,
        valuation=7.5,
        sectors=["Fintech", "Payments"],
        founders=["Harshil Mathur", "Shashank Kumar"],
    )
    s = build_startup(record)

    assert s.name == "Razorpay"
    assert s.normalized_name == "razorpay"
    assert s.fundings == 7.5e9  
    assert s.sectors == ["Fintech", "Payments"]
    assert s.founders == ["Harshil Mathur", "Shashank Kumar"]
    assert s.founded_year is None  
    assert "unicorn" in s.description.lower()
    
    assert str(s.source_url).rstrip("/").endswith("List_of_unicorn_startup_companies")

def test_build_startup_with_article_enriches_from_infobox_and_lead():
    record = UnicornRecord(
        name="Oyo",
        slug="Oyo_Rooms",
        valuation=9.6,
        sectors=["Hospitality"],
        founders=["Ritesh Agarwal"],
    )
    s = build_startup(record, ARTICLE_HTML)

    assert s.founded_year == 2012
    assert s.headquarters == "Gurgaon, Haryana, India"
    assert s.fundings == 9.6e9
    assert "hospitality chain" in s.description.lower()
    assert str(s.source_url).endswith("Oyo_Rooms")

def test_build_startup_defaults_founders_when_missing():
    record = UnicornRecord(name="Mystery", slug=None, valuation=None)
    s = build_startup(record)
    assert s.founders == ["Unknown"]  
    assert len(s.description) >= 5

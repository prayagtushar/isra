

from src.scraper import (
    UnicornRecord,
    _clean,
    _parse_valuation,
    _split_multi,
    build_startup,
    parse_infobox,
    parse_unicorn_table,
    resolve_slug,
    seed_details,
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

MISMATCHED_LINK_HTML = """
<table class="wikitable">
  <tbody>
    <tr><th>Company</th><th>Valuation (US$ billions)</th><th>Valuation date</th>
        <th>Industry</th><th>Country/ countries</th><th>Founder(s)</th></tr>
    <tr>
      <td><a href="//en.wikipedia.org/wiki/Ola_Electric" title="Ola Electric">Krutrim</a></td>
      <td>1+</td>
      <td>26 January 2024</td>
      <td><a href="/wiki/Artificial_intelligence">Artificial intelligence</a></td>
      <td>India</td>
      <td>Bhavish Aggarwal</td>
    </tr>
    <tr>
      <td><a href="/wiki/Ola_Cabs" title="Ola Cabs">Ola Consumer</a></td>
      <td>2.0</td>
      <td>2024</td>
      <td><a href="/wiki/Transport">Transport</a></td>
      <td>India</td>
      <td>Bhavish Aggarwal</td>
    </tr>
  </tbody>
</table>
"""

def test_parse_unicorn_table_rejects_link_to_unrelated_article():
    # A row can link to another company's article; a stub beats the wrong company's data.
    records = parse_unicorn_table(MISMATCHED_LINK_HTML)
    assert [r.name for r in records] == ["Krutrim", "Ola Consumer"]

    krutrim, ola_consumer = records
    assert krutrim.slug is None

    # Partial overlaps are legitimate ("Oyo" -> Oyo_Rooms) and must survive the guard.
    assert ola_consumer.slug == "Ola_Cabs"

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
    assert s.sectors == ["Financial Technology", "Payments"]
    assert s.founders == ["Harshil Mathur", "Shashank Kumar"]
    assert s.founded_year is None
    # The stub states facts about this company, not the word every record would share.
    assert "US$7.5 billion" in s.description
    assert "Harshil Mathur" in s.description


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

# --- list values split across markup, not commas ---

INFOBOX_LIST_MARKUP = """
<table class="infobox">
  <tbody>
    <tr><th>Industry</th><td><ul><li>Financial technology</li><li>Payments</li>
        <li>Adware</li></ul></td></tr>
    <tr><th>Founder</th><td>Vijay Shekhar Sharma</td></tr>
  </tbody>
</table>
"""

INFOBOX_BR_MARKUP = """
<table class="infobox">
  <tbody>
    <tr><th>Industry</th><td>Cloud computing<br/>Backup</td></tr>
    <tr><th>Founder</th><td>Jyoti Bansal<br/>Bipul Sinha</td></tr>
  </tbody>
</table>
"""

INFOBOX_CITED_LIST_MARKUP = """
<table class="infobox">
  <tbody>
    <tr><th>Industry</th><td><ul>
      <li>Financial technology<sup class="reference"><a href="#cite_note-1">[1]</a></sup></li>
      <li>Payments</li></ul></td></tr>
    <tr><th>Founder</th><td>Vijay Shekhar Sharma<sup>[2]</sup></td></tr>
  </tbody>
</table>
"""

def test_clean_strips_editorial_markers_not_just_numbered_footnotes():
    """[update]-style markers get embedded and rendered, not merely stored."""
    assert _clean("As of August 2024,[update] it operates 250 stores.[12]") == (
        "As of August 2024, it operates 250 stores."
    )
    assert _clean("It was profitable[citation needed] by 2023.") == (
        "It was profitable by 2023."
    )

def test_clean_keeps_brackets_that_are_part_of_the_text():
    """Markers are enumerated, so a bracket a company actually wrote is not deleted."""
    assert _clean("The product [Beta] shipped.") == "The product [Beta] shipped."

def test_parse_infobox_drops_citation_markers_from_a_list():
    """Citations go before separators, or <sup>[1]</sup> leaves "1" and "[" as sectors."""
    info = parse_infobox(INFOBOX_CITED_LIST_MARKUP)
    assert info["industry"] == ["Financial technology", "Payments"]
    assert info["founders"] == ["Vijay Shekhar Sharma"]

def test_parse_infobox_splits_a_list_of_industries():
    assert parse_infobox(INFOBOX_LIST_MARKUP)["industry"] == [
        "Financial technology",
        "Payments",
        "Adware",
    ]

def test_parse_infobox_splits_industries_separated_by_line_breaks():
    assert parse_infobox(INFOBOX_BR_MARKUP)["industry"] == ["Cloud computing", "Backup"]

def test_parse_infobox_splits_founders_separated_by_line_breaks():
    """Same defect, worse in founders: two people become one impossible name."""
    assert parse_infobox(INFOBOX_BR_MARKUP)["founders"] == ["Jyoti Bansal", "Bipul Sinha"]

TABLE_LIST_MARKUP = """
<table class="wikitable">
  <tbody>
    <tr><th>Company</th><th>Valuation</th><th>Date</th><th>Industry</th>
        <th>Country</th><th>Founder(s)</th></tr>
    <tr>
      <td>Zepto</td>
      <td>5</td>
      <td>2024</td>
      <td><ul><li>Retail</li><li>E-commerce</li></ul></td>
      <td>India</td>
      <td><ul><li>Aadit Palicha</li><li>Kaivalya Vohra</li></ul></td>
    </tr>
  </tbody>
</table>
"""

def test_parse_unicorn_table_splits_list_cells():
    record = parse_unicorn_table(TABLE_LIST_MARKUP)[0]
    assert record.sectors == ["Retail", "E-commerce"]
    assert record.founders == ["Aadit Palicha", "Kaivalya Vohra"]

def test_parse_unicorn_table_keeps_a_name_containing_a_comma_intact():
    """Splitting cells must not reach the name column."""
    html = TABLE_LIST_MARKUP.replace("<td>Zepto</td>", "<td>Zepto, Inc.</td>")
    assert parse_unicorn_table(html)[0].name == "Zepto, Inc."

# --- recovering an article the list page did not link ---

def _titles(
    *pages: tuple[str, bool],
    redirects: dict[str, str] | None = None,
    disambiguations: tuple[str, ...] = (),
) -> dict:
    """Shape of action=query&prop=info|pageprops&titles=...&redirects=1."""
    query: dict = {
        "pages": {
            str(index): (
                {
                    "title": title,
                    **(
                        {"pageprops": {"disambiguation": ""}}
                        if title in disambiguations
                        else {}
                    ),
                }
                if exists
                else {"title": title, "missing": ""}
            )
            for index, (title, exists) in enumerate(pages)
        }
    }
    if redirects:
        query["redirects"] = [{"from": k, "to": v} for k, v in redirects.items()]
    return {"query": query}

def test_resolve_slug_accepts_an_article_that_exists_under_the_company_name():
    assert resolve_slug("Zepto", _titles(("Zepto (company)", True))) == "Zepto_(company)"

def test_resolve_slug_returns_none_when_wikipedia_has_no_such_article():
    """The common case, not a bug: a third of the list has no article, and keeps its stub."""
    assert resolve_slug("Razorpay", _titles(("Razorpay", False))) is None
    assert resolve_slug("Razorpay", {}) is None

def test_resolve_slug_follows_a_redirect_even_to_an_unrecognizable_name():
    """A redirect is an editor asserting two names are one subject. Zomato became Eternal Limited."""
    resolved = resolve_slug(
        "Zomato", _titles(("Eternal Limited", True), redirects={"Zomato": "Eternal Limited"})
    )
    assert resolved == "Eternal_Limited"

WEBSITE_INFOBOX_MARKUP = """
<table class="infobox">
  <tbody>
    <tr><th>Type of site</th><td>Online food ordering</td></tr>
    <tr><th>Founded</th><td>2008</td></tr>
    <tr><th>Services</th><td>Food delivery<br/>Table reservation</td></tr>
  </tbody>
</table>
"""

def test_parse_infobox_reads_type_of_site_when_there_is_no_industry():
    """{{infobox website}} has no Industry row, which left Zomato with no sector at all."""
    assert parse_infobox(WEBSITE_INFOBOX_MARKUP)["industry"] == ["Online food ordering"]

def test_parse_infobox_prefers_industry_over_type_of_site():
    both = WEBSITE_INFOBOX_MARKUP.replace(
        "<tr><th>Founded</th>", "<tr><th>Industry</th><td>Hospitality</td></tr><tr><th>Founded</th>"
    )
    assert parse_infobox(both)["industry"] == ["Hospitality"]

def test_parse_infobox_ignores_services_which_are_products_not_sectors():
    """"Table reservation" is a feature, not a sector."""
    assert parse_infobox(WEBSITE_INFOBOX_MARKUP)["industry"] == ["Online food ordering"]

def test_seed_details_scrapes_by_name_and_skips_what_has_no_article():
    """A name with no article is skipped, not stubbed: a stub adds nothing to retrieve."""
    from unittest.mock import patch

    with (
        patch("src.scraper._lookup_slug", side_effect=lambda n: None if n == "Paytm" else n),
        patch("src.scraper._fetch", return_value=ARTICLE_HTML),
        patch("src.scraper.NOTABLE_NAMES", ["Paytm", "Oyo"]),
    ):
        result = seed_details()

    assert [s.name for s in result] == ["Oyo"]
    # Built through build_startup, so it carries the lead and infobox, not a raw dump.
    assert "hospitality chain" in result[0].description.lower()
    assert result[0].founded_year == 2012
    assert str(result[0].source_url).endswith("Oyo")

def test_resolve_slug_skips_a_disambiguation_page():
    """"Apna" reached the live corpus as "Apna or APNA can mean:" because the title matched."""
    resolved = resolve_slug("Apna", _titles(("Apna", True), disambiguations=("Apna",)))
    assert resolved is None

def test_resolve_slug_takes_the_company_page_beside_a_disambiguation_page():
    resolved = resolve_slug(
        "Apna",
        _titles(("Apna", True), ("Apna (company)", True), disambiguations=("Apna",)),
    )
    assert resolved == "Apna_(company)"

def test_resolve_slug_prefers_a_matching_title_over_a_redirect():
    """"Zepto" redirects to "Metric prefix"; the grocery company is at "Zepto (company)"."""
    resolved = resolve_slug(
        "Zepto",
        _titles(
            ("Metric prefix", True),
            ("Zepto (company)", True),
            redirects={"Zepto": "Metric prefix"},
        ),
    )
    assert resolved == "Zepto_(company)"

def test_resolve_slug_rejects_an_article_about_something_else():
    """Sharing a title is not being the same subject: "MPL" is a disambiguation page."""
    assert resolve_slug("Meesho", _titles(("Meerut", True))) is None

# --- the stub, when there is genuinely no article ----------------------------

def test_stub_description_states_facts_rather_than_repeating_itself():
    """The old second sentence was identical across every stub, so it distinguished none of them."""
    record = UnicornRecord(
        name="Zepto",
        slug=None,
        valuation=5.0,
        sectors=["Retail", "E-commerce"],
        founders=["Aadit Palicha", "Kaivalya Vohra"],
    )
    description = build_startup(record).description

    assert "Aadit Palicha" in description
    assert "5" in description
    assert "featured on Wikipedia's list" not in description

    # No shared filler either: a clause repeated across stubs is the same defect.
    assert "places it among" not in description
    assert "unicorns" not in description

def test_stub_description_holds_up_when_the_row_knows_almost_nothing():
    record = UnicornRecord(name="Mystery", slug=None, valuation=None)
    description = build_startup(record).description
    assert "Mystery" in description
    assert len(description) >= 5

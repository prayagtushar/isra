

from src.scraper import (
    UnicornRecord,
    _clean,
    _parse_valuation,
    _split_multi,
    build_startup,
    parse_infobox,
    parse_unicorn_table,
    resolve_slug,
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
    # Wikipedia's list sometimes links a company name to a *different*
    # company's article (e.g. "Krutrim" -> /wiki/Ola_Electric). Enriching from
    # that article contaminates the record, so the slug must be dropped —
    # a stub description beats the wrong company's data.
    records = parse_unicorn_table(MISMATCHED_LINK_HTML)
    assert [r.name for r in records] == ["Krutrim", "Ola Consumer"]

    krutrim, ola_consumer = records
    assert krutrim.slug is None

    # Partial overlaps are legitimate ("Ola Consumer" -> Ola_Cabs,
    # "Oyo" -> Oyo_Rooms) and must survive the guard.
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

# --- list values split across markup, not commas -----------------------------
#
# The fixtures above separate industries with commas, which is why the bug they
# were meant to cover went unnoticed for the whole corpus: real infoboxes use
# <br> or a <ul>, and get_text() with no separator argument joins the pieces
# with nothing at all. That produced sector chips like
# "Financial technologyPaymentsAdware" on the live site.

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
    """Only [1]-style footnotes were removed, so a description reached the
    corpus reading "As of August 2024,[update] ..." -- and the description is
    what gets embedded and rendered, not merely stored."""
    assert _clean("As of August 2024,[update] it operates 250 stores.[12]") == (
        "As of August 2024, it operates 250 stores."
    )
    assert _clean("It was profitable[citation needed] by 2023.") == (
        "It was profitable by 2023."
    )

def test_clean_keeps_brackets_that_are_part_of_the_text():
    """The marker list is enumerated rather than matched by shape, so a bracket
    a company actually wrote is not silently deleted."""
    assert _clean("The product [Beta] shipped.") == "The product [Beta] shipped."

def test_parse_infobox_drops_citation_markers_from_a_list():
    """A reference renders as <sup>[1]</sup>. Inserting separators at every node
    boundary first would turn it into "[, 1, ]", which the citation pattern no
    longer matches -- leaving "1" and "[" as sectors in their own right. So the
    citation has to be removed as markup, before the separators go in."""
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
    """Same defect, and worse when it lands in founders: two people become one
    person with an impossible name."""
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
    """Splitting cells must not reach the name column: separators are inserted
    at markup boundaries, and a name is one text node however it is punctuated."""
    html = TABLE_LIST_MARKUP.replace("<td>Zepto</td>", "<td>Zepto, Inc.</td>")
    assert parse_unicorn_table(html)[0].name == "Zepto, Inc."

# --- recovering an article the list page did not link ------------------------
#
# A row with no usable link meant no article fetch, so build_startup fell back
# to a generated stub. That happened for 32 of 111 companies, and those stubs
# are what /search returned: near-identical sentences with a name swapped in.
# Searching by name recovers most of them.

def _titles(*pages: tuple[str, bool], redirects: dict[str, str] | None = None) -> dict:
    """Shape of action=query&prop=info&titles=...&redirects=1."""
    query: dict = {
        "pages": {
            str(index): ({"title": title} if exists else {"title": title, "missing": ""})
            for index, (title, exists) in enumerate(pages)
        }
    }
    if redirects:
        query["redirects"] = [{"from": k, "to": v} for k, v in redirects.items()]
    return {"query": query}

def test_resolve_slug_accepts_an_article_that_exists_under_the_company_name():
    assert resolve_slug("Zepto", _titles(("Zepto (company)", True))) == "Zepto_(company)"

def test_resolve_slug_returns_none_when_wikipedia_has_no_such_article():
    """The common case, and not a bug: Wikipedia has no article for roughly a
    third of the companies on its own unicorn list. Those keep their stub."""
    assert resolve_slug("Razorpay", _titles(("Razorpay", False))) is None
    assert resolve_slug("Razorpay", {}) is None

def test_resolve_slug_follows_a_redirect_even_to_an_unrecognizable_name():
    """A redirect is an editor asserting that two names are one subject, which
    is the only reliable signal for a company that has been renamed. Zomato
    became Eternal Limited; no string comparison would connect those."""
    resolved = resolve_slug(
        "Zomato", _titles(("Eternal Limited", True), redirects={"Zomato": "Eternal Limited"})
    )
    assert resolved == "Eternal_Limited"

def test_resolve_slug_prefers_a_matching_title_over_a_redirect():
    """Real case, and the reason title matches are checked first: "Zepto"
    redirects to "Metric prefix" -- the SI unit -- while the grocery company
    lives at "Zepto (company)". Trusting the redirect first files an article
    about scientific notation under a startup's name."""
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
    """Wikipedia has an article at "MPL" -- a disambiguation page covering
    Muslim personal law among others -- and none for Mobile Premier League.
    Sharing a title is not being the same subject."""
    assert resolve_slug("Meesho", _titles(("Meerut", True))) is None

# --- the stub, when there is genuinely no article ----------------------------

def test_stub_description_states_facts_rather_than_repeating_itself():
    """The old stub's second sentence -- "It is featured on Wikipedia's list of
    unicorn startup companies" -- was identical across every stubbed record, so
    it added a strong shared signal to 32 chunks and helped distinguish none of
    them. Whatever the row does know goes in instead."""
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

def test_stub_description_holds_up_when_the_row_knows_almost_nothing():
    record = UnicornRecord(name="Mystery", slug=None, valuation=None)
    description = build_startup(record).description
    assert "Mystery" in description
    assert len(description) >= 5

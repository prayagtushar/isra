import copy
import re
from dataclasses import dataclass, replace
from datetime import datetime
from typing import List

import httpx
from bs4 import BeautifulSoup

from src.schema import Startup
from src.sectors import normalize_sectors

USER_AGENT = "ISRA-Bot/0.1 {+https://github.com/prayagtushar/isra.git}"

_LIST_URL = "https://en.wikipedia.org/wiki/List_of_unicorn_startup_companies"

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
# Footnotes and the editorial markers Wikipedia renders inline. Only numeric
# footnotes were stripped, so descriptions reached the corpus reading
# "As of August 2024,[update] the company..." -- and that text is what gets
# embedded and shown, not just stored. Enumerated rather than matched by shape,
# so a bracket a company actually wrote survives.
_CITATION = re.compile(
    r"\[\s*(?:\d+|[a-z]|note\s+\d+|update|citation needed|clarify|sic|"
    r"who\?|when\?|why\?|where\?|according to whom\?)\s*\]",
    re.IGNORECASE,
)
_SPLIT_RE = re.compile(r"[,;&]")

@dataclass(frozen=True)
class UnicornRecord:
    name: str
    slug: str | None = None
    valuation: float | None = None
    sectors: list[str] | None = None
    founders: list[str] | None = None

def _clean(value: str) -> str:
    value = _CITATION.sub("", value)
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+,", ",", value)
    value = re.sub(r",\s+", ", ", value)
    return value.strip(" ,;")

def _split_multi(value: str) -> list[str]:
    parts = _SPLIT_RE.split(value)
    return [_clean(p) for p in parts if _clean(p)]

def _list_cell(cell) -> list[str]:
    """Read a cell that holds several values, however the page separates them.

    Wikipedia writes multi-value cells three ways -- "a, b", "a<br>b", and a
    <ul> of <li> -- and get_text() with no separator concatenates the last two
    into one string. That is how the corpus ended up with a sector called
    "Financial technologyPaymentsAdware" and a founder called
    "Jyoti BansalBipul Sinha".

    Inserting a comma at every markup boundary turns all three spellings into
    the comma-separated case, which _split_multi already handles. Only cells
    that are genuinely lists get this treatment: doing it to a scalar cell
    would corrupt values that legitimately contain commas, such as a
    headquarters address.

    Citations are removed as markup, before the separators go in. A reference
    renders as <sup>[1]</sup>, and separating every node first turns it into
    "[, 1, ]" -- which the citation pattern no longer recognizes, so "1" and
    "[" survive as sectors of their own.
    """
    cell = copy.copy(cell)
    for sup in cell.find_all("sup"):
        sup.decompose()
    return [value for value in _split_multi(cell.get_text(separator=", ")) if _has_letter(value)]

def _has_letter(value: str) -> bool:
    """Reject fragments left by markup, e.g. a stray bracket or footnote number.
    A sector name contains a letter; punctuation and digits alone never do."""
    return any(char.isalpha() for char in value)

def _parse_valuation(value: str) -> float | None:
    value = _clean(value)
    match = re.search(r"[\d.]+", value)
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None

def _link_matches_name(name: str, slug: str, title: str) -> bool:
    """Guard against list rows whose link points at a different company's
    article (e.g. "Krutrim" linked to /wiki/Ola_Electric). The link target is
    trusted only if the company name and the article name overlap: one
    contains the other, or they share a token of >= 3 characters."""
    def norm(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.lower())

    name_n = norm(name)
    for target in (norm(slug), norm(title)):
        if not target:
            continue
        if name_n in target or target in name_n:
            return True
        for token in re.split(r"[^a-z0-9]+", name.lower()):
            if len(token) >= 3 and token in target:
                return True
    return False

def resolve_slug(name: str, query_json: dict) -> str | None:
    """Find the article for a company whose list row carried no usable link.

    Roughly a third of the rows link nowhere useful -- no link at all, or one
    _link_matches_name rejected as pointing at a different company -- and
    without an article those records fall back to a stub.

    This reads a title query (action=query&titles=...&redirects=1), not a
    full-text search. Full-text search was tried first and is unusable here: it
    ranks by relevance rather than identity, so "Razorpay India company"
    returns Cred, the Central Bank of India, and an article about fintech in
    India, with no mention of Razorpay at all. Picking from that list means
    filing one company's history under another company's name.

    A title query answers the only question worth asking -- does an article with
    this name exist -- and resolves redirects, which is what catches companies
    renamed since the list was written.

    Order matters, and it is the whole subtlety here. A matching title wins over
    a redirect, because a company name that collides with an ordinary word
    redirects somewhere useless: "Zepto" redirects to "Metric prefix", the SI
    unit, while the grocery company lives at "Zepto (company)". Only when no
    title matches is the redirect trusted -- and then it is trusted even if the
    target looks nothing like the name, because at that point an editor
    asserting the two names are one subject is the only evidence available, and
    it is how "Zomato" correctly reaches "Eternal Limited".

    Anything else returns None and the record keeps its stub.
    """
    if not name.strip():
        return None

    query = query_json.get("query") or {}
    target = re.sub(r"[^a-z0-9]", "", name.lower())

    for page in (query.get("pages") or {}).values():
        if "missing" in page:
            continue
        title = page.get("title") or ""
        # Article titles disambiguate with a parenthetical -- "Zepto (company)"
        # -- which should not count against the match.
        bare = re.sub(r"\s*\([^)]*\)\s*$", "", title)
        candidate = re.sub(r"[^a-z0-9]", "", bare.lower())
        if candidate and (target in candidate or candidate in target):
            return title.replace(" ", "_")

    # No article carries this name. A redirect is the remaining evidence.
    redirects = {r.get("from"): r.get("to") for r in query.get("redirects") or []}
    if name in redirects:
        return str(redirects[name]).replace(" ", "_")
    return None

def parse_unicorn_table(html: str) -> list[UnicornRecord]:
    """Extract Indian unicorn rows from the Wikipedia page.

    The page has several `wikitable`s (count-over-time, by-country, the main
    per-company list, and an exited-unicorns list). We scan every table and
    keep rows shaped like the per-company list (>= 6 cells, country in col 5).
    """
    soup = BeautifulSoup(html, "lxml")
    records: list[UnicornRecord] = []

    for table in soup.find_all("table", {"class": "wikitable"}):
        rows = table.find_all("tr")
        if len(rows) < 2:
            continue

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < 6:
                continue

            country = _clean(cells[4].get_text())
            if "india" not in country.lower():
                continue

            name_cell = cells[0]
            link = name_cell.find("a")
            name = _clean(name_cell.get_text())
            if not name:
                continue
            slug = link["href"].split("/wiki/")[-1] if link and link.get("href") else None
            if slug and not _link_matches_name(name, slug, link.get("title", "")):
                slug = None

            valuation = _parse_valuation(cells[1].get_text())
            sectors = _list_cell(cells[3])
            founders = _list_cell(cells[5]) or ["Unknown"]

            records.append(UnicornRecord(name=name, slug=slug, valuation=valuation, sectors=sectors, founders=founders))

    return records

def parse_infobox(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    info = {}
    infobox = soup.find("table", {"class": "infobox"})
    if not infobox:
        return info

    for row in infobox.find_all("tr"):
        header = row.find("th")
        data = row.find("td")
        if not header or not data:
            continue

        key = header.get_text(strip=True).lower()
        value = _clean(data.get_text())

        if key == "industry":
            info["industry"] = _list_cell(data)
        elif key == "founded":
            match = re.search(r"\b(\d{4})\b", value)
            if match:
                info["founded_year"] = int(match.group(1))
        elif key in ("founder", "founders"):
            info["founders"] = _list_cell(data)
        elif key == "headquarters":
            # Scalar, and commonly "City, State, Country" -- read without the
            # inserted separators so the address survives intact.
            info["headquarters"] = value

    return info

def _extract_lead(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header", "table"]):
        tag.decompose()
    paragraphs = soup.find_all("p")
    for p in paragraphs:
        text = re.sub(r"\s+", " ", p.get_text())
        text = _clean(text)
        if text:
            return text
    return ""

def _stub_description(record: UnicornRecord, info: dict) -> str:
    """Describe a company with only what its list row and infobox knew.

    The previous stub ended every record with the same sentence -- "It is
    featured on Wikipedia's list of unicorn startup companies." Repeated across
    32 of 111 records, that sentence became a substantial fraction of the
    embedded text and was identical in all of them, so it pulled those chunks
    together in vector space while telling a reader nothing. Retrieval for
    "fintech unicorn payments" returned three of them, indistinguishable.

    What the row does know -- valuation, founders, sector, year, headquarters --
    is specific per company, and answers questions the corpus is actually asked.
    """
    # Canonical spellings, so the prose matches the sector shown beside it.
    sectors = normalize_sectors(record.sectors or [])
    sentences = []

    opening = f"{record.name} is an Indian startup"
    if sectors:
        opening += f" in {_join(sectors)}"
    founded = info.get("founded_year")
    if founded:
        opening += f", founded in {founded}"
    sentences.append(opening + ".")

    if record.valuation:
        valuation = f"{record.valuation:g}"
        sentences.append(
            f"It is valued at about US${valuation} billion, which places it among "
            "India's unicorns."
        )

    founders = [f for f in (record.founders or info.get("founders") or []) if f != "Unknown"]
    if founders:
        sentences.append(f"{record.name} was founded by {_join(founders)}.")

    headquarters = info.get("headquarters")
    if headquarters:
        sentences.append(f"It is headquartered in {headquarters}.")

    return " ".join(sentences)

def _join(items: list[str]) -> str:
    """Comma-separate a list, with "and" before the last item."""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"

def build_startup(record: UnicornRecord, article_html: str | None = None) -> Startup:
    now = datetime.now()
    info = parse_infobox(article_html) if article_html else {}

    description = _extract_lead(article_html) if article_html else ""
    if not description:
        description = _stub_description(record, info)

    source_url = f"https://en.wikipedia.org/wiki/{record.slug}" if record.slug else _LIST_URL

    return Startup(
        name=record.name,
        normalized_name=record.name,
        source_url=source_url,
        description=description,
        founders=info.get("founders", record.founders or ["Unknown"]),
        sectors=info.get("industry", record.sectors or []),
        founded_year=info.get("founded_year"),
        headquarters=info.get("headquarters"),
        fundings=record.valuation * 1_000_000_000 if record.valuation else None,
        scraped_date=now,
    )

def _fetch(url: str) -> str:
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.text

def _lookup_slug(name: str) -> str | None:
    """Ask Wikipedia whether an article exists under this name. Best effort.

    Both spellings are queried in one request: the plain name, and the
    "(company)" form Wikipedia uses when a name is ambiguous.
    """
    params = {
        "action": "query",
        "prop": "info",
        "titles": f"{name}|{name} (company)",
        "redirects": "1",
        "format": "json",
    }
    try:
        with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30) as client:
            r = client.get("https://en.wikipedia.org/w/api.php", params=params)
            r.raise_for_status()
            return resolve_slug(name, r.json())
    except Exception as exc:
        print(f"article lookup failed for {name}: {exc}")
        return None

def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(separator=" ")).strip()

def scrape_wikipedia(startup_slug: str, startup_name: str) -> Startup:
    url = f"https://en.wikipedia.org/wiki/{startup_slug}"
    html = _fetch(url)
    text = _extract_text(html)
    description = " ".join(text.split()[:1000])

    return Startup(
        name=startup_name,
        normalized_name=startup_name,
        source_url=url,
        description=description,
        founders=["Unknown"],
        scraped_date=datetime.now(),
    )

def scrape_startups(limit: int | None = None, fetch_articles: bool = True) -> list[Startup]:
    """Scrape Indian unicorns from the Wikipedia list (richest valuations first).

    Fetches the list page once, parses the per-company table, dedupes by name,
    and (optionally) fetches each company's article for a real description.
    Article fetches are best-effort: failures fall back to a generated blurb.
    """
    records = parse_unicorn_table(_fetch(_LIST_URL))

    seen: set[str] = set()
    unique: list[UnicornRecord] = []
    for record in records:
        key = record.name.lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(record)

    if limit is not None:
        unique = unique[:limit]

    startups: list[Startup] = []
    stubbed: list[str] = []
    for record in unique:
        # A row that links nowhere useful used to go straight to a stub. Look
        # the title up first; resolve_slug rejects anything that does not name
        # this company, so it cannot enrich a record from a different one.
        slug = record.slug
        if fetch_articles and not slug:
            slug = _lookup_slug(record.name)
            if slug:
                record = replace(record, slug=slug)

        article_html = None
        if fetch_articles and slug:
            try:
                article_html = _fetch(f"https://en.wikipedia.org/wiki/{slug}")
            except Exception as exc:
                print(f"article fetch failed for {record.name}: {exc}")
        try:
            startup = build_startup(record, article_html)
            startups.append(startup)
            if not article_html:
                stubbed.append(record.name)
        except Exception as exc:
            print(f"skip {record.name}: {exc}")

    if stubbed:
        # Worth printing rather than swallowing: every name here is a company
        # whose only text is a generated stub, which is the ceiling on what
        # retrieval can do for it.
        print(f"no article found for {len(stubbed)}/{len(unique)}: {', '.join(stubbed)}")

    return startups

def seed_details() -> list[Startup]:
    slugs = [
        ("Ola_Electric", "Ola Electric"),
        ("Zomato", "Zomato"),
        ("Razorpay", "Razorpay"),
        ("Zerodha", "Zerodha"),
        ("PharmEasy", "PharmEasy"),
    ]

    result: list[Startup] = []
    for slug, name in slugs:
        try:
            result.append(scrape_wikipedia(slug, name))
        except Exception as e:
            print(f"Failed to scrape {slug}: {e}")
    return result

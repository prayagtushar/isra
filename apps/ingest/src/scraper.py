import re
from dataclasses import dataclass
from datetime import datetime
from typing import List

import httpx
from bs4 import BeautifulSoup

from src.schema import Startup

USER_AGENT = "ISRA-Bot/0.1 {+https://github.com/prayagtushar/isra.git}"

_LIST_URL = "https://en.wikipedia.org/wiki/List_of_unicorn_startup_companies"

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_CITATION = re.compile(r"\[\s*\d+\s*\]")
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
    value = re.sub(r"\s+,", ",", value)
    value = re.sub(r",\s+", ", ", value)
    return value.strip(" ,;")

def _split_multi(value: str) -> list[str]:
    parts = _SPLIT_RE.split(value)
    return [_clean(p) for p in parts if _clean(p)]

def _parse_valuation(value: str) -> float | None:
    value = _clean(value)
    match = re.search(r"[\d.]+", value)
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None

def parse_unicorn_table(html: str) -> list[UnicornRecord]:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", {"class": "wikitable"})
    if not table:
        return []

    rows = table.find_all("tr")
    if len(rows) < 2:
        return []

    records: list[UnicornRecord] = []
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
        slug = link["href"].split("/wiki/")[-1] if link and link.get("href") else None

        valuation = _parse_valuation(cells[1].get_text())
        sectors = _split_multi(cells[3].get_text())
        founders = _split_multi(cells[5].get_text()) or ["Unknown"]

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
            info["industry"] = _split_multi(value)
        elif key == "founded":
            match = re.search(r"\b(\d{4})\b", value)
            if match:
                info["founded_year"] = int(match.group(1))
        elif key == "founder":
            info["founders"] = _split_multi(value)
        elif key == "headquarters":
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

def build_startup(record: UnicornRecord, article_html: str | None = None) -> Startup:
    now = datetime.now()
    info = parse_infobox(article_html) if article_html else {}

    description = _extract_lead(article_html) if article_html else ""
    if not description:
        sectors = record.sectors or ["its sector"]
        description = (
            f"{record.name} is an Indian unicorn startup "
            f"operating in {', '.join(sectors)}. "
            "It is featured on Wikipedia's list of unicorn startup companies."
        )

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

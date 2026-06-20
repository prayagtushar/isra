import re
import httpx
from typing import List
from bs4 import BeautifulSoup

from src.schema import Startup

USER_AGENT = "ISRA-Bot/0.1 {+https://github.com/prayagtushar/isra.git}"


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
    )


def seed_details() -> List[Startup]:
    slugs = [
        ("Ola_Electric", "Ola Electric"),
        ("Zomato", "Zomato"),
        ("Razorpay", "Razorpay"),
        ("Zerodha", "Zerodha"),
        ("PharmEasy", "PharmEasy"),
    ]

    result: List[Startup] = []
    for slug, name in slugs:
        try:
            result.append(scrape_wikipedia(slug, name))
        except Exception as e:
            print(f"Failed to scrape {slug}: {e}")
    return result

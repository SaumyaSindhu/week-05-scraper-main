"""
Stage 2: read a catalogue page — which books are listed, where's "next".
Stage 3: read a book detail page into the eight raw fields.

Selectors are aimed at specific product/detail elements, not "the first
thing that looks like a price" — that breaks the day the page changes.
"""

from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .schema import RawBookRecord


def parse_catalogue_page(html: str, page_url: str):
    """Returns (book_urls: list[str], next_url: str | None)."""
    soup = BeautifulSoup(html, "html.parser")

    book_urls = []
    for article in soup.select("article.product_pod"):
        link = article.select_one("h3 a")
        if link and link.get("href"):
            # Always resolve via URL tools — never by gluing strings.
            book_urls.append(urljoin(page_url, link["href"]))

    next_link = soup.select_one("li.next a")
    next_url = urljoin(page_url, next_link["href"]) if next_link and next_link.get("href") else None

    return book_urls, next_url


def parse_book_page(html: str, book_url: str, source_page: str) -> RawBookRecord:
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.select_one("div.product_main h1")
    title = title_el.get_text(strip=True) if title_el else ""

    price_el = soup.select_one("p.price_color")
    price_text = price_el.get_text(strip=True) if price_el else ""

    availability_el = soup.select_one("p.availability")
    availability_text = availability_el.get_text(strip=True) if availability_el else ""

    rating_el = soup.select_one("p.star-rating")
    rating_text = ""
    if rating_el and rating_el.get("class"):
        rating_text = next((c for c in rating_el.get("class") if c != "star-rating"), "")

    # The description is the paragraph right after the #product_description
    # heading block. Some books simply don't have one — store null, never
    # invent text that wasn't on the page.
    description_el = soup.select_one("#product_description ~ p")
    description = description_el.get_text(strip=True) if description_el else None

    return RawBookRecord(
        title=title,
        product_url=book_url,
        price_text=price_text,
        availability_text=availability_text,
        rating_text=rating_text,
        description=description,
        source_page=source_page,
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )

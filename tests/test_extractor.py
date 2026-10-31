import os

from src.extractor import parse_book_page, parse_catalogue_page
from src.normalize import normalize_record

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def load_fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return f.read()


def test_relative_links_become_absolute_urls():
    html = load_fixture("catalogue_page.html")
    urls, next_url = parse_catalogue_page(html, "https://books.toscrape.com/catalogue/page-1.html")

    assert len(urls) == 2
    assert all(u.startswith("https://books.toscrape.com/") for u in urls)
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_missing_description_is_none():
    html = load_fixture("book_page_no_description.html")
    record = parse_book_page(
        html,
        "https://books.toscrape.com/catalogue/no-desc_1/index.html",
        "https://books.toscrape.com/catalogue/page-1.html",
    )
    assert record.description is None


def test_description_present_and_whitespace_cleaned():
    html = load_fixture("book_page_with_description.html")
    record = parse_book_page(
        html,
        "https://books.toscrape.com/catalogue/with-desc_1/index.html",
        "https://books.toscrape.com/catalogue/page-1.html",
    )
    normalized = normalize_record(record)
    assert normalized.description == "This is a sample   description with   extra whitespace."
    assert normalized.price_gbp == 51.77
    assert normalized.rating_text == "Three"


def test_malformed_page_missing_price_fails_normalization():
    html = load_fixture("book_page_malformed.html")
    raw = parse_book_page(
        html,
        "https://books.toscrape.com/catalogue/malformed_1/index.html",
        "https://books.toscrape.com/catalogue/page-1.html",
    )
    # Extraction never crashes — it just records an empty price_text.
    assert raw.price_text == ""

    # Normalization is where a bad record gets caught, per Stage 4.
    try:
        normalize_record(raw)
        assert False, "expected normalize_record to raise on an empty price"
    except ValueError:
        pass

import re

from .schema import BookRecord, RawBookRecord

PRICE_RE = re.compile(r"[\d.]+")


def normalize_price(price_text: str) -> float:
    """'£51.77' -> 51.77. Raises ValueError if no number is found."""
    match = PRICE_RE.search(price_text)
    if not match:
        raise ValueError(f"Could not parse a price from '{price_text}'")
    return float(match.group())


def normalize_record(raw: RawBookRecord) -> BookRecord:
    price_gbp = normalize_price(raw.price_text)
    return BookRecord(
        title=raw.title.strip(),
        product_url=raw.product_url,
        price_text=raw.price_text,
        price_gbp=price_gbp,
        availability_text=" ".join(raw.availability_text.split()),
        rating_text=raw.rating_text.strip(),
        description=raw.description.strip() if raw.description else None,
        source_page=raw.source_page,
        fetched_at=raw.fetched_at,
    )

"""
Stage 4: the schema is the recipe. RawBookRecord is exactly what Stage 3
scraped off the page — strings, untouched. BookRecord is what's allowed
into books.json: typed, validated, with the original text kept alongside
the clean value.
"""

from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator


class RawBookRecord(BaseModel):
    title: str
    product_url: str
    price_text: str
    availability_text: str
    rating_text: str
    description: Optional[str] = None
    source_page: str
    fetched_at: str


class BookRecord(BaseModel):
    title: str
    product_url: HttpUrl          # canonical identity of the record
    price_text: str               # raw text kept side-by-side with...
    price_gbp: float              # ...the clean numeric value
    availability_text: str
    rating_text: str
    description: Optional[str] = None
    source_page: HttpUrl
    fetched_at: str

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v

    @field_validator("price_gbp")
    @classmethod
    def price_not_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price_gbp must not be negative")
        return v

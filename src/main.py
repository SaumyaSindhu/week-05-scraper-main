"""
Orchestrates the whole pipeline: fetch -> extract -> normalize ->
validate -> store -> report. Run with:

    python -m src.main

Set INJECT_BROKEN_URL=1 to add one deliberately fake book URL and prove
Stage 5's checkpoint: the run still finishes, 60 good records still
survive, and run-report.json shows failed_pages: 1.
"""

import json
import os
from datetime import datetime, timezone

from pydantic import ValidationError

from . import config
from .extractor import parse_book_page, parse_catalogue_page
from .fetcher import FetchError, fetch
from .normalize import normalize_record
from .report import write_run_report
from .utils import dedupe_preserve_order


def run():
    start_time = datetime.now(timezone.utc)
    stats = {
        "catalogue_pages": 0,
        "discovered_urls": 0,
        "pages_fetched": 0,
        "cache_hits": 0,
        "valid_records": 0,
        "invalid_records": 0,
        "failed_pages": 0,
    }

    # ---- Stage 2: discover book URLs across the first 3 catalogue pages ----
    all_book_urls = []
    source_of = {}  # book_url -> catalogue page it was found on
    page_url = f"{config.BASE_URL}/catalogue/page-1.html"
    pages_visited = 0

    while page_url and pages_visited < config.MAX_CATALOGUE_PAGES:
        cache_key = f"catalogue-page-{pages_visited + 1}"
        try:
            html = fetch(page_url, cache_key, stats)
        except FetchError as exc:
            print(f"FAILED     {page_url}  ({exc})")
            stats["failed_pages"] += 1
            break

        urls, next_url = parse_catalogue_page(html, page_url)
        for u in urls:
            source_of.setdefault(u, page_url)
        all_book_urls.extend(urls)

        pages_visited += 1
        stats["catalogue_pages"] = pages_visited
        page_url = next_url

    unique_urls = dedupe_preserve_order(all_book_urls)
    stats["discovered_urls"] = len(unique_urls)

    print(
        f"\ncatalogue_pages={stats['catalogue_pages']} "
        f"discovered={len(all_book_urls)} unique_urls={len(unique_urls)}\n"
    )

    if os.getenv("INJECT_BROKEN_URL") == "1":
        fake_url = f"{config.BASE_URL}/catalogue/this-book-does-not-exist_9999/index.html"
        unique_urls.append(fake_url)
        source_of[fake_url] = "manual-test-injection"
        print(f"INJECTED   {fake_url}  (Stage 5 failure test)\n")

    # ---- Stage 3 & 4: extract, normalize, validate every book page ----
    valid_records = []
    invalid_entries = []

    for i, book_url in enumerate(unique_urls, start=1):
        cache_key = f"book-{i:03d}"
        try:
            html = fetch(book_url, cache_key, stats)
        except FetchError as exc:
            stats["failed_pages"] += 1
            invalid_entries.append({"url": book_url, "reason": str(exc)})
            continue

        try:
            raw = parse_book_page(html, book_url, source_page=source_of.get(book_url, book_url))
            record = normalize_record(raw)
        except (ValidationError, ValueError) as exc:
            stats["invalid_records"] += 1
            invalid_entries.append({"url": book_url, "reason": str(exc)})
            continue

        valid_records.append(record)

    # ---- Stage 4: store, de-duplicated by canonical URL (idempotent) ----
    dedup = {}
    for r in valid_records:
        dedup[str(r.product_url)] = r
    final_records = list(dedup.values())
    stats["valid_records"] = len(final_records)

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    books_path = os.path.join(config.OUTPUT_DIR, "books.json")
    with open(books_path, "w", encoding="utf-8") as f:
        json.dump([r.model_dump(mode="json") for r in final_records], f, indent=2)

    errors_path = os.path.join(config.OUTPUT_DIR, "errors.json")
    with open(errors_path, "w", encoding="utf-8") as f:
        json.dump(invalid_entries, f, indent=2)

    print(f"Wrote {len(final_records)} records to {books_path}")
    print(f"Wrote {len(invalid_entries)} errors to {errors_path}")

    # ---- Stage 5: report ----
    write_run_report(stats, start_time)


if __name__ == "__main__":
    run()

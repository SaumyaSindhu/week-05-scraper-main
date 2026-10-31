# The polite scraper — Books to Scrape

A small pipeline that downloads the first 3 catalogue pages of
[Books to Scrape](https://books.toscrape.com), visits all 60 book pages,
and turns the messy HTML into clean, schema-checked JSON — politely, and
without crashing on a broken page.

## Target classification (Stage 0)

- **Site:** `books.toscrape.com` — a public sandbox built specifically so
  people can practise scraping. [toscrape.com](https://toscrape.com)
  states this directly.
- **Scope:** the first 3 catalogue pages only (60 books total). No other
  pages, no other site.
- **Data collected:** title, price, availability, star rating, and
  description for each book — all publicly rendered on the page the
  server sends, nothing behind a login or paywall.
- **robots.txt result:** `GET https://books.toscrape.com/robots.txt -> 404`.
  No robots file found. A missing file is not permission — it's just a
  missing file — but combined with the sandbox's own stated purpose,
  scraping the first 3 catalogue pages here is appropriate.
- **Why this is appropriate:** the site exists for exactly this purpose,
  the scope is small and fixed, and every request identifies itself.

> I will not reuse this code on another site without checking its rules
> and terms first.

## Lane & install

Python 3.10+.

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run it

```bash
python -m src.main
```

First run prints `FETCH` for every page and writes `cache/`. Run it
again and you'll see `CACHE HIT` instead — the site is only asked once
per page while you're developing.

**Stage 5 failure-injection checkpoint** (adds one fake book URL on
purpose, on your own machine, never against the live site more than
necessary):

```bash
INJECT_BROKEN_URL=1 python -m src.main
```

`books.json` still ends up with 60 good records; `run-report.json`
shows `"failed_pages": 1`.

### Tests

```bash
pytest
```

## Politeness rules this scraper follows

- **User-Agent:** every real request identifies itself as
  `FlyRankInternshipA9/1.0 (+link-to-your-repo)` — set in `src/config.py`.
- **Timeout:** every request gives up after 10 seconds rather than
  hanging forever.
- **Delay:** at least 600ms between real network requests. Cached pages
  cost nothing and add no delay.
- **Caching:** every fetched page is saved to `cache/` and read from
  disk on subsequent runs, so the site is only touched once per page.
- **Status checks:** only `200` is treated as success. `404`/`403` are
  never retried; `5xx` and timeouts get one retry.

## Record schema (Stage 4)

Raw fields extracted per book (`RawBookRecord` in `src/schema.py`):

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "...",
  "source_page": "https://books.toscrape.com/catalogue/page-1.html",
  "fetched_at": "2026-08-06T10:00:00Z"
}
```

Clean, validated fields stored in `output/books.json` (`BookRecord`):
same as above, plus a numeric `price_gbp` (e.g. `51.77`) sitting
alongside the original `price_text`. `product_url` is each record's
canonical identity — a rerun updates, never duplicates.

Records that fail validation go to `output/errors.json` with a reason
instead of silently disappearing.

## Run report — real output

Clean run against the live site (first run, cold cache). Note
`pages_fetched: 63` = 3 catalogue pages + 60 book detail pages, not a
bug — `discovered_urls` and `valid_records` are the numbers that track
the actual book count:

```json
{
  "start_time": "2026-08-17T09:56:56.759360+00:00",
  "end_time": "2026-08-17T10:00:30.102217+00:00",
  "duration_seconds": 213.34,
  "catalogue_pages": 3,
  "discovered_urls": 60,
  "pages_fetched": 63,
  "cache_hits": 0,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

Clean rerun (warm cache — proves idempotency, Stage 1/4):

```json
{
  "start_time": "2026-08-17T10:04:04.832299+00:00",
  "end_time": "2026-08-17T10:04:05.755111+00:00",
  "duration_seconds": 0.92,
  "catalogue_pages": 3,
  "discovered_urls": 60,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0
}
```

Stage 5 failure-injection run (`INJECT_BROKEN_URL=1`, one fake book URL
added on purpose) — the run still finishes and the 60 good records
survive:

```json
{
  "start_time": "2026-08-17T10:01:27.013863+00:00",
  "end_time": "2026-08-17T10:01:30.705395+00:00",
  "duration_seconds": 3.69,
  "catalogue_pages": 3,
  "discovered_urls": 60,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1
}
```

## Why no browser was needed

Books to Scrape renders every field directly in the HTML the server
sends — view-source shows the same title, price, and description
`BeautifulSoup` parses here. A headless browser would only add startup
cost and memory for zero extra data.

## Ethics note

- Use an official API when one exists, instead of scraping.
- Never bypass logins, paywalls, CAPTCHAs, or explicit blocks.
- Collect only the fields you actually need, at the smallest scope that
  does the job.
- Treat every scraped page as untrusted input — validate before storing.

## Known limitation

The retry logic gives one flat retry on timeouts/5xx with no exponential
backoff and doesn't read the `Retry-After` header — that's the upgrade
A16 (next week's assignment) asks for. For a small, fixed-size sandbox
run like this one, a single retry was enough; it wouldn't be enough for
a larger or less predictable target.

## Project structure

```
scraper/
├── src/
│   ├── config.py         # target, politeness constants, paths
│   ├── fetcher.py         # Stage 1 + 5: fetch, cache, retry rules
│   ├── extractor.py       # Stage 2 + 3: catalogue + book page parsing
│   ├── schema.py           # Stage 4: RawBookRecord / BookRecord
│   ├── normalize.py        # Stage 4: price parsing, cleanup
│   ├── report.py           # Stage 5: run-report.json
│   ├── check_robots.py     # Stage 0: run once by hand
│   └── main.py              # orchestrates the whole pipeline
├── tests/                  # unit tests + HTML fixtures
├── cache/                  # gitignored — saved HTML pages
├── output/                 # books.json, errors.json, run-report.json
└── requirements.txt
```

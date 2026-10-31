"""
Stage 1 + Stage 5: fetch a page politely, cache it to disk, and never
crash the whole run over one bad page.

Politeness rules enforced here, in one place:
- identifying User-Agent on every real request
- a timeout so a hung request can't hang the whole run
- a status-code check before anything else happens
- at least DELAY_SECONDS between real requests (cache hits are free)
- retry once on timeout/5xx; never retry 404 (doesn't exist) or 403 (told no)
"""

import os
import time
import requests

from . import config


class FetchError(Exception):
    def __init__(self, message, status_code=None, retryable=False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


def _cache_path(cache_key: str) -> str:
    os.makedirs(config.CACHE_DIR, exist_ok=True)
    safe_name = cache_key.replace("/", "_").replace(":", "_")
    return os.path.join(config.CACHE_DIR, f"{safe_name}.html")


def fetch(url: str, cache_key: str, stats: dict) -> str:
    """Return the HTML for `url`, using the on-disk cache when present."""
    path = _cache_path(cache_key)

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"CACHE HIT  {url}  ({len(html)} bytes)")
        stats["cache_hits"] += 1
        return html

    last_error = None

    for attempt in range(1, config.RETRY_ATTEMPTS + 1):
        try:
            response = requests.get(
                url,
                headers={"User-Agent": config.USER_AGENT},
                timeout=config.TIMEOUT_SECONDS,
            )
        except requests.exceptions.Timeout:
            last_error = FetchError(f"Timeout fetching {url}", retryable=True)
        except requests.exceptions.RequestException as exc:
            last_error = FetchError(f"Network error fetching {url}: {exc}", retryable=True)
        else:
            status = response.status_code

            if status == 200:
                html = response.text
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"FETCH      {url}  ({len(html)} bytes, status {status})")
                stats["pages_fetched"] += 1
                time.sleep(config.DELAY_SECONDS)
                return html

            if status in (404, 403):
                # Not found or explicitly forbidden — asking again won't help.
                time.sleep(config.DELAY_SECONDS)
                raise FetchError(
                    f"Status {status} for {url}", status_code=status, retryable=False
                )

            if 500 <= status < 600:
                last_error = FetchError(
                    f"Status {status} for {url}", status_code=status, retryable=True
                )
            else:
                time.sleep(config.DELAY_SECONDS)
                raise FetchError(
                    f"Unexpected status {status} for {url}", status_code=status, retryable=False
                )

        time.sleep(config.DELAY_SECONDS)
        if attempt < config.RETRY_ATTEMPTS:
            print(f"RETRY      {url}  (attempt {attempt} failed: {last_error})")

    raise last_error

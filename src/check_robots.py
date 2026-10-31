"""
Stage 0. Run this once by hand:

    python -m src.check_robots

Paste whatever it prints into the README's "Target classification"
section. A missing robots.txt is not permission — it's just a missing
file — so note that honestly if it happens.
"""

import requests

from . import config

ROBOTS_URL = f"{config.BASE_URL}/robots.txt"


def main():
    try:
        response = requests.get(
            ROBOTS_URL,
            headers={"User-Agent": config.USER_AGENT},
            timeout=config.TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as exc:
        print(f"Could not fetch {ROBOTS_URL}: {exc}")
        return

    print(f"GET {ROBOTS_URL} -> {response.status_code}")
    if response.status_code == 200 and response.text.strip():
        print("--- robots.txt content ---")
        print(response.text)
    else:
        print(
            "No robots file found (or an empty/non-200 response). "
            "A missing file is not permission — it's just a missing file."
        )


if __name__ == "__main__":
    main()

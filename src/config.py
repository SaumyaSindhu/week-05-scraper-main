"""
All the numbers and strings that make this scraper polite live here,
in one place, so Stage 5's politeness rules are easy to audit.
"""

import os

BASE_URL = "https://books.toscrape.com"

# Change the repo link before you publish — this is how a site owner
# who sees this in their logs can find out who you are.
USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/yourusername/your-repo)"

TIMEOUT_SECONDS = 10
DELAY_SECONDS = 0.6          # only applied between *real* network requests
MAX_CATALOGUE_PAGES = 3
RETRY_ATTEMPTS = 2           # 1 initial try + 1 retry, only for timeouts/5xx

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(PROJECT_ROOT, "cache")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")

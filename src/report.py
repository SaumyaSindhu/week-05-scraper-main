import json
import os
from datetime import datetime, timezone

from . import config


def write_run_report(stats: dict, start_time: datetime) -> dict:
    end_time = datetime.now(timezone.utc)
    report = {
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": round((end_time - start_time).total_seconds(), 2),
        "catalogue_pages": stats["catalogue_pages"],
        "discovered_urls": stats["discovered_urls"],
        "pages_fetched": stats["pages_fetched"],
        "cache_hits": stats["cache_hits"],
        "valid_records": stats["valid_records"],
        "invalid_records": stats["invalid_records"],
        "failed_pages": stats["failed_pages"],
    }

    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    path = os.path.join(config.OUTPUT_DIR, "run-report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n--- RUN REPORT ---")
    print(json.dumps(report, indent=2))
    return report

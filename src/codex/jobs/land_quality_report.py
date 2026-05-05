from __future__ import annotations

import json
from pathlib import Path

from codex.services.land_quality_checks import run_land_quality_checks
from codex.services.land_storage import merge_land_records


OUTPUT_PATH = Path("data/storage/reports/land_quality_report.json")


def run() -> None:
    items = merge_land_records()
    report = run_land_quality_checks(items)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\nSaved report → {OUTPUT_PATH}")


if __name__ == "__main__":
    run()

from __future__ import annotations

import json
from pathlib import Path

from codex.services.city_divergence_index import compute_city_divergence_index
from codex.services.sqlite_land_warehouse import city_land_summary


OUTPUT_PATH = Path("data/storage/reports/city_divergence_report.json")


def run() -> None:
    summary = city_land_summary()
    ranking = compute_city_divergence_index(summary)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(ranking, file, ensure_ascii=False, indent=2)

    print(json.dumps(ranking, ensure_ascii=False, indent=2))
    print(f"\nSaved report → {OUTPUT_PATH}")


if __name__ == "__main__":
    run()

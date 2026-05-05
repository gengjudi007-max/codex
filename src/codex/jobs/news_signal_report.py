from __future__ import annotations

import json
from pathlib import Path

from codex.services.news_signal_detector import detect_news_signals
from codex.services.sqlite_land_warehouse import query_land_records


OUTPUT_PATH = Path("data/storage/reports/news_signal_report.json")


def run(limit: int = 200) -> None:
    records = query_land_records(limit=limit)
    signals = detect_news_signals(records)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(signals, file, ensure_ascii=False, indent=2)

    print(json.dumps(signals, ensure_ascii=False, indent=2))
    print(f"\nSaved report → {OUTPUT_PATH}")


if __name__ == "__main__":
    run()

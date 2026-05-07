from __future__ import annotations

import json
from pathlib import Path

from codex.services.city_divergence_index import compute_city_divergence_index
from codex.services.final_story_engine import generate_final_story
from codex.services.news_signal_detector import detect_news_signals
from codex.services.sqlite_land_warehouse import city_land_summary, query_land_records


OUTPUT_DIR = Path("data/storage/newsroom")


TOPIC = "核心城市土地市场分化加剧"


def run() -> None:
    records = query_land_records(limit=500)
    summary = city_land_summary()
    ranking = compute_city_divergence_index(summary)
    signals = detect_news_signals(records)

    article = generate_final_story(
        topic=TOPIC,
        signals=signals,
        city_ranking=ranking,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "daily_story.json"

    with path.open("w", encoding="utf-8") as file:
        json.dump(article, file, ensure_ascii=False, indent=2)

    print(json.dumps(article, ensure_ascii=False, indent=2))
    print(f"\nSaved story → {path}")


if __name__ == "__main__":
    run()

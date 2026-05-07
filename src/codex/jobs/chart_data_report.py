from __future__ import annotations

import json
from pathlib import Path

from codex.services.chart_data_builder import (
    build_city_ranking_chart_data,
    build_floor_price_chart_data,
)
from codex.services.city_divergence_index import compute_city_divergence_index
from codex.services.sqlite_land_warehouse import city_land_summary


OUTPUT_DIR = Path("data/storage/chart_data")


def run() -> None:
    summary = city_land_summary()
    ranking = compute_city_divergence_index(summary)

    charts = {
        "city_divergence_ranking": build_city_ranking_chart_data(ranking),
        "avg_floor_price": build_floor_price_chart_data(summary),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, payload in charts.items():
        path = OUTPUT_DIR / f"{name}.json"
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
        print(f"Saved chart data → {path}")


if __name__ == "__main__":
    run()

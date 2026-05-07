from __future__ import annotations

import json
from pathlib import Path

from codex.services.city_divergence_index import compute_city_divergence_index
from codex.services.html_dashboard_renderer import render_dashboard
from codex.services.news_signal_detector import detect_news_signals
from codex.services.sqlite_land_warehouse import city_land_summary, query_land_records


OUTPUT_PATH = Path("data/storage/dashboard/newsroom_dashboard.html")


def run() -> None:
    records = query_land_records(limit=500)
    summary = city_land_summary()
    ranking = compute_city_divergence_index(summary)
    signals = detect_news_signals(records)

    cards = [
        {
            "title": "城市分化排行榜",
            "content": json.dumps(ranking[:10], ensure_ascii=False, indent=2),
        },
        {
            "title": "新闻信号",
            "content": json.dumps(signals[:20], ensure_ascii=False, indent=2),
        },
        {
            "title": "最近土地数据",
            "content": json.dumps(records[:20], ensure_ascii=False, indent=2),
        },
    ]

    render_dashboard(
        title="Codex Newsroom Dashboard",
        cards=cards,
        output_path=OUTPUT_PATH,
    )

    print(f"Dashboard generated → {OUTPUT_PATH}")


if __name__ == "__main__":
    run()

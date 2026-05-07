from __future__ import annotations

import json
from pathlib import Path

from codex.connectors.city_land_sources import get_city_land_sources
from codex.connectors.generic_land_connector import fetch_generic_html_table


OUTPUT = Path("data/processed/all_city_land_items.json")


def run():
    sources = get_city_land_sources()
    all_items = []

    for source in sources:
        print(f"Fetching: {source.city}")
        items = fetch_generic_html_table(source)
        print(f"  -> {len(items)} rows")
        all_items.extend(items)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump({"items": all_items}, f, ensure_ascii=False, indent=2)

    print(f"\nTotal {len(all_items)} items saved → {OUTPUT}")


if __name__ == "__main__":
    run()

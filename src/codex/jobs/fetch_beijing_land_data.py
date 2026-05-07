from __future__ import annotations

import json
from pathlib import Path

from codex.connectors.beijing_land_connector import fetch_beijing_land_items


OUTPUT = Path("data/processed/beijing_land_items.json")


def run():
    items = fetch_beijing_land_items()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump({"items": items}, f, ensure_ascii=False, indent=2)

    print(f"Fetched {len(items)} Beijing land items → {OUTPUT}")


if __name__ == "__main__":
    run()

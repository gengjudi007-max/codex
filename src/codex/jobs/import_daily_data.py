from __future__ import annotations

import json
from pathlib import Path
from typing import List

from codex.services.data_ingestion_engine import build_default_engine, data_items_to_dicts


DEFAULT_IMPORT_DIR = Path("data/import")
DEFAULT_OUTPUT = Path("data/processed/daily_items.json")


def run_import(input_dir: Path = DEFAULT_IMPORT_DIR, output_file: Path = DEFAULT_OUTPUT) -> Path:
    engine = build_default_engine()

    items = []

    for file in input_dir.glob("*"):
        if file.suffix.lower() == ".csv":
            items.extend(engine.import_csv(file, source_name="Wind", category="market_data"))
        elif file.suffix.lower() == ".json":
            items.extend(engine.import_json(file, source_name="中指研究院", category="market_data"))

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", encoding="utf-8") as f:
        json.dump({"items": data_items_to_dicts(items)}, f, ensure_ascii=False, indent=2)

    print(f"Imported {len(items)} items → {output_file}")

    return output_file


if __name__ == "__main__":
    run_import()

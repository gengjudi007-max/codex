from __future__ import annotations

import argparse
from pathlib import Path

from codex.services.sqlite_land_warehouse import insert_land_records, load_land_json


DEFAULT_INPUT = Path("data/processed/beijing_land_items.json")


def run(input_path: Path = DEFAULT_INPUT) -> int:
    records = load_land_json(input_path)
    count = insert_land_records(records)
    print(f"Loaded {count} land records into data/storage/codex.db from {input_path}")
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description="Load land json into SQLite warehouse")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Input land json file")
    args = parser.parse_args()
    run(Path(args.input))


if __name__ == "__main__":
    main()

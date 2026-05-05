from __future__ import annotations

from pathlib import Path

from codex.services.land_data_parser import convert_land_csv_to_json


DEFAULT_INPUT = Path("data/import/land/land_data.csv")
DEFAULT_OUTPUT = Path("data/processed/land_items.json")


def run():
    output = convert_land_csv_to_json(DEFAULT_INPUT, DEFAULT_OUTPUT)
    print(f"Land data converted → {output}")


if __name__ == "__main__":
    run()

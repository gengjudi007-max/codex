from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import List

from codex.services.data_ingestion_engine import (
    build_default_engine,
    data_items_to_dicts,
)
from codex.services.daily_newsroom_pipeline import run_daily_newsroom_pipeline
from codex.services.storage import save_daily_run_result


def run(
    input_files: List[Path],
    output_dir: Path,
    include_example_fetchers: bool = False,
) -> dict:
    engine = build_default_engine(include_example_fetchers=include_example_fetchers)

    items = []
    for file in input_files:
        if file.suffix.lower() == ".csv":
            items.extend(engine.import_csv(file, source_name="Wind", category="market_data"))
        elif file.suffix.lower() == ".json":
            items.extend(engine.import_json(file, source_name="中指研究院", category="market_data"))

    input_dicts = data_items_to_dicts(items)

    result = run_daily_newsroom_pipeline(
        input_items=input_dicts,
        draft_depth="deep",
    )

    result["date"] = datetime.now().strftime("%Y-%m-%d")

    paths = save_daily_run_result(result, base_dir=output_dir)

    print("\n=== DAILY RUN COMPLETED ===")
    print("topics:", len(result.get("daily_topics", [])))
    print("articles:", len(result.get("generated_articles", [])))
    print("saved:", paths)

    return result


def main():
    parser = argparse.ArgumentParser(description="Run codex daily newsroom pipeline")
    parser.add_argument(
        "--input",
        nargs="+",
        default=["data/samples/cities.json"],
        help="Input data files (CSV/JSON)",
    )
    parser.add_argument(
        "--output",
        default="data/storage",
        help="Output directory",
    )
    parser.add_argument(
        "--use-example-fetcher",
        action="store_true",
        help="Enable example policy fetcher",
    )

    args = parser.parse_args()

    input_files = [Path(p) for p in args.input]
    output_dir = Path(args.output)

    run(input_files, output_dir, include_example_fetchers=args.use_example_fetcher)


if __name__ == "__main__":
    main()

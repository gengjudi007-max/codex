from __future__ import annotations

import argparse
import json
from pathlib import Path

from codex.services.reporter_style_engine import build_style_revision_report


DEFAULT_INPUT = Path("data/storage/articles.jsonl")


def run(input_path: Path) -> None:
    if not input_path.exists():
        print(f"File not found: {input_path}")
        return

    text = input_path.read_text(encoding="utf-8")
    report = build_style_revision_report(text)

    print(json.dumps(report, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Review newsroom style and AI traces")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="Input article file")
    args = parser.parse_args()
    run(Path(args.input))


if __name__ == "__main__":
    main()

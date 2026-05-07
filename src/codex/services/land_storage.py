from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_STORAGE_DIR = Path("data/storage/land")


def save_land_records(city: str, records: List[Dict[str, Any]]) -> Path:
    DEFAULT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = DEFAULT_STORAGE_DIR / f"{city}_land_{timestamp}.json"
    with path.open("w", encoding="utf-8") as file:
        json.dump(records, file, ensure_ascii=False, indent=2)
    return path


def merge_land_records() -> List[Dict[str, Any]]:
    DEFAULT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    merged: List[Dict[str, Any]] = []
    for path in sorted(DEFAULT_STORAGE_DIR.glob("*_land_*.json")):
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, list):
                merged.extend(data)
        except Exception:
            continue
    return merged

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_STORAGE_DIR = Path("data/storage")


class JsonStorage:
    """轻量级 JSONL 存储层。

    用于保存：
    - 城市数据记录；
    - 采访素材；
    - 每日选题；
    - 成稿结果；
    - 终检报告。

    该层先采用本地 JSONL，便于调试和版本迁移；后续可替换为 SQLite/PostgreSQL。
    """

    def __init__(self, base_dir: Path | str = DEFAULT_STORAGE_DIR) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def append(self, namespace: str, record: Dict[str, Any]) -> Path:
        path = self._path(namespace)
        payload = self._normalize(record)
        payload.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
        with path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return path

    def extend(self, namespace: str, records: List[Dict[str, Any]]) -> Path:
        path = self._path(namespace)
        with path.open("a", encoding="utf-8") as file:
            for record in records:
                payload = self._normalize(record)
                payload.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
                file.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return path

    def read_all(self, namespace: str) -> List[Dict[str, Any]]:
        path = self._path(namespace)
        if not path.exists():
            return []
        rows = []
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows

    def write_snapshot(self, namespace: str, payload: Dict[str, Any], name: Optional[str] = None) -> Path:
        folder = self.base_dir / namespace
        folder.mkdir(parents=True, exist_ok=True)
        filename = name or datetime.now().strftime("%Y%m%d_%H%M%S.json")
        path = folder / filename
        with path.open("w", encoding="utf-8") as file:
            json.dump(self._normalize(payload), file, ensure_ascii=False, indent=2)
        return path

    def _path(self, namespace: str) -> Path:
        safe = namespace.replace("/", "_")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        return self.base_dir / f"{safe}.jsonl"

    def _normalize(self, value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, dict):
            return {key: self._normalize(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._normalize(item) for item in value]
        if isinstance(value, Path):
            return str(value)
        return value


def save_daily_run_result(result: Dict[str, Any], base_dir: Path | str = DEFAULT_STORAGE_DIR) -> Dict[str, str]:
    storage = JsonStorage(base_dir)
    date = result.get("date") or datetime.now().strftime("%Y-%m-%d")
    daily_path = storage.write_snapshot("daily_runs", result, name=f"{date}.json")

    topics = result.get("daily_topics", [])
    articles = result.get("generated_articles", [])
    if topics:
        storage.extend("topics", topics)
    if articles:
        storage.extend("articles", articles)

    return {
        "daily_run": str(daily_path),
        "topics": str(storage._path("topics")),
        "articles": str(storage._path("articles")),
    }

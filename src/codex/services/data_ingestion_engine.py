from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from codex.services.source_whitelist import validate_source_name


@dataclass
class DataItem:
    category: str  # policy | announcement | financial | land | transaction | price | market_data
    title: str
    content: str
    source: str
    url: Optional[str]
    city: Optional[str]
    company: Optional[str]
    date: str
    raw: Dict[str, Any]
    metrics: Optional[Dict[str, Any]] = None
    source_level: Optional[str] = None
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


Fetcher = Callable[[], List[Dict[str, Any]]]
Parser = Callable[[Dict[str, Any]], Optional[DataItem]]


class DataIngestionEngine:
    """多源数据抓取、导入与解析总线。

    现实使用方式：
    - 政府、交易所、自然资源和住建部门：可逐步实现 fetcher/parser；
    - Wind、同花顺、东方财富、DM、中指、CRIC、贝壳：优先通过 CSV/JSON 导入；
    - 所有来源先过白名单校验，再转为统一 DataItem。
    """

    def __init__(self) -> None:
        self._sources: Dict[str, Dict[str, Any]] = {}

    def register_source(
        self,
        name: str,
        category: str,
        fetcher: Optional[Fetcher] = None,
        parser: Optional[Parser] = None,
        usage: Optional[str] = None,
    ) -> None:
        check = validate_source_name(name, usage=usage)
        if not check.get("allowed"):
            raise ValueError(f"来源不允许接入：{name}，原因：{check.get('reason')}")
        self._sources[name] = {
            "name": name,
            "category": category,
            "fetcher": fetcher,
            "parser": parser,
            "usage": usage,
            "source_level": check.get("level"),
        }

    def ingest(self) -> List[DataItem]:
        results: List[DataItem] = []
        for source_name, config in self._sources.items():
            fetcher: Optional[Fetcher] = config.get("fetcher")
            parser: Optional[Parser] = config.get("parser")
            if not fetcher:
                continue
            try:
                raw_items = fetcher() or []
            except Exception:
                continue
            for raw in raw_items:
                item = parser(raw) if parser else self._default_parse(raw, source_name, config.get("category"))
                if item:
                    if not item.source_level:
                        item.source_level = config.get("source_level")
                    results.append(item)
        return results

    def import_external_dataset(
        self,
        name: str,
        dataset: List[Dict[str, Any]],
        category: str,
        usage: Optional[str] = None,
    ) -> List[DataItem]:
        check = validate_source_name(name, usage=usage)
        if not check.get("allowed"):
            raise ValueError(f"来源不允许导入：{name}，原因：{check.get('reason')}")
        items: List[DataItem] = []
        for row in dataset:
            item = self._default_parse(row, name, category)
            if item:
                item.source_level = str(check.get("level"))
                item.verified = bool(row.get("verified", True))
                items.append(item)
        return items

    def import_csv(
        self,
        path: Path | str,
        source_name: str,
        category: str,
        usage: Optional[str] = None,
        encoding: str = "utf-8-sig",
    ) -> List[DataItem]:
        rows = read_csv_rows(path, encoding=encoding)
        return self.import_external_dataset(source_name, rows, category=category, usage=usage)

    def import_json(
        self,
        path: Path | str,
        source_name: str,
        category: str,
        usage: Optional[str] = None,
    ) -> List[DataItem]:
        rows = read_json_items(path)
        return self.import_external_dataset(source_name, rows, category=category, usage=usage)

    def _default_parse(self, raw: Dict[str, Any], source: str, category: str) -> Optional[DataItem]:
        title = str(raw.get("title") or raw.get("name") or _build_title(raw)).strip()
        content = str(raw.get("content") or raw.get("summary") or _build_content(raw)).strip()
        if not (title or content):
            return None
        return DataItem(
            category=category,
            title=title,
            content=content,
            source=raw.get("source") or source,
            url=raw.get("url"),
            city=raw.get("city"),
            company=raw.get("company"),
            date=raw.get("date") or raw.get("period") or datetime.now().strftime("%Y-%m-%d"),
            raw=raw,
            metrics=extract_metrics_from_row(raw),
            source_level=raw.get("source_level"),
            verified=bool(raw.get("verified", False)),
        )


def read_csv_rows(path: Path | str, encoding: str = "utf-8-sig") -> List[Dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding=encoding, newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def read_json_items(path: Path | str) -> List[Dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if isinstance(data, dict) and "items" in data:
        return list(data["items"])
    if isinstance(data, list):
        return data
    return []


def load_items_from_paths(paths: Iterable[Path | str]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for path in paths:
        path = Path(path)
        if path.suffix.lower() == ".csv":
            items.extend(read_csv_rows(path))
        elif path.suffix.lower() == ".json":
            items.extend(read_json_items(path))
    return items


def extract_metrics_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {}
    skip = {"title", "name", "content", "summary", "source", "source_level", "url", "city", "company", "date", "period", "category", "type", "verified", "notes"}
    for key, value in row.items():
        if key in skip or value in [None, ""]:
            continue
        parsed = _to_number(value)
        if parsed is not None:
            metrics[key] = parsed
    return metrics


def data_items_to_dicts(items: List[DataItem]) -> List[Dict[str, Any]]:
    return [item.to_dict() for item in items]


def _build_title(row: Dict[str, Any]) -> str:
    city = row.get("city") or ""
    metric = row.get("metric") or row.get("category") or row.get("type") or "房地产数据"
    period = row.get("period") or row.get("date") or ""
    return f"{city}{period}{metric}".strip()


def _build_content(row: Dict[str, Any]) -> str:
    city = row.get("city") or "相关城市"
    parts = [f"{city}房地产相关数据"]
    for key in ["new_home_area_yoy", "secondhand_area_yoy", "price_mom", "premium_rate", "inventory_months"]:
        if key in row and row[key] not in [None, ""]:
            parts.append(f"{key}={row[key]}")
    return "，".join(parts)


def _to_number(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if not isinstance(value, str):
        return None
    cleaned = value.strip().replace("%", "").replace(",", "")
    if cleaned == "":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


# 示例 fetcher/parser，真实使用时替换为政府RSS、交易所公告索引或手工导出数据。
def example_policy_fetcher() -> List[Dict[str, Any]]:
    return [
        {
            "title": "某地发布房地产新政",
            "content": "调整限购、信贷等措施",
            "url": "https://example.gov.cn/policy/123",
            "city": "某城市",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "verified": False,
        }
    ]


def example_policy_parser(raw: Dict[str, Any]) -> Optional[DataItem]:
    return DataItem(
        category="policy",
        title=raw.get("title", ""),
        content=raw.get("content", ""),
        source="地方政府官网",
        url=raw.get("url"),
        city=raw.get("city"),
        company=None,
        date=raw.get("date") or datetime.now().strftime("%Y-%m-%d"),
        raw=raw,
        metrics=extract_metrics_from_row(raw),
        source_level="level_2",
        verified=bool(raw.get("verified", False)),
    )


def build_default_engine(include_example_fetchers: bool = False) -> DataIngestionEngine:
    engine = DataIngestionEngine()
    engine.register_source(
        name="地方政府官网",
        category="policy",
        fetcher=example_policy_fetcher if include_example_fetchers else None,
        parser=example_policy_parser if include_example_fetchers else None,
        usage="local_policy",
    )
    for name in ["上交所", "深交所", "港交所"]:
        engine.register_source(name=name, category="announcement", usage="announcement")
    for name in ["Wind", "同花顺", "东方财富", "DM", "中指研究院", "CRIC"]:
        engine.register_source(name=name, category="market_data", usage="market_data")
    engine.register_source(name="贝壳研究院", category="market_data", usage="secondhand_market")
    engine.register_source(name="地方自然资源和规划部门", category="land", usage="land_transaction")
    engine.register_source(name="地方住建部门", category="transaction", usage="transaction_data")
    return engine

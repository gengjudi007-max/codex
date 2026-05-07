from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


FIELD_ALIASES = {
    "city": ["城市", "所在城市", "city"],
    "district": ["区县", "区域", "district"],
    "date": ["日期", "成交日期", "统计日期", "date", "period"],
    "new_home_units": ["新房成交套数", "商品住宅成交套数", "新建商品住宅成交套数", "new_home_units"],
    "new_home_area": ["新房成交面积", "商品住宅成交面积", "新建商品住宅成交面积", "new_home_area"],
    "secondhand_units": ["二手房成交套数", "存量房成交套数", "二手住宅成交套数", "secondhand_units"],
    "secondhand_area": ["二手房成交面积", "存量房成交面积", "二手住宅成交面积", "secondhand_area"],
    "new_home_units_yoy": ["新房成交套数同比", "商品住宅成交套数同比", "new_home_units_yoy"],
    "new_home_area_yoy": ["新房成交面积同比", "商品住宅成交面积同比", "new_home_area_yoy"],
    "secondhand_units_yoy": ["二手房成交套数同比", "secondhand_units_yoy"],
    "secondhand_area_yoy": ["二手房成交面积同比", "secondhand_area_yoy"],
    "source": ["来源", "source"],
    "url": ["链接", "url"],
}

METRIC_FIELDS = [
    "new_home_units",
    "new_home_area",
    "secondhand_units",
    "secondhand_area",
    "new_home_units_yoy",
    "new_home_area_yoy",
    "secondhand_units_yoy",
    "secondhand_area_yoy",
]


def parse_transaction_rows(rows: Iterable[Dict[str, Any]], default_source: str = "手动导入") -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for row in rows:
        normalized = normalize_transaction_row(row)
        city = normalized.get("city")
        if not city:
            continue
        metrics = {field: normalized.get(field) for field in METRIC_FIELDS if normalized.get(field) is not None}
        if not metrics:
            continue
        items.append(
            {
                "category": "transaction",
                "title": f"{city}{normalized.get('date') or ''}房地产成交数据",
                "content": build_transaction_content(normalized),
                "city": city,
                "date": normalized.get("date"),
                "source": normalized.get("source") or default_source,
                "source_level": guess_source_level(normalized.get("source") or default_source),
                "url": normalized.get("url"),
                "verified": True,
                "metrics": metrics,
                "raw": normalized,
            }
        )
    return items


def normalize_transaction_row(row: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for target, aliases in FIELD_ALIASES.items():
        value = first_present(row, aliases)
        if target in METRIC_FIELDS:
            normalized[target] = to_number(value)
        else:
            normalized[target] = clean_text(value)
    return normalized


def read_transaction_csv(path: Path | str, encoding: str = "utf-8-sig") -> List[Dict[str, Any]]:
    path = Path(path)
    with path.open("r", encoding=encoding, newline="") as file:
        return list(csv.DictReader(file))


def convert_transaction_csv_to_json(
    input_path: Path | str,
    output_path: Path | str,
    default_source: str = "手动导入",
) -> Path:
    rows = read_transaction_csv(input_path)
    items = parse_transaction_rows(rows, default_source=default_source)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump({"items": items}, file, ensure_ascii=False, indent=2)
    return output_path


def build_transaction_content(row: Dict[str, Any]) -> str:
    parts = []
    if row.get("new_home_units") is not None:
        parts.append(f"新房成交{row['new_home_units']}套")
    if row.get("new_home_area") is not None:
        parts.append(f"新房成交面积{row['new_home_area']}")
    if row.get("secondhand_units") is not None:
        parts.append(f"二手房成交{row['secondhand_units']}套")
    if row.get("secondhand_area") is not None:
        parts.append(f"二手房成交面积{row['secondhand_area']}")
    for key, label in [
        ("new_home_area_yoy", "新房成交面积同比"),
        ("secondhand_area_yoy", "二手房成交面积同比"),
    ]:
        if row.get(key) is not None:
            parts.append(f"{label}{row[key]}%")
    return "，".join(parts) + "。" if parts else "房地产成交数据。"


def first_present(row: Dict[str, Any], aliases: List[str]) -> Any:
    for alias in aliases:
        if alias in row and row[alias] not in [None, ""]:
            return row[alias]
    return None


def clean_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def to_number(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace("%", "")
    if text in ["-", "--", "—"]:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def guess_source_level(source: str) -> str:
    if any(keyword in source for keyword in ["住建", "政府", "房管", "统计局"]):
        return "level_2"
    if any(keyword in source for keyword in ["中指", "CRIC", "Wind", "同花顺", "贝壳"]):
        return "level_3"
    return "level_3"

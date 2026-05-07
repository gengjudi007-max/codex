from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


FIELD_ALIASES = {
    "city": ["城市", "所在城市", "city"],
    "district": ["区县", "区域", "板块", "district"],
    "land_name": ["地块名称", "宗地名称", "土地名称", "land_name", "name"],
    "land_code": ["地块编号", "宗地编号", "编号", "land_code"],
    "land_use": ["规划用途", "土地用途", "用途", "land_use"],
    "land_area": ["总用地面积(㎡)", "总用地面积", "建设用地面积", "成交土地建设用地面积", "land_area"],
    "planned_gfa": ["规划建筑面积(㎡)", "规划建筑面积", "规划建面", "planned_gfa"],
    "transaction_date": ["成交时间", "成交日期", "transaction_date", "date"],
    "buyer": ["竞得方", "竞得人", "拿地企业", "buyer"],
    "land_amount": ["成交价(万元)", "成交价", "成交土地出让金", "土地出让金", "land_amount"],
    "floor_price": ["成交楼面价(元/㎡)", "成交楼面价", "楼面价", "floor_price"],
    "premium_rate": ["溢价率(%)", "平均溢价率", "成交土地平均溢价率", "溢价率", "premium_rate"],
    "start_price": ["起始价(万元)", "起始价", "挂牌价", "start_price"],
    "transaction_status": ["交易状态", "状态", "transaction_status"],
    "source": ["来源", "source"],
    "url": ["链接", "url"],
}


LAND_METRIC_FIELDS = [
    "land_area",
    "planned_gfa",
    "land_amount",
    "floor_price",
    "premium_rate",
    "start_price",
]


def parse_land_rows(rows: Iterable[Dict[str, Any]], default_source: str = "手动导入") -> List[Dict[str, Any]]:
    """将土地表格行转换为系统 DataItem 风格字典。"""
    items: List[Dict[str, Any]] = []
    for row in rows:
        normalized = normalize_land_row(row)
        city = normalized.get("city")
        if not city:
            continue

        metrics = {field: normalized.get(field) for field in LAND_METRIC_FIELDS if normalized.get(field) is not None}
        title_parts = [city]
        if normalized.get("district"):
            title_parts.append(str(normalized["district"]))
        if normalized.get("land_name"):
            title_parts.append(str(normalized["land_name"]))

        items.append(
            {
                "category": "land",
                "title": "-".join(title_parts),
                "content": build_land_content(normalized),
                "city": city,
                "date": normalized.get("transaction_date"),
                "source": normalized.get("source") or default_source,
                "source_level": guess_source_level(normalized.get("source") or default_source),
                "url": normalized.get("url"),
                "verified": True,
                "metrics": metrics,
                "raw": normalized,
            }
        )
    return items


def normalize_land_row(row: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for target, aliases in FIELD_ALIASES.items():
        value = first_present(row, aliases)
        if target in LAND_METRIC_FIELDS:
            normalized[target] = to_number(value)
        else:
            normalized[target] = clean_text(value)
    return normalized


def read_land_csv(path: Path | str, encoding: str = "utf-8-sig") -> List[Dict[str, Any]]:
    path = Path(path)
    with path.open("r", encoding=encoding, newline="") as file:
        return list(csv.DictReader(file))


def convert_land_csv_to_json(
    input_path: Path | str,
    output_path: Path | str,
    default_source: str = "手动导入",
) -> Path:
    rows = read_land_csv(input_path)
    items = parse_land_rows(rows, default_source=default_source)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump({"items": items}, file, ensure_ascii=False, indent=2)
    return output_path


def build_land_content(row: Dict[str, Any]) -> str:
    parts = []
    if row.get("land_name"):
        parts.append(f"地块名称为{row['land_name']}")
    if row.get("land_use"):
        parts.append(f"规划用途为{row['land_use']}")
    if row.get("buyer"):
        parts.append(f"竞得方为{row['buyer']}")
    if row.get("land_amount") is not None:
        parts.append(f"成交价为{row['land_amount']}万元")
    if row.get("floor_price") is not None:
        parts.append(f"成交楼面价为{row['floor_price']}元/平方米")
    if row.get("premium_rate") is not None:
        parts.append(f"溢价率为{row['premium_rate']}%")
    return "，".join(parts) + "。" if parts else "土地成交数据。"


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
    if any(keyword in source for keyword in ["自然资源", "住建", "政府", "交易所"]):
        return "level_2"
    if any(keyword in source for keyword in ["中指", "CRIC", "Wind", "同花顺", "贝壳"]):
        return "level_3"
    return "level_3"

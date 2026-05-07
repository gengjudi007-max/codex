from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


CITY_DIMENSIONS = [
    "transaction",
    "price",
    "policy",
    "land",
    "inventory",
    "company_activity",
    "secondhand_market",
]


@dataclass
class CityRealEstateRecord:
    """城市级房地产数据库单条记录。"""

    city: str
    province: Optional[str]
    period: str
    source: str
    source_level: str
    dimension: str
    metric: str
    value: Optional[float]
    unit: Optional[str]
    yoy: Optional[float] = None
    mom: Optional[float] = None
    raw_text: Optional[str] = None
    url: Optional[str] = None
    verified: bool = False
    notes: Optional[str] = None


class CityRealEstateDatabase:
    """城市级房地产数据库。

    设计目标：
    - 将北京、上海、广州、深圳、杭州、武汉等城市的成交、价格、政策、土地、库存等数据统一入库；
    - 支持按城市、维度、时间段查询；
    - 支持输出城市画像，供分化分析引擎调用。
    """

    def __init__(self) -> None:
        self.records: List[CityRealEstateRecord] = []

    def add_record(self, record: CityRealEstateRecord) -> None:
        if record.dimension not in CITY_DIMENSIONS:
            raise ValueError(f"未知城市数据维度：{record.dimension}")
        self.records.append(record)

    def add_records(self, records: List[CityRealEstateRecord]) -> None:
        for record in records:
            self.add_record(record)

    def import_rows(self, rows: List[Dict[str, Any]]) -> None:
        for row in rows:
            self.add_record(
                CityRealEstateRecord(
                    city=row.get("city", "未知城市"),
                    province=row.get("province"),
                    period=row.get("period", "unknown"),
                    source=row.get("source", "unknown"),
                    source_level=row.get("source_level", "unknown"),
                    dimension=row.get("dimension", "transaction"),
                    metric=row.get("metric", "unknown"),
                    value=_as_float(row.get("value")),
                    unit=row.get("unit"),
                    yoy=_as_float(row.get("yoy")),
                    mom=_as_float(row.get("mom")),
                    raw_text=row.get("raw_text"),
                    url=row.get("url"),
                    verified=bool(row.get("verified", False)),
                    notes=row.get("notes"),
                )
            )

    def query(
        self,
        city: Optional[str] = None,
        dimension: Optional[str] = None,
        period: Optional[str] = None,
        metric: Optional[str] = None,
        verified_only: bool = False,
    ) -> List[Dict[str, Any]]:
        result = []
        for record in self.records:
            if city and record.city != city:
                continue
            if dimension and record.dimension != dimension:
                continue
            if period and record.period != period:
                continue
            if metric and record.metric != metric:
                continue
            if verified_only and not record.verified:
                continue
            result.append(asdict(record))
        return result

    def city_profile(self, city: str, period: Optional[str] = None) -> Dict[str, Any]:
        rows = self.query(city=city, period=period) if period else self.query(city=city)
        profile: Dict[str, Any] = {
            "city": city,
            "period": period,
            "dimensions": {dimension: [] for dimension in CITY_DIMENSIONS},
            "data_gaps": [],
        }
        for row in rows:
            profile["dimensions"].setdefault(row["dimension"], []).append(row)

        for dimension in CITY_DIMENSIONS:
            if not profile["dimensions"].get(dimension):
                profile["data_gaps"].append(f"缺少{dimension}维度数据")
        return profile

    def profiles(self, cities: List[str], period: Optional[str] = None) -> List[Dict[str, Any]]:
        return [self.city_profile(city, period=period) for city in cities]


def build_city_records_from_data_items(items: List[Dict[str, Any]]) -> List[CityRealEstateRecord]:
    """将数据抓取引擎输出转为城市数据库记录。"""
    records: List[CityRealEstateRecord] = []
    for item in items:
        city = item.get("city")
        if not city:
            continue
        category = item.get("category") or item.get("type") or "transaction"
        metrics = item.get("metrics", {}) or {}
        source = item.get("source", "unknown")
        source_level = item.get("source_level", "unknown")
        period = item.get("date") or item.get("period") or "unknown"

        dimension = _category_to_dimension(category)
        if metrics:
            for metric, value in metrics.items():
                if isinstance(value, (int, float)):
                    records.append(
                        CityRealEstateRecord(
                            city=city,
                            province=item.get("province"),
                            period=period,
                            source=source,
                            source_level=source_level,
                            dimension=dimension,
                            metric=metric,
                            value=_as_float(value),
                            unit=item.get("unit"),
                            yoy=_as_float(item.get("yoy")),
                            mom=_as_float(item.get("mom")),
                            raw_text=item.get("content") or item.get("summary"),
                            url=item.get("url"),
                            verified=bool(item.get("verified", False)),
                            notes=item.get("notes"),
                        )
                    )
        else:
            records.append(
                CityRealEstateRecord(
                    city=city,
                    province=item.get("province"),
                    period=period,
                    source=source,
                    source_level=source_level,
                    dimension=dimension,
                    metric="text_signal",
                    value=None,
                    unit=None,
                    raw_text=item.get("content") or item.get("summary"),
                    url=item.get("url"),
                    verified=bool(item.get("verified", False)),
                    notes=item.get("notes"),
                )
            )
    return records


def _category_to_dimension(category: str) -> str:
    mapping = {
        "policy": "policy",
        "local_policy": "policy",
        "announcement": "company_activity",
        "financial": "company_activity",
        "land": "land",
        "land_transaction": "land",
        "transaction": "transaction",
        "market_data": "transaction",
        "price": "price",
        "secondhand_market": "secondhand_market",
        "inventory": "inventory",
    }
    return mapping.get(category, "transaction")


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from codex.services.source_whitelist import validate_source_name


@dataclass
class DataItem:
    category: str  # policy | announcement | financial | land | transaction | price
    title: str
    content: str
    source: str
    url: Optional[str]
    city: Optional[str]
    company: Optional[str]
    date: str
    raw: Dict[str, Any]


Fetcher = Callable[[], List[Dict[str, Any]]]
Parser = Callable[[Dict[str, Any]], Optional[DataItem]]


class DataIngestionEngine:
    """多源数据抓取与解析总线。

    说明：
    - 不内置具体站点爬虫（避免不稳定与合规风险）；
    - 通过注册 fetcher + parser 的方式接入；
    - 对 Wind/同花顺等终端数据，使用“导入接口”而非抓取。
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
        }

    def ingest(self) -> List[DataItem]:
        results: List[DataItem] = []
        for source_name, config in self._sources.items():
            fetcher: Optional[Fetcher] = config.get("fetcher")
            parser: Optional[Parser] = config.get("parser")

            if not fetcher:
                continue

            raw_items = []
            try:
                raw_items = fetcher() or []
            except Exception:
                continue

            for raw in raw_items:
                if parser:
                    item = parser(raw)
                else:
                    item = self._default_parse(raw, source_name, config.get("category"))
                if item:
                    results.append(item)

        return results

    def import_external_dataset(
        self,
        name: str,
        dataset: List[Dict[str, Any]],
        category: str,
        usage: Optional[str] = None,
    ) -> List[DataItem]:
        """用于导入 Wind、同花顺等终端导出的数据。"""
        check = validate_source_name(name, usage=usage)
        if not check.get("allowed"):
            raise ValueError(f"来源不允许导入：{name}，原因：{check.get('reason')}")

        items: List[DataItem] = []
        for row in dataset:
            item = self._default_parse(row, name, category)
            if item:
                items.append(item)
        return items

    def _default_parse(self, raw: Dict[str, Any], source: str, category: str) -> Optional[DataItem]:
        title = str(raw.get("title") or raw.get("name") or "").strip()
        content = str(raw.get("content") or raw.get("summary") or "").strip()
        if not (title or content):
            return None

        return DataItem(
            category=category,
            title=title,
            content=content,
            source=source,
            url=raw.get("url"),
            city=raw.get("city"),
            company=raw.get("company"),
            date=raw.get("date") or datetime.now().strftime("%Y-%m-%d"),
            raw=raw,
        )


# ---- 示例 Fetcher / Parser（需要根据实际站点实现） ----

def example_policy_fetcher() -> List[Dict[str, Any]]:
    """示例：抓取政策（需要替换为真实实现，如政府RSS或公开接口）。"""
    return [
        {
            "title": "某地发布房地产新政",
            "content": "调整限购、信贷等措施",
            "url": "https://example.gov.cn/policy/123",
            "city": "某城市",
            "date": datetime.now().strftime("%Y-%m-%d"),
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
        date=raw.get("date"),
        raw=raw,
    )


# ---- 预设接入点（可按需开启） ----

def build_default_engine() -> DataIngestionEngine:
    engine = DataIngestionEngine()

    # 政策（示例）
    engine.register_source(
        name="地方政府官网",
        category="policy",
        fetcher=example_policy_fetcher,
        parser=example_policy_parser,
        usage="local_policy",
    )

    # 交易所公告（需实现具体抓取）
    engine.register_source(
        name="上交所",
        category="announcement",
        fetcher=None,
        parser=None,
        usage="announcement",
    )

    engine.register_source(
        name="深交所",
        category="announcement",
        fetcher=None,
        parser=None,
        usage="announcement",
    )

    engine.register_source(
        name="港交所",
        category="announcement",
        fetcher=None,
        parser=None,
        usage="announcement",
    )

    # 机构数据（通过导入接口）
    engine.register_source(
        name="Wind",
        category="market_data",
        fetcher=None,
        parser=None,
        usage="market_data",
    )

    engine.register_source(
        name="同花顺",
        category="market_data",
        fetcher=None,
        parser=None,
        usage="market_data",
    )

    engine.register_source(
        name="中指研究院",
        category="market_data",
        fetcher=None,
        parser=None,
        usage="market_data",
    )

    engine.register_source(
        name="CRIC",
        category="market_data",
        fetcher=None,
        parser=None,
        usage="market_data",
    )

    engine.register_source(
        name="贝壳研究院",
        category="market_data",
        fetcher=None,
        parser=None,
        usage="secondhand_market",
    )

    # 土地市场（地方自然资源）
    engine.register_source(
        name="地方自然资源和规划部门",
        category="land",
        fetcher=None,
        parser=None,
        usage="land_transaction",
    )

    # 成交数据（住建委）
    engine.register_source(
        name="地方住建部门",
        category="transaction",
        fetcher=None,
        parser=None,
        usage="transaction_data",
    )

    return engine

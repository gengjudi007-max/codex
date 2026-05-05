from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SourceRule:
    name: str
    level: str  # level_1 | level_2 | level_3 | blocked
    category: str
    allowed_usage: List[str]
    notes: str = ""


SOURCE_WHITELIST: Dict[str, SourceRule] = {
    "新华社": SourceRule("新华社", "level_1", "official_media", ["policy", "macro", "market_background"], "官方媒体，可直接作为政策和宏观事实来源。"),
    "中国政府网": SourceRule("中国政府网", "level_1", "central_government", ["policy", "macro"], "中央政策原文优先来源。"),
    "自然资源部": SourceRule("自然资源部", "level_1", "ministry", ["land", "policy"], "土地政策和自然资源数据来源。"),
    "住房和城乡建设部": SourceRule("住房和城乡建设部", "level_1", "ministry", ["housing_policy", "market_policy"], "住房政策、房地产政策来源。"),
    "中国人民银行": SourceRule("中国人民银行", "level_1", "regulator", ["finance_policy", "credit", "mortgage"], "金融政策来源。"),
    "证监会": SourceRule("证监会", "level_1", "regulator", ["capital_market", "listed_company"], "上市公司监管政策来源。"),
    "国家金融监督管理总局": SourceRule("国家金融监督管理总局", "level_1", "regulator", ["finance_policy", "banking", "insurance"], "金融监管政策来源。"),
    "上交所": SourceRule("上交所", "level_1", "exchange", ["announcement", "financial_report", "bond"], "上市公司公告和债券公告来源。"),
    "深交所": SourceRule("深交所", "level_1", "exchange", ["announcement", "financial_report", "bond"], "上市公司公告和债券公告来源。"),
    "港交所": SourceRule("港交所", "level_1", "exchange", ["announcement", "financial_report"], "港股房企公告来源。"),
    "地方政府官网": SourceRule("地方政府官网", "level_2", "local_government", ["local_policy", "land", "housing_policy"], "需核验发布主体、日期和文件原文。"),
    "地方自然资源和规划部门": SourceRule("地方自然资源和规划部门", "level_2", "local_department", ["land_transaction", "land_plan", "land_policy"], "城市土地成交与供应原始来源。"),
    "地方住建部门": SourceRule("地方住建部门", "level_2", "local_department", ["housing_policy", "transaction_data", "market_notice"], "城市新房、二手房成交和政策来源。"),
    "中指研究院": SourceRule("中指研究院", "level_2", "third_party_research", ["market_data", "land_data", "company_data"], "机构数据，建议与政府或另一机构交叉验证。"),
    "CRIC": SourceRule("CRIC", "level_2", "third_party_research", ["market_data", "land_data", "company_data"], "机构数据，建议与政府或另一机构交叉验证。"),
    "贝壳研究院": SourceRule("贝壳研究院", "level_2", "third_party_platform", ["secondhand_market", "new_home_market", "broker_observation"], "平台数据，需标注口径和覆盖范围。"),
    "Wind": SourceRule("Wind", "level_3", "data_terminal", ["market_data", "financial_data", "land_data"], "仅用于核心数据或报告，不采用转载新闻。"),
    "同花顺": SourceRule("同花顺", "level_3", "data_terminal", ["market_data", "financial_data"], "仅用于核心数据或报告，不采用转载新闻。"),
    "东方财富": SourceRule("东方财富", "level_3", "data_terminal", ["market_data", "financial_data", "announcement_index"], "仅用于核心数据和公告索引，不采用转载新闻。"),
    "DM": SourceRule("DM", "level_3", "data_terminal", ["market_data", "financial_data", "land_data"], "仅用于核心数据或报告。"),
    "国内媒体转载": SourceRule("国内媒体转载", "blocked", "media_reprint", [], "默认不采用，除非无可替代且完成交叉核验。"),
    "自媒体": SourceRule("自媒体", "blocked", "social_media", [], "不得作为事实或数据来源。"),
}


def validate_source_name(name: str, usage: Optional[str] = None) -> Dict[str, object]:
    rule = SOURCE_WHITELIST.get(name)
    if not rule:
        return {
            "allowed": False,
            "level": "unknown",
            "reason": "来源未在白名单中。",
            "suggestion": "替换为政府、交易所、新华社、中指、CRIC、Wind等来源。",
        }
    if rule.level == "blocked":
        return {
            "allowed": False,
            "level": rule.level,
            "reason": rule.notes,
            "suggestion": "仅在无可替代时作为线索，不进入正文核心事实。",
        }
    if usage and usage not in rule.allowed_usage:
        return {
            "allowed": False,
            "level": rule.level,
            "reason": f"来源“{name}”不适用于“{usage}”用途。",
            "suggestion": f"该来源允许用途：{', '.join(rule.allowed_usage)}。",
        }
    return {
        "allowed": True,
        "level": rule.level,
        "category": rule.category,
        "allowed_usage": rule.allowed_usage,
        "notes": rule.notes,
    }


def export_whitelist_for_check_engine() -> List[Dict[str, object]]:
    return [
        {
            "name": rule.name,
            "source_level": rule.level,
            "source_type": rule.category,
            "allowed_usage": rule.allowed_usage,
            "verified": rule.level in ["level_1", "level_2", "level_3"],
        }
        for rule in SOURCE_WHITELIST.values()
        if rule.level != "blocked"
    ]

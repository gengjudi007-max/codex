from __future__ import annotations

import json
import sqlite3
from collections import Counter
from typing import Any, Dict, List

from codex.services.autonomous_intelligence import run_autonomous_intelligence
from codex.services.knowledge_graph_store import related_entities
from codex.services.retrieval_engine import entity_query, newsroom_summary, timeline_query
from codex.services.sqlite_store import DEFAULT_DB_PATH, init_db

REGIME_SIGNALS = {
    "upcycle": ["溢价率回升", "民企回归", "成交回升", "价格上涨", "拿地积极"],
    "downcycle": ["流拍", "底价成交", "价格下跌", "成交低迷", "库存去化", "减值", "亏损"],
    "policy_support": ["止跌回稳", "白名单", "收储", "专项债", "合理控制新增房地产用地供应"],
    "balance_sheet_repair": ["降负债", "经营现金流", "谨慎拿地", "债务重组", "资产处置"],
    "quality_contraction": ["退出低效项目", "撤场", "不再续约", "应收账款", "毛利率承压"],
}

STRATEGIC_THEMES = {
    "land_finance": ["土地财政", "城投", "收储", "专项债", "流拍", "底价成交"],
    "developer_repair": ["净利润", "减值", "经营现金流", "降负债", "谨慎拿地"],
    "property_services_reset": ["在管面积", "合同面积", "退出低效项目", "应收账款", "增值服务"],
    "policy_semantics": ["着力稳定", "努力稳定", "止跌回稳", "供地", "白名单"],
    "urban_inventory": ["库存", "去化", "收储", "保障房", "城市更新"],
}


def run_strategic_intelligence(db_path: str = DEFAULT_DB_PATH, focus_entity: str = "") -> Dict[str, Any]:
    init_db(db_path)
    text_corpus = _corpus_text(db_path)
    autonomous = run_autonomous_intelligence(db_path)
    regime = detect_market_regime(text_corpus)
    themes = detect_strategic_themes(text_corpus)
    structural = structural_risk_model(themes, autonomous)
    focus = entity_strategic_profile(focus_entity, db_path) if focus_entity else None
    return {
        "mode": "strategic_real_estate_intelligence",
        "market_regime": regime,
        "strategic_themes": themes,
        "structural_risk_model": structural,
        "policy_semantic_memory": policy_semantic_memory(text_corpus),
        "long_cycle_observations": long_cycle_observations(regime, themes, structural),
        "editorial_worldview": editorial_worldview(regime, themes),
        "strategic_storylines": strategic_storylines(regime, themes, structural),
        "focus_entity_profile": focus,
        "claim_boundary": "战略情报层生成长期行业判断框架和选题方向，不替代数据核验、采访和原始文件。",
    }


def detect_market_regime(text: str) -> Dict[str, Any]:
    scores = []
    for regime, keywords in REGIME_SIGNALS.items():
        hits = [keyword for keyword in keywords if keyword in text]
        scores.append({"regime": regime, "hits": hits, "score": min(len(hits) * 20, 100)})
    ranked = sorted(scores, key=lambda item: item["score"], reverse=True)
    dominant = ranked[0] if ranked and ranked[0]["score"] > 0 else {"regime": "unknown", "hits": [], "score": 0}
    return {
        "dominant_regime": dominant["regime"],
        "confidence": dominant["score"],
        "signals": ranked,
        "reading": _regime_reading(dominant["regime"]),
    }


def detect_strategic_themes(text: str) -> List[Dict[str, Any]]:
    themes = []
    for theme, keywords in STRATEGIC_THEMES.items():
        hits = [keyword for keyword in keywords if keyword in text]
        if hits:
            themes.append({"theme": theme, "hits": hits, "score": min(len(hits) * 20, 100), "reading": _theme_reading(theme)})
    return sorted(themes, key=lambda item: item["score"], reverse=True)


def structural_risk_model(themes: List[Dict[str, Any]], autonomous: Dict[str, Any]) -> Dict[str, Any]:
    theme_names = {theme["theme"] for theme in themes}
    chains = []
    if "land_finance" in theme_names and "urban_inventory" in theme_names:
        chains.append({"chain": "土地财政—库存去化—收储资金", "risk": "地方财政与市场出清之间可能形成长期张力。"})
    if "developer_repair" in theme_names:
        chains.append({"chain": "房企利润—减值—现金流—投资收缩", "risk": "资产负债表修复可能压低未来新增供给和投资强度。"})
    if "property_services_reset" in theme_names:
        chains.append({"chain": "规模扩张—低效项目—应收账款—质量经营", "risk": "物业公司可能进入从规模叙事到现金流叙事的切换期。"})
    warning_count = len([warning for warning in autonomous.get("early_warnings", []) if "暂无" not in warning])
    return {
        "chains": chains,
        "warning_count": warning_count,
        "strategic_risk_level": "high" if warning_count >= 2 or len(chains) >= 3 else ("medium" if chains else "low"),
    }


def policy_semantic_memory(text: str) -> Dict[str, Any]:
    terms = ["着力稳定", "努力稳定", "止跌回稳", "合理控制新增房地产用地供应", "白名单", "收储"]
    hits = [term for term in terms if term in text]
    return {
        "terms": hits,
        "reading": "政策语义正在从泛化稳定转向更具体的价格、供地、融资和库存工具组合。" if hits else "尚未识别明确政策语义演化信号。",
        "watch_metrics": ["成交量", "价格", "去化周期", "房企融资", "土地成交结构", "收储进展"],
    }


def long_cycle_observations(regime: Dict[str, Any], themes: List[Dict[str, Any]], structural: Dict[str, Any]) -> List[str]:
    observations = []
    if regime.get("dominant_regime") == "downcycle":
        observations.append("房地产行业仍可能处于下行后的修复阶段，短期政策和成交改善不宜直接等同于周期反转。")
    if any(theme.get("theme") == "land_finance" for theme in themes):
        observations.append("土地财政链条仍是理解地方政府、城投平台和房地产市场关系的核心线索。")
    if any(theme.get("theme") == "developer_repair" for theme in themes):
        observations.append("房企经营叙事正从规模增长转向资产负债表修复和现金流安全。")
    if structural.get("strategic_risk_level") == "high":
        observations.append("多个结构性风险链同时出现，应从单篇报道升级为长期专题跟踪。")
    return observations or ["当前战略信号不足，应继续积累政策、土地、财报和采访材料。"]


def editorial_worldview(regime: Dict[str, Any], themes: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "core_lens": [
            "房地产报道不只看成交涨跌，更要看资金、土地、政策和居民预期之间的传导。",
            "企业动作应放入资产负债表、城市周期和政策约束中理解。",
            "地方托底、收储和供地调整需要区分市场修复与行政性支撑。",
        ],
        "current_bias_to_check": [
            "避免把短期成交改善写成周期反转。",
            "避免把企业口径写成行业结论。",
            "避免把政策意图直接等同于市场结果。",
        ],
        "style_implication": "更适合采用经济观察报式问题链和财新式证据链结合的深度报道方法。",
    }


def strategic_storylines(regime: Dict[str, Any], themes: List[Dict[str, Any]], structural: Dict[str, Any]) -> List[Dict[str, Any]]:
    storylines = []
    for theme in themes[:5]:
        storylines.append({
            "theme": theme["theme"],
            "suggested_format": "深度报道" if theme["score"] >= 60 else "行业观察",
            "angle": theme["reading"],
            "must_verify": ["核心数据口径", "政策原文", "企业公告", "第三方或采访交叉信源"],
        })
    if structural.get("strategic_risk_level") in {"medium", "high"}:
        storylines.insert(0, {
            "theme": "structural_risk_watch",
            "suggested_format": "系列专题",
            "angle": "多个结构性风险链并行出现，适合建立长期追踪专题。",
            "must_verify": ["时间线", "主体责任", "资金来源", "反向证据"],
        })
    return storylines or [{"theme": "continue_monitoring", "suggested_format": "监控", "angle": "继续积累信号。", "must_verify": []}]


def entity_strategic_profile(entity: str, db_path: str) -> Dict[str, Any]:
    return {
        "entity": entity,
        "entity_query": entity_query(entity, db_path=db_path),
        "timeline": timeline_query(entity, db_path=db_path),
        "relations": related_entities(entity, db_path=db_path),
    }


def _corpus_text(db_path: str) -> str:
    parts: List[str] = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for table, fields in (
            ("sources", ["title", "content", "city", "company"]),
            ("memory_events", ["title", "content", "city", "company", "risks_json", "risk_chains_json"]),
            ("claims", ["claim", "status"]),
            ("alerts", ["message"]),
        ):
            try:
                rows = conn.execute(f"SELECT * FROM {table}").fetchall()
            except sqlite3.OperationalError:
                continue
            for row in rows:
                for field in fields:
                    if field in row.keys() and row[field]:
                        parts.append(str(row[field]))
    return " ".join(parts)


def _regime_reading(regime: str) -> str:
    return {
        "upcycle": "市场可能出现修复信号，但仍需核验其是否由真实需求驱动。",
        "downcycle": "行业仍处于压力释放和资产负债表修复阶段。",
        "policy_support": "政策工具正在增强，但传导效果需要成交、价格和现金流验证。",
        "balance_sheet_repair": "企业端更重视现金流和债务安全，扩张逻辑弱化。",
        "quality_contraction": "行业可能从规模扩张转向质量和现金流经营。",
        "unknown": "战略周期信号不足。",
    }.get(regime, "战略周期信号不足。")


def _theme_reading(theme: str) -> str:
    return {
        "land_finance": "土地财政和城投托底仍是理解地方房地产市场的重要线索。",
        "developer_repair": "房企叙事从规模扩张转向现金流、减值和债务安全。",
        "property_services_reset": "物业行业正在从规模叙事转向质量经营和现金流约束。",
        "policy_semantics": "政策措辞变化需要放入历史语义中观察。",
        "urban_inventory": "库存去化和收储可能成为城市分化的重要变量。",
    }.get(theme, "需要继续观察。")

from __future__ import annotations

from typing import Any, Dict, List

from codex.services.text_utils import normalize_text, unique

RISK_SIGNALS = {
    "city_investment_land": {
        "keywords": ["城投拿地", "地方平台", "托底", "底价成交", "土地财政", "专项债", "流拍"],
        "risk_nodes": ["地方财政压力", "土地财政依赖", "城投托底", "地块后续开发不确定"],
        "followups": [
            "城投拿地资金来源是什么？",
            "地块是否实质开工，后续是否存在闲置风险？",
            "地方土地出让收入是否继续承压？",
        ],
    },
    "developer_finance": {
        "keywords": ["净利润下降", "亏损", "减值", "经营现金流", "债务重组", "展期", "融资收缩"],
        "risk_nodes": ["盈利能力下滑", "资产质量恶化", "融资能力弱化", "投资拿地收缩"],
        "followups": [
            "利润下降主要来自销售、毛利率还是资产减值？",
            "经营现金流与利润表是否背离？",
            "债务期限结构和再融资能力是否恶化？",
        ],
    },
    "policy_supply": {
        "keywords": ["合理控制新增房地产用地供应", "库存", "去化", "收储", "保障房", "城中村改造"],
        "risk_nodes": ["库存去化压力", "供地结构调整", "地方财政再平衡", "政策执行差异"],
        "followups": [
            "供地减少是否会影响地方财政收入？",
            "库存压力主要集中在哪些城市和板块？",
            "收储资金来源和退出机制是否清晰？",
        ],
    },
    "property_service": {
        "keywords": ["物业", "在管面积", "合同面积", "撤场", "退出低效项目", "应收账款"],
        "risk_nodes": ["规模扩张后遗症", "低效项目出清", "应收账款压力", "增值服务增长放缓"],
        "followups": [
            "退出项目是否改善利润率和现金流？",
            "在管面积与合同面积变化是否背离？",
            "母公司关联交易和应收账款是否形成拖累？",
        ],
    },
}


def analyze_risk_chain(payload: Any) -> Dict[str, Any]:
    text = _payload_to_text(payload)
    matched = []

    for name, rule in RISK_SIGNALS.items():
        hits = [keyword for keyword in rule["keywords"] if keyword in text]
        if hits:
            priority = _priority(len(hits), len(rule["risk_nodes"]))
            matched.append(
                {
                    "chain": name,
                    "matched_keywords": unique(hits),
                    "risk_nodes": rule["risk_nodes"],
                    "followup_questions": rule["followups"],
                    "priority": priority["level"],
                    "priority_score": priority["score"],
                }
            )

    return {
        "chains": sorted(matched, key=lambda item: item["priority_score"], reverse=True),
        "risk_map": _risk_map(matched),
        "reporting_path": _reporting_path(matched),
        "claim_boundary": "风险链只提示可能关联和采访方向，不能替代项目、财务、政策文件和采访核验。",
    }


def _payload_to_text(payload: Any) -> str:
    if isinstance(payload, dict):
        parts = []
        for key in ("title", "summary", "content", "text", "message"):
            parts.append(str(payload.get(key, "")))
        if isinstance(payload.get("items"), list):
            parts.extend(_payload_to_text(item) for item in payload["items"])
        return normalize_text(" ".join(parts))
    if isinstance(payload, list):
        return normalize_text(" ".join(_payload_to_text(item) for item in payload))
    return normalize_text(payload)


def _priority(hit_count: int, node_count: int) -> Dict[str, Any]:
    score = min(hit_count * 18 + node_count * 5, 100)
    if score >= 70:
        level = "high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"
    return {"level": level, "score": score}


def _risk_map(chains: List[Dict[str, Any]]) -> Dict[str, Any]:
    nodes = []
    for chain in chains:
        nodes.extend(chain["risk_nodes"])
    return {
        "node_count": len(unique(nodes)),
        "nodes": unique(nodes),
        "summary": "、".join(unique(nodes)[:8]) if nodes else "暂未识别明确风险链",
    }


def _reporting_path(chains: List[Dict[str, Any]]) -> List[str]:
    if not chains:
        return ["补充政策文件、公告、土地成交、财务指标或采访材料后再判断风险链。"]
    steps = [
        "先确认触发信号是否来自权威材料或可核验数据。",
        "再区分主体风险、项目风险、地方财政风险和行业周期风险。",
        "最后用采访和数据验证风险是否已经发生、正在累积，还是仅为潜在线索。",
    ]
    if any(chain["chain"] == "city_investment_land" for chain in chains):
        steps.append("城投拿地链条需继续追踪地块开工、资金来源、收储安排和闲置状态。")
    if any(chain["chain"] == "developer_finance" for chain in chains):
        steps.append("房企财务链条需拆分利润表、现金流量表、债务期限和资产减值。")
    return steps

from __future__ import annotations

from typing import Any, Dict, List

from codex.services.industry_intelligence import analyze_industry_intelligence
from codex.services.risk_chain import analyze_risk_chain
from codex.services.text_utils import normalize_text

CAUSAL_PATTERNS = [
    {
        "name": "land_finance_feedback",
        "triggers": ["土地财政", "城投拿地", "专项债", "收储", "底价成交"],
        "chain": ["土地出让承压", "地方平台托底", "财政与债务压力再平衡", "后续开发和去化不确定"],
        "question": "地方托底是短期稳定市场，还是延后风险暴露？",
    },
    {
        "name": "developer_balance_sheet_contraction",
        "triggers": ["净利润下降", "减值", "经营现金流", "降负债", "谨慎拿地"],
        "chain": ["利润和资产质量承压", "现金流优先级提高", "投资收缩", "行业供给侧继续出清"],
        "question": "房企是主动防守，还是被动缩表？",
    },
    {
        "name": "property_service_quality_shift",
        "triggers": ["退出低效项目", "撤场", "在管面积", "合同面积", "应收账款"],
        "chain": ["规模扩张红利减弱", "低效项目出清", "现金流和利润率再平衡", "物业行业回归基础服务"],
        "question": "物业公司收缩规模后，利润率和现金流是否真正改善？",
    },
    {
        "name": "policy_to_market_transmission",
        "triggers": ["止跌回稳", "努力稳定", "白名单", "合理控制新增房地产用地供应"],
        "chain": ["政策目标明确", "地方执行分化", "金融和土地端工具配合", "市场预期修复仍需成交验证"],
        "question": "政策信号能否转化为成交、价格和现金流改善？",
    },
]


def reason_real_estate(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = _payload_text(payload)
    industry = analyze_industry_intelligence(payload)
    risk = analyze_risk_chain(payload)
    causal_chains = _match_causal_chains(text)

    return {
        "mode": "real_estate_reasoning",
        "causal_chains": causal_chains,
        "cycle_reading": _cycle_reading(industry, risk, causal_chains),
        "policy_transmission": _policy_transmission(industry, causal_chains),
        "risk_evolution": _risk_evolution(risk, causal_chains),
        "counter_arguments": _counter_arguments(causal_chains),
        "reporting_questions": _reporting_questions(causal_chains, industry),
        "claim_boundary": "推理引擎输出的是可验证的分析假设，不是事实结论；必须通过数据、文件和采访验证。",
    }


def _payload_text(payload: Dict[str, Any]) -> str:
    parts: List[str] = []
    for key in ("title", "summary", "content", "text", "message", "current_policy", "previous_policy"):
        parts.append(str(payload.get(key, "")))
    if isinstance(payload.get("items"), list):
        for item in payload["items"]:
            if isinstance(item, dict):
                parts.extend(str(item.get(key, "")) for key in ("title", "summary", "content", "text"))
    return normalize_text(" ".join(parts))


def _match_causal_chains(text: str) -> List[Dict[str, Any]]:
    matches = []
    for pattern in CAUSAL_PATTERNS:
        hits = [trigger for trigger in pattern["triggers"] if trigger in text]
        if hits:
            matches.append(
                {
                    "name": pattern["name"],
                    "matched_triggers": hits,
                    "chain": pattern["chain"],
                    "core_question": pattern["question"],
                    "confidence": min(len(hits) * 25, 90),
                }
            )
    return sorted(matches, key=lambda item: item["confidence"], reverse=True)


def _cycle_reading(
    industry: Dict[str, Any],
    risk: Dict[str, Any],
    causal_chains: List[Dict[str, Any]],
) -> Dict[str, Any]:
    readings = list(industry.get("industry_reading", []))
    if any(chain["name"] == "developer_balance_sheet_contraction" for chain in causal_chains):
        readings.append("房企端可能仍处于资产负债表修复期，投资和扩张意愿受现金流约束。")
    if any(chain["name"] == "land_finance_feedback" for chain in causal_chains):
        readings.append("土地端信号更像周期下行后的财政与市场再平衡，而非简单成交恢复。")
    return {
        "summary": readings,
        "risk_nodes": risk.get("risk_map", {}).get("nodes", []),
    }


def _policy_transmission(
    industry: Dict[str, Any],
    causal_chains: List[Dict[str, Any]],
) -> Dict[str, Any]:
    policy = industry.get("policy_semantics", {})
    chains = [chain for chain in causal_chains if chain["name"] == "policy_to_market_transmission"]
    return {
        "policy_focus": policy.get("policy_focus", {}),
        "semantic_shifts": policy.get("semantic_shifts", []),
        "transmission_hypothesis": chains[0]["chain"] if chains else ["政策信号", "地方执行", "市场反馈"],
        "verification_metric": ["成交量", "价格", "去化周期", "房企现金流", "土地成交结构"],
    }


def _risk_evolution(risk: Dict[str, Any], causal_chains: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    evolutions = []
    for chain in causal_chains:
        evolutions.append(
            {
                "chain": chain["name"],
                "stage_1": chain["chain"][0],
                "stage_2": chain["chain"][1] if len(chain["chain"]) > 1 else "待观察",
                "stage_3": chain["chain"][-1],
                "verification": "需要用时间线、数据和采访验证风险是否已发生、正在累积或只是潜在线索。",
            }
        )
    if not evolutions:
        evolutions.append(
            {
                "chain": "unknown",
                "stage_1": "信号不足",
                "stage_2": "补充数据",
                "stage_3": "再判断风险演化",
                "verification": "当前缺少可推理链条。",
            }
        )
    return evolutions


def _counter_arguments(causal_chains: List[Dict[str, Any]]) -> List[str]:
    counters = [
        "单一数据变化不能直接证明周期反转。",
        "企业口径需要与公告、财报、项目现场和第三方数据交叉核验。",
    ]
    if any(chain["name"] == "land_finance_feedback" for chain in causal_chains):
        counters.append("城投拿地不一定等于风险加剧，也可能是阶段性供地结构调整。")
    if any(chain["name"] == "policy_to_market_transmission" for chain in causal_chains):
        counters.append("政策表述增强不必然带来成交修复，需观察地方执行和居民预期。")
    return counters


def _reporting_questions(causal_chains: List[Dict[str, Any]], industry: Dict[str, Any]) -> List[str]:
    questions = [chain["core_question"] for chain in causal_chains]
    questions.extend(industry.get("reporting_implications", []))
    return questions or ["当前信号不足，需补充政策、财报、土地、融资和采访材料。"]

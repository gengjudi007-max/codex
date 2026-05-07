from __future__ import annotations

from typing import Any, Dict, List

from codex.services.strategic_intelligence import run_strategic_intelligence
from codex.services.autonomous_intelligence import run_autonomous_intelligence
from codex.services.sqlite_store import DEFAULT_DB_PATH


def run_executive_intelligence(db_path: str = DEFAULT_DB_PATH, focus_entity: str = "") -> Dict[str, Any]:
    """Chief-editor / think-tank layer for real estate newsroom strategy."""
    strategic = run_strategic_intelligence(db_path=db_path, focus_entity=focus_entity)
    autonomous = run_autonomous_intelligence(db_path=db_path)
    scenarios = scenario_planning(strategic, autonomous)
    policy_model = policy_transmission_model(strategic)
    risk_paths = risk_path_forecast(strategic, autonomous)
    narrative = narrative_competition_analysis(strategic)

    return {
        "mode": "executive_real_estate_intelligence",
        "strategic_base": strategic,
        "scenario_planning": scenarios,
        "policy_transmission_model": policy_model,
        "risk_path_forecast": risk_paths,
        "narrative_competition": narrative,
        "editorial_positioning": editorial_positioning(strategic, scenarios, narrative),
        "chief_editor_brief": chief_editor_brief(strategic, scenarios, risk_paths),
        "institutional_memory_update": institutional_memory_update(strategic, autonomous),
        "claim_boundary": "Executive Intelligence 只提供主编层战略判断、情景假设和选题方向，不替代事实核查、采访和法律审核。",
    }


def scenario_planning(strategic: Dict[str, Any], autonomous: Dict[str, Any]) -> List[Dict[str, Any]]:
    regime = strategic.get("market_regime", {}).get("dominant_regime", "unknown")
    themes = {theme.get("theme") for theme in strategic.get("strategic_themes", [])}
    warnings = autonomous.get("early_warnings", [])

    scenarios = [
        {
            "name": "base_case",
            "probability": "medium",
            "path": "政策托底继续，市场缓慢修复，但成交、价格和现金流之间存在传导损耗。",
            "watch": ["成交量", "价格", "去化周期", "房企现金流", "土地成交结构"],
        }
    ]

    if regime in {"downcycle", "balance_sheet_repair"} or "developer_repair" in themes:
        scenarios.append({
            "name": "balance_sheet_repair_case",
            "probability": "medium_high",
            "path": "房企继续缩表，新增投资谨慎，利润表修复慢于政策预期。",
            "watch": ["减值", "经营现金流", "债务到期", "拿地强度", "销售回款"],
        })
    if "land_finance" in themes:
        scenarios.append({
            "name": "land_finance_pressure_case",
            "probability": "medium",
            "path": "土地财政压力延续，城投、专项债和收储工具继续参与市场稳定。",
            "watch": ["城投拿地比例", "专项债投向", "收储进度", "地块开发状态"],
        })
    if any("高风险" in warning or "风险" in warning for warning in warnings):
        scenarios.append({
            "name": "risk_escalation_case",
            "probability": "watch",
            "path": "局部风险信号积累，可能从企业端、土地端或地方财政端外溢。",
            "watch": ["高风险 claims", "alerts", "债务重组", "项目停滞", "舆情扩散"],
        })
    return scenarios


def policy_transmission_model(strategic: Dict[str, Any]) -> Dict[str, Any]:
    policy_memory = strategic.get("policy_semantic_memory", {})
    return {
        "semantic_terms": policy_memory.get("terms", []),
        "transmission_chain": [
            "中央政策表述",
            "部委工具细化",
            "地方执行强度",
            "金融机构风险偏好",
            "房企现金流",
            "居民购房预期",
            "成交与价格验证",
        ],
        "key_friction_points": [
            "地方执行能力和财政空间",
            "金融机构风险偏好",
            "居民收入和预期",
            "库存结构与城市分化",
        ],
        "editorial_warning": "不能把政策意图直接写成市场结果，应持续观察传导链是否闭合。",
    }


def risk_path_forecast(strategic: Dict[str, Any], autonomous: Dict[str, Any]) -> List[Dict[str, Any]]:
    paths = []
    structural = strategic.get("structural_risk_model", {})
    for chain in structural.get("chains", []):
        paths.append({
            "chain": chain.get("chain"),
            "risk": chain.get("risk"),
            "near_term": "信号确认与数据补强",
            "medium_term": "主体行为变化与政策工具落地",
            "long_term": "行业结构或地方财政约束再定价",
            "verification": ["时间线", "一手文件", "财务指标", "地方执行", "反向证据"],
        })
    if autonomous.get("contradiction_evolution", {}).get("high_risk_claim_count", 0):
        paths.append({
            "chain": "事实风险—发稿风险—公信力风险",
            "risk": "高风险声明若未核验即进入终稿，会损害媒体可信度。",
            "near_term": "冻结相关结论",
            "medium_term": "补证据或改写为待核验线索",
            "long_term": "沉淀事实核查规范",
            "verification": ["来源等级", "交叉验证", "口径说明"],
        })
    return paths or [{"chain": "monitoring", "risk": "暂无明确风险路径。", "verification": []}]


def narrative_competition_analysis(strategic: Dict[str, Any]) -> Dict[str, Any]:
    regime = strategic.get("market_regime", {}).get("dominant_regime", "unknown")
    return {
        "dominant_market_narratives": [
            "政策托底带来修复",
            "房企资产负债表仍在修复",
            "土地财政与库存去化再平衡",
            "城市分化加剧",
        ],
        "narrative_risks": [
            "将短期成交改善过度叙事为周期反转",
            "将企业自救写成行业复苏",
            "忽略地方财政和居民预期的约束",
        ],
        "recommended_position": "采用问题链 + 证据链写法，避免站队式叙事。",
        "current_regime_context": regime,
    }


def editorial_positioning(strategic: Dict[str, Any], scenarios: List[Dict[str, Any]], narrative: Dict[str, Any]) -> Dict[str, Any]:
    storylines = strategic.get("strategic_storylines", [])
    return {
        "position": "房地产财经深度观察与风险追踪",
        "priority_beats": ["政策语义", "土地财政", "房企现金流", "物业重构", "城市库存"],
        "coverage_strategy": [
            "用长期数据库跟踪同一城市、企业和政策语义。",
            "用证据链约束判断，用问题链组织深度报道。",
            "把单篇新闻升级为系列专题和长期观察。",
        ],
        "top_storylines": storylines[:5],
        "scenario_focus": [scenario.get("name") for scenario in scenarios],
        "narrative_position": narrative.get("recommended_position"),
    }


def chief_editor_brief(strategic: Dict[str, Any], scenarios: List[Dict[str, Any]], risk_paths: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "one_sentence": "房地产报道应从单点市场变化转向政策、土地、财政、企业现金流和居民预期的传导链观察。",
        "market_regime": strategic.get("market_regime", {}),
        "decision": "优先做可长期追踪的结构性选题，而不是追逐短期行情波动。",
        "this_week_focus": [scenario.get("name") for scenario in scenarios[:3]],
        "risk_paths_to_watch": [path.get("chain") for path in risk_paths[:5]],
    }


def institutional_memory_update(strategic: Dict[str, Any], autonomous: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "memory_principles": [
            "所有周期判断必须绑定数据验证指标。",
            "所有政策判断必须跟踪传导链，而不是只记录措辞。",
            "所有企业判断必须拆解利润表、现金流和资产负债表。",
            "所有土地财政判断必须追踪城投、专项债、收储和后续开发。",
        ],
        "new_memory_candidates": strategic.get("long_cycle_observations", []) + autonomous.get("early_warnings", []),
        "update_action": "将长期观察写入编辑部战略记忆，并与后续报道结果对照修正。",
    }

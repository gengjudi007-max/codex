from __future__ import annotations

from typing import Any, Dict, List

from codex.services.propaganda_detector import detect_propaganda_style
from codex.services.text_utils import normalize_text


THIRD_PERSON_REPLACEMENTS = {
    "我们": "该企业",
    "我司": "该企业",
    "公司将": "企业称将",
    "公司始终": "企业称其一直",
    "公司持续": "企业称其持续",
    "致力于": "试图",
    "赋能": "提供支持",
    "深耕": "持续布局",
    "引领": "推动",
    "打造": "建设",
    "焕新": "更新",
    "美好生活": "居住与消费需求",
}

STRUCTURE_TEMPLATE = [
    {
        "section": "导语",
        "purpose": "交代新闻由头、核心事实和待核验问题，避免直接采用企业愿景式开头。",
        "checks": ["是否有明确时间、主体、事件", "是否有数据或来源", "是否提示行业背景或问题意识"],
    },
    {
        "section": "第一部分：事实与变化",
        "purpose": "说明企业动作、项目变化或指标变化，区分事实、企业说法和记者判断。",
        "checks": ["事实是否可核验", "企业说法是否加以归属", "是否避免形容词堆砌"],
    },
    {
        "section": "第二部分：商业逻辑与行业背景",
        "purpose": "解释动作背后的行业周期、财务约束、市场变化和竞争格局。",
        "checks": ["是否补充同业或市场背景", "是否说明为何此时发生", "是否有反向信息"],
    },
    {
        "section": "第三部分：影响与未解问题",
        "purpose": "分析对企业、行业、消费者或城市的影响，并列出后续观察点。",
        "checks": ["是否保留不确定性", "是否列出后续核验方向", "是否避免结论过满"],
    },
]


def plan_newsroom_rewrite(text: Any) -> Dict[str, Any]:
    """Create an actionable newsroom rewrite plan without fabricating facts."""
    normalized = normalize_text(text)
    detection = detect_propaganda_style(text)

    return {
        "mode": "newsroom_rewrite_plan",
        "propaganda_risk": detection,
        "rewrite_positioning": _positioning(detection),
        "third_person_rewrite_map": _replacement_hits(normalized),
        "structure_template": STRUCTURE_TEMPLATE,
        "fact_check_questions": _fact_check_questions(detection),
        "editing_actions": _editing_actions(detection),
        "claim_boundary": "该模块只提供编辑规划和表达转换建议，不补写未经核实的数据、采访和事实。",
    }


def _positioning(detection: Dict[str, Any]) -> Dict[str, str]:
    risk_level = detection.get("risk_level")
    if risk_level == "high":
        return {
            "target": "从企业宣传稿改为第三方行业观察稿",
            "priority": "先压缩宣传性判断，再补事实来源、第三方信源和风险信息。",
        }
    if risk_level == "medium":
        return {
            "target": "从偏企业口径稿改为财经媒体稿",
            "priority": "保留事实信息，调整叙述主体，补充行业背景和约束条件。",
        }
    return {
        "target": "做基础新闻精校",
        "priority": "重点检查事实口径、数字来源和段落节奏。",
    }


def _replacement_hits(text: str) -> List[Dict[str, str]]:
    hits = []
    for original, replacement in THIRD_PERSON_REPLACEMENTS.items():
        if original in text:
            hits.append({"original": original, "suggested": replacement})
    return hits


def _fact_check_questions(detection: Dict[str, Any]) -> List[str]:
    questions = [
        "稿件中的核心事实是否能对应到公告、财报、政府文件、合同或采访记录？",
        "所有数字是否标明统计口径、时间范围和来源？",
        "企业自述是否已明确归属为企业说法，而非媒体结论？",
    ]
    if detection.get("absolute_terms"):
        questions.append("首个、唯一、领先等绝对化表述是否有权威来源支撑？")
    if "缺少第三方信源或外部评价" in detection.get("missing_elements", []):
        questions.append("是否需要补充业内人士、业主、投资者、研究机构或主管部门视角？")
    if "缺少风险、约束或反向信息" in detection.get("missing_elements", []):
        questions.append("是否存在市场下行、销售压力、资金约束、项目兑现难度等反向信息？")
    return questions


def _editing_actions(detection: Dict[str, Any]) -> List[str]:
    actions = [
        "将企业愿景式开头改为新闻事实开头。",
        "把形容词判断改为可核验事实或删去。",
        "将企业第一人称改为第三方表述。",
    ]
    if detection.get("propaganda_terms"):
        actions.append("集中替换高频宣传词，保留必要事实信息。")
    if detection.get("structural_signals"):
        actions.append("把时间线材料重组为问题链：发生了什么、为什么发生、影响什么、还要核验什么。")
    if detection.get("missing_elements"):
        actions.append("补充数据来源、第三方信源和风险约束后，再进入成稿。")
    return actions

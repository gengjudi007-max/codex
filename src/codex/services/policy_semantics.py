from __future__ import annotations

import re
from typing import Any, Dict, List

from codex.services.text_utils import normalize_text, unique

POLICY_TERMS = {
    "着力稳定": {
        "category": "稳市场",
        "strength": 4,
        "meaning": "强调政策执行力度和问题处置的主动性。",
    },
    "努力稳定": {
        "category": "稳市场",
        "strength": 3,
        "meaning": "强调目标导向，但措辞力度弱于“着力稳定”。",
    },
    "止跌回稳": {
        "category": "稳市场",
        "strength": 5,
        "meaning": "通常意味着价格、成交和预期均进入政策关注范围。",
    },
    "因城施策": {
        "category": "地方调控",
        "strength": 4,
        "meaning": "地方政府仍有政策工具箱和自主调整空间。",
    },
    "防范化解风险": {
        "category": "风险处置",
        "strength": 5,
        "meaning": "政策重心涉及房企、金融、交付或地方财政风险。",
    },
    "保交楼": {
        "category": "项目交付",
        "strength": 5,
        "meaning": "政策聚焦已售项目交付和购房者权益保护。",
    },
    "白名单": {
        "category": "融资支持",
        "strength": 4,
        "meaning": "融资协调机制可能成为项目层面纾困的重要工具。",
    },
    "合理控制新增房地产用地供应": {
        "category": "土地供应",
        "strength": 5,
        "meaning": "供地端进入约束阶段，通常对应库存去化和土地财政压力再平衡。",
    },
}

SHIFT_PAIRS = [
    ("着力稳定", "努力稳定", "稳市场措辞由执行力度导向转向目标努力导向，需观察政策力度是否边际变化。"),
    ("促进房地产市场平稳健康发展", "止跌回稳", "政策表述从长期健康发展转向短期止跌目标，市场压力信号更强。"),
    ("供需两端", "合理控制新增房地产用地供应", "政策关注从需求刺激扩展到供给约束和库存消化。"),
]


def analyze_policy_semantics(current_text: Any, previous_text: Any = "") -> Dict[str, Any]:
    current = normalize_text(current_text)
    previous = normalize_text(previous_text)

    current_terms = _matched_terms(current)
    previous_terms = _matched_terms(previous)
    shifts = _detect_shifts(current, previous)

    return {
        "current_terms": current_terms,
        "previous_terms": previous_terms,
        "semantic_shifts": shifts,
        "policy_focus": _focus_summary(current_terms),
        "news_value": _news_value(current_terms, shifts),
        "reporting_questions": _reporting_questions(current_terms, shifts),
        "claim_boundary": "政策语义分析只能提示报道方向，不能替代政策原文、历史表述和主管部门解释的核验。",
    }


def _matched_terms(text: str) -> List[Dict[str, Any]]:
    matches = []
    for term, meta in POLICY_TERMS.items():
        if term in text:
            matches.append({"term": term, **meta})
    return matches


def _detect_shifts(current: str, previous: str) -> List[Dict[str, str]]:
    shifts = []
    for old, new, implication in SHIFT_PAIRS:
        if new in current and old in previous:
            shifts.append({"from": old, "to": new, "implication": implication})
    return shifts


def _focus_summary(terms: List[Dict[str, Any]]) -> Dict[str, Any]:
    categories = unique(str(term["category"]) for term in terms)
    max_strength = max((int(term["strength"]) for term in terms), default=0)
    return {
        "categories": categories,
        "max_strength": max_strength,
        "summary": "、".join(categories) if categories else "暂未识别明确房地产政策焦点",
    }


def _news_value(terms: List[Dict[str, Any]], shifts: List[Dict[str, str]]) -> Dict[str, Any]:
    score = min(len(terms) * 12 + len(shifts) * 25, 100)
    if score >= 70:
        level = "high"
    elif score >= 35:
        level = "medium"
    else:
        level = "low"
    reasons = []
    if shifts:
        reasons.append("存在可对比的政策措辞变化")
    if any(term["strength"] >= 5 for term in terms):
        reasons.append("出现高强度政策信号词")
    if not reasons:
        reasons.append("目前仅能作为一般政策背景线索")
    return {"level": level, "score": score, "reasons": reasons}


def _reporting_questions(terms: List[Dict[str, Any]], shifts: List[Dict[str, str]]) -> List[str]:
    questions = [
        "本次表述与上一次中央或部委口径相比，变化发生在哪些关键词上？",
        "地方政府、金融机构和房企后续可能分别如何响应？",
        "政策目标更偏向稳预期、稳价格、稳成交，还是风险处置？",
    ]
    if shifts:
        questions.append("措辞变化是政策力度变化，还是阶段性任务表述变化？")
    categories = {term["category"] for term in terms}
    if "土地供应" in categories:
        questions.append("供地收缩如何影响地方土地财政、库存去化和城投拿地？")
    if "融资支持" in categories:
        questions.append("融资支持是面向企业主体，还是更多下沉到项目层面？")
    return questions

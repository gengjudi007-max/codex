from __future__ import annotations

from typing import Dict, List


ECONOMIC_OBSERVER_RULES = {
    "lead": [
        "优先使用事实切入",
        "减少口号化表达",
        "导语强调行业变化",
        "避免企业宣传口吻",
    ],
    "body": [
        "多使用市场主体动作",
        "增加市场博弈感",
        "减少空泛趋势判断",
        "增加历史变化与周期背景",
    ],
    "ending": [
        "从行业角度收束",
        "避免企业愿景式结尾",
    ],
}


WEAK_EXPRESSIONS = [
    "整体来看",
    "值得注意的是",
    "从某种程度上",
    "可以预见",
    "有业内人士指出",
]


STRONGER_REPLACEMENTS = {
    "整体来看": "从当前市场表现看",
    "值得注意的是": "一个变化正在出现",
    "从某种程度上": "在当前市场环境下",
    "可以预见": "市场已经开始出现",
}


def enhance_text(text: str) -> str:
    revised = text
    for weak, strong in STRONGER_REPLACEMENTS.items():
        revised = revised.replace(weak, strong)
    return revised


def build_expression_review(text: str) -> Dict:
    weak_hits: List[str] = []
    for expression in WEAK_EXPRESSIONS:
        if expression in text:
            weak_hits.append(expression)

    return {
        "weak_expressions": weak_hits,
        "rules": ECONOMIC_OBSERVER_RULES,
        "enhanced_preview": enhance_text(text[:1200]),
    }

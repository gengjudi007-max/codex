from __future__ import annotations

from typing import Dict, List


AI_STYLE_BLACKLIST = [
    "整体来看",
    "值得注意的是",
    "从某种意义上",
    "业内人士认为",
    "可以看出",
]


REPORTER_STYLE_GUIDE = {
    "lead": [
        "优先使用事实开场，而非观点开场",
        "避免宏大叙事空话",
        "优先写成交、企业、项目、时间、地点",
    ],
    "structure": [
        "允许长短段混合",
        "避免三段式套路重复",
        "减少模板化转场",
    ],
    "language": [
        "减少抽象判断",
        "增加现场感",
        "增加采访引用",
        "使用行业表达",
    ],
}


def detect_ai_style_phrases(text: str) -> List[str]:
    return [phrase for phrase in AI_STYLE_BLACKLIST if phrase in text]


def build_style_revision_report(text: str) -> Dict:
    return {
        "ai_style_phrases": detect_ai_style_phrases(text),
        "style_guide": REPORTER_STYLE_GUIDE,
    }

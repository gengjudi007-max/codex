from __future__ import annotations

import re
from typing import Any, Dict, List


WEAK_EXPRESSIONS = ["业内人士表示", "值得注意的是", "不可否认", "众所周知", "相关数据显示"]


def edit_draft(text: str) -> Dict[str, Any]:
    """对稿件做非生成式基础体检和编辑建议。"""
    cleaned = _clean_text(text)
    paragraphs = [paragraph for paragraph in cleaned.split("\n") if paragraph.strip()]

    issues = []
    issues.extend(_find_weak_expressions(cleaned))
    issues.extend(_find_long_paragraphs(paragraphs))
    issues.extend(_find_missing_attribution(cleaned))

    return {
        "cleaned_text": cleaned,
        "paragraph_count": len(paragraphs),
        "character_count": len(cleaned),
        "issues": issues,
        "fact_check_queue": _fact_check_queue(cleaned),
        "structure_suggestions": _structure_suggestions(paragraphs),
        "headline_options": _headline_options(cleaned),
    }


def _clean_text(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", str(text or ""))
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("。 ", "。\n")
    return text.strip()


def _find_weak_expressions(text: str) -> List[Dict[str, str]]:
    issues = []
    for expression in WEAK_EXPRESSIONS:
        if expression in text:
            issues.append({
                "type": "weak_expression",
                "message": f"表达“{expression}”偏模板化，建议替换为具体信源、数据或判断依据。",
            })
    return issues


def _find_long_paragraphs(paragraphs: List[str]) -> List[Dict[str, str]]:
    issues = []
    for index, paragraph in enumerate(paragraphs, 1):
        if len(paragraph) > 280:
            issues.append({
                "type": "long_paragraph",
                "message": f"第{index}段超过280字，建议拆分为事实、原因和影响三层。",
            })
    return issues


def _find_missing_attribution(text: str) -> List[Dict[str, str]]:
    if re.search(r"\d+(?:\.\d+)?\s*(?:亿元|万平方米|%|个百分点)", text) and not any(
        keyword in text for keyword in ["据", "公告", "年报", "文件", "数据显示", "披露"]
    ):
        return [{
            "type": "missing_attribution",
            "message": "稿件含关键数字但缺少明确来源，建议补充数据出处和统计口径。",
        }]
    return []


def _fact_check_queue(text: str) -> List[Dict[str, str]]:
    queue = []
    for match in re.finditer(
        r"[^。！？\n]*\d+(?:\.\d+)?\s*(?:亿元|万平方米|%|个百分点|宗)[^。！？\n]*[。！？]?",
        text,
    ):
        sentence = match.group(0).strip()
        if sentence:
            queue.append({
                "claim": sentence,
                "required_source": "补充原始公告、政府文件、交易数据或机构数据库口径。",
                "status": "needs_check",
            })
    if any(keyword in text for keyword in ["预计", "可能", "或将", "业内认为", "分析人士"]):
        queue.append({
            "claim": "稿件包含趋势预测或观点判断。",
            "required_source": "区分记者判断、受访者观点和已发生事实，并保留受访者身份类型。",
            "status": "needs_check",
        })
    return queue


def _structure_suggestions(paragraphs: List[str]) -> List[str]:
    suggestions = []
    if paragraphs and len(paragraphs[0]) > 120:
        suggestions.append("导语偏长，可压缩为事件、关键数字、核心矛盾三句话。")
    if len(paragraphs) < 4:
        suggestions.append("稿件层次偏少，建议补充背景、机制解释、影响和后续观察。")
    suggestions.append("结尾建议落到可验证的后续指标，而不是泛泛预测。")
    return suggestions


def _headline_options(text: str) -> List[str]:
    if "城投" in text or "土地" in text:
        return ["城投托底土地市场之后：地块如何消化成新问题", "土地成交回暖背后，谁在真正拿地"]
    if "净利润" in text or "亏损" in text:
        return ["房企利润表继续承压，经营质量仍待现金流验证", "净利润波动背后：房企开发主业再定价"]
    if "政策" in text:
        return ["房地产政策表述变化释放哪些信号", "从政策原文看楼市调控重心变化"]
    return ["这条房地产线索，真正值得追问的是什么"]

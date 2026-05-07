from __future__ import annotations

import re
from typing import Any, Dict, List

from codex.services.text_utils import normalize_text, unique

PR_TERMS = [
    "赋能", "生态", "深耕", "引领", "标杆", "高质量发展", "美好生活", "焕新",
    "战略布局", "持续发力", "全面升级", "价值共创", "品质人居", "匠心",
    "城市共建", "美好愿景", "创新驱动", "长期主义", "破局", "蝶变", "新篇章",
]

ABSOLUTE_TERMS = [
    "首个", "唯一", "第一", "领先", "最优", "顶级", "全面领先", "行业第一",
]

CORPORATE_VOICE_PATTERNS = [
    r"我们(?:将|始终|持续|坚持|致力于)",
    r"公司(?:将|始终|持续|坚持|致力于)",
    r"企业(?:将|始终|持续|坚持|致力于)",
]

SOURCE_TERMS = ["数据显示", "公告显示", "年报显示", "据", "采访", "记者", "公开资料", "根据"]
COUNTERBALANCE_TERMS = ["但", "不过", "然而", "同时", "风险", "压力", "仍需", "待观察", "不确定"]
THIRD_PARTY_TERMS = ["业内人士", "分析师", "研究机构", "专家", "受访者", "业主", "居民", "投资者"]


def detect_propaganda_style(text: Any) -> Dict[str, Any]:
    """Detect PR-style writing risks in Chinese business/news drafts."""
    normalized = normalize_text(text)
    paragraphs = _split_paragraphs(str(text or ""))
    sentences = _split_sentences(normalized)

    pr_hits = _find_terms(normalized, PR_TERMS)
    absolute_hits = _find_terms(normalized, ABSOLUTE_TERMS)
    corporate_voice_hits = _find_patterns(normalized, CORPORATE_VOICE_PATTERNS)

    missing_elements = []
    if not _find_terms(normalized, SOURCE_TERMS):
        missing_elements.append("缺少明确资料来源或数据出处")
    if not _find_terms(normalized, THIRD_PARTY_TERMS):
        missing_elements.append("缺少第三方信源或外部评价")
    if not _find_terms(normalized, COUNTERBALANCE_TERMS):
        missing_elements.append("缺少风险、约束或反向信息")

    structural_signals = []
    if _looks_like_timeline(paragraphs):
        structural_signals.append("时间线堆砌较明显，建议改为问题导向或逻辑导向结构")
    if _long_paragraph_count(paragraphs) >= 2:
        structural_signals.append("长段落较多，可能影响新闻稿件节奏")
    if len(sentences) >= 6 and len(pr_hits) / max(len(sentences), 1) > 0.6:
        structural_signals.append("宣传性词汇密度偏高")

    score = _risk_score(
        pr_hits=pr_hits,
        absolute_hits=absolute_hits,
        corporate_voice_hits=corporate_voice_hits,
        missing_elements=missing_elements,
        structural_signals=structural_signals,
    )

    return {
        "risk_level": _risk_level(score),
        "risk_score": score,
        "propaganda_terms": pr_hits,
        "absolute_terms": absolute_hits,
        "corporate_voice_hits": corporate_voice_hits,
        "missing_elements": missing_elements,
        "structural_signals": structural_signals,
        "rewrite_suggestions": _rewrite_suggestions(
            pr_hits,
            absolute_hits,
            corporate_voice_hits,
            missing_elements,
            structural_signals,
        ),
        "editorial_principles": [
            "把企业口径改写为第三方观察",
            "用可核验数据替代形容词",
            "补充行业背景、约束条件和反向信息",
            "区分已证实事实、企业说法和待核验判断",
        ],
    }


def _find_terms(text: str, terms: List[str]) -> List[str]:
    return unique(term for term in terms if term in text)


def _find_patterns(text: str, patterns: List[str]) -> List[str]:
    hits = []
    for pattern in patterns:
        hits.extend(match.group(0) for match in re.finditer(pattern, text))
    return unique(hits)


def _split_paragraphs(text: str) -> List[str]:
    return [paragraph.strip() for paragraph in re.split(r"\n+", text) if paragraph.strip()]


def _split_sentences(text: str) -> List[str]:
    return [sentence for sentence in re.split(r"[。！？；;]", text) if sentence.strip()]


def _looks_like_timeline(paragraphs: List[str]) -> bool:
    if not paragraphs:
        return False
    date_like = 0
    for paragraph in paragraphs:
        if re.search(r"\d{4}年|\d{1,2}月\d{1,2}日|近日|日前|随后|此后", paragraph):
            date_like += 1
    return date_like >= 3 and date_like / max(len(paragraphs), 1) >= 0.5


def _long_paragraph_count(paragraphs: List[str]) -> int:
    return sum(1 for paragraph in paragraphs if len(paragraph) > 280)


def _risk_score(
    pr_hits: List[str],
    absolute_hits: List[str],
    corporate_voice_hits: List[str],
    missing_elements: List[str],
    structural_signals: List[str],
) -> int:
    score = 0
    score += min(len(pr_hits) * 5, 35)
    score += min(len(absolute_hits) * 6, 18)
    score += min(len(corporate_voice_hits) * 8, 24)
    score += len(missing_elements) * 10
    score += len(structural_signals) * 8
    return min(score, 100)


def _risk_level(score: int) -> str:
    if score >= 70:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def _rewrite_suggestions(
    pr_hits: List[str],
    absolute_hits: List[str],
    corporate_voice_hits: List[str],
    missing_elements: List[str],
    structural_signals: List[str],
) -> List[str]:
    suggestions = []
    if pr_hits:
        suggestions.append("压缩或替换宣传性词汇：" + "、".join(pr_hits[:8]))
    if absolute_hits:
        suggestions.append("慎用绝对化表述，除非能提供权威来源：" + "、".join(absolute_hits[:6]))
    if corporate_voice_hits:
        suggestions.append("将企业第一人称或企业自述改为第三方新闻表述")
    if missing_elements:
        suggestions.append("补充缺失要素：" + "；".join(missing_elements))
    if structural_signals:
        suggestions.extend(structural_signals)
    if not suggestions:
        suggestions.append("当前宣传稿风险较低，可继续检查事实来源、数据口径和采访平衡性")
    return suggestions

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


ALLOWED_SOURCE_LEVELS = ["level_1", "level_2", "level_3"]

HIGH_RISK_PHRASES = [
    "必然",
    "一定",
    "彻底",
    "全面复苏",
    "崩盘",
    "暴雷",
    "违规",
    "造假",
    "内幕",
    "资金链断裂",
    "恶意",
    "操纵",
]

AI_PATTERN_PHRASES = [
    "整体来看",
    "从数据来看",
    "可以看出",
    "本质上",
    "意味着",
    "值得注意的是",
    "需要指出的是",
    "进一步来看",
    "可以发现",
]

FACT_KEYWORDS = [
    "成交",
    "认购",
    "来访",
    "同比",
    "环比",
    "面积",
    "套",
    "亿元",
    "万平方米",
    "净利润",
    "营收",
    "拿地",
    "溢价率",
    "流拍率",
    "专项债",
]


@dataclass
class CheckIssue:
    level: str  # error | warning | note
    category: str
    message: str
    suggestion: str
    location: Optional[str] = None


@dataclass
class FinalCheckReport:
    pass_status: bool
    score: int
    issues: List[Dict[str, Any]]
    summary: Dict[str, Any]


def run_final_check(
    article: Dict[str, Any],
    sources: List[Dict[str, Any]],
    interview_materials: Optional[List[Dict[str, Any]]] = None,
    topic: Optional[str] = None,
) -> Dict[str, Any]:
    """成稿前事实校验总控。

    输入：
    article = {
        "title": "...",
        "lead": "...",
        "sections": [
            {"title": "...", "content": "..."}
        ]
    }

    sources = [
        {
            "name": "中指研究院",
            "source_level": "level_2",
            "source_type": "third_party_data",
            "url": "...",
            "used_for": ["成交面积", "成交套数"],
            "verified": True,
        }
    ]

    规则：
    1. 数据句必须有来源；
    2. 来源必须在白名单等级内；
    3. 采访材料必须标明是否可引用和是否已核验；
    4. 高风险定性表达进入错误或警告；
    5. AI模板句进入风格警告；
    6. 主题不匹配内容进入警告。
    """
    interview_materials = interview_materials or []
    issues: List[CheckIssue] = []

    text_blocks = _flatten_article(article)
    issues.extend(_check_sources(sources))
    issues.extend(_check_fact_sentences(text_blocks, sources))
    issues.extend(_check_interview_materials(interview_materials))
    issues.extend(_check_risk_phrases(text_blocks))
    issues.extend(_check_ai_patterns(text_blocks))

    if topic:
        issues.extend(_check_topic_relevance(text_blocks, topic))

    score = _calculate_score(issues)
    pass_status = not any(issue.level == "error" for issue in issues) and score >= 75

    report = FinalCheckReport(
        pass_status=pass_status,
        score=score,
        issues=[asdict(issue) for issue in issues],
        summary=_build_summary(issues, sources, interview_materials),
    )
    return asdict(report)


def _flatten_article(article: Dict[str, Any]) -> List[Dict[str, str]]:
    blocks = []
    if article.get("title"):
        blocks.append({"location": "title", "text": article["title"]})
    if article.get("lead"):
        blocks.append({"location": "lead", "text": article["lead"]})
    for index, section in enumerate(article.get("sections", []), 1):
        title = section.get("title", f"section_{index}")
        if title:
            blocks.append({"location": f"section_{index}_title", "text": title})
        if section.get("content"):
            blocks.append({"location": f"section_{index}:{title}", "text": section["content"]})
    return blocks


def _check_sources(sources: List[Dict[str, Any]]) -> List[CheckIssue]:
    issues = []
    if not sources:
        return [
            CheckIssue(
                level="error",
                category="source",
                message="稿件未提供任何数据或事实来源。",
                suggestion="至少补充一个一级或二级白名单来源，如政府官网、交易所、中指、CRIC、Wind等。",
            )
        ]

    for source in sources:
        name = source.get("name", "未命名来源")
        level = source.get("source_level")
        verified = bool(source.get("verified"))
        source_type = source.get("source_type", "")

        if level not in ALLOWED_SOURCE_LEVELS:
            issues.append(
                CheckIssue(
                    level="error",
                    category="source_whitelist",
                    message=f"来源“{name}”不在白名单等级内。",
                    suggestion="删除该来源，或替换为新华社、政府部门、交易所、中指、CRIC、Wind等白名单来源。",
                )
            )
        elif level == "level_3" and "news" in source_type:
            issues.append(
                CheckIssue(
                    level="error",
                    category="source_scope",
                    message=f"来源“{name}”为数据平台，但被用于新闻报道内容。",
                    suggestion="Wind、同花顺、东方财富、DM等仅用于核心数据或报告，不用于转载新闻。",
                )
            )
        elif not verified:
            issues.append(
                CheckIssue(
                    level="warning",
                    category="source_verification",
                    message=f"来源“{name}”尚未标记为已核验。",
                    suggestion="补充URL、发布日期、统计口径，并与至少一个来源交叉核验。",
                )
            )

    return issues


def _check_fact_sentences(
    text_blocks: List[Dict[str, str]], sources: List[Dict[str, Any]]
) -> List[CheckIssue]:
    issues = []
    source_terms = _source_terms(sources)

    for block in text_blocks:
        sentences = _split_sentences(block["text"])
        for sentence in sentences:
            if _looks_like_fact_sentence(sentence):
                if not _has_source_marker(sentence, source_terms):
                    issues.append(
                        CheckIssue(
                            level="warning",
                            category="fact_source",
                            message=f"事实或数据句缺少明确来源：{sentence[:80]}",
                            suggestion="为该句补充来源表述，如“中指研究院数据显示”“据自然资源部门披露”等。",
                            location=block["location"],
                        )
                    )
    return issues


def _check_interview_materials(materials: List[Dict[str, Any]]) -> List[CheckIssue]:
    issues = []
    for material in materials:
        material_id = material.get("material_id", "未命名采访素材")
        status = material.get("status", "raw")
        can_quote = bool(material.get("can_quote"))
        quote_style = material.get("quote_style", "paraphrase")
        verification = material.get("verification", [])
        content = material.get("content", "")

        if status == "do_not_use":
            issues.append(
                CheckIssue(
                    level="error",
                    category="interview_material",
                    message=f"采访素材“{material_id}”标记为不得使用。",
                    suggestion="从稿件中删除该素材。",
                )
            )
        elif status == "raw":
            issues.append(
                CheckIssue(
                    level="warning",
                    category="interview_material",
                    message=f"采访素材“{material_id}”仍为原始状态。",
                    suggestion="完成对象身份、引用授权和事实核验后，再进入成稿。",
                )
            )

        if can_quote and quote_style == "direct" and not verification:
            issues.append(
                CheckIssue(
                    level="warning",
                    category="direct_quote",
                    message=f"采访素材“{material_id}”为直接引语，但缺少授权或核验说明。",
                    suggestion="补充录音、微信确认、采访笔记，或改为概述性表述。",
                )
            )

        if _looks_like_fact_sentence(content) and not verification:
            issues.append(
                CheckIssue(
                    level="warning",
                    category="interview_fact",
                    message=f"采访素材“{material_id}”包含数据或事实判断，但未提供核验依据。",
                    suggestion="用网签、公告、机构数据或第二采访源核验。",
                )
            )
    return issues


def _check_risk_phrases(text_blocks: List[Dict[str, str]]) -> List[CheckIssue]:
    issues = []
    for block in text_blocks:
        for phrase in HIGH_RISK_PHRASES:
            if phrase in block["text"]:
                issues.append(
                    CheckIssue(
                        level="warning",
                        category="legal_risk_expression",
                        message=f"发现高风险定性表达：“{phrase}”。",
                        suggestion="改为事实陈述，避免对企业、市场或行为作未经充分核验的定性。",
                        location=block["location"],
                    )
                )
    return issues


def _check_ai_patterns(text_blocks: List[Dict[str, str]]) -> List[CheckIssue]:
    issues = []
    for block in text_blocks:
        for phrase in AI_PATTERN_PHRASES:
            if phrase in block["text"]:
                issues.append(
                    CheckIssue(
                        level="note",
                        category="style_ai_pattern",
                        message=f"发现模板化表达：“{phrase}”。",
                        suggestion="改为具体事实推进句，减少套路化分析表达。",
                        location=block["location"],
                    )
                )
    return issues


def _check_topic_relevance(text_blocks: List[Dict[str, str]], topic: str) -> List[CheckIssue]:
    issues = []
    topic_keywords = _topic_keywords(topic)
    for block in text_blocks:
        if block["location"] == "title":
            continue
        text = block["text"]
        if len(text) < 80:
            continue
        if not any(keyword in text for keyword in topic_keywords):
            issues.append(
                CheckIssue(
                    level="note",
                    category="topic_relevance",
                    message=f"该段与主题关键词关联度较低：{block['location']}",
                    suggestion="确认该段是否直接服务主选题；如不能回答主问题，建议删除或移至背景段。",
                    location=block["location"],
                )
            )
    return issues


def _calculate_score(issues: List[CheckIssue]) -> int:
    score = 100
    for issue in issues:
        if issue.level == "error":
            score -= 20
        elif issue.level == "warning":
            score -= 8
        else:
            score -= 2
    return max(score, 0)


def _build_summary(
    issues: List[CheckIssue], sources: List[Dict[str, Any]], materials: List[Dict[str, Any]]
) -> Dict[str, Any]:
    return {
        "error_count": sum(1 for issue in issues if issue.level == "error"),
        "warning_count": sum(1 for issue in issues if issue.level == "warning"),
        "note_count": sum(1 for issue in issues if issue.level == "note"),
        "source_count": len(sources),
        "interview_material_count": len(materials),
        "source_levels": {
            level: sum(1 for source in sources if source.get("source_level") == level)
            for level in ALLOWED_SOURCE_LEVELS
        },
    }


def _split_sentences(text: str) -> List[str]:
    separators = "。！？；\n"
    sentences = []
    current = []
    for char in text:
        current.append(char)
        if char in separators:
            sentence = "".join(current).strip()
            if sentence:
                sentences.append(sentence)
            current = []
    if current:
        sentence = "".join(current).strip()
        if sentence:
            sentences.append(sentence)
    return sentences


def _looks_like_fact_sentence(sentence: str) -> bool:
    has_number = any(char.isdigit() for char in sentence)
    has_fact_keyword = any(keyword in sentence for keyword in FACT_KEYWORDS)
    return has_number or has_fact_keyword


def _source_terms(sources: List[Dict[str, Any]]) -> List[str]:
    terms = []
    for source in sources:
        name = source.get("name")
        if name:
            terms.append(name)
        for alias in source.get("aliases", []) or []:
            terms.append(alias)
    terms.extend(["数据显示", "披露", "统计", "公告", "报告", "监测"])
    return list(dict.fromkeys(terms))


def _has_source_marker(sentence: str, source_terms: List[str]) -> bool:
    return any(term and term in sentence for term in source_terms)


def _topic_keywords(topic: str) -> List[str]:
    if "五一" in topic or "假期" in topic:
        return ["五一", "假期", "成交", "来访", "认购", "项目", "客户", "二手房", "新房"]
    if "城投" in topic or "土地" in topic or "拿地" in topic:
        return ["城投", "土地", "拿地", "土拍", "底价", "溢价", "流拍", "专项债", "收储"]
    if "房企" in topic or "年报" in topic or "利润" in topic:
        return ["房企", "年报", "利润", "营收", "减值", "现金流", "融资", "销售"]
    return [part for part in topic.replace("，", " ").replace("、", " ").split() if part]

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from codex.services.publisher_engine import generate_publish_ready_article
from codex.services.topic_finder import find_topics
from codex.services.topic_scoring import score_topics


DEFAULT_SOURCE_POLICY = {
    "allowed": [
        "新华社",
        "中国政府网",
        "自然资源部",
        "住房和城乡建设部",
        "中国人民银行",
        "证监会",
        "国家金融监督管理总局",
        "上交所",
        "深交所",
        "地方政府官网",
        "地方自然资源和规划部门",
        "地方住建部门",
        "中指研究院",
        "CRIC",
        "Wind",
        "同花顺",
        "东方财富",
        "DM",
        "券商研究所",
        "银行研究院",
    ],
    "blocked_by_default": ["国内媒体转载", "自媒体", "无来源市场传闻"],
}


def run_daily_newsroom_pipeline(
    input_items: List[Dict[str, Any]],
    sources: Optional[List[Dict[str, Any]]] = None,
    interview_materials: Optional[List[Dict[str, Any]]] = None,
    field_materials: Optional[List[Dict[str, Any]]] = None,
    max_topics: int = 5,
    draft_depth: str = "brief",
) -> Dict[str, Any]:
    """每日自动选题 + 自动出稿流水线。

    输入：
        input_items: 当日政策、公告、市场、土地、金融等信息条目。
        sources: 已通过白名单的数据来源列表。
        interview_materials: 结构化采访素材。
        field_materials: 项目现场或探访素材。
        max_topics: 当日最多生成多少个选题。
        draft_depth: brief | deep。brief用于每日快跑，deep用于重点稿。

    输出：
        - daily_topics: 评分后的选题清单；
        - generated_articles: 每个选题对应的成稿/问题清单；
        - newsroom_notes: 当日编辑部提示。
    """
    sources = sources or []
    interview_materials = interview_materials or []
    field_materials = field_materials or []

    topics = find_topics({"items": input_items})
    scored_topics = score_topics(topics)[:max_topics]

    generated_articles = []
    for topic in scored_topics:
        article_seed = build_article_seed(topic, draft_depth=draft_depth)
        article_result = generate_publish_ready_article(
            topic=topic.get("topic", ""),
            article=article_seed,
            sources=sources,
            interview_materials=interview_materials,
            field_materials=field_materials,
        )
        generated_articles.append(
            {
                "topic": topic,
                "article": article_result,
            }
        )

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source_policy": DEFAULT_SOURCE_POLICY,
        "daily_topics": scored_topics,
        "generated_articles": generated_articles,
        "newsroom_notes": build_newsroom_notes(scored_topics, generated_articles),
    }


def build_article_seed(topic: Dict[str, Any], draft_depth: str = "brief") -> Dict[str, Any]:
    """根据选题生成一篇可供终稿引擎处理的初始稿件骨架。"""
    title = topic.get("topic", "房地产市场观察")
    angle = topic.get("angle", "")
    reason = topic.get("reason", "")
    category = topic.get("category", "房地产")
    trigger = topic.get("trigger", "")
    materials = topic.get("materials", [])
    questions = topic.get("questions", [])

    if draft_depth == "deep":
        sections = [
            {
                "title": "信息出现变化",
                "content": _deep_section_information(trigger, category, angle),
            },
            {
                "title": "企业、项目与城市之间表现不一",
                "content": _deep_section_structure(topic),
            },
            {
                "title": "仍需核验的数据和采访",
                "content": _deep_section_verification(materials, questions),
            },
        ]
    else:
        sections = [
            {
                "title": "当日信息",
                "content": f"{trigger}。{angle}",
            },
            {
                "title": "可操作方向",
                "content": f"该选题可围绕{category}展开。{reason}",
            },
            {
                "title": "待补材料",
                "content": "；".join(materials[:6]) if materials else "需补充白名单数据来源和一线采访材料。",
            },
        ]

    return {
        "title": title,
        "lead": _build_lead(topic),
        "sections": sections,
    }


def build_newsroom_notes(
    topics: List[Dict[str, Any]],
    generated_articles: List[Dict[str, Any]],
) -> List[str]:
    notes = []
    if not topics:
        notes.append("今日未触发高优先级房地产选题，建议继续跟踪政策、公告和土地成交。")
        return notes

    a_topics = [topic for topic in topics if topic.get("priority") == "重点选题"]
    if a_topics:
        notes.append("今日存在重点选题，建议优先核验数据并补充一线采访。")

    failed = [item for item in generated_articles if not item.get("article", {}).get("pass_status")]
    if failed:
        notes.append("部分稿件未通过终检，需根据 repair_plan 补数据、补采访或删改风险表达。")

    notes.append("正式发稿前，应以政府、交易所、中指、CRIC、Wind等白名单来源替换模拟或未核验信息。")
    return notes


def _build_lead(topic: Dict[str, Any]) -> str:
    trigger = topic.get("trigger", "相关信息")
    angle = topic.get("angle", "")
    return f"{trigger}。围绕这一变化，后续报道可继续核验数据、项目表现及相关主体说法。{angle}"


def _deep_section_information(trigger: str, category: str, angle: str) -> str:
    return (
        f"{trigger}。该信息属于{category}领域。报道可先梳理公开文件、公告或机构数据，"
        f"再核对同一口径下的历史变化。{angle}"
    )


def _deep_section_structure(topic: Dict[str, Any]) -> str:
    targets = topic.get("interview_targets", [])
    target_text = "、".join(targets[:5]) if targets else "相关企业、机构和项目一线人士"
    return (
        f"该选题不宜仅停留在单一数据变化上，可进一步比较不同城市、企业或项目之间的表现。"
        f"采访对象可包括{target_text}。稿件应区分数据事实、采访观察和分析背景。"
    )


def _deep_section_verification(materials: List[str], questions: List[str]) -> str:
    material_text = "、".join(materials[:6]) if materials else "政策原文、公告、成交数据、项目现场材料"
    question_text = "；".join(questions[:4]) if questions else "相关数据是否可核验；是否存在口径差异；采访对象是否授权引用"
    return f"需优先补充：{material_text}。采访和核验问题包括：{question_text}。"

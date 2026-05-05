from __future__ import annotations

from typing import Any, Dict, List, Optional

from codex.services.city_divergence_visualizer import (
    build_caption_suggestions,
    build_chart_specs,
    build_city_divergence_cards,
    build_city_divergence_ranking_table,
    export_markdown_table,
)
from codex.services.publisher_engine import generate_publish_ready_article, render_article


DEFAULT_FULL_PAGE_STRUCTURE = [
    "main_article",
    "ranking_table",
    "city_cards",
    "chart_specs",
    "captions",
    "editor_notes",
]


def build_full_page_package(
    topic: str,
    article_seed: Dict[str, Any],
    divergence_result: Dict[str, Any],
    sources: List[Dict[str, Any]],
    interview_materials: Optional[List[Dict[str, Any]]] = None,
    field_materials: Optional[List[Dict[str, Any]]] = None,
    table_limit: Optional[int] = 10,
    package_type: str = "newspaper",
) -> Dict[str, Any]:
    """生成整版稿输出包。

    package_type:
        newspaper: 纸媒/深度报道版面
        wechat: 公众号图文
        briefing: 内部选题会/晨会材料
        report: 研究报告式输出
    """
    article_output = generate_publish_ready_article(
        topic=topic,
        article=article_seed,
        sources=sources,
        interview_materials=interview_materials or [],
        field_materials=field_materials or [],
    )

    ranking_table = build_city_divergence_ranking_table(divergence_result, limit=table_limit)
    city_cards = build_city_divergence_cards(divergence_result, limit=table_limit)
    chart_specs = build_chart_specs(divergence_result)
    captions = build_caption_suggestions(divergence_result)

    return {
        "package_type": package_type,
        "topic": topic,
        "main_article": article_output.get("publish_version"),
        "article_check": {
            "pass_status": article_output.get("pass_status"),
            "score": article_output.get("score"),
            "repair_plan": article_output.get("repair_plan"),
        },
        "ranking_table": ranking_table,
        "ranking_table_markdown": export_markdown_table(ranking_table),
        "city_cards": city_cards,
        "chart_specs": chart_specs,
        "captions": captions,
        "layout_suggestion": build_layout_suggestion(package_type, ranking_table, city_cards, chart_specs),
        "editor_notes": build_editor_notes(article_output, divergence_result),
    }


def render_full_page_markdown(package: Dict[str, Any]) -> str:
    """将整版稿输出包渲染为 Markdown。"""
    parts = []

    if package.get("main_article"):
        parts.append(package["main_article"])

    if package.get("ranking_table_markdown"):
        parts.append("城市分化榜单")
        parts.append(package["ranking_table_markdown"])

    cards = package.get("city_cards", [])
    if cards:
        parts.append("城市数据卡")
        for card in cards:
            parts.append(render_city_card(card))

    chart_specs = package.get("chart_specs", {})
    if chart_specs:
        parts.append("图表配置")
        for key, spec in chart_specs.items():
            parts.append(render_chart_spec(key, spec))

    captions = package.get("captions", [])
    if captions:
        parts.append("图注建议")
        parts.extend([f"- {caption}" for caption in captions])

    notes = package.get("editor_notes", [])
    if notes:
        parts.append("编辑提示")
        parts.extend([f"- {note}" for note in notes])

    return "\n\n".join(parts)


def build_layout_suggestion(
    package_type: str,
    ranking_table: List[Dict[str, Any]],
    city_cards: List[Dict[str, Any]],
    chart_specs: Dict[str, Any],
) -> Dict[str, Any]:
    """生成版面/公众号/报告布局建议。"""
    if package_type == "wechat":
        return {
            "order": [
                "标题与导语",
                "核心图：城市评分排名",
                "正文第一部分：分化格局",
                "城市卡片：3—5个重点城市",
                "正文第二部分：成交与价格结构",
                "结构拆解图",
                "正文第三部分：土地、政策与房企行为",
                "榜单表",
                "收束段",
            ],
            "visual_priority": ["bar_score_ranking", "stacked_score_breakdown", "label_distribution"],
            "note": "公众号版本宜图文交错，避免连续大段文字。",
        }

    if package_type == "briefing":
        return {
            "order": ["今日判断", "城市榜单", "重点城市卡片", "可写选题", "待补数据"],
            "visual_priority": ["top_bottom_table", "bar_score_ranking"],
            "note": "内部材料以决策效率为主，保留问题清单和数据缺口。",
        }

    if package_type == "report":
        return {
            "order": ["摘要", "方法论", "榜单", "图表", "城市分组", "重点城市分析", "风险提示"],
            "visual_priority": ["stacked_score_breakdown", "label_distribution", "bar_score_ranking"],
            "note": "报告版本应保留评分方法和数据口径说明。",
        }

    return {
        "order": [
            "主稿标题与导语",
            "主稿第一部分",
            "城市分化榜单表",
            "主稿第二部分",
            "城市评分排名图",
            "主稿第三部分",
            "重点城市卡片",
            "收束段",
        ],
        "visual_priority": ["bar_score_ranking", "top_bottom_table", "stacked_score_breakdown"],
        "note": "纸媒版面应以主稿为核心，图表作为解释结构的辅助材料。",
    }


def build_editor_notes(article_output: Dict[str, Any], divergence_result: Dict[str, Any]) -> List[str]:
    notes = []
    check = article_output.get("editor_version", {}).get("final_check", {})
    if not article_output.get("pass_status"):
        notes.append("主稿未完全通过终检，发稿前需处理 repair_plan 中的数据、采访或风险表达问题。")
    else:
        notes.append("主稿通过终检，可进入人工编辑审阅。")

    ranking = divergence_result.get("ranking", [])
    if ranking:
        notes.append("城市榜单反映样本数据口径下的阶段性表现，不宜单独作为市场冷暖结论。")

    groups = divergence_result.get("groups", {})
    empty_groups = [label for label, cities in groups.items() if not cities]
    if empty_groups:
        notes.append(f"部分城市类型暂无样本：{'、'.join(empty_groups)}，可补充更多城市后再做榜单发布。")

    repair_plan = article_output.get("repair_plan", {})
    data_gaps = repair_plan.get("data_gaps", []) if repair_plan else []
    if data_gaps:
        notes.append("存在数据缺口，优先补充政府、交易所、中指、CRIC、Wind等来源。")

    return notes


def render_city_card(card: Dict[str, Any]) -> str:
    signals = card.get("key_signals", [])
    signal_text = "；".join(signals) if signals else "暂无明确信号"
    return (
        f"{card.get('city')}｜{card.get('label')}｜综合评分：{card.get('score')}\n"
        f"主要信号：{signal_text}\n"
        f"优势维度：{card.get('strongest_dimension')}；压力维度：{card.get('weakest_dimension')}\n"
        f"写作角度：{card.get('suggested_angle')}"
    )


def render_chart_spec(key: str, spec: Dict[str, Any]) -> str:
    title = spec.get("title", key)
    chart_type = spec.get("type", "unknown")
    note = spec.get("note", "")
    return f"{title}\n类型：{chart_type}\n说明：{note}"


def build_full_page_from_rendered_article(
    topic: str,
    rendered_article: str,
    divergence_result: Dict[str, Any],
    table_limit: Optional[int] = 10,
    package_type: str = "newspaper",
) -> Dict[str, Any]:
    """当已有人工编辑后的成稿时，直接生成图表和版面包。"""
    ranking_table = build_city_divergence_ranking_table(divergence_result, limit=table_limit)
    city_cards = build_city_divergence_cards(divergence_result, limit=table_limit)
    chart_specs = build_chart_specs(divergence_result)
    captions = build_caption_suggestions(divergence_result)

    return {
        "package_type": package_type,
        "topic": topic,
        "main_article": rendered_article,
        "ranking_table": ranking_table,
        "ranking_table_markdown": export_markdown_table(ranking_table),
        "city_cards": city_cards,
        "chart_specs": chart_specs,
        "captions": captions,
        "layout_suggestion": build_layout_suggestion(package_type, ranking_table, city_cards, chart_specs),
        "editor_notes": ["该包使用人工编辑后的成稿生成，未重新执行终检。"],
    }

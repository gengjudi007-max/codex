from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from codex.services.chart_render_engine import build_chart_manifest, render_full_page_charts
from codex.services.city_divergence_engine import CityDivergenceEngine
from codex.services.city_real_estate_database import (
    CityRealEstateDatabase,
    build_city_records_from_data_items,
)
from codex.services.city_divergence_visualizer import generate_visual_package
from codex.services.daily_newsroom_pipeline import run_daily_newsroom_pipeline
from codex.services.data_ingestion_engine import DataIngestionEngine, build_default_engine
from codex.services.full_page_package_engine import (
    build_full_page_package,
    render_full_page_markdown,
)
from codex.services.publisher_engine import generate_publish_ready_article
from codex.services.source_whitelist import export_whitelist_for_check_engine


DEFAULT_CITIES = [
    "北京",
    "上海",
    "广州",
    "深圳",
    "杭州",
    "成都",
    "南京",
    "武汉",
    "郑州",
    "西安",
]


def run_daily_auto_report_system(
    cities: Optional[List[str]] = None,
    data_items: Optional[List[Dict[str, Any]]] = None,
    sources: Optional[List[Dict[str, Any]]] = None,
    interview_materials: Optional[List[Dict[str, Any]]] = None,
    field_materials: Optional[List[Dict[str, Any]]] = None,
    ingestion_engine: Optional[DataIngestionEngine] = None,
    output_dir: str = "outputs/daily_report",
    render_charts: bool = True,
    max_topics: int = 5,
) -> Dict[str, Any]:
    """每日自动日报终版。

    该函数是整个房地产财经记者系统的每日总入口：
    1. 自动接入/导入数据；
    2. 更新城市级数据库；
    3. 运行城市分化分析；
    4. 生成城市榜单、图表配置和图片；
    5. 生成每日选题清单；
    6. 生成重点深度稿和整版稿包；
    7. 输出日报 Markdown、图表清单和待补清单。

    注意：
    - 不编造数据；
    - 无来源数据不进入正式稿；
    - Wind/同花顺等终端数据应通过 data_items 或 import_external_dataset 导入。
    """
    cities = cities or DEFAULT_CITIES
    sources = sources or export_whitelist_for_check_engine()
    interview_materials = interview_materials or []
    field_materials = field_materials or []

    if data_items is None:
        engine = ingestion_engine or build_default_engine()
        data_items = [_data_item_to_dict(item) for item in engine.ingest()]

    output_path = Path(output_dir) / datetime.now().strftime("%Y-%m-%d")
    output_path.mkdir(parents=True, exist_ok=True)

    city_db = CityRealEstateDatabase()
    city_records = build_city_records_from_data_items(data_items)
    city_db.add_records(city_records)
    city_profiles = city_db.profiles(cities)

    divergence_engine = CityDivergenceEngine()
    divergence_result = divergence_engine.analyze(city_profiles)
    visual_package = generate_visual_package(divergence_result, table_limit=10)

    newsroom_result = run_daily_newsroom_pipeline(
        input_items=data_items,
        sources=sources,
        interview_materials=interview_materials,
        field_materials=field_materials,
        max_topics=max_topics,
        draft_depth="deep",
    )

    city_article_seed = build_city_divergence_article_seed(divergence_result)
    full_page_package = build_full_page_package(
        topic="城市房地产市场分化",
        article_seed=city_article_seed,
        divergence_result=divergence_result,
        sources=sources,
        interview_materials=interview_materials,
        field_materials=field_materials,
        table_limit=10,
        package_type="newspaper",
    )

    if render_charts:
        full_page_package = render_full_page_charts(
            full_page_package,
            output_dir=str(output_path / "charts"),
        )
        full_page_package["chart_manifest"] = build_chart_manifest(
            full_page_package.get("rendered_charts", {})
        )

    daily_markdown = render_daily_report_markdown(
        newsroom_result=newsroom_result,
        divergence_result=divergence_result,
        visual_package=visual_package,
        full_page_package=full_page_package,
    )

    markdown_path = output_path / "daily_report.md"
    markdown_path.write_text(daily_markdown, encoding="utf-8")

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "output_dir": str(output_path),
        "daily_report_markdown_path": str(markdown_path),
        "data_item_count": len(data_items),
        "city_record_count": len(city_records),
        "city_profiles": city_profiles,
        "divergence_result": divergence_result,
        "visual_package": visual_package,
        "newsroom_result": newsroom_result,
        "full_page_package": full_page_package,
        "daily_report_markdown": daily_markdown,
        "final_status": build_final_status(newsroom_result, full_page_package),
    }


def build_city_divergence_article_seed(divergence_result: Dict[str, Any]) -> Dict[str, Any]:
    ranking = divergence_result.get("ranking", [])
    groups = divergence_result.get("groups", {})
    summary = divergence_result.get("summary", "")

    top_cities = [item.get("city") for item in ranking[:3] if item.get("city")]
    topic_cities = "、".join(top_cities) if top_cities else "重点城市"

    title = f"房地产城市分化观察：{topic_cities}等城市表现各异"
    lead = (
        f"近期，多个重点城市房地产市场在成交、价格、土地和政策层面呈现差异。{summary}"
        "相关变化需要结合成交套数、成交面积、价格、土地成交、库存和房企项目活动等多项数据观察。"
    )

    sections = [
        {
            "title": "城市表现被分为几类",
            "content": build_group_section(groups, ranking),
        },
        {
            "title": "成交、价格和库存影响分化结果",
            "content": build_breakdown_section(ranking),
        },
        {
            "title": "土地、政策和房企活动仍需逐项核验",
            "content": build_verification_section(ranking),
        },
    ]

    return {"title": title, "lead": lead, "sections": sections}


def build_group_section(groups: Dict[str, List[str]], ranking: List[Dict[str, Any]]) -> str:
    parts = []
    for label in ["恢复型", "分化型", "托底型", "风险型"]:
        cities = groups.get(label, [])
        if cities:
            parts.append(f"{label}城市包括：{'、'.join(cities)}。")
    if ranking:
        parts.append(
            "分组仅反映当前样本和数据口径下的阶段性特征，正式报道仍需回到具体城市的成交、价格、土地和政策数据。"
        )
    return "".join(parts) or "当前样本尚不足以形成稳定分组。"


def build_breakdown_section(ranking: List[Dict[str, Any]]) -> str:
    paragraphs = []
    for item in ranking[:5]:
        city = item.get("city")
        label = item.get("label")
        breakdown = item.get("score_breakdown", {})
        signals = "；".join(item.get("signals", [])[:3])
        paragraphs.append(
            f"{city}被归入{label}，成交、价格、土地、库存、政策和房企活动的分项评分分别为"
            f"{breakdown.get('transaction')}、{breakdown.get('price')}、{breakdown.get('land')}、"
            f"{breakdown.get('inventory')}、{breakdown.get('policy')}、{breakdown.get('company_activity')}。"
            f"主要信号包括：{signals}。"
        )
    return "\n\n".join(paragraphs) if paragraphs else "暂无可用于拆解的城市评分。"


def build_verification_section(ranking: List[Dict[str, Any]]) -> str:
    gaps = []
    for item in ranking:
        city = item.get("city")
        city_gaps = item.get("data_gaps", [])
        if city_gaps:
            gaps.append(f"{city}仍缺少：{'、'.join(city_gaps[:4])}。")
    if not gaps:
        return "当前样本未显示明显数据缺口，但发稿前仍应核验统计口径、发布时间和来源层级。"
    return "".join(gaps) + "这些缺口会影响城市分类和分化判断，发稿前应优先补齐。"


def render_daily_report_markdown(
    newsroom_result: Dict[str, Any],
    divergence_result: Dict[str, Any],
    visual_package: Dict[str, Any],
    full_page_package: Dict[str, Any],
) -> str:
    parts = []
    date = newsroom_result.get("date") or datetime.now().strftime("%Y-%m-%d")
    parts.append(f"房地产自动日报｜{date}")

    notes = newsroom_result.get("newsroom_notes", [])
    if notes:
        parts.append("今日编辑提示")
        parts.extend([f"- {note}" for note in notes])

    topics = newsroom_result.get("daily_topics", [])
    if topics:
        parts.append("今日选题清单")
        for idx, topic in enumerate(topics, 1):
            parts.append(
                f"{idx}. {topic.get('topic')}｜{topic.get('priority')}｜评分：{topic.get('final_score')}\n"
                f"   角度：{topic.get('angle')}"
            )

    parts.append("城市分化摘要")
    parts.append(divergence_result.get("summary", "暂无城市分化摘要。"))

    ranking_table_md = full_page_package.get("ranking_table_markdown")
    if ranking_table_md:
        parts.append("城市分化榜单")
        parts.append(ranking_table_md)

    chart_manifest = full_page_package.get("chart_manifest", [])
    if chart_manifest:
        parts.append("图表文件")
        for item in chart_manifest:
            parts.append(f"- {item.get('chart_key')}：{item.get('file_path')}｜{item.get('suggested_usage')}")

    main_article = full_page_package.get("main_article")
    if main_article:
        parts.append("今日整版稿")
        parts.append(main_article)

    repair_plan = full_page_package.get("article_check", {}).get("repair_plan", {})
    if repair_plan:
        parts.append("待补与风控清单")
        for key, value in repair_plan.items():
            if value:
                parts.append(f"{key}：{value}")

    return "\n\n".join(parts)


def build_final_status(newsroom_result: Dict[str, Any], full_page_package: Dict[str, Any]) -> Dict[str, Any]:
    article_check = full_page_package.get("article_check", {})
    return {
        "article_pass_status": article_check.get("pass_status"),
        "article_score": article_check.get("score"),
        "topic_count": len(newsroom_result.get("daily_topics", [])),
        "has_rendered_charts": bool(full_page_package.get("rendered_charts")),
        "need_manual_review": not bool(article_check.get("pass_status")),
    }


def _data_item_to_dict(item: Any) -> Dict[str, Any]:
    if isinstance(item, dict):
        return item
    return {
        "category": getattr(item, "category", None),
        "title": getattr(item, "title", None),
        "content": getattr(item, "content", None),
        "source": getattr(item, "source", None),
        "url": getattr(item, "url", None),
        "city": getattr(item, "city", None),
        "company": getattr(item, "company", None),
        "date": getattr(item, "date", None),
        "raw": getattr(item, "raw", {}),
    }

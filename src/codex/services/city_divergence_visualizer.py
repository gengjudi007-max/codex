from __future__ import annotations

from typing import Any, Dict, List, Optional


DEFAULT_LABEL_ORDER = ["恢复型", "分化型", "托底型", "风险型"]


def build_city_divergence_ranking_table(
    divergence_result: Dict[str, Any],
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """将城市分化分析结果转换为榜单表格。

    输出可直接用于：
    - 稿件数据表；
    - 公众号表格；
    - PPT数据页；
    - 后续图表绘制。
    """
    rows = []
    ranking = divergence_result.get("ranking", [])
    if limit:
        ranking = ranking[:limit]

    for index, item in enumerate(ranking, 1):
        breakdown = item.get("score_breakdown", {})
        rows.append(
            {
                "rank": index,
                "city": item.get("city"),
                "label": item.get("label"),
                "score": item.get("score"),
                "transaction_score": breakdown.get("transaction"),
                "price_score": breakdown.get("price"),
                "land_score": breakdown.get("land"),
                "inventory_score": breakdown.get("inventory"),
                "policy_score": breakdown.get("policy"),
                "company_activity_score": breakdown.get("company_activity"),
                "signals": "；".join(item.get("signals", [])),
                "writing_angle": item.get("writing_angle"),
            }
        )
    return rows


def build_city_divergence_cards(
    divergence_result: Dict[str, Any],
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """生成城市数据卡片。"""
    ranking = divergence_result.get("ranking", [])
    if limit:
        ranking = ranking[:limit]

    cards = []
    for item in ranking:
        breakdown = item.get("score_breakdown", {})
        strongest_dimension = _max_dimension(breakdown)
        weakest_dimension = _min_dimension(breakdown)
        cards.append(
            {
                "city": item.get("city"),
                "label": item.get("label"),
                "score": item.get("score"),
                "headline": _card_headline(item),
                "key_signals": item.get("signals", [])[:3],
                "strongest_dimension": strongest_dimension,
                "weakest_dimension": weakest_dimension,
                "suggested_angle": item.get("writing_angle"),
            }
        )
    return cards


def build_chart_specs(divergence_result: Dict[str, Any]) -> Dict[str, Any]:
    """生成图表配置，不直接绑定具体绘图库。

    前端、PPT、matplotlib、ECharts 都可复用该结构。
    """
    ranking = divergence_result.get("ranking", [])
    groups = divergence_result.get("groups", {})

    return {
        "bar_score_ranking": {
            "title": "城市房地产市场分化评分",
            "type": "bar",
            "x": [item.get("city") for item in ranking],
            "y": [item.get("score") for item in ranking],
            "series_name": "分化评分",
            "note": "评分越高，代表成交、价格、土地、库存、政策和房企活动等综合表现越强。",
        },
        "stacked_score_breakdown": {
            "title": "城市分化评分拆解",
            "type": "stacked_bar",
            "x": [item.get("city") for item in ranking],
            "series": _build_breakdown_series(ranking),
            "note": "拆解成交、价格、土地、库存、政策和房企活动对城市评分的贡献。",
        },
        "label_distribution": {
            "title": "城市类型分布",
            "type": "pie",
            "labels": DEFAULT_LABEL_ORDER,
            "values": [len(groups.get(label, [])) for label in DEFAULT_LABEL_ORDER],
            "note": "按恢复型、分化型、托底型、风险型进行分组。",
        },
        "top_bottom_table": {
            "title": "城市分化榜单摘要",
            "type": "table",
            "rows": build_city_divergence_ranking_table(divergence_result),
        },
    }


def generate_visual_package(
    divergence_result: Dict[str, Any],
    table_limit: Optional[int] = None,
) -> Dict[str, Any]:
    """生成城市分化可视化包。"""
    return {
        "ranking_table": build_city_divergence_ranking_table(divergence_result, limit=table_limit),
        "city_cards": build_city_divergence_cards(divergence_result, limit=table_limit),
        "chart_specs": build_chart_specs(divergence_result),
        "caption_suggestions": build_caption_suggestions(divergence_result),
    }


def build_caption_suggestions(divergence_result: Dict[str, Any]) -> List[str]:
    """为图表生成说明文字，供稿件、PPT或公众号使用。"""
    ranking = divergence_result.get("ranking", [])
    groups = divergence_result.get("groups", {})
    captions = []

    if ranking:
        top = ranking[0]
        bottom = ranking[-1]
        captions.append(
            f"在当前样本中，{top.get('city')}综合评分较高，{bottom.get('city')}相对靠后。评分仅反映样本数据口径下的阶段性表现。"
        )

    for label in DEFAULT_LABEL_ORDER:
        cities = groups.get(label, [])
        if cities:
            captions.append(f"{label}城市包括：{'、'.join(cities)}。")

    captions.append("榜单应结合成交、价格、土地、库存、政策和房企活动等多维数据解读，不宜单独作为市场冷暖判断依据。")
    return captions


def export_markdown_table(rows: List[Dict[str, Any]]) -> str:
    """将榜单导出为 Markdown 表格。"""
    if not rows:
        return ""
    headers = ["排名", "城市", "类型", "评分", "成交", "价格", "土地", "库存", "政策", "房企活动", "主要信号"]
    keys = [
        "rank",
        "city",
        "label",
        "score",
        "transaction_score",
        "price_score",
        "land_score",
        "inventory_score",
        "policy_score",
        "company_activity_score",
        "signals",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        values = [str(row.get(key, "")) for key in keys]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def _build_breakdown_series(ranking: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    dimensions = ["transaction", "price", "land", "inventory", "policy", "company_activity"]
    names = {
        "transaction": "成交",
        "price": "价格",
        "land": "土地",
        "inventory": "库存",
        "policy": "政策",
        "company_activity": "房企活动",
    }
    series = []
    for dimension in dimensions:
        series.append(
            {
                "name": names[dimension],
                "data": [item.get("score_breakdown", {}).get(dimension, 0) for item in ranking],
            }
        )
    return series


def _max_dimension(breakdown: Dict[str, Any]) -> Optional[str]:
    if not breakdown:
        return None
    return max(breakdown.items(), key=lambda item: item[1] if item[1] is not None else -999)[0]


def _min_dimension(breakdown: Dict[str, Any]) -> Optional[str]:
    if not breakdown:
        return None
    return min(breakdown.items(), key=lambda item: item[1] if item[1] is not None else 999)[0]


def _card_headline(item: Dict[str, Any]) -> str:
    city = item.get("city")
    label = item.get("label")
    score = item.get("score")
    return f"{city}：{label}，综合评分{score}"

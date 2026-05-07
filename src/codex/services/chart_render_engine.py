from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover
    plt = None


class ChartRenderError(RuntimeError):
    pass


def render_chart_specs(
    chart_specs: Dict[str, Any],
    output_dir: str = "outputs/charts",
    image_format: str = "png",
) -> Dict[str, str]:
    """批量渲染图表配置。

    输入来自 city_divergence_visualizer.build_chart_specs()。
    输出为 {chart_key: file_path}。

    注意：
    - 不在代码中指定颜色，便于沿用 matplotlib 默认样式；
    - 每张图单独生成，不使用 subplot；
    - 若 matplotlib 未安装，会返回清晰错误。
    """
    if plt is None:
        raise ChartRenderError("matplotlib is not installed. Run: pip install matplotlib")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rendered: Dict[str, str] = {}
    for key, spec in chart_specs.items():
        chart_type = spec.get("type")
        file_path = output_path / f"{key}.{image_format}"

        if chart_type == "bar":
            render_bar_chart(spec, file_path)
        elif chart_type == "stacked_bar":
            render_stacked_bar_chart(spec, file_path)
        elif chart_type == "pie":
            render_pie_chart(spec, file_path)
        elif chart_type == "table":
            render_table_chart(spec, file_path)
        else:
            continue

        rendered[key] = str(file_path)

    return rendered


def render_bar_chart(spec: Dict[str, Any], file_path: Path) -> None:
    x = spec.get("x", [])
    y = spec.get("y", [])
    title = spec.get("title", "")
    series_name = spec.get("series_name", "")
    note = spec.get("note", "")

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x, y)
    ax.set_title(title)
    ax.set_ylabel(series_name)
    ax.tick_params(axis="x", rotation=45)
    _add_note(fig, note)
    fig.tight_layout()
    fig.savefig(file_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def render_stacked_bar_chart(spec: Dict[str, Any], file_path: Path) -> None:
    x = spec.get("x", [])
    series = spec.get("series", [])
    title = spec.get("title", "")
    note = spec.get("note", "")

    fig, ax = plt.subplots(figsize=(11, 6))
    bottoms = [0] * len(x)

    for item in series:
        data = item.get("data", [])
        ax.bar(x, data, bottom=bottoms, label=item.get("name", ""))
        bottoms = [b + (d or 0) for b, d in zip(bottoms, data)]

    ax.set_title(title)
    ax.tick_params(axis="x", rotation=45)
    ax.legend()
    _add_note(fig, note)
    fig.tight_layout()
    fig.savefig(file_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def render_pie_chart(spec: Dict[str, Any], file_path: Path) -> None:
    labels = spec.get("labels", [])
    values = spec.get("values", [])
    title = spec.get("title", "")
    note = spec.get("note", "")

    filtered_labels = []
    filtered_values = []
    for label, value in zip(labels, values):
        if value:
            filtered_labels.append(label)
            filtered_values.append(value)

    fig, ax = plt.subplots(figsize=(8, 8))
    if filtered_values:
        ax.pie(filtered_values, labels=filtered_labels, autopct="%1.1f%%")
    ax.set_title(title)
    _add_note(fig, note)
    fig.tight_layout()
    fig.savefig(file_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def render_table_chart(spec: Dict[str, Any], file_path: Path) -> None:
    rows = spec.get("rows", [])
    title = spec.get("title", "")

    if not rows:
        rows = [{"提示": "暂无数据"}]

    columns = list(rows[0].keys())
    cell_text = [[str(row.get(column, "")) for column in columns] for row in rows]

    fig, ax = plt.subplots(figsize=(14, max(4, len(rows) * 0.45 + 2)))
    ax.axis("off")
    ax.set_title(title)
    table = ax.table(
        cellText=cell_text,
        colLabels=columns,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.3)
    fig.tight_layout()
    fig.savefig(file_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def render_full_page_charts(
    full_page_package: Dict[str, Any],
    output_dir: str = "outputs/charts",
) -> Dict[str, Any]:
    """为整版稿输出包渲染图表，并把图片路径写回 package。"""
    chart_specs = full_page_package.get("chart_specs", {})
    rendered = render_chart_specs(chart_specs, output_dir=output_dir)
    enriched = dict(full_page_package)
    enriched["rendered_charts"] = rendered
    return enriched


def build_chart_manifest(rendered_charts: Dict[str, str]) -> List[Dict[str, str]]:
    """生成图片清单，便于版面或公众号使用。"""
    return [
        {
            "chart_key": key,
            "file_path": path,
            "suggested_usage": _suggested_usage(key),
        }
        for key, path in rendered_charts.items()
    ]


def _suggested_usage(chart_key: str) -> str:
    mapping = {
        "bar_score_ranking": "主图：城市评分排名，可放在导语后或第一部分后。",
        "stacked_score_breakdown": "解释图：用于说明各城市评分由哪些维度构成。",
        "label_distribution": "辅助图：用于展示恢复型、分化型、托底型、风险型城市数量。",
        "top_bottom_table": "表格图：可作为版面数据表或公众号长图。",
    }
    return mapping.get(chart_key, "辅助图表。")


def _add_note(fig: Any, note: str) -> None:
    if note:
        fig.text(0.01, 0.01, note, ha="left", va="bottom", fontsize=8)

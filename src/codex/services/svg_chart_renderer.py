from __future__ import annotations

from pathlib import Path
from typing import Dict, List


DEFAULT_WIDTH = 900
DEFAULT_HEIGHT = 500


def render_bar_chart(chart_data: Dict, output_path: Path | str) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    labels: List[str] = chart_data.get("x", [])
    values: List[float] = chart_data.get("y", [])
    title = chart_data.get("title", "Chart")

    if not values:
        output_path.write_text("<svg xmlns='http://www.w3.org/2000/svg'></svg>", encoding="utf-8")
        return output_path

    max_value = max(values) or 1
    bar_width = 40
    gap = 20
    start_x = 80
    chart_bottom = 420

    bars = []

    for idx, value in enumerate(values):
        height = (value / max_value) * 300
        x = start_x + idx * (bar_width + gap)
        y = chart_bottom - height

        bars.append(f"<rect x='{x}' y='{y}' width='{bar_width}' height='{height}' fill='#4a90e2'/>")
        bars.append(f"<text x='{x}' y='{chart_bottom + 20}' font-size='12'>{labels[idx]}</text>")
        bars.append(f"<text x='{x}' y='{y - 5}' font-size='12'>{round(value, 1)}</text>")

    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' width='{DEFAULT_WIDTH}' height='{DEFAULT_HEIGHT}'>
        <text x='50' y='40' font-size='24'>{title}</text>
        <line x1='60' y1='420' x2='850' y2='420' stroke='black'/>
        <line x1='60' y1='80' x2='60' y2='420' stroke='black'/>
        {''.join(bars)}
    </svg>
    """

    output_path.write_text(svg, encoding='utf-8')
    return output_path

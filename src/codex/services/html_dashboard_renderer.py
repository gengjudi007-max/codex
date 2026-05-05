from __future__ import annotations

from pathlib import Path
from typing import Dict, List


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang='zh'>
<head>
<meta charset='utf-8'>
<title>{title}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 40px; }}
.card {{ border: 1px solid #ddd; padding: 20px; margin-bottom: 20px; border-radius: 8px; }}
h1 {{ margin-bottom: 30px; }}
</style>
</head>
<body>
<h1>{title}</h1>
{content}
</body>
</html>
"""


def render_dashboard(title: str, cards: List[Dict], output_path: Path | str) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    blocks = []
    for card in cards:
        blocks.append(
            f"<div class='card'><h2>{card.get('title')}</h2><pre>{card.get('content')}</pre></div>"
        )

    html = HTML_TEMPLATE.format(
        title=title,
        content="\n".join(blocks),
    )

    output_path.write_text(html, encoding="utf-8")
    return output_path

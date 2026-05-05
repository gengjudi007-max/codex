from __future__ import annotations

from typing import Dict

from codex.services.economic_observer_style_engine import build_expression_review
from codex.services.reporter_style_engine import build_style_revision_report


EDITOR_PIPELINE = [
    "事实校验",
    "数据一致性检查",
    "AI味检查",
    "记者表达增强",
    "行业逻辑增强",
    "标题优化",
    "终稿风格统一",
]


def run_editor_pipeline(text: str) -> Dict:
    style_review = build_style_revision_report(text)
    observer_review = build_expression_review(text)

    return {
        "pipeline": EDITOR_PIPELINE,
        "style_review": style_review,
        "observer_review": observer_review,
        "final_preview": observer_review.get("enhanced_preview"),
    }

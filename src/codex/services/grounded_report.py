"""Source-bound reporting without invented interviews or placeholder prose.

This offline writer assembles attributed source excerpts, not generative analysis.
A draft is never certified for publication by string matching or source count.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import urlparse

SECTIONS = (
    ("销售与项目进展", ("现房", "预售", "封顶", "成交", "地块", "交付")),
    ("贷款与资金管理", ("贷款", "融资", "主办银行", "资金", "资本金", "按揭")),
    ("适用范围与过渡安排", ("在途", "过渡", "施行前", "原有", "适用", "已取得", "此前")),
)


def source_records(payload: Dict[str, Any]) -> List[Dict[str, str]]:
    raw = payload.get("sources", [])
    if not isinstance(raw, list) or any(not isinstance(s, dict) for s in raw):
        raise ValueError("sources 必须是来源对象列表。")
    records = []
    seen = set()
    for source in raw:
        content = source.get("content") or source.get("text") or source.get("summary") or ""
        if not isinstance(content, str):
            raise ValueError("来源 content/text/summary 必须为文本。")
        content = content.strip()
        url = str(source.get("url") or source.get("source_url") or "").strip()
        title = str(source.get("title") or "未命名材料").strip()
        key = (url, title, content)
        if not content or key in seen:
            continue
        seen.add(key)
        records.append({"id": f"S{len(records) + 1}", "title": title, "url": url,
                        "source_type": str(source.get("source_type") or "unknown"),
                        "content": content})
    return records


def source_items(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [{"title": s["title"], "content": s["content"], "summary": s["content"],
             "url": s["url"], "source": s["source_type"]} for s in source_records(payload)]


def _sentences(text: str) -> List[str]:
    # Chinese punctuation only: decimal values and URLs must remain intact.
    # Keep quoted speech together rather than cutting an attribution in half.
    result, start, stack = [], 0, []
    pairs = {"“": "”", "「": "」", "‘": "’"}
    for index, char in enumerate(text):
        if char in pairs:
            stack.append(pairs[char])
        elif stack and char == stack[-1]:
            stack.pop()
        terminal = char in "。！？\n" or (char in "”」’" and index and text[index - 1] in "。！？")
        if terminal and not stack:
            sentence = text[start:index + 1].strip()
            if sentence:
                result.append(sentence)
            start = index + 1
    if text[start:].strip():
        result.append(text[start:].strip())
    return result


def _section(text: str) -> str:
    # Transition exceptions take precedence over a generic sales/loan keyword.
    for title, words in reversed(SECTIONS):
        if any(word in text for word in words):
            return title
    return "其他已提供事实"


def write_grounded_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    sources = source_records(payload)
    if not sources:
        return {"mode": "grounded_report", "headline": "", "article_text": "",
                "paragraphs": [], "sources": [], "verification_gate": {
                    "status": "blocked_missing_source_content", "publishable": False,
                    "issues": ["需要来源正文；仅有链接或线索标题不能生成有据可查的正文。"]},
                "writer": "extractive", "claim_boundary": "不自动抓取链接，不补造事实。"}
    writer = payload.get("writer", "extractive")
    if writer not in {"extractive", "model"}:
        raise ValueError("writer 仅支持 extractive 或 model。")
    if writer == "model":
        from codex.services.model_writer import generate_model_report
        return generate_model_report(sources, str(payload.get("headline") or ""))
    paragraphs, seen = [], set()
    for source in sources:
        for excerpt in _sentences(source["content"]):
            canonical = re.sub(r"\s+", "", excerpt)
            if canonical in seen:
                continue
            seen.add(canonical)
            paragraphs.append({"id": f"P{len(paragraphs) + 1}", "section": _section(excerpt),
                               "source_id": source["id"], "excerpt": excerpt,
                               "text": f"据《{source['title']}》，{excerpt}",
                               "verification_status": "source_excerpt_only"})
    # No template instructions in the body and no repetition between lead/body.
    lead = paragraphs[:1]
    rest = paragraphs[1:]
    headline = str(payload.get("headline") or sources[0]["title"])
    parts = [headline, *(p["text"] for p in lead)]
    for title in [s[0] for s in SECTIONS] + ["其他已提供事实"]:
        group = [p["text"] for p in rest if p["section"] == title]
        if group:
            parts.extend([title, *group])
    issues = ["正文为来源摘编，来源真实性、时效、适用范围和结论仍需编辑审核。"]
    if len(paragraphs) < 4:
        issues.append("材料偏少，仅生成简讯，不扩写为深度报道。")
    if any(urlparse(s["url"]).scheme not in {"http", "https"} for s in sources):
        issues.append("部分来源缺少可追溯的网页地址，请补充原始文件或采访记录。")
    return {"mode": "grounded_report", "headline": headline, "article_text": "\n\n".join(parts),
            "paragraphs": paragraphs, "sources": sources, "writer": "extractive",
            "verification_gate": {"status": "draft_for_editor_review", "publishable": False,
                                  "source_count": len(sources), "issues": issues},
            "claim_boundary": "来源对应表示文本可追溯，不等于事实已核验或可自动发布。"}

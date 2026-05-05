from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

from codex.services.text_utils import compact_text, normalize_text, unique


VERIFICATION_VERIFIED = "verified"
VERIFICATION_NEEDS_CHECK = "needs_check"
VERIFICATION_INSUFFICIENT = "insufficient_source"


def build_evidence(item: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Build source evidence records from an input item and optional derived context."""
    context = context or {}
    records: List[Dict[str, Any]] = []

    title = normalize_text(item.get("title") or context.get("trigger") or "未命名信息")
    source = normalize_text(item.get("source") or context.get("source") or "unknown")
    url = normalize_text(item.get("url") or item.get("source_url") or "")
    published_at = normalize_text(item.get("published_at") or item.get("date") or "")
    excerpt = compact_text(item.get("summary") or item.get("content") or title, 220)

    records.append(
        {
            "source": source,
            "title": title,
            "url": url or None,
            "published_at": published_at or None,
            "excerpt": excerpt,
            "source_type": _source_type(source, url),
            "status": VERIFICATION_NEEDS_CHECK if not url else VERIFICATION_VERIFIED,
        }
    )

    for material in context.get("materials", []) or []:
        records.append(
            {
                "source": "required_material",
                "title": normalize_text(material),
                "url": None,
                "published_at": None,
                "excerpt": "报道前需取得或核验该材料。",
                "source_type": "required_material",
                "status": VERIFICATION_INSUFFICIENT,
            }
        )

    return _dedupe_records(records)


def assess_confidence(
    evidence: List[Dict[str, Any]],
    *,
    has_metrics: bool = False,
    has_original_url: bool = False,
    required_materials: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Assess whether the current output is verified fact or a reporting lead."""
    required = list(required_materials or [])
    source_score = 0.0

    if evidence:
        source_score += 0.25
    if has_original_url or any(record.get("url") for record in evidence):
        source_score += 0.25
    if has_metrics:
        source_score += 0.2
    if required:
        source_score += 0.1
    if len(evidence) >= 2:
        source_score += 0.1
    if any(record.get("source_type") in {"government", "exchange", "company"} for record in evidence):
        source_score += 0.1

    confidence = round(min(source_score, 0.95), 2)
    if confidence >= 0.75:
        status = VERIFICATION_VERIFIED
    elif confidence >= 0.4:
        status = VERIFICATION_NEEDS_CHECK
    else:
        status = VERIFICATION_INSUFFICIENT

    return {
        "confidence": confidence,
        "verification_status": status,
        "evidence_count": len(evidence),
        "limitations": _limitations(evidence, required, has_metrics),
    }


def attach_credibility(
    payload: Dict[str, Any],
    item: Dict[str, Any],
    *,
    required_materials: Optional[Iterable[str]] = None,
) -> Dict[str, Any]:
    """Return payload with evidence and confidence metadata attached."""
    evidence = build_evidence(item, payload)
    text = " ".join(str(item.get(key, "")) for key in ("title", "summary", "content"))
    assessment = assess_confidence(
        evidence,
        has_metrics=_has_metrics(text) or bool(item.get("metrics")),
        has_original_url=bool(item.get("url") or item.get("source_url")),
        required_materials=required_materials or payload.get("materials"),
    )
    enriched = dict(payload)
    enriched["evidence"] = evidence
    enriched.update(assessment)
    enriched["claim_boundary"] = _claim_boundary(assessment["verification_status"])
    return enriched


def source_quality(url: str, source: str = "") -> Dict[str, Any]:
    source_type = _source_type(source, url)
    scores = {
        "government": 0.95,
        "exchange": 0.9,
        "company": 0.8,
        "institution": 0.7,
        "media": 0.6,
        "unknown": 0.4,
    }
    return {
        "source_type": source_type,
        "reliability_score": scores.get(source_type, 0.4),
        "requires_cross_check": source_type not in {"government", "exchange", "company"},
    }


def _source_type(source: str, url: str) -> str:
    text = f"{source} {url}".lower()
    if any(domain in text for domain in [".gov.cn", "gov.cn", "mohurd", "pbc.gov", "stats.gov"]):
        return "government"
    if any(domain in text for domain in ["sse.com.cn", "szse.cn", "hkexnews.hk", "cninfo.com.cn"]):
        return "exchange"
    if any(word in text for word in ["公告", "年报", "公司", "企业官网", "developer"]):
        return "company"
    if any(word in text for word in ["中指", "克而瑞", "贝壳", "诸葛", "研究院", "评级"]):
        return "institution"
    if any(word in text for word in ["news", "证券", "财经", "日报", "时报"]):
        return "media"
    return "unknown"


def _has_metrics(text: str) -> bool:
    return bool(re.search(r"\d+(?:\.\d+)?\s*(?:%|亿元|万平方米|㎡|宗|个百分点)", text))


def _limitations(
    evidence: List[Dict[str, Any]], required_materials: List[str], has_metrics: bool
) -> List[str]:
    limitations = []
    if not any(record.get("url") for record in evidence):
        limitations.append("缺少原始链接，输出只能作为报道线索。")
    if len(evidence) < 2:
        limitations.append("缺少第二独立来源，需交叉核验。")
    if not has_metrics:
        limitations.append("缺少关键量化指标，难以支撑趋势判断。")
    if required_materials:
        limitations.append("必备材料尚未全部取得前，不应写成确定结论。")
    return limitations


def _claim_boundary(status: str) -> str:
    if status == VERIFICATION_VERIFIED:
        return "可作为已核验事实使用，但仍需保留原始来源和统计口径。"
    if status == VERIFICATION_NEEDS_CHECK:
        return "可作为报道线索和采访方向，不应直接作为定论。"
    return "证据不足，只能进入观察池或资料补充环节。"


def _dedupe_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    keys = unique(
        f"{normalize_text(record.get('source'))}|{normalize_text(record.get('title'))}|{normalize_text(record.get('url'))}"
        for record in records
    )
    result = []
    for key in keys:
        for record in records:
            record_key = (
                f"{normalize_text(record.get('source'))}|"
                f"{normalize_text(record.get('title'))}|"
                f"{normalize_text(record.get('url'))}"
            )
            if record_key == key:
                result.append(record)
                break
    return result

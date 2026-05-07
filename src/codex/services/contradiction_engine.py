from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from codex.services.fact_check_engine import extract_claims, run_fact_check
from codex.services.text_utils import normalize_text

METRIC_TERMS = [
    "销售额", "销售金额", "净利润", "营收", "收入", "毛利率", "经营现金流", "在管面积", "合同面积",
    "拿地金额", "拿地面积", "库存", "去化", "负债", "减值",
]


def detect_contradictions(texts: List[Any], sources: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    documents = [_normalize_document(index, text) for index, text in enumerate(texts)]
    all_claims = []

    for document in documents:
        fact_check = run_fact_check(document["text"], sources=sources or [])
        for claim in fact_check["claims"]:
            enriched = dict(claim)
            enriched["document_id"] = document["id"]
            enriched["document_title"] = document["title"]
            enriched["metrics"] = _metrics(claim["text"])
            enriched["subjects"] = _subjects(claim["text"])
            all_claims.append(enriched)

    number_conflicts = _number_conflicts(all_claims)
    time_conflicts = _time_conflicts(all_claims)
    unsupported_strong_claims = _unsupported_strong_claims(texts, sources or [])

    contradictions = number_conflicts + time_conflicts + unsupported_strong_claims

    return {
        "claim_count": len(all_claims),
        "contradiction_count": len(contradictions),
        "contradictions": contradictions,
        "severity": _overall_severity(contradictions),
        "claim_boundary": "矛盾检测基于规则匹配和数字/时间抽取，只提示核查方向，不自动判定哪一方正确。",
    }


def _normalize_document(index: int, text: Any) -> Dict[str, str]:
    if isinstance(text, dict):
        return {
            "id": str(text.get("id") or f"doc_{index}"),
            "title": str(text.get("title") or f"document_{index}"),
            "text": normalize_text(" ".join(str(text.get(key, "")) for key in ("title", "summary", "content", "text"))),
        }
    return {"id": f"doc_{index}", "title": f"document_{index}", "text": normalize_text(text)}


def _metrics(text: str) -> List[str]:
    return [term for term in METRIC_TERMS if term in text]


def _subjects(text: str) -> List[str]:
    candidates = re.findall(r"([\u4e00-\u9fa5A-Za-z0-9]{2,16})(?:202\d年|净利润|销售额|销售金额|营收|收入|经营现金流|在管面积|合同面积|拿地)", text)
    return list(dict.fromkeys(candidates))


def _number_conflicts(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        for metric in claim.get("metrics", []):
            subject = claim.get("subjects", [""])[0] if claim.get("subjects") else "unknown"
            buckets[(subject, metric)].append(claim)

    conflicts = []
    for (subject, metric), grouped in buckets.items():
        values = _numeric_values(grouped)
        if len(set(values)) >= 2:
            conflicts.append(
                {
                    "type": "number_conflict",
                    "severity": "high",
                    "subject": subject,
                    "metric": metric,
                    "values": sorted(set(values)),
                    "claims": _claim_summaries(grouped),
                    "required_action": "核对该指标的统计口径、时间范围、单位和原始来源。",
                }
            )
    return conflicts


def _time_conflicts(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for claim in claims:
        for subject in claim.get("subjects", []) or ["unknown"]:
            if claim.get("dates"):
                buckets[subject].append(claim)

    conflicts = []
    for subject, grouped in buckets.items():
        date_values = sorted({date for claim in grouped for date in claim.get("dates", [])})
        if len(date_values) >= 2 and _same_event_keywords(grouped):
            conflicts.append(
                {
                    "type": "time_conflict",
                    "severity": "medium",
                    "subject": subject,
                    "dates": date_values,
                    "claims": _claim_summaries(grouped),
                    "required_action": "核对事件发生、公告披露、项目开工/停工等不同时间口径。",
                }
            )
    return conflicts


def _unsupported_strong_claims(texts: List[Any], sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    conflicts = []
    for text in texts:
        fact_check = run_fact_check(_normalize_document(0, text)["text"], sources=sources)
        for result in fact_check["verification"]["results"]:
            flags = result.get("risk_flags", [])
            if result["status"] in {"unsupported", "needs_verification"} and (
                "strong_causality" in flags or "absolute_expression" in flags
            ):
                conflicts.append(
                    {
                        "type": "unsupported_strong_claim",
                        "severity": "high",
                        "claim": result["claim"],
                        "risk_flags": flags,
                        "required_action": "删除绝对化/强因果表达，或补充一手证据和反向信息。",
                    }
                )
    return conflicts


def _numeric_values(claims: List[Dict[str, Any]]) -> List[str]:
    values = []
    for claim in claims:
        values.extend(str(number).replace(" ", "") for number in claim.get("numbers", []))
    return values


def _claim_summaries(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "document_id": claim.get("document_id"),
            "document_title": claim.get("document_title"),
            "claim": claim.get("text"),
            "numbers": claim.get("numbers", []),
            "dates": claim.get("dates", []),
        }
        for claim in claims
    ]


def _same_event_keywords(claims: List[Dict[str, Any]]) -> bool:
    keywords = ("停工", "开工", "披露", "公告", "交付", "销售", "拿地", "退出")
    hit_count = 0
    for keyword in keywords:
        if sum(1 for claim in claims if keyword in claim.get("text", "")) >= 2:
            hit_count += 1
    return hit_count > 0


def _overall_severity(contradictions: List[Dict[str, Any]]) -> str:
    if any(item.get("severity") == "high" for item in contradictions):
        return "high"
    if contradictions:
        return "medium"
    return "none"

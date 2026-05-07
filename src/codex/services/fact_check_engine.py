from __future__ import annotations

import re
from typing import Any, Dict, List

from codex.services.text_utils import normalize_text, unique

SOURCE_CREDIBILITY = {
    "official_disclosure": 95,
    "government_document": 92,
    "exchange_filing": 90,
    "annual_report": 88,
    "bond_prospectus": 85,
    "research_report": 70,
    "media_report": 60,
    "company_statement": 55,
    "anonymous_source": 40,
    "unknown": 20,
}

SOURCE_HINTS = {
    "公告": "exchange_filing",
    "年报": "annual_report",
    "财报": "annual_report",
    "政府": "government_document",
    "自然资源": "government_document",
    "募集说明书": "bond_prospectus",
    "专项债": "bond_prospectus",
    "研究报告": "research_report",
    "机构报告": "research_report",
    "媒体": "media_report",
    "公司称": "company_statement",
    "企业称": "company_statement",
    "匿名": "anonymous_source",
}

JUDGMENT_TERMS = ["表明", "意味着", "反映", "导致", "推动", "拖累", "证明", "显示"]
RISKY_ABSOLUTES = ["唯一", "首个", "第一", "最高", "最低", "全面领先", "彻底", "完全"]


def run_fact_check(text: Any, sources: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    normalized = normalize_text(text)
    claims = extract_claims(normalized)
    evidence = build_evidence_ledger(claims, sources or [])
    verification = assess_verification(claims, evidence)
    return {
        "claims": claims,
        "evidence_ledger": evidence,
        "verification": verification,
        "fact_check_summary": _summary(verification),
        "claim_boundary": "事实核查引擎只能标记风险和证据状态；不能替代人工核验原始文件、采访记录和数据口径。",
    }


def extract_claims(text: str) -> List[Dict[str, Any]]:
    sentences = _split_sentences(text)
    claims = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        claim_type = _claim_type(sentence)
        if claim_type == "background":
            continue
        claims.append(
            {
                "text": sentence,
                "type": claim_type,
                "numbers": _numbers(sentence),
                "dates": _dates(sentence),
                "risk_flags": _risk_flags(sentence),
                "source_type_hint": infer_source_type(sentence),
                "verification_status": "unchecked",
            }
        )
    return claims


def build_evidence_ledger(
    claims: List[Dict[str, Any]],
    sources: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    normalized_sources = [_normalize_source(source) for source in sources if isinstance(source, dict)]
    ledger = []
    for claim in claims:
        matches = _match_sources(claim, normalized_sources)
        ledger.append(
            {
                "claim": claim["text"],
                "claim_type": claim["type"],
                "matched_sources": matches,
                "best_source_score": max((source["credibility_score"] for source in matches), default=0),
                "source_count": len(matches),
            }
        )
    return ledger


def assess_verification(
    claims: List[Dict[str, Any]],
    evidence_ledger: List[Dict[str, Any]],
) -> Dict[str, Any]:
    results = []
    for claim, ledger in zip(claims, evidence_ledger):
        status = _status_for_claim(claim, ledger)
        results.append(
            {
                "claim": claim["text"],
                "type": claim["type"],
                "status": status,
                "risk_flags": claim.get("risk_flags", []),
                "source_count": ledger.get("source_count", 0),
                "best_source_score": ledger.get("best_source_score", 0),
                "required_action": _required_action(status, claim),
            }
        )
    status_counts: Dict[str, int] = {}
    for result in results:
        status_counts[result["status"]] = status_counts.get(result["status"], 0) + 1
    return {
        "claim_count": len(results),
        "status_counts": status_counts,
        "results": results,
        "overall_status": _overall_status(results),
    }


def infer_source_type(text: str) -> str:
    for hint, source_type in SOURCE_HINTS.items():
        if hint in text:
            return source_type
    return "unknown"


def source_credibility(source_type: str) -> int:
    return SOURCE_CREDIBILITY.get(source_type or "unknown", SOURCE_CREDIBILITY["unknown"])


def _claim_type(sentence: str) -> str:
    if _numbers(sentence):
        return "number"
    if _dates(sentence):
        return "time"
    if any(term in sentence for term in JUDGMENT_TERMS):
        return "judgment"
    if any(term in sentence for term in RISKY_ABSOLUTES):
        return "absolute"
    if any(term in sentence for term in ("称", "表示", "认为")):
        return "attribution"
    if len(sentence) >= 18:
        return "factual"
    return "background"


def _numbers(sentence: str) -> List[str]:
    return re.findall(r"[-+]?\d+(?:\.\d+)?\s*(?:%|亿元|万亿元|平方米|万平方米|亿平方米|套|宗|家|个|年|月)?", sentence)


def _dates(sentence: str) -> List[str]:
    return re.findall(r"20\d{2}年(?:\d{1,2}月)?(?:\d{1,2}日)?|20\d{2}-\d{1,2}(?:-\d{1,2})?", sentence)


def _risk_flags(sentence: str) -> List[str]:
    flags = []
    if any(term in sentence for term in RISKY_ABSOLUTES):
        flags.append("absolute_expression")
    if any(term in sentence for term in ("导致", "证明", "必然")):
        flags.append("strong_causality")
    if _numbers(sentence) and infer_source_type(sentence) == "unknown":
        flags.append("number_without_source")
    if any(term in sentence for term in JUDGMENT_TERMS) and infer_source_type(sentence) == "unknown":
        flags.append("judgment_without_source")
    return flags


def _normalize_source(source: Dict[str, Any]) -> Dict[str, Any]:
    source_type = str(source.get("source_type") or infer_source_type(str(source)) or "unknown")
    text = normalize_text(" ".join(str(source.get(key, "")) for key in ("title", "summary", "content", "text", "url")))
    return {
        "title": source.get("title") or source.get("name") or source_type,
        "source_type": source_type,
        "credibility_score": source_credibility(source_type),
        "text": text,
        "url": source.get("url"),
    }


def _match_sources(claim: Dict[str, Any], sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    claim_text = normalize_text(claim["text"])
    claim_numbers = set(claim.get("numbers", []))
    matches = []
    for source in sources:
        score = 0
        if any(number and number in source["text"] for number in claim_numbers):
            score += 40
        shared_terms = set(claim_text.split()) & set(source["text"].split())
        score += min(len(shared_terms) * 5, 25)
        if claim.get("source_type_hint") == source.get("source_type"):
            score += 20
        if score > 0:
            enriched = dict(source)
            enriched["match_score"] = min(score, 100)
            matches.append(enriched)
    return sorted(matches, key=lambda item: (item["credibility_score"], item["match_score"]), reverse=True)


def _status_for_claim(claim: Dict[str, Any], ledger: Dict[str, Any]) -> str:
    if claim.get("risk_flags") and ledger.get("best_source_score", 0) < 70:
        return "needs_verification"
    if ledger.get("best_source_score", 0) >= 85:
        return "supported_by_primary_source"
    if ledger.get("best_source_score", 0) >= 60:
        return "partially_supported"
    if claim.get("source_type_hint") in {"company_statement", "anonymous_source"}:
        return "attribution_required"
    return "unsupported"


def _required_action(status: str, claim: Dict[str, Any]) -> str:
    if status == "supported_by_primary_source":
        return "核对原始文件页码、发布日期和数据口径。"
    if status == "partially_supported":
        return "补充一手来源或交叉来源。"
    if status == "attribution_required":
        return "明确归属为企业说法、受访者说法或匿名信源，不写成媒体结论。"
    if status == "needs_verification":
        return "优先核验数字、绝对化表述或因果判断。"
    return "补充权威来源，否则删除或改写为待核验线索。"


def _overall_status(results: List[Dict[str, Any]]) -> str:
    if not results:
        return "no_claims"
    risky = [result for result in results if result["status"] in {"unsupported", "needs_verification"}]
    if risky:
        return "needs_verification"
    if any(result["status"] == "partially_supported" for result in results):
        return "partially_verified"
    return "verified_with_sources"


def _summary(verification: Dict[str, Any]) -> str:
    counts = verification.get("status_counts", {})
    return "；".join(f"{key}: {value}" for key, value in counts.items()) or "未识别需要核查的声明。"


def _split_sentences(text: str) -> List[str]:
    return [sentence for sentence in re.split(r"[。！？；;\n]", text) if sentence.strip()]

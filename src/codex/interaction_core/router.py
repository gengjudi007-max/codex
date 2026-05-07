from __future__ import annotations

from typing import Any, Dict


def infer_mode(payload: Dict[str, Any]) -> str:
    explicit_mode = str(payload.get("mode", ""))
    if explicit_mode:
        return explicit_mode
    if payload.get("propaganda_check") is True:
        return "propaganda_detect"
    if payload.get("rewrite_plan") is True:
        return "newsroom_rewrite_plan"
    if payload.get("risk_chain") is True:
        return "risk_chain"
    if payload.get("policy_semantics") is True:
        return "policy_semantics"
    if "companies" in payload:
        return "developer_compare"
    if "cities" in payload:
        return "city_land_compare"
    if any(key in payload for key in ("yearly", "disposal", "special_bonds")):
        return "city_investment_land"
    if "reports" in payload or "report" in payload:
        return "annual_report"
    if payload.get("tracking") is True:
        return "signal_monitor"
    if "sources" in payload:
        return "fetch_sources"
    if "query" in payload and "path" in payload:
        return "search_store"
    if "paths" in payload:
        return "parse_documents"
    if "path" in payload:
        return "import_terminal"
    if "ifind" in payload:
        return "ifind_query"
    if "query" in payload and ("store" in payload or "keyword" in payload):
        return "search_store"
    if "text" in payload and "items" not in payload:
        return "draft_edit"
    return "topic_pipeline"

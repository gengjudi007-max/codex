from __future__ import annotations

from typing import Any, Dict

from codex.interaction_core.defaults import DEFAULT_ITEMS, error_response, require_list
from codex.interaction_core.pipeline import message_to_item, run_topic_pipeline
from codex.services.annual_report_parser import parse_annual_reports
from codex.services.city_investment_land_model import build_city_investment_land_model
from codex.services.city_land_comparator import compare_city_land_markets
from codex.services.company_comparator import compare_developers
from codex.services.data_fetcher import fetch_source_dicts
from codex.services.document_parser import parse_documents
from codex.services.draft_editor import edit_draft
from codex.services.ifind_client import IFIndError, ifind_result_to_items, run_ifind_query
from codex.services.news_rewrite_planner import plan_newsroom_rewrite
from codex.services.policy_semantics import analyze_policy_semantics
from codex.services.propaganda_detector import detect_propaganda_style
from codex.services.risk_chain import analyze_risk_chain
from codex.services.signal_monitor import monitor_signals
from codex.services.source_store import search_jsonl, summarize_jsonl
from codex.services.terminal_importer import import_terminal_file


HANDLERS = {
    "propaganda_detect": lambda payload: _propaganda_detect(payload),
    "newsroom_rewrite_plan": lambda payload: _rewrite_plan(payload),
    "policy_semantics": lambda payload: _policy_semantics(payload),
    "risk_chain": lambda payload: _risk_chain(payload),
    "developer_compare": lambda payload: _developer_compare(payload),
    "city_land_compare": lambda payload: _city_land_compare(payload),
    "city_investment_land": lambda payload: _city_investment_land(payload),
    "annual_report": lambda payload: _annual_report(payload),
    "draft_edit": lambda payload: _draft_edit(payload),
    "signal_monitor": lambda payload: _signal_monitor(payload),
    "fetch_sources": lambda payload: _fetch_sources(payload),
    "parse_documents": lambda payload: _parse_documents(payload),
    "import_terminal": lambda payload: _import_terminal(payload),
    "ifind_query": lambda payload: _ifind_query(payload),
    "search_store": lambda payload: _search_store(payload),
    "topic_pipeline": lambda payload: _topic_pipeline(payload),
}


def dispatch(mode: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    handler = HANDLERS.get(mode)
    if not handler:
        return error_response(f"未知模式: {mode}", mode)
    try:
        return handler(payload)
    except Exception as exc:  # noqa: BLE001
        return error_response(str(exc), mode)


def _propaganda_detect(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = str(payload.get("text") or payload.get("message") or "")
    if not text.strip():
        return error_response("propaganda_detect 模式需要 text 或 message。", "propaganda_detect")
    return {"mode": "propaganda_detect", "result": detect_propaganda_style(text)}


def _rewrite_plan(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = str(payload.get("text") or payload.get("message") or "")
    if not text.strip():
        return error_response("newsroom_rewrite_plan 模式需要 text 或 message。", "newsroom_rewrite_plan")
    return {"mode": "newsroom_rewrite_plan", "result": plan_newsroom_rewrite(text)}


def _policy_semantics(payload: Dict[str, Any]) -> Dict[str, Any]:
    current = payload.get("current") or payload.get("text") or payload.get("message") or ""
    previous = payload.get("previous") or ""
    return {"mode": "policy_semantics", "result": analyze_policy_semantics(current, previous)}


def _risk_chain(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"mode": "risk_chain", "result": analyze_risk_chain(payload)}


def _developer_compare(payload: Dict[str, Any]) -> Dict[str, Any]:
    ok, error = require_list(payload, "companies")
    if not ok:
        return error_response(error, "developer_compare")
    return {"mode": "developer_compare", "result": compare_developers(payload.get("companies", []))}


def _city_land_compare(payload: Dict[str, Any]) -> Dict[str, Any]:
    ok, error = require_list(payload, "cities")
    if not ok:
        return error_response(error, "city_land_compare")
    return {"mode": "city_land_compare", "result": compare_city_land_markets(payload.get("cities", []))}


def _city_investment_land(payload: Dict[str, Any]) -> Dict[str, Any]:
    for key in ("yearly", "disposal", "special_bonds"):
        if key in payload and not isinstance(payload.get(key), list):
            return error_response(f"{key} 必须是列表。", "city_investment_land")
    return {"mode": "city_investment_land", "result": build_city_investment_land_model(payload)}


def _annual_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    reports = payload.get("reports")
    if reports is None and "report" in payload:
        reports = [payload["report"]]
    if not isinstance(reports, list):
        return error_response("annual_report 模式需要 reports 列表或 report 对象。", "annual_report")
    parsed_items = parse_annual_reports(reports)
    return {"mode": "annual_report", "result": {"parsed_reports": parsed_items, "topic_pipeline": run_topic_pipeline(parsed_items)}}


def _draft_edit(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = str(payload.get("text") or payload.get("message") or "")
    if not text.strip():
        return error_response("draft_edit 模式需要 text 或 message。", "draft_edit")
    return {"mode": "draft_edit", "result": edit_draft(text)}


def _signal_monitor(payload: Dict[str, Any]) -> Dict[str, Any]:
    ok, error = require_list(payload, "items")
    if not ok:
        return error_response(error, "signal_monitor")
    return {"mode": "signal_monitor", "result": monitor_signals(payload.get("items", []))}


def _fetch_sources(payload: Dict[str, Any]) -> Dict[str, Any]:
    ok, error = require_list(payload, "sources")
    if not ok:
        return error_response(error, "fetch_sources")
    return {"mode": "fetch_sources", "result": fetch_source_dicts(payload.get("sources", []))}


def _parse_documents(payload: Dict[str, Any]) -> Dict[str, Any]:
    ok, error = require_list(payload, "paths")
    if not ok:
        return error_response(error, "parse_documents")
    return {"mode": "parse_documents", "result": parse_documents(payload.get("paths", []), source=str(payload.get("source") or "document"))}


def _import_terminal(payload: Dict[str, Any]) -> Dict[str, Any]:
    path = str(payload.get("path") or "")
    if not path:
        return error_response("import_terminal 模式需要 path。", "import_terminal")
    return {"mode": "import_terminal", "result": import_terminal_file(path, source=str(payload.get("source") or "terminal"))}


def _ifind_query(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        result = run_ifind_query(payload)
    except IFIndError as exc:
        return error_response(str(exc), "ifind_query")
    return {"mode": "ifind_query", "result": {"raw": result, "items": ifind_result_to_items(result)}}


def _search_store(payload: Dict[str, Any]) -> Dict[str, Any]:
    path = str(payload.get("path") or payload.get("store") or "data/source_items.jsonl")
    query = str(payload.get("query") or payload.get("keyword") or "")
    limit = int(payload.get("limit", 20))
    offset = int(payload.get("offset", 0))
    return {"mode": "search_store", "result": {"search": search_jsonl(path, query=query, limit=limit, offset=offset), "summary": summarize_jsonl(path)}}


def _topic_pipeline(payload: Dict[str, Any]) -> Dict[str, Any]:
    items = payload.get("items")
    if items is not None and not isinstance(items, list):
        return error_response("items 必须是列表。", "topic_pipeline")
    if not items:
        message = str(payload.get("message", "")).strip()
        items = [message_to_item(message)] if message else DEFAULT_ITEMS
    return {"mode": "topic_pipeline", "result": run_topic_pipeline(items)}

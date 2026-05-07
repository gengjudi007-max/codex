from __future__ import annotations

from typing import Any, Dict, List, Tuple

from codex.services.annual_report_parser import parse_annual_reports
from codex.services.bulk_importer import import_paths
from codex.services.city_investment_land_model import build_city_investment_land_model
from codex.services.city_land_comparator import compare_city_land_markets
from codex.services.company_comparator import compare_developers
from codex.services.data_fetcher import fetch_source_dicts
from codex.services.document_parser import parse_documents
from codex.services.draft_editor import edit_draft
from codex.services.evidence import attach_credibility
from codex.services.ifind_client import ifind_result_to_items, run_ifind_query
from codex.services.interview_planner import plan_interview
from codex.services.material_builder import build_materials
from codex.services.photo_planner import plan_photography
from codex.services.signal_monitor import monitor_signals
from codex.services.source_store import (
    append_jsonl,
    dedupe_items,
    load_jsonl,
    search_jsonl,
    summarize_jsonl,
)
from codex.services.terminal_importer import import_terminal_file
from codex.services.text_utils import compact_text, infer_city, infer_company
from codex.services.topic_finder import find_topics
from codex.services.topic_scoring import score_topics


DEFAULT_ITEMS: List[Dict[str, Any]] = [
    {
        "source": "policy",
        "title": "政治局会议提出努力稳定房地产市场",
        "summary": "政策强调努力稳定房地产市场，后续地方可能继续因城施策。",
    },
    {
        "source": "announcement",
        "company": "保利发展",
        "title": "保利发展净利润同比下降40%",
        "summary": "利润下滑与资产减值增加，经营现金流仍需观察。",
    },
    {
        "source": "land",
        "city": "武汉",
        "title": "武汉土拍城投占比超70%",
        "summary": "土地市场仍依赖地方平台托底，需追踪后续开工和收储路径。",
    },
]


def analyze_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Route structured or free-text input to the matching reporting model."""
    if not isinstance(payload, dict):
        return _error("payload 必须是 JSON 对象。")

    mode = payload.get("mode") or _infer_mode(payload)

    if mode == "developer_compare":
        ok, error = _require_list(payload, "companies")
        if not ok:
            return _error(error, mode)
        return {
            "mode": mode,
            "result": compare_developers(payload.get("companies", [])),
        }

    if mode == "city_land_compare":
        ok, error = _require_list(payload, "cities")
        if not ok:
            return _error(error, mode)
        return {
            "mode": mode,
            "result": compare_city_land_markets(payload.get("cities", [])),
        }

    if mode == "city_investment_land":
        for key in ("yearly", "disposal", "special_bonds"):
            if key in payload and not isinstance(payload.get(key), list):
                return _error(f"{key} 必须是列表。", mode)
        return {
            "mode": mode,
            "result": build_city_investment_land_model(payload),
        }

    if mode == "annual_report":
        reports = payload.get("reports")
        if reports is None and "report" in payload:
            reports = [payload["report"]]
        if not isinstance(reports, list):
            return _error("annual_report 模式需要 reports 列表或 report 对象。", mode)
        parsed_items = parse_annual_reports(reports)
        return {
            "mode": mode,
            "result": {
                "parsed_reports": parsed_items,
                "topic_pipeline": run_topic_pipeline(parsed_items),
            },
        }

    if mode == "draft_edit":
        text = str(payload.get("text") or payload.get("message") or "")
        if not text.strip():
            return _error("draft_edit 模式需要 text 或 message。", mode)
        return {
            "mode": mode,
            "result": edit_draft(text),
        }

    if mode == "signal_monitor":
        ok, error = _require_list(payload, "items")
        if not ok:
            return _error(error, mode)
        return {
            "mode": mode,
            "result": monitor_signals(payload.get("items", [])),
        }

    if mode == "fetch_sources":
        ok, error = _require_list(payload, "sources")
        if not ok:
            return _error(error, mode)
        timeout = int(payload.get("timeout", 15))
        fetched = fetch_source_dicts(payload.get("sources", []), timeout=timeout)
        store_result = None
        if payload.get("store_path"):
            store_result = append_jsonl(str(payload.get("store_path")), fetched)
        return {
            "mode": mode,
            "result": {
                "fetched": fetched,
                "store": store_result,
                "topic_pipeline": run_topic_pipeline(fetched),
                "signal_monitor": monitor_signals(fetched),
            },
        }

    if mode == "import_terminal":
        path = str(payload.get("path") or "")
        if not path:
            return _error("import_terminal 模式需要 path。", mode)
        imported = import_terminal_file(path, source=str(payload.get("source") or "terminal"))
        return {
            "mode": mode,
            "result": {
                **imported,
                "topic_pipeline": run_topic_pipeline(imported["items"]),
                "signal_monitor": monitor_signals(imported["items"]),
                "city_land_compare": compare_city_land_markets(
                    imported["city_land_payload"].get("cities", [])
                )
                if imported["city_land_payload"].get("cities")
                else None,
            },
        }

    if mode == "parse_documents":
        ok, error = _require_list(payload, "paths")
        if not ok:
            return _error(error, mode)
        items = parse_documents(payload.get("paths", []), source=str(payload.get("source") or "document"))
        return {
            "mode": mode,
            "result": {
                "items": items,
                "topic_pipeline": run_topic_pipeline(items),
                "signal_monitor": monitor_signals(items),
            },
        }

    if mode == "import_library":
        ok, error = _require_list(payload, "paths")
        if not ok:
            return _error(error, mode)
        output_path = str(payload.get("output_path") or "data/source_items.jsonl")
        imported = import_paths(
            payload.get("paths", []),
            output_path=output_path,
            source=str(payload.get("source") or "local_library"),
            max_files=payload.get("max_files"),
            per_file_timeout_seconds=int(payload.get("per_file_timeout_seconds", 20)),
        )
        items = load_jsonl(imported["output_path"])
        return {
            "mode": mode,
            "result": {
                **imported,
                "store_summary": summarize_jsonl(imported["output_path"]),
                "signal_monitor": monitor_signals(items),
            },
        }

    if mode == "store_items":
        ok, error = _require_list(payload, "items")
        if not ok:
            return _error(error, mode)
        path = str(payload.get("path") or "data/source_items.jsonl")
        unique_items = dedupe_items(payload.get("items", []))
        store_result = append_jsonl(path, unique_items)
        return {
            "mode": mode,
            "result": {
                **store_result,
                "items": unique_items,
            },
        }

    if mode == "load_store":
        path = str(payload.get("path") or "data/source_items.jsonl")
        items = load_jsonl(path)
        return {
            "mode": mode,
            "result": {
                "path": path,
                "items": items,
                "signal_monitor": monitor_signals(items),
            },
        }

    if mode == "store_summary":
        path = str(payload.get("path") or "data/source_items.jsonl")
        return {
            "mode": mode,
            "result": summarize_jsonl(path),
        }

    if mode == "search_store":
        path = str(payload.get("path") or "data/source_items.jsonl")
        query = str(payload.get("query") or payload.get("keyword") or "")
        limit = int(payload.get("limit", 20))
        offset = int(payload.get("offset", 0))
        return {
            "mode": mode,
            "result": search_jsonl(path, query=query, limit=limit, offset=offset),
        }

    if mode == "ifind_query":
        try:
            result = run_ifind_query(payload)
        except Exception as exc:  # noqa: BLE001
            return _error(str(exc), mode)
        items = ifind_result_to_items(result)
        return {
            "mode": mode,
            "result": {
                "ifind": result,
                "items": items,
                "topic_pipeline": run_topic_pipeline(items),
                "signal_monitor": monitor_signals(items),
            },
        }

    items = payload.get("items")
    if items is not None and not isinstance(items, list):
        return _error("items 必须是列表。", "topic_pipeline")

    if not items:
        message = str(payload.get("message", "")).strip()
        items = [_message_to_item(message)] if message else DEFAULT_ITEMS

    return {
        "mode": "topic_pipeline",
        "result": run_topic_pipeline(items),
    }


def run_topic_pipeline(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run topic discovery, scoring, material planning, and interview planning."""
    normalized_items = [_normalize_item(item) for item in items if isinstance(item, dict)]
    topics = score_topics(find_topics({"items": normalized_items}))
    enriched_topics = []

    for topic in topics:
        material_plan = build_materials(topic)
        interview_plan = plan_interview(topic)
        photo_plan = plan_photography(topic)
        source_item = topic.get("input_item") if isinstance(topic.get("input_item"), dict) else topic
        enriched = attach_credibility(
            {key: value for key, value in topic.items() if key != "input_item"},
            source_item,
            required_materials=material_plan.get("must_have", []),
        )
        enriched["material_plan"] = material_plan
        enriched["interview_plan"] = interview_plan
        enriched["photo_plan"] = photo_plan
        enriched_topics.append(enriched)

    return {
        "input_count": len(normalized_items),
        "topic_count": len(enriched_topics),
        "topics": enriched_topics,
        "warnings": _pipeline_warnings(items, normalized_items, enriched_topics),
        "message": _build_topic_message(enriched_topics),
    }


def _infer_mode(payload: Dict[str, Any]) -> str:
    explicit_mode = str(payload.get("mode", ""))
    if explicit_mode:
        return explicit_mode
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
    if "library_paths" in payload:
        payload["paths"] = payload["library_paths"]
        return "import_library"
    if "query" in payload and "path" in payload:
        return "search_store"
    if "path" in payload:
        return "import_terminal"
    if "paths" in payload:
        return "parse_documents"
    if "ifind" in payload:
        return "ifind_query"
    if "query" in payload and ("store" in payload or "keyword" in payload):
        return "search_store"
    if "text" in payload and "items" not in payload:
        return "draft_edit"
    return "topic_pipeline"


def _message_to_item(message: str) -> Dict[str, Any]:
    return {
        "source": "user",
        "title": compact_text(message, 60) or "用户输入",
        "summary": message,
        "content": message,
        "city": infer_city(message),
        "company": infer_company(message),
    }


def _build_topic_message(topics: List[Dict[str, Any]]) -> str:
    if not topics:
        return "暂未匹配到明确选题。可以补充政策措辞、公司公告、土地成交或金融工具等关键词。"

    top = topics[0]
    return f"已识别 {len(topics)} 个选题，优先处理：{top['topic']}（{top['priority']}，评分 {top['final_score']}）。"


def _normalize_item(item: Dict[str, Any]) -> Dict[str, Any]:
    text = " ".join(str(item.get(key, "")) for key in ("title", "summary", "content"))
    normalized = dict(item)
    normalized.setdefault("source", "unknown")
    normalized.setdefault("title", compact_text(text, 60) or "未命名信息源")
    normalized.setdefault("summary", text)
    if not normalized.get("city"):
        normalized["city"] = infer_city(text)
    if not normalized.get("company"):
        normalized["company"] = infer_company(text)
    return normalized


def _pipeline_warnings(
    original_items: List[Any],
    normalized_items: List[Dict[str, Any]],
    topics: List[Dict[str, Any]],
) -> List[str]:
    warnings = []
    dropped = len(original_items) - len(normalized_items)
    if dropped:
        warnings.append(f"已忽略 {dropped} 条非对象输入。")
    if normalized_items and not topics:
        warnings.append("未命中规则库，可补充政策、公告、土地、融资、城市更新或物业服务关键词。")
    return warnings


def _require_list(payload: Dict[str, Any], key: str) -> Tuple[bool, str]:
    if not isinstance(payload.get(key), list):
        return False, f"{key} 必须是列表。"
    return True, ""


def _error(message: str, mode: str = "unknown") -> Dict[str, Any]:
    return {
        "mode": mode,
        "error": message,
        "result": None,
    }

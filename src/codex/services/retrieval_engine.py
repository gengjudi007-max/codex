from __future__ import annotations

import json
import sqlite3
from collections import Counter
from typing import Any, Dict, List

from codex.services.sqlite_store import DEFAULT_DB_PATH, init_db, query_sources


def search_newsroom(query: str = "", db_path: str = DEFAULT_DB_PATH, limit: int = 20) -> Dict[str, Any]:
    """Search across persisted newsroom sources."""
    return {
        "mode": "search_newsroom",
        "sources": query_sources(query=query, db_path=db_path, limit=limit),
    }


def timeline_query(entity: str, db_path: str = DEFAULT_DB_PATH, limit: int = 50) -> Dict[str, Any]:
    init_db(db_path)
    like = f"%{entity}%"
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT * FROM memory_events
            WHERE title LIKE ? OR content LIKE ? OR city LIKE ? OR company LIKE ?
            ORDER BY COALESCE(occurred_at, created_at) ASC
            LIMIT ?
            """,
            (like, like, like, like, limit),
        ).fetchall()
    return {
        "mode": "timeline_query",
        "entity": entity,
        "event_count": len(rows),
        "timeline": [_memory_row(row) for row in rows],
    }


def entity_query(entity: str, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    like = f"%{entity}%"
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        source_rows = conn.execute(
            """
            SELECT * FROM sources
            WHERE title LIKE ? OR content LIKE ? OR city LIKE ? OR company LIKE ?
            ORDER BY id DESC LIMIT 50
            """,
            (like, like, like, like),
        ).fetchall()
        memory_rows = conn.execute(
            """
            SELECT * FROM memory_events
            WHERE title LIKE ? OR content LIKE ? OR city LIKE ? OR company LIKE ?
            ORDER BY COALESCE(occurred_at, created_at) DESC LIMIT 50
            """,
            (like, like, like, like),
        ).fetchall()
    risks = []
    chains = []
    for row in memory_rows:
        risks.extend(_json_list(row["risks_json"]))
        chains.extend(_json_list(row["risk_chains_json"]))
    return {
        "mode": "entity_query",
        "entity": entity,
        "source_count": len(source_rows),
        "memory_count": len(memory_rows),
        "risks": _top_values(risks),
        "risk_chains": _top_values(chains),
        "recent_sources": [_source_row(row) for row in source_rows[:10]],
        "recent_events": [_memory_row(row) for row in memory_rows[:10]],
    }


def claims_query(status: str = "", db_path: str = DEFAULT_DB_PATH, limit: int = 50) -> Dict[str, Any]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if status:
            rows = conn.execute(
                "SELECT * FROM claims WHERE status = ? ORDER BY id DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM claims ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return {
        "mode": "claims_query",
        "status": status,
        "claim_count": len(rows),
        "claims": [_claim_row(row) for row in rows],
    }


def alerts_query(db_path: str = DEFAULT_DB_PATH, limit: int = 50) -> Dict[str, Any]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return {
        "mode": "alerts_query",
        "alert_count": len(rows),
        "alerts": [_alert_row(row) for row in rows],
    }


def newsroom_summary(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        source_types = Counter(
            row["source_type"] or "unknown"
            for row in conn.execute("SELECT source_type FROM sources").fetchall()
        )
        claim_status = Counter(
            row["status"] or "unknown"
            for row in conn.execute("SELECT status FROM claims").fetchall()
        )
        alerts = conn.execute("SELECT COUNT(*) AS count FROM alerts").fetchone()["count"]
        runs = conn.execute("SELECT COUNT(*) AS count FROM run_logs").fetchone()["count"]
    return {
        "mode": "newsroom_summary",
        "db_path": db_path,
        "source_types": dict(source_types),
        "claim_status": dict(claim_status),
        "alert_count": alerts,
        "run_count": runs,
    }


def _source_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "source_type": row["source_type"],
        "source": row["source"],
        "url": row["url"],
        "city": row["city"],
        "company": row["company"],
        "created_at": row["created_at"],
    }


def _memory_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "occurred_at": row["occurred_at"],
        "city": row["city"],
        "company": row["company"],
        "risks": _json_list(row["risks_json"]),
        "risk_chains": _json_list(row["risk_chains_json"]),
        "created_at": row["created_at"],
    }


def _claim_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "claim": row["claim"],
        "claim_type": row["claim_type"],
        "status": row["status"],
        "source_count": row["source_count"],
        "best_source_score": row["best_source_score"],
        "created_at": row["created_at"],
    }


def _alert_row(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "level": row["level"],
        "message": row["message"],
        "source": row["source"],
        "created_at": row["created_at"],
    }


def _json_list(value: str | None) -> List[Any]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _top_values(values: List[Any], limit: int = 10) -> List[Dict[str, Any]]:
    counter = Counter(str(value) for value in values if value)
    return [{"value": value, "count": count} for value, count in counter.most_common(limit)]

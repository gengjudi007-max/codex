from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

DEFAULT_DB_PATH = "data/newsroom.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    source_type TEXT,
    source TEXT,
    url TEXT,
    city TEXT,
    company TEXT,
    content TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memory_events (
    id TEXT PRIMARY KEY,
    title TEXT,
    occurred_at TEXT,
    city TEXT,
    company TEXT,
    risks_json TEXT,
    risk_chains_json TEXT,
    content TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS run_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ran_at TEXT,
    status TEXT,
    alerts_json TEXT,
    payload_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim TEXT,
    claim_type TEXT,
    status TEXT,
    source_count INTEGER,
    best_source_score INTEGER,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT,
    message TEXT,
    source TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type);
CREATE INDEX IF NOT EXISTS idx_sources_city ON sources(city);
CREATE INDEX IF NOT EXISTS idx_sources_company ON sources(company);
CREATE INDEX IF NOT EXISTS idx_memory_city ON memory_events(city);
CREATE INDEX IF NOT EXISTS idx_memory_company ON memory_events(company);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
"""


def init_db(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
    return {"db_path": str(path), "status": "ok"}


def save_sources(items: Iterable[Dict[str, Any]], db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    count = 0
    with sqlite3.connect(db_path) as conn:
        for item in items:
            conn.execute(
                """
                INSERT INTO sources(title, source_type, source, url, city, company, content, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get("title"),
                    item.get("source_type") or item.get("type"),
                    item.get("source"),
                    item.get("url"),
                    item.get("city"),
                    item.get("company"),
                    item.get("content") or item.get("summary"),
                    json.dumps(item, ensure_ascii=False),
                    _now(),
                ),
            )
            count += 1
    return {"db_path": db_path, "written": count}


def save_memory_events(events: Iterable[Dict[str, Any]], db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    count = 0
    with sqlite3.connect(db_path) as conn:
        for event in events:
            event_id = str(event.get("id") or event.get("title") or count)
            conn.execute(
                """
                INSERT OR REPLACE INTO memory_events(
                    id, title, occurred_at, city, company, risks_json, risk_chains_json, content, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    event.get("title"),
                    event.get("occurred_at"),
                    event.get("city"),
                    event.get("company"),
                    json.dumps(event.get("risks", []), ensure_ascii=False),
                    json.dumps(event.get("risk_chains", []), ensure_ascii=False),
                    event.get("content") or event.get("summary"),
                    json.dumps(event, ensure_ascii=False),
                    _now(),
                ),
            )
            count += 1
    return {"db_path": db_path, "written": count}


def save_run_log(run_result: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    summary = run_result.get("summary", {})
    status = summary.get("overall_status") or "unknown"
    alerts = run_result.get("alerts", [])
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO run_logs(ran_at, status, alerts_json, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                run_result.get("ran_at"),
                status,
                json.dumps(alerts, ensure_ascii=False),
                json.dumps(run_result, ensure_ascii=False),
                _now(),
            ),
        )
    return {"db_path": db_path, "written": 1}


def save_claims(fact_check: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    results = fact_check.get("verification", {}).get("results", [])
    count = 0
    with sqlite3.connect(db_path) as conn:
        for result in results:
            conn.execute(
                """
                INSERT INTO claims(claim, claim_type, status, source_count, best_source_score, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.get("claim"),
                    result.get("type"),
                    result.get("status"),
                    result.get("source_count", 0),
                    result.get("best_source_score", 0),
                    json.dumps(result, ensure_ascii=False),
                    _now(),
                ),
            )
            count += 1
    return {"db_path": db_path, "written": count}


def save_alerts(alerts: Iterable[str], source: str = "continuous_runner", db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    count = 0
    with sqlite3.connect(db_path) as conn:
        for alert in alerts:
            conn.execute(
                """
                INSERT INTO alerts(level, message, source, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("info", alert, source, "{}", _now()),
            )
            count += 1
    return {"db_path": db_path, "written": count}


def query_sources(query: str = "", db_path: str = DEFAULT_DB_PATH, limit: int = 20) -> Dict[str, Any]:
    init_db(db_path)
    like = f"%{query}%"
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if query:
            rows = conn.execute(
                """
                SELECT * FROM sources
                WHERE title LIKE ? OR content LIKE ? OR city LIKE ? OR company LIKE ?
                ORDER BY id DESC LIMIT ?
                """,
                (like, like, like, like, limit),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM sources ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return {"matched": len(rows), "rows": [_row_to_dict(row) for row in rows]}


def db_summary(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        return {
            "db_path": db_path,
            "sources": _count(conn, "sources"),
            "memory_events": _count(conn, "memory_events"),
            "run_logs": _count(conn, "run_logs"),
            "claims": _count(conn, "claims"),
            "alerts": _count(conn, "alerts"),
        }


def _count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

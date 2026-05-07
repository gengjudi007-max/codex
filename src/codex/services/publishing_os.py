from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from codex.services.final_editorial_engine import final_edit_report
from codex.services.fact_check_engine import run_fact_check
from codex.services.sqlite_store import DEFAULT_DB_PATH, init_db

PUBLISHING_SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT,
    status TEXT NOT NULL,
    style TEXT,
    body TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS article_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    title TEXT,
    body TEXT,
    editor_note TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS publication_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    approver_role TEXT,
    note TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS distribution_routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    package_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS post_publication_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_versions_article ON article_versions(article_id);
CREATE INDEX IF NOT EXISTS idx_approvals_article ON publication_approvals(article_id);
CREATE INDEX IF NOT EXISTS idx_routes_article ON distribution_routes(article_id);
"""

ARTICLE_STATUSES = {"draft", "editing", "fact_check", "approved", "scheduled", "published", "blocked", "archived"}
APPROVAL_STAGES = {"editorial", "fact_check", "legal", "final"}
APPROVAL_STATUSES = {"pending", "approved", "changes_requested", "rejected"}
CHANNELS = {"cms", "newsletter", "archive", "social_brief", "internal_brief"}


def init_publishing_os(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(PUBLISHING_SCHEMA)
    return {"mode": "init_publishing_os", "db_path": db_path, "status": "ok"}


def create_article(
    title: str,
    body: str,
    style: str = "economic_observer",
    metadata: Dict[str, Any] | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    init_publishing_os(db_path)
    now = _now()
    slug = _slug(title)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO articles(title, slug, status, style, body, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, slug, "draft", style, body, json.dumps(metadata or {}, ensure_ascii=False), now, now),
        )
        article_id = int(cursor.lastrowid)
    add_article_version(article_id, title, body, "initial draft", metadata or {}, db_path=db_path)
    return get_article(article_id, db_path=db_path)


def package_article(article_id: int, channel: str = "archive", db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    if channel not in CHANNELS:
        raise ValueError(f"未知 channel: {channel}")
    article = get_article(article_id, db_path=db_path)
    if article.get("error"):
        return article
    title = article["article"]["title"]
    body = article["article"]["body"]
    package = _channel_package(title, body, channel)
    now = _now()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO distribution_routes(article_id, channel, status, package_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (article_id, channel, "packaged", json.dumps(package, ensure_ascii=False), now, now),
        )
    return {"article_id": article_id, "channel": channel, "status": "packaged", "package": package}


def prepare_final_package(
    payload: Dict[str, Any],
    style: str = "economic_observer",
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    final = final_edit_report(payload, style=style)
    title = final.get("headline") or payload.get("title") or "未命名稿件"
    body = final.get("edited_text") or payload.get("text") or ""
    fact_check = run_fact_check(body, sources=payload.get("sources", []))
    article = create_article(title, body, style=style, metadata={"final_editorial": final, "fact_check": fact_check}, db_path=db_path)
    article_id = article["article"]["id"]
    add_approval(article_id, "editorial", "pending", "责任编辑", "等待编辑确认。", db_path=db_path)
    add_approval(article_id, "fact_check", "pending", "事实核查", "等待核验核心事实。", db_path=db_path)
    package_article(article_id, "archive", db_path=db_path)
    return get_article(article_id, db_path=db_path)


def add_article_version(
    article_id: int,
    title: str,
    body: str,
    editor_note: str = "",
    metadata: Dict[str, Any] | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    init_publishing_os(db_path)
    with sqlite3.connect(db_path) as conn:
        current = conn.execute("SELECT MAX(version) FROM article_versions WHERE article_id = ?", (article_id,)).fetchone()[0]
        next_version = int(current or 0) + 1
        conn.execute(
            """
            INSERT INTO article_versions(article_id, version, title, body, editor_note, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (article_id, next_version, title, body, editor_note, json.dumps(metadata or {}, ensure_ascii=False), _now()),
        )
        conn.execute(
            "UPDATE articles SET title = ?, body = ?, updated_at = ? WHERE id = ?",
            (title, body, _now(), article_id),
        )
    return {"article_id": article_id, "version": next_version}


def add_approval(
    article_id: int,
    stage: str,
    status: str,
    approver_role: str,
    note: str = "",
    metadata: Dict[str, Any] | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    if stage not in APPROVAL_STAGES:
        raise ValueError(f"未知 approval stage: {stage}")
    if status not in APPROVAL_STATUSES:
        raise ValueError(f"未知 approval status: {status}")
    init_publishing_os(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO publication_approvals(article_id, stage, status, approver_role, note, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (article_id, stage, status, approver_role, note, json.dumps(metadata or {}, ensure_ascii=False), _now()),
        )
    _refresh_article_status(article_id, db_path)
    return get_article(article_id, db_path=db_path)


def mark_published(article_id: int, channel: str = "archive", db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    gate = publication_gate(article_id, db_path=db_path)
    if not gate.get("can_publish"):
        return {"article_id": article_id, "status": "blocked", "gate": gate}
    now = _now()
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE articles SET status = ?, updated_at = ? WHERE id = ?", ("published", now, article_id))
        conn.execute(
            """
            INSERT INTO post_publication_events(article_id, event_type, payload_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (article_id, "published", json.dumps({"channel": channel}, ensure_ascii=False), now),
        )
    return get_article(article_id, db_path=db_path)


def publication_gate(article_id: int, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    article = get_article(article_id, db_path=db_path)
    if article.get("error"):
        return article
    approvals = article.get("approvals", [])
    latest_by_stage: Dict[str, str] = {}
    for approval in approvals:
        latest_by_stage[approval["stage"]] = approval["status"]
    required = ["editorial", "fact_check", "final"]
    missing = [stage for stage in required if latest_by_stage.get(stage) != "approved"]
    can_publish = not missing
    return {"article_id": article_id, "can_publish": can_publish, "missing_approvals": missing, "latest_approvals": latest_by_stage}


def get_article(article_id: int, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_publishing_os(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        article = conn.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
        if not article:
            return {"error": "article not found", "article_id": article_id}
        versions = conn.execute("SELECT * FROM article_versions WHERE article_id = ? ORDER BY version ASC", (article_id,)).fetchall()
        approvals = conn.execute("SELECT * FROM publication_approvals WHERE article_id = ? ORDER BY id ASC", (article_id,)).fetchall()
        routes = conn.execute("SELECT * FROM distribution_routes WHERE article_id = ? ORDER BY id ASC", (article_id,)).fetchall()
        events = conn.execute("SELECT * FROM post_publication_events WHERE article_id = ? ORDER BY id ASC", (article_id,)).fetchall()
    return {
        "article": _row(article),
        "versions": [_row(row) for row in versions],
        "approvals": [_row(row) for row in approvals],
        "routes": [_row(row) for row in routes],
        "post_publication_events": [_row(row) for row in events],
    }


def publishing_board(db_path: str = DEFAULT_DB_PATH, status: str = "") -> Dict[str, Any]:
    init_publishing_os(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if status:
            rows = conn.execute("SELECT * FROM articles WHERE status = ? ORDER BY updated_at DESC", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM articles ORDER BY updated_at DESC").fetchall()
    return {"mode": "publishing_board", "status": status, "count": len(rows), "articles": [_row(row) for row in rows]}


def record_post_publication_event(article_id: int, event_type: str, payload: Dict[str, Any], db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_publishing_os(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO post_publication_events(article_id, event_type, payload_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (article_id, event_type, json.dumps(payload, ensure_ascii=False), _now()),
        )
    return get_article(article_id, db_path=db_path)


def _refresh_article_status(article_id: int, db_path: str) -> None:
    gate = publication_gate(article_id, db_path=db_path)
    status = "approved" if gate.get("can_publish") else "fact_check"
    with sqlite3.connect(db_path) as conn:
        conn.execute("UPDATE articles SET status = ?, updated_at = ? WHERE id = ?", (status, _now(), article_id))


def _channel_package(title: str, body: str, channel: str) -> Dict[str, Any]:
    if channel == "social_brief":
        return {"title": title, "body": body[:180], "format": "short_text"}
    if channel == "newsletter":
        return {"subject": title, "body": body, "format": "newsletter"}
    if channel == "internal_brief":
        return {"headline": title, "summary": body[:500], "format": "internal_brief"}
    return {"title": title, "body": body, "format": channel}


def _slug(title: str) -> str:
    raw = "".join(ch if ch.isalnum() else "-" for ch in title.lower()).strip("-")
    return raw[:80] or "article"


def _row(row: sqlite3.Row) -> Dict[str, Any]:
    data = {key: row[key] for key in row.keys()}
    for key in ("metadata_json", "package_json", "payload_json"):
        if key in data:
            try:
                data[key.replace("_json", "")] = json.loads(data[key] or "{}")
            except json.JSONDecodeError:
                data[key.replace("_json", "")] = {}
    return data


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from codex.services.sqlite_store import DEFAULT_DB_PATH, init_db

COLLAB_SCHEMA = """
CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    status TEXT NOT NULL,
    owner_role TEXT,
    editor_role TEXT,
    priority TEXT,
    due_at TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS editorial_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    reviewer_role TEXT,
    notes TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS verification_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER,
    claim TEXT,
    source_needed TEXT,
    status TEXT NOT NULL,
    evidence TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS story_lifecycle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assignment_id INTEGER,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    summary TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_assignments_status ON assignments(status);
CREATE INDEX IF NOT EXISTS idx_reviews_assignment ON editorial_reviews(assignment_id);
CREATE INDEX IF NOT EXISTS idx_verification_assignment ON verification_tasks(assignment_id);
CREATE INDEX IF NOT EXISTS idx_lifecycle_assignment ON story_lifecycle(assignment_id);
"""

ASSIGNMENT_STATUSES = {"new", "assigned", "reporting", "drafting", "editing", "blocked", "ready_for_publish", "published", "killed"}
REVIEW_STAGES = {"topic_review", "reporting_review", "draft_review", "fact_check", "legal_review", "final_review"}
VERIFICATION_STATUSES = {"open", "in_progress", "verified", "unsupported", "waived"}


def init_collaboration_os(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(COLLAB_SCHEMA)
    return {"mode": "init_collaboration_os", "db_path": db_path, "status": "ok"}


def create_assignment(
    topic: str,
    owner_role: str = "房地产财经记者",
    editor_role: str = "深度报道编辑",
    priority: str = "medium",
    due_at: str = "",
    metadata: Dict[str, Any] | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    init_collaboration_os(db_path)
    now = _now()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO assignments(topic, status, owner_role, editor_role, priority, due_at, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (topic, "new", owner_role, editor_role, priority, due_at, json.dumps(metadata or {}, ensure_ascii=False), now, now),
        )
        assignment_id = int(cursor.lastrowid)
    record_lifecycle(assignment_id, "assignment_created", "done", f"创建选题：{topic}", db_path=db_path)
    return get_assignment(assignment_id, db_path=db_path)


def update_assignment_status(assignment_id: int, status: str, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    if status not in ASSIGNMENT_STATUSES:
        raise ValueError(f"未知 assignment status: {status}")
    init_collaboration_os(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE assignments SET status = ?, updated_at = ? WHERE id = ?",
            (status, _now(), assignment_id),
        )
    record_lifecycle(assignment_id, f"status:{status}", "done", f"选题状态更新为 {status}", db_path=db_path)
    return get_assignment(assignment_id, db_path=db_path)


def add_editorial_review(
    assignment_id: int,
    stage: str,
    status: str,
    reviewer_role: str,
    notes: str,
    metadata: Dict[str, Any] | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    if stage not in REVIEW_STAGES:
        raise ValueError(f"未知 review stage: {stage}")
    init_collaboration_os(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO editorial_reviews(assignment_id, stage, status, reviewer_role, notes, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (assignment_id, stage, status, reviewer_role, notes, json.dumps(metadata or {}, ensure_ascii=False), _now()),
        )
    record_lifecycle(assignment_id, f"review:{stage}", status, notes, db_path=db_path)
    return get_assignment(assignment_id, db_path=db_path)


def add_verification_task(
    assignment_id: int,
    claim: str,
    source_needed: str,
    metadata: Dict[str, Any] | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    init_collaboration_os(db_path)
    now = _now()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO verification_tasks(assignment_id, claim, source_needed, status, evidence, metadata_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (assignment_id, claim, source_needed, "open", "", json.dumps(metadata or {}, ensure_ascii=False), now, now),
        )
    record_lifecycle(assignment_id, "verification_task_created", "open", claim, db_path=db_path)
    return get_assignment(assignment_id, db_path=db_path)


def update_verification_task(
    task_id: int,
    status: str,
    evidence: str = "",
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    if status not in VERIFICATION_STATUSES:
        raise ValueError(f"未知 verification status: {status}")
    init_collaboration_os(db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT assignment_id FROM verification_tasks WHERE id = ?", (task_id,)).fetchone()
        assignment_id = int(row[0]) if row else 0
        conn.execute(
            "UPDATE verification_tasks SET status = ?, evidence = ?, updated_at = ? WHERE id = ?",
            (status, evidence, _now(), task_id),
        )
    if assignment_id:
        record_lifecycle(assignment_id, "verification_task_updated", status, evidence or f"task {task_id}", db_path=db_path)
        return get_assignment(assignment_id, db_path=db_path)
    return {"error": "verification task not found", "task_id": task_id}


def record_lifecycle(
    assignment_id: int,
    stage: str,
    status: str,
    summary: str,
    metadata: Dict[str, Any] | None = None,
    db_path: str = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    init_collaboration_os(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO story_lifecycle(assignment_id, stage, status, summary, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (assignment_id, stage, status, summary, json.dumps(metadata or {}, ensure_ascii=False), _now()),
        )
    return {"assignment_id": assignment_id, "stage": stage, "status": status}


def get_assignment(assignment_id: int, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_collaboration_os(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        assignment = conn.execute("SELECT * FROM assignments WHERE id = ?", (assignment_id,)).fetchone()
        if not assignment:
            return {"error": "assignment not found", "assignment_id": assignment_id}
        reviews = conn.execute("SELECT * FROM editorial_reviews WHERE assignment_id = ? ORDER BY id ASC", (assignment_id,)).fetchall()
        tasks = conn.execute("SELECT * FROM verification_tasks WHERE assignment_id = ? ORDER BY id ASC", (assignment_id,)).fetchall()
        lifecycle = conn.execute("SELECT * FROM story_lifecycle WHERE assignment_id = ? ORDER BY id ASC", (assignment_id,)).fetchall()
    return {
        "assignment": _row(assignment),
        "reviews": [_row(row) for row in reviews],
        "verification_tasks": [_row(row) for row in tasks],
        "lifecycle": [_row(row) for row in lifecycle],
        "publication_gate": _publication_gate([_row(row) for row in tasks], [_row(row) for row in reviews]),
    }


def assignment_board(db_path: str = DEFAULT_DB_PATH, status: str = "") -> Dict[str, Any]:
    init_collaboration_os(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if status:
            rows = conn.execute("SELECT * FROM assignments WHERE status = ? ORDER BY updated_at DESC", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM assignments ORDER BY updated_at DESC").fetchall()
    return {"mode": "assignment_board", "status": status, "count": len(rows), "assignments": [_row(row) for row in rows]}


def collaboration_summary(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_collaboration_os(db_path)
    with sqlite3.connect(db_path) as conn:
        return {
            "mode": "collaboration_summary",
            "assignments": _count(conn, "assignments"),
            "reviews": _count(conn, "editorial_reviews"),
            "verification_tasks": _count(conn, "verification_tasks"),
            "lifecycle_events": _count(conn, "story_lifecycle"),
        }


def _publication_gate(tasks: List[Dict[str, Any]], reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
    open_tasks = [task for task in tasks if task.get("status") in {"open", "in_progress"}]
    unsupported = [task for task in tasks if task.get("status") == "unsupported"]
    final_reviews = [review for review in reviews if review.get("stage") == "final_review"]
    can_publish = not open_tasks and not unsupported and any(review.get("status") in {"approved", "pass"} for review in final_reviews)
    return {
        "can_publish": can_publish,
        "open_verification_count": len(open_tasks),
        "unsupported_count": len(unsupported),
        "has_final_approval": any(review.get("status") in {"approved", "pass"} for review in final_reviews),
    }


def _count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def _row(row: sqlite3.Row) -> Dict[str, Any]:
    data = {key: row[key] for key in row.keys()}
    for key in ("metadata_json",):
        if key in data:
            try:
                data[key.replace("_json", "")] = json.loads(data[key] or "{}")
            except json.JSONDecodeError:
                data[key.replace("_json", "")] = {}
    return data


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

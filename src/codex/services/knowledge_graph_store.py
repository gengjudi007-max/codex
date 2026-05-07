from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

from codex.services.sqlite_store import DEFAULT_DB_PATH, init_db

GRAPH_SCHEMA = """
CREATE TABLE IF NOT EXISTS kg_nodes (
    id TEXT PRIMARY KEY,
    node_type TEXT,
    label TEXT,
    metadata_json TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS kg_edges (
    id TEXT PRIMARY KEY,
    source_id TEXT,
    target_id TEXT,
    relation TEXT,
    weight INTEGER DEFAULT 1,
    metadata_json TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kg_nodes_type ON kg_nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_kg_edges_source ON kg_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_kg_edges_target ON kg_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_kg_edges_relation ON kg_edges(relation);
"""


def init_knowledge_graph(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(GRAPH_SCHEMA)
    return {"db_path": db_path, "status": "ok"}


def rebuild_knowledge_graph(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_knowledge_graph(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("DELETE FROM kg_edges")
        conn.execute("DELETE FROM kg_nodes")

        sources = conn.execute("SELECT * FROM sources").fetchall()
        memory = conn.execute("SELECT * FROM memory_events").fetchall()
        claims = conn.execute("SELECT * FROM claims").fetchall()
        alerts = conn.execute("SELECT * FROM alerts").fetchall()

        node_count = 0
        edge_count = 0

        for row in sources:
            source_id = f"source:{row['id']}"
            node_count += _upsert_node(conn, source_id, "source", row["title"] or source_id, _row(row))
            for entity_id, entity_type, label in _source_entities(row):
                node_count += _upsert_node(conn, entity_id, entity_type, label, {})
                edge_count += _upsert_edge(conn, source_id, entity_id, "mentions", 1, {})

        for row in memory:
            event_id = f"event:{row['id']}"
            node_count += _upsert_node(conn, event_id, "event", row["title"] or event_id, _row(row))
            for entity_id, entity_type, label in _memory_entities(row):
                node_count += _upsert_node(conn, entity_id, entity_type, label, {})
                edge_count += _upsert_edge(conn, event_id, entity_id, "mentions", 2, {})

        for row in claims:
            claim_id = f"claim:{row['id']}"
            node_count += _upsert_node(conn, claim_id, "claim", row["claim"] or claim_id, _row(row))
            if row["status"]:
                status_id = f"claim_status:{row['status']}"
                node_count += _upsert_node(conn, status_id, "claim_status", row["status"], {})
                edge_count += _upsert_edge(conn, claim_id, status_id, "has_status", 1, {})

        for row in alerts:
            alert_id = f"alert:{row['id']}"
            node_count += _upsert_node(conn, alert_id, "alert", row["message"] or alert_id, _row(row))
            if row["source"]:
                source_id = f"alert_source:{row['source']}"
                node_count += _upsert_node(conn, source_id, "alert_source", row["source"], {})
                edge_count += _upsert_edge(conn, alert_id, source_id, "from_source", 1, {})

    return {
        "mode": "rebuild_knowledge_graph",
        "db_path": db_path,
        "node_writes": node_count,
        "edge_writes": edge_count,
        "summary": knowledge_graph_summary(db_path),
    }


def knowledge_graph_summary(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    init_knowledge_graph(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        node_types = Counter(row["node_type"] for row in conn.execute("SELECT node_type FROM kg_nodes"))
        relations = Counter(row["relation"] for row in conn.execute("SELECT relation FROM kg_edges"))
        top_edges = conn.execute(
            "SELECT source_id, target_id, relation, weight FROM kg_edges ORDER BY weight DESC LIMIT 20"
        ).fetchall()
    return {
        "mode": "knowledge_graph_summary",
        "node_types": dict(node_types),
        "relations": dict(relations),
        "top_edges": [dict(row) for row in top_edges],
    }


def related_entities(entity: str, db_path: str = DEFAULT_DB_PATH, limit: int = 20) -> Dict[str, Any]:
    init_knowledge_graph(db_path)
    entity_like = f"%{entity}%"
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        nodes = conn.execute(
            "SELECT id FROM kg_nodes WHERE label LIKE ? OR id LIKE ? LIMIT 20",
            (entity_like, entity_like),
        ).fetchall()
        node_ids = [row["id"] for row in nodes]
        related = []
        for node_id in node_ids:
            rows = conn.execute(
                """
                SELECT e.source_id, e.target_id, e.relation, e.weight,
                       ns.label AS source_label, nt.label AS target_label,
                       ns.node_type AS source_type, nt.node_type AS target_type
                FROM kg_edges e
                LEFT JOIN kg_nodes ns ON e.source_id = ns.id
                LEFT JOIN kg_nodes nt ON e.target_id = nt.id
                WHERE e.source_id = ? OR e.target_id = ?
                ORDER BY e.weight DESC LIMIT ?
                """,
                (node_id, node_id, limit),
            ).fetchall()
            related.extend(dict(row) for row in rows)
    return {
        "mode": "related_entities",
        "entity": entity,
        "matched_nodes": node_ids,
        "related_count": len(related),
        "relations": related[:limit],
    }


def risk_propagation(risk: str, db_path: str = DEFAULT_DB_PATH, limit: int = 30) -> Dict[str, Any]:
    init_knowledge_graph(db_path)
    risk_node = f"risk:{risk}"
    related = related_entities(risk_node, db_path=db_path, limit=limit)
    cities = []
    companies = []
    events = []
    for rel in related.get("relations", []):
        for label_key, type_key in (("source_label", "source_type"), ("target_label", "target_type")):
            if rel.get(type_key) == "city":
                cities.append(rel.get(label_key))
            elif rel.get(type_key) == "company":
                companies.append(rel.get(label_key))
            elif rel.get(type_key) == "event":
                events.append(rel.get(label_key))
    return {
        "mode": "risk_propagation",
        "risk": risk,
        "cities": _unique(cities),
        "companies": _unique(companies),
        "events": _unique(events),
        "relations": related.get("relations", []),
    }


def knowledge_map(entity: str = "", db_path: str = DEFAULT_DB_PATH, limit: int = 50) -> Dict[str, Any]:
    init_knowledge_graph(db_path)
    if entity:
        rels = related_entities(entity, db_path=db_path, limit=limit).get("relations", [])
        node_ids = set()
        for rel in rels:
            node_ids.add(rel["source_id"])
            node_ids.add(rel["target_id"])
    else:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rels = [dict(row) for row in conn.execute(
                "SELECT source_id, target_id, relation, weight FROM kg_edges ORDER BY weight DESC LIMIT ?",
                (limit,),
            ).fetchall()]
        node_ids = {rel["source_id"] for rel in rels} | {rel["target_id"] for rel in rels}

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        nodes = []
        for node_id in node_ids:
            row = conn.execute("SELECT * FROM kg_nodes WHERE id = ?", (node_id,)).fetchone()
            if row:
                nodes.append(dict(row))
    return {"mode": "knowledge_map", "entity": entity, "nodes": nodes, "edges": rels}


def _source_entities(row: sqlite3.Row) -> List[Tuple[str, str, str]]:
    entities = []
    if row["city"]:
        entities.append((f"city:{row['city']}", "city", row["city"]))
    if row["company"]:
        entities.append((f"company:{row['company']}", "company", row["company"]))
    if row["source_type"]:
        entities.append((f"source_type:{row['source_type']}", "source_type", row["source_type"]))
    return entities


def _memory_entities(row: sqlite3.Row) -> List[Tuple[str, str, str]]:
    entities = _source_entities(row)
    for risk in _json_list(row["risks_json"]):
        entities.append((f"risk:{risk}", "risk", str(risk)))
    for chain in _json_list(row["risk_chains_json"]):
        entities.append((f"risk_chain:{chain}", "risk_chain", str(chain)))
    return entities


def _upsert_node(conn: sqlite3.Connection, node_id: str, node_type: str, label: str, metadata: Dict[str, Any]) -> int:
    conn.execute(
        """
        INSERT OR REPLACE INTO kg_nodes(id, node_type, label, metadata_json, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (node_id, node_type, label, json.dumps(metadata, ensure_ascii=False)),
    )
    return 1


def _upsert_edge(conn: sqlite3.Connection, source_id: str, target_id: str, relation: str, weight: int, metadata: Dict[str, Any]) -> int:
    edge_id = f"{source_id}|{relation}|{target_id}"
    conn.execute(
        """
        INSERT OR REPLACE INTO kg_edges(id, source_id, target_id, relation, weight, metadata_json, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (edge_id, source_id, target_id, relation, weight, json.dumps(metadata, ensure_ascii=False)),
    )
    return 1


def _json_list(value: str | None) -> List[Any]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _row(row: sqlite3.Row) -> Dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _unique(values: List[Any]) -> List[Any]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result

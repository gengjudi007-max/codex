from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_DB_PATH = Path("data/storage/codex.db")


SCHEMA = """
CREATE TABLE IF NOT EXISTS land_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city TEXT,
    district TEXT,
    title TEXT,
    land_use TEXT,
    buyer TEXT,
    date TEXT,
    source TEXT,
    source_level TEXT,
    url TEXT,
    land_area REAL,
    planned_gfa REAL,
    land_amount REAL,
    floor_price REAL,
    premium_rate REAL,
    raw_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_land_city ON land_records(city);
CREATE INDEX IF NOT EXISTS idx_land_date ON land_records(date);
CREATE INDEX IF NOT EXISTS idx_land_buyer ON land_records(buyer);
"""


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def insert_land_records(records: Iterable[Dict[str, Any]], db_path: Path | str = DEFAULT_DB_PATH) -> int:
    conn = connect(db_path)
    count = 0
    with conn:
        for item in records:
            raw = item.get("raw") or {}
            metrics = item.get("metrics") or {}
            conn.execute(
                """
                INSERT INTO land_records (
                    city, district, title, land_use, buyer, date, source, source_level, url,
                    land_area, planned_gfa, land_amount, floor_price, premium_rate, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.get("city"),
                    raw.get("district") or raw.get("county") or raw.get("qx"),
                    item.get("title"),
                    raw.get("land_use") or raw.get("landuse") or raw.get("tdyt") or raw.get("ghyt"),
                    raw.get("buyer") or raw.get("jdr") or raw.get("winner"),
                    item.get("date"),
                    item.get("source"),
                    item.get("source_level"),
                    item.get("url"),
                    metrics.get("land_area"),
                    metrics.get("planned_gfa"),
                    metrics.get("land_amount"),
                    metrics.get("floor_price"),
                    metrics.get("premium_rate"),
                    json.dumps(raw, ensure_ascii=False),
                ),
            )
            count += 1
    conn.close()
    return count


def load_land_json(path: Path | str) -> List[Dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    if isinstance(data, list):
        return data
    return []


def city_land_summary(db_path: Path | str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    conn = connect(db_path)
    rows = conn.execute(
        """
        SELECT
            city,
            COUNT(*) AS land_count,
            AVG(floor_price) AS avg_floor_price,
            AVG(premium_rate) AS avg_premium_rate,
            SUM(land_amount) AS total_land_amount,
            SUM(planned_gfa) AS total_planned_gfa
        FROM land_records
        WHERE city IS NOT NULL
        GROUP BY city
        ORDER BY total_land_amount DESC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def query_land_records(city: Optional[str] = None, limit: int = 20, db_path: Path | str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    conn = connect(db_path)
    if city:
        rows = conn.execute(
            "SELECT * FROM land_records WHERE city = ? ORDER BY date DESC LIMIT ?",
            (city, limit),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM land_records ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]

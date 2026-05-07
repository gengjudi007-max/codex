from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


DEFAULT_DUCKDB_PATH = Path("data/storage/codex.duckdb")


class DuckDBNotInstalled(RuntimeError):
    pass


def _duckdb():
    try:
        import duckdb  # type: ignore
        return duckdb
    except ImportError as exc:
        raise DuckDBNotInstalled(
            "DuckDB 未安装。执行：python -m pip install duckdb"
        ) from exc


def connect(db_path: Path | str = DEFAULT_DUCKDB_PATH):
    duckdb = _duckdb()
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS land_records (
            city VARCHAR,
            district VARCHAR,
            title VARCHAR,
            land_use VARCHAR,
            buyer VARCHAR,
            date VARCHAR,
            source VARCHAR,
            source_level VARCHAR,
            land_area DOUBLE,
            planned_gfa DOUBLE,
            land_amount DOUBLE,
            floor_price DOUBLE,
            premium_rate DOUBLE,
            raw_json VARCHAR
        )
        """
    )
    return conn


def load_land_json_to_duckdb(input_path: Path | str, db_path: Path | str = DEFAULT_DUCKDB_PATH) -> int:
    path = Path(input_path)
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items", data if isinstance(data, list) else [])

    conn = connect(db_path)
    count = 0
    for item in items:
        raw = item.get("raw") or {}
        metrics = item.get("metrics") or {}
        conn.execute(
            """
            INSERT INTO land_records VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                item.get("city"),
                raw.get("district") or raw.get("county") or raw.get("qx"),
                item.get("title"),
                raw.get("land_use") or raw.get("landuse") or raw.get("tdyt") or raw.get("ghyt"),
                raw.get("buyer") or raw.get("jdr") or raw.get("winner"),
                item.get("date"),
                item.get("source"),
                item.get("source_level"),
                metrics.get("land_area"),
                metrics.get("planned_gfa"),
                metrics.get("land_amount"),
                metrics.get("floor_price"),
                metrics.get("premium_rate"),
                json.dumps(raw, ensure_ascii=False),
            ],
        )
        count += 1
    conn.close()
    return count


def run_land_analytics(db_path: Path | str = DEFAULT_DUCKDB_PATH) -> List[Dict[str, Any]]:
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
        ORDER BY total_land_amount DESC NULLS LAST
        """
    ).fetchall()
    columns = [desc[0] for desc in conn.description]
    conn.close()
    return [dict(zip(columns, row)) for row in rows]

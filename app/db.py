from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app.config import INSTANCE_DIR, settings


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def encode_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def decode_json(value: str | None, default: Any = None) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS demands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                requester TEXT NOT NULL,
                business_unit TEXT NOT NULL,
                problem_statement TEXT NOT NULL,
                expected_impact TEXT NOT NULL,
                target_date TEXT NOT NULL,
                constraints TEXT NOT NULL,
                optional_skills TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'intake',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                demand_id INTEGER NOT NULL,
                stage TEXT NOT NULL,
                summary TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (demand_id) REFERENCES demands(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS analyses (
                demand_id INTEGER PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (demand_id) REFERENCES demands(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS decisions (
                demand_id INTEGER PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (demand_id) REFERENCES demands(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS manager_assignments (
                demand_id INTEGER PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (demand_id) REFERENCES demands(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS team_plans (
                demand_id INTEGER PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (demand_id) REFERENCES demands(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS tracking_plans (
                demand_id INTEGER PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (demand_id) REFERENCES demands(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS notifications (
                demand_id INTEGER PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (demand_id) REFERENCES demands(id) ON DELETE CASCADE
            );
            """
        )


def insert_demand(payload: dict[str, Any]) -> dict[str, Any]:
    timestamp = now_iso()
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO demands (
                title, requester, business_unit, problem_statement,
                expected_impact, target_date, constraints, optional_skills,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["title"],
                payload["requester"],
                payload["business_unit"],
                payload["problem_statement"],
                payload["expected_impact"],
                payload["target_date"],
                payload.get("constraints", ""),
                payload.get("optional_skills", ""),
                "intake",
                timestamp,
                timestamp,
            ),
        )
        demand_id = cursor.lastrowid
    add_audit_event(demand_id, "intake", "Demand captured from single-entry form.", payload)
    demand = get_demand(demand_id)
    if demand is None:
        raise RuntimeError("Demand could not be loaded after insert.")
    return demand


def get_demand(demand_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM demands WHERE id = ?", (demand_id,)).fetchone()
    return row_to_dict(row)


def update_demand_status(demand_id: int, status: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE demands SET status = ?, updated_at = ? WHERE id = ?",
            (status, now_iso(), demand_id),
        )


def upsert_payload(table: str, demand_id: int, payload: dict[str, Any]) -> None:
    allowed_tables = {
        "analyses",
        "decisions",
        "manager_assignments",
        "team_plans",
        "tracking_plans",
        "notifications",
    }
    if table not in allowed_tables:
        raise ValueError(f"Unsupported table: {table}")

    with connect() as conn:
        conn.execute(
            f"""
            INSERT INTO {table} (demand_id, payload_json, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(demand_id) DO UPDATE SET
                payload_json = excluded.payload_json,
                created_at = excluded.created_at
            """,
            (demand_id, encode_json(payload), now_iso()),
        )


def get_payload(table: str, demand_id: int) -> dict[str, Any] | None:
    allowed_tables = {
        "analyses",
        "decisions",
        "manager_assignments",
        "team_plans",
        "tracking_plans",
        "notifications",
    }
    if table not in allowed_tables:
        raise ValueError(f"Unsupported table: {table}")
    with connect() as conn:
        row = conn.execute(
            f"SELECT payload_json FROM {table} WHERE demand_id = ?", (demand_id,)
        ).fetchone()
    if row is None:
        return None
    return decode_json(row["payload_json"], {})


def add_audit_event(
    demand_id: int, stage: str, summary: str, payload: dict[str, Any]
) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO audit_events (demand_id, stage, summary, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (demand_id, stage, summary, encode_json(payload), now_iso()),
        )


def list_audit_events(demand_id: int) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, stage, summary, payload_json, created_at
            FROM audit_events
            WHERE demand_id = ?
            ORDER BY id ASC
            """,
            (demand_id,),
        ).fetchall()
    events = []
    for row in rows:
        item = row_to_dict(row) or {}
        item["payload"] = decode_json(item.pop("payload_json", None), {})
        events.append(item)
    return events

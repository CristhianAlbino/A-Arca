"""Local activity history shown on the HOME screen. Never leaves the computer."""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import UTC, datetime
from typing import Any

_lock = threading.Lock()


def now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def log_activity(
    conn: sqlite3.Connection, kind: str, message: str, data: dict[str, Any] | None = None
) -> None:
    with _lock:
        conn.execute(
            "INSERT INTO activity_log (at, kind, message, data_json) VALUES (?, ?, ?, ?)",
            (now_iso(), kind, message, json.dumps(data, ensure_ascii=False) if data else None),
        )
        conn.commit()


def recent_activity(
    conn: sqlite3.Connection, limit: int = 50, kind: str | None = None
) -> list[dict[str, Any]]:
    sql = "SELECT id, at, kind, message, data_json FROM activity_log"
    params: list[Any] = []
    if kind:
        sql += " WHERE kind = ?"
        params.append(kind)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [
        {
            "id": r["id"],
            "at": r["at"],
            "kind": r["kind"],
            "message": r["message"],
            "data": json.loads(r["data_json"]) if r["data_json"] else None,
        }
        for r in rows
    ]

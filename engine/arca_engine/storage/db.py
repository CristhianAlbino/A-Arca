"""SQLite database: connection setup and versioned migrations.

The schema version lives in PRAGMA user_version. Each migration runs once,
in order, inside a transaction. Never edit a migration that has shipped:
add a new one.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

MIGRATIONS: list[str] = [
    # 1 — Phase 1 core tables
    """
    CREATE TABLE volumes (
        id            TEXT PRIMARY KEY,          -- UUID from .arca-volume.json
        label         TEXT NOT NULL,
        last_root     TEXT,                       -- where it was last seen (may change)
        created_at    TEXT NOT NULL,
        last_seen_at  TEXT
    );

    CREATE TABLE items (
        id             TEXT PRIMARY KEY,          -- e.g. ARCA-0001
        name           TEXT NOT NULL,
        category       TEXT NOT NULL,
        subcategory    TEXT,
        origin         TEXT,
        author         TEXT,
        published      TEXT,
        language       TEXT,
        format         TEXT,
        size_bytes     INTEGER,
        license        TEXT,
        reliability    TEXT CHECK (reliability IN ('A','B','C','D')),
        sha256         TEXT,
        storage        TEXT,                       -- 'drive' | 'url-externa' | 'local'
        local_status   TEXT NOT NULL DEFAULT 'so-nuvem'
                       CHECK (local_status IN ('so-nuvem','baixado','verificado','indexado')),
        uri            TEXT,                       -- vol://<uuid>/<relative path>
        notes          TEXT,
        created_at     TEXT NOT NULL,
        updated_at     TEXT NOT NULL
    );
    CREATE INDEX items_category ON items(category);

    CREATE TABLE activity_log (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        at         TEXT NOT NULL,
        kind       TEXT NOT NULL,                  -- e.g. 'engine', 'volume', 'network'
        message    TEXT NOT NULL,
        data_json  TEXT
    );
    CREATE INDEX activity_at ON activity_log(at);
    """,
    # 2 — Phase 2 conversations with the AI
    """
    CREATE TABLE conversations (
        id          TEXT PRIMARY KEY,               -- UUID
        title       TEXT NOT NULL,
        provider    TEXT NOT NULL,                  -- 'ollama', later 'anthropic', 'openai'...
        model       TEXT,
        created_at  TEXT NOT NULL,
        updated_at  TEXT NOT NULL
    );
    CREATE INDEX conversations_updated ON conversations(updated_at);

    CREATE TABLE messages (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id  TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        role             TEXT NOT NULL CHECK (role IN ('user','assistant','system')),
        content          TEXT NOT NULL,
        model            TEXT,
        status           TEXT NOT NULL DEFAULT 'ok' CHECK (status IN ('ok','interrupted','error')),
        stats_json       TEXT,
        created_at       TEXT NOT NULL
    );
    CREATE INDEX messages_conversation ON messages(conversation_id, id);
    """,
    # 3 — Phase 3 catalog of ZIM encyclopedias seen on ARCA volumes
    """
    CREATE TABLE zims (
        id             TEXT PRIMARY KEY,            -- the ZIM's own UUID
        volume_id      TEXT NOT NULL REFERENCES volumes(id),
        uri            TEXT NOT NULL,               -- vol://<uuid>/<relative path>
        title          TEXT NOT NULL,
        description    TEXT NOT NULL DEFAULT '',
        language       TEXT NOT NULL DEFAULT '',
        article_count  INTEGER NOT NULL,
        size_bytes     INTEGER NOT NULL,
        has_fulltext   INTEGER NOT NULL,
        first_seen_at  TEXT NOT NULL,
        last_seen_at   TEXT NOT NULL
    );
    """,
]


def connect(path: Path | str) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def schema_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def migrate(conn: sqlite3.Connection) -> int:
    """Apply pending migrations. Returns the resulting schema version."""
    current = schema_version(conn)
    if current > len(MIGRATIONS):
        raise RuntimeError(
            f"Database schema {current} is newer than this engine ({len(MIGRATIONS)}). "
            "Update the ARCA before opening this database."
        )
    for version, sql in enumerate(MIGRATIONS[current:], start=current + 1):
        try:
            conn.execute("BEGIN")
            for statement in _split_statements(sql):
                conn.execute(statement)
            conn.execute(f"PRAGMA user_version = {version}")
            conn.execute("COMMIT")
        except BaseException:
            conn.execute("ROLLBACK")
            raise
    return schema_version(conn)


def _split_statements(sql: str) -> list[str]:
    statements, buffer = [], []
    for line in sql.splitlines():
        code = line.split("--", 1)[0]
        buffer.append(code)
        if code.rstrip().endswith(";"):
            joined = "\n".join(buffer).strip()
            if joined:
                statements.append(joined)
            buffer = []
    rest = "\n".join(buffer).strip()
    if rest:
        statements.append(rest)
    return statements


def open_database(path: Path | str) -> sqlite3.Connection:
    conn = connect(path)
    migrate(conn)
    return conn

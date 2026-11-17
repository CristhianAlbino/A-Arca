import pytest

from arca_engine.activity import log_activity, recent_activity
from arca_engine.storage import db as dbmod


def test_migrations_create_tables(db):
    assert dbmod.schema_version(db) == len(dbmod.MIGRATIONS)
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"volumes", "items", "activity_log"} <= tables


def test_wal_mode_is_enabled(db):
    assert db.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def test_migrate_is_idempotent(db):
    assert dbmod.migrate(db) == len(dbmod.MIGRATIONS)


def test_newer_database_is_refused(db):
    db.execute(f"PRAGMA user_version = {len(dbmod.MIGRATIONS) + 1}")
    with pytest.raises(RuntimeError):
        dbmod.migrate(db)


def test_item_status_is_constrained(db):
    import sqlite3

    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO items (id, name, category, local_status, created_at, updated_at) "
            "VALUES ('X', 'x', 'c', 'perdido', 'now', 'now')"
        )


def test_activity_log_newest_first(db):
    log_activity(db, "engine", "primeiro")
    log_activity(db, "volume", "segundo", {"id": "abc"})
    items = recent_activity(db)
    assert [i["message"] for i in items] == ["segundo", "primeiro"]
    assert items[0]["data"] == {"id": "abc"}
    assert [i["message"] for i in recent_activity(db, kind="engine")] == ["primeiro"]

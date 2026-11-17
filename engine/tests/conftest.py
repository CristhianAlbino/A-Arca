import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from arca_engine.config.paths import resolve_app_paths  # noqa: E402
from arca_engine.storage.db import open_database  # noqa: E402


@pytest.fixture
def app_paths(tmp_path):
    return resolve_app_paths(env={"ARCA_HOME": str(tmp_path / "arca-home")}).ensure()


@pytest.fixture
def db(app_paths):
    conn = open_database(app_paths.database_file)
    yield conn
    conn.close()

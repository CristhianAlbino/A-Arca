import json
from pathlib import Path

import pytest

from arca_engine.config.paths import resolve_app_paths
from arca_engine.config.settings import Settings, load_settings, save_settings


def test_windows_paths_use_appdata_and_localappdata():
    env = {"APPDATA": r"C:\Users\cris\AppData\Roaming", "LOCALAPPDATA": r"C:\Users\cris\AppData\Local"}
    paths = resolve_app_paths(env=env, platform="win32")
    assert paths.config_dir == Path(env["APPDATA"]) / "ARCA" / "config"
    assert paths.data_dir == Path(env["LOCALAPPDATA"]) / "ARCA" / "data"
    assert paths.database_file.name == "arca.db"


def test_arca_home_overrides_everything(tmp_path):
    paths = resolve_app_paths(env={"ARCA_HOME": str(tmp_path)}, platform="win32")
    assert paths.config_dir == tmp_path / "config"
    assert paths.data_dir == tmp_path / "data"


def test_missing_settings_file_gives_defaults(tmp_path):
    settings = load_settings(tmp_path / "nope.json")
    assert settings.network_mode == "blocked"
    assert settings.language == "pt-BR"


def test_settings_roundtrip_keeps_unknown_keys(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"network_mode": "online", "future_option": 42}), encoding="utf-8")
    settings = load_settings(path)
    assert settings.network_mode == "online"
    save_settings(path, settings)
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["future_option"] == 42
    assert saved["network_mode"] == "online"


def test_invalid_network_mode_is_rejected():
    with pytest.raises(ValueError):
        Settings.from_dict({"network_mode": "sometimes"})

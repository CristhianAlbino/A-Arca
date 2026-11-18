"""Where the engine keeps its own files.

Defaults follow each OS's conventions. On Windows:
- config  -> %APPDATA%\\ARCA\\config
- data    -> %LOCALAPPDATA%\\ARCA\\data   (SQLite database, always on the internal disk)
- logs    -> %LOCALAPPDATA%\\ARCA\\logs

Setting the ARCA_HOME environment variable puts everything under one folder
(portable installs and tests).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

APP_DIR_NAME = "ARCA"


@dataclass(frozen=True)
class AppPaths:
    config_dir: Path
    data_dir: Path
    logs_dir: Path

    @property
    def settings_file(self) -> Path:
        return self.config_dir / "settings.json"

    @property
    def database_file(self) -> Path:
        return self.data_dir / "arca.db"

    def ensure(self) -> AppPaths:
        for d in (self.config_dir, self.data_dir, self.logs_dir):
            d.mkdir(parents=True, exist_ok=True)
        return self


def resolve_app_paths(env: dict[str, str] | None = None, platform: str | None = None) -> AppPaths:
    """Return the engine's folders without creating them."""
    env = dict(os.environ) if env is None else env
    platform = sys.platform if platform is None else platform

    home_override = env.get("ARCA_HOME")
    if home_override:
        root = Path(home_override)
        return AppPaths(root / "config", root / "data", root / "logs")

    if platform.startswith("win"):
        roaming = Path(env.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        local = Path(env.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        return AppPaths(
            roaming / APP_DIR_NAME / "config",
            local / APP_DIR_NAME / "data",
            local / APP_DIR_NAME / "logs",
        )

    if platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / APP_DIR_NAME
        return AppPaths(base / "config", base / "data", base / "logs")

    config_home = Path(env.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    data_home = Path(env.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")
    state_home = Path(env.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
    name = APP_DIR_NAME.lower()
    return AppPaths(config_home / name, data_home / name, state_home / name / "logs")

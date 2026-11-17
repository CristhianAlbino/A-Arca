"""User settings stored as JSON in the config folder.

Unknown keys are preserved so that a newer engine never loses data written by
an older or newer version. Writes are atomic (temp file + replace).
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SETTINGS_SCHEMA = 1


@dataclass
class Settings:
    schema: int = SETTINGS_SCHEMA
    language: str = "pt-BR"
    # Network starts blocked. "online" only after the user turns it on.
    network_mode: str = "blocked"
    # Hosts the user allowed while online (e.g. "api.anthropic.com").
    network_allowlist: list[str] = field(default_factory=list)
    # Extra folders to look for ARCA volumes in (mount points, folders on drives).
    volume_search_paths: list[str] = field(default_factory=list)
    # Minutes before an idle local model is unloaded (used from Phase 2).
    model_idle_unload_minutes: int = 5
    extra: dict[str, Any] = field(default_factory=dict)

    VALID_NETWORK_MODES = ("blocked", "online")

    def validate(self) -> None:
        if self.network_mode not in self.VALID_NETWORK_MODES:
            raise ValueError(f"network_mode must be one of {self.VALID_NETWORK_MODES}")
        if self.model_idle_unload_minutes < 1:
            raise ValueError("model_idle_unload_minutes must be >= 1")

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        extra = data.pop("extra")
        return {**extra, **data}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Settings":
        known = {f for f in cls.__dataclass_fields__ if f != "extra"}
        kwargs = {k: v for k, v in data.items() if k in known}
        extra = {k: v for k, v in data.items() if k not in known}
        settings = cls(**kwargs, extra=extra)
        settings.validate()
        return settings


def load_settings(path: Path) -> Settings:
    if not path.exists():
        return Settings()
    with path.open("r", encoding="utf-8") as fh:
        return Settings.from_dict(json.load(fh))


def save_settings(path: Path, settings: Settings) -> None:
    settings.validate()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".settings-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(settings.to_dict(), fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise

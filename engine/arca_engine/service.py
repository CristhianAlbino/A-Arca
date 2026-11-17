"""What the API does, without the web framework.

Keeping the logic here lets it be tested without FastAPI and keeps the HTTP
layer (api/app.py) a thin translation of these functions.
"""

from __future__ import annotations

from typing import Any

from . import __version__
from .activity import log_activity, recent_activity
from .context import AppContext
from .storage.db import schema_version
from .system import info

EDITABLE_SETTINGS = {
    "language",
    "network_mode",
    "network_allowlist",
    "volume_search_paths",
    "model_idle_unload_minutes",
}


class ServiceError(Exception):
    def __init__(self, message: str, status: int = 400):
        self.status = status
        super().__init__(message)


def health(ctx: AppContext) -> dict[str, Any]:
    return {
        "status": "ok",
        "version": __version__,
        "db_schema": schema_version(ctx.db),
        "network_mode": ctx.settings.network_mode,
    }


def system(ctx: AppContext) -> dict[str, Any]:
    snap = info.snapshot(ctx.paths.data_dir)
    snap["volumes"] = ctx.volumes.status()
    snap["network_mode"] = ctx.settings.network_mode
    return snap


def list_volumes(ctx: AppContext, rescan: bool = False) -> list[dict[str, Any]]:
    if rescan:
        ctx.volumes.scan()
    return ctx.volumes.status()


def register_volume(ctx: AppContext, path: str, label: str) -> dict[str, Any]:
    label = label.strip()
    if not label:
        raise ServiceError("Informe um nome para o volume.")
    try:
        marker = ctx.volumes.register(path, label)
    except Exception as exc:  # VolumeError, OSError
        raise ServiceError(str(exc)) from exc
    return {"id": marker.volume_id, "label": marker.label}


def get_settings(ctx: AppContext) -> dict[str, Any]:
    return ctx.settings.to_dict()


def update_settings(ctx: AppContext, changes: dict[str, Any]) -> dict[str, Any]:
    unknown = set(changes) - EDITABLE_SETTINGS
    if unknown:
        raise ServiceError(f"Configurações não editáveis: {', '.join(sorted(unknown))}")
    try:
        return ctx.update_settings(changes).to_dict()
    except (ValueError, TypeError) as exc:
        raise ServiceError(str(exc)) from exc


def activity(ctx: AppContext, limit: int = 50) -> list[dict[str, Any]]:
    return recent_activity(ctx.db, limit=max(1, min(limit, 500)))


def network_attempts(ctx: AppContext, only_blocked: bool = False) -> list[dict[str, Any]]:
    return ctx.netguard.attempts(only_blocked=only_blocked)


def engine_started(ctx: AppContext) -> None:
    log_activity(ctx.db, "engine", f"Motor iniciado (versão {__version__})")

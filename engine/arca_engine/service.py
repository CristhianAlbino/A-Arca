"""What the API does, without the web framework.

Keeping the logic here lets it be tested without FastAPI and keeps the HTTP
layer (api/app.py) a thin translation of these functions.
"""

from __future__ import annotations

from typing import Any

from . import __version__
from collections.abc import Iterator

from .activity import log_activity, recent_activity
from .ai.base import ProviderError, ProviderUnavailable
from .ai.chat import ChatStore, chat_stream
from .context import AppContext
from .storage.db import schema_version
from .system import info

EDITABLE_SETTINGS = {
    "language",
    "network_mode",
    "network_allowlist",
    "volume_search_paths",
    "model_idle_unload_minutes",
    "ollama_url",
    "default_model",
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


# --- AI (Phase 2) -------------------------------------------------------------
def memory_free() -> tuple[int | None, int]:
    """Free VRAM (None without an NVIDIA GPU) and available RAM, in bytes."""
    gpu = info.gpus()
    vram = None
    if gpu["available"]:
        card = gpu["devices"][0]
        vram = max(0, card["total_bytes"] - card["used_bytes"])
    return vram, info.memory()["available_bytes"]


def ai_status(ctx: AppContext) -> dict[str, Any]:
    provider = ctx.ai_provider()
    status = provider.status()
    out: dict[str, Any] = {
        "provider": provider.name,
        "url": provider.base_url,
        **status,
        "models": [],
        "loaded": [],
        "default_model": ctx.settings.default_model,
    }
    if status["available"]:
        try:
            out["models"] = [m.to_dict() for m in provider.list_models()]
            out["loaded"] = [vars(m) for m in provider.loaded()]
        except (ProviderUnavailable, ProviderError) as exc:
            out.update(available=False, reason=str(exc))
    return out


def unload_model(ctx: AppContext, model: str) -> dict[str, Any]:
    try:
        ctx.ai_provider().unload(model)
    except (ProviderUnavailable, ProviderError) as exc:
        raise ServiceError(str(exc), status=503) from exc
    log_activity(ctx.db, "ai", f"Modelo descarregado da memória: {model}")
    return {"unloaded": model}


def list_conversations(ctx: AppContext, limit: int = 100) -> list[dict[str, Any]]:
    return ChatStore(ctx.db).list(limit=max(1, min(limit, 500)))


def get_conversation(ctx: AppContext, conversation_id: str) -> dict[str, Any]:
    conv = ChatStore(ctx.db).get(conversation_id)
    if conv is None:
        raise ServiceError("Conversa não encontrada.", status=404)
    return conv


def delete_conversation(ctx: AppContext, conversation_id: str) -> dict[str, Any]:
    if not ChatStore(ctx.db).delete(conversation_id):
        raise ServiceError("Conversa não encontrada.", status=404)
    return {"deleted": conversation_id}


def chat(
    ctx: AppContext,
    text: str,
    model: str | None = None,
    conversation_id: str | None = None,
    memory_probe=memory_free,
) -> Iterator[dict[str, Any]]:
    model = model or ctx.settings.default_model
    if not model:
        return iter([{"type": "error", "message": "Escolha um modelo para conversar."}])
    return chat_stream(
        ChatStore(ctx.db),
        ctx.ai_provider(),
        text=text,
        model=model,
        conversation_id=conversation_id,
        memory_probe=memory_probe,
        keep_alive_minutes=ctx.settings.model_idle_unload_minutes,
    )

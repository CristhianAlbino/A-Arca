"""What the API does, without the web framework.

Keeping the logic here lets it be tested without FastAPI and keeps the HTTP
layer (api/app.py) a thin translation of these functions.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from . import __version__
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
        "network_mode": ctx.settings.network_mode,
        "idle_unload_minutes": ctx.settings.model_idle_unload_minutes,
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


MODEL_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-/]{0,127}(:[A-Za-z0-9._\-]{1,64})?$")
ONLINE_REQUIRED = (
    "Baixar modelos precisa de internet. Ligue o modo online nas configurações "
    "e tente de novo; o resto da ARCA continua funcionando offline."
)


def _check_model_name(model: str) -> str:
    model = model.strip()
    if not MODEL_NAME.match(model) or ".." in model:
        raise ServiceError("Nome de modelo inválido. Exemplo: llama3.2:3b")
    return model


def pull_model(ctx: AppContext, model: str) -> Iterator[dict[str, Any]]:
    """Download a model through Ollama. Only with online mode on.

    Validation errors raise before streaming starts (HTTP 4xx); errors during
    the download arrive as a final {"type": "error"} event.
    """
    model = _check_model_name(model)
    if ctx.settings.network_mode != "online":
        raise ServiceError(ONLINE_REQUIRED, status=403)
    provider = ctx.ai_provider()

    def events() -> Iterator[dict[str, Any]]:
        log_activity(ctx.db, "ai", f"Download de modelo iniciado: {model}")
        try:
            for ev in provider.pull(model):
                yield {
                    "type": "progress",
                    "status": ev.get("status", ""),
                    "completed": ev.get("completed"),
                    "total": ev.get("total"),
                }
        except (ProviderUnavailable, ProviderError) as exc:
            log_activity(ctx.db, "ai", f"Download de modelo falhou: {model}")
            yield {"type": "error", "message": str(exc)}
            return
        log_activity(ctx.db, "ai", f"Modelo baixado: {model}")
        yield {"type": "done", "model": model}

    return events()


def delete_model(ctx: AppContext, model: str) -> dict[str, Any]:
    """Remove a model from Ollama's disk. Unloads it from memory first."""
    model = _check_model_name(model)
    provider = ctx.ai_provider()
    try:
        if any(m.name == model for m in provider.loaded()):
            provider.unload(model)
        provider.delete(model)
    except ProviderUnavailable as exc:
        raise ServiceError(str(exc), status=503) from exc
    except ProviderError as exc:
        raise ServiceError(str(exc), status=404 if "not found" in str(exc) else 502) from exc
    if ctx.settings.default_model == model:
        ctx.update_settings({"default_model": None})
    log_activity(ctx.db, "ai", f"Modelo removido: {model}")
    return {"deleted": model}


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


# --- Knowledge: offline encyclopedias (Phase 3) ---------------------------------
def _knowledge(call):
    from .knowledge.kiwix import KnowledgeError

    try:
        return call()
    except KnowledgeError as exc:
        raise ServiceError(str(exc), status=exc.status) from exc


def list_zims(ctx: AppContext, rescan: bool = False) -> list[dict[str, Any]]:
    return _knowledge(lambda: ctx.zims.catalog(rescan=rescan))


def search_knowledge(
    ctx: AppContext, query: str, zim_id: str | None = None, limit: int = 20
) -> list[dict[str, Any]]:
    if len(query) > 300:
        raise ServiceError("Busca longa demais (máximo de 300 caracteres).")
    limit = max(1, min(limit, 50))
    return _knowledge(lambda: ctx.zims.search(query, zim_id=zim_id, limit=limit))


def read_article(ctx: AppContext, zim_id: str, path: str | None = None) -> dict[str, Any]:
    return _knowledge(lambda: ctx.zims.article(zim_id, path))
